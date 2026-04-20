# ComplianceObligation Aggregate Specification

**Module:** `CRM` (Compliance)
**Aggregate:** `ComplianceObligation`
**Primary link:** `Building` (by `building_id`)
**Program link:** `LL152Program` (today) / future `Program` aggregates (later)
**Source of Truth:** `crates/pcd-domain/src/crm/compliance_obligation.rs` + `crates/pcd-db/src/crm/obligations.rs`
**Version:** 2.0.0

---

## Objective

Provide a single, scalable aggregate for tracking **per-building compliance duties** across multiple NYC programs.

This spec is designed to:

1. Track compliance duties for **LL152** without embedding LL152 logic inside `Building`.
2. Scale to many future obligations without schema churn.
3. Avoid assumptions: canonical dates and requirements come from **explicit authorities** (program policy + DOB datasets + user-provided evidence), not from inferred building attributes.

---

## 1) What this Aggregate is

A `ComplianceObligation` represents:

* **One building**
* **One program**
* **One cycle/period**

It stores:

* The **official deadline window** for the obligation (inspection window / filing windows when applicable).
* The **facts/evidence** a user provides (inspection performed date, filing dates, report details, etc.).
* A **derived status** computed from facts + deadlines.

---

## 2) What this Aggregate is NOT

* It is not a job/work order dispatcher. (That belongs in a `WorkOrder` / `InspectionJob` aggregate.)
* It does not own building identity or canonical building metadata (BIN/address/BBL/CD/class). Those live in `Building`.
* It does not "discover" whether a building is in-scope by guessing from building metadata.

---

## 3) Authorities (No-Assumptions)

### 3.1 Canonical deadline authority

A deadline window is written from exactly one of the following:

1. **Program policy schedule** (e.g., LL152 schedule windows as published by DOB / codified in rule).
2. **DOB published property list / roster** when it provides per-property deadlines.

If both exist:

* Store both, choose one as canonical according to the program's import policy (see `LL152ProgramSpec`).
* Never overwrite silently; record a mismatch anomaly.

### 3.2 Canonical compliance facts authority

Facts are written only by:

* **User/operator actions** in the app (uploads, date entry, confirmations), or
* **An authoritative filing/portal integration** (future).

### 3.3 Building metadata is external

The obligation may read `Building` fields for derived computation (e.g., community district → subcycle), but it does not own them.

---

## 4) Core Model

### 4.1 Identity

A `ComplianceObligation` is uniquely identified by:

* `building_id` (UUID)
* `program_code` (e.g., `LL152`)
* `cycle_key` (a program-defined key)

**Uniqueness invariant:** `(building_id, program_code, cycle_key)` must be unique.

### 4.2 Program cycle key

A cycle key is program-defined and must be stable over time.

Example (LL152):

* `cycle_key = "2026"` (cycle year)
* Program-specific details like `subcycle` are stored in the program's extension table (e.g., `ll152_obligation_details`), not on the engine.

> System decision: Store `cycle_year` separately for query ergonomics, even if the program's cycle key is string-based.

---

## 5) Data Fields

### 5.1 Required fields

* `id: UUID`
* `building_id: UUID`
* `program_code: string` (enum-like; e.g., `LL152`)
* `cycle_key: string`

### 5.2 Canonical deadline window

* `window_start: date?`
* `window_end: date?`
* `deadline_source: enum` = `PROGRAM_SCHEDULE | DOB_ROSTER | MANUAL`
* `deadline_source_version: string?` (e.g., schedule version, roster version)

> Invariant: if `window_start` is present, `window_end` must be present and `window_start <= window_end`.

### 5.3 Optional filing windows (relative to an inspection date)

For programs like LL152 where the rule defines "within N days of inspection," store:

* `inspection_date: date?`
* `report_to_owner_due_days: int?` (LL152: 30)
* `owner_filing_due_days: int?` (LL152: 60)
* `correction_cert_due_days: int?` (LL152: 120)
* `final_correction_due_days: int?` (LL152: 180)

And store the user-reported facts:

* `report_delivered_at: date?`
* `cert_filed_at: date?` (GPS2)
* `correction_cert_filed_at: date?` (120-day pathway)
* `final_correction_cert_filed_at: date?` (180-day pathway)

> Invariant: filing windows are program policy values; they are not inferred from user input.

### 5.4 Correction branching (LL152)

Store the minimum fields needed to determine whether the 120/180 branches apply:

* `conditions_requiring_correction: boolean?`
* `additional_time_needed: boolean?`

### 5.5 Alternate "not required" pathways (LL152)

Store user-reported "statement/certification filed" facts without assuming they exist unless provided:

* `no_gas_piping_cert_filed_at: date?`
* `no_gas_service_statement_filed_at: date?`

> Program rule nuance: some of these statements are "submit once" pathways. Whether DOB accepts them is an external fact; we track what the user reports and attach evidence.

### 5.6 Extension tracking (LL152)

LL152 allows a one-time 180-day extension per cycle (requested via DOB mechanism).

Store only what we can know without guessing:

* `extension_requested_at: date?`
* `extension_granted_at: date?` (if user confirms)
* `extension_deadline: date?` (if known, e.g., shown in DOB portal)
* `extension_notes: text?`

> System decision: do not compute `extension_deadline` unless the program policy explicitly defines how the extension deadline is calculated OR the user provides the deadline.

### 5.7 Provenance

* `created_from_source: string` (e.g., `DOB_ROSTER`, `MANUAL`)
* `created_from_version: string?`
* `last_imported_from_source: string?`
* `last_imported_from_version: string?`
* `last_imported_at: timestamp?`

### 5.8 Evidence attachments (optional)

A general mechanism to link artifacts:

* `evidence: EvidenceBundle` (VO)

  * `documents[]` (URLs/keys)
  * `notes` (text)
  * `verified_by` (user id)
  * `verified_at` (timestamp)

---

## 6) Status Model (Derived)

### 6.1 ObligationStatus

`status` is a derived summary for UX and filtering.

Recommended enum (generic):

* `UNKNOWN` (insufficient data)
* `OPEN` (within cycle window and not satisfied)
* `DUE_SOON` (within a configurable threshold)
* `OVERDUE` (past deadline and not satisfied)
* `SATISFIED` (completed via an accepted pathway)
* `AT_RISK` (facts indicate a rule-based risk condition, e.g., filing too late)
* `NOT_REQUIRED` (user-reported statement/cert pathway)

> Rule: status must always be recomputable from persisted facts. Treat `status` as denormalized.

### 6.2 Satisfaction paths

A satisfied obligation records *how* it was satisfied:

* `satisfaction_path: enum?`

  * `INSPECTION_CERTIFICATION`
  * `NO_GAS_PIPING_CERTIFICATION`
  * `NO_GAS_SERVICE_STATEMENT`
  * (future)

---

## 7) Commands (Write API)

All commands must be idempotent and must trigger `recomputeStatus()`.

### 7.1 Creation / upsert

* `upsertFromRoster({ building_id, program_code, cycle_key, window_start, window_end, deadline_source_version })`
* `createManual({ building_id, program_code, cycle_key, window_start?, window_end? })`

### 7.2 Recording inspection + filings

* `recordInspection({ inspection_date, performed_by?, notes? })`
* `recordReportDelivered({ report_delivered_at })`
* `recordCertificationFiled({ cert_filed_at, confirmation_number?, method? })`
* `recordCorrectionCertification({ correction_cert_filed_at, additional_time_needed })`
* `recordFinalCorrectionCertification({ final_correction_cert_filed_at })`

### 7.3 Not-required pathways

* `recordNoGasPipingCertification({ no_gas_piping_cert_filed_at })`
* `recordNoGasServiceStatement({ no_gas_service_statement_filed_at })`

### 7.4 Extension

* `recordExtensionRequested({ extension_requested_at })`
* `recordExtensionGranted({ extension_granted_at, extension_deadline? })`

### 7.5 Reconciliation

* `attachMismatchAnomaly({ type, canonical_value, incoming_value, source, version })`

---

## 8) Events

* `ObligationCreated`
* `ObligationDeadlineUpdated`
* `ObligationFactRecorded`
* `ObligationEvidenceAttached`
* `ObligationStatusRecomputed`

---

## 9) Invariants

* `(building_id, program_code, cycle_key)` is unique.
* `window_start <= window_end` when both present.
* If `status = SATISFIED`, then `satisfaction_path` must be non-null.
* If `satisfaction_path = INSPECTION_CERTIFICATION`, then `inspection_date` must be non-null.

---

## 10) Persistence (SQL spec)

```sql
CREATE TABLE compliance_obligations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  building_id UUID NOT NULL REFERENCES buildings(id),

  program_code TEXT NOT NULL,
  cycle_key TEXT NOT NULL,
  cycle_year INTEGER,

  window_start DATE,
  window_end DATE,
  deadline_source TEXT NOT NULL DEFAULT 'PROGRAM_SCHEDULE',
  deadline_source_version TEXT,

  -- LL152-style relative windows (policy parameters)
  report_to_owner_due_days INTEGER,
  owner_filing_due_days INTEGER,
  correction_cert_due_days INTEGER,
  final_correction_due_days INTEGER,

  -- Facts (user/portal)
  inspection_date DATE,
  report_delivered_at DATE,
  cert_filed_at DATE,
  correction_cert_filed_at DATE,
  final_correction_cert_filed_at DATE,

  conditions_requiring_correction BOOLEAN,
  additional_time_needed BOOLEAN,

  no_gas_piping_cert_filed_at DATE,
  no_gas_service_statement_filed_at DATE,

  extension_requested_at DATE,
  extension_granted_at DATE,
  extension_deadline DATE,
  extension_notes TEXT,

  status TEXT NOT NULL DEFAULT 'UNKNOWN',
  satisfaction_path TEXT,
  roster_status TEXT NOT NULL DEFAULT 'ACTIVE',

  created_from_source TEXT,
  created_from_version TEXT,
  last_imported_from_source TEXT,
  last_imported_from_version TEXT,
  last_imported_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_obligation UNIQUE (building_id, program_code, cycle_key)
);

CREATE INDEX idx_obligation_program_cycle ON compliance_obligations(program_code, cycle_key);
CREATE INDEX idx_obligation_status ON compliance_obligations(status);
CREATE INDEX idx_obligation_building ON compliance_obligations(building_id);

CREATE TABLE obligation_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obligation_id UUID NOT NULL REFERENCES compliance_obligations(id),
  event_type TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  import_run_id UUID,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 11) LL152 Program Binding (How LL152 uses this aggregate)

LL152 obligations are created/updated using:

* `program_code = 'LL152'`
* `cycle_key = <cycle-year>`
* `subcycle = <A|B|C|D>` stored in `ll152_obligation_details` extension table (accessed via JOIN)
* `window_start/window_end` from LL152 published schedule OR DOB property list per-building deadline
* Policy parameters:

  * `report_to_owner_due_days = 30`
  * `owner_filing_due_days = 60`
  * `correction_cert_due_days = 120`
  * `final_correction_due_days = 180`

> Important: This binding should be implemented in `LL152Program` (policy layer), not inside the generic aggregate.
