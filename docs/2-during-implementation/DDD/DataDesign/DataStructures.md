# Data Structures

> **Parent:** [Data Design](./README.md) | **Source:** [ERD](./ERD.md)

This document defines the **Shared / Cross-cutting Domain Objects** used across modules. Module-specific internal structures are documented within each Module Design file.

## Shared Domain Objects

### Identity Types

```
UUID              — Standard v4 UUID used as primary key type across all tables.
Timestamp         — UTC timestamp (chrono::DateTime<Utc> in Rust, ISO 8601 in API).
```

### User Role Enum *(future — Auth module not yet implemented)*

| Value | Description |
|-------|-------------|
| `PLATFORM_ADMIN` | Full system access |
| `COMPANY_ADMIN` | Full access within a company scope |
| `TECHNICIAN` | Access to assigned jobs and capture features |
| `OWNER` | Read-only access to properties and inspections |

### Job Status Enum

| Value | Transitions To | Terminal? |
|-------|----------------|-----------|
| `OPEN` | `IN_PROGRESS` | No |
| `IN_PROGRESS` | `COMPLETED`, `CANCELED` | No |
| `COMPLETED` | — | Yes |
| `CANCELED` | — | Yes |

> **Source:** `crates/pcd-domain/src/jobs/job_status.rs`

### Job Priority Enum

| Value | Rank |
|-------|------|
| `NORMAL` | 1 |
| `HIGH` | 2 |
| `URGENT` | 3 |

### Job Source Kind Enum

| Value | Description |
|-------|-------------|
| `INBOUND_CALL` | Customer called in |
| `OUTREACH` | Proactive marketing |
| `REFERRAL` | Third-party referral |
| `WALK_IN` | In-person request |
| `OBLIGATION_LINKED` | Generated from compliance obligation |
| `OTHER` | Uncategorized |

### Compliance Obligation Status Enum

| Value | Description |
|-------|-------------|
| `UNKNOWN` | Status not yet determined |
| `OPEN` | Inspection required |
| `DUE_SOON` | Approaching deadline |
| `OVERDUE` | Past deadline |
| `SATISFIED` | Inspection completed |
| `AT_RISK` | May miss deadline |
| `NOT_REQUIRED` | Exempt from requirement |

### Roster Status Enum

| Value | Description |
|-------|-------------|
| `ACTIVE` | Currently on DOB roster |
| `INACTIVE` | Dropped from roster (historical record preserved) |

---

## Module Mapping

| Domain Object | Owner Module | Source |
|---------------|-------------|--------|
| `Building`, `BuildingAddress` | CRM / Assets | `crates/pcd-domain/src/crm/building.rs` |
| `ComplianceObligation` | CRM / Compliance | `crates/pcd-domain/src/crm/compliance_obligation.rs` |
| `ImportRun`, `ImportAnomaly` | CRM / Assets | `crates/pcd-domain/src/crm/import_run.rs` |
| `Job`, `JobStatus`, `JobNumber` | Jobs / Engine | `crates/pcd-domain/src/jobs/` |
| `User`, `UserRole` | Auth *(future)* | — |
| `PlumbingCompany`, `Technician` | Users *(future)* | — |
| `InspectionForm`, `InspectionReport` | Jobs / Workflows *(future)* | — |
