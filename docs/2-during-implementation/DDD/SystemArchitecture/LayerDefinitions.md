# Architectural Patterns: Layer Definitions

> **Parent:** [Technology Stack](TechnologyStack.md)

This document explains the **Crate-Based Separation** pattern employed in the Rust backend, which achieves the goals of Hexagonal Architecture (Ports & Adapters) through Rust's crate dependency system.

---

## Crate Structure

The system is split into three Rust crates with strict dependency rules:

```
crates/
├── pcd-domain/    → Pure business logic (aggregates, VOs, events, traits)
│   └── src/
│       ├── crm/   → CRM module (Building, ComplianceObligation, ImportRun)
│       └── jobs/  → Jobs module (Job aggregate, status machine, value objects)
├── pcd-db/        → Database queries + repository implementations (sqlx)
│   └── src/
│       ├── crm/   → CRM queries (search, profile, timeline, obligations, anomalies)
│       └── jobs/  → Jobs persistence (save, find, reconstitute)
└── pcd-api/       → HTTP server + route handlers (Axum)
    └── src/
        ├── routes/crm.rs   → CRM API endpoints
        └── routes/jobs.rs  → Jobs API endpoints
```

### Dependency Rules

| Crate | Can Depend On | Cannot Depend On |
|-------|--------------|------------------|
| **pcd-domain** | Nothing (pure) | pcd-db, pcd-api |
| **pcd-db** | pcd-domain | pcd-api |
| **pcd-api** | pcd-domain, pcd-db | — (top of the stack) |

These rules are enforced by `Cargo.toml` — if `pcd-domain` tried to `use` anything from `pcd-db`, the Rust compiler would refuse to build. This is strictly enforced, not a convention.

### Comparison to Hexagonal Architecture

| Hexagonal Concept | Rust Equivalent |
|---|---|
| **Domain** (entities, VOs, business rules) | `pcd-domain` — pure logic, zero infrastructure deps |
| **Ports** (repository interfaces) | `trait` definitions in `pcd-domain` (e.g., `JobRepository` trait) |
| **Adapters** (implementations) | `pcd-db` — implements the traits using sqlx |
| **Application** (use cases) | Currently inlined in `pcd-api` route handlers. Can be extracted into a separate `pcd-application` crate if needed. |

> **Note:** The CRM module does not currently define repository traits. Its queries are called directly from `pcd-api` → `pcd-db`. The Jobs module follows the full trait-based pattern. This is a known simplification documented in the [deferred backlog](../../../deferred/rust-migration-backlog.md).

---

## System Layers

### 1. Apps Layer (`apps/`)
**Purpose:** Deployable entry points (non-Rust).

- **Responsibilities:**
  - Dev dashboard UI (`apps/dev-dashboard` — Next.js)
  - Ingestion pipelines (`apps/pad-ingestion`, `apps/ll152-ingestion`)
- **Constraints:**
  - NO business logic
  - Communicates with the Rust API over HTTP

### 2. Crates Layer (`crates/`)
**Purpose:** Core system logic in Rust.

- **Responsibilities:**
  - Domain logic and business rules (`pcd-domain`)
  - Database persistence and queries (`pcd-db`)
  - HTTP API routing and request handling (`pcd-api`)
- **Constraints:**
  - `pcd-domain` must remain framework-agnostic (no axum, no sqlx)
  - `pcd-db` does not know about HTTP concerns
  - `pcd-api` is a thin routing shell — no business logic

### 3. Data Layer
**Purpose:** PostgreSQL database.

- Single database shared across all crates via connection pool
- Schema managed via SQL migrations
- Uses PostgreSQL-specific features (JSONB, lateral joins, CTEs)

---

## Composition Root

The `pcd-api/src/main.rs` wires everything together:

```rust
// crates/pcd-api/src/main.rs (simplified)
let pool = PgPool::connect(&database_url).await?;

// CRM: direct DB facade (no trait)
let crm_repo = Arc::new(SqlxCrmRepository::new(pool.clone()));

// Jobs: trait-based repository
let job_repo = Arc::new(SqlxJobRepository::new(pool.clone()));

let app = Router::new()
    .nest("/api", crm::router().with_state(crm_repo))
    .nest("/api/jobs", jobs::router().with_state(job_repo));
```
