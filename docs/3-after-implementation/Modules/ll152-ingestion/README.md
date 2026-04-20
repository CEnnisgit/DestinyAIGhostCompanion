# LL152 Ingestion Module

## Overview
The `ll152-ingestion` module is a high-performance Rust CLI worker designed to ingest Manhattan Plumbing Compliance (LL152) rosters provided by the DOB in Excel format.

## Key Features
- **Excel Parsing**: Uses `calamine` for fast, memory-efficient extraction from large `.xlsx` files.
- **Strongly Typed Domain**: Implements the `Bin` Value Object with strict validation rules.
- **Pipeline B Specification**: 
    - Automatically creates "Stub" buildings for unknown BINs.
    - Reconciliation logic to deactivate obligations not present in the latest roster.
- **Quarantine System**: Failed rows are moved to `quarantined_rows` for audit and manual intervention.
- **Event Logging**: Tracks status changes and ingestion results in `obligation_events` and `import_runs`.

## Documentation

### Architecture
- [Architecture Diagram](Architecture.md) — Component and sequence diagrams

### Code Walkthroughs
- [main.md](main.md) — Orchestrator and ETL lifecycle
- [pipeline.md](pipeline.md) — Domain transformation and validation logic
- [db.md](db.md) — Database access layer, upserts, and reconciliation
- [models.md](models.md) — Domain types: `Bin` VO, DTOs, and error types
- [tests.md](tests.md) — Unit test suite with coverage analysis

## Location
- Source: `apps/ll152-ingestion/src`
- Tests: `apps/ll152-ingestion/src/tests.rs`
