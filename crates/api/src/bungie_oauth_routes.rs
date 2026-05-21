use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::{IntoResponse, Redirect},
    Json,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};

use domain::auth::token::BungieOAuthToken;

use crate::app_state::AppState;
use crate::auth_middleware::{mint_jwt, AuthUser};

// ── Request / Response types ────────────────────────────────────────────────

#[derive(Deserialize)]
pub struct CallbackParams {
    code: String,
}

/// Shape returned by Bungie's `/Platform/App/OAuth/Token/` endpoint.
#[derive(Deserialize)]
struct BungieTokenResponse {
    access_token: String,
    refresh_token: String,
    expires_in: i64,
    refresh_expires_in: i64,
}

#[derive(Serialize)]
struct AuthTokenPayload {
    membership_id: String,
    token: String,
}

// ── Handlers ────────────────────────────────────────────────────────────────

/// Redirect the user to the Bungie OAuth consent page.
pub async fn auth_login(State(state): State<AppState>) -> impl IntoResponse {
    let url = format!(
        "https://www.bungie.net/en/OAuth/Authorize?client_id={}&response_type=code",
        state.config.bungie_client_id,
    );
    Redirect::temporary(&url)
}

/// Handle the OAuth callback from Bungie.
///
/// Exchanges the authorization `code` for tokens, delegates identity resolution
/// and persistence to the domain saga, then mints a local JWT.
pub async fn auth_callback(
    State(state): State<AppState>,
    Query(params): Query<CallbackParams>,
) -> impl IntoResponse {
    match exchange_and_login(&state, &params.code).await {
        Ok(payload) => (StatusCode::OK, Json(serde_json::to_value(payload).unwrap())).into_response(),
        Err(e) => {
            tracing::error!(error = %e, "auth_callback failed");
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(serde_json::json!({ "error": e.to_string() })),
            )
                .into_response()
        }
    }
}

/// Refresh the stored Bungie OAuth tokens and re-mint the local JWT.
///
/// Requires a valid JWT (enforced by the [`AuthUser`] extractor).
pub async fn auth_refresh(
    State(state): State<AppState>,
    auth: AuthUser,
) -> impl IntoResponse {
    match refresh_and_mint(&state, &auth).await {
        Ok(payload) => (StatusCode::OK, Json(serde_json::to_value(payload).unwrap())).into_response(),
        Err(e) => {
            tracing::error!(error = %e, "auth_refresh failed");
            let status = if e.to_string().contains("no stored token") {
                StatusCode::UNAUTHORIZED
            } else {
                StatusCode::INTERNAL_SERVER_ERROR
            };
            (status, Json(serde_json::json!({ "error": e.to_string() }))).into_response()
        }
    }
}

/// Return the authenticated user's membership ID.
pub async fn auth_me(auth: AuthUser) -> impl IntoResponse {
    Json(serde_json::json!({ "membership_id": auth.membership_id.0 }))
}

// ── Private helpers ─────────────────────────────────────────────────────────

async fn exchange_and_login(
    state: &AppState,
    code: &str,
) -> Result<AuthTokenPayload, anyhow::Error> {
    let bungie_tokens: BungieTokenResponse = state
        .http_client
        .post("https://www.bungie.net/Platform/App/OAuth/Token/")
        .form(&[
            ("grant_type", "authorization_code"),
            ("code", code),
            ("client_id", &state.config.bungie_client_id),
            ("client_secret", &state.config.bungie_client_secret),
        ])
        .send()
        .await?
        .error_for_status()?
        .json()
        .await?;

    let now = Utc::now();
    let token = BungieOAuthToken {
        access_token: bungie_tokens.access_token,
        refresh_token: bungie_tokens.refresh_token,
        expires_at: now + chrono::TimeDelta::seconds(bungie_tokens.expires_in),
        refresh_expires_at: now + chrono::TimeDelta::seconds(bungie_tokens.refresh_expires_in),
    };

    let membership_id = state.auth_saga.process_new_login(token).await?;
    let jwt = mint_jwt(&membership_id, &state.config.jwt_secret)?;

    Ok(AuthTokenPayload {
        membership_id: membership_id.0,
        token: jwt,
    })
}

async fn refresh_and_mint(
    state: &AppState,
    auth: &AuthUser,
) -> Result<AuthTokenPayload, anyhow::Error> {
    let stored = state
        .token_storage
        .get_token(&auth.membership_id)
        .await?
        .ok_or_else(|| anyhow::anyhow!("no stored token for this user"))?;

    let bungie_tokens: BungieTokenResponse = state
        .http_client
        .post("https://www.bungie.net/Platform/App/OAuth/Token/")
        .form(&[
            ("grant_type", "refresh_token"),
            ("refresh_token", &stored.refresh_token),
            ("client_id", &state.config.bungie_client_id),
            ("client_secret", &state.config.bungie_client_secret),
        ])
        .send()
        .await?
        .error_for_status()?
        .json()
        .await?;

    let now = Utc::now();
    let new_token = BungieOAuthToken {
        access_token: bungie_tokens.access_token,
        refresh_token: bungie_tokens.refresh_token,
        expires_at: now + chrono::TimeDelta::seconds(bungie_tokens.expires_in),
        refresh_expires_at: now + chrono::TimeDelta::seconds(bungie_tokens.refresh_expires_in),
    };

    state
        .token_storage
        .save_token(&auth.membership_id, &new_token)
        .await?;

    let jwt = mint_jwt(&auth.membership_id, &state.config.jwt_secret)?;

    Ok(AuthTokenPayload {
        membership_id: auth.membership_id.0.clone(),
        token: jwt,
    })
}
