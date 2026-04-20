# CRMModule (The Target)

> **Source of Truth:** `crates/pcd-domain/src/crm/` (domain) + `crates/pcd-db/src/crm/` (queries)
> **Scope:** Pilot Core (LL152) - **Phase 3**

## Traceability

> **Refer to:** [TraceabilityMatrix_SFR.md](./TRACEABILITY_SFR.md)

This module manages the "External World" actors and assets.

## Sub-Modules

### 1. [Assets](./Assets/README.md)
**Responsibility:** Physical Buildings.
*   Address Verification.
*   BIN / Community District Management.
*   Compliance Cycle Determination.

### 2. [Clients](./Clients/README.md) *(future)*
**Responsibility:** Human Owners.
*   Owner Profiles.
*   Contact Information.
*   Billing/Invoicing Data.

### 3. [Operations](./Operations/README.md) *(future)*
**Responsibility:** Tenant-Specific Workflow Overlay.
*   **Firm Overlay:** Private tags, notes, and statuses for global buildings.
*   **Organization:** Buckets, Projects, Lists.
*   **Workflow:** Outreach tracking and Job creation.

## Module Interactions

- **Consumes**: `AuthModule` (future).
- **Produces**: `Building` entities for `Jobs`.

## Current Implementation

| Component | Location | Status |
|-----------|----------|--------|
| Building aggregate | `crates/pcd-domain/src/crm/building.rs` | ✅ |
| ComplianceObligation | `crates/pcd-domain/src/crm/compliance_obligation.rs` | ✅ |
| ImportRun / ImportAnomaly | `crates/pcd-domain/src/crm/import_run.rs` | ✅ |
| Search, profile, timeline queries | `crates/pcd-db/src/crm/` (6 submodules) | ✅ |
| API routes | `crates/pcd-api/src/routes/crm.rs` | ✅ |
| Clients sub-module | — | ⏳ Future |
| Operations sub-module | — | ⏳ Future |
