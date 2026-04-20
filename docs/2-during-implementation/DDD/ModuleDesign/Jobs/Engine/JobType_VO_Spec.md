# JobType Value Object

**Version:** 1.0.1  
**Status:** Official Draft  
**Module:** Job Engine  
**Parent Aggregate:** `Job`

---

## 1. Objective

`JobType` identifies **what kind of work** a Job represents.

It answers the question:

> What workflow governs this job?

It is the **engine/workflow seam discriminator** — the single value that tells the system which workflow module's rules, forms, completeness criteria, and deliverable logic apply.

It does **not** answer:

- why the job was created (that is `SourceKind`)
- how urgent it is (that is `Priority`)
- what lifecycle state it is in (that is `JobStatus`)
- what specific form fields exist (that belongs to the workflow module itself)

---

## 2. What This Value Object Is

`JobType` is:

- a **semi-open enumeration** — new types are added as the platform supports new kinds of work, but existing types must not be removed or renamed without a spec revision
- **required** — every Job must have exactly one `JobType`
- **immutable after creation** — changing the type of work means creating a different job
- the **primary routing key** between the generic Job engine and workflow-specific modules
- **not a workflow itself** — it is a pointer to a workflow, not the workflow logic

---

## 3. What This Value Object Is Not

`JobType` is **not**:

- a workflow engine or state machine (the workflow module owns that)
- a form schema (the workflow module owns field definitions)
- a job status (that is `JobStatus`)
- a categorization for reporting only — it has real behavioral consequences
- a billing code (invoicing may derive from it, but it is not primarily financial)

---

## 4. Enumerated Values

### Known v1 values

| Value | Meaning | Governing workflow |
| --- | --- | --- |
| `LL152_INSPECTION` | Local Law 152 gas piping inspection | LL152 Workflow Module |
| `EMERGENCY` | Emergency response work | Generic handler (may carry urgency defaults) |
| `REPAIR` | A repair job | Generic handler (no specific compliance driver) |

### Future candidate values

| Value | Meaning | Notes |
| --- | --- | --- |
| `ESTIMATE` | An estimate or assessment visit | May convert to a full job via `ESTIMATE_CONVERSION` |
| `FOLLOW_UP` | Follow-up visit from a prior job | Often triggered by a failed inspection. **Caution:** may resolve as a `SourceKind`, a job relationship, or another visit under an existing Job rather than a distinct type. |
| `MAINTENANCE` | Routine maintenance visit | Preventive rather than reactive |

These are **not** committed to. They indicate the direction the enumeration may grow.

### Enumeration rules

1. This enumeration is **semi-open** — new values may be added as the platform supports new kinds of work.
2. Existing values must not be renamed or removed without a spec revision and migration plan.
3. Every `JobType` value must have a corresponding **workflow implementation** registered in the system at runtime. A workflow implementation may be a full workflow module (e.g., LL152) or a minimal generic handler.
4. Values are stored as uppercase strings.

---

## 5. The Engine/Workflow Seam

`JobType` is the **key** that bridges the generic Job engine and workflow-specific modules.

### What the seam means

```
┌─────────────────────────┐          ┌──────────────────────────────┐
│     Job Engine          │          │     Workflow Module          │
│                         │          │                              │
│  job_id                 │          │  workflow-specific state     │
│  job_number             │          │  form schemas                │
│  job_status             │   ────►  │  completeness rules          │
│  job_type ──────────────┼──        │  validation rules            │
│  building_id            │          │  review rules                │
│  client_id              │          │  deliverable generation      │
│  site_notes             │          │  workflow-specific events     │
│  priority               │          │                              │
│  source_kind            │          │                              │
└─────────────────────────┘          └──────────────────────────────┘
```

### Seam contract

The `JobType` value determines:

| Concern | What it routes to |
| --- | --- |
| **Form schema** | Which fields and sections the workflow presents for data capture |
| **Completeness rules** | What counts as "done enough" to allow `CompleteJob` |
| **Validation rules** | What domain-specific validation applies to captured data |
| **Review rules** | What review process (if any) applies before completion |
| **Deliverable logic** | What output artifacts the workflow must produce |
| **Workflow-specific state** | What finer-grained states the workflow tracks internally |

### What JobType does NOT route

| Concern | Why it stays in the engine |
| --- | --- |
| Generic lifecycle (`JobStatus`) | Same 4 states for all job types |
| Identity (`job_id`, `job_number`) | Same model for all job types |
| References (`building_id`, `client_id`) | Same model for all job types |
| Priority, SourceKind | Type-independent classification |

---

## 6. Invariants

1. Every Job must have exactly one `JobType`.
2. `JobType` must be non-empty and must resolve to a value registered in the system's workflow registry.
3. `JobType` is immutable — once set at creation, it cannot be changed.
4. Every registered `JobType` must have a corresponding workflow implementation.
5. Changing the kind of work requires creating a new Job, not mutating the type.

---

## 7. Relationship to Title Auto-Generation

> **Note:** Title generation is a downstream application concern, not a core reason `JobType` exists. This section documents how `JobType` participates in it.

`JobType` is one of two inputs to the auto-generated `title`:

```
{job_type display name} - {building address}
```

Examples:

- `LL152 Inspection - 123 Main St`
- `Repair - 98 Atlantic Ave`
- `Estimate Visit - 45 Court St`

Each `JobType` value must have a **human-readable display name** for title generation purposes. This display name is a presentation concern, not a domain invariant, but it must exist for every registered type.

---

## 8. Equality and Identity

`JobType` is a value object — it has no identity of its own.

- Two `JobType` values are equal if and only if they contain the same enumerated value.
- Values are stored and compared as uppercase strings.
- `JobType` is immutable — it cannot be modified after construction.

---

## 9. Commands and Events

### Commands

`JobType` is set as part of `OpenJob`. There is no dedicated command for `JobType`.

It has **no update command** — the kind of work a job represents does not change.

### Events

`JobType` is included in the `JOB_OPENED` event payload. Downstream consumers (including workflow modules) use this value to determine whether they need to react to the new Job.

No separate event exists for `JobType` because it is always set as part of creation.

---

## 10. Persistence

`JobType` persists as a single column on the `jobs` table:

- **Column:** `job_type`
- **Type:** `VARCHAR(40)` or `TEXT` with CHECK
- **Constraint:** `NOT NULL`, CHECK against registered values
- **Immutability:** application-enforced (no UPDATE on this column after INSERT)

---

## 11. Workflow Registration

Every `JobType` value must have a corresponding entry in the system's workflow registry.

### Registry contract (conceptual)

A workflow implementation must provide:

| Field | Purpose |
| --- | --- |
| `job_type` value | The enum value this workflow handles |
| Display name | Human-readable name for title generation and UI |
| Completeness check | Function/rule that determines if workflow criteria are met for `CompleteJob` |
| Form schema reference | Pointer to the workflow's data capture schema |

### v1 reality

For v1, only one workflow module exists: **LL152 Inspection**. The registry mechanism may be implicit (hardcoded dispatch) rather than a formal plugin system. The spec documents the conceptual contract so that future types can be added cleanly.

---

## 12. Open Decisions

1. **Workflow registration mechanism**  
   Is the mapping from `JobType` to workflow implementation a formal registry (table, config), a code-level dispatch (switch/match), or a plugin system? For v1 with a single type, this can be deferred, but the decision affects how easily new types are added. This will likely resolve during LL152 workflow implementation.

2. **Default/generic workflow implementation**  
   If a `JobType` is registered but its workflow implementation is minimal (e.g., a simple `REPAIR` with no compliance forms), does it fall through to a generic handler, or must every type have a fully specified workflow? This affects how quickly new job types can be added.

---

## 13. Summary

> `JobType` is a required, immutable, semi-open enumeration that identifies what kind of work a Job represents. It is the engine/workflow seam discriminator — the single value that routes a generic Job to its governing workflow module's rules, forms, completeness criteria, and deliverable logic. The only v1 value is `LL152_INSPECTION`. New values are added as the platform supports new kinds of work.
