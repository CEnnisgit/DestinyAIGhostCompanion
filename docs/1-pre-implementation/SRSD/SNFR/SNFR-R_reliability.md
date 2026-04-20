# SNFR-R: Reliability Requirements

> **Parent:** [SNFR Index](../README.md) | **Prev:** [SNFR-S](./SNFR-S_security.md) | **Next:** [SNFR-M](./SNFR-M_maintainability.md)

## Sub-Types
- [SNFR-RAV (Availability)](#snfr-rav-availability)
- [SNFR-RAC (Accuracy)](#snfr-rac-accuracy)
- [SNFR-RR (Robustness)](#snfr-rr-robustness)

---

## SNFR-RAV: Availability

### Uptime Targets

| Code | Description | Target | PRD Ref |
|------|-------------|--------|---------|
| `SNFR-RAV-01` | **System Uptime:** Production availability. | 99.5% (~4 hrs downtime/month) | Implicit |
| `SNFR-RAV-02` | **Scheduled Maintenance:** Maintenance windows outside business hours (6am-8pm ET). | After 10pm ET | Implicit |

### Disaster Recovery

| Code | Description |
|------|-------------|
| `SNFR-RAV-10` | **Database Backups:** Automated daily backups with 7-day retention. |
| `SNFR-RAV-11` | **Recovery Time Objective (RTO):** Restore from backup within 4 hours. |

---

## SNFR-RAC: Accuracy

### Calculation Accuracy

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SNFR-RAC-01` | **Deadline Calculation:** GPS1/GPS2 due dates accurate to the day (UTC→ET conversion handled correctly). | §Deliverables |
| `SNFR-RAC-02` | **Compliance Cycle:** Community District sub-cycle (A/B/C/D) correctly maps to 4-year window. | §2.3 |

### Data Accuracy

| Code | Description |
|------|-------------|
| `SNFR-RAC-10` | **No Data Loss on Submit:** Submitted findings persisted atomically (no partial saves). |
| `SNFR-RAC-11` | **Photo Integrity:** Uploaded photos verified (checksum) and stored without corruption. |

---

## SNFR-RR: Robustness

### Offline Resilience

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SNFR-RR-01` | **Draft Persistence:** In-progress form data saved locally on mobile. If app crashes, user can resume. | §0.2 |
| `SNFR-RR-02` | **Sync on Reconnect:** When network returns, pending submissions automatically sync. | §0.2 |

### Error Handling

| Code | Description |
|------|-------------|
| `SNFR-RR-10` | **Graceful Degradation:** If API unavailable, app shows cached data with "offline" indicator. |
| `SNFR-RR-11` | **Retry Logic:** Failed photo uploads retry automatically (3 attempts with exponential backoff). |
