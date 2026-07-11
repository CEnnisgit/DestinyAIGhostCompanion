//! Postgres adapter for the auth domain's `AccountErasurePort`.
//!
//! "Delete my account" spans every table that stores something about a
//! Guardian: `bungie_tokens` (their OAuth grant) and `chat_threads` (their
//! synced conversations; `chat_messages` follows by ON DELETE CASCADE). The
//! remaining tables — `destiny_lore`, `destiny_items`, `destiny_activities`,
//! `destiny_records`, `manifest_metadata` — are global game data mirrored from
//! Bungie and contain nothing about any user.
//!
//! `session_revocations` is deliberately *written*, not deleted. Sessions are
//! stateless HMAC tokens with a 30-day expiry, so the only way to kill a live
//! one is a cutoff timestamp. Clearing the row would resurrect every outstanding
//! token for that membership id, letting a just-deleted account keep talking to
//! the Ghost and recreate the rows it asked us to erase. The tombstone that
//! remains is a membership id and a timestamp — the minimum needed to keep the
//! deletion enforced.

use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::PgPool;

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::AccountErasurePort;

pub struct PostgresAccountEraser {
    pool: PgPool,
}

impl PostgresAccountEraser {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl AccountErasurePort for PostgresAccountEraser {
    async fn erase_account(
        &self,
        membership_id: &BungieMembershipId,
        revoked_at: DateTime<Utc>,
    ) -> Result<(), anyhow::Error> {
        let mut tx = self.pool.begin().await?;

        // Revoke first: inside the transaction, so a concurrent request holding a
        // live token cannot slip a new row in between the delete and the cutoff.
        sqlx::query(
            "INSERT INTO session_revocations (membership_id, revoked_before)
             VALUES ($1, $2)
             ON CONFLICT (membership_id) DO UPDATE SET revoked_before = EXCLUDED.revoked_before",
        )
        .bind(&membership_id.0)
        .bind(revoked_at)
        .execute(&mut *tx)
        .await?;

        // Conversations. `chat_messages` cascades from `chat_threads`.
        sqlx::query("DELETE FROM chat_threads WHERE owner_id = $1")
            .bind(&membership_id.0)
            .execute(&mut *tx)
            .await?;

        // The Bungie OAuth grant. Without it the backend can no longer act on
        // the user's behalf; they must sign in again to recreate an account.
        sqlx::query("DELETE FROM bungie_tokens WHERE membership_id = $1")
            .bind(&membership_id.0)
            .execute(&mut *tx)
            .await?;

        tx.commit().await?;
        Ok(())
    }
}
