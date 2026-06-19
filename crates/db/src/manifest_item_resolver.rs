//! Phase 4D (temporary): Postgres-backed `ManifestDatabasePort`.
//!
//! Resolves a transcribed item name to a `DestinyItemHash` via simple `ILIKE`
//! matching over the `destiny_items` table (migration 003). The full semantic
//! pipeline replaces this in Phase 4E; the port contract stays the same.

use anyhow::{anyhow, Context};
use async_trait::async_trait;
use sqlx::{PgPool, Row};

use domain::inventory::item::DestinyItemHash;
use domain::inventory::ports::ManifestDatabasePort;

/// Concrete `ManifestDatabasePort` backed by `sqlx::PgPool`.
pub struct ManifestItemResolver {
    pool: PgPool,
}

impl ManifestItemResolver {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl ManifestDatabasePort for ManifestItemResolver {
    async fn resolve_item_hash(
        &self,
        transcribed_name: &str,
    ) -> Result<DestinyItemHash, anyhow::Error> {
        let trimmed = transcribed_name.trim();
        if trimmed.is_empty() {
            return Err(anyhow!("cannot resolve an empty item name"));
        }

        // Prefer an exact (case-insensitive) name match, then fall back to a
        // substring match, preferring the shortest candidate name.
        let row = sqlx::query(
            r#"
            SELECT hash
            FROM destiny_items
            WHERE name ILIKE $1 OR name ILIKE $2
            ORDER BY (name ILIKE $1) DESC, length(name) ASC
            LIMIT 1
            "#,
        )
        .bind(trimmed)
        .bind(format!("%{trimmed}%"))
        .fetch_optional(&self.pool)
        .await
        .context("querying destiny_items")?
        .ok_or_else(|| anyhow!("no Destiny item matched '{transcribed_name}'"))?;

        let hash: i64 = row.try_get("hash")?;
        let hash = u32::try_from(hash)
            .map_err(|_| anyhow!("item hash {hash} out of u32 range"))?;

        DestinyItemHash::new(hash).map_err(|e| anyhow!(e))
    }
}
