# SNFR-SC: Scalability Requirements

> **Parent:** [SNFR Index](../README.md) | **Prev:** [SNFR-S](./SNFR-S_security.md) | **Next:** [SNFR-M](./SNFR-M_maintainability.md)

## Sub-Types
- [SNFR-SC: Scalability Requirements](#snfr-sc-scalability-requirements)
  - [Sub-Types](#sub-types)
  - [SNFR-SCS: Scale Targets](#snfr-scs-scale-targets)
    - [Growth Targets](#growth-targets)
  - [SNFR-SCI: Infrastructure](#snfr-sci-infrastructure)

---

## SNFR-SCS: Scale Targets

### Growth Targets

| Code | Description | Target | PRD Ref |
|------|-------------|--------|---------|
| `SNFR-SCS-01` | **Post-Pilot (3 companies):** | 50 users, 50 jobs/day | §7.3 |
| `SNFR-SCS-02` | **Future Growth:** | 200 users, 200 jobs/day | Roadmap |

---

## SNFR-SCI: Infrastructure

| Code | Description |
|------|-------------|
| `SNFR-SCI-10` | **Cloud Run Auto-Scaling:** Min 1, Max 10 instances for pilot. |
| `SNFR-SCI-11` | **Database Connection Pooling:** PostgreSQL connection pool sized for concurrent load. |
