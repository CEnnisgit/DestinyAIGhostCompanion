# Priority Value Object

**Version:** 1.0.1  
**Status:** Official Draft  
**Module:** Job Engine  
**Parent Aggregate:** `Job`

---

## 1. Objective

`Priority` represents the **generic urgency or importance** of a Job.

It answers the question:

> How urgent is this work relative to other jobs?

It does **not** answer:

- when the job is scheduled (that is booking/dispatch)
- what SLA or deadline applies (that is workflow or contract policy)
- what order work should be performed in (that is dispatch optimization)

---

## 2. What This Value Object Is

`Priority` is:

- a **closed enumeration** — exactly 3 values
- **optional** — not every job requires an explicit priority classification
- **mutable** — priority can change during a job's lifecycle (e.g., a routine job becomes urgent after a new complaint)
- a **human-facing signal** — helps office staff and dispatchers make judgment calls

---

## 3. What This Value Object Is Not

`Priority` is **not**:

- an SLA timer or deadline engine (that would be policy/contract logic)
- a dispatch ordering algorithm (dispatch owns sequencing)
- a workflow-specific severity scale (e.g., DOB violation severity belongs to LL152)
- a billing modifier (rush charges belong to invoicing)

---

## 4. Enumerated Values

| Value | Meaning |
| --- | --- |
| `NORMAL` | Standard priority, no special urgency |
| `HIGH` | Work should be prioritized above normal jobs |
| `URGENT` | Work requires immediate attention |

### Value rules

- This enumeration is **closed** — no additional values may be added without a spec revision.
- If not explicitly set, `Priority` is `null` (absent), not defaulted.
- Values are stored as uppercase strings.
- The ordering `NORMAL < HIGH < URGENT` is semantically meaningful and may be used for sorting and filtering.

---

## 5. Mutability

Unlike `SourceKind` (immutable) and `JobNumber` (immutable), `Priority` is **mutable**.

A job's priority can change because:

- new information arrives (tenant reports smell → turns out it's a gas leak)
- customer escalates
- office staff reassess urgency based on updated context

### Mutation rules

1. `Priority` may be changed at any time while `JobStatus` is `OPEN` or `IN_PROGRESS`.
2. `Priority` must not be changed after `JobStatus` is `COMPLETED` or `CANCELED` (terminal states are frozen).
3. `Priority` changes are not state-machine transitions — any value can move to any other value.

---

## 6. Invariants

1. If present, `Priority` must contain a recognized value from the enumeration.
2. `Priority` is optional — a Job may exist without it.
3. `Priority` may only be changed while the Job is in a non-terminal state (`OPEN` or `IN_PROGRESS`).
4. `Priority` carries no implicit behavioral side-effects in the engine — it is a classification signal, not a trigger.

---

## 7. Behavioral Implications

`Priority` currently has **no engine-level behavioral side-effects**. It does not:

- automatically change `JobStatus`
- trigger notifications
- affect workflow completeness rules
- modify scheduling

It exists as a **signal to human actors** — office staff and dispatchers use it to make decisions.

### Future behavior potential

`Priority` may serve as an input to application-layer policy in future revisions:

| Potential future behavior | Example |
| --- | --- |
| Sort order | `URGENT` jobs appear first in dispatch queue |
| Visual indicators | `URGENT` shows a red badge in the UI |
| Notification triggers | `URGENT` sends an alert to the assigned user |
| SLA association | `HIGH` and `URGENT` may carry response-time expectations |

These are **not** part of v1. If behavior is added, it should be modeled as policy that *uses `Priority` as an input*, not as logic embedded in the VO.

---

## 8. Equality and Identity

`Priority` is a value object — it has no identity of its own.

- Two `Priority` values are equal if and only if they contain the same enumerated value.
- Values are stored and compared as uppercase strings.
- `Priority` is comparable — `NORMAL < HIGH < URGENT` is a defined ordering.

---

## 9. Commands and Events

### Commands

| Command | Relationship |
| --- | --- |
| `OpenJob` | `Priority` may be set as part of Job creation (optional) |
| `UpdateJobPriority` | Changes `Priority` on an existing Job |

> Note: `UpdateJobPriority` is a new command not yet listed in the Job Aggregate §12. It should be added in the next aggregate revision.

### Events

| Event | When |
| --- | --- |
| `JOB_OPENED` | `Priority` included in payload if set at creation |
| `JOB_PRIORITY_UPDATED` | Emitted when `Priority` is changed on an existing Job |

> Note: `JOB_PRIORITY_UPDATED` is a new event not yet listed in the Job Aggregate §13. It should be added in the next aggregate revision.

---

## 10. Persistence

`Priority` persists as a single column on the `jobs` table:

- **Column:** `priority`
- **Type:** `VARCHAR(10)` or `TEXT` with CHECK
- **Constraint:** nullable, CHECK against the 3 valid values

---

## 11. Open Decisions

1. **Should Priority be required?**  
   The current spec makes it optional. But in emergency and repair scenarios, having no priority is operationally risky — dispatchers need to know urgency. Pilot usage should determine whether `Priority` should become required, and if so, whether the default should be `NORMAL`. (Relates to Job Aggregate Open Decision #6.)

---

## 12. Summary

> `Priority` is an optional, mutable, closed 3-value enumeration (`NORMAL`, `HIGH`, `URGENT`) representing the generic urgency of a Job. It is a human-facing classification signal with no engine-level behavioral side-effects in v1. It can change during a job's lifecycle but freezes at terminal states.
