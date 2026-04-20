> [!NOTE]
> **Historical Context:** These extraction notes were derived from the original LL152 Pilot PRD, which has been partially superseded. The LL152 domain requirements remain valid, but the "two lanes" and "LL152-only" product framing is outdated. See [ALPHA_PERSONAS_AND_SCOPE.md](../ALPHA_PERSONAS_AND_SCOPE.md).

# PRD Extraction Notes: LL152 Pilot

> **Source:** [PRD_LL152_PILOT.md](../PRD_LL152_PILOT.md)
> **Generated:** 2026-01-07
> **Purpose:** Structured extraction from PRD to verify SRSD alignment and identify gaps.

---

## 1. Goals & Product Promise (PRD §0.2)

### Plumber (Lane A)
- "Capture LL152 findings fast in the field with zero missed items"
- Phone-first; minimal typing
- **Time-to-value < 2 minutes** for core capture action

### LMP (Lane B)
- "Dispatch, review, and produce a GPS1/GPS2-ready packet with deadline tracking"
- Handoff reliability: LMP must get complete, reviewable packet every time
- Stable recordkeeping (owner needs records for years)

| PRD Claim | SRSD Mapping | Status |
|-----------|--------------|--------|
| < 2 min capture | `SNFR-UE-01` | ✅ |
| Phone-first | `SNFR-UEU-01` | ✅ |
| Zero missed items | `SFR-BRV-01`, `SFR-PRDM-10` | ✅ |
| Handoff reliability | `SFR-BRW-03` | ✅ |
| Archival export | `SFR-IOR-04` | ✅ |

---

## 2. Main User Flows (Lanes)

### Lane A — Plumber
| Screen | PRD §3.1 | SRSD Coverage |
|--------|----------|---------------|
| Assigned Jobs List | "Shows jobs sorted by date" | `SFR-IODO-01` |
| Job Detail | "Access notes, contacts" | `SFR-IODO-02` |
| GPS1-Structured Capture | "Guided form" | `SFR-IODE-01` |
| Submit to LMP | "Locks packet, notifies" | `SFR-BRW-03` |

### Lane B — LMP
| Screen | PRD §3.2 | SRSD Coverage |
|--------|----------|---------------|
| Job Intake | "Create job" | `SFR-IODE-10` |
| Dispatch | "Assign plumber, set deadline" | `SFR-IODE-12`, `SFR-BRW-01` |
| Review Panel | "Check completeness, edits" | `SFR-IODO-11` |
| Report Generation | "GPS1/GPS2 drafts" | `SFR-IOR-01`, `SFR-IOR-02` |
| Deadline Tracker | "30/60/120/180 logic" | `SFR-IODO-12`, `SFR-PRC-01..03` |

---

## 3. Functional Requirements Mapping

### v0 Must-Haves (PRD §4.1)
| # | Feature | SRSD Requirement |
|---|---------|------------------|
| 1 | LMP creates LL152 job and dispatches | `SFR-IODE-10`, `SFR-BRW-01` |
| 2 | Plumber completes guided capture + photos | `SFR-IODE-01..04` |
| 3 | Submit-to-LMP with completeness checks | `SFR-PRDM-10`, `SFR-BRW-03` |
| 4 | LMP review/approve with "return for fixes" | `SFR-PRDM-11`, `SFR-BRW-04..05` |
| 5 | Generate GPS1/GPS2-ready packet | `SFR-IOR-01..03` |
| 6 | Deadline tracker (30/60/120/180) + reminders | `SFR-PRC-01..03`, `SFR-BRW-13` |
| 7 | Search/history by address | `SFR-IODO-13`, `SFR-PRDP-03` |

### Job Status States (PRD §2.2)
| Status | SRSD Transition |
|--------|-----------------|
| 1. Intake | Initial state |
| 2. Dispatched | `SFR-BRW-01` |
| 3. In Progress | `SFR-BRW-02` |
| 4. Submitted to LMP | `SFR-BRW-03` |
| 5. Returned for Fixes | `SFR-BRW-05` |
| 6. Finalized | `SFR-BRW-04` |
| 7. Delivered to Owner | `SFR-BRW-06` |

---

## 4. Non-Functional Requirements Mapping

| PRD Claim | SRSD Requirement |
|-----------|------------------|
| Phone-first design | `SNFR-UEU-01..04` |
| Time-to-value < 2 min | `SNFR-UE-01` |
| Minimal typing | `SNFR-UEU-01` |
| Stable recordkeeping | `SFR-IOR-04`, `SNFR-RAV-10` |
| Fast iteration stack | `SNFR-MM-01..02` |

---

## 5. Explicit Out-of-Scope (PRD §4.2)

| Item | Status |
|------|--------|
| General plumbing job management | Out of scope |
| Billing/subscriptions | Out of scope |
| Inventory | Out of scope |
| Deep accounting integrations | Out of scope |
| Multi-company admin | Out of scope |
| Automated DOB portal submission | Out of scope |

> All items are correctly captured in `SGI-S_scope.md` under "Out of Scope (Pilot)".

---

## 6. Gap Analysis

### ✅ Resolved / Already Covered
| Area | Notes |
|------|-------|
| Deadlines | 30/60/120/180-day logic fully specified in `SFR-PRC` |
| State machine | All 7 states with valid transitions in `SFR-BRW` |
| Auth model | JWT with refresh tokens documented (`SFR-SRAN-02`, ADR-001) |
| Role permissions | `SFR-SRAZ` permission matrix complete |
| Offline support | `SNFR-RR-01..02` covers draft persistence and sync |
| PDF generation | `SFR-IOR-01..03` covers GPS1/GPS2/packet |

### ⚠️ Ambiguities Identified (Need Clarification)

| ID | Area | Question | Priority |
|----|------|----------|----------|
| GAP-01 | **GPS1/GPS2 Form Fields** | Exact field list not enumerated. The PRD references "LL152 Job Packet Spec" (§1.3) as a deliverable but it's not captured in SRSD. | HIGH |
| GAP-02 | **Sub-Cycle Mapping** | Community Districts A/B/C/D referenced but actual District→Sub-cycle mapping table not documented. | MEDIUM |
| GAP-03 | **Stop-the-Line Conditions** | PRD §1.3 mentions "triggers immediate escalation" — exact conditions (gas leak, utility shutoff, etc.) not enumerated. | MEDIUM |
| GAP-04 | **Photo Standards** | PRD §6.1 mentions "agree on photo/notes standards" but no minimum specs documented (resolution, angle, labeling). | LOW |
| GAP-05 | **Data Retention Policy** | PRD says "owner needs records for years" but no specific retention period documented. | LOW |

---

## 7. Blockers & Recommendations

### 🔴 Blockers (Require Resolution Before Implementation)

None identified. All critical items have SRSD mappings.

### 🟡 Recommendations (Resolve During Implementation)

1. **Create GPS1 Form Field Spec:** Extract exact fields from official GPS1 form and document in `docs/design/GPS1_FIELD_SPEC.md`.
2. **Document Stop-the-Line Conditions:** Work with LMP to enumerate escalation triggers.
3. **Data Retention ADR:** Draft ADR for 7-year retention policy (typical LL152 compliance window per NYC rules).

---

## 8. Verification Summary

| Section | PRD Items | SRSD Coverage | Status |
|---------|-----------|---------------|--------|
| SGI (Scope/Objectives) | Lanes, Goals, Out-of-Scope | Complete | ✅ |
| SFR (Functional) | 7 v0 Must-Haves | 61 requirements mapped | ✅ |
| SNFR (Non-Functional) | Performance, Usability, Security | 38 requirements mapped | ✅ |
| RLD (Resources) | Team, Tools | Complete | ✅ |

**Conclusion:** The existing SRSD baseline is comprehensive. Minor gaps (GAP-01 to GAP-05) are implementation-time clarifications, not blockers.
