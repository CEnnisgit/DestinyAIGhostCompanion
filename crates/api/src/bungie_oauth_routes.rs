//! Phase 4B: Bungie OAuth2 callback routes (axum) — the driving (inbound) adapter.
//!
//! `/auth/login`   → redirect the Guardian to Bungie's consent screen.
//! `/auth/callback`→ exchange the returned code for tokens, then hand them to the
//!                   domain `OAuthSessionSaga` which resolves identity + persists.
//!
//! ADR-005: delegated authentication — no passwords, 100% Bungie OAuth2 SSO.

use std::sync::Arc;

use axum::{
    extract::{Path, Query, State},
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Json, Redirect, Response},
    routing::get,
    Router,
};
use chrono::{Duration, Utc};
use serde::Deserialize;
use serde_json::json;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::SessionAuthority;
use domain::auth::saga::OAuthSessionSaga;
use domain::auth::session::Session;
use domain::auth::token::BungieOAuthToken;
use domain::career::saga::GuardianProfileSaga;
use domain::chats::model::NewMessage;
use domain::chats::saga::ChatSyncSaga;
use domain::inventory::saga::EquipItemSaga;
use domain::lore::saga::LoreSaga;
use domain::voice_ai::conversation::ConversationSaga;
use domain::voice_ai::saga::VoiceCommandSaga;

use crate::bungie_character_client::{CharacterClient, CharacterSummary};

const AUTHORIZE_URL: &str = "https://www.bungie.net/en/OAuth/Authorize";
const TOKEN_URL: &str = "https://www.bungie.net/Platform/App/OAuth/Token/";
/// Bungie refresh tokens live ~90 days; used only when the response omits the field.
const DEFAULT_REFRESH_EXPIRES_SECS: i64 = 90 * 24 * 60 * 60;

/// Bungie OAuth client credentials (loaded from the environment by the composition root).
#[derive(Clone)]
pub struct BungieOAuthConfig {
    pub client_id: String,
    pub client_secret: String,
    pub api_key: String,
    /// When set (e.g. `ghostcompanion://auth`), the callback redirects here with the
    /// membership id so a native app's ASWebAuthenticationSession can complete the
    /// flow. When `None`, the callback returns JSON (web clients).
    pub mobile_callback: Option<String>,
    /// Allowed origins a browser may be redirected back to after login. The web
    /// app passes its return URL via `/auth/login?redirect=...`; the callback only
    /// honors it if it starts with one of these (prevents open redirects).
    pub web_callbacks: Vec<String>,
}

impl BungieOAuthConfig {
    /// Reads `BUNGIE_CLIENT_ID`, `BUNGIE_CLIENT_SECRET`, `BUNGIE_API_KEY`, the optional
    /// `GHOST_MOBILE_CALLBACK`, and the optional `GHOST_WEB_CALLBACK` allowlist
    /// (comma-separated origins).
    pub fn from_env() -> Result<Self, anyhow::Error> {
        let web_callbacks = std::env::var("GHOST_WEB_CALLBACK")
            .unwrap_or_default()
            .split(',')
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect();
        Ok(Self {
            client_id: std::env::var("BUNGIE_CLIENT_ID")?,
            client_secret: std::env::var("BUNGIE_CLIENT_SECRET")?,
            api_key: std::env::var("BUNGIE_API_KEY")?,
            mobile_callback: std::env::var("GHOST_MOBILE_CALLBACK")
                .ok()
                .filter(|s| !s.trim().is_empty()),
            web_callbacks,
        })
    }

    /// True when `url` is an allowed web return target (origin allowlisted).
    fn allows_web(&self, url: &str) -> bool {
        self.web_callbacks.iter().any(|origin| url.starts_with(origin))
    }
}

/// Shared state for the HTTP + WebSocket routes.
#[derive(Clone)]
pub struct AppState {
    pub auth_saga: Arc<OAuthSessionSaga>,
    pub oauth: BungieOAuthConfig,
    pub http: reqwest::Client,
    /// Voice command orchestrator; `None` when no LLM is configured (server still boots).
    pub voice_saga: Option<Arc<VoiceCommandSaga>>,
    /// Free-form conversational Ghost (lore + dossier grounded); `None` without an LLM.
    pub conversation_saga: Option<Arc<ConversationSaga>>,
    /// Inventory transaction engine (equip/transfer/vault/postmaster).
    pub equip_saga: Arc<EquipItemSaga>,
    /// Lore RAG retrieval; `None` when no embeddings provider is configured.
    pub lore_saga: Option<Arc<LoreSaga>>,
    /// Lists a signed-in user's characters (equip-target selection).
    pub character_client: Arc<CharacterClient>,
    /// Builds a Guardian's career dossier for personalization.
    pub profile_saga: Arc<GuardianProfileSaga>,
    /// Generic authenticated Bungie read passthrough (any Platform GET).
    pub bungie_api: Arc<crate::bungie_api_client::BungieApiClient>,
    /// Local manifest mirror for naming definition hashes (Triumphs, activities…).
    pub manifest_defs: Arc<db::ManifestDefinitionResolver>,
    /// Server-side conversation store so chats sync across the user's devices.
    pub chat_saga: Arc<ChatSyncSaga>,
    /// Mints/verifies session tokens (the authenticated owner of a request).
    pub session: Arc<dyn SessionAuthority>,
    /// When true, requests MUST carry a valid session — the `membership_id`
    /// parameter dev fallback is disabled. Set in production.
    pub require_auth: bool,
    /// Read access to the lore corpus for the browsable Codex.
    pub lore_library: Arc<db::LoreLibrary>,
    /// Optional shared dev token gating `/ws/voice`. When `None`, the socket is
    /// open locally. TODO: replace with real Bungie-session/JWT validation once
    /// session minting exists (Phase 4B currently returns the membership id only).
    pub ws_dev_token: Option<String>,
}

/// Session lifetime: how long a minted token stays valid.
const SESSION_TTL_DAYS: i64 = 30;

impl AppState {
    /// Resolves the authenticated owner of a request. A valid `Authorization:
    /// Bearer <session>` always wins. Otherwise, only in dev (`require_auth ==
    /// false`) do we fall back to a client-supplied `membership_id` claim;
    /// in production a missing/invalid session is a 401.
    pub fn resolve_owner(
        &self,
        headers: &HeaderMap,
        claimed: Option<&str>,
    ) -> Result<BungieMembershipId, AppError> {
        if let Some(token) = bearer_token(headers) {
            let session = self
                .session
                .verify(&token)
                .map_err(|_| AppError::unauthorized("invalid or expired session"))?;
            return Ok(session.membership_id);
        }
        if !self.require_auth {
            if let Some(id) = claimed.map(str::trim).filter(|s| !s.is_empty()) {
                return BungieMembershipId::new(id.to_string())
                    .map_err(AppError::unauthorized);
            }
        }
        Err(AppError::unauthorized("authentication required"))
    }
}

/// Extracts a bearer token from the `Authorization` header, if present.
fn bearer_token(headers: &HeaderMap) -> Option<String> {
    let value = headers.get(axum::http::header::AUTHORIZATION)?.to_str().ok()?;
    value
        .strip_prefix("Bearer ")
        .or_else(|| value.strip_prefix("bearer "))
        .map(|t| t.trim().to_string())
}

/// Mounts the auth routes onto a router using the provided state.
pub fn auth_router(state: AppState) -> Router {
    Router::new()
        .route("/auth/login", get(login))
        .route("/auth/callback", get(callback))
        .route("/characters", get(characters))
        .route("/profile/summary", get(profile_summary))
        .route("/activity/summary", get(activity_summary))
        .route("/bungie", get(bungie_passthrough))
        .route("/manifest/define", get(manifest_define))
        .route(
            "/conversations",
            get(list_conversations).post(create_conversation),
        )
        .route(
            "/conversations/:id",
            get(get_conversation)
                .patch(rename_conversation)
                .delete(delete_conversation),
        )
        .route("/conversations/:id/messages", axum::routing::post(append_message))
        .route("/chat", axum::routing::post(chat))
        .route("/lore", get(lore))
        .route("/lore/categories", get(lore_categories))
        .route("/lore/browse", get(lore_browse))
        .route("/lore/search", get(lore_search))
        .route("/lore/random", get(lore_random))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
struct RandomQuery {
    n: Option<i64>,
}

/// `GET /lore/random?n=` — random entries for lore discovery.
async fn lore_random(
    State(state): State<AppState>,
    Query(params): Query<RandomQuery>,
) -> Result<Json<Vec<db::LoreEntry>>, AppError> {
    let n = params.n.unwrap_or(1).clamp(1, 10);
    Ok(Json(state.lore_library.random(n).await?))
}

/// `GET /lore/categories` — Codex index: categories with entry counts.
async fn lore_categories(
    State(state): State<AppState>,
) -> Result<Json<Vec<db::LoreCategory>>, AppError> {
    Ok(Json(state.lore_library.categories().await?))
}

#[derive(Debug, Deserialize)]
struct BrowseQuery {
    category: String,
}

/// `GET /lore/browse?category=...` — entries within a category.
async fn lore_browse(
    State(state): State<AppState>,
    Query(params): Query<BrowseQuery>,
) -> Result<Json<Vec<db::LoreEntry>>, AppError> {
    Ok(Json(state.lore_library.browse(&params.category, 200).await?))
}

/// `GET /lore/search?q=...` — structured (entry-level) lore search.
async fn lore_search(
    State(state): State<AppState>,
    Query(params): Query<LoreQuery>,
) -> Result<Json<Vec<db::LoreEntry>>, AppError> {
    Ok(Json(state.lore_library.search(&params.q, 25).await?))
}

#[derive(Debug, Deserialize)]
struct MembershipQuery {
    membership_id: Option<String>,
}

/// `GET /profile/summary` — the authenticated Guardian's career dossier.
async fn profile_summary(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(params): Query<MembershipQuery>,
) -> Result<Json<serde_json::Value>, AppError> {
    let membership = state.resolve_owner(&headers, params.membership_id.as_deref())?;
    let summary = match state.profile_saga.summarize(&membership).await {
        Ok(dossier) => dossier,
        Err(message) => message,
    };
    Ok(Json(json!({ "summary": summary })))
}

/// `GET /activity/summary` — the authenticated Guardian's recent activity
/// history: what they played, when, completion, and the fireteam (D2 + D1).
/// Includes a natural-language narrative for display.
async fn activity_summary(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(params): Query<MembershipQuery>,
) -> Result<Json<serde_json::Value>, AppError> {
    let membership = state.resolve_owner(&headers, params.membership_id.as_deref())?;
    let summary = state.profile_saga.activity(&membership).await;
    Ok(Json(json!({
        "narrative": summary.narrative(),
        "recent": summary.recent,
    })))
}

// --- Cross-device chat sync ------------------------------------------------
//
// Conversations live server-side keyed by the owner (Bungie membership id), so
// they follow the user across devices. For now `membership_id` arrives as a
// parameter (the existing dev auth seam); the security pass will derive the
// owner from a validated session instead. The store already scopes every query
// by owner, so a real session id slots straight in.

#[derive(Debug, Deserialize)]
struct OwnerQuery {
    /// Dev fallback only; ignored when a session bearer is present / required.
    membership_id: Option<String>,
}

/// `GET /conversations` — the authenticated owner's thread list.
async fn list_conversations(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(params): Query<OwnerQuery>,
) -> Result<Json<serde_json::Value>, AppError> {
    let owner = state.resolve_owner(&headers, params.membership_id.as_deref())?;
    let threads = state.chat_saga.list(&owner.0).await?;
    Ok(Json(json!({ "threads": threads })))
}

#[derive(Debug, Deserialize)]
struct CreateConversation {
    membership_id: Option<String>,
    title: Option<String>,
}

/// `POST /conversations` — create a new thread for the owner.
async fn create_conversation(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(req): Json<CreateConversation>,
) -> Result<Json<serde_json::Value>, AppError> {
    let owner = state.resolve_owner(&headers, req.membership_id.as_deref())?;
    let thread = state.chat_saga.create(&owner.0, req.title.as_deref()).await?;
    Ok(Json(json!({ "thread": thread })))
}

/// `GET /conversations/{id}` — a thread with its messages.
async fn get_conversation(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(id): Path<String>,
    Query(params): Query<OwnerQuery>,
) -> Result<Response, AppError> {
    let owner = state.resolve_owner(&headers, params.membership_id.as_deref())?;
    match state.chat_saga.get(&owner.0, &id).await? {
        Some(thread) => Ok(Json(json!({ "thread": thread })).into_response()),
        None => Ok((StatusCode::NOT_FOUND, "conversation not found").into_response()),
    }
}

#[derive(Debug, Deserialize)]
struct AppendMessage {
    membership_id: Option<String>,
    role: String,
    text: String,
    intent: Option<String>,
}

/// `POST /conversations/{id}/messages` — append a message to a thread.
async fn append_message(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(id): Path<String>,
    Json(req): Json<AppendMessage>,
) -> Result<Response, AppError> {
    let owner = state.resolve_owner(&headers, req.membership_id.as_deref())?;
    let message = NewMessage::new(req.role, req.text, req.intent);
    match state.chat_saga.append(&owner.0, &id, message).await? {
        Some(stored) => Ok(Json(json!({ "message": stored })).into_response()),
        None => Ok((StatusCode::NOT_FOUND, "conversation not found").into_response()),
    }
}

#[derive(Debug, Deserialize)]
struct RenameConversation {
    membership_id: Option<String>,
    title: String,
}

/// `PATCH /conversations/{id}` — rename a thread.
async fn rename_conversation(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(id): Path<String>,
    Json(req): Json<RenameConversation>,
) -> Result<Json<serde_json::Value>, AppError> {
    let owner = state.resolve_owner(&headers, req.membership_id.as_deref())?;
    state.chat_saga.rename(&owner.0, &id, &req.title).await?;
    Ok(Json(json!({ "ok": true })))
}

/// `DELETE /conversations/{id}` — delete a thread.
async fn delete_conversation(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(id): Path<String>,
    Query(params): Query<OwnerQuery>,
) -> Result<Json<serde_json::Value>, AppError> {
    let owner = state.resolve_owner(&headers, params.membership_id.as_deref())?;
    state.chat_saga.delete(&owner.0, &id).await?;
    Ok(Json(json!({ "ok": true })))
}

#[derive(Debug, Deserialize)]
struct DefineQuery {
    kind: String,
    hash: i64,
}

/// `GET /manifest/define?kind=record&hash=...` — resolve a definition hash to its
/// name + description from the local manifest mirror (public; no game data).
async fn manifest_define(
    State(state): State<AppState>,
    Query(params): Query<DefineQuery>,
) -> Result<Response, AppError> {
    match state.manifest_defs.define(&params.kind, params.hash).await {
        Some(entry) => Ok(Json(entry).into_response()),
        None => Ok((StatusCode::NOT_FOUND, "definition not found").into_response()),
    }
}

#[derive(Debug, Deserialize)]
struct BungiePassthroughQuery {
    /// A Bungie Platform path, e.g. `/Platform/Destiny2/3/Profile/123/?components=200,900`.
    path: String,
    /// When present, the Guardian's OAuth token is attached for authed components.
    membership_id: Option<String>,
}

/// `GET /bungie?path=...&membership_id=...` — generic read passthrough to any
/// Bungie Platform endpoint (D2 + D1). Read-only and path-allowlisted. This lets
/// the Ghost reach any game data the Guardian is authorized for without a
/// bespoke route per endpoint.
async fn bungie_passthrough(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(params): Query<BungiePassthroughQuery>,
) -> Result<Json<serde_json::Value>, AppError> {
    // Reads are authenticated as the owner so a user only sees their own data.
    let owner = state.resolve_owner(&headers, params.membership_id.as_deref())?;
    let body = state.bungie_api.get(Some(&owner), &params.path).await?;
    Ok(Json(body))
}

#[derive(Debug, Deserialize)]
struct ChatRequest {
    message: String,
    /// Optional: when present, the reply is grounded in this Guardian's career +
    /// activity dossier so the Ghost speaks to what they've actually done.
    membership_id: Option<String>,
    /// Optional synced thread id. When present (with a membership), the Guardian
    /// message and the Ghost's reply are persisted so the conversation syncs
    /// across the user's devices.
    conversation_id: Option<String>,
    /// The active character to target for any gear changes (equip/transfer). When
    /// present (with a membership), the Ghost can do quick swaps from chat.
    character_id: Option<String>,
}

/// `POST /chat` — free-form conversation with the Ghost. Body:
/// `{ "message": "who is the Witness?", "membership_id": "..." }`. The reply is
/// grounded in lore RAG and (when `membership_id` is given) the player's dossier.
async fn chat(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(req): Json<ChatRequest>,
) -> Result<Json<serde_json::Value>, AppError> {
    let Some(conversation) = &state.conversation_saga else {
        return Ok(Json(json!({
            "reply": "The Ghost's voice is offline — no language model is configured.",
        })));
    };

    // Resolve the Guardian (when authenticated): used for the dossier context and
    // to bind the live-data tool. Anonymous chat (no auth, dev) is still allowed —
    // it just isn't personalized or persisted.
    let membership = state.resolve_owner(&headers, req.membership_id.as_deref()).ok();

    let context: Option<String> = match &membership {
        Some(m) => state.profile_saga.full_context(m).await,
        None => None,
    };

    let mut executor = crate::bungie_api_client::BungieToolExecutor::new(
        state.bungie_api.clone(),
        membership.clone(),
    )
    .with_definitions(state.manifest_defs.clone());
    // Enable quick gear changes when we know the active character.
    if membership.is_some() && req.character_id.is_some() {
        executor = executor.with_writes(state.equip_saga.clone(), req.character_id.clone());
    }

    let reply = match conversation
        .converse_with_tools(&req.message, context.as_deref(), Some(&executor))
        .await
    {
        Ok(reply) => reply,
        Err(_) => "The Ghost faltered reaching for an answer. Try again in a moment.".to_string(),
    };

    // Persist the turn to the synced thread when authenticated and one is given.
    if let (Some(owner), Some(thread_id)) = (&membership, req.conversation_id.as_deref()) {
        let _ = state
            .chat_saga
            .append(&owner.0, thread_id, NewMessage::new("guardian", &req.message, None))
            .await;
        let _ = state
            .chat_saga
            .append(
                &owner.0,
                thread_id,
                NewMessage::new("ghost", &reply, Some("conversation".to_string())),
            )
            .await;
    }

    Ok(Json(json!({ "reply": reply })))
}

#[derive(Debug, Deserialize)]
struct LoreQuery {
    q: String,
}

/// `GET /lore?q=...` — direct lore lookup (no LLM intent parsing required).
/// Works against the curated seed and/or manifest lore via the RAG pipeline.
async fn lore(
    State(state): State<AppState>,
    Query(params): Query<LoreQuery>,
) -> Result<Json<serde_json::Value>, AppError> {
    let Some(lore_saga) = &state.lore_saga else {
        return Ok(Json(json!({ "topic": params.q, "context": "Lore is not configured." })));
    };
    let context = match lore_saga.process_lore_query(&params.q).await {
        Ok(found) => found,
        Err(message) => message,
    };
    Ok(Json(json!({ "topic": params.q, "context": context })))
}

#[derive(Debug, Deserialize)]
struct CharactersQuery {
    membership_id: Option<String>,
}

/// `GET /characters` — the authenticated user's Destiny characters.
async fn characters(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(params): Query<CharactersQuery>,
) -> Result<Json<Vec<CharacterSummary>>, AppError> {
    let membership = state.resolve_owner(&headers, params.membership_id.as_deref())?;
    let characters = state.character_client.list_characters(&membership).await?;
    Ok(Json(characters))
}

#[derive(Debug, Deserialize)]
struct LoginQuery {
    /// Web SPA return URL; round-tripped via OAuth `state` if allowlisted.
    redirect: Option<String>,
}

/// `GET /auth/login` — send the user to Bungie's consent screen.
async fn login(State(state): State<AppState>, Query(params): Query<LoginQuery>) -> Redirect {
    let mut url = format!(
        "{AUTHORIZE_URL}?client_id={}&response_type=code",
        state.oauth.client_id
    );
    if let Some(redirect) = params.redirect.filter(|r| state.oauth.allows_web(r)) {
        url.push_str(&format!("&state={}", urlencoding::encode(&redirect)));
    }
    Redirect::temporary(&url)
}

#[derive(Debug, Deserialize)]
struct CallbackQuery {
    code: String,
    /// Echoed back from `/auth/login` — the web return URL, if any.
    state: Option<String>,
}

/// `GET /auth/callback?code=...` — exchange the code and run the login saga.
/// Redirects to the web return URL or the native app scheme; otherwise JSON.
async fn callback(
    State(state): State<AppState>,
    Query(params): Query<CallbackQuery>,
) -> Result<Response, AppError> {
    let token = exchange_code_for_token(&state, &params.code).await?;
    let membership_id = state.auth_saga.process_new_login(token).await?;

    // Mint a signed session the client presents on subsequent requests.
    let session = Session::new(
        membership_id.clone(),
        Utc::now() + Duration::days(SESSION_TTL_DAYS),
    );
    let session_token = state.session.mint(&session)?;
    let session_q = urlencoding::encode(&session_token);

    // 1. Web flow: redirect back to the (allowlisted) SPA return URL.
    if let Some(redirect) = params.state.filter(|r| state.oauth.allows_web(r)) {
        let sep = if redirect.contains('?') { '&' } else { '?' };
        let target = format!(
            "{redirect}{sep}membership_id={}&session={session_q}",
            membership_id.0
        );
        return Ok(Redirect::to(&target).into_response());
    }

    // 2. Native flow: redirect to the app URL scheme.
    if let Some(scheme) = &state.oauth.mobile_callback {
        let sep = if scheme.contains('?') { '&' } else { '?' };
        let target = format!(
            "{scheme}{sep}membership_id={}&session={session_q}",
            membership_id.0
        );
        return Ok(Redirect::to(&target).into_response());
    }

    // 3. Fallback: JSON.
    Ok(Json(json!({ "membership_id": membership_id.0, "session": session_token })).into_response())
}

#[derive(Debug, Deserialize)]
struct TokenExchangeResponse {
    access_token: String,
    refresh_token: String,
    expires_in: i64,
    refresh_expires_in: Option<i64>,
}

/// Exchanges an authorization `code` for a `BungieOAuthToken` via Bungie's token endpoint.
async fn exchange_code_for_token(
    state: &AppState,
    code: &str,
) -> Result<BungieOAuthToken, anyhow::Error> {
    let form = [
        ("grant_type", "authorization_code"),
        ("code", code),
        ("client_id", state.oauth.client_id.as_str()),
        ("client_secret", state.oauth.client_secret.as_str()),
    ];

    let resp: TokenExchangeResponse = state
        .http
        .post(TOKEN_URL)
        .header("X-API-Key", &state.oauth.api_key)
        .form(&form)
        .send()
        .await?
        .error_for_status()?
        .json()
        .await?;

    let now = Utc::now();
    let refresh_secs = resp
        .refresh_expires_in
        .unwrap_or(DEFAULT_REFRESH_EXPIRES_SECS);

    Ok(BungieOAuthToken {
        access_token: resp.access_token,
        refresh_token: resp.refresh_token,
        expires_at: now + Duration::seconds(resp.expires_in),
        refresh_expires_at: now + Duration::seconds(refresh_secs),
    })
}

/// A route error carrying the client-facing status + message. Internal errors
/// are logged but never leaked (they surface as a generic 500); explicit cases
/// like 401 carry a safe public message.
pub struct AppError {
    status: StatusCode,
    message: String,
    /// Logged server-side only (for 500s); never sent to the client.
    source: Option<anyhow::Error>,
}

impl AppError {
    /// A 401 with a safe, client-facing message.
    pub fn unauthorized(message: impl Into<String>) -> Self {
        Self {
            status: StatusCode::UNAUTHORIZED,
            message: message.into(),
            source: None,
        }
    }
}

impl<E> From<E> for AppError
where
    E: Into<anyhow::Error>,
{
    fn from(err: E) -> Self {
        Self {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            message: "internal error".to_string(),
            source: Some(err.into()),
        }
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        if let Some(source) = &self.source {
            tracing::error!(error = %source, "route failed");
        }
        (self.status, self.message).into_response()
    }
}
