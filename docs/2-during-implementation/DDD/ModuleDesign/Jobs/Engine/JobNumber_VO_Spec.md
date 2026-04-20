# JobNumber Value Object

**Version:** 1.0.1  
**Status:** Official Draft  
**Module:** Job Engine  
**Parent Aggregate:** `Job`

---

## 1. Objective

`JobNumber` is the **human-facing reference** for a Job.

It answers the question:

> What is the number this job is known by to office staff, field staff, and clients?

It is not the internal aggregate identity (`job_id`). It is the value that appears on:

- printed work orders
- phone calls between office and field
- client-facing communications
- scheduling boards and dispatch screens
- invoices and reports

---

## 2. What This Value Object Is

`JobNumber` is:

- a **human-readable, externally-communicated identifier**
- **unique per company** — no two jobs in the same company share a `JobNumber`
- **immutable once assigned** — cannot be changed after creation
- **always present** — every Job must have exactly one `JobNumber`
- **not the system primary key** — `job_id` is the internal identity

---

## 3. What This Value Object Is Not

`JobNumber` is **not**:

- a UUID or system-generated internal ID (that is `job_id`)
- a workflow reference (LL152 has its own filing numbers)
- a client-facing invoice number (that belongs to billing)
- a building identifier (that is `building_id` / BIN / BBL)
- a globally unique value — uniqueness is scoped to `company_id`

---

## 4. Format

### VO validation rules

The `JobNumber` VO enforces only fundamental string validity:

1. Must be **non-empty** and **non-blank** (no whitespace-only values).
2. Maximum length: **20 characters**.
3. **Normalized to uppercase** at construction.

The VO does not enforce a specific structural pattern. It validates that the value is a usable, storable human reference.

### Application convention

The default application convention is `{PREFIX}-{SEQUENCE}`:

- `PREFIX` — a short, fixed string identifying the company or job domain (default: `J`)
- `SEQUENCE` — a zero-padded numeric value, monotonically increasing per company

Examples:

- `J-00001`
- `J-00142`
- `J-01538`

This convention is **not a VO invariant**. Companies may configure their own prefix (e.g., `PLM-`, `NYC-`), and independent plumbers may use a plain sequence (`142`). Pattern enforcement is an **application-level configuration concern**.

### Human-speakable requirement

The format should produce values a person can say over the phone. This is a design goal guiding the generation strategy, not a machine-enforced rule.

---

## 5. Assignment

### When is JobNumber assigned?

`JobNumber` is assigned **at Job creation time**. It is part of the `OpenJob` command output.

There is no concept of a Job existing without a `JobNumber` — it is required from the first moment the Job is persisted.

### How is it generated?

`JobNumber` generation is an **infrastructure concern**, not a VO concern. The VO receives and validates the value; it does not generate it.

Likely generation strategies:

| Strategy | Example | Notes |
| --- | --- | --- |
| Auto-increment per company | `J-00142` | Simplest. Sequence counter per `company_id`. |
| Date-prefixed | `2026-0053` | Resets sequence yearly. Human-readable year context. |
| Custom prefix | `PLM-00142` | Company-configurable prefix. |

The generation strategy is chosen at the application/infrastructure layer and is not part of this VO spec.

---

## 6. Invariants

1. Every Job must have exactly one `JobNumber`.
2. `JobNumber` must be non-empty and non-blank.
3. `JobNumber` must not exceed 20 characters.
4. `JobNumber` must be unique within the scope of `company_id`.
5. `JobNumber` is immutable — once assigned, it cannot be changed.
6. `JobNumber` must be assigned at creation time (part of `OpenJob`).

---

## 7. Equality and Identity

`JobNumber` is a value object — it has no identity of its own.

- `JobNumber` is normalized to **uppercase at construction**, so equality is simple stored-string comparison.
- Two `JobNumber` values are equal if and only if their stored strings are identical.
- `JobNumber` is immutable — it cannot be modified after construction.

---

## 8. Uniqueness Enforcement

`JobNumber` uniqueness is scoped to `company_id`:

- Within one company, no two Jobs may share the same `JobNumber`.
- Across companies, duplicate `JobNumber` values are allowed (each company has its own sequence).

### Enforcement mechanism

Uniqueness is enforced at the **persistence layer** via a unique constraint:

```sql
UNIQUE (company_id, job_number)
```

The VO itself does not enforce cross-aggregate uniqueness — that is an infrastructure/repository concern.

---

## 9. Persistence

`JobNumber` persists as a single column on the `jobs` table:

- **Column:** `job_number`
- **Type:** `VARCHAR(20)` or `TEXT` with CHECK
- **Constraint:** `NOT NULL`, `UNIQUE (company_id, job_number)`
- **Immutability:** application-enforced (no UPDATE on this column after INSERT)

---

## 10. Relationship to Other Identifiers

| Identifier | Scope | Purpose | Owned by |
| --- | --- | --- | --- |
| `job_id` | System-wide | Internal aggregate identity (UUID) | Job Engine |
| `job_number` | Per company | Human-facing reference | Job Engine |
| LL152 filing number | Per workflow | Compliance filing reference | LL152 Workflow |
| Invoice number | Per billing | Financial document reference | Billing module |

`JobNumber` is the **primary human reference** for a Job. All other identifiers serve different scopes and purposes.

---

## 11. Commands and Events

### Commands that use JobNumber

| Command | Relationship |
| --- | --- |
| `OpenJob` | `JobNumber` is assigned as part of Job creation |

`JobNumber` does not have its own dedicated command — it is set once during `OpenJob` and never changed.

### Events

`JobNumber` is included in the `JOB_OPENED` event payload so that downstream consumers can associate the human reference with the new Job.

No separate event exists for `JobNumber` assignment because it always occurs as part of creation.

---

## 12. Display and Communication

`JobNumber` is the value used when:

- an office admin says "pull up job J-00142"
- a field worker sees a job reference on their mobile device
- a client receives a confirmation ("your job number is J-00142")
- a report or export lists jobs in a table

It should be displayed **exactly as stored** — no reformatting or truncation in the UI.

---

## 13. Open Decisions

None. The assignment timing question (Job Aggregate Open Decision #2) is resolved: `JobNumber` is always assigned at creation.

---

## 14. Summary

> `JobNumber` is an immutable, company-scoped, human-facing reference string assigned at Job creation. It is unique within a company, speakable over the phone, and serves as the primary human identifier for a Job. Generation strategy is an infrastructure concern; the VO validates format and enforces immutability.
