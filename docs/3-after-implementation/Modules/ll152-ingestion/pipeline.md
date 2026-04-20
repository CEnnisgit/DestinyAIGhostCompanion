# pipeline.rs — Domain Transformation Logic

> Source: [`apps/ll152-ingestion/src/pipeline.rs`](file:///c:/github/pcd/apps/ll152-ingestion/src/pipeline.rs)

## Purpose
Pure domain logic for transforming raw Excel rows into strongly typed `ComplianceObligationPayload` structs. This module contains **no I/O** — it validates, extracts, and calculates.

---

## `process_ll152_row()` (Lines 6–86)

**Signature:**
```rust
pub fn process_ll152_row(
    index: usize,
    raw: Ll152ExcelRow,
    program_code: &str,
) -> Result<ComplianceObligationPayload, ParseError>
```

### Step-by-step Walkthrough

#### 1. Preserve Raw Data (Line 12)
```rust
let raw_json = serde_json::to_value(&raw).unwrap();
```
Serializes the raw row to JSON **before** any fields are moved out. This ensures the quarantine system always has the original data, even after field ownership transfers.

#### 2. BIN Validation (Lines 14–36)
```rust
let bin_val = match raw.bin {
    Some(b) => Bin(b),
    None => return Err(ParseError { reason_code: "BIN_MISSING", ... }),
};
if !bin_val.is_valid() {
    return Err(ParseError { reason_code: bin_val.rejection_reason(), ... });
}
```
- **Missing BIN** → `BIN_MISSING` error.
- **Invalid BIN** → delegates to `Bin::rejection_reason()` which returns either `BIN_ALL_ZEROS_AFTER_BOROUGH` or `BIN_INVALID_FORMAT`.

#### 3. Subcycle Extraction (Lines 38–49)
```rust
let subcycle = subcycle_raw.replace("Subcycle ", "").trim().to_string();
if !["A", "B", "C", "D"].contains(&subcycle.as_str()) {
    return Err(ParseError { reason_code: "LL152_INVALID_SUBCYCLE", ... });
}
```
- Strips the `"Subcycle "` prefix from values like `"Subcycle A"`.
- Validates the result is one of the four legal subcycles: **A, B, C, D**.

#### 4. Deadline Parsing & Window Calculation (Lines 51–74)
```rust
let window_end = NaiveDate::parse_from_str(deadline_raw.trim(), "%B %d, %Y")?;
let cycle_year = window_end.year();
let window_start = NaiveDate::from_ymd_opt(cycle_year, 1, 1)...;
```
- Parses the deadline string (e.g., `"December 31, 2024"`) using the `%B %d, %Y` format.
- Derives `cycle_year` from the parsed date.
- Calculates `window_start` as **January 1** of the cycle year per LL152 schedule rules (§4.3).

#### 5. Payload Construction (Lines 76–85)
Returns a `ComplianceObligationPayload` with `building_id: None` — this is intentionally deferred to the DB phase where the building is resolved or stubbed.

---

## Design Decisions

| Decision | Rationale |
| :--- | :--- |
| No I/O in this module | Keeps transformation pure and easily testable |
| `building_id: None` | Separation of concerns: building resolution is a DB responsibility |
| Raw JSON preserved first | Guarantees quarantine data integrity even if Rust ownership moves fields |
