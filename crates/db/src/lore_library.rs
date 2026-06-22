//! Read access to the lore corpus for a browsable Codex: list categories,
//! browse a category, and structured (entry-level) search.

use anyhow::Context;
use serde::Serialize;
use sqlx::{PgPool, Row};

use crate::grimoire_search::build_or_tsquery;

#[derive(Debug, Clone, Serialize)]
pub struct LoreEntry {
    pub name: String,
    pub description: String,
    pub category: Option<String>,
    pub source: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct LoreCategory {
    pub category: String,
    pub count: i64,
}

pub struct LoreLibrary {
    pool: PgPool,
}

impl LoreLibrary {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Categories with entry counts (for the Codex index).
    pub async fn categories(&self) -> Result<Vec<LoreCategory>, anyhow::Error> {
        let rows = sqlx::query(
            "SELECT category, count(*) AS n FROM destiny_lore
             WHERE category IS NOT NULL GROUP BY category ORDER BY category",
        )
        .fetch_all(&self.pool)
        .await
        .context("listing lore categories")?;
        Ok(rows
            .into_iter()
            .map(|r| LoreCategory { category: r.get("category"), count: r.get("n") })
            .collect())
    }

    /// Entries within a category, alphabetical.
    pub async fn browse(&self, category: &str, limit: i64) -> Result<Vec<LoreEntry>, anyhow::Error> {
        let rows = sqlx::query(
            "SELECT name, description, category, source FROM destiny_lore
             WHERE category = $1 ORDER BY name LIMIT $2",
        )
        .bind(category)
        .bind(limit)
        .fetch_all(&self.pool)
        .await
        .context("browsing lore category")?;
        Ok(rows.into_iter().map(row_to_entry).collect())
    }

    /// Structured relevance search over the corpus.
    pub async fn search(&self, query: &str, limit: i64) -> Result<Vec<LoreEntry>, anyhow::Error> {
        if let Some(ts) = build_or_tsquery(query) {
            let rows = sqlx::query(
                r#"
                SELECT name, description, category, source
                FROM destiny_lore, to_tsquery('english', $1) AS q
                WHERE to_tsvector('english', name || ' ' || COALESCE(description, '')) @@ q
                ORDER BY (source = 'curated') ASC,
                         ts_rank(to_tsvector('english', name || ' ' || COALESCE(description, '')), q) DESC
                LIMIT $2
                "#,
            )
            .bind(&ts)
            .bind(limit)
            .fetch_all(&self.pool)
            .await
            .context("searching lore")?;
            if !rows.is_empty() {
                return Ok(rows.into_iter().map(row_to_entry).collect());
            }
        }

        let like = format!("%{}%", query.trim());
        let rows = sqlx::query(
            "SELECT name, description, category, source FROM destiny_lore
             WHERE name ILIKE $1 OR description ILIKE $1
             ORDER BY (source = 'curated') ASC, length(name) ASC LIMIT $2",
        )
        .bind(&like)
        .bind(limit)
        .fetch_all(&self.pool)
        .await
        .context("searching lore (fallback)")?;
        Ok(rows.into_iter().map(row_to_entry).collect())
    }
}

fn row_to_entry(r: sqlx::postgres::PgRow) -> LoreEntry {
    LoreEntry {
        name: r.get("name"),
        description: r.get("description"),
        category: r.try_get("category").ok(),
        source: r.try_get("source").ok(),
    }
}
