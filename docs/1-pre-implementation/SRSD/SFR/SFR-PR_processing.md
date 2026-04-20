# SFR-PR: Processing Requirements

> **Parent:** [SFR Index](../README.md) | **Prev:** [SFR-IO](./SFR-IO_input-output.md) | **Next:** [SFR-BR](./SFR-BR_business-rules.md)

## Sub-Types
- [SFR-PRC (Calculation)](#sfr-prc-calculation)
- [SFR-PRDM (Decision Making)](#sfr-prdm-decision-making)
- [SFR-PRDP (Data Manipulation)](#sfr-prdp-data-manipulation)

---

## SFR-PRC: Calculation

### Deadline Computation

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-PRC-01` | **GPS1 Due Date:** Calculate `Inspection Date + 30 days` as GPS1 report due date to owner. | §Deliverables |
| `SFR-PRC-02` | **GPS2 Due Date:** Calculate `Inspection Date + 60 days` as GPS2 certification due date to DOB. | §Deliverables |
| `SFR-PRC-03` | **Correction Window:** If defects require correction, calculate `Inspection Date + 120 days` (or +180 if extension granted). | §Deliverables |
| `SFR-PRC-04` | **Compliance Year:** Determine building's 4-year inspection cycle based on Community District sub-cycle (A/B/C/D). | §2.3 |
| `SFR-PRC-05` | **[TBD] Sub-Cycle Map:** Exact mapping of Community Districts to Sub-Cycles (A/B/C/D) to be defined. | GAP-02 |

### Time Metrics

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-PRC-10` | **Time-to-Capture:** Track timestamp from "Capture Started" to "Submit" for monitoring <2 minute target. | §0.2, §5.2 |

---

## SFR-PRDM: Decision Making

### Dispatch Logic

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-PRDM-01` | **Plumber Assignment:** LMP selects which Plumber (Technician) to assign to a job. System validates Plumber is active. | §4.1.1 |
| `SFR-PRDM-02` | **Auto-Routing (Future):** (Not in v0) System could suggest nearest available Plumber. | N/A |

### State Transitions

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-PRDM-10` | **Completeness Check:** Before allowing "Submit to LMP", system validates all required GPS1 fields are filled and at least 1 photo attached. | §4.1.3 |
| `SFR-PRDM-11` | **Approve/Return Decision:** LMP reviews submission. If complete, advances to FINALIZED. If incomplete, returns to Plumber with notes. | §4.1.4 |
| `SFR-PRDM-12` | **Escalation Check:** If Plumber flags "Stop-the-line" condition, system alerts LMP immediately (push/notification). | §1.3 |

---

## SFR-PRDP: Data Manipulation

### Sorting & Filtering

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-PRDP-01` | **Sort by Scheduled Date:** Assigned Jobs list defaults to soonest-first. | §3.1 |
| `SFR-PRDP-02` | **Filter by Status:** LMP can filter job queue by status (e.g., "Needs Review", "Approaching Deadline"). | §3.2 |
| `SFR-PRDP-03` | **Search by Address:** LMP can search job history by address string or building ID. | §4.1.7 |

### Data Aggregation

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-PRDP-10` | **Funnel Counts:** Track count of jobs at each status for LMP dashboard overview. | §5.2 |
