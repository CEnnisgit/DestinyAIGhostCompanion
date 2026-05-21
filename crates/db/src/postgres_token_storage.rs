use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::{PgPool, Row};

use domain::auth::membership::BungieMembershipId;
use domain::auth::ports::TokenStoragePort;
use domain::auth::token::BungieOAuthToken;

use crate::crypto;

/// Adapter that persists Bungie OAuth tokens in PostgreSQL with
/// AES-256-GCM encryption for the token values at rest.
pub struct PostgresTokenStorageAdapter {
    pool: PgPool,
    encryption_key: [u8; 32],
}

impl PostgresTokenStorageAdapter {
    pub fn new(pool: PgPool, encryption_key: [u8; 32]) -> Self {
        Self {
            pool,
            encryption_key,
        }
    }
}

#[async_trait]
impl TokenStoragePort for PostgresTokenStorageAdapter {
    async fn save_token(
        &self,
        membership_id: &BungieMembershipId,
        token: &BungieOAuthToken,
    ) -> Result<(), anyhow::Error> {
        let encrypted_access = crypto::encrypt(&token.access_token, &self.encryption_key)?;
        let encrypted_refresh = crypto::encrypt(&token.refresh_token, &self.encryption_key)?;

        sqlx::query(
            r#"
            INSERT INTO bungie_tokens (
                membership_id,
                access_token,
                refresh_token,
                expires_at,
                refresh_expires_at
            )
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (membership_id) DO UPDATE SET
                access_token       = $2,
                refresh_token      = $3,
                expires_at         = $4,
                refresh_expires_at = $5
            "#,
        )
        .bind(&membership_id.0)
        .bind(&encrypted_access)
        .bind(&encrypted_refresh)
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
            SELECT access_token,
                   refresh_token,
                   expires_at,
                   refresh_expires_at
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

        let encrypted_access: Vec<u8> = row.get("access_token");
        let encrypted_refresh: Vec<u8> = row.get("refresh_token");
        let expires_at: DateTime<Utc> = row.get("expires_at");
        let refresh_expires_at: DateTime<Utc> = row.get("refresh_expires_at");

        let access_token = crypto::decrypt(&encrypted_access, &self.encryption_key)?;
        let refresh_token = crypto::decrypt(&encrypted_refresh, &self.encryption_key)?;

        Ok(Some(BungieOAuthToken {
            access_token,
            refresh_token,
            expires_at,
            refresh_expires_at,
        }))
    }
}
