//! The driven port for chat persistence. Every method is scoped by `owner`
//! (the Guardian's membership id) so a user can only ever touch their own
//! conversations — the store enforces this, not the caller.

use async_trait::async_trait;

use super::model::{ChatThread, ChatThreadSummary, NewMessage, StoredMessage};

#[async_trait]
pub trait ChatStorePort: Send + Sync {
    /// All of the owner's threads, most-recently-updated first.
    async fn list_threads(&self, owner: &str) -> Result<Vec<ChatThreadSummary>, anyhow::Error>;

    /// Creates a new empty thread and returns its summary.
    async fn create_thread(
        &self,
        owner: &str,
        title: &str,
    ) -> Result<ChatThreadSummary, anyhow::Error>;

    /// Fetches one thread with its messages, or `None` if it isn't the owner's.
    async fn get_thread(
        &self,
        owner: &str,
        thread_id: &str,
    ) -> Result<Option<ChatThread>, anyhow::Error>;

    /// Appends a message and bumps the thread's `updated_at`. Returns the stored
    /// message, or `None` if the thread isn't the owner's.
    async fn append_message(
        &self,
        owner: &str,
        thread_id: &str,
        message: NewMessage,
    ) -> Result<Option<StoredMessage>, anyhow::Error>;

    /// Renames a thread. No-op if it isn't the owner's.
    async fn rename_thread(
        &self,
        owner: &str,
        thread_id: &str,
        title: &str,
    ) -> Result<(), anyhow::Error>;

    /// Deletes a thread (and its messages). No-op if it isn't the owner's.
    async fn delete_thread(&self, owner: &str, thread_id: &str) -> Result<(), anyhow::Error>;
}
