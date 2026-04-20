# Value Objects — Walkthrough

The Job Engine uses 5 Value Objects to enforce business rules at the type level. Each VO validates at construction and is immutable thereafter.

## JobStatus

**File:** `crates/pcd-domain/src/jobs/job_status.rs` (92 lines)

State machine enum with transition validation.

```rust
pub enum JobStatus {
    Open,
    InProgress,
    Completed,  // terminal
    Canceled,   // terminal
}
```

| Method | Purpose |
| :--- | :--- |
| `initial()` | Returns `Open` |
| `transition_to(target)` | Validates transition, returns `Err(InvalidTransition)` if invalid |
| `is_terminal()` | Returns `true` for `Completed` and `Canceled` |
| `as_str()` / `from_str()` | Serialization roundtrip (`OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELED`) |

**Allowed transitions:**
- `Open → InProgress`, `Open → Canceled`
- `InProgress → Completed`, `InProgress → Canceled`
- Terminal states have zero valid transitions

---

## JobNumber

**File:** `crates/pcd-domain/src/jobs/job_number.rs` (40 lines)

Company-scoped sequential identifier (e.g., `JOB-00001`).

**Validation rules:**
- Non-empty (rejects empty string and whitespace-only)
- Max 20 characters
- Normalized to **uppercase** at construction

```rust
let num = JobNumber::new("job-00001")?;
assert_eq!(num.value(), "JOB-00001");
```

---

## JobType

**File:** `crates/pcd-domain/src/jobs/job_type.rs` (43 lines)

Extensible enum identifying the kind of work.

| Value | Display Name | Workflow |
| :--- | :--- | :--- |
| `LL152_INSPECTION` | "LL152 Inspection" | LL152 Workflow Module |
| `EMERGENCY` | "Emergency" | Generic handler |
| `REPAIR` | "Repair" | Generic handler |

**Methods:**
- `from_str()` — parses uppercase string, rejects unknown values
- `display_name()` — human-readable label for UI
- `as_str()` — uppercase string for persistence
- `all()` — returns all variants as a slice (for UI dropdowns)

**Design:** Semi-open enum per ADR-0016. New job types are added as variants and don't require schema changes.

---

## SourceKind

**File:** `crates/pcd-domain/src/jobs/source_kind.rs` (50 lines)

Tracks how a job was initiated.

| Value | Description |
| :--- | :--- |
| `OBLIGATION_DRIVEN` | System-generated from compliance obligation |
| `CUSTOMER_REQUEST` | Owner/manager contacted the firm |
| `FOLLOW_UP` | Return visit from previous work |
| `ESTIMATE_CONVERSION` | Estimate accepted by client |
| `OFFICE_INITIATED` | Internal decision by office staff |
| `EMERGENCY_CALL` | Urgent emergency request |

**Optional field:** A job can exist without a source kind.

---

## Priority

**File:** `crates/pcd-domain/src/jobs/priority.rs` (50 lines)

Three-level urgency ranking.

| Value | Rank | Use Case |
| :--- | :--- | :--- |
| `NORMAL` | 0 | Default work |
| `HIGH` | 1 | Time-sensitive |
| `URGENT` | 2 | Emergency / overdue deadlines |

**Implements `Ord`:** Priorities can be sorted — `NORMAL < HIGH < URGENT`.

**Optional field:** A job can exist without a priority. No default is assigned automatically.
