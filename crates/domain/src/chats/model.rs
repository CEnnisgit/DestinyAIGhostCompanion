//! Entities for cross-device chat sync. A `ChatThread` is one conversation,
//! owned by a Guardian and synced server-side so it follows them across devices.

use chrono::{DateTime, Utc};
use serde::Serialize;

/// A conversation's summary (for the sidebar/list — no messages).
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct ChatThreadSummary {
    pub id: String,
    pub title: String,
    pub updated_at: DateTime<Utc>,
}

/// A single stored message within a thread.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct StoredMessage {
    pub id: String,
    /// "guardian" (the player) or "ghost" (the assistant).
    pub role: String,
    pub text: String,
    /// Optional intent label the backend tagged the reply with.
    pub intent: Option<String>,
    pub created_at: DateTime<Utc>,
}

/// A full conversation: summary plus its messages, in order.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct ChatThread {
    pub id: String,
    pub title: String,
    pub updated_at: DateTime<Utc>,
    pub messages: Vec<StoredMessage>,
}

/// A message to append (id/timestamp are assigned by the store).
#[derive(Debug, Clone, PartialEq)]
pub struct NewMessage {
    pub role: String,
    pub text: String,
    pub intent: Option<String>,
}

impl NewMessage {
    pub fn new(role: impl Into<String>, text: impl Into<String>, intent: Option<String>) -> Self {
        Self {
            role: role.into(),
            text: text.into(),
            intent,
        }
    }
}
