use anyhow::{anyhow, Context};
use async_trait::async_trait;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::BungieIdentityProviderPort;
use domain::auth::token::BungieOAuthToken;

/// Adapter that implements [`BungieIdentityProviderPort`] by calling the
/// Bungie.net platform API to resolve the canonical Destiny membership ID
/// from an OAuth access token.
pub struct BungieIdentityClient {
    http_client: reqwest::Client,
    api_key: String,
}

impl BungieIdentityClient {
    pub fn new(http_client: reqwest::Client, api_key: String) -> Self {
        Self {
            http_client,
            api_key,
        }
    }
}

#[async_trait]
impl BungieIdentityProviderPort for BungieIdentityClient {
    async fn resolve_user_identity(
        &self,
        token: &BungieOAuthToken,
    ) -> Result<BungieMembershipId, anyhow::Error> {
        let response = self
            .http_client
            .get("https://www.bungie.net/Platform/User/GetMembershipsForCurrentUser/")
            .header("Authorization", format!("Bearer {}", token.access_token))
            .header("X-API-Key", &self.api_key)
            .send()
            .await
            .context("failed to call Bungie GetMembershipsForCurrentUser")?
            .error_for_status()
            .context("Bungie GetMembershipsForCurrentUser returned an error")?;

        let body: serde_json::Value = response
            .json()
            .await
            .context("failed to parse Bungie memberships response")?;

        let resp = body
            .get("Response")
            .ok_or_else(|| anyhow!("Bungie response missing 'Response' key"))?;

        // Prefer primaryMembershipId when present and non-empty.
        let id = resp
            .get("primaryMembershipId")
            .and_then(|v| v.as_str())
            .filter(|s| !s.is_empty())
            .or_else(|| {
                resp.get("destinyMemberships")
                    .and_then(|m| m.as_array())
                    .and_then(|arr| arr.first())
                    .and_then(|entry| entry.get("membershipId"))
                    .and_then(|v| v.as_str())
            })
            .ok_or_else(|| anyhow!("no membership ID found in Bungie response"))?;

        BungieMembershipId::new(id).map_err(|e| anyhow!(e))
    }
}
