# Entity Relationship Diagram (ERD)

> **Source of Truth:** SQL queries in `crates/pcd-db/src/` (sqlx raw SQL)
> **Scope:** [Pilot Core (LL152)](file:///c:/github/pcd/docs/PILOT_SCOPE_CONTEXT.md) — Future tables shown in dashed outline.

## Entities (Implemented)

### CRM / Assets
- **buildings**: The central entity. Identity derived from BIN. Populated by PAD Bootstrap pipeline.
- **building_addresses**: PAD address entries linked to a BIN. Multiple per building per version.
- **building_events**: JSONB diff-based event log for building field changes.
- **building_pad_versions**: Junction table tracking which PAD versions contain each building (ADR-0014).

### CRM / Compliance
- **compliance_obligations**: Per-building compliance duties (program + cycle). Engine table.
- **obligation_events**: Historical changes to obligation status/roster.
- **ll152_obligation_details**: 1:1 extension table for LL152 program (subcycle A/B/C/D).

### Ingestion
- **import_runs**: Provenance tracking per pipeline execution.
- **import_anomalies**: Data quality issues detected during ingestion.
- **quarantined_rows**: Raw CSV rows that failed ingestion (ERROR severity).

### Jobs / Engine
- **jobs**: Job aggregate — lifecycle, assignment, priority, status.
- **job_events**: Domain events emitted by Job aggregate operations.

## Diagram

```mermaid
erDiagram
    %% ===== CRM / Assets =====
    buildings {
        uuid id PK
        varchar bin UK
        text house_number
        text street_name
        text borough
        text pad_version
        text created_from_source
    }
    building_addresses {
        bigserial id PK
        varchar bin FK
        text pad_version
        smallint borough_code
        text street_name
        text house_number_display
    }
    building_events {
        uuid id PK
        varchar bin FK
        varchar event_type
        jsonb changed_fields
        timestamp created_at
    }
    building_pad_versions {
        bigserial id PK
        varchar bin FK
        text pad_version
        timestamp first_seen_at
    }

    %% ===== CRM / Compliance =====
    compliance_obligations {
        uuid id PK
        uuid building_id FK
        text program_code
        text cycle_key
        text status
        text roster_status
    }
    obligation_events {
        uuid id PK
        uuid obligation_id FK
        text event_type
        uuid import_run_id FK
        timestamp occurred_at
    }
    ll152_obligation_details {
        uuid obligation_id PK
        varchar subcycle
    }

    %% ===== Ingestion =====
    import_runs {
        uuid id PK
        text pipeline_name
        text source_file
        integer rows_parsed
        integer rows_inserted
        timestamp started_at
    }
    import_anomalies {
        uuid id PK
        uuid import_run_id FK
        varchar severity
        varchar reason_code
        varchar building_bin
    }
    quarantined_rows {
        uuid id PK
        uuid import_run_id FK
        varchar reason_code
        jsonb raw_payload
    }

    %% ===== Jobs / Engine =====
    jobs {
        uuid id PK
        text job_number
        uuid company_id
        text job_type
        uuid building_id FK
        uuid compliance_obligation_id FK
        text job_status
        timestamp created_at
    }
    job_events {
        uuid id PK
        uuid job_id FK
        text event_type
        jsonb payload
        uuid actor_user_id
    }

    %% ===== Relationships =====
    buildings ||--|{ building_addresses : "has"
    buildings ||--o{ building_events : "tracks"
    buildings ||--|{ building_pad_versions : "appears_in"
    buildings ||--o{ compliance_obligations : "may_have"
    buildings ||--o{ jobs : "site_of"

    compliance_obligations ||--o{ obligation_events : "tracks"
    compliance_obligations ||--o| ll152_obligation_details : "extends"
    compliance_obligations ||--o{ jobs : "linked_to"

    obligation_events }o--o| import_runs : "caused_by"
    import_runs ||--o{ import_anomalies : "produces"
    import_runs ||--o{ quarantined_rows : "quarantines"

    jobs ||--o{ job_events : "emits"
```

## Relationships Summary

| From | To | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `buildings` | `building_addresses` | 1:N | Each building has multiple PAD addresses |
| `buildings` | `building_events` | 1:N | JSONB diff events for field changes |
| `buildings` | `building_pad_versions` | 1:N | Which PAD versions contain this building |
| `buildings` | `compliance_obligations` | 1:N | Per-program compliance duties |
| `buildings` | `jobs` | 1:N | Jobs target a building |
| `compliance_obligations` | `obligation_events` | 1:N | Status change history |
| `compliance_obligations` | `ll152_obligation_details` | 1:1 | LL152-specific extension |
| `compliance_obligations` | `jobs` | 1:N | Jobs may link to an obligation |
| `import_runs` | `import_anomalies` | 1:N | Anomalies detected per run |
| `import_runs` | `quarantined_rows` | 1:N | Failed rows per run |
| `import_runs` | `obligation_events` | 1:N | Roster changes traced to import |
| `jobs` | `job_events` | 1:N | Domain events per job |
