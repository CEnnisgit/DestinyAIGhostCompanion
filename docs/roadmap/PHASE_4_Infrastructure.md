# Phase 4: Infrastructure

> **Status:** 🟡 Up Next
> **Objective:** Connect the pristine Domain Ports to the real world, finalizing the Rust backend for cloud/desktop hybrid deployment.
> **Scope:** `crates/db` (Postgres & RAG), `crates/api` (Axum/Reqwest), and Dockerization.

---

## 1. DevOps & Containerization
Because this backend serves both a web version and the Electron desktop client, it is designed to run in the cloud.
- [ ] **Docker** — Containerize the Rust workspace (multi-stage build).
- [ ] **Docker Compose** — Scaffold a `docker-compose.yml` that provisions a **PostgreSQL 15+** database with `pgvector` enabled for semantic search.
- [ ] **Database Migrations** — Setup `sqlx-cli` for Postgres migrations.

---

## 2. The Database (`crates/db`)

### Token Persistence
- [ ] Implement `PostgresTokenStorageAdapter` using `sqlx` to strictly persist Bungie OAuth session keys securely in Postgres.

### The Manifest & RAG Pipeline
Bungie distributes its manifest as an SQLite file. Because our primary datastore is Postgres, we need an ETL pipeline.
- [ ] Create a background worker that pings Bungie, downloads the `.sqlite` Manifest zip, and extracts it to memory/disk.
- [ ] Transform the Destiny definitions (Items, Lore) and run an UPSERT into our **PostgreSQL** tables.
- [ ] Implement `ManifestDatabaseAdapter` to perform fast index lookups and pgvector semantic searches against the Postgres Lore tables for the RAG engine.

---

## 3. The Networking (`crates/api`)

### Bungie Client
- [ ] Implement `reqwest` HTTP wrappers for `TransferItem` and `EquipItem`.
- [ ] Implement automatic 401 Unauthorized token refreshes inside the client port.

### Generative AI
- [ ] Point the `GenerativeAiPort` to the desired LLM API (OpenAI or open-source fallback) to power Ghost's conversational responses.

### WebSocket/HTTP Server
- [ ] Scaffold an `axum` Web server exposing a WebSocket connection for the Electron desktop client / web frontend to stream continuous voice commands.
