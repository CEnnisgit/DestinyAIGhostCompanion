# ADR 003: In-Memory Manifest Caching Pipeline

## Status
Accepted

## Context
Bungie's live player inventory endpoints (e.g., `GetProfile`) do not return human-readable item names (like "Sunshot"). They only return `itemInstanceId` and `itemHash` numbers. Translating these hashes into English is required before they can be piped into an LLM context window. In the legacy Python application, the Ghost attempted lazy lookups over HTTP to Bungie's `/Manifest/` endpoints, resulting in massive API request loops and excessive latency. 

## Decision
We will implement a robust, eagerly-loaded Manifest Cache inside the `crates/db` layer. 
When the Rust backend boots, it will execute a background job to download Bungie's latest Manifest SQLite database, extract the necessary definition tables (e.g., `DestinyInventoryItemDefinition`), and load them entirely into a thread-safe, in-memory HashMap (like `DashMap` or an `RwLock<HashMap>`).

## Consequences
- **Positive:** Rust can translate Destiny Hashes to human readable strings in 0.001ms with zero HTTP overhead. The AI assistant can operate incredibly fast since the entire Destiny encyclopedia is held in RAM.
- **Negative:** Increased host RAM usage for the backend server (~100-200MB depending on how much of the manifest is parsed), and a slower server boot time while the background job syncs.
