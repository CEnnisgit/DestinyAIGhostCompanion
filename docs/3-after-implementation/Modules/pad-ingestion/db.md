# db.rs — Database Access Layer

> Source: [`apps/pad-ingestion/src/db.rs`](file:///c:/github/pcd/apps/pad-ingestion/src/db.rs)

## Purpose
Encapsulates all database operations for the PAD Bootstrap pipeline. Uses `sqlx::QueryBuilder` for high-throughput batched inserts with a unified chunk size of 1000 rows.

---

## Constants & Helpers

### `CHUNK_SIZE` (Line 11)
```rust
const CHUNK_SIZE: usize = 1000;
```
All batch operations use this uniform chunk size.

### `fmt_bbl_triple()` (Lines 14–19)
Formats an optional `(borough, block, lot)` triple as a human-readable `"1-10-50"` string for event logging.

### Internal Structs

**`BuildingRow`** (Lines 22–35): Intermediate struct accumulating all fields for a single building UPSERT.

**`EventRow`** (Lines 38–42): Intermediate struct for change-detection events logged to `building_events`.

---

## Functions

### `flush_buildings()` (Lines 44–224)
```rust
pub async fn flush_buildings(pool, buildings, bbl_cache, pad_version) -> Result<()>
```
The largest and most complex function. Processes buildings in chunks:

#### Per-Chunk Flow:
1. **Batch Fetch**: `SELECT ... FROM buildings WHERE bin = ANY($1)` — loads existing records for diff comparison.
2. **Enrichment**: For each building, looks up the primary BBL in the `BblCache` to pull condo flag, billing BBL, and lot ranges.
3. **Change Detection** (Lines 107–137): Compares incoming data against existing records. Tracks diffs in:
   - `primary_bbl` (borough/block/lot triple)
   - `pad_condo_flag`
   - `pad_billing_bbl`
   - New buildings get `action: "CREATED"`.
4. **Batched UPSERT** (Lines 158–204): Uses `QueryBuilder::push_values()` to build a single `INSERT ... ON CONFLICT (bin) DO UPDATE SET ...` statement for the entire chunk.
5. **Event Logging** (Lines 206–218): Inserts `building_events` rows for any changed or newly created buildings.
6. **Transaction**: Each chunk is wrapped in its own transaction.

#### Columns Updated on Conflict:
- `primary_bbl_borough_code`, `primary_bbl_block`, `primary_bbl_lot`
- `pad_version`, `pad_condo_flag`
- `pad_billing_bbl_*`, `pad_low_bbl_lot`, `pad_high_bbl_lot`
- `pad_last_seen_at`, provenance fields

---

### `flush_anomalies()` (Lines 226–267)
```rust
pub async fn flush_anomalies(pool, buildings, import_run_id, source_ref) -> Result<()>
```
Filters buildings where `is_anomalous == true` and writes `BIN_MULTIPLE_BBLS_PRIMARY_SELECTED` anomalies to `import_anomalies` with `WARN` severity.

---

### `flush_parse_errors()` (Lines 271–360)
```rust
pub async fn flush_parse_errors(pool, errors, import_run_id, source_ref) -> Result<()>
```
Two-stage write:

1. **All errors** → `import_anomalies` (preserves all three severity levels).
2. **ERROR-only** → `quarantined_rows` (includes `raw_payload` as JSONB with all original CSV fields).

---

### `flush_addresses_streaming()` (Lines 362–406)
```rust
pub async fn flush_addresses_streaming<R: Read>(pool, reader, pad_version) -> Result<usize>
```
Second pass over `adr.txt`. Three stages:

1. **Stale Cleanup**: `DELETE FROM building_addresses WHERE pad_version != $1` — removes addresses from previous PAD versions.
2. **Streaming**: Reads CSV in chunks of `CHUNK_SIZE`, calling `flush_address_chunk()` for each batch.
3. **Returns**: Total count of flushed addresses.

---

### `flush_address_chunk()` (Lines 418–465)
```rust
async fn flush_address_chunk(pool, rows, pad_version) -> Result<()>
```
Internal helper applying `Address_VO_Spec.md` normalization:

| Normalization | Example |
| :--- | :--- |
| Uppercase street name | `"broadway"` → `"BROADWAY"` |
| Collapse whitespace | `"  EAST   42ND   ST  "` → `"EAST 42ND ST"` |
| Borough code validation | Skips rows where borough is outside 1–5 |

Builds a display string as `"{house_number} {street_name}"` for the `house_number_display` column.

---

## Transaction Boundaries

| Operation | Transaction Scope |
| :--- | :--- |
| Building upserts + events | Per-chunk transaction |
| Anomaly writes | Auto-committed (direct pool) |
| Parse error writes | Auto-committed (direct pool) |
| Stale address cleanup | Auto-committed (direct pool) |
| Address chunk inserts | Auto-committed (direct pool) |
