//! Postgres adapter for the auth domain's `SessionRevocationPort`.
//!
//! Backs the `session_revocations` table (migration 011): a per-user cutoff
//! timestamp. A session whose `issued_at` precedes the cutoff is revoked. Setting
//! the cutoff to now (on sign-out) invalidates all of that user's live tokens.

use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::{PgPool, Row};

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::SessionRevocationPort;

pub struct PostgresSessionRevocationStore {
    pool: PgPool,
}

impl PostgresSessionRevocationStore {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl SessionRevocationPort for PostgresSessionRevocationStore {
    async fn revoked_before(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<Option<DateTime<Utc>>, anyhow::Error> {
        let row = sqlx::query(
            "SELECT revoked_before FROM session_revocations WHERE membership_id = $1",
        )
        .bind(&membership_id.0)
        .fetch_optional(&self.pool)
        .await?;
        Ok(row.map(|r| r.get::<DateTime<Utc>, _>("revoked_before")))
    }

    async fn revoke_before(
        &self,
        membership_id: &BungieMembershipId,
        cutoff: DateTime<Utc>,
    ) -> Result<(), anyhow::Error> {
        sqlx::query(
            "INSERT INTO session_revocations (membership_id, revoked_before)
             VALUES ($1, $2)
             ON CONFLICT (membership_id) DO UPDATE SET revoked_before = EXCLUDED.revoked_before",
        )
        .bind(&membership_id.0)
        .bind(cutoff)
        .execute(&self.pool)
        .await?;
        Ok(())
    }
}
