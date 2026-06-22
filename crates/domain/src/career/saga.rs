use std::sync::Arc;

use crate::auth::membership::BungieMembershipId;
use super::activity::ActivitySummary;
use super::ports::{ActivityHistoryPort, CareerStatsPort};
use super::profile::GuardianProfile;

/// Builds a Guardian's career dossier — used for the app greeting and to
/// personalize the Ghost's voice prompt. Optionally folds in recent activity
/// history (what they've played, when, and with whom) when an
/// [`ActivityHistoryPort`] is wired.
pub struct GuardianProfileSaga {
    stats_port: Arc<dyn CareerStatsPort>,
    activity_port: Option<Arc<dyn ActivityHistoryPort>>,
}

impl GuardianProfileSaga {
    pub fn new(stats_port: Arc<dyn CareerStatsPort>) -> Self {
        Self {
            stats_port,
            activity_port: None,
        }
    }

    /// Adds a recent-activity source so the dossier includes what the Guardian
    /// has actually done in-game (raid dates, fireteams, …).
    pub fn with_activity(mut self, activity_port: Arc<dyn ActivityHistoryPort>) -> Self {
        self.activity_port = Some(activity_port);
        self
    }

    /// Returns the raw profile.
    pub async fn profile(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<GuardianProfile, anyhow::Error> {
        self.stats_port.fetch_profile(membership_id).await
    }

    /// Returns the recent-activity summary, or an empty summary when no activity
    /// source is configured or the fetch fails.
    pub async fn activity(&self, membership_id: &BungieMembershipId) -> ActivitySummary {
        match &self.activity_port {
            Some(port) => port
                .fetch_recent_activities(membership_id)
                .await
                .unwrap_or_default(),
            None => ActivitySummary::default(),
        }
    }

    /// Returns the personalized dossier line, or a graceful fallback message.
    pub async fn summarize(&self, membership_id: &BungieMembershipId) -> Result<String, String> {
        match self.stats_port.fetch_profile(membership_id).await {
            Ok(profile) => Ok(profile.dossier()),
            Err(_) => Err("I couldn't reach your Guardian records just now.".to_string()),
        }
    }

    /// The full personalization context for the conversational Ghost: the career
    /// dossier plus a recent-activity narrative when available. `None` when even
    /// the base career profile can't be reached.
    pub async fn full_context(&self, membership_id: &BungieMembershipId) -> Option<String> {
        let profile = self.stats_port.fetch_profile(membership_id).await.ok()?;
        let mut context = profile.dossier();

        let narrative = self.activity(membership_id).await.narrative();
        if !narrative.is_empty() {
            context.push(' ');
            context.push_str(&narrative);
        }
        Some(context)
    }
}
