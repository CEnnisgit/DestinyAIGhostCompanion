# SFR-IO: Input/Output Requirements

> **Parent:** [SFR Index](../README.md) | **Next:** [SFR-PR](./SFR-PR_processing.md)

## Sub-Types
- [SFR-IODE (Data Entry)](#sfr-iode-data-entry)
- [SFR-IODO (Data Output)](#sfr-iodo-data-output)
- [SFR-IOR (Reporting)](#sfr-ior-reporting)

---

## SFR-IODE: Data Entry

### Plumber Lane (Field Capture)

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-IODE-01` | **GPS1-Structured Capture:** Plumber inputs LL152 inspection findings via guided form mapped to GPS1 sections (categories, conditions, access limitations). | §1.2, §3.1 |
| `SFR-IODE-02` | **Photo Attachments:** Plumber attaches photos for meter room, boiler room, any defects found. Minimum 1 photo required for defect conditions. | §1.3 |
| `SFR-IODE-03` | **Notes/Comments:** Free-text field for plumber to add observations not covered by structured fields. | §1.2 |
| `SFR-IODE-04` | **Stop-the-line Flags:** Plumber can flag immediate hazard conditions requiring LMP/utility/DOB escalation. | §1.3 |

### LMP Lane (Job Intake)

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-IODE-10` | **Job Header:** LMP creates LL152 job with: Address, BIN/Block/Lot (optional), Community District (A/B/C/D), Owner Contact, Access Notes (keys, super, meter room location). | §1.2, §4.1 |
| `SFR-IODE-11` | **Building Profile:** LMP can associate job with existing Building record or create new. | §2.1 |
| `SFR-IODE-12` | **Dispatch Info:** LMP assigns Plumber and sets scheduled date. | §3.2, §4.1 |

---

## SFR-IODO: Data Output

### Plumber Views

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-IODO-01` | **Assigned Jobs List:** Plumber sees list of jobs assigned to them, sorted by scheduled date (soonest first). Shows: Address, Scheduled Date, Status. | §3.1 |
| `SFR-IODO-02` | **Job Detail View:** Plumber sees job header with access notes, contacts, building details before arriving on-site. | §1.2, §3.1 |
| `SFR-IODO-03` | **Submission Confirmation:** After submit, Plumber sees confirmation screen with job ID and "Pending LMP Review" status. | §3.1 |

### LMP Views

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-IODO-10` | **Job Queue:** LMP sees all jobs across statuses (Intake, Dispatched, Submitted, Finalized, Delivered). Filterable by status, deadline. | §3.2, §4.1 |
| `SFR-IODO-11` | **Review Panel:** LMP sees Plumber's submitted findings, photos, notes in a reviewable format. Can approve or return with notes. | §3.2, §4.1 |
| `SFR-IODO-12` | **Deadline Dashboard:** LMP sees jobs approaching 30/60/120/180-day deadlines with countdown indicators. | §4.1.6 |
| `SFR-IODO-13` | **Search/History:** LMP can search past jobs by address or building to retrieve historical inspections. | §4.1.7 |

---

## SFR-IOR: Reporting

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-IOR-01` | **GPS1 Report Generation:** System generates a GPS1-formatted PDF from Plumber's structured findings. No retyping required. | §4.1.5, §0.3 |
| `SFR-IOR-02` | **GPS2 Draft Generation:** System generates a GPS2 certification draft (LMP fills in signature/seal manually or electronically). | §4.1.5 |
| `SFR-IOR-03` | **Owner Packet Export:** LMP can export combined GPS1 + GPS2 + Photos as a single deliverable package (PDF bundle or structured export). | §4.1.5 |
| `SFR-IOR-04` | **Archival Export:** System allows export of job records for long-term archival (owner needs records for years). | §0.2 |
