# UX Research Notes

> **Context:** Pre-prototype research conducted via external UX review
> **Prototype:** `prototype-v1` on branch `prototype/web-dashboard`

## Research Methodology

An external UX reviewer analyzed the prototype context and a UX brief covering all 4 rails (Dashboard, Jobs, Buildings, Settings). The reviewer compared against competitor tools (Jobber, Housecall Pro, ServiceTitan, SafetyCulture) and NYC LL152 regulatory requirements.

## Key Findings

### 1. Buildings Must Be First-Class Objects

> *"Your prototype is already pointed in the right direction — it treats Buildings as a first-class object. That is smarter than most generic field-service tools, which usually lead with customers/jobs first."*

- LL152 compliance is **building-centric**, not customer-centric
- Building = the canonical compliance container (cycle, obligation, filings)
- Competitors treat properties as secondary records — PCD should not

**Prototype response:** Building Profile page with compliance status, filing chain tracker, and job history.

---

### 2. Solo vs. Firm Is a Real Wedge

> *"Separating solo from firm contexts is smarter than most competitors."*

- Solo plumber cares about: *What do I do today? What paperwork is due?*
- Firm owner cares about: *Who's idle? What needs dispatch? What deadlines are approaching?*
- These are fundamentally different operational modes, not just feature flags

**Prototype response:** Solo "My Day" vs Firm "Ops Console" on Dashboard; conditional team UI across all rails.

---

### 3. Dashboard Should Be Action-Oriented, Not Generic Admin

> *"The prototype currently behaves like a generic admin dashboard more than a morning operations console."*

Original prototype had passive metric cards. Research said:
- Lead with **what needs attention today**
- Surface **who is idle** (firm) or **what's your next stop** (solo)
- Make deadlines and filing gaps **immediately visible**

**Prototype response:** My Day queue with next-stop hero, dispatch queue with "Assign" buttons.

---

### 4. Compliance Chain Must Be Visualized

> *"LL152 has a strict filing sequence. Visualizing this reduces compliance errors."*

The filing chain: `Inspection → GPS1 (owner report) → GPS2 (DOB filing) → Compliant/Correction`

- Users need to see where each job AND building stands in this chain
- Corrections add a branch (120-day window)
- Current status should be visible in list views AND detail pages

**Prototype response:** Horizontal step tracker on both JobDetail and BuildingProfile pages.

---

### 5. Settings Needs Compliance Config

> *"Settings is far too thin for a compliance product."*

Original had only mode toggle and company info. Research identified:
- Signatory / seal / stamp details (required on GPS forms)
- Form template defaults
- Filing borough defaults
- Notification granularity (per-category × per-channel)
- Import center for DOB roster management

**Prototype response:** 4-tab admin area: Organization (with compliance config), Team & Permissions, Notifications, Data & Integrations.

---

### 6. Prospect Mode for DOB Roster

DOB publishes rosters of buildings with LL152 obligations. Firms import these as **prospects** — buildings they haven't been hired for yet but could outreach to.

Key UX need: prospects must be **visually distinct** from active clients (dimmed, badged, filterable) to avoid confusion.

**Prototype response:** `isProspect` flag on MockBuilding, dimmed table rows, "Prospect" badge, Client Type filter in drawer.

---

## Competitor Landscape

| Tool | Strengths (relevant to PCD) | Weaknesses |
|---|---|---|
| **Jobber** | Clean scheduling, role-based access | No compliance tracking, property is secondary |
| **Housecall Pro** | Dispatch board, customer-centric | No LL152 awareness, no building profiles |
| **ServiceTitan** | Enterprise-grade, field-tech separation | Overbuilt for solo plumber, expensive |
| **SafetyCulture (iAuditor)** | Inspection checklists, template library | Not field-service, no job lifecycle |

**PCD's wedge:** None of these tools treat buildings as compliance containers or understand the GPS1/GPS2 filing chain. PCD is purpose-built for LL152.

---

## What Prototype V1 Does NOT Include (Deferred)

| Feature | Why Deferred |
|---|---|
| Calendar / map views | Complex, validates after core list/detail patterns |
| GPS1/GPS2 form generation | Requires backend, separate workstream |
| Notifications delivery | Only preference UI is needed for prototype |
| Mobile / responsive | Field-tech UX is a separate product concern |
| Client / contact management | Building-first approach means clients come after |
| Real-time updates | Requires websockets/SSE, not needed for UX validation |

---

## Sources

- External UX review (March 2026)
- [NYC LL152 Regulatory Reference](https://www.nyc.gov/site/buildings/safety/gas-piping-periodic-inspection.page)
- Competitor product trials and documentation
- ADR-0017: Solo/Firm modal split
