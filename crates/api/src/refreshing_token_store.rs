//! A `TokenStoragePort` decorator that keeps Bungie access tokens fresh.
//!
//! Bungie access tokens expire in ~1 hour, but our sessions last far longer.
//! Without refresh, every live-data call would start failing ~1 hour after
//! login. This wraps the real (Postgres) token store: on `get_token`, if the
//! stored access token is expired (or about to be), it uses the refresh token to
//! mint a new one from Bungie, persists it, and returns the fresh token — so the
//! five Bungie clients keep working unchanged. When the *refresh* token itself
//! has expired, we return what we have and let the call fail, prompting re-login.

use std::sync::Arc;

use anyhow::Context;
use async_trait::async_trait;
use chrono::{DateTime, Duration, Utc};
use serde::Deserialize;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;
use domain::auth::token::BungieOAuthToken;

const TOKEN_URL: &str = "https://www.bungie.net/Platform/App/OAuth/Token/";
/// Refresh a little early so a token doesn't expire mid-request.
const EXPIRY_BUFFER_SECS: i64 = 120;
/// Bungie refresh tokens live ~90 days; used only if the response omits the field.
const DEFAULT_REFRESH_EXPIRES_SECS: i64 = 90 * 24 * 60 * 60;

pub struct RefreshingTokenStore {
    inner: Arc<dyn TokenStoragePort>,
    http: reqwest::Client,
    client_id: String,
    client_secret: String,
    api_key: String,
}

impl RefreshingTokenStore {
    pub fn new(
        inner: Arc<dyn TokenStoragePort>,
        http: reqwest::Client,
        client_id: impl Into<String>,
        client_secret: impl Into<String>,
        api_key: impl Into<String>,
    ) -> Self {
        Self {
            inner,
            http,
            client_id: client_id.into(),
            client_secret: client_secret.into(),
            api_key: api_key.into(),
        }
    }

    /// Exchanges a refresh token for a fresh `BungieOAuthToken`.
    async fn refresh(&self, refresh_token: &str) -> Result<BungieOAuthToken, anyhow::Error> {
        let form = [
            ("grant_type", "refresh_token"),
            ("refresh_token", refresh_token),
            ("client_id", self.client_id.as_str()),
            ("client_secret", self.client_secret.as_str()),
        ];

        let resp: RefreshResponse = self
            .http
            .post(TOKEN_URL)
            .header("X-API-Key", &self.api_key)
            .form(&form)
            .send()
            .await
            .context("refreshing Bungie token")?
            .error_for_status()
            .context("Bungie token refresh returned an error status")?
            .json()
            .await
            .context("decoding Bungie token refresh response")?;

        let now = Utc::now();
        let refresh_secs = resp.refresh_expires_in.unwrap_or(DEFAULT_REFRESH_EXPIRES_SECS);
        Ok(BungieOAuthToken {
            access_token: resp.access_token,
            refresh_token: resp.refresh_token,
            expires_at: now + Duration::seconds(resp.expires_in),
            refresh_expires_at: now + Duration::seconds(refresh_secs),
        })
    }
}

#[async_trait]
impl TokenStoragePort for RefreshingTokenStore {
    async fn save_token(
        &self,
        membership_id: &BungieMembershipId,
        token: &BungieOAuthToken,
    ) -> Result<(), anyhow::Error> {
        self.inner.save_token(membership_id, token).await
    }

    async fn get_token(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<Option<BungieOAuthToken>, anyhow::Error> {
        let Some(token) = self.inner.get_token(membership_id).await? else {
            return Ok(None);
        };

        let now = Utc::now();
        // Still valid (with a buffer): use as-is.
        if !needs_refresh(&token, now) {
            return Ok(Some(token));
        }
        // Access expired but the refresh token is dead too: nothing we can do.
        if now >= token.refresh_expires_at {
            tracing::warn!("Bungie refresh token expired — user must sign in again");
            return Ok(Some(token));
        }

        // Refresh, persist, and return the fresh token. On failure, fall back to
        // the stale token so a transient refresh error isn't fatal.
        match self.refresh(&token.refresh_token).await {
            Ok(fresh) => {
                self.inner.save_token(membership_id, &fresh).await?;
                tracing::info!("refreshed Bungie access token");
                Ok(Some(fresh))
            }
            Err(err) => {
                tracing::warn!(error = %err, "Bungie token refresh failed; using stale token");
                Ok(Some(token))
            }
        }
    }
}

/// True when the access token is expired or within the early-refresh buffer.
fn needs_refresh(token: &BungieOAuthToken, now: DateTime<Utc>) -> bool {
    now + Duration::seconds(EXPIRY_BUFFER_SECS) >= token.expires_at
}

#[derive(Debug, Deserialize)]
struct RefreshResponse {
    access_token: String,
    refresh_token: String,
    expires_in: i64,
    refresh_expires_in: Option<i64>,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn token(expires_in_secs: i64) -> BungieOAuthToken {
        let now = Utc::now();
        BungieOAuthToken {
            access_token: "a".into(),
            refresh_token: "r".into(),
            expires_at: now + Duration::seconds(expires_in_secs),
            refresh_expires_at: now + Duration::days(90),
        }
    }

    #[test]
    fn fresh_token_does_not_need_refresh() {
        assert!(!needs_refresh(&token(3600), Utc::now()));
    }

    #[test]
    fn expired_token_needs_refresh() {
        assert!(needs_refresh(&token(-10), Utc::now()));
    }

    #[test]
    fn near_expiry_token_needs_refresh_within_buffer() {
        // 60s left, buffer is 120s → should refresh early.
        assert!(needs_refresh(&token(60), Utc::now()));
    }
}
