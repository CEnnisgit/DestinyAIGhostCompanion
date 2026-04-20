# PAD Ingestion Module

## Overview
The `pad-ingestion` module is a high-performance Rust CLI worker that bootstraps the building identity layer by ingesting NYC's Property Address Directory (PAD) data files (`bbl.txt` and `adr.txt`). This is **Pipeline A** — the foundational data source.

## Key Features
- **Two-Pass CSV Processing**: First pass resolves primary BBLs via tie-breaking; second pass streams addresses to DB.
- **BBL Tie-Breaking**: When a BIN maps to multiple BBLs, the most frequent one wins (with deterministic secondary sort).
- **BBL Evidence Cache**: Loads condo flags, billing BBLs, and lot ranges from `bbl.txt` into memory.
- **Batched DB Writes**: Uses `QueryBuilder` with chunked inserts (1000 rows/chunk) for high throughput.
- **Change Detection**: Compares incoming data against existing records and logs diffs to `building_events`.
- **Three-Tier Severity**: ERROR (quarantine), WARN (anomaly), INFO (accepted with flag) per `Ingestion_Diagnostics.md`.

## Documentation

### Architecture
- [Architecture Diagram](Architecture.md) — Component and sequence diagrams

### Code Walkthroughs
- [main.md](main.md) — Orchestrator and two-pass ETL lifecycle
- [pipeline.md](pipeline.md) — BBL cache construction, tie-breaking, and severity classification
- [db.md](db.md) — Batched upserts, anomaly/quarantine flushing, streaming address writes
- [models.md](models.md) — `Bin` VO, `Bbl` VO, CSV deserialization structs
- [tests.md](tests.md) — Unit test suite with coverage analysis

## Location
- Source: `apps/pad-ingestion/src`
- Tests: `apps/pad-ingestion/src/tests.rs`
