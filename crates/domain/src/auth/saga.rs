use std::sync::Arc;
use crate::auth::token::BungieOAuthToken;
use crate::auth::membership::BungieMembershipId;
use crate::auth::ports::{TokenStoragePort, BungieIdentityProviderPort};

/// The Orchestrator Aggregate that handles the SSO flow
pub struct OAuthSessionSaga {
    token_storage: Arc<dyn TokenStoragePort>,
    bungie_identity: Arc<dyn BungieIdentityProviderPort>,
}

impl OAuthSessionSaga {
    pub fn new(
        token_storage: Arc<dyn TokenStoragePort>,
        bungie_identity: Arc<dyn BungieIdentityProviderPort>,
    ) -> Self {
        Self {
            token_storage,
            bungie_identity,
        }
    }

    /// Handles a successfully negotiated OAuth token from the external API route.
    /// It verifies the token against Bungie to definitively find out WHO this token belongs to,
    /// then persists it locally for AuthZ.
    pub async fn process_new_login(&self, new_token: BungieOAuthToken) -> Result<BungieMembershipId, anyhow::Error> {
        // 1. Resolve Identity via Secondary Port (Hitting Bungie APIs)
        let membership_id = self.bungie_identity.resolve_user_identity(&new_token).await?;

        // 2. Persist the token to our DB (AuthZ binding) via Secondary Port
        self.token_storage.save_token(&membership_id, &new_token).await?;

        // 3. Return the ID back to the Primary Port (so `crates/api` can mint a JWT for this ID)
        Ok(membership_id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bungie_membership_id_rejects_empty() {
        let result = BungieMembershipId::new("   ");
        assert!(result.is_err(), "Should reject empty string");

        let result = BungieMembershipId::new("");
        assert!(result.is_err(), "Should reject empty string");

        let result = BungieMembershipId::new("12345");
        assert!(result.is_ok(), "Should accept valid ID");
        assert_eq!(result.unwrap().0, "12345");
    }
}
