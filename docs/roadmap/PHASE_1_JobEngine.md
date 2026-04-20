# Phase 1: The Job Engine

> **Status:** ✅ Complete
> **Objective:** Design the generic Job aggregate — the core work container that manages the lifecycle of any field assignment.
> **ADR:** [ADR-0016](../adr/0016-job-engine-pluggable-workflows.md)

---

## Domain Concepts Designed

### 1. Job Aggregate

The central aggregate of the application. A company-scoped, workflow-agnostic work container — *"go do something at this building."*

**Implemented in:** `crates/pcd-domain/src/jobs/job.rs` (387 lines)

| Aspect | Decision |
|--------|----------|
| Identity | UUID (`id`) + company-scoped sequential `JobNumber` (JOB-00001) |
| Required at creation | `company_id`, `job_type`, `building_id`, `created_by_user_id` |
| Accumulated over time | `client_id`, `compliance_obligation_id`, `priority`, `site_notes`, `assigned_to` |
| Relationship to Building | Reference by `building_id` (always fetched from Building aggregate, not copied) |
| Relationship to Obligation | Optional link via `compliance_obligation_id` (can link/unlink) |
| Job type discriminator | `JobType` VO with `LL152_INSPECTION` as first type (extensible enum per ADR-0016) |
| Extension table pattern | Deferred to Phase 2 — `ll152_job_details` table will extend the generic Job |

### 2. Job State Machine

**Implemented in:** `crates/pcd-domain/src/jobs/job_status.rs` (92 lines)

> [!NOTE]
> The PRD (§2.2) proposed 7 states (INTAKE→DISPATCHED→IN_PROGRESS→SUBMITTED→RETURNED→FINALIZED→DELIVERED). After domain research, we simplified the **engine-level** state machine to 4 generic states. The workflow-specific states (SUBMITTED, RETURNED, FINALIZED, DELIVERED) belong to the LL152 Workflow in Phase 2.

```
OPEN ──→ IN_PROGRESS ──→ COMPLETED (terminal)
  │            │
  └──→ CANCELED ←──┘ (terminal)
```

- Terminal states (`COMPLETED`, `CANCELED`) block all update commands via `guard_not_terminal()`
- No backward transitions from terminal states
- 11 domain events emitted by 11 aggregate commands

### 3. Handoff Contract

Deferred to Phase 2 (LL152 Workflow). The handoff is workflow-specific — what constitutes a "complete" LL152 submission is different from what a future job type might require. The engine provides the state transitions; the workflow provides the validation.

---

## Value Objects

| VO | Spec | Rust Code |
|----|------|-----------|
| JobStatus | [JobStatus_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Engine/JobStatus_VO_Spec.md) | `job_status.rs` — 4-value enum (OPEN, IN_PROGRESS, COMPLETED, CANCELED) |
| JobNumber | [JobNumber_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Engine/JobNumber_VO_Spec.md) | `job_number.rs` — company-scoped sequential (JOB-00001) |
| JobType | [JobType_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Engine/JobType_VO_Spec.md) | `job_type.rs` — extensible enum (LL152_INSPECTION first) |
| SourceKind | [SourceKind_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Engine/SourceKind_VO_Spec.md) | `source_kind.rs` — 6 values: OBLIGATION_DRIVEN, CUSTOMER_REQUEST, FOLLOW_UP, ESTIMATE_CONVERSION, OFFICE_INITIATED, EMERGENCY_CALL |
| Priority | [Priority_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Engine/Priority_VO_Spec.md) | `priority.rs` — NORMAL, HIGH, URGENT |

---

## Implementation Artifacts

| Artifact | Technology | Location |
|----------|------------|----------|
| Job Aggregate Root | Rust | `crates/pcd-domain/src/jobs/` (9 files) |
| Database tables | SQLx | `jobs` (22 cols) + `job_events` (6 cols) |
| Repository adapter | Rust/SQLx | `crates/pcd-db/src/jobs/mod.rs` — `impl JobRepository for SqlxJobRepository` |
| API endpoints | Rust/Axum | `crates/pcd-api/src/routes/jobs.rs` (316 lines, 13 endpoints) |

---

## Research Questions — Status

### Aggregate Design — ✅ All answered

- [x] What is the **minimum viable Job**? → `OpenJobParams`: company_id, job_type, building_id, created_by_user_id
- [x] What is the **natural identity** of a Job? → Company-scoped sequential `JobNumber` (JOB-00001)
- [x] What data **belongs to the Job** vs **referenced**? → References by UUID (building_id, client_id, obligation_id)
- [x] Are there **natural ValueObjects**? → Yes: JobNumber, JobStatus, JobType, SourceKind, Priority. ScheduleWindow/AccessInfo/DispatchAssignment deferred to Phase 2 workflow.
- [x] What are the **invariants**? → Must reference a building; terminal states block updates; no backward transitions
- [x] What is the **consistency boundary**? → Single Job aggregate with optimistic concurrency via `updated_at`

### State Machine Validation — ✅ Answered (simplified)

- [x] Walk through real process → Simplified to 4 engine states; workflow-level states deferred to Phase 2
- [x] States PRD doesn't capture? → CANCELED added; DISPATCHED/SUBMITTED/RETURNED/FINALIZED moved to workflow level
- [x] What triggers each transition? → Explicit commands (start, complete, cancel) with domain events
- [x] Implicit transitions? → None at engine level; all transitions require explicit API calls

### Job Creation & Intake — ✅ All answered

- [x] How does a job start? → `Job::open()` factory with `source_kind` (6 values: OBLIGATION_DRIVEN, CUSTOMER_REQUEST, etc.)
- [x] What info at creation? → building_id required; client_id, obligation_id, priority optional
- [x] Can a job exist without a Building? → No, `building_id` is required
- [x] Batch creation? → API supports single-job creation; batch is a UI concern

### Dispatch — 🟡 Partially answered

- [x] Reassignment? → `assign` command allows changing `assigned_to`
- [ ] Full dispatch flow (scheduling, notifications, lead time) → Deferred to Phase 2 workflow
- [ ] Info needed before arriving? → Deferred to Phase 2 (site_notes exists as placeholder)
- [ ] Multiple plumbers? → Deferred; current model: single `assigned_to`

### Handoff — 🔲 Deferred to Phase 2

- [ ] What constitutes "done"? → Workflow-specific (Phase 2)
- [ ] Common return reasons? → Workflow-specific (Phase 2)
- [ ] LMP editing vs return? → Workflow-specific (Phase 2)

### General — ✅ All answered

- [x] Job priority/urgency? → Priority VO: NORMAL, HIGH, URGENT (no LOW)
- [x] How does LMP track? → Job list API with status filtering

---

## Deliverables — ✅ All complete

- [x] `Job_Aggregate.md` — aggregate boundaries, identity, invariants, persistence contract
- [x] Job state machine — implemented with guards and domain events (not just a diagram)
- [x] `JobsModule/Engine/` internal structure — 7 spec files + 9 Rust source files
- [x] Decision: Job-Obligation relationship — optional link via `compliance_obligation_id`, link/unlink commands

---

## Exit Criteria

- [x] Job aggregate boundaries are clear
- [x] State machine is validated (simplified to 4 engine states; workflow states in Phase 2)
- [x] Handoff contract → correctly deferred to Phase 2 (workflow-specific)
- [x] Job type discriminator pattern decided → `JobType` VO with extensible enum

---

## Key ADRs

- [ADR-0016](../adr/0016-job-engine-pluggable-workflows.md) — Job Engine + Pluggable Workflows
- [ADR-0017](../adr/0017-independent-plumber-tenancy.md) — Independent Plumber Tenancy (`company_id` on Job)
- [ADR-0018](../adr/0018-single-aggregate-api-per-domain.md) — Single Aggregate API per Domain
- [ADR-0019](../adr/0019-camelcase-api-serialization.md) — camelCase API Serialization

---

## LL152 Workflow Research (Phase 2 head start)

> These research documents were created during Phase 1 but are Phase 2 deliverables.

| Document | Path |
|----------|------|
| LL152 Inspection Workflow | [LL152_Inspection_Workflow.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/LL152_Inspection_Workflow.md) |
| Open Design Questions | [OPEN_DESIGN_QUESTIONS.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/OPEN_DESIGN_QUESTIONS.md) |
| GPS1 Form Spec | [gps_1_form_spec.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/research/gps_1_form_spec.md) |
| GPS2 Certification & Filing | [gps_2_certification_and_filing_branches.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/research/gps_2_certification_and_filing_branches.md) |
| Branch Topology | [ll_152_branch_topology.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/research/ll_152_branch_topology.md) |
| Findings & Stop Conditions | [ll_152_findings_and_stop_conditions_spec.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/research/ll_152_findings_and_stop_conditions_spec.md) |
| Workflow State Spec | [ll_152_workflow_state_spec.md](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/research/ll_152_workflow_state_spec.md) |
