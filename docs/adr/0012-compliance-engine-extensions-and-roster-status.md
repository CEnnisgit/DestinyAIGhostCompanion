# ADR 0012: Compliance Engine Extensions and Event-Sourced Roster Status

**Date**: 2026-03-04  
**Status**: Accepted  
**Context**: Finalizing the architecture of the CRM/Compliance module during the implementation of Pipeline B (DOB LL152 Roster Ingestion). 

## Application Context

The `compliance_obligations` table is designed as a generic engine to track per-building compliance duties across multiple NYC programs (LL152, boiler inspections, backflow, etc.). During the implementation of the LL152 pipeline, we encountered two architectural friction points:

1. **Program-Specific State vs. Engine State:** The specifications originally placed program-specific fields (like the LL152 `subcycle`) directly on the generic engine table.
2. **Handling Roster Drop-offs:** An authoritative program roster (like the DOB's LL152 list) defines what obligations exist *right now*. When a building disappears from a newer version of the roster, we must decide how the system reflects this loss of obligation while preserving historical auditability.

## Decision 1: The Engine Extension Pattern

We elected to enforce a strict boundary between the generic engine and program-specific details. 

- **Engine Identity:** The `compliance_obligations` table is strictly limited to fields shared across all programs: identity (`building_id`, `program_code`, `cycle_key`), broad timeline bounds (`window_start`, `window_end`), and generalized status summaries.
- **Extensions:** Program-specific fields (like `LL152Subcycle`) are moved entirely out of the engine table and into 1:1 extension tables (e.g., `ll152_obligation_details`). 

## Decision 2: Event-Sourced Roster Status Tracking

We elected to implement a soft-deactivation pattern driven by post-import reconciliation, rather than row deletion.

- **`roster_status`:** A new column was added to the engine table (`ACTIVE` / `INACTIVE`). Every time a pipeline upserts a row, it forces the status to `ACTIVE`. 
- **Reconciliation Pass:** After a pipeline completes, a reconciliation query finds all obligations for that `program_code` that remain `ACTIVE` but were *not touched* (based on `last_imported_from_version`) by the current run. These stale rows are marked `INACTIVE`.
- **`obligation_events`:** We introduced an event log table. Every transition from `ACTIVE` to `INACTIVE` is recorded here, linked to the `import_run_id` that triggered the deactivation.

## Rationale

1. **Engine Extension Pattern:** 
   - Keeps the generic engine table clean, stable, and focused on core platform capabilities (like a unified dashboard of upcoming deadlines across all programs).
   - Allows new programs to be added in the future without muddying the core schema with sparse, nullable columns only relevant to one specific program.
2. **Event-Sourced Roster Status:**
   - **Data Retention:** Deleting rows destroys historical evidence that a building *used* to have an obligation, which might be critical for understanding past user interactions or resolving disputes about past compliance cycles.
   - **Recoverability:** If a building temporarily drops off a DOB list due to an upstream glitch, the `INACTIVE` status can easily revert to `ACTIVE` on the next run without losing the engine's internal UUID or historical event log.
   - **Auditability:** The `obligation_events` table gives us a precise timeline of exactly *when* and *why* an obligation status changed, linked directly back to the `import_runs` provenance table.

## Consequences

**Positive:**
- Complete historical traceability for compliance obligations.
- A clean, highly extensible architecture for adding future compliance programs (e.g. Boiler, Backflow).
- Clear separation of concerns between generic platform tracking and program-specific business logic.

**Negative:**
- **Join Complexity:** Queries that require both generic state and program-specific state (e.g., "Find all generic deadlines for Subcycle A") now enforce a `JOIN` across `compliance_obligations` and `ll152_obligation_details`.
- **Pipeline Complexity:** Ingestion pipelines are no longer just pure stateless upserts; they must implement and execute the stateful reconciliation pass at the end of every run.
