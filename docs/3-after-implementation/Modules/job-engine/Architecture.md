# Job Engine Architecture

The Job Engine spans three Rust crates following hexagonal architecture. The domain layer owns the business rules, the database adapter implements persistence, and the API layer exposes HTTP endpoints — all connected through a trait-based port.

## Hexagonal Layer Diagram

```mermaid
graph TB
    subgraph "API Layer (pcd-api)"
        ROUTER["Router\n13 endpoints"]
        HANDLERS["Handlers\nState(repo): State<AppState>"]
        CMD["command_handler()\nGeneric load→mutate→save"]
        REQ["Request Types\nCreateJobRequest, TextBody, etc."]
        RES["Response Types\nJobResponse (From<&Job>)"]
    end

    subgraph "Domain Layer (pcd-domain)"
        AGG["Job Aggregate Root\njob.rs (387 lines)"]
        VOS["Value Objects\nJobStatus, JobNumber, JobType\nSourceKind, Priority"]
        EVENTS["Domain Events\n11 types, JSONB payloads"]
        TRAIT["JobRepository Trait\n(Port — 5 async methods)"]
    end

    subgraph "Infrastructure Layer (pcd-db)"
        ADAPTER["SqlxJobRepository\nimpl JobRepository for ..."]
        SQL["Raw SQL\nUPSERT jobs + INSERT events"]
    end

    subgraph "Database"
        PG[("PostgreSQL\njobs (22 cols)\njob_events (6 cols)")]
    end

    ROUTER --> HANDLERS
    HANDLERS --> CMD
    CMD --> AGG
    CMD -->|"Arc<dyn JobRepository>"| TRAIT
    TRAIT -.->|"implements"| ADAPTER
    AGG --> VOS
    AGG --> EVENTS
    ADAPTER --> SQL
    SQL --> PG

    style AGG fill:#8b5cf6,color:#fff
    style TRAIT fill:#f97316,color:#fff
    style ADAPTER fill:#22c55e,color:#fff
    style PG fill:#f59e0b,color:#fff
    style CMD fill:#ec4899,color:#fff
```

> 🟣 Domain | 🟠 Port | 🟢 Adapter | 🟡 Database | 🩷 Pattern

## State Machine

```mermaid
stateDiagram-v2
    [*] --> OPEN : Job.open()
    OPEN --> IN_PROGRESS : job.start()
    OPEN --> CANCELED : job.cancel()
    IN_PROGRESS --> COMPLETED : job.complete()
    IN_PROGRESS --> CANCELED : job.cancel()
    COMPLETED --> [*]
    CANCELED --> [*]

    note right of COMPLETED : Terminal — blocks all updates
    note right of CANCELED : Terminal — blocks all updates
```

- 4 states, 2 terminal (`COMPLETED`, `CANCELED`)
- Terminal states block all update commands via `guard_not_terminal()`
- No backward transitions from terminal states

## Command Flow (Sequence)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client (HTTP)
    participant H as Handler
    participant R as JobRepository (dyn)
    participant A as Job Aggregate
    participant DB as PostgreSQL

    C->>H: PATCH /api/jobs/{id}/start
    H->>R: find_by_id(id)
    R->>DB: SELECT * FROM jobs WHERE id = $1
    DB-->>R: JobRow
    R-->>H: Job (reconstituted)
    H->>A: job.start(actor_id)
    A->>A: validate transition (OPEN → IN_PROGRESS)
    A->>A: emit JobStarted event
    A-->>H: Ok(())
    H->>R: save(&mut job)
    R->>DB: BEGIN TX
    R->>DB: UPSERT jobs SET status = 'IN_PROGRESS'
    R->>DB: INSERT INTO job_events (JobStarted)
    R->>DB: COMMIT
    R-->>H: Ok(())
    H->>A: clear_uncommitted_events()
    H-->>C: 200 OK + JobResponse JSON
```

## Module Responsibilities

| Module | Crate | Responsibility |
| :--- | :--- | :--- |
| **job.rs** | pcd-domain | Aggregate root: factory, 8 commands, terminal guard, event emission, reconstitution |
| **job_status.rs** | pcd-domain | State machine: 4 states, valid transitions, `is_terminal()`, `transition_to()` |
| **job_number.rs** | pcd-domain | VO: non-empty, max 20 chars, uppercase normalization |
| **job_type.rs** | pcd-domain | VO: extensible enum with `LL152_INSPECTION` as first type |
| **source_kind.rs** | pcd-domain | VO: 6 intake source categories |
| **priority.rs** | pcd-domain | VO: 3-value enum (NORMAL, HIGH, URGENT) with ordinal ranking |
| **events.rs** | pcd-domain | 11 domain event types + typed `JobOpenedPayload` struct |
| **repository.rs** | pcd-domain | Port: `JobRepository` trait (5 async methods) |
| **tests.rs** | pcd-domain | 47 unit tests across 7 modules |
| **mod.rs** | pcd-db | Adapter: `SqlxJobRepository` implementing `JobRepository` |
| **routes/jobs.rs** | pcd-api | 13 HTTP handlers + `command_handler` generic pattern |
