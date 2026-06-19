//! Phase 4E: OpenAI-compatible embeddings client (ADR-007 — configurable base URL).
//!
//! Used by the grimoire search (embed the query) and the lore backfill (embed
//! each lore entry). Returns raw `Vec<f32>` vectors for pgvector storage/search.

use anyhow::{anyhow, Context};
use serde::Deserialize;
use serde_json::json;

const DEFAULT_BASE_URL: &str = "https://api.openai.com/v1";
const DEFAULT_MODEL: &str = "text-embedding-3-small";

/// Dimensionality of `text-embedding-3-small`; must match `vector(N)` in migration 004.
pub const EMBEDDING_DIMS: usize = 1536;

#[derive(Clone)]
pub struct EmbeddingClient {
    http: reqwest::Client,
    base_url: String,
    api_key: String,
    model: String,
}

impl EmbeddingClient {
    pub fn new(
        http: reqwest::Client,
        base_url: impl Into<String>,
        api_key: impl Into<String>,
        model: impl Into<String>,
    ) -> Self {
        Self {
            http,
            base_url: base_url.into(),
            api_key: api_key.into(),
            model: model.into(),
        }
    }

    /// Builds from `EMBEDDING_BASE_URL`/`LLM_BASE_URL`, `EMBEDDING_MODEL`, and
    /// `EMBEDDING_API_KEY`/`LLM_API_KEY`/`OPENAI_API_KEY`. `None` if no key is set.
    pub fn from_env(http: reqwest::Client) -> Option<Self> {
        let api_key = std::env::var("EMBEDDING_API_KEY")
            .or_else(|_| std::env::var("LLM_API_KEY"))
            .or_else(|_| std::env::var("OPENAI_API_KEY"))
            .ok()
            .filter(|k| !k.trim().is_empty())?;
        let base_url = std::env::var("EMBEDDING_BASE_URL")
            .or_else(|_| std::env::var("LLM_BASE_URL"))
            .unwrap_or_else(|_| DEFAULT_BASE_URL.into());
        let model = std::env::var("EMBEDDING_MODEL").unwrap_or_else(|_| DEFAULT_MODEL.into());
        Some(Self::new(http, base_url, api_key, model))
    }

    /// Embeds a single string.
    pub async fn embed(&self, input: &str) -> Result<Vec<f32>, anyhow::Error> {
        let mut out = self.embed_batch(std::slice::from_ref(&input.to_string())).await?;
        out.pop()
            .ok_or_else(|| anyhow!("embeddings API returned no vector"))
    }

    /// Embeds a batch of strings, preserving input order.
    pub async fn embed_batch(&self, inputs: &[String]) -> Result<Vec<Vec<f32>>, anyhow::Error> {
        if inputs.is_empty() {
            return Ok(Vec::new());
        }

        let url = format!("{}/embeddings", self.base_url.trim_end_matches('/'));
        let resp: EmbeddingResponse = self
            .http
            .post(&url)
            .bearer_auth(&self.api_key)
            .json(&json!({ "model": self.model, "input": inputs }))
            .send()
            .await
            .context("calling embeddings API")?
            .error_for_status()
            .context("embeddings API returned an error status")?
            .json()
            .await
            .context("decoding embeddings response")?;

        let mut data = resp.data;
        // The API may return out of order; sort by the index it echoes back.
        data.sort_by_key(|d| d.index);
        Ok(data.into_iter().map(|d| d.embedding).collect())
    }
}

#[derive(Debug, Deserialize)]
struct EmbeddingResponse {
    data: Vec<EmbeddingDatum>,
}

#[derive(Debug, Deserialize)]
struct EmbeddingDatum {
    index: usize,
    embedding: Vec<f32>,
}
