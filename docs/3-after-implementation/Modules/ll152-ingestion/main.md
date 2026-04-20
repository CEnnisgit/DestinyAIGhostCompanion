# main.rs — Orchestrator

> Source: [`apps/ll152-ingestion/src/main.rs`](file:///c:/github/pcd/apps/ll152-ingestion/src/main.rs)

## Purpose
Entry point and orchestrator for the LL152 ingestion pipeline. Coordinates the full ETL lifecycle: CLI parsing → Excel extraction → row processing → database flush → reconciliation.

---

## Structs

### `Args` (Lines 13–27)
CLI argument parser using `clap::Parser`.

| Argument | Default | Description |
| :--- | :--- | :--- |
| `roster_file` | `docs/LL152_Properties.xlsx` | Path to the DOB Excel roster |
| `program_code` | `LL152` | Compliance program identifier |
| `roster_version` | `cycle-2-initial` | Version tag for provenance tracking |
| `database_url` | `postgres://pcd:pcd123@...` | Connection string |

---

## `main()` — Async Entry Point (Lines 29–116)

### Step-by-step Walkthrough

#### 1. Initialization (Lines 31–41)
```rust
env_logger::init_from_env(...);
let args = Args::parse();
let import_run_id = Uuid::new_v4();
let pool = sqlx::PgPool::connect(&args.database_url).await?;
db::create_import_run(&pool, import_run_id, ...);
```
- Initializes logging (default level: `info`).
- Parses CLI args and generates a unique `import_run_id` for traceability.
- Opens the Postgres connection pool.
- Records the import run in the `import_runs` table **before** any processing begins.

#### 2. Excel Parsing (Lines 43–78)
```rust
let mut workbook: Xlsx<_> = open_workbook(&args.roster_file)?;
let range = workbook.worksheet_range(sheet_name).unwrap();
let iter = RangeDeserializerBuilder::new().from_range::<_, Ll152ExcelRow>(&range)?;
```
- Opens the `.xlsx` file using `calamine`.
- Assumes the **first sheet** is the target.
- Deserializes each row into an `Ll152ExcelRow` struct.

**Row Loop**: Each row is sent to `pipeline::process_ll152_row()`. Results are sorted into two vectors:
- `payloads: Vec<ComplianceObligationPayload>` — valid rows
- `parse_errors: Vec<ParseError>` — quarantine candidates

#### 3. Database Transaction (Lines 83–97)
```rust
let mut tx = pool.begin().await?;
for mut payload in payloads {
    db::upsert_compliance_payload(&mut tx, &mut payload, &args.roster_version).await?;
}
tx.commit().await?;
```
- Wraps all upserts in a **single transaction** for atomicity.
- Each payload triggers building resolution, obligation upsert, and LL152 detail upsert.
- Failed individual rows are logged but don't abort the batch.

#### 4. Post-Transaction Cleanup (Lines 99–114)
Three sequential operations after the main commit:

| Step | Function | Effect |
| :--- | :--- | :--- |
| Quarantine | `db::flush_parse_errors()` | Writes bad rows to `quarantined_rows` |
| Reconciliation | `db::reconcile_inactive_obligations()` | Marks stale obligations as `INACTIVE` |
| Finalization | `db::complete_import_run()` | Updates `import_runs` with counts and `completed_at` |
