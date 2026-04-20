# Job Aggregate

**Version:** 1.2.0  
**Status:** Updated — synced with Phase 1.5 implementation (2026-03-27)  
**Module:** Job Engine  
**Aggregate Root:** `Job`

---

## 1. Objective

The Job aggregate exists to represent a **specific piece of work** that the company intends to perform.

It is the generic, workflow-agnostic work container of the Job Engine.

The Job aggregate answers the following domain questions:

- What work is being done?
- For whom is it being done?
- Where is it being done?
- What kind of job is it?
- What other domain objects does it reference?
- What is its current generic lifecycle state?
- Who currently has broad ownership of it?

The Job aggregate does **not** answer workflow-specific questions such as:

- What fields are on a specific workflow form?
- What counts as a complete workflow submission?
- What review rules apply to a specific workflow?
- What photos or evidence are required?
- What deliverable packet must be generated?

Those belong to workflow-specific modules.

---

## 2. Core Architectural Position

The Job aggregate is the **engine layer** of the Job module.

It is intentionally separated from:

- workflow-specific details
- dispatch / booking execution details
- billing / invoice concerns
- deliverable generation concerns

### Design Principle

A Job is a **durable work container**, not a full business pipeline.

This allows the aggregate to remain reusable across many kinds of trades work, including:

- LL152 inspection
- repair job
- estimate visit
- follow-up job
- maintenance visit
- emergency call

---

## 3. What This Aggregate Is

A Job is:

- company-scoped (where "company" may be a firm or an independent plumber — see [ADR-0017](../../../../adr/0017-independent-plumber-tenancy.md))
- a single identifiable unit of work
- performed for a client (client may be attached later, not required at creation)
- tied to a place/building
- categorized by job type
- optionally related to a compliance obligation
- tracked through a small generic lifecycle

---

## 4. What This Aggregate Is Not

The Job aggregate is **not**:

- a Building identity aggregate
- a Compliance aggregate
- a dispatch calendar
- a booking / visit record
- an assignment history log
- a workflow payload store
- an invoice or materials ledger
- a deliverable / report generator

### Important Negative Boundaries

The Job aggregate does **not** own:

- visit scheduling windows
- technician travel / arrival states
- LL152 findings
- GPS1 / GPS2 payloads
- workflow-specific completeness rules
- workflow-specific review rules
- photos / evidence requirements
- invoice / payment state
- labor / material line items

---

## 5. Aggregate Root

**Aggregate Root:** `Job`

The `Job` aggregate root owns the generic identity, references, lifecycle, and minimal operational context required for a piece of work.

---

## 6. Identity Model

### Root Identity

- `job_id` — stable internal aggregate identity

### Human Reference

- `job_number` — human-facing reference used by office staff and field staff

### Type Identity

- `job_type` — identifies the workflow type that governs type-specific behavior

### Scope Identity

- `company_id` — identifies which company owns the job

---

## 7. Core References

The aggregate may reference other domain objects, but does not own them.

### Required references

- `address` — freeform text from the caller (always required)

### Optional references

- `building_id` — resolved reference to a global building (optional; resolved lazily)
- `client_id`
- `compliance_obligation_id`
- `requester_contact_id`

### Notes

- **Address-first (ADR-0023):** Per the "notebook test" design, `address` is always required and `building_id` is optional. A job can be created with just an address (e.g., "123 Main St") and matched to a building later. The `building_unresolved` flag tracks whether resolution is pending.
- `client_id` is an **account-level reference** — the entity the work is being done for (e.g., a property management company, a condo board, a landlord). This is who you bill, who owns the relationship. It is optional because jobs may be created from an obligation or building before a client contact is known. The client can be attached later. See [ADR-0018](../../../../adr/0018-client-account-vs-requester-contact.md).
- `compliance_obligation_id` is optional because not all jobs are obligation-driven.
- `requester_contact_id` captures the specific **person** who initiated this job request, when that person is meaningfully distinct from the client/account the work is for. Examples: the super who called, the board secretary who emailed, the tenant liaison who flagged the issue. Optional, secondary, and deferred until intake reality proves it matters. Must not duplicate or replace `client_id`.

---

## 8. Core Field Set

### 8.1 Required fields

| Field | Meaning |
|---|---|
| `job_id` | Stable aggregate identity |
| `job_number` | Human-facing job reference |
| `company_id` | Company ownership |
| `job_type` | Workflow discriminator |
| `address` | Freeform address text from caller (always required) |
| `title` | Short human-readable job label (auto-generated, optionally editable) |
| `job_status` | Small generic lifecycle state |
| `created_at` | Creation timestamp |
| `created_by_user_id` | Actor who created the job |

### 8.2 Optional fields

| Field | Meaning |
|---|---|
| `building_id` | Resolved building reference (optional; set when address maps to a known building) |
| `building_unresolved` | Flag indicating the address has not been resolved to a building_id yet |
| `client_id` | Client/service-account reference (attached when known) |
| `compliance_obligation_id` | Optional obligation linkage |
| `requester_contact_id` | Optional contact who requested the work |
| `summary` | Optional generic work description |
| `source_kind` | Why the job exists |
| `priority` | Generic operational priority |
| `site_notes` | Practical job-site context (location, access, entry instructions) |
| `assigned_to` | Who is dispatched to execute this job's fieldwork (see [ADR-0034](../../../../adr/0034-role-aware-workspace-interaction.md)) |
| `started_at` | Generic work-start timestamp |
| `completed_at` | Generic completion timestamp |
| `canceled_at` | Generic cancellation timestamp |
| `cancellation_reason` | Reason the job was canceled |
| `updated_at` | Last modification timestamp |

---

## 9. Universal Field Meanings

### `title`
A short, human-readable job label. **Auto-generated** at creation from `job_type` + building address. Optionally editable by the user after creation.

Auto-generated examples:
- `LL152 Inspection - 123 Main St`
- `Boiler Repair - 98 Atlantic Ave`
- `Estimate Visit - 45 Court St`

### `summary`
An optional, concise, generic description of the work being requested or performed. Not auto-generated — the user fills this in when extra context is helpful.

This field must remain workflow-agnostic.

Examples:
- `tenant reported gas smell in basement`
- `follow-up from last month's failed inspection`
- `landlord wants estimate before scheduling full job`

### `source_kind`
Why the job exists.

Candidate values:
- `OBLIGATION_DRIVEN`
- `CUSTOMER_REQUEST`
- `FOLLOW_UP`
- `ESTIMATE_CONVERSION`
- `OFFICE_INITIATED`
- `EMERGENCY_CALL`

### `priority`
A generic urgency or importance indicator.

Candidate values:
- `NORMAL`
- `HIGH`
- `URGENT`

### `site_notes`
Practical, job-specific context about the work location and access. Captures where on site the work happens, how to get in, who to call, and any entry quirks — all in one field.

This is a single combined field because in practice, office users write location and access context together as one natural note.

Examples:
- `cellar meter room, super has the key, call before coming`
- `rear commercial unit — lockbox code 4521`
- `roof access hatch, tenant must be home to let you in`
- `boiler room in basement, enter through side door`

> Split into separate fields only if a future need emerges for structured validation or separate display/routing of location vs access data.

---

## 10. Lifecycle Model

The Job aggregate owns only the smallest generic lifecycle shared across many job types.

### Design principle

> The Job engine owns **coarse lifecycle meaning**.
> Workflow and dispatch modules own the **finer-grained operational meaning**.
>
> - Booking tells you *when labor is arranged*
> - Workflow tells you *what detailed progress exists*
> - Job tells you *whether the work record is open, active, finished, or dead*

### Lifecycle states

- `OPEN`
- `IN_PROGRESS`
- `COMPLETED`
- `CANCELED`

### State definitions

**`OPEN`** — The job exists and is active, but no meaningful execution has begun. The job may be dispatched, scheduled, or assigned during this state — those are booking/dispatch concerns, not engine lifecycle transitions.

**`IN_PROGRESS`** — Execution of the job has begun, triggered by an explicit `StartJob` command. Workflow activity (e.g., a field worker begins capture, evidence is recorded) may satisfy the precondition for issuing `StartJob`, but does not implicitly cause the transition. Dispatch, scheduling, assignment, and travel do **not** trigger this transition. Only real execution does.

**`COMPLETED`** — The job has been formally concluded by an authorized actor after the governing workflow has satisfied its completion criteria. The engine does not autonomously decide completion — the workflow declares its own criteria met, and an authorized actor (typically the LMP) completes the Job at the engine level.

**`CANCELED`** — The job is no longer intended to proceed. **`CANCELED` is terminal.** A canceled Job cannot be reopened. If work resumes later, a new Job must be created, optionally linked to the original through a future job-relationship mechanism.

### Valid transitions

```
OPEN → IN_PROGRESS     (first real execution activity)
OPEN → CANCELED         (work abandoned before starting)
IN_PROGRESS → COMPLETED (authorized actor + workflow criteria satisfied)
IN_PROGRESS → CANCELED  (work abandoned after starting)
```

No other transitions are valid. In particular:
- `COMPLETED` and `CANCELED` are both **terminal** — no backward transitions.
- There is no `COMPLETED → CANCELED` or `CANCELED → OPEN` path.

### Transition rules

| Transition | Trigger | Guard |
|---|---|---|
| `OPEN → IN_PROGRESS` | `StartJob` command | Job must be in `OPEN` state |
| `OPEN → CANCELED` | `CancelJob` command | Job must be in `OPEN` state |
| `IN_PROGRESS → COMPLETED` | `CompleteJob` command | Workflow completion criteria must be satisfied |
| `IN_PROGRESS → CANCELED` | `CancelJob` command | Job must be in `IN_PROGRESS` state |

> Authorization policy (who may issue these commands) is defined by the Job aggregate and role model, not by `JobStatus`. See `JobStatus_VO_Spec.md`.

### Explicit exclusions

These are **not** part of the pure Job lifecycle:

- `SCHEDULED` / `UNSCHEDULED`
- `DISPATCHED`
- `TRAVELING` / `ARRIVED` / `LATE`
- `RETURNED_FOR_REVIEW`
- `SUBMITTED`

Those belong either to:

- booking / dispatch concepts, or
- workflow-specific lifecycle extensions

---

## 11. Invariants

### Identity invariants

1. Every Job must have exactly one `job_id`.
2. Every Job must have exactly one `job_number`.
3. Every Job must belong to exactly one `company_id`.

### Reference invariants

4. Every Job must have an `address` (non-empty text).
4a. A Job may optionally reference a `building_id` (resolved lazily from address).
5. A Job may reference at most one `client_id`.
6. A Job may reference at most one `compliance_obligation_id`.

### Type invariants

7. Every Job must have exactly one `job_type`.
8. `job_type` determines which workflow extension rules may apply.

### Lifecycle invariants

9. Every Job must always have exactly one `job_status`.
10. If `job_status = COMPLETED`, then `completed_at` must be present.
11. If `job_status = CANCELED`, then `canceled_at` must be present.
12. If `job_status = CANCELED`, then `cancellation_reason` should be present.
13. If `completed_at` is present, `job_status` must be `COMPLETED`.
14. If `canceled_at` is present, `job_status` must be `CANCELED`.

### Boundary invariants

15. The Job aggregate must not directly own workflow-specific form payloads.
16. The Job aggregate must not directly own booking / visit execution records.
17. The Job aggregate must not directly own invoice / payment state.

---

## 12. Candidate Commands

These are generic Job-engine commands, not workflow-specific commands.

- `OpenJob`
- `UpdateJobSummary`
- `UpdateJobSiteNotes`
- `UpdateJobPriority`
- `AttachClient`
- `AssignJobOwnership`
- `StartJob`
- `CompleteJob`
- `CancelJob`
- `LinkComplianceObligation`
- `UnlinkComplianceObligation`

### Command notes

- `AttachClient` allows `client_id` to be set after job creation, since client may not be known at intake.
- `AssignJobOwnership` means lightweight ownership only, not full dispatch scheduling.
- Workflow modules may define additional commands outside the pure Job aggregate.

---

## 13. Candidate Events

These are generic Job events.

- `JOB_OPENED`
- `JOB_SUMMARY_UPDATED`
- `JOB_SITE_NOTES_UPDATED`
- `JOB_PRIORITY_UPDATED`
- `JOB_CLIENT_ATTACHED`
- `JOB_OWNERSHIP_ASSIGNED`
- `JOB_STARTED`
- `JOB_COMPLETED`
- `JOB_CANCELED`
- `JOB_OBLIGATION_LINKED`
- `JOB_OBLIGATION_UNLINKED`

### Event scope rule

Events in this aggregate must remain generic.

Examples of events that do **not** belong here:
- `GPS1_SUBMITTED`
- `LL152_REVIEW_RETURNED`
- `PHOTOS_VALIDATED`
- `DELIVERABLE_PACKET_GENERATED`

Those belong to workflow-specific modules.

---

## 14. Engine / Workflow Seam

The Job aggregate is the engine layer.

Workflow modules may plug into the Job through `job_type` and a workflow extension model.

### Engine owns

- generic identity
- generic references
- generic lifecycle
- generic ownership
- generic context fields

### Workflow owns

- form schemas
- findings models
- completeness rules
- validation rules
- review rules
- deadline rules
- deliverable generation
- workflow-specific states beyond the generic lifecycle

### Dual-status pattern (ADR-0025)

Workflow modules that have richer lifecycles (e.g., LL152) persist their own `workflow_status` on their extension table, parallel to the generic `job_status`. The engine's coarse states (`OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELED`) coexist with the workflow's detailed states (`DRAFT`, `CAPTURING`, `READY_FOR_REVIEW`, etc.). The two are coordinated but independently owned. See [ADR-0025](../../../../adr/0025-dual-status-model.md).

---

## 15. Neighboring Concepts (Outside Job Core)

These are likely neighboring modules/entities rather than Job fields.

### Likely separate concepts

- `Booking` / `Visit`
- `DispatchAssignment`
- `WorkflowExtension`
- `JobAttachment`
- `JobComment`
- `JobEventHistory`
- `InvoiceLink`
- `EstimateLink`

### Notes

These may still be related to Job, but they should not automatically be folded into the aggregate root.

---

## 16. Supporting Value Objects to Spec Next

These are the strongest candidate supporting specs.

### Likely VO candidates

- `JobNumber`
- `JobType`
- `JobStatus`
- `SourceKind`
- `Priority`

### Lower-confidence candidates

- `SiteNotes`
- `JobTitle`
- `JobSummary`

These may remain simple fields unless stronger invariants emerge.

---

## 17. Open Decisions

The following points remain unresolved and should be validated before declaring the aggregate fully stable.

1. ~~**`created_at` vs `opened_at`**~~
   Resolved: Collapsed to `created_at`. The `Job::open()` factory creates and opens in a single step — there is no state where a Job exists but hasn't been opened. The `JOB_OPENED` domain event timestamp serves as the opening marker if the distinction ever matters for audit.

2. ~~**`job_number` timing**~~
   Resolved: `JobNumber` is always assigned at creation. See `JobNumber_VO_Spec.md`.

3. ~~**`responsible_user_id` scope**~~
   Resolved → **Superseded by 3C.1 Q3.** The original `responsible_user_id` was a premature abstraction. Replaced by `assigned_to: Option<Uuid>` — a single field meaning "who is dispatched to execute this job's fieldwork." TECHNICIAN scoping in the authorization model (ADR-0034) depends on this field: `WHERE assigned_to = $auth.user_id`. The Booking/Dispatch module concern (§15) remains deferred.

4. ~~**Generic lifecycle depth**~~
   Resolved: `OPEN / IN_PROGRESS / COMPLETED / CANCELED` is sufficient. See §10.

5. ~~**Source kind universality**~~
   Resolved: Keep as optional. The 6 `SourceKind` values (`OBLIGATION_DRIVEN`, `CUSTOMER_REQUEST`, `FOLLOW_UP`, `ESTIMATE_CONVERSION`, `OFFICE_INITIATED`, `EMERGENCY_CALL`) cover all observed intake patterns. If a job source doesn't fit, it can be omitted. Adding new values to the enum is non-breaking.

6. ~~**Priority requirement**~~
   Resolved: Keep optional. Defaults to no priority (not "NORMAL"). Emergency/repair scenarios can set `URGENT`, but requiring priority on every job adds intake friction without proportional benefit. The VO spec defines 3 values: `NORMAL`, `HIGH`, `URGENT`.

7. ~~**Job relationships**~~
   Resolved: Deferred. No `parent_job_id` for now. If follow-up/callback patterns emerge during production use, design a dedicated `JobRelationship` model then. Avoid premature coupling between Job aggregates.

---

## 18. Persistence Shape (First Draft)

A first persistence sketch for the aggregate root may look like:

### `jobs`

- `job_id`
- `job_number`
- `company_id`
- `job_type`
- `address` (TEXT NOT NULL)
- `building_id` (UUID, nullable — resolved lazily)
- `building_unresolved` (BOOLEAN, default true)
- `client_id`
- `compliance_obligation_id`
- `requester_contact_id`
- `title`
- `summary`
- `source_kind`
- `priority`
- `site_notes`
- `assigned_to`
- `job_status`
- `created_at`
- `created_by_user_id`
- `started_at`
- `completed_at`
- `canceled_at`
- `cancellation_reason`
- `updated_at`

This is only a sketch and does not yet define indexes, foreign-key policy, or extension-table contracts.

---

## 19. First Official Summary

The current official definition is:

> A Job is a company-scoped, workflow-agnostic work container representing a specific piece of work to be performed at a building/site, typically for a client, with stable identity, generic references, minimal context, lightweight ownership, and a small generic lifecycle.

This definition must remain stable even as specific workflow types such as LL152 are designed later.

---

## 20. Next Spec Candidates

After stabilizing `Job_Aggregate.md`, the next likely supporting specs are:

1. `JobStatus_VO_Spec.md`
2. `JobNumber_VO_Spec.md`
3. `SourceKind_VO_Spec.md`
4. `Priority_VO_Spec.md` (if kept as structured enum/policy object)
5. `JobType_VO_Spec.md`
6. `LL152_Inspection_Workflow_Spec.md`

---

## 21. Drafting Note

This document is the official 1.1.0 draft of the pure Job aggregate.

It is intentionally focused on the **Job engine** and must not expand to absorb workflow, dispatch, billing, or deliverable concerns.

