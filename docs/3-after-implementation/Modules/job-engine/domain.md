# Job Aggregate — Domain Walkthrough

**File:** `crates/pcd-domain/src/jobs/job.rs` (387 lines)

## Overview

The `Job` struct is the aggregate root of the Job Engine. It encapsulates identity, references, context, ownership, lifecycle state, and uncommitted domain events. All mutations go through command methods that enforce invariants and emit events.

## Struct Layout

The aggregate organizes its 24 fields into 5 logical groups:

```rust
pub struct Job {
    // Identity (immutable after creation)
    pub id: Uuid,
    pub job_number: JobNumber,
    pub company_id: Uuid,
    pub job_type: JobType,

    // References (mutable — can be attached/linked later)
    pub address: String,                // always required (address-first per ADR-0023)
    pub building_id: Option<Uuid>,      // resolved lazily from address
    pub building_unresolved: bool,      // true until building_id is resolved
    pub client_id: Option<Uuid>,
    pub compliance_obligation_id: Option<Uuid>,
    pub requester_contact_id: Option<Uuid>,

    // Context (mutable while non-terminal)
    pub title: String,
    pub summary: Option<String>,
    pub source_kind: Option<SourceKind>,
    pub priority: Option<Priority>,
    pub site_notes: Option<String>,

    // Ownership
    pub assigned_to: Option<Uuid>,
    pub created_by_user_id: Uuid,

    // Lifecycle
    pub status: JobStatus,
    pub created_at: DateTime<Utc>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub canceled_at: Option<DateTime<Utc>>,
    pub cancellation_reason: Option<String>,
    pub updated_at: DateTime<Utc>,

    // Internal (not persisted as a field)
    uncommitted_events: Vec<JobDomainEvent>,
}
```

## Factory: `Job::open()`

Creates a new Job in `OPEN` state. This is the **only way** to create a Job — there's no public constructor.

**Validation chain:**
1. `JobNumber::new()` — validates non-empty, max 20 chars, normalizes to uppercase
2. `JobType::from_str()` — validates against known types (`LL152_INSPECTION`, `EMERGENCY`, `REPAIR`)
3. `SourceKind::from_str()` — optional, validates against 6 values
4. `Priority::from_str()` — optional, validates against 3 values

**Auto-generated title:** If no title is provided, one is generated from `"{display_name} - {address}"` (e.g., "LL152 Inspection - 123 Main St"). Falls back to `"{display_name} - Job {number}"` if address is not useful.

**Event:** Emits `JobOpened` with a typed `JobOpenedPayload` struct containing all creation parameters.

## Reconstitution: `Job::reconstitute()`

Rebuilds a Job from database columns **without** emitting events. Used by the repository adapter when loading from persistence. All VOs are re-parsed (to enforce type safety) but no business rules are re-validated.

## Commands

### Lifecycle Commands (state transitions)

| Command | Method | Transition | Timestamp Set |
| :--- | :--- | :--- | :--- |
| StartJob | `start()` | OPEN → IN_PROGRESS | `started_at` |
| CompleteJob | `complete()` | IN_PROGRESS → COMPLETED | `completed_at` |
| CancelJob | `cancel(reason)` | OPEN\|IN_PROGRESS → CANCELED | `canceled_at` + `cancellation_reason` |

### Update Commands (guarded by `guard_not_terminal`)

| Command | Method | What Changes |
| :--- | :--- | :--- |
| UpdateSummary | `update_summary(new)` | `summary` field |
| UpdateSiteNotes | `update_site_notes(new)` | `site_notes` field |
| UpdatePriority | `update_priority(new)` | `priority` field (re-validates VO) |

### Reference Commands (guarded by `guard_not_terminal`)

| Command | Method | What Changes |
| :--- | :--- | :--- |
| AttachClient | `attach_client(id)` | `client_id` field |
| Assign | `assign(user_id, actor)` | `assigned_to` field |
| LinkObligation | `link_obligation(id)` | `compliance_obligation_id` field |
| UnlinkObligation | `unlink_obligation()` | Clears `compliance_obligation_id` (requires one to be linked) |

## Error Handling

```rust
pub enum JobError {
    InvalidJobNumber(String),      // Bad format at creation
    InvalidJobType(String),        // Unknown job type
    InvalidSourceKind(String),     // Unknown source kind
    InvalidPriority(String),       // Unknown priority value
    InvalidTransition(..),         // State machine violation
    TerminalState { command, status }, // Update on COMPLETED/CANCELED
    NoObligationLinked,            // Unlink when none linked
}
```

All 7 error variants are exercised by the test suite.

## Event Management

Events are accumulated in `uncommitted_events: Vec<JobDomainEvent>` during command execution. The repository's `save()` method persists them to `job_events`, then calls `clear_uncommitted_events()`.

```
Command → mutate state → emit event → save() → persist job + events in TX → clear events
```
