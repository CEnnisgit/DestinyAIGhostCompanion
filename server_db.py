"""Lightweight SQLite persistence for users, OAuth tokens, and chats.

Tables
- users: minimal auth (email + password_hash) for server-managed sessions.
- bungie_tokens: per-user Bungie OAuth tokens and membership metadata.
- conversations/messages: server-side storage of chat history per user.

This module centralizes schema and CRUD operations so the API layer can
depend on simple, typed helpers. Connections use `Row` factory so rows can
be accessed like dictionaries and serialized easily.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterable, Any

DB_PATH = Path("data/app.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    """Return a connection with `Row` factory and ensured DB path.

    Note: Callers should prefer the context manager style (`with get_conn():`)
    so commits/rollbacks and connection close are handled automatically.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables on first run; safe to call multiple times."""
    with get_conn() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS bungie_tokens (
                user_id INTEGER NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                membership_id TEXT,
                membership_type INTEGER,
                access_token_expires REAL,
                updated_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (user_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                provider TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                ts TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
            """
        )


def create_user(email: str, password_hash: str) -> int:
    """Insert a new user and return its integer id."""
    with get_conn() as con:
        cur = con.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, password_hash))
        return int(cur.lastrowid)


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    """Lookup a user row by email; returns `None` if not found."""
    with get_conn() as con:
        cur = con.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cur.fetchone()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    """Lookup a user row by integer id; returns `None` if not found."""
    with get_conn() as con:
        cur = con.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cur.fetchone()


def upsert_bungie_tokens(user_id: int, tokens: dict[str, Any]) -> None:
    """Insert or update Bungie OAuth tokens for the given `user_id`.

    Stores expiry and membership hints to speed up auth-dependent flows.
    """
    with get_conn() as con:
        con.execute(
            """
            INSERT INTO bungie_tokens (user_id, access_token, refresh_token, membership_id, membership_type, access_token_expires)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                access_token=excluded.access_token,
                refresh_token=excluded.refresh_token,
                membership_id=excluded.membership_id,
                membership_type=excluded.membership_type,
                access_token_expires=excluded.access_token_expires,
                updated_at=datetime('now')
            """,
            (
                user_id,
                tokens.get("access_token"),
                tokens.get("refresh_token"),
                tokens.get("membership_id"),
                tokens.get("membership_type"),
                tokens.get("access_token_expires"),
            ),
        )


def get_bungie_tokens(user_id: int) -> dict[str, Any] | None:
    """Return Bungie tokens as a dict or `None` if missing."""
    with get_conn() as con:
        cur = con.execute("SELECT * FROM bungie_tokens WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)


# Conversations ---------------------------------------------------------------
def ensure_conversation(conversation_id: str, user_id: int, name: str, provider: str | None) -> None:
    """Create the conversation if absent; otherwise bump timestamp/provider."""
    with get_conn() as con:
        con.execute(
            """
            INSERT INTO conversations (id, user_id, name, provider)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                updated_at=datetime('now'),
                provider=COALESCE(excluded.provider, provider)
            """,
            (conversation_id, user_id, name, provider),
        )


def append_message(conversation_id: str, msg_id: str, role: str, content: str) -> None:
    """Append a message to a conversation and update its `updated_at`."""
    with get_conn() as con:
        con.execute(
            "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)",
            (msg_id, conversation_id, role, content),
        )
        con.execute(
            "UPDATE conversations SET updated_at=datetime('now') WHERE id = ?",
            (conversation_id,),
        )


def list_conversations(user_id: int) -> list[dict[str, Any]]:
    """Return recent conversations for a user ordered by last update."""
    with get_conn() as con:
        cur = con.execute(
            "SELECT id, name, provider, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def get_conversation_messages(conversation_id: str, user_id: int) -> list[dict[str, Any]]:
    """Return messages for a conversation if owned by `user_id`; else empty list."""
    with get_conn() as con:
        # Verify ownership
        c = con.execute("SELECT 1 FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)).fetchone()
        if not c:
            return []
        cur = con.execute(
            "SELECT id, role, content, ts FROM messages WHERE conversation_id = ? ORDER BY ts ASC",
            (conversation_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def create_conversation(user_id: int, name: str, provider: str | None, conv_id: str | None = None) -> str:
    """Create a new conversation and return its string id.

    If `conv_id` is omitted, a unique id is generated with a `conv-` prefix.
    """
    if not conv_id:
        conv_id = f"conv-{__import__('uuid').uuid4().hex}"
    with get_conn() as con:
        con.execute(
            "INSERT INTO conversations (id, user_id, name, provider) VALUES (?, ?, ?, ?)",
            (conv_id, user_id, name, provider),
        )
    return conv_id


def rename_conversation(conversation_id: str, user_id: int, name: str) -> None:
    """Rename a conversation owned by `user_id`. No-op if not found."""
    with get_conn() as con:
        con.execute(
            "UPDATE conversations SET name = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
            (name, conversation_id, user_id),
        )


def update_conversation_provider(conversation_id: str, user_id: int, provider: str | None) -> None:
    """Set the provider label for a conversation; useful for UI display."""
    with get_conn() as con:
        con.execute(
            "UPDATE conversations SET provider = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
            (provider, conversation_id, user_id),
        )


def delete_conversation(conversation_id: str, user_id: int) -> None:
    """Delete a conversation if it belongs to `user_id`."""
    with get_conn() as con:
        con.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
