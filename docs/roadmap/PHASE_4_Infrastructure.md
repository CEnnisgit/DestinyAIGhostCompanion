# Phase 4: Infrastructure

> **Status:** 🟡 Up Next
> **Objective:** Connect the pristine Domain Ports to the chaotic real world.
> **Scope:** `crates/db` (SQLite caching & Token persistence), `crates/api` (Bungie HTTP `reqwest` calls, WebSocket listeners).

---

## The Database (`crates/db`)

### 1. Token Storage
- [ ] Implement `SqliteTokenStoragePort` to securely persist Bungie OAuth keys locally.

### 2. The Manifest Pipeline
- [ ] Create logic to automatically ping Bungie and download the `.sqlite` Manifest zip on application boot.
- [ ] Implement the `ManifestDatabasePort` using `sqlite`/`sqlx` for RAG Lore semantic searching.

---

## The Networking (`crates/api`)

### 1. Bungie Client
- [ ] Implement `reqwest` wrappers to securely hit `TransferItem` and `EquipItem`.
- [ ] Handle 401 Unauthorized token refreshes automatically inside the client.

### 2. Generative AI
- [ ] Point the `GenerativeAiPort` to generic OpenAI endpoints (compatible with local Ollama fallback).

### 3. Desktop Listener
- [ ] Scaffold an internal WebServer (e.g. `axum`) that listens on localhost for the Electron frontend.
