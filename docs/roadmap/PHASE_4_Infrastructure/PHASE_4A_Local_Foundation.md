# Phase 4A: Local Foundation

> **Status:** 🔲 Not Started
> **Objective:** Get Docker, PostgreSQL, and the Rust workspace compiling with database connectivity.
> **Crate:** N/A (DevOps scaffolding)

---

## Context for the Agent

This is the very first infrastructure task. The developer has Docker Desktop installed. Your job is to generate the containerization files and database migration scaffolding so the Rust backend can connect to a live PostgreSQL instance.

## Prerequisites
- [ ] Docker Desktop installed and running on the developer's machine.
- [ ] Rust toolchain installed (`cargo`, `rustc`).

## Deliverables

### 1. `docker-compose.yml` (Root of Repository)
Create a Docker Compose file that provisions:
- **PostgreSQL 15+** with the `pgvector` extension pre-installed.
  - Use image: `pgvector/pgvector:pg16`
  - Expose port `5432`.
  - Create a database named `ghost_companion`.
  - Use environment variables for credentials (do NOT hardcode secrets).
- **Volume** for persistent Postgres data (`pgdata`).

### 2. Multi-Stage `Dockerfile` (Root of Repository)
Create a Dockerfile for the Rust backend:
- **Stage 1 (Builder):** Use `rust:1.78-slim` as the base. Copy the workspace (`Cargo.toml`, `Cargo.lock`, `crates/`). Run `cargo build --release`.
- **Stage 2 (Runtime):** Use `debian:bookworm-slim`. Copy the compiled binary. Expose port `8080`. Set `CMD` to run the binary.

### 3. Database Migrations
- Add `sqlx` (with `postgres` and `runtime-tokio` features) to the workspace `Cargo.toml`.
- Create an initial migration at `migrations/001_create_tokens_table.sql`:
  ```sql
  CREATE TABLE IF NOT EXISTS bungie_tokens (
      membership_id TEXT PRIMARY KEY,
      access_token  TEXT NOT NULL,
      refresh_token TEXT NOT NULL,
      expires_at    TIMESTAMPTZ NOT NULL,
      created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );
  ```
- Create a second migration at `migrations/002_enable_pgvector.sql`:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

### 4. `.env.example` (Root of Repository)
Create a template (NOT a real `.env`) showing the required environment variables:
```
DATABASE_URL=postgres://ghost:ghost_dev@localhost:5432/ghost_companion
BUNGIE_API_KEY=your_bungie_api_key_here
BUNGIE_CLIENT_ID=your_bungie_client_id_here
BUNGIE_CLIENT_SECRET=your_bungie_client_secret_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Verification
- [ ] `docker compose up -d` starts Postgres without errors.
- [ ] `cargo sqlx migrate run` applies both migrations successfully.
- [ ] `cargo build` compiles the entire workspace without errors.

## ADR References
- None specific to this phase. This is pure infrastructure scaffolding.

## Next Phase
Once verified, proceed to → [Phase 4B: Auth Slice](./PHASE_4B_Auth_Slice.md)
