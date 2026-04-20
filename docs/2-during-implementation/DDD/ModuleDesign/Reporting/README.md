# ReportingModule

> **Source of Truth:** [`packages/features/reports`](file:///c:/github/pcd/packages/features/reports)
> **Scope:** Pilot Core (LL152)

## Traceability
> **Refer to:** [TraceabilityMatrix_SFR.md](../../Traceability/TraceabilityMatrix_SFR.md)

- **Primary Responsibility**: Deliverable Generation (`SFR-IOR-*`) and Review Cycle.
- **Key Requirements**:
    - `SFR-IOR-01`: GPS1 Report Generation (PDF).
    - `SFR-IOR-02`: GPS2 Draft Generation.
    - `SFR-IODO-11`: Review Panel (Flag Management).

## Module Responsibilities
1.  **PDF Generation**: Hydrates `inspection_forms` data into PDF templates (GPS1/GPS2).
2.  **Review Logic**: Manages the `inspection_report_flags` lifecycle (Raised -> Resolved).
3.  **Storage**: Uploads generated artifacts to Blob Storage via `StorageModule` (Adapter).

## Module Structure
- **Package**: `@pcd/reports-backend`
- **Service**: `ReportingService` (Orchestrates generation).
- **Database**: Owns `inspection_reports` and `inspection_report_flags`.
- **API**: `/jobs/:id/report`, `/reports/:id/flags`.

## Module Interactions
- **Consumes**:
    - `Jobs`: Gets raw form data.
    - `UsersModule`: Gets Company/Technician visual signatures/license info for the PDF.
    - `CRMModule`: Gets Owner/Building address data for headers.
- **Produces**:
    - Final PDF URLs stored in `inspection_reports.storage_url`.

## Algorithm Descriptions
- **Flag Resolution**: Logic to determine if a Report is "Clean" (all flags resolved) and ready for Finalization.

## Data Structure Selection
- **Document Store Pattern**: Metadata in DB (`inspection_reports`), Binary in Object Storage (S3/GCS).
