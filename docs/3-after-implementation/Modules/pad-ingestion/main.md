# main.rs — Orchestrator

> Source: [`apps/pad-ingestion/src/main.rs`](file:///c:/github/pcd/apps/pad-ingestion/src/main.rs)

## Purpose
Entry point and orchestrator for the PAD Bootstrap ingestion pipeline (Pipeline A). Coordinates a multi-phase ETL: BBL cache loading → ADR tie-breaking → database flush → address streaming.

---

## Structs

### `Args` (Lines 13–31)
CLI argument parser using `clap::Parser`.

| Argument | Default | Description |
| :--- | :--- | :--- |
| `bbl_file` | `bbl.txt` | Path to the PAD BBL evidence file |
| `adr_file` | `adr.txt` | Path to the PAD Address Range file |
| `pad_version` | `25A` | PAD release version label (e.g., 25A, 25B) |
| `database_url` | `postgres://pcd:pcd123@...` | Connection string |

---

## `main()` — Async Entry Point (Lines 33–85)

### Step-by-step Walkthrough

#### Phase 1: BBL Cache Load (Lines 41–45)
```rust
let bbl_file = File::open(&args.bbl_file)?;
let bbl_cache = pipeline::build_bbl_cache(bbl_file)?;
```
Opens `bbl.txt` and constructs an in-memory `HashMap<Bbl, BblEvidence>` containing condo flags, billing BBLs, and lot ranges. This cache is used during Phase 3 to enrich buildings.

#### Phase 2: ADR Processing & Tie-Breaking (Lines 47–60)
```rust
let adr_file = File::open(&args.adr_file)?;
let (buildings, parse_errors) = pipeline::process_adr_and_tiebreak(adr_file)?;
```
First pass over `adr.txt`. For each row:
- Validates BIN (ERROR if missing/invalid, INFO if temp/dummy)
- Validates BBL (WARN if unparseable)
- Tallies BIN → BBL frequency

Then tie-breaks: for each BIN, selects the most-frequent BBL as `primary_bbl`. Flags multi-BBL BINs as `is_anomalous`.

#### Phase 3: Database Flush (Lines 62–72)
Four sequential flush operations:

| Step | Function | Target Table(s) |
| :--- | :--- | :--- |
| 1 | `db::flush_buildings()` | `buildings`, `building_events` |
| 2 | `db::flush_anomalies()` | `import_anomalies` |
| 3 | `db::flush_parse_errors()` | `import_anomalies`, `quarantined_rows` |
| 4 | `db::flush_addresses_streaming()` | `building_addresses` |

#### Phase 4: Address Streaming (Lines 74–77)
```rust
let adr_file_pass2 = File::open(&args.adr_file)?;
let addr_count = db::flush_addresses_streaming(&pool, adr_file_pass2, &args.pad_version).await?;
```
Second pass over `adr.txt`. Streams address rows directly from CSV to database in batches of 1000, applying `Address_VO_Spec.md` normalization.

---

## Design Decisions

| Decision | Rationale |
| :--- | :--- |
| Two passes over `adr.txt` | Pass 1 needs full tally for tie-breaking; Pass 2 streams addresses without holding all in memory |
| BBL cache in memory | `bbl.txt` is small enough to fit in RAM; avoids repeated disk I/O during enrichment |
| Sequential flush operations | Order matters: buildings must exist before addresses can reference them |
