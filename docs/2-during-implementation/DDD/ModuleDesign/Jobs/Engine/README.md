# Engine Sub-Module (Jobs)

> **Parent:** [JobsModule](../README.md)

## Responsibilities
**Job Lifecycle**: Manages the generic lifecycle of any field work assignment.
- **Job Aggregate**: Identity, assignment, scheduling, building/obligation references.
- **State Machine**: Enforces valid transitions (e.g., `INTAKE` → `DISPATCHED` → `IN_PROGRESS` → `SUBMITTED`).
- **Dispatch**: Links a `Technician` to a `Job`, manages scheduling.
- **Type Discriminator**: Routes to the correct Workflow (e.g., `LL152_INSPECTION`).

## Key Algorithms
- **Single Assignment**: `SFR-BRC-01` ensuring a job has only one active technician at a time.
- **No Backward Transitions**: `SFR-BRC-10` prevents moving from `SUBMITTED` back to `DISPATCHED` without a formal "Return" action.

## Data Structures
- `jobs` table (primary owner — to be designed in Phase 1).

## Status
🔲 **Pending Phase 1 spec work** — see [Domain-First Roadmap](../../../../roadmap/DOMAIN_FIRST_ROADMAP.md).
