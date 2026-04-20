# Event History — Architecture

The event history system is a **cross-cutting concern** — not a standalone module. It provides an append-only audit trail of changes made to domain entities during data ingestion. Two separate producers write to two separate event tables, each with distinct schemas optimized for their domain.

## System-Level Flow

```mermaid
graph TB
    subgraph "Pipeline A: PAD Bootstrap"
        PAD_DB["flush_buildings()\npad-ingestion/db.rs"]
        PAD_DIFF["Diff Engine\nCompare old → new fields"]
    end

    subgraph "Pipeline B: LL152 Import"
        LL_DB["reconcile_inactive()\nll152-ingestion/db.rs"]
        LL_DETECT["Stale Detection\nACTIVE but not in latest roster"]
    end

    subgraph "Job Engine (Phase 1)"
        JOB_SAVE["SqlxJobRepository.save()\npcd-db/jobs/mod.rs"]
        JOB_EVENTS["Domain Events\n11 event types from commands"]
    end

    subgraph "Event Tables"
        BE[("building_events\nJSONB changed_fields")]
        OE[("obligation_events\nold_value → new_value")]
        JE[("job_events\nJSONB payload")]
    end

    PAD_DB --> PAD_DIFF
    PAD_DIFF -->|"CREATED / field changes"| BE

    LL_DB --> LL_DETECT
    LL_DETECT -->|"ROSTER_STATUS_CHANGED"| OE

    JOB_SAVE --> JOB_EVENTS
    JOB_EVENTS -->|"JOB_OPENED, JOB_STARTED, etc."| JE

    style BE fill:#3b82f6,color:#fff
    style OE fill:#3b82f6,color:#fff
    style JE fill:#3b82f6,color:#fff
    style PAD_DIFF fill:#22c55e,color:#fff
    style LL_DETECT fill:#22c55e,color:#fff
    style JOB_EVENTS fill:#8b5cf6,color:#fff
```

## Three Event Systems Compared

| Aspect | Building Events | Obligation Events | Job Events |
| :--- | :--- | :--- | :--- |
| **Table** | `building_events` | `obligation_events` | `job_events` |
| **Producer** | PAD ingestion (`flush_buildings`) | LL152 ingestion (`reconcile_inactive`) | Job aggregate commands |
| **Trigger** | Data import diff | Roster reconciliation | User actions via API |
| **Schema** | JSONB `changed_fields` (structured diff) | Flat `old_value → new_value` | JSONB `payload` (event-specific) |
| **Event types** | `PAD_UPDATE_{version}` | `ROSTER_STATUS_CHANGED` | 11 types (JOB_OPENED, etc.) |
| **FK** | `bin` (varchar) | `obligation_id` (uuid) | `job_id` (uuid) |
| **Actor** | System (import pipeline) | System (import pipeline) | User (`actor_user_id`) |
| **Traceability** | Via `event_type` (PAD version) | Via `import_run_id` | Via `actor_user_id` |

## Design Principles

1. **Append-only** — Events are inserted, never updated or deleted
2. **Domain separation** — Each aggregate has its own event table with a schema optimized for its use case
3. **Co-transactional** — Events are written in the same transaction as their parent entity mutation
4. **Immutable records** — Once written, event data is permanent audit evidence

## Known Gaps

| Gap | Affected Table | Status |
| :--- | :--- | :--- |
| Field-level change tracking during obligation upsert | `obligation_events` | Not yet implemented |
| INACTIVE → ACTIVE reactivation events | `obligation_events` | Not yet implemented |
| Obligation creation events | `obligation_events` | Not yet implemented |

> [!TIP]
> The obligation event gaps can be resolved by adapting PAD's `flush_buildings()` diff pattern: fetch existing records before upserting, compare fields, and insert events for changes.
