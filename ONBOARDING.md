# Destiny AI Ghost Companion — Onboarding Guide

Welcome! If you are reading this, you are taking over the repository after a massive architectural pivot. 

While you originally built the foundation and database for the previous version of this project, **the architecture has been completely migrated to Enterprise Rust.**

This document will catch you up on exactly what changed, why it changed, and how the codebase is fundamentally structured today so you can hit the ground running in Phase 4.

---

## 1. The Great Migration (Python → Rust)

**What we deleted:**
The original `ghost/` Python directory contained a massive 3,000+ line monolithic architecture.

**What we built:**
We implemented strict **Domain-Driven Design (DDD)** using **Hexagonal Architecture (Ports and Adapters)**.
All pure business logic is safely quarantined inside `crates/domain/` with zero infrastructure dependencies.

The app is split into four Bounded Contexts:
1. `auth` — Bungie OAuth state.
2. `inventory` — Atomic cross-character equips.
3. `voice_ai` — Offline/online NLP intent parsing.
4. `lore` — Answers Destiny-specific questions.

---

## 2. Infrastructure: Docker & PostgreSQL (Your Phase 4 Mission)

Because this backend supports both the Electron Desktop Client and a web version, we run locally and remotely via **Docker and PostgreSQL (with pgvector)**.

> [!IMPORTANT]
> The `crates/domain` boundary never talks to Postgres or Docker directly. It only talks to traits (Ports). 
> **Your job is to build the Adapters in `crates/db/` and `crates/api/` that implement those traits.**

### Critical Deliverables for You:
1. **Dockerization:** Scaffold the multi-stage Dockerfile and the `docker-compose.yml` for PostgreSQL.
2. **Postgres Token Storage:** Implement the SQLite-to-Postgres shift for OAuth keys.
3. **The Bungie Manifest ETL:** Bungie provides an SQLite manifest. You must build a worker that downloads it and UPSERTs the data into our PostgreSQL database so we can run `pgvector` semantic searches on the Lore.
4. **Axum WebSockets:** Build the listener for the frontend to stream voice intentions.

---

## 3. Critical Destiny-Specific ADRs (Read `docs/adr/`)

### ADR 010 + 011: Strict Serial Mutations
Bungie enforces a harsh 25 requests/second rate limit. Concurrent item transfers cause failures. We implemented strict serial execution pipelines (`EquipItemSaga`). If an item is in the vault, we pull it first, await response, *then* equip it.

### ADR 014 + 015: Lore RAG
We deleted the PC-bound text files. We use **Retrieval-Augmented Generation (RAG)** against the official Bungie Manifest (which you will be caching in Postgres).

### ADR 005: Delegated Authentication
We do not store passwords. Identity management is 100% delegated to Bungie OAuth2 SSO. We only hold access and refresh tokens.

---

## 4. Workflows & Documentation

1. **The Roadmap**: Open `docs/roadmap/DESTINY_GHOST_ROADMAP.md`. You are starting Phase 4.
2. **The Tests**: See `docs/development/TESTING_MATRIX.md`. `crates/domain` is strictly unit tested. `crates/db` will be strictly Postgres integration-tested via `#[sqlx::test]`.
3. **Commit Formatting**: We strictly enforce Conventional Commits (e.g., `feat(inventory): add equip adapter`). See `docs/development/COMMITS.md`.

Welcome back to the Ghost Companion. Eyes up, Guardian.
