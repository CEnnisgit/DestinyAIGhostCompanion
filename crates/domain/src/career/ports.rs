use async_trait::async_trait;

use crate::auth::membership::BungieMembershipId;
use super::activity::ActivitySummary;
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

/// Secondary Port (Driven): reads a Guardian's recent activity history — what
/// they played, when, whether they completed it, and who was in the fireteam.
/// Implementations span Destiny 2 and the legacy Destiny 1 endpoints.
#[async_trait]
pub trait ActivityHistoryPort: Send + Sync {
    async fn fetch_recent_activities(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<ActivitySummary, anyhow::Error>;
}
