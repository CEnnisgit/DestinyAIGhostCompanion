use std::sync::Arc;

use crate::auth::membership::BungieMembershipId;
use super::ports::CareerStatsPort;
use super::profile::GuardianProfile;

/// Builds a Guardian's career dossier — used for the app greeting and to
/// personalize the Ghost's voice prompt.
pub struct GuardianProfileSaga {
    stats_port: Arc<dyn CareerStatsPort>,
}

impl GuardianProfileSaga {
    pub fn new(stats_port: Arc<dyn CareerStatsPort>) -> Self {
        Self { stats_port }
    }

    /// Returns the raw profile.
    pub async fn profile(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<GuardianProfile, anyhow::Error> {
        self.stats_port.fetch_profile(membership_id).await
    }

    /// Returns the personalized dossier line, or a graceful fallback message.
    pub async fn summarize(&self, membership_id: &BungieMembershipId) -> Result<String, String> {
        match self.stats_port.fetch_profile(membership_id).await {
            Ok(profile) => Ok(profile.dossier()),
            Err(_) => Err("I couldn't reach your Guardian records just now.".to_string()),
        }
    }
}
