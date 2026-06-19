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
use domain::inventory::saga::EquipItemSaga;
use domain::voice_ai::intent::VoiceIntent;
use domain::voice_ai::saga::VoiceCommandSaga;

use crate::bungie_oauth_routes::AppState;

/// Mounts `/ws/voice`.
pub fn voice_ws_router(state: AppState) -> Router {
    Router::new()
        .route("/ws/voice", get(voice_ws_handler))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
struct WsAuthQuery {
    token: Option<String>,
    // DEV SEAM: a real implementation derives these from the authenticated
    // session (Bungie membership) and resolves the character from the intent's
    // class. Until session minting exists they may be passed as query params so
    // the equip flow is end-to-end testable. TODO: replace with real session.
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
    if !is_authorized(&state, query.token.as_deref()) {
        return (StatusCode::UNAUTHORIZED, "missing or invalid session token").into_response();
    }

    let equip_ctx = match (query.membership_id, query.character_id) {
        (Some(m), Some(c)) if !m.is_empty() && !c.is_empty() => {
            BungieMembershipId::new(m).ok().map(|membership_id| EquipContext {
                membership_id,
                character_id: c,
            })
        }
        _ => None,
    };

    match state.voice_saga.clone() {
        Some(saga) => {
            let equip_saga = state.equip_saga.clone();
            ws.on_upgrade(move |socket| handle_socket(socket, saga, equip_saga, equip_ctx))
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

async fn handle_socket(
    mut socket: WebSocket,
    saga: Arc<VoiceCommandSaga>,
    equip_saga: Arc<EquipItemSaga>,
    equip_ctx: Option<EquipContext>,
) {
    while let Some(Ok(msg)) = socket.recv().await {
        match msg {
            Message::Text(text) => {
                let reply = process_text(&saga, &equip_saga, equip_ctx.as_ref(), &text).await;
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
async fn process_text(
    saga: &VoiceCommandSaga,
    equip_saga: &EquipItemSaga,
    equip_ctx: Option<&EquipContext>,
    raw: &str,
) -> String {
    let Ok(inbound) = serde_json::from_str::<InboundVoice>(raw) else {
        return json!({
            "response": "I couldn't parse that message. Send { \"text\": \"...\" }.",
            "intent": "error"
        })
        .to_string();
    };

    match saga.process_voice_command(&inbound.text).await {
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
