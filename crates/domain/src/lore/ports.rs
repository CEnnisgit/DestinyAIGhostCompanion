use async_trait::async_trait;

#[async_trait]
pub trait GrimoireDatabasePort: Send + Sync {
    /// Executes a RAG (Retrieval-Augmented Generation) semantic search against the Bungie Manifest.
    async fn fetch_semantic_lore_context(&self, topic: &str) -> Result<String, anyhow::Error>;
}
