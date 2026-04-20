# pipeline.rs — Domain Transformation Logic

> Source: [`apps/pad-ingestion/src/pipeline.rs`](file:///c:/github/pcd/apps/pad-ingestion/src/pipeline.rs)

## Purpose
Pure domain logic for the PAD Bootstrap pipeline. Builds the BBL evidence cache, processes ADR rows with three-tier severity classification, and applies the tie-breaking algorithm to resolve primary BBLs.

---

## Types

### `BblEvidence` (Lines 4–10)
```rust
pub struct BblEvidence {
    pub pad_condo_flag: Option<String>,
    pub pad_billing_bbl: Option<Bbl>,
    pub pad_low_bbl_lot: Option<String>,
    pub pad_high_bbl_lot: Option<String>,
}
```
Evidence record from `bbl.txt` that enriches a building during the database flush. Indexed by `Bbl` in the `BblCache`.

### `TieBreakerResult` (Lines 12–17)
```rust
pub struct TieBreakerResult {
    pub bin: Bin,
    pub primary_bbl: Bbl,
    pub is_anomalous: bool,
}
```
Output of the tie-breaking phase. `is_anomalous = true` when a BIN maps to more than one distinct BBL.

### `ParseError` (Lines 24–34)
Three-tier error type following `Ingestion_Diagnostics.md`:

| Severity | Meaning | Quarantine? |
| :--- | :--- | :--- |
| `ERROR` | Identity failure (BIN broken) | ✅ Yes |
| `WARN` | Attribute failure (BBL broken) | ❌ No |
| `INFO` | BIN accepted with flag (temp/dummy) | ❌ No |

### `BblCache` (Line 37)
```rust
pub type BblCache = HashMap<Bbl, BblEvidence>;
```

---

## Functions

### `build_bbl_cache()` (Lines 39–61)
```rust
pub fn build_bbl_cache<R: std::io::Read>(reader: R) -> Result<BblCache, csv::Error>
```
**Phase 1.** Parses `bbl.txt` into a `HashMap<Bbl, BblEvidence>`:
- For each row, attempts to parse a valid `Bbl` via `record.get_bbl()`.
- Extracts condo flag, billing BBL, and lot range as optional evidence.
- Skips rows with unparseable BBLs (silently — these are not buildings of interest).

---

### `process_adr_and_tiebreak()` (Lines 63–190)
```rust
pub fn process_adr_and_tiebreak<R: std::io::Read>(
    reader: R,
) -> Result<(Vec<TieBreakerResult>, Vec<ParseError>), csv::Error>
```
**Phase 2.** The core pipeline function. Two stages:

#### Stage A: Row Processing (Lines 81–158)
For each CSV row:

1. **BIN Validation** (Lines 88–132):
   - `None` → `ERROR / BIN_MISSING` (quarantine + skip)
   - Invalid → `ERROR / BIN_INVALID_FORMAT` or `BIN_ALL_ZEROS_AFTER_BOROUGH` (quarantine + skip)
   - Valid with 2nd digit `9` → `INFO / BIN_TEMP_GSS` (accepted, flagged)
   - Valid with 2nd digit `8` → `INFO / BIN_DOB_DUMMY` (accepted, flagged)

2. **BBL Validation** (Lines 134–157):
   - Valid → tallied into `HashMap<Bin, HashMap<Bbl, usize>>`
   - Invalid → `WARN` with specific reason code (row NOT skipped — BIN still valid)

#### Stage B: Tie-Breaking (Lines 170–187)
```rust
candidates.sort_by(|a, b| {
    b.1.cmp(a.1).then_with(|| a.0.0.cmp(&b.0.0))
});
```
For each BIN:
1. Collect all BBLs and their frequency counts.
2. Flag `is_anomalous = true` if multiple BBLs exist.
3. Sort by **frequency descending**, then **BBL string ascending** (deterministic tiebreak).
4. Select the winning BBL as `primary_bbl`.

---

## Design Decisions

| Decision | Rationale |
| :--- | :--- |
| Generic `R: std::io::Read` | Enables unit testing with `Cursor<String>` instead of real files |
| WARN doesn't skip row | A bad BBL shouldn't discard a valid BIN — the building can still be created |
| Deterministic secondary sort | Ensures repeatable results when two BBLs tie on frequency |
