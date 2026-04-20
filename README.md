# Destiny AI Ghost Companion

A voice-controlled AI assistant for Destiny 2. Ask your Ghost to equip weapons, explain lore, manage your vault, and more — all through natural speech or text.

Built with **Rust** (backend) and **React + Electron** (desktop), using a **Hexagonal Architecture** with strict Domain-Driven Design boundaries.

---

## Project Structure

```
DestinyAIGhostCompanion/
│
├── crates/                    ← Rust library crates
│   ├── domain/                   Pure business logic (✅ Complete)
│   ├── db/                       PostgreSQL adapters (Phase 4)
│   └── api/                      HTTP + WebSocket adapters (Phase 4)
│
├── apps/                      ← Runnable applications
│   ├── server/                   Rust composition root (Phase 4)
│   ├── desktop/                  Electron + Web UI (Phase 5)
│   └── ios/                      Native iOS client (Future)
│
├── docs/                      ← Documentation
│   ├── roadmap/                  Phase trackers (4A–4E, 5A–5F)
│   ├── adr/                      16 Architectural Decision Records
│   └── 2-during-implementation/  DDD module designs
│
├── .cortex/workflows/         ← Agent slash commands
└── archive/                   ← Legacy Python code (reference only)
```

## Architecture

The codebase follows **Hexagonal Architecture** (Ports & Adapters):

- **`crates/domain/`** — Pure business logic. Contains sagas, value objects, and trait-based ports. Zero infrastructure dependencies. Already complete.
- **`crates/db/`** — PostgreSQL adapters implementing the domain's storage ports.
- **`crates/api/`** — HTTP clients (Bungie, OpenAI) and the axum WebSocket server.
- **`apps/server/`** — The composition root. A thin binary that wires the crates together and starts the listener. See [`apps/README.md`](apps/README.md) for details.

> **Key Rule:** The domain never imports infrastructure. Adapters talk to the domain through Rust traits (Ports).

## Domain Modules

| Module | Saga | What It Does |
|:-------|:-----|:-------------|
| `auth` | `OAuthSessionSaga` | Bungie OAuth2 login + token persistence |
| `voice_ai` | `VoiceCommandSaga` | Intent parsing with AI failover circuit |
| `inventory` | `EquipItemSaga` | Serial item equip/transfer/vault via Bungie API |
| `lore` | `LoreSaga` | RAG-powered semantic lore search |

## Tech Stack

| Layer | Technology |
|:------|:-----------|
| Domain Logic | Rust |
| Database | PostgreSQL 15 + pgvector |
| HTTP Server | axum + tokio |
| Bungie Client | reqwest |
| AI Provider | OpenAI-compatible (configurable via ADR 007) |
| Desktop App | Vite + React + TypeScript + Electron |
| iOS App | Swift + SwiftUI |
| Containers | Docker + Docker Compose |

## Getting Started

> **Prerequisites:** Rust toolchain, Docker Desktop, Node.js 18+

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Run database migrations
cargo sqlx migrate run

# 3. Start the backend
cargo run --bin ghost-server

# 4. Start the frontend (in another terminal)
cd apps/desktop && npm run dev
```

See [`ONBOARDING.md`](ONBOARDING.md) for a comprehensive guide.

## Roadmap

| Phase | Status | Description |
|:------|:-------|:------------|
| 1–3 | ✅ Complete | Domain Foundation — sagas, ports, value objects |
| 4 | 🟡 Up Next | [Infrastructure](docs/roadmap/PHASE_4_Infrastructure/README.md) — Docker, Postgres, Bungie API, OpenAI |
| 5 | 🔲 Queued | [Presentation](docs/roadmap/PHASE_5_Presentation/README.md) — Electron desktop + web UI |

## Key ADRs

| ADR | Decision |
|:----|:---------|
| 005 | Delegated Authentication — 100% Bungie OAuth2 SSO |
| 007 | Universal OpenAI LLM Adapter — any OpenAI-compatible API |
| 010 | Strict Serial Inventory Mutations — no concurrent Bungie requests |
| 015 | Lore Manifest Semantic Search — RAG via pgvector |

Full list in [`docs/adr/`](docs/adr/).

## Contributing

This project uses [Conventional Commits](https://www.conventionalcommits.org/). See [`docs/development/COMMITS.md`](docs/development/COMMITS.md) for the commit format and scopes.

## License

Private repository. All rights reserved.
