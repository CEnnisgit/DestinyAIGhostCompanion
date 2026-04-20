# LL152 Program Specification

**Module:** `CRM` (Compliance)
**Sub-Module:** `LL152`
**Aggregate:** `LL152Program`
**Related Aggregate:** `ComplianceObligation`
**Source of Truth:** `crates/pcd-domain/src/crm/compliance_obligation.rs` (engine) — LL152-specific logic not yet ported to Rust
**Version:** 2.0.0

---

## Objective

Define the **program-level truth** for Local Law 152 (Periodic Gas Piping System Inspections):

1. A **stable program identity** (`LL152`) and its policy boundaries.
2. A **schedule model** that can generate cycle/subcycle windows without guessing.
3. A **no-assumptions import contract** for DOB program datasets.
4. A clean separation:

   * `LL152Program` = **policy + schedule + import contract**
   * `ComplianceObligation` = **per-building obligations and status**

---

## 1) Program Identity

### 1.1 Program Code

* `programCode = "LL152"`

### 1.2 What the Program governs

* Periodic inspection requirements for building gas piping systems.
* Submission / filing timing rules.
* Cycle/subcycle schedule definition.

### 1.3 What the Program does NOT govern

* A building's canonical `BIN`, `Address`, `CommunityDistrict`, or `BBL` (those live in `Building` and are governed by Building authorities).
* Per-building compliance state (those live in `ComplianceObligation`).

---

## 2) Authorities (No-Assumptions)

Every rule below must cite a real authority outside of our system.

### 2.1 Primary Policy Authority

* **DOB Rule:** `1 RCNY §103-10` (Periodic Inspection of Gas Piping Systems).

### 2.2 Secondary Operational Guidance

* DOB public guidance pages (used for UX language and to confirm how DOB operationalizes the rule).

### 2.3 Dataset Authority for "Which properties"

* **DOB-maintained property list / roster** (the DOB-published list of properties to which LL152 applies and deadlines for each).

> System rule: We do **not** infer LL152 applicability solely from internal building attributes unless we can trace the inference to DOB-provided, published rules and we have the required authoritative data fields.

---

## 3) Core Concepts

### 3.1 Inspection Cycle vs Subcycle

* **Subcycle** partitions buildings by **Community District number** (1–18) (applies across boroughs).
* **Cycle** is the 4-year repeating cadence.

### 3.2 Inspection Window vs Filing Windows

* **Inspection Window:** the date range during which the inspection must occur for the cycle.
* **Filing windows:** relative to the inspection date (30/60/120/180 days) for delivering reports and filing certifications.

### 3.3 Community District number

* In this program spec, "Community District" means the **district number** (1–18).
* A building's canonical Community District is stored on `Building` (authority = Geoclient verification pipeline).

---

## 4) Program Schedule (Subcycles)

### 4.1 LL152Subcycle (Value Object)

**Values:** `A`, `B`, `C`, `D`.

### 4.2 Subcycle → Community District set

* `A` → `{1, 3, 10}`
* `B` → `{2, 5, 7, 13, 18}`
* `C` → `{4, 6, 8, 9, 16}`
* `D` → `{11, 12, 14, 15, 17}`

### 4.3 Cycle windows

The rule defines:

* inspections occur **at least once every four years**
* for the specified Community District groups.

We model the schedule as an explicit set of windows, sourced from DOB.

#### Known windows (explicitly published)

| Subcycle | Cycle 1 window          | Cycle 2 window          | Cycle 3 window          |
| -------- | ----------------------- | ----------------------- | ----------------------- |
| A        | 2020-01-01 → 2021-06-30 | 2024-01-01 → 2024-12-31 | 2028-01-01 → 2028-12-31 |
| B        | 2021-01-01 → 2022-06-30 | 2025-01-01 → 2025-12-31 | 2029-01-01 → 2029-12-31 |
| C        | 2022-01-01 → 2022-12-31 | 2026-01-01 → 2026-12-31 | 2030-01-01 → 2030-12-31 |
| D        | 2023-01-01 → 2023-12-31 | 2027-01-01 → 2027-12-31 | 2031-01-01 → 2031-12-31 |

#### Repeat rule (program logic)

After a subcycle's cycle year `Y`, subsequent cycles repeat every 4 calendar years.

> Implementation note: if DOB publishes a new schedule table or amends cycle windows by rule, we update this program schedule via `LL152ProgramPolicyUpdated`.

---

## 5) Who Must Comply (Policy Statements)

### 5.1 General scope

* Applies to gas piping systems in all buildings **except** buildings classified in occupancy group `R-3`.

### 5.2 Buildings with NO gas piping

* Periodic inspections do not apply if the owner submits a certification that the building contains **no gas piping system**.
* Such statement is submitted **once** (unless gas piping is later installed).

### 5.3 Buildings with gas piping but NO gas service / no connected appliances

* The rule provides a separate statement pathway where certain buildings are not required to undergo the periodic inspection while they remain without gas service and without appliances connected to gas piping.

### 5.4 New buildings

* The rule defines a special schedule for "new buildings" (certificate of occupancy issued on or after a specific date), where the initial inspection is performed during the tenth year after the certificate of occupancy.

> System decision: unless we have an authoritative Certificate of Occupancy issuance date available in our Building model, we do **not** compute the "new building tenth-year" schedule in-app; we rely on DOB's published property list / roster for the deadline.

---

## 6) Filing & Timing Rules (Policy)

### 6.1 Pre-inspection notice

* The qualified inspection entity must notify DOB of an inspection in the manner DOB specifies at least **two (2) days prior** to the inspection.

### 6.2 30-day delivery to owner

* The inspection entity must provide the building owner:

  * an inspection report, and
  * a certification of inspection
    **no later than 30 days** following the inspection date.

### 6.3 60-day filing to DOB

* The building owner must submit the certification of inspection to DOB **no later than 60 days** following the inspection date.
* Filing more than 60 days after the inspection date does **not** satisfy the requirement and triggers "new inspection required."

### 6.4 120-day correction certification

* If the initial certification indicates conditions requiring correction, the building owner must submit a licensed-master-plumber certification that corrections were made **no later than 120 days** after the inspection date.

### 6.5 180-day correction certification

* If additional time is indicated, the building owner must submit a final correction certification **no later than 180 days** after the inspection date.

### 6.6 Record retention

* Owner and inspection entity must retain required reports and certifications for **10 years** following the inspection date.

### 6.7 One-time 180-day extension (inspection deadline)

* DOB allows an owner who cannot obtain inspection by the cycle deadline to request a **one-time 180-day extension** per cycle, through DOB's mechanism.

---

## 7) Penalties (Policy)

The rule defines civil penalties for failure to file required certifications by the due date.

* `$1,500` for a **3-family building**
* `$5,000` for **all other buildings**

> System note: we store penalties only as static reference text for UX; enforcement is handled by DOB.

---

## 8) Program Dataset Import Contract

### 8.1 Purpose of the roster/property list import

We import DOB's published property list to:

* establish "in-program" membership (which properties DOB expects filings from),
* create/update `ComplianceObligation` records,
* attach DOB-provided deadlines when present.

### 8.2 Required keys (minimum viable import)

A roster row is importable only if it provides:

* `BIN`
* a deadline date OR sufficient information to derive a deadline (e.g., subcycle + cycle year)

Rows missing the required key(s) are quarantined.

### 8.3 Roster versioning

Every import run captures:

* `sourcePublishedUpdatedAt` (if provided by DOB)
* `downloadedAt`
* `sourceUrl`
* `fileHash`

### 8.4 Authority-per-field for roster-derived properties

* **Program schedule (subcycle sets + repeating cadence):** policy authority (`1 RCNY §103-10` and/or DOB published schedule table)
* **Property membership list:** DOB roster/property list
* **Per-property deadline values in roster:** treated as DOB-provided data; if a deadline conflicts with the program schedule derived from policy + building community district, log an anomaly and store both values (canonical remains schedule-derived unless DOB explicitly amended the schedule).

---

## 9) Program Behaviors (Aggregate API)

### 9.1 Commands

* `LL152Program.updatePolicy({ policyVersion, scheduleWindows, notes })`
* `LL152Program.registerRosterImport({ rosterVersion, sourceUrl, fileHash, downloadedAt })`

### 9.2 Events

* `LL152ProgramPolicyUpdated`
* `LL152RosterImported`

### 9.3 Invariants

* Subcycle must be one of `A/B/C/D`.
* Each schedule window must have:

  * `startDate <= endDate`
  * non-overlapping windows within the same subcycle for the same cycle number.
* If a policy update changes a window affecting a future deadline, downstream obligations must be recomputed via a migration or a batch reconciliation job.

---

## 10) Test Vectors

### 10.1 Deriving subcycle from CD

* Input: `communityDistrictNumber = 10` → `subcycle = A`
* Input: `communityDistrictNumber = 16` → `subcycle = C`

### 10.2 Cycle 2 deadline examples

* Subcycle `A` cycle 2 window ends `2024-12-31`.
* Subcycle `C` cycle 2 window ends `2026-12-31`.

### 10.3 Filing deadline examples (relative)

* Inspection date `2026-03-01`:

  * Owner filing due date = `2026-04-30` (60 days)
  * Correction cert due date (if required) = `2026-06-29` (120 days)
  * Final correction due date (if extra time) = `2026-08-28` (180 days)

> Date arithmetic is performed by the application layer using a timezone-safe date library; the program spec defines only the offsets and rules.
