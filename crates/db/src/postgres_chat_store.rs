//! Postgres adapter for the chats domain's `ChatStorePort` (cross-device sync).
//!
//! Backs the `chat_threads` / `chat_messages` tables (migration 008). Every query
//! is scoped by `owner_id` so a Guardian can only ever read or mutate their own
//! conversations. UUIDs are cast to/from `text` so the workspace needs no extra
//! sqlx UUID feature, and runtime queries keep it buildable without a live DB.

use anyhow::Context;
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::{PgPool, Row};

use domain::chats::model::{ChatThread, ChatThreadSummary, NewMessage, StoredMessage};
use domain::chats::ports::ChatStorePort;

pub struct PostgresChatStore {
    pool: PgPool,
}

impl PostgresChatStore {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl ChatStorePort for PostgresChatStore {
    async fn list_threads(&self, owner: &str) -> Result<Vec<ChatThreadSummary>, anyhow::Error> {
        let rows = sqlx::query(
            "SELECT id::text AS id, title, updated_at
             FROM chat_threads WHERE owner_id = $1
             ORDER BY updated_at DESC",
        )
        .bind(owner)
        .fetch_all(&self.pool)
        .await
        .context("listing chat threads")?;

        Ok(rows
            .into_iter()
            .map(|r| ChatThreadSummary {
                id: r.get("id"),
                title: r.get("title"),
                updated_at: r.get::<DateTime<Utc>, _>("updated_at"),
            })
            .collect())
    }

    async fn create_thread(
        &self,
        owner: &str,
        title: &str,
    ) -> Result<ChatThreadSummary, anyhow::Error> {
        let row = sqlx::query(
            "INSERT INTO chat_threads (owner_id, title)
             VALUES ($1, $2)
             RETURNING id::text AS id, title, updated_at",
        )
        .bind(owner)
        .bind(title)
        .fetch_one(&self.pool)
        .await
        .context("creating chat thread")?;

        Ok(ChatThreadSummary {
            id: row.get("id"),
            title: row.get("title"),
            updated_at: row.get::<DateTime<Utc>, _>("updated_at"),
        })
    }

    async fn get_thread(
        &self,
        owner: &str,
        thread_id: &str,
    ) -> Result<Option<ChatThread>, anyhow::Error> {
        // Ownership check + summary in one shot. `$2::uuid` validates the id
        // shape; a malformed id simply yields no row.
        let head = sqlx::query(
            "SELECT id::text AS id, title, updated_at
             FROM chat_threads WHERE owner_id = $1 AND id = $2::uuid",
        )
        .bind(owner)
        .bind(thread_id)
        .fetch_optional(&self.pool)
        .await
        .context("fetching chat thread")?;

        let Some(head) = head else { return Ok(None) };

        let rows = sqlx::query(
            "SELECT id::text AS id, role, body, intent, created_at
             FROM chat_messages WHERE thread_id = $1::uuid
             ORDER BY created_at",
        )
        .bind(thread_id)
        .fetch_all(&self.pool)
        .await
        .context("fetching chat messages")?;

        let messages = rows
            .into_iter()
            .map(|r| StoredMessage {
                id: r.get("id"),
                role: r.get("role"),
                text: r.get("body"),
                intent: r.try_get("intent").ok(),
                created_at: r.get::<DateTime<Utc>, _>("created_at"),
            })
            .collect();

        Ok(Some(ChatThread {
            id: head.get("id"),
            title: head.get("title"),
            updated_at: head.get::<DateTime<Utc>, _>("updated_at"),
            messages,
        }))
    }

    async fn append_message(
        &self,
        owner: &str,
        thread_id: &str,
        message: NewMessage,
    ) -> Result<Option<StoredMessage>, anyhow::Error> {
        // Guard: only the owner's thread. Returns None when not found/owned.
        let owns = sqlx::query(
            "SELECT 1 FROM chat_threads WHERE owner_id = $1 AND id = $2::uuid",
        )
        .bind(owner)
        .bind(thread_id)
        .fetch_optional(&self.pool)
        .await
        .context("verifying thread ownership")?;
        if owns.is_none() {
            return Ok(None);
        }

        let row = sqlx::query(
            "INSERT INTO chat_messages (thread_id, role, body, intent)
             VALUES ($1::uuid, $2, $3, $4)
             RETURNING id::text AS id, role, body, intent, created_at",
        )
        .bind(thread_id)
        .bind(&message.role)
        .bind(&message.text)
        .bind(&message.intent)
        .fetch_one(&self.pool)
        .await
        .context("appending chat message")?;

        sqlx::query("UPDATE chat_threads SET updated_at = NOW() WHERE id = $1::uuid")
            .bind(thread_id)
            .execute(&self.pool)
            .await
            .context("bumping thread timestamp")?;

        Ok(Some(StoredMessage {
            id: row.get("id"),
            role: row.get("role"),
            text: row.get("body"),
            intent: row.try_get("intent").ok(),
            created_at: row.get::<DateTime<Utc>, _>("created_at"),
        }))
    }

    async fn rename_thread(
        &self,
        owner: &str,
        thread_id: &str,
        title: &str,
    ) -> Result<(), anyhow::Error> {
        sqlx::query(
            "UPDATE chat_threads SET title = $3, updated_at = NOW()
             WHERE owner_id = $1 AND id = $2::uuid",
        )
        .bind(owner)
        .bind(thread_id)
        .bind(title)
        .execute(&self.pool)
        .await
        .context("renaming chat thread")?;
        Ok(())
    }

    async fn delete_thread(&self, owner: &str, thread_id: &str) -> Result<(), anyhow::Error> {
        sqlx::query("DELETE FROM chat_threads WHERE owner_id = $1 AND id = $2::uuid")
            .bind(owner)
            .bind(thread_id)
            .execute(&self.pool)
            .await
            .context("deleting chat thread")?;
        Ok(())
    }
}
