# SNFR-S: Security Requirements (Non-Functional)

> **Parent:** [SNFR Index](../README.md) | **Prev:** [SNFR-U](./SNFR-U_usability.md) | **Next:** [SNFR-R](./SNFR-R_reliability.md)

## Sub-Types
- [SNFR-SC (Confidentiality)](#snfr-sc-confidentiality)
- [SNFR-SI (Integrity)](#snfr-si-integrity)
- [SNFR-SA (Availability)](#snfr-sa-availability)

---

## SNFR-SC: Confidentiality

### Data Protection

| Code | Description | Implementation |
|------|-------------|----------------|
| `SNFR-SC-01` | **Data in Transit:** All API calls over HTTPS with TLS 1.3. | Enforced at Cloud Run |
| `SNFR-SC-02` | **Data at Rest:** Database encryption using GCP-managed keys. | Cloud SQL default |
| `SNFR-SC-03` | **Photo Storage:** Photos stored in private Cloud Storage bucket (no public access). | ACL enforced |

### Sensitive Data

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SNFR-SC-10` | **Owner PII:** Owner contact info (name, phone, email) encrypted at rest. | §0.2 |
| `SNFR-SC-11` | **Password Storage:** User passwords hashed with Argon2. | ADR-001 |
| `SNFR-SC-12` | **[TBD] Data Retention:** Job records retained for N years (Target: 7 years) per compliance rules. | GAP-05 |

---

## SNFR-SI: Integrity

### Data Integrity

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SNFR-SI-01` | **Inspection Immutability:** Once FINALIZED, inspection findings cannot be modified (append-only corrections if needed). | §0.2 |
| `SNFR-SI-02` | **Audit Trail:** All status transitions logged with user ID, timestamp, and previous value. | §5.2 |

### System Integrity

| Code | Description |
|------|-------------|
| `SNFR-SI-10` | **Input Validation:** All user inputs sanitized to prevent SQL injection and XSS. |
| `SNFR-SI-11` | **CSRF Protection:** All state-changing requests protected with CSRF tokens or same-origin checks. |

---

## SNFR-SA: Availability (Security Context)

### Attack Resilience

| Code | Description | Implementation |
|------|-------------|----------------|
| `SNFR-SA-01` | **Rate Limiting:** API endpoints protected from brute-force (100 req/min per IP). | Express middleware |
| `SNFR-SA-02` | **DDoS Protection:** Cloud Run provides basic DDoS mitigation. | GCP-managed |
| `SNFR-SA-03` | **Token Expiry:** Short-lived access tokens (15 min) limit window for stolen token abuse. | ADR-001 |
