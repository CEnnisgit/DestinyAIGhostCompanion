//! Phase 4E: pgvector-backed `GrimoireDatabasePort` (ADR-015 semantic lore search).
//!
//! Embeds the topic, finds the nearest lore entries by cosine distance, and
//! concatenates them into a grounding context string for the `LoreSaga`.

use anyhow::{anyhow, Context};
use async_trait::async_trait;
use sqlx::{PgPool, Row};

use domain::lore::ports::GrimoireDatabasePort;

use crate::embedding_client::EmbeddingClient;

const TOP_K: i64 = 5;

pub struct GrimoireSearch {
    pool: PgPool,
    embeddings: EmbeddingClient,
}

impl GrimoireSearch {
    pub fn new(pool: PgPool, embeddings: EmbeddingClient) -> Self {
        Self { pool, embeddings }
    }
}

#[async_trait]
impl GrimoireDatabasePort for GrimoireSearch {
    async fn fetch_semantic_lore_context(&self, topic: &str) -> Result<String, anyhow::Error> {
        let query_vector = pgvector::Vector::from(self.embeddings.embed(topic).await?);

        // `<=>` is cosine distance (pgvector); nearest entries first.
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

        if rows.is_empty() {
            return Err(anyhow!("no embedded lore entries matched '{topic}'"));
        }

        let context = rows
            .iter()
            .map(|row| {
                let name: String = row.get("name");
                let description: String = row.get("description");
                format!("{name}: {description}")
            })
            .collect::<Vec<_>>()
            .join("\n\n");

        Ok(context)
    }
}
