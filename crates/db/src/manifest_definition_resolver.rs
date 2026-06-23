//! Generic manifest-definition name lookup across the ingested mirrors
//! (`destiny_records`, `destiny_activities`, `destiny_items`, `destiny_lore`).
//!
//! Lets the Ghost turn a raw definition hash — e.g. a Triumph hash from profile
//! component 900, or an activity hash — into a human name + description from the
//! local database, with no per-hash Bungie API call. A `kind` it doesn't know,
//! or an un-ingested manifest, simply yields `None` (caller can fall back).

use anyhow::Context;
use serde::Serialize;
use sqlx::{PgPool, Row};

#[derive(Debug, Clone, Serialize)]
pub struct DefinitionEntry {
    pub name: String,
    pub description: Option<String>,
}

pub struct ManifestDefinitionResolver {
    pool: PgPool,
}

impl ManifestDefinitionResolver {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// The accepted `kind` values, for tool/endpoint documentation.
    pub const KINDS: &'static [&'static str] = &["record", "activity", "item", "lore"];

    /// Resolves `(kind, hash)` to a name + description from the local mirror.
    pub async fn define(&self, kind: &str, hash: i64) -> Option<DefinitionEntry> {
        // Map the kind to its table; unknown kinds resolve to None.
        let sql = match kind.to_ascii_lowercase().as_str() {
            "record" | "triumph" => "SELECT name, description FROM destiny_records WHERE hash = $1",
            "activity" => "SELECT name, description FROM destiny_activities WHERE hash = $1",
            "item" => "SELECT name, NULL::text AS description FROM destiny_items WHERE hash = $1",
            "lore" => "SELECT name, description FROM destiny_lore WHERE hash = $1",
            _ => return None,
        };

        let row = sqlx::query(sql)
            .bind(hash)
            .fetch_optional(&self.pool)
            .await
            .context("resolving manifest definition")
            .ok()??;

        let name: String = row.try_get("name").ok()?;
        if name.is_empty() {
            return None;
        }
        Some(DefinitionEntry {
            name,
            description: row.try_get("description").ok(),
        })
    }
}
