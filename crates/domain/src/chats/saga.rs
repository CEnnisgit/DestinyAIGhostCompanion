//! Use-cases for cross-device chat sync. A thin orchestration layer over the
//! [`ChatStorePort`]; ownership scoping lives in the store so it can't be
//! bypassed. Kept as a saga for symmetry with the other bounded contexts and so
//! cross-cutting policy (titling, trimming) has a home.

use std::sync::Arc;

use super::model::{ChatThread, ChatThreadSummary, NewMessage, StoredMessage};
use super::ports::ChatStorePort;

/// Max characters of the first message used to auto-title a fresh thread.
const TITLE_LEN: usize = 40;

pub struct ChatSyncSaga {
    store: Arc<dyn ChatStorePort>,
}

impl ChatSyncSaga {
    pub fn new(store: Arc<dyn ChatStorePort>) -> Self {
        Self { store }
    }

    pub async fn list(&self, owner: &str) -> Result<Vec<ChatThreadSummary>, anyhow::Error> {
        self.store.list_threads(owner).await
    }

    pub async fn create(
        &self,
        owner: &str,
        title: Option<&str>,
    ) -> Result<ChatThreadSummary, anyhow::Error> {
        let title = title
            .map(str::trim)
            .filter(|t| !t.is_empty())
            .unwrap_or("New Conversation");
        self.store.create_thread(owner, title).await
    }

    pub async fn get(
        &self,
        owner: &str,
        thread_id: &str,
    ) -> Result<Option<ChatThread>, anyhow::Error> {
        self.store.get_thread(owner, thread_id).await
    }

    /// Appends a message. When the thread is still untitled and this is a
    /// Guardian message, derives a title from it so synced sidebars read well.
    pub async fn append(
        &self,
        owner: &str,
        thread_id: &str,
        message: NewMessage,
    ) -> Result<Option<StoredMessage>, anyhow::Error> {
        if message.role == "guardian" {
            if let Some(thread) = self.store.get_thread(owner, thread_id).await? {
                if thread.title == "New Conversation" && thread.messages.is_empty() {
                    let title = derive_title(&message.text);
                    if !title.is_empty() {
                        self.store.rename_thread(owner, thread_id, &title).await?;
                    }
                }
            }
        }
        self.store.append_message(owner, thread_id, message).await
    }

    pub async fn rename(
        &self,
        owner: &str,
        thread_id: &str,
        title: &str,
    ) -> Result<(), anyhow::Error> {
        self.store.rename_thread(owner, thread_id, title.trim()).await
    }

    pub async fn delete(&self, owner: &str, thread_id: &str) -> Result<(), anyhow::Error> {
        self.store.delete_thread(owner, thread_id).await
    }
}

/// First line of `text`, trimmed to `TITLE_LEN` on a char boundary.
fn derive_title(text: &str) -> String {
    let first_line = text.lines().next().unwrap_or("").trim();
    if first_line.chars().count() <= TITLE_LEN {
        return first_line.to_string();
    }
    let truncated: String = first_line.chars().take(TITLE_LEN).collect();
    format!("{}…", truncated.trim_end())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn derive_title_truncates_long_input() {
        let long = "tell me everything about the rise of the witness and the final shape please";
        let title = derive_title(long);
        assert!(title.chars().count() <= TITLE_LEN + 1); // +1 for the ellipsis
        assert!(title.ends_with('…'));
    }

    #[test]
    fn derive_title_keeps_short_input() {
        assert_eq!(derive_title("who is Savathûn?"), "who is Savathûn?");
    }
}
