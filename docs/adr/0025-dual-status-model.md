# ADR-0025: Dual-Status Model — Generic Job Status + Workflow Status

**Status:** Accepted  
**Date:** 2026-03-27  
**Deciders:** Marcus, AI Pair Programming  

## Context

The Job Engine (ADR-0016) is intentionally workflow-agnostic. The `jobs` table tracks a generic lifecycle (`OPEN → IN_PROGRESS → COMPLETED | CANCELED`) shared across all job types.

However, workflow-typed jobs like LL152 inspections have a richer, domain-specific lifecycle:

```
DRAFT → CAPTURING → READY_FOR_REVIEW → UNDER_REVIEW → ... → FINALIZED
```

These workflow states carry meaning that the generic lifecycle cannot express. A job `IN_PROGRESS` might be in field capture, or it might be submitted and awaiting LMP review — two very different states from a user's perspective.

We need a pattern for how the generic lifecycle and workflow-specific lifecycle coexist.

## Options Considered

### Option A: Workflow states replace generic states

LL152 jobs would use only the LL152 state machine. The generic `OPEN/IN_PROGRESS/COMPLETED/CANCELED` states would not apply.

**Rejected.** This breaks the Job Engine's polymorphism. The job list, search, and filtering all depend on a universal status column. If each job type has a different set of valid statuses, every query that touches `job_status` needs type-specific logic.

### Option B: Workflow states are nested inside IN_PROGRESS

The LL152 states would be sub-states of `IN_PROGRESS`. Crossing a generic boundary (e.g., `OPEN → IN_PROGRESS`) would be a separate action from crossing a workflow boundary.

**Rejected.** Confusing. "In Progress" would mean completely different things at different times, and the two state machines would need tight coupling to stay synchronized.

### Option C: Parallel tracks — generic status + workflow status

The `jobs` table keeps the coarse generic status. The workflow extension table (`ll152_job_details`) has its own `workflow_status` column. They are coordinated but independently persisted.

**Accepted.** See below.

## Decision

Adopt the **parallel tracks** model:

```
jobs table (generic)               ll152_job_details (extension, 1:1)
┌────────────────────────┐         ┌──────────────────────────────┐
│ job_id                 │────────▶│ job_id (FK)                  │
│ job_type = LL152       │         │ branch_discriminator         │
│ job_status = IN_PROGRESS│        │ workflow_status = CAPTURING  │
│ address, client, ...   │         │ inspection_date, ...         │
└────────────────────────┘         └──────────────────────────────┘
```

### What each status answers

| Status Layer | Question | Example Values |
|---|---|---|
| **Generic (`job_status`)** | Is this work active or done? | `OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELED` |
| **Workflow (`workflow_status`)** | Where in the process are we? | `DRAFT`, `CAPTURING`, `READY_FOR_REVIEW`, ... |

### Coordination rules

The two statuses are coordinated. Neither can move independently without the other making sense:

| User Action | Generic Status | LL152 Workflow Status |
|---|---|---|
| Create LL152 job | `OPEN` | `DRAFT` |
| QI starts field capture | `IN_PROGRESS` | `CAPTURING` |
| QI submits for review | `IN_PROGRESS` | `READY_FOR_REVIEW` |
| QI recalls submission | `IN_PROGRESS` | `CAPTURING` |
| LMP finalizes (post-alpha) | `COMPLETED` | `FINALIZED` |
| Anyone cancels | `CANCELED` | — (no workflow status change needed) |

### Transition ownership

- **Generic transitions** are triggered by **engine-level commands** (`StartJob`, `CompleteJob`, `CancelJob`).
- **Workflow transitions** are triggered by **workflow-specific commands** (`StartCapture`, `SubmitForReview`, `RecallSubmission`).
- When a workflow command _implies_ a generic transition, the workflow module issues both. Example: `StartCapture` on a `DRAFT`/`OPEN` job triggers both `DRAFT → CAPTURING` and `OPEN → IN_PROGRESS`.

### Non-LL152 job types

For simple job types (Emergency Repair, General Repair), there may be no extension table and no workflow status. The generic lifecycle is sufficient. This pattern only activates when `job_type` refers to a workflow that owns its own state machine.

## Consequences

- The `jobs` table remains universally queryable. Filtering by "all active jobs" is always `WHERE job_status IN ('OPEN', 'IN_PROGRESS')`, regardless of job type.
- Job lists can show a unified status badge that renders differently per type: generic status for simple jobs, workflow status for LL152 jobs.
- The extension table pattern (`ll152_job_details`) becomes the standard seam for workflow-specific persistence.
- Each workflow module owns its own state machine validation — the engine does not need to understand LL152 states.
- Adding a new workflow type (e.g., backflow testing) means: add a new `job_type` enum value, create a new extension table, define its workflow states. The engine is untouched.

## References

- [ADR-0016: Job Engine with Pluggable Workflows](./0016-job-engine-pluggable-workflows.md)
- [Job Aggregate Spec §10 (Lifecycle)](../docs/2-during-implementation/DDD/ModuleDesign/Jobs/Engine/Job_Aggregate.md)
- [Job Aggregate Spec §14 (Engine/Workflow Seam)](../docs/2-during-implementation/DDD/ModuleDesign/Jobs/Engine/Job_Aggregate.md)
- [LL152 Inspection Workflow](../docs/2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/LL152_Inspection_Workflow.md)
