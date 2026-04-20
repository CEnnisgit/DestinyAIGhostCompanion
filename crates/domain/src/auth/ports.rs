use async_trait::async_trait;
use crate::auth::membership::BungieMembershipId;
use crate::auth::token::BungieOAuthToken;

/// Secondary Port (Driven): Allows the Auth domain to persist tokens securely
#[async_trait]
pub trait TokenStoragePort: Send + Sync {
    async fn save_token(&self, membership_id: &BungieMembershipId, token: &BungieOAuthToken) -> Result<(), anyhow::Error>;
    async fn get_token(&self, membership_id: &BungieMembershipId) -> Result<Option<BungieOAuthToken>, anyhow::Error>;
}

/// Secondary Port (Driven): Allows the Auth domain to fetch canonical user IDs from Bungie
#[async_trait]
pub trait BungieIdentityProviderPort: Send + Sync {
    /// Takes a newly negotiated OAuth token, hits Bungie, and returns the canonical Destiny user profile
    async fn resolve_user_identity(&self, token: &BungieOAuthToken) -> Result<BungieMembershipId, anyhow::Error>;
}
