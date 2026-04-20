# SourceKind Value Object

**Version:** 1.0.1  
**Status:** Official Draft  
**Module:** Job Engine  
**Parent Aggregate:** `Job`

---

## 1. Objective

`SourceKind` captures **why a Job exists** — the origin or reason it was created.

It answers the question:

> What caused this job to be opened?

It does **not** describe:

- who created the job (that is `created_by_user_id`)
- what kind of work it is (that is `JobType`)
- how urgent it is (that is `Priority`)

---

## 2. What This Value Object Is

`SourceKind` is:

- a **semi-open enumeration** — a defined set of values that may grow as new intake patterns emerge
- **optional** — not every job's origin needs to be classified, though it usually will be
- **immutable after creation** — the reason a job was created does not change
- **set once at creation** — populated during `OpenJob`, never updated afterward

---

## 3. What This Value Object Is Not

`SourceKind` is **not**:

- a workflow type (that is `JobType`)
- a priority indicator (that is `Priority`)
- an actor identity (that is `created_by_user_id`)
- a referral tracking system (that would be a CRM/marketing concern)
- a billing category (that belongs to invoicing)

---

## 4. Enumerated Values

### Current candidates

| Value | Meaning | Example scenario |
| --- | --- | --- |
| `OBLIGATION_DRIVEN` | Job exists because a compliance obligation requires it | LL152 4-year cycle creates inspection job |
| `CUSTOMER_REQUEST` | Job exists because a customer directly requested work | Client calls to report a leak |
| `FOLLOW_UP` | Job exists as follow-up to a previous job | Failed inspection triggers re-inspection |
| `ESTIMATE_CONVERSION` | Job exists because a prior estimate was accepted | Customer approves repair quote |
| `OFFICE_INITIATED` | Job was opened by office staff without a specific external trigger | Admin opens a job for internal scheduling or tracking |
| `EMERGENCY_CALL` | Job exists in response to an emergency | After-hours gas leak call |

### Enumeration rules

- This enumeration is **semi-open** — new values may be added as intake patterns are discovered, but existing values must not be renamed or removed without a spec revision.
- Values are stored as uppercase strings.
- The value set is the same across all `JobType` values — `SourceKind` is universal, not workflow-specific.

---

## 5. Relationship to Other Fields

`SourceKind` classifies the **origin** of a Job. Other fields classify different dimensions:

| Field | Dimension | Example |
| --- | --- | --- |
| `SourceKind` | Why the job was created | `OBLIGATION_DRIVEN` |
| `JobType` | What kind of work it is | `LL152_INSPECTION` |
| `Priority` | How urgent it is | `HIGH` |
| `created_by_user_id` | Who created it | User ID of the office admin |

These are orthogonal — a job can be `EMERGENCY_CALL` + `REPAIR` + `URGENT` + created by `user-42`. Each field answers a different question.

---

## 6. Invariants

1. If present, `SourceKind` must contain a recognized value from the enumeration.
2. `SourceKind` is immutable — once set, it cannot be changed.
3. `SourceKind` is optional — a Job may exist without it.
4. `SourceKind` is set at creation time only (part of `OpenJob`). It cannot be attached later.
5. If `SourceKind` is not provided at creation, the absence is **permanent** — it cannot be backfilled. A `null` value means "origin not captured at intake."

---

## 7. Behavioral Implications

`SourceKind` currently has **no behavioral side-effects** in the engine. It is primarily a classification and reporting field.

However, it may serve as an **input to application-layer policy** in future revisions:

| Potential future behavior | Example |
| --- | --- |
| Default priority inference | `EMERGENCY_CALL` → suggest `Priority = URGENT` |
| Reporting and analytics | Filter dashboard by obligation-driven vs customer-request jobs |
| Workflow routing hints | `FOLLOW_UP` could auto-link to parent job |

These are **not** part of v1. If behavior is added, it should be modeled as application-layer policy that *uses `SourceKind` as an input*, not as logic derived directly from the VO alone. `SourceKind` must not become a hidden workflow switch.

---

## 8. Equality and Identity

`SourceKind` is a value object — it has no identity of its own.

- Two `SourceKind` values are equal if and only if they contain the same enumerated value.
- Values are stored and compared as uppercase strings.
- `SourceKind` is immutable — it cannot be modified after construction.

---

## 9. Commands and Events

### Commands

`SourceKind` is set as part of `OpenJob`. There is no dedicated command for `SourceKind`.

It has **no update command** — the reason a job exists does not change.

### Events

`SourceKind` is included in the `JOB_OPENED` event payload as metadata about the new Job's origin.

No separate event exists for `SourceKind` because it is always set as part of creation.

---

## 10. Persistence

`SourceKind` persists as a single column on the `jobs` table:

- **Column:** `source_kind`
- **Type:** `VARCHAR(40)` or `TEXT` with CHECK
- **Constraint:** nullable, CHECK against recognized values
- **Immutability:** application-enforced (no UPDATE on this column after INSERT)

---

## 11. Open Decisions

1. **Universality in practice**  
   Is `SourceKind` truly populated for every job in real intake workflows, or are there common scenarios where it is meaningfully unknown? If pilot usage shows it is almost always populated, it may be promoted to required in a future revision. (Relates to Job Aggregate Open Decision #5.)

---

## 12. Summary

> `SourceKind` is an optional, immutable, semi-open enumeration that classifies why a Job was created. It is set once at creation and never changed. It currently serves classification and reporting purposes only, with no engine-level behavioral side-effects. The value set is universal across all job types.
