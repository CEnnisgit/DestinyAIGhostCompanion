# JobStatus Value Object

**Version:** 1.0.1  
**Status:** Official Draft  
**Module:** Job Engine  
**Parent Aggregate:** `Job`

---

## 1. Objective

`JobStatus` represents the **current generic lifecycle state** of a Job.

It answers the single question:

> Is this job open, active, finished, or dead?

It does **not** answer workflow-specific progress questions such as:

- Has the GPS1 form been submitted?
- Is the inspection waiting for LMP review?
- Has the deliverable packet been generated?

Those belong to workflow-specific state models.

---

## 2. What This Value Object Is

`JobStatus` is:

- a **closed enumeration** — exactly 4 values, no more
- a **state machine node** — not a free-choice field
- the **engine-level** lifecycle indicator for any Job regardless of workflow type
- **always present** — every Job has exactly one `JobStatus` at all times

---

## 3. What This Value Object Is Not

`JobStatus` is **not**:

- a workflow progress tracker (that's workflow-specific state)
- a dispatch/scheduling status (that's booking/visit state)
- a deliverable readiness indicator (that's output state)
- a freeform or user-editable field

---

## 4. Enumerated Values

| Value | Meaning |
| --- | --- |
| `OPEN` | The job exists and is active, but no meaningful execution has begun |
| `IN_PROGRESS` | Execution of the job has begun |
| `COMPLETED` | The job has been formally concluded |
| `CANCELED` | The job is no longer intended to proceed |

### Value rules

- This enumeration is **closed** — no additional values may be added without a spec revision.
- The initial state of every new Job is always `OPEN`.
- `COMPLETED` and `CANCELED` are **terminal** — once entered, no further transitions are possible.

---

## 5. State Machine

### Transition diagram

```
         ┌──────────────────────────────────────┐
         │                                      │
         ▼                                      │
      ┌──────┐         ┌─────────────┐    ┌───────────┐
      │ OPEN │────────►│ IN_PROGRESS │───►│ COMPLETED │
      └──────┘         └─────────────┘    └───────────┘
         │                   │
         │                   │
         ▼                   ▼
      ┌──────────┐    ┌──────────┐
      │ CANCELED │    │ CANCELED │
      └──────────┘    └──────────┘
```

### Valid transitions

| From | To | Trigger | Guard |
| --- | --- | --- | --- |
| `OPEN` | `IN_PROGRESS` | `StartJob` command | Current state must be `OPEN` |
| `OPEN` | `CANCELED` | `CancelJob` command | Current state must be `OPEN` |
| `IN_PROGRESS` | `COMPLETED` | `CompleteJob` command | Workflow completion criteria must be satisfied |
| `IN_PROGRESS` | `CANCELED` | `CancelJob` command | Current state must be `IN_PROGRESS` |

> Authorization policy (who may issue these commands) is defined outside this VO by the Job aggregate and role model. `JobStatus` itself does not own auth semantics.

### Invalid transitions (explicitly prohibited)

| From | To | Reason |
| --- | --- | --- |
| `COMPLETED` | any | Terminal state — job is finished |
| `CANCELED` | any | Terminal state — job is dead |
| `IN_PROGRESS` | `OPEN` | Cannot revert to pre-execution state |
| `COMPLETED` | `CANCELED` | Cannot cancel a finished job — create a corrective job instead |

---

## 6. Invariants

1. Every Job must have exactly one `JobStatus` at all times.
2. A newly created Job must start in `OPEN`.
3. `JobStatus` may only change through a valid transition (see §5).
4. If `JobStatus = COMPLETED`, then `completed_at` must be present on the Job.
5. If `JobStatus = CANCELED`, then `canceled_at` must be present on the Job.
6. If `JobStatus = CANCELED`, then `cancellation_reason` should be present on the Job.
7. If `completed_at` is present, `JobStatus` must be `COMPLETED`.
8. If `canceled_at` is present, `JobStatus` must be `CANCELED`.
9. `JobStatus` must not be set freely — only transition commands may change it.

---

## 7. Timestamp Coupling

`JobStatus` has **bidirectional coupling** with Job-level timestamps:

| Status | Required timestamp | Meaning |
| --- | --- | --- |
| `OPEN` | `created_at` (on Job) | When the job was created |
| `IN_PROGRESS` | `started_at` (on Job) | When execution began |
| `COMPLETED` | `completed_at` (on Job) | When the job was formally concluded |
| `CANCELED` | `canceled_at` (on Job) | When the job was canceled |

### Coupling rules

- When transitioning to `IN_PROGRESS`, `started_at` must be set.
- When transitioning to `COMPLETED`, `completed_at` must be set.
- When transitioning to `CANCELED`, `canceled_at` must be set.
- These timestamps are **write-once** — they cannot be changed after being set.

---

## 8. Commands That Change JobStatus

### Initial state

`OpenJob` **creates** a Job with `JobStatus = OPEN`. This is not a transition — it is the initial value assigned at aggregate creation.

### Transition commands

These are the only commands that cause `JobStatus` transitions after creation:

| Command | Transition | Notes |
| --- | --- | --- |
| `StartJob` | `OPEN` → `IN_PROGRESS` | Always an explicit command. Workflow activity may satisfy the precondition for issuing it, but does not implicitly cause the transition. Also sets `started_at`. |
| `CompleteJob` | `IN_PROGRESS` → `COMPLETED` | Guards: workflow completion criteria must be satisfied. Also sets `completed_at`. |
| `CancelJob` | `OPEN` or `IN_PROGRESS` → `CANCELED` | Also sets `canceled_at` and `cancellation_reason`. |

No other commands may change `JobStatus`.

---

## 9. Events Emitted on Transition

| Transition | Event | Notes |
| --- | --- | --- |
| (creation) | `JOB_OPENED` | Emitted when Job is created with initial `OPEN` state |
| `OPEN` → `IN_PROGRESS` | `JOB_STARTED` | |
| `IN_PROGRESS` → `COMPLETED` | `JOB_COMPLETED` | |
| any → `CANCELED` | `JOB_CANCELED` | |

---

## 10. Equality and Identity

`JobStatus` is a value object — it has no identity of its own.

- Two `JobStatus` values are equal if and only if they contain the same enumerated value.
- `JobStatus` should be compared by value, not by reference.
- `JobStatus` is immutable as a value — transitions produce a new value, they don't mutate the old one.

---

## 11. Persistence

`JobStatus` persists as a single column on the `jobs` table:

- **Column:** `job_status`
- **Type:** text or enum (implementation decision)
- **Constraint:** NOT NULL, CHECK against the 4 valid values
- **Default:** `'OPEN'`

---

## 12. Relationship to Workflow State

`JobStatus` is the **engine-level** lifecycle. Workflow modules may have their own richer state models.

### Example: LL152 Inspection Workflow

The LL152 workflow might track states like:

- `CAPTURING` → `SUBMITTED` → `UNDER_REVIEW` → `RETURNED` → `FINALIZED` → `DELIVERED`

These are **not** `JobStatus` values. They exist in the workflow layer.

The mapping between workflow state and engine `JobStatus`:

| Workflow state | Engine JobStatus |
| --- | --- |
| Workflow not yet started | `OPEN` |
| `CAPTURING`, `SUBMITTED`, `UNDER_REVIEW`, `RETURNED` | `IN_PROGRESS` |
| `FINALIZED` or `DELIVERED` (after LMP completes) | `COMPLETED` |
| Canceled at any point | `CANCELED` |

The key rule:

> The workflow does not directly set `JobStatus`. The workflow declares its own criteria met, and an authorized actor (or a domain service) then transitions the engine-level `JobStatus`.

---

## 13. Open Decisions

The 4-state model itself is resolved per Job Aggregate §10 and §17 (Open Decision #4).

1. **Completion authority model**  
   Is `COMPLETED` always set by an explicit human action (authorized actor issues `CompleteJob`), or can a domain service automatically finalize once workflow criteria are satisfied? The current spec leans toward explicit authority, but the boundary between "human completes" and "service completes on criteria" is not yet formally decided. This will likely resolve during LL152 workflow design.

---

## 14. Summary

> `JobStatus` is a closed 4-value enumeration (`OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELED`) that represents the generic lifecycle of a Job. It is a state machine with strict transition rules, timestamp coupling, and terminal states. It is the engine's single answer to "is this work open, active, finished, or dead?"
