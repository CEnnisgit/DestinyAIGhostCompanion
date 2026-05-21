use axum::{
    extract::FromRequestParts,
    http::{StatusCode, header, request::Parts},
};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};

use domain::auth::membership::BungieMembershipId;

use crate::app_state::AppState;

// ── JWT Claims ──────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: usize,
}

// ── Extractor ───────────────────────────────────────────────────────────────

/// Axum extractor that validates a `Bearer` JWT and resolves a [`BungieMembershipId`].
///
/// Drop this into any handler signature to enforce authentication:
///
/// ```ignore
/// async fn protected(auth: AuthUser) -> impl IntoResponse { … }
/// ```
pub struct AuthUser {
    pub membership_id: BungieMembershipId,
}

impl FromRequestParts<AppState> for AuthUser {
    type Rejection = (StatusCode, axum::Json<serde_json::Value>);

    async fn from_request_parts(
        parts: &mut Parts,
        state: &AppState,
    ) -> Result<Self, Self::Rejection> {
        let auth_header = parts
            .headers
            .get(header::AUTHORIZATION)
            .and_then(|v| v.to_str().ok())
            .ok_or_else(|| unauthorized("missing Authorization header"))?;

        let token = auth_header
            .strip_prefix("Bearer ")
            .ok_or_else(|| unauthorized("Authorization header must start with 'Bearer '"))?;

        let key = DecodingKey::from_secret(state.config.jwt_secret.as_bytes());
        let mut validation = Validation::new(jsonwebtoken::Algorithm::HS256);
        validation.set_required_spec_claims(&["sub", "exp"]);

        let token_data = decode::<Claims>(token, &key, &validation)
            .map_err(|e| unauthorized(&format!("invalid token: {e}")))?;

        let membership_id = BungieMembershipId::new(token_data.claims.sub)
            .map_err(|e| unauthorized(&format!("invalid membership id in token: {e}")))?;

        Ok(Self { membership_id })
    }
}

// ── JWT minting ─────────────────────────────────────────────────────────────

/// Create a signed JWT with `sub` = membership id and a 1-hour expiry.
pub fn mint_jwt(membership_id: &BungieMembershipId, secret: &str) -> Result<String, anyhow::Error> {
    let exp = chrono::Utc::now()
        .checked_add_signed(chrono::TimeDelta::hours(1))
        .expect("valid timestamp")
        .timestamp() as usize;

    let claims = Claims {
        sub: membership_id.0.clone(),
        exp,
    };

    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )?;

    Ok(token)
}

// ── helpers ─────────────────────────────────────────────────────────────────

fn unauthorized(msg: &str) -> (StatusCode, axum::Json<serde_json::Value>) {
    (
        StatusCode::UNAUTHORIZED,
        axum::Json(serde_json::json!({ "error": msg })),
    )
}
