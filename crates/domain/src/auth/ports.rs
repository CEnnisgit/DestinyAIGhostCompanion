use async_trait::async_trait;
use chrono::{DateTime, Utc};
use crate::auth::membership::BungieMembershipId;
use crate::auth::session::Session;
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

/// Secondary Port (Driven): mints and verifies tamper-proof session tokens, so a
/// request can prove which Guardian it belongs to without re-running OAuth. The
/// crypto lives in an adapter; the domain only depends on this contract.
pub trait SessionAuthority: Send + Sync {
    /// Serializes a `Session` into an opaque, signed token string.
    fn mint(&self, session: &Session) -> Result<String, anyhow::Error>;
    /// Verifies a token's signature and expiry, returning the `Session` it proves.
    fn verify(&self, token: &str) -> Result<Session, anyhow::Error>;
}

/// Secondary Port (Driven): stateless session tokens can't be deleted, so
/// revocation is a per-user cutoff — any session issued before it is invalid.
/// Signing out sets the cutoff to "now", invalidating that user's tokens.
#[async_trait]
pub trait SessionRevocationPort: Send + Sync {
    /// The revocation cutoff for the user, if one has been set.
    async fn revoked_before(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<Option<DateTime<Utc>>, anyhow::Error>;

    /// Revokes every session for the user issued before `cutoff`.
    async fn revoke_before(
        &self,
        membership_id: &BungieMembershipId,
        cutoff: DateTime<Utc>,
    ) -> Result<(), anyhow::Error>;
}
