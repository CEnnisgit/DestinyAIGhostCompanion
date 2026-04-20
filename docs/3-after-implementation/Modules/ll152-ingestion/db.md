# db.rs — Database Access Layer

> Source: [`apps/ll152-ingestion/src/db.rs`](file:///c:/github/pcd/apps/ll152-ingestion/src/db.rs)

## Purpose
Encapsulates all SQL interactions for the LL152 ingestion pipeline. Handles import run tracking, building resolution/stub creation, obligation upserting, quarantine writes, and reconciliation.

---

## Functions

### `create_import_run()` (Lines 8–29)
```rust
pub async fn create_import_run(pool, import_run_id, pipeline_name, source_file, source_version)
```
Inserts a new row into `import_runs` to record the start of an ingestion session. Called at the very beginning of `main()` to establish traceability before any data processing.

---

### `complete_import_run()` (Lines 31–53)
```rust
pub async fn complete_import_run(pool, import_run_id, rows_parsed, rows_inserted, rows_quarantined)
```
Updates the `import_runs` row with final counts (`rows_parsed`, `rows_inserted`, `rows_quarantined`) and a `completed_at` timestamp. Called as the very last step in `main()`.

---

### `flush_parse_errors()` (Lines 57–93)
```rust
pub async fn flush_parse_errors(pool, import_run_id, errors: &[ParseError])
```
Writes `ERROR`-severity parse failures to the `quarantined_rows` table.

- Operates in its **own transaction**, separate from the main upsert transaction.
- Only quarantines rows with `severity == "ERROR"`.
- Each row stores the `raw_payload` as JSONB for manual audit.

---

### `resolve_building_id_or_stub()` (Lines 97–129)
```rust
pub async fn resolve_building_id_or_stub(tx, bin_val: &Bin) -> Result<Uuid>
```
The **"Pipeline B" stub building** pattern:

1. **Lookup**: `SELECT id FROM buildings WHERE bin = $1`
2. **If found**: Returns the existing `building.id`.
3. **If not found**: Creates a minimal "stub" building with only the `bin` and `created_from_source = 'DOB_LL152'`.

This enables the compliance obligation to be linked to a building even when the full building record hasn't been imported yet (e.g., via Pipeline A / PAD ingestion).

---

### `upsert_compliance_payload()` (Lines 133–197)
```rust
pub async fn upsert_compliance_payload(tx, payload, source_version)
```
The core upsert engine. Performs three operations within the caller's transaction:

#### Step 1 — Resolve Building
Calls `resolve_building_id_or_stub()` and patches `payload.building_id`.

#### Step 2 — Upsert Compliance Obligation
```sql
INSERT INTO compliance_obligations (...)
ON CONFLICT (building_id, program_code, cycle_key) DO UPDATE SET
    window_start = EXCLUDED.window_start,
    window_end = EXCLUDED.window_end,
    ...
RETURNING id
```
- Uses the natural unique constraint `(building_id, program_code, cycle_key)`.
- On conflict, updates window dates and provenance fields.
- Hardcodes LL152-specific policy parameters: `report_to_owner_due_days=30`, `owner_filing_due_days=60`, `correction_cert_due_days=120`, `final_correction_due_days=180`.

#### Step 3 — Upsert LL152 Extension
```sql
INSERT INTO ll152_obligation_details (obligation_id, subcycle)
ON CONFLICT (obligation_id) DO UPDATE SET subcycle = EXCLUDED.subcycle
```
Maintains the 1:1 extension record for LL152-specific data (subcycle letter).

---

### `reconcile_inactive_obligations()` (Lines 201–264)
```rust
pub async fn reconcile_inactive_obligations(pool, import_run_id, program_code, roster_version) -> Result<u64>
```
Post-import reconciliation to detect **stale obligations**:

1. **Find stale**: Selects obligations where `roster_status = 'ACTIVE'` but `last_imported_from_version != current_version`.
2. **Mark inactive**: Updates each stale row to `roster_status = 'INACTIVE'`.
3. **Log event**: Inserts a `ROSTER_STATUS_CHANGED` event in `obligation_events` for audit trail.

Runs in its own transaction after the main commit.

---

## Transaction Boundaries

| Operation | Transaction Scope |
| :--- | :--- |
| All per-row upserts | Single shared transaction (from `main.rs`) |
| Quarantine writes | Separate transaction |
| Reconciliation updates | Separate transaction |
| Import run start/end | Direct pool queries (auto-committed) |
