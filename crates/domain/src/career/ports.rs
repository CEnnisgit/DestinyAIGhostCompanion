use async_trait::async_trait;

use crate::auth::membership::BungieMembershipId;
use super::profile::GuardianProfile;

/// Secondary Port (Driven): reads a Guardian's career stats from Bungie so the
/// Ghost can personalize itself to the player.
#[async_trait]
pub trait CareerStatsPort: Send + Sync {
    async fn fetch_profile(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<GuardianProfile, anyhow::Error>;
}
