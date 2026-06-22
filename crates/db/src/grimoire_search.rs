//! Phase 4E: `GrimoireDatabasePort` over `destiny_lore`.
//!
//! Uses pgvector cosine search (ADR-015) when an embeddings provider is
//! configured, and always falls back to keyword (ILIKE) search — so the Ghost
//! can answer lore even with no LLM/embeddings key, against the curated seed
//! and/or the manifest lore.

use anyhow::{anyhow, Context};
use async_trait::async_trait;
use sqlx::{PgPool, Row};

use domain::lore::ports::GrimoireDatabasePort;

use crate::embedding_client::EmbeddingClient;

const TOP_K: i64 = 5;

pub struct GrimoireSearch {
    pool: PgPool,
    embeddings: Option<EmbeddingClient>,
}

impl GrimoireSearch {
    pub fn new(pool: PgPool, embeddings: Option<EmbeddingClient>) -> Self {
        Self { pool, embeddings }
    }

    /// Cosine nearest-neighbours over embedded lore.
    async fn semantic(&self, topic: &str, embeddings: &EmbeddingClient) -> Result<Vec<(String, String)>, anyhow::Error> {
        let query_vector = pgvector::Vector::from(embeddings.embed(topic).await?);
        let rows = sqlx::query(
            r#"
            SELECT name, description
            FROM destiny_lore
            WHERE embedding IS NOT NULL
            ORDER BY (source = 'curated') ASC, embedding <=> $1
            LIMIT $2
            "#,
        )
        .bind(query_vector)
        .bind(TOP_K)
        .fetch_all(&self.pool)
        .await
        .context("semantic lore search")?;
        Ok(rows.into_iter().map(|r| (r.get("name"), r.get("description"))).collect())
    }

    /// Text search with no embeddings needed: Postgres full-text search over an
    /// OR of the query's significant words (ranked by relevance), then a simple
    /// substring fallback for anything FTS misses (e.g. hyphenated "Cayde-6").
    async fn keyword(&self, topic: &str) -> Result<Vec<(String, String)>, anyhow::Error> {
        let topic = topic.trim();

        if let Some(query) = build_or_tsquery(topic) {
            let fts = sqlx::query(
                r#"
                SELECT name, description
                FROM destiny_lore, to_tsquery('english', $1) AS q
                WHERE to_tsvector('english', name || ' ' || COALESCE(description, '')) @@ q
                ORDER BY (source = 'curated') ASC,
                         ts_rank(to_tsvector('english', name || ' ' || COALESCE(description, '')), q) DESC
                LIMIT $2
                "#,
            )
            .bind(&query)
            .bind(TOP_K)
            .fetch_all(&self.pool)
            .await
            .context("full-text lore search")?;
            if !fts.is_empty() {
                return Ok(fts.into_iter().map(|r| (r.get("name"), r.get("description"))).collect());
            }
        }

        let like = format!("%{topic}%");
        let rows = sqlx::query(
            r#"
            SELECT name, description
            FROM destiny_lore
            WHERE name ILIKE $1 OR description ILIKE $1
            ORDER BY (source = 'curated') ASC, (name ILIKE $1) DESC, length(name) ASC
            LIMIT $2
            "#,
        )
        .bind(&like)
        .bind(TOP_K)
        .fetch_all(&self.pool)
        .await
        .context("keyword lore search")?;
        Ok(rows.into_iter().map(|r| (r.get("name"), r.get("description"))).collect())
    }
}

/// Builds a Postgres `to_tsquery` OR-expression from a natural-language topic:
/// keeps significant words, drops short words and common stop words, joins with `|`.
/// Returns `None` when nothing significant remains.
pub(crate) fn build_or_tsquery(topic: &str) -> Option<String> {
    const STOP: &[&str] = &[
        "the", "and", "for", "was", "are", "you", "who", "what", "whats", "tell", "about", "give",
        "does", "did", "how", "why", "can", "with", "from", "this", "that", "your", "his", "her",
        "she", "him", "them", "they", "into", "anything", "everything", "something", "know",
    ];
    let words: Vec<String> = topic
        .split(|c: char| !c.is_alphanumeric())
        .filter(|w| w.len() >= 3)
        .map(|w| w.to_lowercase())
        .filter(|w| !STOP.contains(&w.as_str()))
        .collect();
    if words.is_empty() {
        None
    } else {
        Some(words.join(" | "))
    }
}

#[async_trait]
impl GrimoireDatabasePort for GrimoireSearch {
    async fn fetch_semantic_lore_context(&self, topic: &str) -> Result<String, anyhow::Error> {
        let mut rows = match &self.embeddings {
            Some(embeddings) => self.semantic(topic, embeddings).await?,
            None => Vec::new(),
        };
        if rows.is_empty() {
            rows = self.keyword(topic).await?;
        }
        if rows.is_empty() {
            return Err(anyhow!("no lore matched '{topic}'"));
        }

        let context = rows
            .iter()
            .map(|(name, description)| format!("{name}: {description}"))
            .collect::<Vec<_>>()
            .join("\n\n");
        Ok(context)
    }
}

#[cfg(test)]
mod tests {
    use super::build_or_tsquery;

    #[test]
    fn drops_stop_words_and_short_words_and_ors_the_rest() {
        assert_eq!(build_or_tsquery("who killed cayde").as_deref(), Some("killed | cayde"));
        assert_eq!(
            build_or_tsquery("tell me about the vault of glass").as_deref(),
            Some("vault | glass")
        );
        assert_eq!(build_or_tsquery("Cayde-6").as_deref(), Some("cayde")); // "6" too short
    }

    #[test]
    fn none_when_only_noise() {
        assert_eq!(build_or_tsquery("who are you?"), None);
    }
}
