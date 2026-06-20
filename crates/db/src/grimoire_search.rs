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
            ORDER BY embedding <=> $1
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

    /// Case-insensitive keyword match over name/description (no embeddings needed).
    async fn keyword(&self, topic: &str) -> Result<Vec<(String, String)>, anyhow::Error> {
        let like = format!("%{}%", topic.trim());
        let rows = sqlx::query(
            r#"
            SELECT name, description
            FROM destiny_lore
            WHERE name ILIKE $1 OR description ILIKE $1
            ORDER BY (name ILIKE $1) DESC, length(name) ASC
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
