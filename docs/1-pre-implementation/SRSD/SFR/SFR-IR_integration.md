# SFR-IR: Integration Requirements

> **Parent:** [SFR Index](../README.md) | **Prev:** [SFR-SR](./SFR-SR_security.md)

## Sub-Types
- [SFR-IRI (Interface)](#sfr-iri-interface)
- [SFR-IRDX (Data Exchange)](#sfr-irdx-data-exchange)
- [SFR-IRIN (Interoperability)](#sfr-irin-interoperability)

---

## SFR-IRI: Interface

### System Interfaces

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-IRI-01` | **Mobile App → Backend:** Plumber mobile app communicates via REST API (`/api/v1/jobs`, `/api/v1/inspections`). | §5.1 |
| `SFR-IRI-02` | **Dashboard → Backend:** LMP dashboard communicates via same REST API. | §5.1 |
| `SFR-IRI-03` | **File Upload:** Photos uploaded via multipart POST to `/api/v1/photos`. | Implicit |

### External Integrations (v0)

| Code | Description | Status | PRD Ref |
|------|-------------|--------|---------|
| `SFR-IRI-10` | **DOB Portal:** Manual export only. No automated submission. | Not in v0 | §4.2 |
| `SFR-IRI-11` | **Email Delivery:** (Future) Send packet to owner via email. | Planned | Implicit |

---

## SFR-IRDX: Data Exchange

### API Formats

| Code | Description |
|------|-------------|
| `SFR-IRDX-01` | **Request/Response:** JSON for all API payloads. |
| `SFR-IRDX-02` | **File Uploads:** Multipart form-data for photos (JPEG/PNG, max 10MB per file). |
| `SFR-IRDX-03` | **Export Formats:** PDF for GPS1/GPS2 reports. ZIP for bundled packet export. |

### Sync Behavior

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-IRDX-10` | **Online-First:** Mobile app requires network for submit. Draft data stored locally until network available. | §0.2 |

---

## SFR-IRIN: Interoperability

### Platform Compatibility

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-IRIN-01` | **Mobile:** iOS 15+ (Safari WebView), Android 12+ (Chrome WebView). | §0.2 |
| `SFR-IRIN-02` | **Desktop:** Chrome, Safari, Edge (latest 2 versions). | Implicit |

### Standards Compliance

| Code | Description |
|------|-------------|
| `SFR-IRIN-10` | **GPS1/GPS2 Format:** Generated PDFs must match NYC DOB GPS1/GPS2 form layout for manual submission. |
