# SNFR-P: Performance Requirements

> **Parent:** [SNFR Index](../README.md) | **Next:** [SNFR-U](./SNFR-U_usability.md)

## Sub-Types
- [SNFR-PRT (Response Time)](#snfr-prt-response-time)
- [SNFR-PT (Throughput)](#snfr-pt-throughput)
- [SNFR-PS (Scalability)](#snfr-ps-scalability)

---

## SNFR-PRT: Response Time

### User-Facing Latency

| Code | Description | Target | PRD Ref |
|------|-------------|--------|---------|
| `SNFR-PRT-01` | **API Response (p95):** All core API endpoints respond within target. | < 500ms | §5.1 |
| `SNFR-PRT-02` | **Mobile Screen Load:** Assigned Jobs list renders completely. | < 1.5s | §0.2 |
| `SNFR-PRT-03` | **Form Field Interaction:** Input fields respond instantly (no perceptible lag). | < 100ms | §0.2 |

### Background Operations

| Code | Description | Target |
|------|-------------|--------|
| `SNFR-PRT-10` | **Photo Upload (per photo, on 4G):** | < 5s |
| `SNFR-PRT-11` | **PDF Generation:** GPS1/GPS2 report generation completes. | < 10s |

---

## SNFR-PT: Throughput

### Concurrent Operations (Pilot)

| Code | Description | Target | PRD Ref |
|------|-------------|--------|---------|
| `SNFR-PT-01` | **Concurrent Users:** System handles pilot load without degradation. | 10 users | §6.1 |
| `SNFR-PT-02` | **Photo Uploads per Session:** Multiple photos can be uploaded in parallel. | 5 concurrent | Implicit |
| `SNFR-PT-03` | **Jobs per Day:** System handles daily job volume. | 10 jobs/day | §0.3 |


