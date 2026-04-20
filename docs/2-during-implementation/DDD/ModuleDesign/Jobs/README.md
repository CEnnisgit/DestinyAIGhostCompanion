# JobsModule (The Work)

> **Source of Truth:** `crates/pcd-domain/src/jobs/` (domain) + `crates/pcd-db/src/jobs/` (persistence)
> **Scope:** Pilot Core (LL152)
> **ADR:** [ADR-0016: Job Engine with Pluggable Workflow Types](../../../../adr/0016-job-engine-pluggable-workflows.md)

## Traceability

> **Refer to:** [TraceabilityMatrix_SFR.md](./TRACEABILITY_SFR.md)

This module handles the core "Game Loop" of the application — creating, dispatching, capturing, reviewing, and finalizing field work.

## Architecture

Per ADR-0016, the module follows the **Engine + Workflow** pattern (parallel to CRM/Compliance's Engine + Programs pattern):

- **Engine** — the generic Job aggregate, state machine, dispatch logic
- **Workflows** — type-specific behavior (form schema, validation, review rules, output)

```
crates/pcd-domain/src/jobs/
├── job.rs          → Job aggregate (open, start, complete, cancel, etc.)
├── job_status.rs   → State machine (OPEN → IN_PROGRESS → COMPLETED / CANCELED)
├── job_number.rs   → Job number value object (validation, normalization)
├── job_type.rs     → Job type discriminator (LL152_INSPECTION)
├── priority.rs     → Priority value object (NORMAL / HIGH / URGENT)
├── source_kind.rs  → Source kind (6 variants)
├── events.rs       → Domain events (11 event types)
├── repository.rs   → Repository trait (save, find, nextJobNumber)
└── mod.rs          → Module exports
```

## Sub-Modules

### 1. [Engine](./Engine/README.md)
**Responsibility:** The generic Job lifecycle.
* Job aggregate (identity, assignment, scheduling)
* State machine (OPEN → IN_PROGRESS → COMPLETED / CANCELED)
* Domain commands (14 operations)
* Domain events (11 event types)

### 2. [Workflows/LL152](./Workflows/LL152/README.md) *(future)*
**Responsibility:** LL152 Inspection-specific behavior.
* GPS1 form schema and field capture
* Inspection findings data model
* Validation rules and completeness checks
* Photo evidence requirements
* GPS1/GPS2 packet output
* Deadline computation (30/60/120/180-day)

## Module Interactions

- **Consumes**: `AuthModule` (future), `CRMModule` (Buildings, ComplianceObligations).
- **Produces**: Finalized Job data for `ReportingModule` (future).

## Current Implementation

| Component | Location | Status |
|-----------|----------|--------|
| Job aggregate + 14 commands | `crates/pcd-domain/src/jobs/job.rs` | ✅ |
| 5 value objects | `crates/pcd-domain/src/jobs/*.rs` | ✅ |
| Repository trait | `crates/pcd-domain/src/jobs/repository.rs` | ✅ |
| sqlx repository impl | `crates/pcd-db/src/jobs/mod.rs` | ✅ |
| API routes (CRUD + state transitions) | `crates/pcd-api/src/routes/jobs.rs` | ✅ (partial — 7 PATCH routes deferred) |
| LL152 Workflow | — | ⏳ Future (Phase 1 Inspection) |
