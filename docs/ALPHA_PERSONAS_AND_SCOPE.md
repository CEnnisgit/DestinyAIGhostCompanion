# Alpha Personas & Scope

> **Purpose:** This document defines who the product serves, what roles they play, and what "alpha" means for each real user. It exists to prevent LL152 tunnel vision — the product is a **plumbing company operations platform**, not an LL152-only tool.

---

## 1. What This Product Is

A software platform for small plumbing companies to manage their daily work: jobs, clients, buildings, inspections, and team coordination.

The product is **not** exclusively an LL152 inspection tool. LL152 is one workflow — the most complex one — but it sits alongside simpler job types (emergency calls, repairs, general plumbing work) that are equally important to real users.

---

## 2. Roles (Hats People Wear)

Real plumbers don't fit into one box. They wear multiple hats depending on the job. The system should recognize **roles**, not rigid personas.

### Field Technician
- Goes to the job site and does the work
- Needs: daily job list, navigation to address, on-site data capture, photo evidence
- May be the business owner or an employee

### Qualified Individual (QI)
- A specialized Field Technician role for LL152 inspections
- Performs gas piping inspections under an LMP's license
- Needs: GPS1 structured capture, findings checklist, handoff package to LMP
- This is a **subset** of Field Technician, not a separate persona

### Small Company Owner
- Runs the business — manages clients, tracks jobs, handles billing
- May also be in the field doing jobs (solo operator)
- Needs: client/building portfolio, job creation, job tracking, basic reporting

### Team Dispatcher
- Assigns jobs to 2-4 employees
- Tracks who is doing what and where
- Needs: job assignment, employee status visibility, schedule overview
- Often the same person as the Small Company Owner

### Licensed Master Plumber (LMP)
- Holds the plumbing license that authorizes the company's work
- For LL152: reviews QI inspection work, signs off on GPS1, handles GPS2/DOB filing
- May be office-based and supervisory, or may also do field work
- **Not an alpha user.** This role's review/certification workflow needs more research.

---

## 3. Alpha Users — Real People

### User A: Marcus's Father

**Hats he wears:**
- ✅ Small Company Owner — runs his own LLC
- ✅ Field Technician — does general plumbing work (emergency, repairs)
- ✅ Qualified Individual — performs LL152 inspections under an external LMP
- ❌ LMP — he works under someone else's license for LL152
- ❌ Team Dispatcher — solo operator

**His real workflow (LL152):**
1. Gets assigned a job from the LMP (address + contact info)
2. Drives to the building
3. Performs the gas piping inspection (walks the building, checks 5 categories)
4. **Pain point:** Struggles to produce the GPS1 report — currently done manually with help, then emailed to the LMP
5. Moves on to the next job. Everything after this is the LMP's problem.

**His real workflow (general plumbing):**
1. Gets a call from a client or referral
2. Schedules and drives to the job
3. Does the work
4. Invoices the client

**What he needs from alpha:**
- Create and track jobs (both LL152 and general)
- Manage his clients and buildings
- LL152: structured GPS1 capture that replaces the manual report process
- LL152: easy handoff to LMP (export/share the completed inspection package)
- Simple, mobile-friendly — he's not tech-savvy

---

### User B: Second Alpha Tester

**Hats he wears:**
- ✅ Small Company Owner — runs his own LLC
- ✅ Field Technician — does general plumbing work
- ✅ Team Dispatcher — sometimes sends out 2-4 employees on jobs
- ❌ QI — does not do LL152 inspections
- ❌ LMP — not a licensed master plumber

**His real workflow:**
1. Gets calls from clients for plumbing work
2. Either goes himself or dispatches an employee
3. Tracks what jobs are in progress, who's where
4. Follows up, invoices

**What he needs from alpha:**
- Create and track jobs (Emergency, Repair, general types)
- Manage his clients and buildings/addresses
- Assign jobs to employees (lightweight dispatch)
- See what's in progress across his small team
- Does **NOT** need LL152 workflow features

---

## 4. Feature-to-User Map

| Feature | User A (Father) | User B (Tester) | LMP (Future) |
|---|:---:|:---:|:---:|
| Job Engine (create, track, complete) | ✅ | ✅ | ✅ |
| Job Types: Emergency, Repair | ✅ | ✅ | ✅ |
| Client Portfolio (owners) | ✅ | ✅ | ✅ |
| Building/Address Management | ✅ | ✅ | ✅ |
| LL152 Workflow (GPS1 capture) | ✅ | ❌ | ✅ |
| LL152 Review (GPS2, certification) | ❌ (sends to LMP) | ❌ | ✅ |
| Job Assignment / Dispatch | ❌ (solo) | ✅ | ✅ |
| Team Visibility | ❌ (solo) | ✅ | ✅ |
| Compliance Filing (DOB) | ❌ | ❌ | ✅ |

---

## 5. What This Means for Alpha Scope

### The shared foundation (serves both users)
- Job Engine with multiple job types (LL152, Emergency, Repair)
- Client/owner portfolio
- Building/address tracking
- Job creation, status tracking, completion
- Mobile-friendly UI

### LL152-specific (serves User A only)
- Structured GPS1 data capture
- Five findings categories with observed/not-observed
- Inspection package export/handoff to LMP
- Workflow states: `DRAFT → CAPTURING → READY_FOR_REVIEW` (alpha endpoint)

### Dispatch/team features (serves User B only)
- Job assignment to employees
- Visibility into team workload
- **Scope TBD** — needs conversation with User B to understand exact pain points

### Not in alpha
- LMP review workflow (`UNDER_REVIEW` → certification states)
- GPS2 / DOB filing
- Anything after the QI hands off to the LMP

---

## 6. The Rule

> When designing or building a feature, always ask: **"Which user is this for?"**
>
> If the answer is only "the LMP," it's not an alpha feature.
> If the answer is "both users," it belongs in the shared foundation.
> If the answer is "User A only," it's LL152-specific work.
> If the answer is "User B only," it's dispatch/team work.

---

## 7. Relationship to Existing Docs

- **`PRD_LL152_PILOT.md`** — This is stale framing. The product is not an "LL152 Pilot." LL152 is one feature. The PRD should be updated or superseded by a broader product definition.
- **`PILOT_SCOPE_CONTEXT.md`** — The "zombie code" warnings are still valid, but the entity whitelist is too narrow. It was written assuming an LL152-only product.
- **Phase 2 specs** — These are correct for what they cover (LL152 workflow design), but they should be understood as one feature track, not "the next phase of the entire product."
- **ADR-0016 (Pluggable Workflows)** — This is the right architecture. The engine is generic; workflows are plugins. LL152 is the first complex plugin.

---

*Created: 2026-03-27*
*Status: Active — update as alpha testing reveals new insights*
