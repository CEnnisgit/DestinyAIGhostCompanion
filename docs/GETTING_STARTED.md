# Getting Started

Welcome to **Plumbers Compliance & Dispatch (PCD)** — an operations platform for NYC plumbing companies.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Rust** | 1.75+ | API server, domain logic, data pipelines |
| **Node.js** | 20+ | Web dashboard, dev tools |
| **pnpm** | 9+ | JavaScript package manager (monorepo) |
| **Docker** (recommended) | Latest | PostgreSQL + pgAdmin |
| **Git** | Latest | Version control |

> **Note:** PostgreSQL 15+ is required. Docker Compose is the easiest setup path.

## Quick Setup

### 1. Clone and Install

```bash
git clone https://github.com/MarsGetsGitty/pcd.git
cd pcd

# Install JS dependencies (web dashboard, dev tools)
pnpm install
```

### 2. Set Up Database

**Option A: Docker Compose (recommended)**

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

This starts:
- **PostgreSQL 15** on `localhost:5432` (user: `pcd`, password: `pcd123`, db: `plumbers_compliance`)
- **pgAdmin** on `localhost:5050` (email: `admin@pcd.com`, password: `admin123`)

**Option B: Local PostgreSQL**

Create a database named `plumbers_compliance` and set credentials in `.env`:

```bash
# .env (project root)
DATABASE_URL=postgresql://pcd:pcd123@localhost:5432/plumbers_compliance
```

### 3. Bootstrap the Database

The API server auto-creates tables on startup via SQLx migrations. For the PAD building data pipeline:

```bash
# Run the PAD ingestion pipeline with bootstrap flag
cargo run -p pad-ingestion -- --bootstrap
```

### 4. Start Development

```bash
# Terminal 1: Rust API server (port 8080)
cargo run -p pcd-api

# Terminal 2: Web Dashboard (port 3002)
pnpm --filter @pcd/web-dashboard dev

# Terminal 3 (optional): Dev Dashboard (port 3000)
pnpm --filter @pcd/dev-dashboard dev
```

## Verify It Works

| Service | URL | Expected |
|---------|-----|----------|
| API Health Check | http://localhost:8080/health | `ok` |
| Web Dashboard | http://localhost:3002 | Dashboard UI |
| pgAdmin | http://localhost:5050 | Database browser |

### Quick API Test

```bash
# List jobs (should return an empty array initially)
curl http://localhost:8080/api/jobs
```

## Project Structure

```
crates/                      ← Rust workspace (production backend)
├── pcd-api/                 Axum HTTP server (port 8080)
│   └── src/routes/          Jobs, CRM, Tenant, LL152 endpoints
├── pcd-domain/              Pure domain layer (no DB, no HTTP)
│   ├── jobs/                Job aggregate, state machine, 5 VOs
│   ├── crm/                 Building, ComplianceObligation
│   ├── tenant/              Client, SavedBuilding
│   └── ll152/               LL152 workflow extension
└── pcd-db/                  SQLx repositories + queries

apps/                        ← Application frontends & pipelines
├── web-dashboard/           Company dashboard (React/Vite)
├── mobile-technician/       Field technician app (React Native)
├── pad-ingestion/           PAD building data pipeline (Rust)
├── ll152-ingestion/         DOB LL152 roster import pipeline (Rust)
└── dev-dashboard/           Internal dev tools (Next.js)

infra/docker/                ← Docker Compose for dev environment
docs/                        ← Documentation (PDA-SDD methodology)
```

## Available Commands

### Rust (Backend)

```bash
cargo run -p pcd-api                     # Start API server
cargo test --workspace                   # Run all Rust tests
cargo run -p pad-ingestion -- --bootstrap # Bootstrap PAD data
cargo run -p ll152-ingestion             # Import LL152 roster
```

### JavaScript (Frontend)

```bash
pnpm install                             # Install all JS dependencies
pnpm --filter @pcd/web-dashboard dev     # Start web dashboard
pnpm --filter @pcd/dev-dashboard dev     # Start dev dashboard
```

### Docker

```bash
docker compose -f infra/docker/docker-compose.yml up -d    # Start DB + pgAdmin
docker compose -f infra/docker/docker-compose.yml down      # Stop services
docker compose -f infra/docker/docker-compose.yml down -v   # Stop + delete data
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://pcd:pcd123@localhost:5432/plumbers_compliance` | PostgreSQL connection string |
| `RUST_LOG` | (none) | Set to `pcd_api=debug` for verbose API logging |

## Troubleshooting

### "DATABASE_URL must be set"
- Ensure `.env` file exists in the project root with `DATABASE_URL=...`
- If using Docker, ensure the container is running: `docker ps`

### "Cannot connect to database"
- Start PostgreSQL: `docker compose -f infra/docker/docker-compose.yml up -d`
- Check the connection string in `.env`

### "Port 5432 already in use"
- Another PostgreSQL instance is running. Stop it or change the port mapping in `docker-compose.yml`

### Rust build issues
- Ensure Rust 1.75+: `rustc --version`
- Clean and rebuild: `cargo clean && cargo build`

## Next Steps

- Read [`docs/CONTRIBUTING.md`](CONTRIBUTING.md) for development conventions
- Read [`docs/roadmap/DOMAIN_FIRST_ROADMAP.md`](roadmap/DOMAIN_FIRST_ROADMAP.md) for project roadmap
- Read [`docs/ALPHA_PERSONAS_AND_SCOPE.md`](ALPHA_PERSONAS_AND_SCOPE.md) for product context
