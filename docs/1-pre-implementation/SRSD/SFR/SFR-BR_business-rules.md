# SFR-BR: Business Rules

> **Parent:** [SFR Index](../README.md) | **Prev:** [SFR-PR](./SFR-PR_processing.md) | **Next:** [SFR-SR](./SFR-SR_security.md)

## Sub-Types
- [SFR-BRC (Constraints)](#sfr-brc-constraints)
- [SFR-BRV (Validation)](#sfr-brv-validation)
- [SFR-BRW (Workflow)](#sfr-brw-workflow)

---

## SFR-BRC: Constraints

### Job Constraints

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-BRC-01` | **Single Assignment:** A job can only be assigned to one Plumber at a time. | Implicit |
| `SFR-BRC-02` | **Inspection Date Required:** Inspection Date must be set when Plumber starts capture. Cannot be in the future. | §2.3 |
| `SFR-BRC-03` | **Community District Required:** Job must have Community District (A/B/C/D) to calculate compliance window. | §2.3 |
| `SFR-BRC-04` | **[TBD] Stop-Conditions:** Explicit conditions triggering "Stop-the-line" escalation (e.g., Gas Leak level X) to be enumerated. | GAP-03 |

### Status Constraints

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-BRC-10` | **No Backward Transitions:** Once FINALIZED, job cannot return to SUBMITTED or earlier (immutable). | §2.2 |
| `SFR-BRC-11` | **Return Only Before Finalize:** LMP can only "Return for Fixes" while in SUBMITTED state. | §2.2 |

---

## SFR-BRV: Validation

### Submission Validation

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-BRV-01` | **Required Fields Check:** All GPS1 required fields (per LL152 Job Packet Spec) must be filled before submission. | §1.3, §4.1.3 |
| `SFR-BRV-02` | **Photo Minimum:** At least 1 photo required for submission. If defect flagged, additional photo of defect required. | §1.3 |
| `SFR-BRV-03` | **Inspection Date Valid:** Inspection date must be today or in the past. | §2.3 |

### Intake Validation

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-BRV-10` | **Address Required:** Job must have a valid address. | §1.2 |
| `SFR-BRV-11` | **Owner Contact Recommended:** System warns if owner contact info is empty (not blocking). | §1.2 |

---

## SFR-BRW: Workflow

### State Machine (LL152 Job Lifecycle)

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-BRW-01` | **Intake → Dispatched:** LMP assigns Plumber. Job moves from INTAKE to DISPATCHED. Plumber notified. | §2.2, §4.1.1 |
| `SFR-BRW-02` | **Dispatched → In Progress:** Plumber opens job and starts capture. Status changes to IN_PROGRESS. | §2.2 |
| `SFR-BRW-03` | **In Progress → Submitted:** Plumber completes capture and submits. Status changes to SUBMITTED. Job is locked. LMP notified. | §2.2, §3.1 |
| `SFR-BRW-04` | **Submitted → Finalized:** LMP approves findings. Status changes to FINALIZED. GPS1/GPS2 can be generated. | §2.2, §4.1.4 |
| `SFR-BRW-05` | **Submitted → Returned:** LMP returns with notes. Status changes to RETURNED. Job unlocked for Plumber edits. | §2.2, §4.1.4 |
| `SFR-BRW-06` | **Finalized → Delivered:** LMP marks packet as delivered to owner. Status changes to DELIVERED. | §2.2 |

### Notifications

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-BRW-10` | **Dispatch Notification:** Plumber receives push/in-app notification when assigned to job. | §4.1.1 |
| `SFR-BRW-11` | **Submission Notification:** LMP receives notification when Plumber submits. | §3.1 |
| `SFR-BRW-12` | **Return Notification:** Plumber receives notification when job is returned for fixes. | §4.1.4 |
| `SFR-BRW-13` | **Deadline Reminder:** System sends reminders as 30/60-day deadlines approach (e.g., 7 days before, 1 day before). | §4.1.6 |
