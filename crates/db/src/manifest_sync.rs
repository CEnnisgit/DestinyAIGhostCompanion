//! Phase 4E: Bungie manifest acquisition + load (ADR-016) and lore embedding
//! backfill (ADR-014/015).
//!
//! On demand (typically at startup) this:
//!   1. reads the manifest index to get the current version + world-content path,
//!   2. skips if that version is already loaded (`manifest_metadata`),
//!   3. downloads the world-content zip, extracts its SQLite database,
//!   4. loads item + lore definitions into Postgres,
//!   5. backfills embeddings for lore rows that lack them.
//!
//! NOTE: requires a real `BUNGIE_API_KEY` (the manifest endpoint rejects others)
//! and downloads a large file, so it is not exercised by the offline test suite.

use std::io::copy;
use std::path::PathBuf;

use anyhow::{anyhow, Context};
use serde::Deserialize;
use serde_json::Value;
use sqlx::sqlite::SqlitePoolOptions;
use sqlx::{PgPool, Row};

use crate::embedding_client::EmbeddingClient;

const MANIFEST_URL: &str = "https://www.bungie.net/Platform/Destiny2/Manifest/";
const BUNGIE_ROOT: &str = "https://www.bungie.net";
const VERSION_KEY: &str = "manifest_version";
const EMBED_BATCH: usize = 100;
/// Offset applied to item hashes when storing their flavor text as lore, so they
/// never collide with `DestinyLoreDefinition` hashes (u32) or the curated seed.
const ITEM_LORE_HASH_OFFSET: i64 = 5_000_000_000;

pub struct ManifestSync {
    pg: PgPool,
    http: reqwest::Client,
    api_key: String,
    embeddings: Option<EmbeddingClient>,
}

impl ManifestSync {
    pub fn new(
        pg: PgPool,
        http: reqwest::Client,
        api_key: impl Into<String>,
        embeddings: Option<EmbeddingClient>,
    ) -> Self {
        Self {
            pg,
            http,
            api_key: api_key.into(),
            embeddings,
        }
    }

    /// Downloads + loads the manifest only if Bungie's version differs from the
    /// last-loaded one. Safe to call on every startup.
    pub async fn sync_if_changed(&self) -> Result<(), anyhow::Error> {
        let index = self.fetch_index().await?;

        if self.current_version().await?.as_deref() == Some(index.version.as_str()) {
            tracing::info!(version = %index.version, "manifest already up to date");
            return Ok(());
        }

        let path = index
            .mobile_world_content_paths
            .get("en")
            .cloned()
            .ok_or_else(|| anyhow!("manifest has no English world content path"))?;

        tracing::info!(version = %index.version, "downloading Destiny manifest");
        let sqlite_path = self.download_and_extract(&path).await?;
        self.load_definitions(&sqlite_path).await?;

        if let Some(embeddings) = &self.embeddings {
            self.backfill_lore_embeddings(embeddings).await?;
        }

        self.set_version(&index.version).await?;
        let _ = std::fs::remove_file(&sqlite_path);
        tracing::info!(version = %index.version, "manifest sync complete");
        Ok(())
    }

    async fn fetch_index(&self) -> Result<ManifestIndex, anyhow::Error> {
        let envelope: ManifestEnvelope = self
            .http
            .get(MANIFEST_URL)
            .header("X-API-Key", &self.api_key)
            .send()
            .await
            .context("fetching manifest index")?
            .error_for_status()?
            .json()
            .await
            .context("decoding manifest index")?;
        Ok(envelope.response)
    }

    async fn current_version(&self) -> Result<Option<String>, anyhow::Error> {
        let row = sqlx::query("SELECT value FROM manifest_metadata WHERE key = $1")
            .bind(VERSION_KEY)
            .fetch_optional(&self.pg)
            .await?;
        Ok(row.map(|r| r.get::<String, _>("value")))
    }

    async fn set_version(&self, version: &str) -> Result<(), anyhow::Error> {
        sqlx::query(
            "INSERT INTO manifest_metadata (key, value) VALUES ($1, $2)
             ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
        )
        .bind(VERSION_KEY)
        .bind(version)
        .execute(&self.pg)
        .await?;
        Ok(())
    }

    /// Downloads the world-content zip and extracts its single SQLite database to a temp file.
    async fn download_and_extract(&self, content_path: &str) -> Result<PathBuf, anyhow::Error> {
        let url = format!("{BUNGIE_ROOT}{content_path}");
        let bytes = self
            .http
            .get(&url)
            .header("X-API-Key", &self.api_key)
            .send()
            .await
            .context("downloading manifest content")?
            .error_for_status()?
            .bytes()
            .await?;

        let mut archive = zip::ZipArchive::new(std::io::Cursor::new(bytes))
            .context("opening manifest zip")?;
        let mut entry = archive.by_index(0).context("empty manifest zip")?;

        // Use just the file name to avoid zip-slip; write into the temp dir.
        let file_name = std::path::Path::new(entry.name())
            .file_name()
            .map(|n| n.to_owned())
            .ok_or_else(|| anyhow!("manifest zip entry has no file name"))?;
        let out_path = std::env::temp_dir().join(file_name);

        let mut out = std::fs::File::create(&out_path).context("creating temp manifest db")?;
        copy(&mut entry, &mut out).context("extracting manifest db")?;
        Ok(out_path)
    }

    /// Reads item + lore definitions from the manifest SQLite and upserts them into Postgres.
    async fn load_definitions(&self, sqlite_path: &PathBuf) -> Result<(), anyhow::Error> {
        let url = format!("sqlite://{}?mode=ro", sqlite_path.display());
        let sqlite = SqlitePoolOptions::new()
            .max_connections(1)
            .connect(&url)
            .await
            .context("opening manifest SQLite")?;

        // Items.
        let item_rows = sqlx::query("SELECT id, json FROM DestinyInventoryItemDefinition")
            .fetch_all(&sqlite)
            .await
            .context("reading DestinyInventoryItemDefinition")?;
        let mut items = 0u64;
        for row in &item_rows {
            let Some((hash, def)) = decode_def(row) else { continue };
            let name = string_at(&def, &["displayProperties", "name"]);
            if name.is_empty() {
                continue;
            }
            sqlx::query(
                "INSERT INTO destiny_items (hash, name, item_type, tier_type, icon_path)
                 VALUES ($1, $2, $3, $4, $5)
                 ON CONFLICT (hash) DO UPDATE SET
                    name = EXCLUDED.name, item_type = EXCLUDED.item_type,
                    tier_type = EXCLUDED.tier_type, icon_path = EXCLUDED.icon_path",
            )
            .bind(hash)
            .bind(&name)
            .bind(opt_string_at(&def, &["itemTypeDisplayName"]))
            .bind(opt_string_at(&def, &["inventory", "tierTypeName"]))
            .bind(opt_string_at(&def, &["displayProperties", "icon"]))
            .execute(&self.pg)
            .await?;
            items += 1;

            // Many weapons/armor carry italic "flavorText" lore — ingest it into
            // the lore corpus too (offset hash to avoid colliding with lore defs).
            let flavor = string_at(&def, &["flavorText"]);
            if !flavor.is_empty() {
                upsert_lore(&self.pg, hash + ITEM_LORE_HASH_OFFSET, &name, &flavor, "Item Lore").await?;
            }
        }

        // Lore definitions (Grimoire / lore entries).
        let lore_rows = sqlx::query("SELECT id, json FROM DestinyLoreDefinition")
            .fetch_all(&sqlite)
            .await
            .context("reading DestinyLoreDefinition")?;
        let mut lore = 0u64;
        for row in &lore_rows {
            let Some((hash, def)) = decode_def(row) else { continue };
            let name = string_at(&def, &["displayProperties", "name"]);
            let description = string_at(&def, &["displayProperties", "description"]);
            if description.is_empty() {
                continue;
            }
            upsert_lore(&self.pg, hash, &name, &description, "Grimoire").await?;
            lore += 1;
        }

        // Activity definitions — so activity hashes (from a player's history)
        // resolve to names locally, with no per-hash API call.
        let activity_rows = sqlx::query("SELECT id, json FROM DestinyActivityDefinition")
            .fetch_all(&sqlite)
            .await
            .context("reading DestinyActivityDefinition")?;
        let mut activities = 0u64;
        for row in &activity_rows {
            let Some((hash, def)) = decode_def(row) else { continue };
            let name = string_at(&def, &["displayProperties", "name"]);
            if name.is_empty() {
                continue;
            }
            sqlx::query(
                "INSERT INTO destiny_activities (hash, name, description, icon_path)
                 VALUES ($1, $2, $3, $4)
                 ON CONFLICT (hash) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    icon_path = EXCLUDED.icon_path",
            )
            .bind(hash)
            .bind(&name)
            .bind(opt_string_at(&def, &["displayProperties", "description"]))
            .bind(opt_string_at(&def, &["displayProperties", "icon"]))
            .execute(&self.pg)
            .await?;
            activities += 1;
        }

        // Record definitions (Triumphs) — so record hashes resolve to names.
        let record_rows = sqlx::query("SELECT id, json FROM DestinyRecordDefinition")
            .fetch_all(&sqlite)
            .await
            .context("reading DestinyRecordDefinition")?;
        let mut records = 0u64;
        for row in &record_rows {
            let Some((hash, def)) = decode_def(row) else { continue };
            let name = string_at(&def, &["displayProperties", "name"]);
            if name.is_empty() {
                continue;
            }
            sqlx::query(
                "INSERT INTO destiny_records (hash, name, description)
                 VALUES ($1, $2, $3)
                 ON CONFLICT (hash) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description",
            )
            .bind(hash)
            .bind(&name)
            .bind(opt_string_at(&def, &["displayProperties", "description"]))
            .execute(&self.pg)
            .await?;
            records += 1;
        }

        sqlite.close().await;
        tracing::info!(items, lore, activities, records, "loaded manifest definitions");
        Ok(())
    }

    /// Embeds lore rows whose `embedding IS NULL`, in batches.
    async fn backfill_lore_embeddings(
        &self,
        embeddings: &EmbeddingClient,
    ) -> Result<(), anyhow::Error> {
        loop {
            let rows = sqlx::query(
                "SELECT hash, name, description FROM destiny_lore
                 WHERE embedding IS NULL LIMIT $1",
            )
            .bind(EMBED_BATCH as i64)
            .fetch_all(&self.pg)
            .await?;

            if rows.is_empty() {
                break;
            }

            let inputs: Vec<String> = rows
                .iter()
                .map(|r| {
                    format!(
                        "{}: {}",
                        r.get::<String, _>("name"),
                        r.get::<String, _>("description")
                    )
                })
                .collect();

            let vectors = embeddings.embed_batch(&inputs).await?;
            for (row, vector) in rows.iter().zip(vectors) {
                let hash: i64 = row.get("hash");
                sqlx::query("UPDATE destiny_lore SET embedding = $1 WHERE hash = $2")
                    .bind(pgvector::Vector::from(vector))
                    .bind(hash)
                    .execute(&self.pg)
                    .await?;
            }
            tracing::info!(batch = rows.len(), "embedded lore batch");
        }
        Ok(())
    }
}

#[derive(Debug, Deserialize)]
struct ManifestEnvelope {
    #[serde(rename = "Response")]
    response: ManifestIndex,
}

#[derive(Debug, Deserialize)]
struct ManifestIndex {
    version: String,
    #[serde(rename = "mobileWorldContentPaths")]
    mobile_world_content_paths: std::collections::HashMap<String, String>,
}

/// Decodes a manifest row `(id INTEGER, json TEXT)` into `(pg_hash, json)`.
/// Manifest ids are signed 32-bit; reinterpret the bits to recover the u32 hash.
fn decode_def(row: &sqlx::sqlite::SqliteRow) -> Option<(i64, Value)> {
    let id: i64 = row.try_get("id").ok()?;
    let json: String = row.try_get("json").ok()?;
    let hash = (id as i32) as u32 as i64;
    let value = serde_json::from_str::<Value>(&json).ok()?;
    Some((hash, value))
}

/// Upserts a lore row, clearing the embedding only when the text changed.
async fn upsert_lore(
    pg: &sqlx::PgPool,
    hash: i64,
    name: &str,
    description: &str,
    category: &str,
) -> Result<(), anyhow::Error> {
    sqlx::query(
        "INSERT INTO destiny_lore (hash, name, description, category, source)
         VALUES ($1, $2, $3, $4, 'bungie')
         ON CONFLICT (hash) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            category = EXCLUDED.category,
            source = 'bungie',
            embedding = CASE WHEN destiny_lore.description <> EXCLUDED.description
                             THEN NULL ELSE destiny_lore.embedding END",
    )
    .bind(hash)
    .bind(name)
    .bind(description)
    .bind(category)
    .execute(pg)
    .await?;
    Ok(())
}

fn string_at(def: &Value, path: &[&str]) -> String {
    opt_string_at(def, path).unwrap_or_default()
}

fn opt_string_at(def: &Value, path: &[&str]) -> Option<String> {
    let mut cur = def;
    for key in path {
        cur = cur.get(key)?;
    }
    cur.as_str().filter(|s| !s.is_empty()).map(str::to_owned)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn string_at_walks_nested_paths() {
        let def = json!({ "displayProperties": { "name": "Sunshot", "icon": "/x.png" } });
        assert_eq!(string_at(&def, &["displayProperties", "name"]), "Sunshot");
        assert_eq!(
            opt_string_at(&def, &["displayProperties", "icon"]).as_deref(),
            Some("/x.png")
        );
        assert_eq!(string_at(&def, &["displayProperties", "missing"]), "");
    }
}
