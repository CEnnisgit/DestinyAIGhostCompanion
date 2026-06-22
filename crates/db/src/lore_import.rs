//! Generic external-lore importer.
//!
//! Loads every `*.jsonl` file in a directory, each line a lore entry
//! `{ "name": "...", "description": "...", "category": "..." }`, and upserts it
//! into the corpus. This is how the Ghost ingests lore *beyond* the live game —
//! D1 Grimoire dumps, Ishtar Collective exports, transcripts, fan compilations —
//! so it can ultimately know all of Destiny's history. FTS makes imports
//! searchable immediately; embeddings fill in on the next manifest sync.

use std::path::Path;

use anyhow::Context;
use serde::Deserialize;
use sqlx::PgPool;

/// Reserved hash range for imported lore (keyed by a stable hash of the name).
const IMPORT_HASH_BASE: i64 = 6_000_000_000;

#[derive(Debug, Deserialize)]
struct ImportedLore {
    name: String,
    description: String,
    #[serde(default)]
    category: Option<String>,
}

/// Deterministic FNV-1a hash of the entry name, mapped into the import range so
/// re-importing the same entry updates rather than duplicates it.
fn stable_hash(name: &str) -> i64 {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for b in name.as_bytes() {
        h ^= u64::from(*b);
        h = h.wrapping_mul(0x0000_0100_0000_01b3);
    }
    IMPORT_HASH_BASE + (h % 2_000_000_000) as i64
}

/// Imports all `*.jsonl` lore files from `dir`. Returns the number of entries
/// upserted. Missing directory is fine (returns 0).
pub async fn import_lore_dir(pool: &PgPool, dir: impl AsRef<Path>) -> Result<u64, anyhow::Error> {
    let dir = dir.as_ref();
    if !dir.is_dir() {
        return Ok(0);
    }

    let mut count = 0u64;
    for entry in std::fs::read_dir(dir).context("reading lore import dir")? {
        let path = entry?.path();
        if path.extension().and_then(|e| e.to_str()) != Some("jsonl") {
            continue;
        }
        let contents =
            std::fs::read_to_string(&path).with_context(|| format!("reading {}", path.display()))?;
        for line in contents.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            let Ok(item) = serde_json::from_str::<ImportedLore>(line) else {
                continue; // skip malformed lines rather than failing the whole import
            };
            if item.name.trim().is_empty() || item.description.trim().is_empty() {
                continue;
            }
            let category = item.category.unwrap_or_else(|| "Imported".to_string());
            sqlx::query(
                "INSERT INTO destiny_lore (hash, name, description, category, source)
                 VALUES ($1, $2, $3, $4, 'import')
                 ON CONFLICT (hash) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    source = 'import',
                    embedding = CASE WHEN destiny_lore.description <> EXCLUDED.description
                                     THEN NULL ELSE destiny_lore.embedding END",
            )
            .bind(stable_hash(&item.name))
            .bind(&item.name)
            .bind(&item.description)
            .bind(&category)
            .execute(pool)
            .await?;
            count += 1;
        }
    }
    Ok(count)
}

#[cfg(test)]
mod tests {
    use super::stable_hash;

    #[test]
    fn stable_hash_is_deterministic_and_in_range() {
        let a = stable_hash("The Books of Sorrow");
        let b = stable_hash("The Books of Sorrow");
        assert_eq!(a, b);
        assert!(a >= super::IMPORT_HASH_BASE);
        assert_ne!(a, stable_hash("Unveiling"));
    }
}
