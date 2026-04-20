# Technology Stack

## Overview
This document fulfills the second component of the System Architecture: an explanation of the employed programming languages, patterns, and tools chosen to implement the Plumbers Compliance Dispatch (PCD) system.

## Programming Languages

| Context | Language | Notes |
|---------|----------|-------|
| **Backend Core** | Rust | Domain logic, API server, database queries. Chosen for type safety, performance, and reliability. |
| **Dashboard** | TypeScript / React | Next.js dev dashboard for data exploration and testing. |
| **Mobile** | React Native (future) | Cross-platform mobile framework via Expo. Not yet started. |

## Patterns

| Pattern | Description |
|---------|-------------|
| **Crate-Based Separation** | Domain logic (`pcd-domain`), persistence (`pcd-db`), and HTTP (`pcd-api`) are separate Rust crates with strict dependency rules (see [LayerDefinitions.md](LayerDefinitions.md)). |
| **Domain-Driven Design** | Aggregates, Value Objects, and Domain Events model the business. See [ModuleDesign/](../ModuleDesign/). |
| **Modular Monolith** | Logic is split into domain modules (CRM, Jobs) but compiled into a single binary. |
| **Stateless Auth** | JWT-based authentication with RBAC (planned — see [SecurityStrategy.md](SecurityStrategy.md)). |
| **Offline-First** | Mobile app will capture data locally and sync when connected (future). |

## Tools

| Category | Tool | Purpose |
|----------|------|---------|
| **API Framework** | Axum | Async HTTP server for `crates/pcd-api`. Built on Tokio. |
| **Database** | PostgreSQL | Relational persistence for all data. Uses JSONB and specialized indexes. |
| **SQL Driver** | sqlx | Compile-time checked SQL queries. No ORM — raw SQL for clarity. |
| **Serialization** | serde + serde_json | Rust serialization framework. API responses use `#[serde(rename_all = "camelCase")]`. |
| **Hosting** | Google Cloud Run | Serverless container deployment (planned). |
| **Storage** | Google Cloud Storage | Blob storage for inspection photos (future). |
| **Dashboard** | Next.js 15 | React-based dev dashboard in `apps/dev-dashboard`. |
| **Package Mgr** | pnpm | Manages JS/TS workspace packages in `apps/`. |
| **Build (Rust)** | cargo | Rust build system and package manager. |
| **Build (TS)** | Vite / Next.js | Frontend build tools. |

## Monorepo Structure

```
pcd/
├── apps/                → Deployable units (TS/Next.js)
│   ├── dev-dashboard/   → Next.js development dashboard
│   ├── pad-ingestion/   → PAD data ingestion pipeline
│   └── ll152-ingestion/ → LL152 compliance ingestion
├── crates/              → Rust crates (core system)
│   ├── pcd-api/         → Axum HTTP server + route handlers
│   ├── pcd-domain/      → Pure domain: aggregates, VOs, events, traits
│   └── pcd-db/          → sqlx queries + repository implementations
├── docs/                → Documentation (DDD, ADRs, deferred backlog)
├── .archive/            → Pre-Rust TS code (reference only)
└── Cargo.toml           → Rust workspace manifest
```

## Rationale

- **Rust:** Chosen over Node.js/TypeScript for the backend to eliminate runtime type errors, improve performance, and leverage the ownership model for safer concurrency.
- **Axum:** Lightweight, Tokio-native async HTTP. Simpler than Actix; better ergonomics than raw Hyper.
- **sqlx over ORM:** Raw SQL provides full control, avoids query-builder abstraction leaks. Compile-time query checking catches schema drift early.
- **Crate separation:** `pcd-domain` has zero infrastructure deps — pure business logic that can be tested without a database or HTTP server.
- **Google Cloud Run:** Minimizes ops overhead with scale-to-zero efficiency.

## Assumptions and Constraints

- **Google Cloud:** The system targets a GCP environment; migration would require infrastructure refactoring.
- **PostgreSQL specific:** Relies on Postgres features (JSONB, CTEs, lateral joins) throughout.
- **Hybrid monorepo:** Rust crates (`crates/`) coexist with TS/Next.js apps (`apps/`) managed by pnpm workspaces.
