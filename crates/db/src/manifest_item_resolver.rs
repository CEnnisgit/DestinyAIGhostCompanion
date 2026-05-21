use async_trait::async_trait;
use sqlx::PgPool;

use domain::inventory::item::DestinyItemHash;
use domain::inventory::ports::ManifestDatabasePort;

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
    async fn resolve_item_hash(&self, transcribed_name: &str) -> Result<DestinyItemHash, anyhow::Error> {
        // Basic fuzzy match: ILIKE %name%
        // We select the first one if multiple match (will be replaced by vector search in Phase 4E)
        let search_pattern = format!("%{}%", transcribed_name);
        
        let row: Option<(i64,)> = sqlx::query_as(
            "SELECT hash FROM destiny_items WHERE name ILIKE $1 LIMIT 1"
        )
        .bind(&search_pattern)
        .fetch_optional(&self.pool)
        .await?;

        match row {
            Some((hash,)) => {
                // The Postgres hash is a BIGINT (i64), but Bungie uses u32 for DestinyItemHash.
                // Bungie hashes are actually signed 32-bit integers masquerading as unsigned in some APIs.
                // Safely cast i64 down to u32
                let u32_hash = hash as u32;
                Ok(DestinyItemHash::new(u32_hash).map_err(|e| anyhow::anyhow!(e))?)
            }
            None => Err(anyhow::anyhow!("Could not find item matching '{}'", transcribed_name))
        }
    }
}
