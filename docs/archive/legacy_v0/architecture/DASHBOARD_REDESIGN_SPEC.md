# Company Dashboard Redesign Specification (v1.0)

**Product surface:** Company Admin Dashboard (web) — *not* the technician field app. The dashboard manages jobs + technicians, and surfaces inspection/report outcomes at an operational level. 

## 0) Executive summary

This redesign turns the dashboard into an **operational command center** first (what needs action now), and a **scoreboard** second (performance insights). It also removes internal identifiers (like `building_id` UUIDs) from end-user workflows: UUIDs remain internal primary keys, not user input.  

Key outcomes:

* A new **Command Center** landing experience that prioritizes exceptions and "needs action".
* A **Jobs experience** that is status-driven, fast to triage, and supports repeat buildings.
* A clear lifecycle where **"Completed" means report delivered via email** (MVP delivery channel).
* A structured **report readiness + delivery** model (eliminates "inspection completed but report missing" ambiguity).
* A correction loop that preserves compliance integrity while enabling technicians to amend when needed.

---

## 1) Scope and constraints

### In scope

* Company Admin Dashboard IA + UX redesign (Home/Command Center, Jobs, Job Detail, Buildings, Technicians, Settings).
* Job creation flow redesign (remove Building UUID entry requirement).
* Job lifecycle/state machine and related data requirements.
* Report readiness + delivery tracking (email-only in MVP).
* Exception handling: no-show, report missing, data incorrect.

### Out of scope

* Technician field UX (separate mobile app) beyond the minimum hooks needed for status correctness. 
* Owner portal UX (separate surface). 

---

## 2) Design principles (explicit)

1. **Operational calm**: fewer "dashboardy" widgets; more clarity, fewer decisions per screen.
2. **Command Center first, Scoreboard second**: landing experience prioritizes items requiring action.
3. **Status is operational truth**: status names must map to real-world "done-ness", especially around report delivery.
4. **No internal IDs in UX**: UUIDs are internal keys (`<entity>_id`), never user-facing inputs. 
5. **Exceptions are first-class**: no-show, report missing, and data disputes appear as actionable queue items.

---

## 3) Actors and permissions (dashboard)

Primary dashboard user: **Company Admin** (company owner/dispatcher persona).

* Company Admin can manage jobs for their company and technicians in their company. 
* Buildings should be accessible to Company Admin **indirectly via jobs** (tenant isolation). 
* Technician permissions remain scoped to their assigned jobs (mobile app). 

---

## 4) Proposed information architecture (new)

Current IA is essentially Home → Jobs → Technicians → Settings. 
Proposed IA emphasizes operations:

### Left nav (primary)

* **Command Center** (default landing)
* **Jobs**
* **Buildings**
* **Technicians**
* **Reports** (optional shortcut; can be folded into Jobs in MVP)
* **Settings**

### Global "Create" entry point

Top-right **New…** button:

* Create Job
* Add Building
* Add Technician

Rationale: you noted "Create Job" should have options; the "New…" menu standardizes this without cluttering every page.

---

## 5) Core entities and relationship anchors (as implemented)

We keep the same core domain objects: **Building**, **InspectionJob**, **InspectionForm**, **InspectionReport**. 

* `inspection_jobs` links company, technician, building, optional service_request. 
* `inspection_reports` are **derived artifacts**, stored as versioned outputs.  

---

## 6) Job lifecycle redesign

Your current diagrams show a basic flow ending in Completed. 
Your operational requirement changes the meaning of "Completed": **inspection is not operationally complete until the report email is sent**.

### 6.1 Canonical JobStatus (Option A + operational completion)

We will implement **Option A** with a key addition:

* `PENDING_ASSIGNMENT` (optional, but already in schema) 
* `SCHEDULED`
* `IN_PROGRESS`
* `REPORT_READY` *(new)*
* `COMPLETED` *(definition changed: report delivered)*
* `CANCELLED`

This aligns with the existing schema foundation (job_status enum) while adding "REPORT_READY" as the missing operational step. 

### 6.2 Formal definitions (operational)

* **IN_PROGRESS**: technician has started the inspection form (form status `IN_PROGRESS`). 
* **REPORT_READY**: form submitted + report generated and stored (report exists). (Currently report generation happens after submission in the UML flow.) 
* **COMPLETED**: report email has been sent (delivery recorded).

### 6.3 Exceptions (not statuses)

To preserve calm, exceptions become **queue flags**, not new statuses:

* Technician no-show / overdue
* Report missing (expected artifact absent)
* Report flagged as wrong (correction requested)

---

## 7) Command Center (new default Home)

### Purpose

A single place to answer: **"What needs my attention today?"**
Secondarily: "How are we performing?"

### 7.1 Layout

**A) Attention Queue (top, dominant)**
Cards grouped by category:

1. **No-show / overdue**
   Trigger: `job.status = SCHEDULED` and `scheduled_end < now` and no form started.
2. **Report missing / stuck**
   Trigger: form submitted but report record not created (or generation failed). (This addresses the "inspection completed but report missing" issue.)
3. **Report ready to send**
   Trigger: `job.status = REPORT_READY` AND `report.sent_at IS NULL`
4. **Report flagged (data wrong)**
   Trigger: open flag/correction request exists.

Each card includes:

* Building address (primary identifier)
* Technician (if assigned)
* Scheduled window (if applicable)
* Age (how long in this state)
* Primary CTA (Resolve / Send / Request correction / Reschedule)

**B) Today / Upcoming (secondary)**
A compact list of today's scheduled jobs (filter by date).

**C) Scoreboard (tertiary)**
A small set of KPIs:

* Jobs scheduled this week
* Jobs completed this week (Completed = report delivered)
* Median "booking → completed" (PRD metric) 
* Median "inspection submitted → report sent" (new)

---

## 8) Jobs page redesign

### 8.1 Jobs List: structure

* **Status tabs**: Scheduled, In Progress, Report Ready, Completed, Cancelled (+ optional Pending Assignment)
* **Search**: address / borough / zipcode / technician name
* **Filters** (collapsible):

  * Date range
  * Technician
  * Borough/Zip
  * "Has open issues" toggle (maps to exceptions)
* **Table columns** (recommended):

  * Status
  * Scheduled window
  * Building (address line)
  * Technician
  * Report state (Ready / Sent / Flagged)
  * Last updated
  * Actions (contextual)

This supports the PRD expectation that a job list shows address, time window, and status. 

### 8.2 Fast-path actions (row-level)

* Scheduled: Reschedule, Reassign, Cancel
* In Progress: View details
* Report Ready: **Send report**
* Completed: View report (and delivery record)
* Any: Add internal note (optional MVP)

---

## 9) Buildings (new first-class module)

### Why this exists

You called out "Repeat building" as a key creation path. A Buildings module turns repeat work into a one-click job.

### 9.1 Buildings list

Shows buildings relevant to the company **via job history** (RBAC-safe). 
Columns:

* Address
* Borough/Zip
* Last job date
* Next scheduled job (if any)
* "Create job" button

### 9.2 Building detail

* Address + map pin (optional)
* Job history table
* "Create job for this building"
* Owner contact (see data model note below)

---

## 10) Create Job flow (fixing the UUID issue)

### Problem

The current UI requires a "building UUID" to create a job. That's an internal key and violates the naming/DB conventions being used (UUID PKs are internal).  

### New Create Job wizard (2–3 steps)

**Step 1 — Choose building**

* Search by address (typeahead)
* If not found: "Add new building" inline (address + borough + zipcode; optionally lat/lng if using geocoding)

**Step 2 — Schedule & assign**

* Technician (optional)
* Scheduled window: start + end (defaults from Settings; see ADR-006)
* Notes for technician (optional)

**Step 3 — Confirm**

* Summary view
* Create Job

**Important:** Building UUID is never shown; the API simply receives `building_id` behind the scenes.

---

## 11) Job Detail page (operational single source of truth)

### Sections

1. **Header**: Address + status pill + primary CTA based on status
2. **Timeline**: Created → scheduled → started → submitted → report generated → report sent
3. **Assignment**: technician, scheduled window, reschedule/reassign controls
4. **Inspection**: form state, last edit, link to view (read-only for admin)
5. **Report**: latest report version + send status + audit info (sent_at, recipient)

### Contextual CTAs

* REPORT_READY: **Send report** (primary)
* SCHEDULED: Reschedule / Reassign
* IN_PROGRESS: View inspection progress
* COMPLETED: View report + delivery record
* Flagged: Request correction

---

## 12) Report delivery + "Completed" definition

PRD states delivery is email-based and reports are stored in the dashboard. 
UML currently indicates job becomes COMPLETED at form submission, and notifications send immediately. 

### Updated operational contract

* Form submission triggers report generation (same).
* **Job moves to REPORT_READY when the report exists.**
* **Job moves to COMPLETED only when email is sent and recorded.**

This resolves your requirement: "inspection can't be done without a delivered report."

---

## 13) "Data is wrong" correction workflow (MVP-safe)

### Roles (per your current intent)

* Only **Company Admin** can initiate a correction request.
* Technician can amend the inspection via their UI when a correction is requested.

### Proposed mechanism

* Company Admin flags a report (reason + notes).
* System opens a **Correction Request** tied to the underlying form/report.
* Technician edits the form, re-submits.
* System generates **InspectionReport version+1** (reports are versioned artifacts already).  
* Company Admin re-sends email, then marks Completed.

**Note:** This intentionally reconciles the PRD's "locks job from further edits" by making edits possible only when a correction request is open. 

---

## 14) Data + API requirements

### 14.1 Jobs list API shape (BFF-friendly)

Existing visuals show `GET /api/v1/jobs`. 
Naming conventions also support `/api/v1/inspection-jobs`. 
Either is fine; pick one canonical route and alias the other.

**Jobs list response MUST include denormalized display fields:**

* `job_id`, `status`
* `scheduled_start`, `scheduled_end` (or computed window)
* `building: { building_id, address_line1, borough, zipcode }`
* `technician: { technician_id, display_name } | null`
* `report: { latest_report_id, version, created_at, sent_at, flagged_open:boolean } | null`
* `attention_flags: string[]` (computed server-side preferred)

### 14.2 Command Center API

`GET /api/v1/command-center`

* Returns grouped queues with counts + top N items per group
* Returns KPI snapshot

---

## 15) Database changes (delta from current first-pass schema)

Current schema baseline:

* `inspection_jobs` includes `scheduled_at` and `status` enum. 
* `inspection_reports` includes `version` but no delivery metadata. 

### 15.1 Required changes

1. **Extend job_status enum**

* Add `REPORT_READY` to `job_status`.

2. **Scheduling window**

* Add:

  * `scheduled_start TIMESTAMPTZ`
  * `scheduled_end TIMESTAMPTZ`
* Keep `scheduled_at` only if needed for backward compatibility; otherwise migrate.

(Justification: service requests already model a window with start/end, and the PRD expects a time window concept.  )

3. **Report delivery tracking (email-only MVP)**
   Add to `inspection_reports`:

* `sent_at TIMESTAMPTZ NULL`
* `sent_to_email CITEXT NULL` (or TEXT)
* `sent_by_user_id UUID NULL REFERENCES users(user_id)`
* `delivery_channel TEXT NOT NULL DEFAULT 'EMAIL'`

4. **Report flags / correction requests**
   Minimum viable approach:

* `inspection_report_flags` table:

  * `flag_id UUID PK`
  * `report_id UUID FK`
  * `flagged_by_user_id UUID FK`
  * `reason_code TEXT` (e.g., WRONG_DATA, MISSING_FIELD)
  * `notes TEXT`
  * `created_at TIMESTAMPTZ`
  * `resolved_at TIMESTAMPTZ NULL`

Optionally add `inspection_corrections` if you want a more explicit workflow object.

### 15.2 Computed operational states (server-side)

* "No-show" is computed from scheduled_end and form state.
* "Report missing" is computed from form submitted but no report row.
* "Report ready to send" is computed from REPORT_READY + sent_at null.

---

## 16) RBAC / security implications

* Buildings page must enforce "indirect building access via company jobs" to avoid cross-tenant leaks. 
* Company Admin can create jobs and manage technicians within company scope. 
* Technicians can only edit forms for their assigned jobs (mobile side). 

Add audit logging for:

* Job status transitions
* Report generation
* Report sent event
* Report flagged event
  (RBAC doc already recommends auditing for these actions.) 

---

## 17) Migration and rollout plan (pragmatic)

1. Add new columns/tables (non-breaking):

   * `REPORT_READY` enum value
   * scheduled window columns
   * report delivery fields
   * report flags table
2. Update backend transitions:

   * form submission → job becomes REPORT_READY (not COMPLETED)
   * email send action → set report.sent_at and job becomes COMPLETED
3. Ship UI in phases:

   * Phase A: Jobs page redesign + Create Job wizard (no UUID)
   * Phase B: Command Center landing
   * Phase C: Buildings module

---

## 18) Acceptance criteria (what "done" means for this redesign)

* Users can create a job **without ever seeing or entering a Building UUID**.
* Dashboard landing page shows an **Attention Queue** with actionable items.
* "Inspection completed but report missing" is detectable and visible as a queue item.
* A job cannot be marked **COMPLETED** until the report email is sent (delivery recorded).
* Company Admin can flag "data wrong" and trigger a correction loop that results in a new report version.

---

# ADRs (Architecture / Product Decision Records)

## ADR-001 — UUIDs are internal only; never user-entered

**Context:** DB uses UUID primary keys; UI currently requires a building UUID. 
**Decision:** Remove UUID inputs from UX. Building selection is address search; backend uses `building_id`.
**Consequences:** Requires typeahead building search endpoint and/or building creation inline.

## ADR-002 — Default landing is Command Center, not dashboard stats

**Context:** You want "operational calm" and "command center first."
**Decision:** Make Command Center the default route; performance metrics move below attention and/or into a secondary section.
**Consequences:** Requires server-side aggregation endpoint for queue + KPIs.

## ADR-003 — Introduce `REPORT_READY`; redefine `COMPLETED`

**Context:** Current model jumps to COMPLETED at submission in UML; you require completion only after report delivered. 
**Decision:** Add `REPORT_READY` status; `COMPLETED` means "report email sent and recorded."
**Consequences:** Update job transitions and UI tabs; add "Send report" primary action.

## ADR-004 — Report delivery channel is email-only in MVP, but delivery is auditable

**Context:** PRD specifies delivery via email and storage in dashboard. 
**Decision:** Add `sent_at`, `sent_to_email`, `sent_by_user_id`, `delivery_channel='EMAIL'` fields on reports.
**Consequences:** Enables operational truth and debuggability; unlocks future channels without redesign.

## ADR-005 — Corrections create new report versions; edits after submit only when correction is open

**Context:** Reports are versioned artifacts; PRD says submission locks edits, but MVP needs "data wrong" correction.  
**Decision:** Allow technician edits only under an active correction request; regenerate report with version increment.
**Consequences:** Requires report flag/correction tracking and clear audit trail.

## ADR-006 — Scheduling is a window (start/end), default configurable

**Context:** No-show detection requires a window; service requests already express start/end. 
**Decision:** Store `scheduled_start` and `scheduled_end`; default window length set in Settings (e.g., 2 hours by default).
**Consequences:** Improves no-show automation and aligns UI with "time window" expectations.
