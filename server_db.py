"""Lightweight JSON persistence for users, OAuth tokens, and chats."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Optional

STORE_PATH = Path(__file__).resolve().parent / "data" / "store.json"
STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _default_store() -> dict[str, Any]:
    return {
        "users": [],
        "bungie_tokens": {},
        "conversations": [],
        "messages": [],
        "next_user_id": 1,
    }


def _load_store() -> dict[str, Any]:
    if not STORE_PATH.exists():
        return _default_store()
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return _default_store()


def _save_store(store: dict[str, Any]) -> None:
    STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


def init_db() -> None:
    if not STORE_PATH.exists():
        _save_store(_default_store())


def create_user(email: str, password_hash: str) -> int:
    store = _load_store()
    user_id = int(store["next_user_id"])
    store["next_user_id"] = user_id + 1
    store["users"].append(
        {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "created_at": "now",
        }
    )
    _save_store(store)
    return user_id


def get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    store = _load_store()
    for user in store["users"]:
        if user["email"] == email:
            return user
    return None


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    store = _load_store()
    for user in store["users"]:
        if int(user["id"]) == int(user_id):
            return user
    return None


def upsert_bungie_tokens(user_id: int, tokens: dict[str, Any]) -> None:
    store = _load_store()
    store["bungie_tokens"][str(user_id)] = {
        "user_id": user_id,
        **tokens,
    }
    _save_store(store)


def get_bungie_tokens(user_id: int) -> dict[str, Any] | None:
    store = _load_store()
    return store["bungie_tokens"].get(str(user_id))


def ensure_conversation(conversation_id: str, user_id: int, name: str, provider: str | None) -> None:
    store = _load_store()
    existing = next((c for c in store["conversations"] if c["id"] == conversation_id), None)
    if existing:
        existing["provider"] = provider or existing.get("provider")
        existing["updated_at"] = "now"
    else:
        store["conversations"].append(
            {
                "id": conversation_id,
                "user_id": user_id,
                "name": name,
                "provider": provider,
                "created_at": "now",
                "updated_at": "now",
            }
        )
    _save_store(store)


def append_message(conversation_id: str, msg_id: str, role: str, content: str) -> None:
    store = _load_store()
    store["messages"].append(
        {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "ts": "now",
        }
    )
    for conversation in store["conversations"]:
        if conversation["id"] == conversation_id:
            conversation["updated_at"] = "now"
            break
    _save_store(store)


def list_conversations(user_id: int) -> list[dict[str, Any]]:
    store = _load_store()
    items = [c for c in store["conversations"] if int(c["user_id"]) == int(user_id)]
    return sorted(items, key=lambda c: c.get("updated_at", ""), reverse=True)


def get_conversation_messages(conversation_id: str, user_id: int) -> list[dict[str, Any]]:
    store = _load_store()
    owned = any(
        c for c in store["conversations"] if c["id"] == conversation_id and int(c["user_id"]) == int(user_id)
    )
    if not owned:
        return []
    return [m for m in store["messages"] if m["conversation_id"] == conversation_id]


def create_conversation(user_id: int, name: str, provider: str | None, conv_id: str | None = None) -> str:
    conv_id = conv_id or f"conv-{uuid.uuid4().hex}"
    ensure_conversation(conv_id, user_id, name, provider)
    return conv_id


def rename_conversation(conversation_id: str, user_id: int, name: str) -> None:
    store = _load_store()
    for conversation in store["conversations"]:
        if conversation["id"] == conversation_id and int(conversation["user_id"]) == int(user_id):
            conversation["name"] = name
            conversation["updated_at"] = "now"
            break
    _save_store(store)


def update_conversation_provider(conversation_id: str, user_id: int, provider: str | None) -> None:
    store = _load_store()
    for conversation in store["conversations"]:
        if conversation["id"] == conversation_id and int(conversation["user_id"]) == int(user_id):
            conversation["provider"] = provider
            conversation["updated_at"] = "now"
            break
    _save_store(store)


def delete_conversation(conversation_id: str, user_id: int) -> None:
    store = _load_store()
    store["conversations"] = [
        c for c in store["conversations"] if not (c["id"] == conversation_id and int(c["user_id"]) == int(user_id))
    ]
    store["messages"] = [m for m in store["messages"] if m["conversation_id"] != conversation_id]
    _save_store(store)
