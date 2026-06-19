//! Phase 4B: Postgres adapter for the auth domain's `TokenStoragePort`.
//!
//! Persists Bungie OAuth tokens in the `bungie_tokens` table (Phase 4A migration).
//! Uses runtime `sqlx` queries (not the compile-time `query!` macros) so the
//! workspace builds without a live database connection.

use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::{PgPool, Row};

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;
use domain::auth::token::BungieOAuthToken;

/// Concrete `TokenStoragePort` backed by a `sqlx::PgPool`.
pub struct PostgresTokenStorageAdapter {
    pool: PgPool,
}

impl PostgresTokenStorageAdapter {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl TokenStoragePort for PostgresTokenStorageAdapter {
    async fn save_token(
        &self,
        membership_id: &BungieMembershipId,
        token: &BungieOAuthToken,
    ) -> Result<(), anyhow::Error> {
        sqlx::query(
            r#"
            INSERT INTO bungie_tokens
                (membership_id, access_token, refresh_token, expires_at, refresh_expires_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (membership_id) DO UPDATE SET
                access_token       = EXCLUDED.access_token,
                refresh_token      = EXCLUDED.refresh_token,
                expires_at         = EXCLUDED.expires_at,
                refresh_expires_at = EXCLUDED.refresh_expires_at,
                updated_at         = NOW()
            "#,
        )
        .bind(&membership_id.0)
        .bind(&token.access_token)
        .bind(&token.refresh_token)
        .bind(token.expires_at)
        .bind(token.refresh_expires_at)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    async fn get_token(
        &self,
        membership_id: &BungieMembershipId,
    ) -> Result<Option<BungieOAuthToken>, anyhow::Error> {
        let row = sqlx::query(
            r#"
            SELECT access_token, refresh_token, expires_at, refresh_expires_at
            FROM bungie_tokens
            WHERE membership_id = $1
            "#,
        )
        .bind(&membership_id.0)
        .fetch_optional(&self.pool)
        .await?;

        let Some(row) = row else {
            return Ok(None);
        };

        Ok(Some(BungieOAuthToken {
            access_token: row.try_get("access_token")?,
            refresh_token: row.try_get("refresh_token")?,
            expires_at: row.try_get::<DateTime<Utc>, _>("expires_at")?,
            refresh_expires_at: row.try_get::<DateTime<Utc>, _>("refresh_expires_at")?,
        }))
    }
}
