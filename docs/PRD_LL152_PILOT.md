> [!WARNING]
> **HISTORICAL DOCUMENT — Partially Superseded (2026-03-27)**
>
> This PRD was written when the product was conceived as an LL152-only tool with two rigid lanes (Plumber + LMP). The product scope has since broadened to a **plumbing company operations platform** serving multiple roles and job types.
>
> **What's still valid:** The LL152 domain knowledge, GPS1/GPS2 artifact descriptions, deadline rules, and field discovery questions remain valuable references.
>
> **What's outdated:** The "two lanes" framing, the assumption that the product is LL152-only, and the LMP as a launch user. See [ALPHA_PERSONAS_AND_SCOPE.md](ALPHA_PERSONAS_AND_SCOPE.md) for the current user model and scope.

# LL152 Plumber + LMP SaaS Pilot Plan (Point 0 → First Iteration)

**Primary workflow for MVP:** NYC **Local Law 152** (Periodic Gas Piping System Inspection) — end-to-end handling of an **LL152 Inspection Job**.

**Two primary users at launch:**

1. **Plumber (field tech)** — receives an LL152 job, performs the on-site inspection, captures findings, and submits them.
2. **LMP (Licensed Master Plumber / partner)** — receives the job from the owner/manager, dispatches the plumber, reviews findings, signs/seals the certification deliverables, and coordinates owner-facing compliance delivery.

**Your two early scopes (as product “lanes”):**

* **Lane A (Plumber):** Complete the LL152 inspection capture and produce GPS1-ready findings.
* **Lane B (LMP):** Dispatch plumber + review/sign/seal + produce owner packet (GPS1/GPS2) and track deadlines.

---

## Local Law 152 deliverables and deadlines (design anchors)

Use these deadlines to drive product behavior (reminders, due dates, status gates):

* **GPS1 report due to owner:** within **30 days** of inspection.
* **GPS2 certification due to DOB (owner filing):** within **60 days** of inspection.
* If corrections required: follow-up certifications within **120 days** (or **180 days** if additional time is needed).
* Inspections occur on a **4-year** schedule based on **Community District** (sub-cycles A–D).

---

## Point 0 — Pilot Charter (1 page)

**Objective:** define success for the first real LL152 job flow and prevent scope creep.

### 0.1 Product promise (commitment)

* **For plumbers:** “Capture LL152 findings fast in the field with zero missed items.”
* **For LMPs:** “Dispatch, review, and produce a GPS1/GPS2-ready packet with deadline tracking.”

### 0.2 Non-negotiables

* Phone-first for the plumber; minimal typing.
* **Time-to-value < 2 minutes** for the plumber’s core capture action.
* Handoff reliability: LMP must get a complete, reviewable packet every time.
* Stable recordkeeping (owner needs records for years; your system must make export/archival easy).

### 0.3 v0 success criteria (pilot)

* Your father uses it on **real LL152 jobs** for **7 days**.
* At least **N** LL152 jobs processed (choose N based on weekly volume).
* At least **70%** of jobs complete the plumber → LMP handoff without missing required info.
* LMP can produce a **GPS1/GPS2-ready packet** without retyping everything.

### 0.4 Kill / reset criteria

* If it is slower than the existing process after **7–14 days**, stop adding features and redesign the **core capture + review** flow.

**Deliverable:** this section printed as the “pilot charter.”

---

## Phase 1 — Field discovery (LL152-specific) (2–4 hours total)

**Objective:** map the exact LL152 work, identify “must-capture” fields, and formalize the handoff contract.

### 1.1 Collect the ground truth artifacts

* Latest **GPS1** and **GPS2** forms used in practice.
* Examples of your father’s past LL152 jobs (one “clean,” one “messy”).
* LMP’s current dispatch format (text, call, spreadsheet, notes).

### 1.2 Run an end-to-end replay with both users

Walk one job from intake → dispatch → inspection → review → packet delivery.
Capture:

* What the LMP gets from the owner/manager (address, building details, deadline, access).
* What the plumber must know before arriving (keys, super contact, meter room location, gas rooms).
* What must be captured on-site (categories, conditions, photos, notes, access limitations).
* What the LMP needs to confidently sign/seal.

### 1.3 Produce the “LL152 Job Packet Spec”

A one-page checklist of:

* Required job header fields (address, BIN/block/lot if used, community district, owner contact, access notes).
* Required inspection capture fields (mapped to GPS1 sections).
* Required attachments (photos, notes, meter room/boiler room, etc. as your practice dictates).
* “Stop-the-line” conditions: what triggers immediate escalation to LMP/utility/DOB per your practice.

**Deliverable:** LL152 Job Packet Spec (this becomes your data model and validation rules).

---

## Phase 2 — Define your core object model + job states (60 minutes)

**Objective:** make LL152 a single, trackable object with clean handoffs.

### 2.1 Core objects (MVP)

* **LL152 Inspection Job** (primary)
* **Building/Address profile** (lightweight)
* **Inspection Findings** (structured to GPS1)
* **Attachments** (photos/notes)

### 2.2 Status states (enforceable)

1. **Intake (LMP)**
2. **Dispatched (Plumber assigned)**
3. **In Progress (Field)**
4. **Submitted to LMP (Needs Review)**
5. **Returned for Fixes** (optional)
6. **Finalized (GPS1/GPS2-ready)**
7. **Delivered to Owner**

### 2.3 Due dates the app must compute

* Inspection date drives GPS1/GPS2 clocks.
* Sub-cycle label (A/B/C/D) and the building’s compliance year window.

**Deliverables:** state machine + required fields per state + due-date rules.

---

## Phase 3 — Prototype UX (two lanes) before code (same day)

**Objective:** validate speed and clarity before building.

### 3.1 Plumber lane (phone-first)

Minimum screens:

* Assigned jobs list
* Job detail (access notes, contacts)
* Guided inspection capture (GPS1-structured)
* Submit to LMP (locks packet and notifies)

**2-minute test:** start from Assigned Jobs → complete a realistic capture → Submit.

### 3.2 LMP lane (review/sign/packet)

Minimum screens:

* Job intake
* Dispatch (assign plumber, set deadline)
* Review findings (check completeness, add edits)
* Generate/export packet (GPS1 + GPS2 drafts)
* Status + deadline tracker

**Deliverable:** annotated mock + list of changes to remove friction.

---

## Phase 4 — v0 scope (strict) + manualize everything else (1 hour)

**Objective:** ship an end-to-end LL152 flow, not a general plumbing platform.

### 4.1 v0 must-haves (LL152 only)

1. LMP creates LL152 job (intake) and dispatches plumber
2. Plumber completes guided on-site capture + photos/notes
3. Submit-to-LMP handoff with completeness checks
4. LMP review/approve (with “return for fixes”)
5. Generate/export GPS1/GPS2-ready packet (draft PDFs or structured export)
6. Deadline tracker (30/60/120/180-day logic) + reminders
7. Search/history by address/building

### 4.2 Not now (explicit)

* General plumbing job management beyond LL152
* Billing/subscriptions
* Inventory
* Deep accounting integrations
* Multi-company admin complexity
* Automated DOB portal submission

### 4.3 Manualize during pilot

* Onboarding/setup
* Template text setup (company info, signature blocks)
* Data correction, edge cases
* Support and troubleshooting

**Deliverables:** v0 scope + “not now” + manual plan.

---

## Phase 5 — Build v0 for pilot speed (implementation)

**Objective:** ship quickly with minimum analytics.

### 5.1 Build for iteration speed

Pick stack based on your strengths. Optimize for:

* quick UI iteration
* simple data model
* easy deployment

### 5.2 Minimum instrumentation

Track:

* Job created (LMP)
* Job dispatched
* Capture started (plumber)
* Capture submitted (handoff)
* LMP finalized
* Packet exported

**Deliverable:** v0 shipped with basic event logging.

---

## Phase 6 — Pilot with father + LMP (Week 1)

**Objective:** validate real-world completion and handoff quality.

### 6.1 Onboarding (15–30 minutes)

* Create 1–2 real jobs together.
* Confirm required fields and what counts as “complete.”
* Agree on photo/notes standards.

### 6.2 Daily 10-minute feedback loop

Ask both:

* Which jobs did you run through the app?
* Where did it slow you down?
* What did you do instead?
* What info was missing at handoff?

### 6.3 Observe one real session

If possible, watch a real capture and a real review.

**Deliverables:** daily notes + funnel counts + “returned for fixes” reasons.

---

## Phase 7 — First iteration (end of Week 1 or after ~5–10 jobs)

**Objective:** reduce handoff rework and reduce time-to-capture.

### 7.1 Triage into 3 buckets

1. **Blockers** (prevents completion)
2. **Friction reducers** (faster capture/review)
3. **Nice-to-have** (defer)

### 7.2 Ship v0.2 with one measurable goal

Examples:

* Reduce time-to-submit from 3:00 → 1:30
* Reduce “returned for fixes” from 40% → 10%

### 7.3 Expand only after stability

After father + LMP run this reliably, add **2–3 plumber friends** as friendly pilots.

---

## Operating principle (keep visible)

**Until LL152 is a reliable production line:**

* Optimize for **speed**, **completeness checks**, and **clean plumber → LMP handoff**.
* Do not expand scope beyond LL152.
