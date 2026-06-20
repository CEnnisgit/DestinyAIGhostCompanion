//! Phase 4B: Bungie OAuth2 callback routes (axum) — the driving (inbound) adapter.
//!
//! `/auth/login`   → redirect the Guardian to Bungie's consent screen.
//! `/auth/callback`→ exchange the returned code for tokens, then hand them to the
//!                   domain `OAuthSessionSaga` which resolves identity + persists.
//!
//! ADR-005: delegated authentication — no passwords, 100% Bungie OAuth2 SSO.

use std::sync::Arc;

use axum::{
    extract::{Query, State},
    response::{IntoResponse, Json, Redirect, Response},
    routing::get,
    Router,
};
use chrono::{Duration, Utc};
use serde::Deserialize;
use serde_json::json;

use domain::auth::membership::BungieMembershipId;
use domain::auth::saga::OAuthSessionSaga;
use domain::auth::token::BungieOAuthToken;
use domain::inventory::saga::EquipItemSaga;
use domain::lore::saga::LoreSaga;
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
    /// Inventory transaction engine (equip/transfer/vault/postmaster).
    pub equip_saga: Arc<EquipItemSaga>,
    /// Lore RAG retrieval; `None` when no embeddings provider is configured.
    pub lore_saga: Option<Arc<LoreSaga>>,
    /// Lists a signed-in user's characters (equip-target selection).
    pub character_client: Arc<CharacterClient>,
    /// Optional shared dev token gating `/ws/voice`. When `None`, the socket is
    /// open locally. TODO: replace with real Bungie-session/JWT validation once
    /// session minting exists (Phase 4B currently returns the membership id only).
    pub ws_dev_token: Option<String>,
}

/// Mounts the auth routes onto a router using the provided state.
pub fn auth_router(state: AppState) -> Router {
    Router::new()
        .route("/auth/login", get(login))
        .route("/auth/callback", get(callback))
        .route("/characters", get(characters))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
struct CharactersQuery {
    membership_id: String,
}

/// `GET /characters?membership_id=...` — the user's Destiny characters.
async fn characters(
    State(state): State<AppState>,
    Query(params): Query<CharactersQuery>,
) -> Result<Json<Vec<CharacterSummary>>, AppError> {
    let membership = BungieMembershipId::new(params.membership_id).map_err(|e| anyhow::anyhow!(e))?;
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

    // 1. Web flow: redirect back to the (allowlisted) SPA return URL.
    if let Some(redirect) = params.state.filter(|r| state.oauth.allows_web(r)) {
        let sep = if redirect.contains('?') { '&' } else { '?' };
        let target = format!("{redirect}{sep}membership_id={}", membership_id.0);
        return Ok(Redirect::to(&target).into_response());
    }

    // 2. Native flow: redirect to the app URL scheme.
    if let Some(scheme) = &state.oauth.mobile_callback {
        let sep = if scheme.contains('?') { '&' } else { '?' };
        let target = format!("{scheme}{sep}membership_id={}", membership_id.0);
        return Ok(Redirect::to(&target).into_response());
    }

    // 3. Fallback: JSON.
    Ok(Json(json!({ "membership_id": membership_id.0 })).into_response())
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

/// Maps domain/adapter errors to a 500 response without leaking internals to the client.
pub struct AppError(anyhow::Error);

impl<E> From<E> for AppError
where
    E: Into<anyhow::Error>,
{
    fn from(err: E) -> Self {
        Self(err.into())
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        tracing::error!(error = %self.0, "auth route failed");
        (
            axum::http::StatusCode::INTERNAL_SERVER_ERROR,
            "internal error",
        )
            .into_response()
    }
}
