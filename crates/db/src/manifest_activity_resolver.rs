//! Local activity-name resolution from the manifest mirror (`destiny_activities`,
//! migration 009). Lets the activity client turn an activity hash into a name
//! without a per-hash Bungie API call — instant, offline, no rate limit.

use anyhow::Context;
use sqlx::{PgPool, Row};

/// Resolves activity hashes to display names from the local manifest mirror.
pub struct ManifestActivityResolver {
    pool: PgPool,
}

impl ManifestActivityResolver {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// The activity's display name, or `None` if the manifest hasn't been
    /// ingested yet or the hash is unknown (caller can fall back to the API).
    pub async fn name(&self, hash: i64) -> Option<String> {
        let row = sqlx::query("SELECT name FROM destiny_activities WHERE hash = $1")
            .bind(hash)
            .fetch_optional(&self.pool)
            .await
            .context("querying destiny_activities")
            .ok()??;
        let name: String = row.try_get("name").ok()?;
        Some(name).filter(|s| !s.is_empty())
    }
}
