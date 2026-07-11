//! Phase 4C: `/ws/voice` WebSocket endpoint (inbound adapter).
//!
//! The frontend streams `{ "text": "equip my Sunshot" }`; we run it through the
//! domain `VoiceCommandSaga` and stream back `{ "response": "...", "intent": "..." }`.
//! Inventory/lore execution is acknowledged but lands in Phases 4D/4E.

use std::sync::Arc;

use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        Query, State,
    },
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::get,
    Router,
};
use serde::Deserialize;
use serde_json::json;

use domain::auth::membership::BungieMembershipId;
use domain::career::saga::GuardianProfileSaga;
use domain::inventory::saga::EquipItemSaga;
use domain::lore::saga::LoreSaga;
use domain::voice_ai::conversation::ConversationSaga;
use domain::voice_ai::intent::VoiceIntent;
use domain::voice_ai::saga::VoiceCommandSaga;
use domain::voice_ai::tools::ConversationItem;

/// Cap on per-socket conversational memory (most-recent items kept).
const WS_HISTORY_LIMIT: usize = 16;

/// Appends a completed turn to the socket's short-term memory, trimming to cap.
fn remember(history: &mut Vec<ConversationItem>, user: &str, reply: &str) {
    history.push(ConversationItem::User(user.to_string()));
    history.push(ConversationItem::Assistant {
        content: Some(reply.to_string()),
        tool_calls: vec![],
    });
    if history.len() > WS_HISTORY_LIMIT {
        history.drain(0..history.len() - WS_HISTORY_LIMIT);
    }
}

use crate::bungie_oauth_routes::AppState;

/// Mounts `/ws/voice`.
pub fn voice_ws_router(state: AppState) -> Router {
    Router::new()
        .route("/ws/voice", get(voice_ws_handler))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
struct WsAuthQuery {
    /// Optional legacy dev token (gates the socket when no real auth is required).
    token: Option<String>,
    /// Signed session token; when valid it authenticates the connection and
    /// supplies the owning membership (preferred over the `membership_id` param).
    session: Option<String>,
    /// DEV SEAM: membership/character as params. Honored only when auth isn't
    /// required; a valid `session` always takes precedence for the membership.
    membership_id: Option<String>,
    character_id: Option<String>,
}

/// The authenticated context needed to execute gear actions.
#[derive(Clone)]
struct EquipContext {
    membership_id: BungieMembershipId,
    character_id: String,
}

/// Validates the connection, then upgrades to a WebSocket if voice AI is available.
async fn voice_ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
    Query(query): Query<WsAuthQuery>,
) -> Response {
    // A valid (non-revoked) session authenticates the connection and names the owner.
    let session_member = match query.session.as_deref().and_then(|t| state.session.verify(t).ok()) {
        Some(session) => {
            let cutoff = state
                .revocations
                .revoked_before(&session.membership_id)
                .await
                .unwrap_or(None);
            if session.is_revoked(cutoff) {
                None
            } else {
                Some(session.membership_id)
            }
        }
        None => None,
    };

    // Production: a real session is mandatory. Dev: keep the legacy token gate.
    if state.require_auth {
        if session_member.is_none() {
            return (StatusCode::UNAUTHORIZED, "valid session required").into_response();
        }
    } else if !is_authorized(&state, query.token.as_deref()) {
        return (StatusCode::UNAUTHORIZED, "missing or invalid session token").into_response();
    }

    // Owner: the session's membership wins; otherwise the dev param (dev only).
    let membership = session_member.or_else(|| {
        query
            .membership_id
            .filter(|m| !m.is_empty())
            .and_then(|m| BungieMembershipId::new(m).ok())
    });

    // Meter per Guardian, not per socket — otherwise reconnecting would reset the
    // budget. Derived before `equip_ctx` consumes the membership; a signed-in user
    // with no character selected still gets their own bucket.
    let limiter_key = membership
        .as_ref()
        .map_or_else(|| "anonymous".to_string(), |m| m.0.clone());

    let equip_ctx = match (membership, query.character_id) {
        (Some(membership_id), Some(c)) if !c.is_empty() => Some(EquipContext {
            membership_id,
            character_id: c,
        }),
        _ => None,
    };

    match state.voice_saga.clone() {
        Some(saga) => {
            let equip_saga = state.equip_saga.clone();
            let lore_saga = state.lore_saga.clone();
            let profile_saga = state.profile_saga.clone();
            let conversation_saga = state.conversation_saga.clone();
            let bungie_api = state.bungie_api.clone();
            let manifest_defs = state.manifest_defs.clone();
            let limiter = state.chat_limiter.clone();
            ws.on_upgrade(move |socket| {
                handle_socket(
                    socket,
                    saga,
                    conversation_saga,
                    equip_saga,
                    lore_saga,
                    profile_saga,
                    bungie_api,
                    manifest_defs,
                    equip_ctx,
                    limiter,
                    limiter_key,
                )
            })
        }
        None => (
            StatusCode::SERVICE_UNAVAILABLE,
            "voice AI is not configured (set LLM_API_KEY / OPENAI_API_KEY)",
        )
            .into_response(),
    }
}

/// When a dev token is configured it must match; otherwise the socket is open
/// (local dev). Real session validation is a TODO documented on `AppState`.
fn is_authorized(state: &AppState, token: Option<&str>) -> bool {
    match &state.ws_dev_token {
        Some(expected) => token == Some(expected.as_str()),
        None => true,
    }
}

#[allow(clippy::too_many_arguments)]
async fn handle_socket(
    mut socket: WebSocket,
    saga: Arc<VoiceCommandSaga>,
    conversation_saga: Option<Arc<ConversationSaga>>,
    equip_saga: Arc<EquipItemSaga>,
    lore_saga: Option<Arc<LoreSaga>>,
    profile_saga: Arc<GuardianProfileSaga>,
    bungie_api: Arc<crate::bungie_api_client::BungieApiClient>,
    manifest_defs: Arc<db::ManifestDefinitionResolver>,
    equip_ctx: Option<EquipContext>,
    limiter: Arc<crate::rate_limit::RateLimiter>,
    limiter_key: String,
) {
    // For a signed-in user, fetch the full dossier (career stats + recent
    // activity): greet them and use it to personalize and ground every reply.
    let guardian_context: Option<String> = match &equip_ctx {
        Some(ctx) => match profile_saga.full_context(&ctx.membership_id).await {
            Some(dossier) => {
                let greeting = json!({ "response": dossier, "intent": "greeting" }).to_string();
                let _ = socket.send(Message::Text(greeting)).await;
                Some(dossier)
            }
            None => None,
        },
        None => None,
    };

    // Short-term memory for this socket so voice chat can follow up across turns.
    let mut history: Vec<ConversationItem> = Vec::new();

    while let Some(Ok(msg)) = socket.recv().await {
        match msg {
            Message::Text(text) => {
                // Meter before spending inference. Throttling answers in-band
                // rather than closing the socket: the client stays connected and
                // the Guardian sees why the Ghost went quiet.
                if let Err(retry_after) = limiter.check(&limiter_key) {
                    let secs = retry_after.as_secs_f64().ceil().max(1.0) as u64;
                    let throttled = json!({
                        "response": format!(
                            "The Ghost needs a moment to recharge. Try again in {secs}s."
                        ),
                        "intent": "throttled",
                        "retry_after_secs": secs,
                    })
                    .to_string();
                    let _ = socket.send(Message::Text(throttled)).await;
                    continue;
                }

                let reply = process_text(
                    &saga,
                    conversation_saga.as_deref(),
                    &equip_saga,
                    lore_saga.as_deref(),
                    &bungie_api,
                    &manifest_defs,
                    guardian_context.as_deref(),
                    equip_ctx.as_ref(),
                    &mut history,
                    &text,
                )
                .await;
                if socket.send(Message::Text(reply)).await.is_err() {
                    break;
                }
            }
            Message::Close(_) => break,
            _ => {}
        }
    }
}

#[derive(Debug, Deserialize)]
struct InboundVoice {
    text: String,
}

/// Parses one inbound frame, runs the saga, and renders the JSON reply string.
#[allow(clippy::too_many_arguments)]
async fn process_text(
    saga: &VoiceCommandSaga,
    conversation_saga: Option<&ConversationSaga>,
    equip_saga: &Arc<EquipItemSaga>,
    lore_saga: Option<&LoreSaga>,
    bungie_api: &Arc<crate::bungie_api_client::BungieApiClient>,
    manifest_defs: &Arc<db::ManifestDefinitionResolver>,
    guardian_context: Option<&str>,
    equip_ctx: Option<&EquipContext>,
    history: &mut Vec<ConversationItem>,
    raw: &str,
) -> String {
    let Ok(inbound) = serde_json::from_str::<InboundVoice>(raw) else {
        return json!({
            "response": "I couldn't parse that message. Send { \"text\": \"...\" }.",
            "intent": "error"
        })
        .to_string();
    };

    match saga
        .process_voice_command_with_context(&inbound.text, guardian_context)
        .await
    {
        Ok(intent) => {
            // Execute equips for real when we have an authenticated context;
            // otherwise (and for not-yet-wired intents) acknowledge.
            if let (VoiceIntent::Equip { item_name, .. }, Some(ctx)) = (&intent, equip_ctx) {
                let response = match equip_saga
                    .process_equip(&ctx.membership_id, item_name, &ctx.character_id)
                    .await
                {
                    Ok(success) => success,
                    Err(graceful) => graceful,
                };
                return json!({ "response": response, "intent": "equip" }).to_string();
            }

            // Conversational intents (lore questions, open chat) get a free-form,
            // grounded reply from the Ghost when an LLM is configured: anchored in
            // retrieved lore, the Guardian's career/activity dossier, AND live
            // Bungie reads the Ghost can perform on demand (tool-calling).
            if let (VoiceIntent::Lore { .. } | VoiceIntent::Unknown { .. }, Some(chat)) =
                (&intent, conversation_saga)
            {
                let mut executor = crate::bungie_api_client::BungieToolExecutor::new(
                    bungie_api.clone(),
                    equip_ctx.map(|c| c.membership_id.clone()),
                )
                .with_definitions(manifest_defs.clone());
                // Quick gear changes target the connection's active character.
                if let Some(ctx) = equip_ctx {
                    executor = executor
                        .with_writes(equip_saga.clone(), Some(ctx.character_id.clone()));
                }
                match chat
                    .converse_with_tools(&inbound.text, guardian_context, history, Some(&executor))
                    .await
                {
                    Ok(reply) => {
                        remember(history, &inbound.text, &reply);
                        return json!({ "response": reply, "intent": "conversation" }).to_string();
                    }
                    // Fall through to the lore RAG / canned reply on LLM failure.
                    Err(_) => {}
                }
            }

            // Answer lore queries from the RAG pipeline when conversation is unavailable.
            if let (VoiceIntent::Lore { topic }, Some(lore)) = (&intent, lore_saga) {
                let response = match lore.process_lore_query(topic).await {
                    Ok(context) => context,
                    Err(graceful) => graceful,
                };
                return json!({ "response": response, "intent": "lore" }).to_string();
            }

            let (label, response) = describe_intent(&intent);
            json!({ "response": response, "intent": label }).to_string()
        }
        Err(err) => json!({
            "response": format!("The Ghost faltered: {err}"),
            "intent": "error"
        })
        .to_string(),
    }
}

/// Maps a parsed intent to an `(intent_label, response_text)` pair. Execution of
/// gear/lore actions is deferred to Phases 4D/4E, so we acknowledge for now.
fn describe_intent(intent: &VoiceIntent) -> (&'static str, String) {
    match intent {
        VoiceIntent::Equip { item_name, .. } => (
            "equip",
            format!("Understood — you want to equip {item_name}. (Gear actions arrive in Phase 4D.)"),
        ),
        VoiceIntent::Transfer { item_name, to_vault } => {
            let dest = if *to_vault { "the vault" } else { "your character" };
            (
                "transfer",
                format!("Got it — move {item_name} to {dest}. (Gear actions arrive in Phase 4D.)"),
            )
        }
        VoiceIntent::PullPostmaster { .. } => (
            "pull_postmaster",
            "I'll pull your Postmaster items once gear actions land in Phase 4D.".to_string(),
        ),
        VoiceIntent::QueryInventory { .. } => (
            "query_inventory",
            "Inventory readouts arrive in Phase 4D, Guardian.".to_string(),
        ),
        VoiceIntent::Lore { topic } => (
            "lore",
            format!("Searching the archives for \"{topic}\"… (Lore retrieval arrives in Phase 4E.)"),
        ),
        VoiceIntent::Unknown { reason_for_confusion } => (
            "unknown",
            format!("I didn't quite catch that: {reason_for_confusion}"),
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn describe_intent_labels_match_variants() {
        assert_eq!(
            describe_intent(&VoiceIntent::Lore { topic: "the Traveler".into() }).0,
            "lore"
        );
        assert_eq!(
            describe_intent(&VoiceIntent::Equip {
                item_name: "Sunshot".into(),
                character_class: None
            })
            .0,
            "equip"
        );
        assert_eq!(
            describe_intent(&VoiceIntent::Unknown {
                reason_for_confusion: "n/a".into()
            })
            .0,
            "unknown"
        );
    }
}
