# ll152-ingestion Architecture

The `ll152-ingestion` app is a Rust-based CLI worker responsible for ingesting DOB LL152 rosters (Excel format) and managing Compliance Obligations in the database.

## System Components

```mermaid
graph TD
    CLI[CLI Args / main.rs] --> Parser[Excel Reader / calamine]
    Parser --> Pipeline[Pipeline / pipeline.rs]
    Pipeline --> Models[Models / models.rs]
    Pipeline -.-> Quarantine[Parse Errors / models.rs]
    
    main[main.rs] --> DB[Database Interface / db.rs]
    DB --> Postgres[(Postgres DB)]
    
    subgraph Data Flow
        Row[Excel Row] --> Transform[Process & Validate]
        Transform --> Payload[Compliance DTO]
        Payload --> Upsert[DB Upsert]
    end
```

## Ingestion Sequence Flow

This diagram illustrates the step-by-step processing of a roster.

```mermaid
sequenceDiagram
    autonumber
    participant U as User (CLI)
    participant M as main.rs
    participant P as pipeline.rs
    participant D as db.rs
    participant DB as Postgres

    U->>M: Start with roster_file & db_url
    M->>D: create_import_run()
    D->>DB: INSERT INTO import_runs

    loop For each Excel Row
        M->>P: process_ll152_row()
        alt Valid BIN & Logic
            P-->>M: ComplianceObligationPayload
        else Invalid
            P-->>M: ParseError
        end
    end

    M->>D: Transaction Start
    loop For each Payload
        M->>D: upsert_compliance_payload()
        D->>D: resolve_building_id_or_stub()
        D->>DB: UPSERT buildings (if stub)
        D->>DB: UPSERT compliance_obligations
        D->>DB: UPSERT ll152_obligation_details
    end
    M->>D: Transaction Commit

    M->>D: flush_parse_errors() (Quarantine)
    D->>DB: INSERT INTO quarantined_rows

    M->>D: reconcile_inactive_obligations()
    D->>DB: UPDATE stale obligations to INACTIVE
    D->>DB: INSERT INTO obligation_events

    M->>D: complete_import_run()
    D->>DB: UPDATE import_runs (counts & end_at)
```

## Module Responsibilities

| Module | Responsibility |
| :--- | :--- |
| **main** | Orchestrates the ETL workflow: CLI parsing, file opening, transaction management, and workflow sequencing. |
| **pipeline** | Domain logic for transformation. Validates BINs, extracts subcycles, and calculates cycle windows per DOB rules. |
| **db** | All SQL interactions. Handles complex logic like "Stub Building" creation and "Pipeline B" reconciliation. |
| **models** | Strong typing for the domain. Includes the `Bin` Value Object with its own validation logic. |
