# PCD System Architecture Overview

> **Last Updated:** March 2026
> **Status:** Living document reflecting the current architecture

---

## System-Level View

```mermaid
graph TB
    subgraph "API Layer (Active ✅)"
        API["⚡ Rust API Server\ncrates/pcd-api\nAxum + Tower"]
    end

    subgraph "Domain Layer (Active ✅)"
        JOBS["🔧 Job Engine\ncrates/pcd-domain/jobs\nAggregate + VOs + Events"]
    end

    subgraph "Persistence Layer (Active ✅)"
        DB_CRATE["💾 pcd-db\ncrates/pcd-db\nSqlxJobRepository"]
    end

    subgraph "Data Producers (Active ✅)"
        PAD["🗂️ PAD Ingestion\napps/pad-ingestion\nRust + sqlx"]
        LL152["📊 LL152 Ingestion\napps/ll152-ingestion\nRust + sqlx"]
    end

    subgraph "Frontend (Prototype)"
        WEB["🖥️ Web Dashboard v2\napps/web-dashboard\nNext.js"]
        DEV["🛠️ Dev Dashboard\napps/dev-dashboard\nNext.js"]
    end

    WEB -.->|"future"| API
    DEV -.->|"direct SQL"| PG
    API --> JOBS
    JOBS -->|"Arc<dyn JobRepository>"| DB_CRATE
    DB_CRATE --> PG
    PAD -->|"raw SQL"| PG
    LL152 -->|"raw SQL"| PG

    PG[("🐘 PostgreSQL\nplumbers_compliance")]

    style API fill:#8b5cf6,color:#fff
    style JOBS fill:#ec4899,color:#fff
    style DB_CRATE fill:#22c55e,color:#fff
    style PAD fill:#22c55e,color:#fff
    style LL152 fill:#22c55e,color:#fff
    style PG fill:#f59e0b,color:#fff
    style WEB fill:#94a3b8,color:#fff,stroke-dasharray: 5 5
    style DEV fill:#94a3b8,color:#fff,stroke-dasharray: 5 5
```

> 🟣 API | 🩷 Domain | 🟢 Adapters/Producers | 🟡 Database | ⬜ Prototype

---

## Data Flow: Write Path vs Read Path

```mermaid
graph LR
    subgraph "WRITE PATH (Rust — Active ✅)"
        CSV["📄 PAD CSV Files"]
        XLS["📊 DOB LL152 Roster"]
        PA["Pipeline A\npad-ingestion"]
        PB["Pipeline B\nll152-ingestion"]
        CSV --> PA
        XLS --> PB
    end

    subgraph "API PATH (Rust — Active ✅)"
        HTTP["HTTP Clients"]
        AXUM["Axum API\n13 job endpoints"]
        DOMAIN["Job Aggregate\npcd-domain"]
        REPO["SqlxJobRepository\npcd-db"]
        HTTP --> AXUM
        AXUM --> DOMAIN
        DOMAIN --> REPO
    end

    PA -->|"INSERT/UPSERT\nbuildings\nbuilding_addresses\nbuilding_events"| PG
    PB -->|"INSERT/UPSERT\ncompliance_obligations\nobligation_events"| PG
    REPO -->|"UPSERT jobs\nINSERT job_events"| PG

    PG[("PostgreSQL")]

    subgraph "READ PATH (Prototype)"
        DASH["Dev Dashboard\nDirect SQL queries"]
    end

    PG --> DASH

    style PA fill:#22c55e,color:#fff
    style PB fill:#22c55e,color:#fff
    style PG fill:#f59e0b,color:#fff
    style AXUM fill:#8b5cf6,color:#fff
    style DOMAIN fill:#ec4899,color:#fff
    style REPO fill:#22c55e,color:#fff
```

---

## Schema Management

Database tables are created and managed via **raw SQL migrations** committed in the repository. There is no external schema tool (Drizzle was previously used but has been removed). The Rust crates write raw SQL against the tables directly.

> ⚠️ **Schema changes require manual coordination.** If you add or rename a column, you must update the raw SQL in every Rust file that references it.

---

## Hexagonal Architecture (Rust Crates)

```mermaid
graph TB
    subgraph "pcd-api (HTTP Boundary)"
        ROUTE["Route Handler\nParse HTTP → call domain → return JSON"]
        STATE["AppState = Arc<dyn JobRepository>"]
        CMD["command_handler()\nGeneric load→mutate→save pattern"]
    end

    subgraph "pcd-domain (Business Logic)"
        AGG["Job Aggregate Root\nFactory, commands, guards"]
        PORT["JobRepository Trait (Port)\nsave, find_by_id, find_by_job_number,\nnext_job_number, list_all"]
        VOS["Value Objects\nJobStatus, JobNumber, JobType,\nSourceKind, Priority"]
        EVENTS["Domain Events\n11 event types"]
    end

    subgraph "pcd-db (Infrastructure)"
        ADAPTER["SqlxJobRepository\nimpl JobRepository for ..."]
        SQL["Raw SQL via sqlx\nTransactional upsert + event insert"]
    end

    ROUTE --> STATE
    STATE --> CMD
    CMD --> AGG
    CMD --> PORT
    PORT -.->|"implements"| ADAPTER
    AGG --> VOS
    AGG --> EVENTS
    ADAPTER --> SQL
    SQL --> PG[("PostgreSQL")]

    style AGG fill:#8b5cf6,color:#fff
    style PORT fill:#f97316,color:#fff
    style ADAPTER fill:#22c55e,color:#fff
    style PG fill:#f59e0b,color:#fff
    style CMD fill:#ec4899,color:#fff
```

| Layer | Can Import | Cannot Import |
| :--- | :--- | :--- |
| **Domain** (pcd-domain) | Nothing (pure) | pcd-db, pcd-api |
| **Application** (pcd-api) | pcd-domain | pcd-db (only via trait) |
| **Infrastructure** (pcd-db) | pcd-domain (for trait + types) | pcd-api |

---

## Pipeline Architecture (Rust — Flat)

```mermaid
graph LR
    subgraph "Pipeline A: PAD Bootstrap"
        A1["main.rs\nCLI args + orchestration"]
        A2["pipeline.rs\nParse → Validate → Tiebreak"]
        A3["db.rs\nflush_buildings()\nflush_addresses()\n+ building_events"]
    end

    subgraph "Pipeline B: LL152 Import"
        B1["main.rs\nCLI args + orchestration"]
        B2["pipeline.rs\nParse → Validate rows"]
        B3["db.rs\nupsert_compliance_payload()\nreconcile_inactive()\n+ obligation_events"]
    end

    A1 --> A2 --> A3 --> PG
    B1 --> B2 --> B3 --> PG

    PG[("PostgreSQL")]
    style PG fill:#f59e0b,color:#fff
```

> Rust pipelines are **flat**: `main → pipeline → db`. No hexagonal layers needed — they're batch CLI tools, not long-running services.

---

## Technology Summary

| Component | Technology | Role |
| :--- | :--- | :--- |
| `pcd-domain` | Rust | Domain layer — aggregates, VOs, events, repository traits |
| `pcd-db` | Rust + sqlx | Infrastructure — repository adapters |
| `pcd-api` | Rust + Axum | HTTP API server |
| `pad-ingestion` | Rust + sqlx | Pipeline A — building bootstrap |
| `ll152-ingestion` | Rust + sqlx | Pipeline B — compliance obligations |
| `web-dashboard` | TypeScript + Next.js | Prototype UI |
| `dev-dashboard` | TypeScript + Next.js | Developer tools UI |
| PostgreSQL | — | Single database for all data |
