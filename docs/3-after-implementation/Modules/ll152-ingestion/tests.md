# tests.rs — Unit Test Suite

> Source: [`apps/ll152-ingestion/src/tests.rs`](file:///c:/github/pcd/apps/ll152-ingestion/src/tests.rs)

## Purpose
Unit tests for `pipeline::process_ll152_row()`. Validates the happy path and all quarantine/error conditions. These are pure logic tests with no database dependency.

---

## Test Cases

### `test_valid_ll152_row_parsing` (Lines 6–30)
**Happy path.** Verifies that a well-formed row produces the correct payload:

| Input | Expected Output |
| :--- | :--- |
| `BIN = 1000003` | `Bin(1000003)` |
| `Subcycle = "Subcycle A"` | `subcycle = "A"` |
| `Deadline = "December 31, 2024"` | `cycle_key = "2024"`, `window_end = Dec 31 2024` |

Also verifies that `window_start` is derived as **January 1** of the cycle year.

---

### `test_missing_bin` (Lines 32–43)
Verifies that a row with `bin: None` produces:
- `severity: "ERROR"`
- `reason_code: "BIN_MISSING"`

---

### `test_invalid_bin_quarantine` (Lines 45–57)
Uses `BIN = 1000000` (all zeros after borough digit).
Verifies:
- `severity: "ERROR"`
- `reason_code: "BIN_ALL_ZEROS_AFTER_BOROUGH"`

---

### `test_invalid_subcycle` (Lines 59–69)
Uses `Subcycle = "Subcycle E"` (not in A/B/C/D).
Verifies:
- `severity: "ERROR"`
- `reason_code: "LL152_INVALID_SUBCYCLE"`

---

### `test_invalid_deadline` (Lines 72–83)
Uses `Deadline = "Not a date"`.
Verifies:
- `severity: "ERROR"`
- `reason_code: "LL152_INVALID_DEADLINE"`

---

## Coverage Summary

| Scenario | Reason Code | Covered |
| :--- | :--- | :--- |
| Valid row | — | ✅ |
| Missing BIN | `BIN_MISSING` | ✅ |
| Invalid BIN (all-zeros) | `BIN_ALL_ZEROS_AFTER_BOROUGH` | ✅ |
| Invalid BIN (out-of-range) | `BIN_INVALID_FORMAT` | ❌ Not yet |
| Invalid subcycle | `LL152_INVALID_SUBCYCLE` | ✅ |
| Invalid deadline | `LL152_INVALID_DEADLINE` | ✅ |
| Excel deserialize failure | `EXCEL_DESERIALIZE_ERROR` | ❌ Not yet |
