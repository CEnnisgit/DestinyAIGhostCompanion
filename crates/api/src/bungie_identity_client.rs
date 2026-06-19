//! Phase 4B: reqwest adapter for the auth domain's `BungieIdentityProviderPort`.
//!
//! Given a freshly negotiated OAuth token, asks Bungie who the token belongs to
//! and returns the canonical `BungieMembershipId`.

use anyhow::{anyhow, Context};
use async_trait::async_trait;
use serde::Deserialize;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::BungieIdentityProviderPort;
use domain::auth::token::BungieOAuthToken;

const MEMBERSHIPS_URL: &str =
    "https://www.bungie.net/Platform/User/GetMembershipsForCurrentUser/";

/// Concrete `BungieIdentityProviderPort` backed by `reqwest`.
pub struct BungieIdentityClient {
    http: reqwest::Client,
    api_key: String,
}

impl BungieIdentityClient {
    pub fn new(http: reqwest::Client, api_key: impl Into<String>) -> Self {
        Self {
            http,
            api_key: api_key.into(),
        }
    }
}

#[derive(Debug, Deserialize)]
struct MembershipsEnvelope {
    #[serde(rename = "Response")]
    response: MembershipsResponse,
}

#[derive(Debug, Deserialize)]
struct MembershipsResponse {
    #[serde(rename = "primaryMembershipId")]
    primary_membership_id: Option<String>,
    #[serde(rename = "destinyMemberships", default)]
    destiny_memberships: Vec<DestinyMembership>,
}

#[derive(Debug, Deserialize)]
struct DestinyMembership {
    #[serde(rename = "membershipId")]
    membership_id: String,
}

#[async_trait]
impl BungieIdentityProviderPort for BungieIdentityClient {
    async fn resolve_user_identity(
        &self,
        token: &BungieOAuthToken,
    ) -> Result<BungieMembershipId, anyhow::Error> {
        let envelope: MembershipsEnvelope = self
            .http
            .get(MEMBERSHIPS_URL)
            .header("Authorization", format!("Bearer {}", token.access_token))
            .header("X-API-Key", &self.api_key)
            .send()
            .await
            .context("calling Bungie GetMembershipsForCurrentUser")?
            .error_for_status()
            .context("Bungie GetMembershipsForCurrentUser returned an error status")?
            .json()
            .await
            .context("decoding Bungie memberships response")?;

        let destiny_ids = envelope
            .response
            .destiny_memberships
            .into_iter()
            .map(|m| m.membership_id)
            .collect();

        let id = select_membership_id(envelope.response.primary_membership_id, destiny_ids)
            .ok_or_else(|| anyhow!("Bungie returned no Destiny memberships for this user"))?;

        BungieMembershipId::new(id).map_err(|e| anyhow!(e))
    }
}

/// Picks the canonical membership id: prefer Bungie's designated primary
/// (cross-save) membership, otherwise fall back to the first Destiny membership.
fn select_membership_id(primary: Option<String>, destiny_ids: Vec<String>) -> Option<String> {
    primary
        .filter(|s| !s.trim().is_empty())
        .or_else(|| destiny_ids.into_iter().next())
}

#[cfg(test)]
mod tests {
    use super::select_membership_id;

    #[test]
    fn prefers_primary_membership() {
        let chosen = select_membership_id(
            Some("4611686018467260000".to_string()),
            vec!["111".to_string(), "222".to_string()],
        );
        assert_eq!(chosen.as_deref(), Some("4611686018467260000"));
    }

    #[test]
    fn falls_back_to_first_destiny_membership_when_primary_absent() {
        let chosen = select_membership_id(None, vec!["111".to_string(), "222".to_string()]);
        assert_eq!(chosen.as_deref(), Some("111"));
    }

    #[test]
    fn ignores_blank_primary() {
        let chosen =
            select_membership_id(Some("   ".to_string()), vec!["333".to_string()]);
        assert_eq!(chosen.as_deref(), Some("333"));
    }

    #[test]
    fn none_when_no_memberships() {
        assert_eq!(select_membership_id(None, vec![]), None);
    }
}
