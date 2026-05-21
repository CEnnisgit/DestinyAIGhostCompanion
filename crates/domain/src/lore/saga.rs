use std::sync::Arc;

use super::ports::GrimoireDatabasePort;

/// The read-only orchestration engine for the Lore slice.
pub struct LoreSaga {
    db_port: Arc<dyn GrimoireDatabasePort>,
}

impl LoreSaga {
    pub fn new(db_port: Arc<dyn GrimoireDatabasePort>) -> Self {
        Self { db_port }
    }

    /// Takes a topic from the LLM Intent Parser, retrieves the RAG context from the SQLite database,
    /// and formats it for playback.
    pub async fn process_lore_query(&self, topic: &str) -> Result<String, String> {
        match self.db_port.fetch_semantic_lore_context(topic).await {
            Ok(context) => Ok(context),
            Err(_e) => Err(format!("I'm sorry, I could not find any records regarding '{}'.", topic)),
        }
    }
}
