# models.rs — Domain Types

> Source: [`apps/ll152-ingestion/src/models.rs`](file:///c:/github/pcd/apps/ll152-ingestion/src/models.rs)

## Purpose
Defines the strongly typed domain models used across the pipeline. Contains the `Bin` Value Object, the raw Excel deserialization struct, the database-ready payload, and the error type for quarantine.

---

## Structs & Types

### `Bin` — Value Object (Lines 7–28)
```rust
pub struct Bin(pub u32);
```
A newtype wrapper around `u32` implementing the BIN validation rules from `BIN_VO_Spec.md`.

#### `is_valid()` (Line 11–13)
```rust
self.0 >= 1_000_000 && self.0 <= 5_999_999 && self.0 % 1_000_000 != 0
```
A BIN is valid if:
- It is 7 digits (range `1,000,000` – `5,999,999`), covering NYC boroughs 1–5.
- The trailing 6 digits are **not all zeros** (e.g., `1000000` is invalid).

#### `rejection_reason()` (Lines 15–21)
Returns a static string for the quarantine system:
- `"BIN_ALL_ZEROS_AFTER_BOROUGH"` — a borough-valid prefix but meaningless body.
- `"BIN_INVALID_FORMAT"` — catch-all for out-of-range values.

#### `Display` impl (Lines 24–28)
Formats the BIN as its raw numeric value for logging and SQL binding.

---

### `Ll152ExcelRow` — Raw Input (Lines 31–41)
```rust
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Ll152ExcelRow {
    pub bin: Option<u32>,
    pub subcycle: Option<String>,
    pub cycle_2_deadline: Option<String>,
}
```
Deserialized directly from the Excel sheet via `calamine`'s `RangeDeserializerBuilder`. Uses `serde(rename)` to map to the actual column headers:

| Rust Field | Excel Column |
| :--- | :--- |
| `bin` | `BIN` |
| `subcycle` | `LL152 Subcycle` |
| `cycle_2_deadline` | `Cycle 2 Deadline` |

All fields are `Option` to gracefully handle missing data (which triggers quarantine instead of a panic).

---

### `ComplianceObligationPayload` — Database DTO (Lines 44–58)
```rust
pub struct ComplianceObligationPayload {
    pub building_id: Option<Uuid>,
    pub bin: Bin,
    pub program_code: String,
    pub cycle_key: String,
    pub cycle_year: Option<i32>,
    pub window_start: Option<NaiveDateTime>,
    pub window_end: Option<NaiveDateTime>,
    pub subcycle: String,
}
```
The validated, transformed output of `pipeline::process_ll152_row()`. Key design choice: `building_id` starts as `None` and is populated during the DB phase by `resolve_building_id_or_stub()`.

---

### `ParseError` — Quarantine Record (Lines 61–68)
```rust
pub struct ParseError {
    pub index: usize,
    pub severity: &'static str,
    pub reason_code: &'static str,
    pub message: String,
    pub raw_row: Option<serde_json::Value>,
}
```
Carries all context needed to write a `quarantined_rows` record. Uses `&'static str` for `severity` and `reason_code` since these are always string literals defined at compile time.
