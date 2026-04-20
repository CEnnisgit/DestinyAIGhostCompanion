# StorageModule

> **Source of Truth:** [`apps/backend/src/infrastructure/storage`](file:///c:/github/pcd/apps/backend/src/infrastructure/storage)
> **Scope:** [Pilot Core (LL152) - Infrastructure](file:///c:/github/pcd/docs/PILOT_SCOPE_CONTEXT.md)

## Traceability

> **Refer to:** [TraceabilityMatrix_SFR.md](../../Traceability/TraceabilityMatrix_SFR.md)

- **Primary Responsibility**: Blob Storage Adapter (`SFR-IODE-02`, `SFR-IRDX-02`).

## Module Responsibilities

1. **Blob Storage**: Upload/Download files (Images, PDFs) to S3/GCS or Local Disk (Dev).
2. **Signing**: Generating Signed URLs for secure frontend access.

## Module Structure

- **Infrastructure**: Adapter pattern implementing `IStorageProvider`.
- **Database**: No tables (Stateless).

## Module Interactions

- **Consumes**: File Streams from `Jobs` (Photos) and `ReportingModule` (PDFs).
- **Produces**: Public/Signed URLs.

## Algorithm Descriptions

- **N/A**: Infrastructure Adapter.

## Data Structure Selection

- **N/A**: Infrastructure Adapter.
