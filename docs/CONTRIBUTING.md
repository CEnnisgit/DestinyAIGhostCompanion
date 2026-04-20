# Contributing Guide

Thank you for contributing to **Plumbers Compliance & Dispatch**!

## Tech Stack Overview

| Layer | Language | Framework | Notes |
|-------|----------|-----------|-------|
| Domain | Rust | — | Pure business logic, no dependencies |
| Database | Rust | SQLx (raw SQL) | No ORM — explicit queries |
| API | Rust | Axum + Tokio | REST endpoints |
| Web Dashboard | TypeScript | React + Vite | Company dashboard |
| Mobile App | TypeScript | React Native | Field technician (scaffold) |
| Dev Tools | TypeScript | Next.js | Internal dashboard |

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming:**
- `feature/` — New features
- `fix/` — Bug fixes
- `docs/` — Documentation changes
- `refactor/` — Code refactoring
- `chore/` — Maintenance tasks

### 2. Make Changes

- Follow the code style guides below
- Add tests for new functionality
- Update documentation if the change affects APIs or domain behavior

### 3. Test Locally

```bash
# Rust: run all workspace tests
cargo test --workspace

# Rust: run tests for a specific crate
cargo test -p pcd-domain
cargo test -p pcd-api
cargo test -p pcd-db

# Rust: check compilation without running
cargo check --workspace

# TypeScript: lint
pnpm lint
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat(jobs): add technician assignment command"
```

**Commit message format (Conventional Commits):**

```
<type>(<scope>): <description>

[optional body]
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation
- `refactor` — Code restructuring
- `test` — Adding tests
- `chore` — Maintenance

**Scopes (match domain modules):**
- `jobs` — Job Engine (aggregate, VOs, state machine)
- `crm` — CRM module (buildings, compliance)
- `tenant` — Tenant module (clients, saved buildings)
- `ll152` — LL152 workflow
- `api` — API routes and HTTP concerns
- `db` — Database queries and migrations
- `dashboard` — Web dashboard
- `pipeline` — Data pipelines (PAD, LL152 ingestion)

**Examples:**
```
feat(ll152): add findings capture endpoint
fix(jobs): handle terminal state guard for cancel
docs(adr): add ADR-0025 dual-status model
refactor(db): extract common query patterns
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Rust

**Domain layer (`pcd-domain`):**
- Pure business logic — no `sqlx`, no `axum`, no HTTP types
- Value objects are closed enumerations with `from_str()`/`as_str()` patterns
- Aggregates use factory methods (`Job::open()`) and command methods (`job.start()`)
- All VOs serialize with `#[serde(rename_all = "SCREAMING_SNAKE_CASE")]`
- Domain events are emitted from aggregate commands, stored in `uncommitted_events`

```rust
// Good: closed VO with standard interface
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Priority {
    Normal,
    High,
    Urgent,
}

impl Priority {
    pub fn from_str(s: &str) -> Result<Self, String> { ... }
    pub fn as_str(&self) -> &'static str { ... }
}
```

**Database layer (`pcd-db`):**
- Raw SQLx — no ORM
- Repository implementations live here
- Functions return `anyhow::Result<T>`
- Use `sqlx::FromRow` derive when mapping full rows

**API layer (`pcd-api`):**
- Axum handlers
- Request/response types use `#[serde(rename_all = "camelCase")]` (ADR-0019)
- Compose state with `Arc<dyn Trait>` for repository injection

```rust
// Good: camelCase at the serialization boundary
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct JobResponse {
    pub job_id: Uuid,
    pub job_number: String,
    pub job_type: String,
    pub job_status: String,
}
```

### TypeScript / React

- Use functional components with hooks
- Group by feature, not by type
- Use descriptive variable names
- Export types from modules

```typescript
// Good
export function JobCard({ job }: JobCardProps) {
  const { status } = useJobStatus(job.id);
  return <Card>...</Card>;
}
```

## Project Organization

### Rust Crate Boundaries

```
pcd-domain  →  Pure domain (NO external deps beyond serde/chrono/uuid)
     ↑
pcd-db      →  SQLx repositories (depends on pcd-domain)
     ↑
pcd-api     →  Axum HTTP (depends on pcd-domain + pcd-db)
```

The dependency arrow flows **inward** — domain knows nothing about the database or HTTP.

### Domain Module Layout

```
pcd-domain/src/
├── jobs/             ← Job Engine
│   ├── mod.rs           Module root + re-exports
│   ├── job.rs           Aggregate root (factory, commands)
│   ├── job_status.rs    VO: OPEN → IN_PROGRESS → COMPLETED/CANCELED
│   ├── job_type.rs      VO: LL152_INSPECTION, EMERGENCY, REPAIR
│   ├── job_number.rs    VO: validated job identifier
│   ├── priority.rs      VO: NORMAL, HIGH, URGENT
│   ├── source_kind.rs   VO: why the job was created
│   ├── events.rs        Domain events (11 types)
│   ├── repository.rs    Repository trait (port)
│   └── tests.rs         Unit tests
├── crm/              ← CRM (global, pipeline-populated)
│   ├── building.rs      Building entity
│   └── compliance_obligation.rs
├── tenant/           ← Tenant (company-scoped, user-created)
│   ├── client.rs        Client aggregate
│   ├── saved_building.rs
│   ├── repository.rs    Repository traits
│   └── tests.rs
└── ll152/            ← LL152 Workflow (Job extension)
    ├── workflow_status.rs  VO: DRAFT → CAPTURING → READY_FOR_REVIEW
    ├── branch.rs           VO: compliance branch (A/B/C)
    ├── details.rs          1:1 extension entity
    ├── findings.rs         GPS1 inspection findings
    ├── photos.rs           Photo evidence
    ├── events.rs           Workflow-specific events
    └── tests.rs
```

## Adding New Features

### Backend: New Domain Entity

1. Create types in `crates/pcd-domain/src/<module>/`
2. Add repository trait in domain if needed
3. Write domain unit tests
4. Implement SQL queries in `crates/pcd-db/src/<module>/`
5. Add API routes in `crates/pcd-api/src/routes/`
6. Wire state in `main.rs`

### Backend: New API Endpoint

1. Add handler function in the appropriate route module
2. Define request/response types with `#[serde(rename_all = "camelCase")]`
3. Register the route in the module's `router()` function
4. Test with `curl` or the web dashboard

### Frontend Feature

1. Create components in the dashboard's `src/components/`
2. Add API fetch logic
3. Wire into pages

## Documentation Standards (PDA-SDD)

This project follows the **PDA-SDD** methodology. When adding significant features:

1. **Before coding** — Check for existing specs in `docs/1-pre-implementation/`
2. **During coding** — Update DDD specs in `docs/2-during-implementation/DDD/`
3. **After coding** — Log completions in `docs/2-during-implementation/CLD/`

See [`docs/PDA_SDD_PHILOSOPHY.md`](PDA_SDD_PHILOSOPHY.md) for the full framework.

## Pull Request Checklist

- [ ] Code follows the style guides above
- [ ] Rust tests pass (`cargo test --workspace`)
- [ ] Linting passes (`pnpm lint` for TS)
- [ ] Rust compiles clean (`cargo check --workspace`)
- [ ] Documentation updated (if API or domain behavior changed)
- [ ] Commit messages follow Conventional Commits format
- [ ] PR description explains the "why", not just the "what"
