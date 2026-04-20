# tests.rs — Unit Test Suite

> Source: [`apps/pad-ingestion/src/tests.rs`](file:///c:/github/pcd/apps/pad-ingestion/src/tests.rs)

## Purpose
Unit tests for the `Bin` VO, `Bbl` VO, and `pipeline::process_adr_and_tiebreak()`. All tests are pure logic with no database dependency, using in-memory CSV via `std::io::Cursor`.

---

## BIN Validation Tests (Lines 8–61)

| Test | Scenario | Expected |
| :--- | :--- | :--- |
| `test_bin_valid_boroughs` | Boroughs 1–5, non-zero suffix | `is_valid() == true` |
| `test_bin_invalid_borough_range` | Boroughs 0, 6–9 | `is_valid() == false` |
| `test_bin_all_zeros_after_borough_rejected` | `X000000` pattern | `is_valid() == false`, reason = `BIN_ALL_ZEROS_AFTER_BOROUGH` |
| `test_bin_too_small` | Values < 1,000,000 | `is_valid() == false` |
| `test_bin_soft_warnings` | 2nd digit 9 or 8 | `is_valid() == true`, `warning_code()` returns `BIN_TEMP_GSS` or `BIN_DOB_DUMMY` |

---

## BBL Validation Tests (Lines 63–119)

| Test | Scenario | Expected |
| :--- | :--- | :--- |
| `test_bbl_valid` | Pre-padded components | `Bbl("1001230045")` |
| `test_bbl_valid_unpadded` | Unpadded components | Same canonical output |
| `test_bbl_borough_invalid` | Borough 0 or 6+ | `None`, reason = `BBL_BOROUGH_UNRECOGNIZED` |
| `test_bbl_block_zero_rejected` | Block = 0 | `None` |
| `test_bbl_lot_zero_rejected` | Lot = 0 | `None` |
| `test_bbl_empty_components_rejected` | Empty strings | `None`, reason = `BBL_MISSING` |
| `test_bbl_non_numeric_rejected` | Letters in components | `None`, reason = `BBL_NON_NUMERIC` |

---

## Pipeline Integration Tests (Lines 121–218)

### `test_tiebreaker_picks_most_frequent_bbl` (Lines 125–142)
Feeds 4 rows: 3 with BBL `1-1-1` and 1 with BBL `1-2-10` for the same BIN.
- Verifies the most-frequent BBL (`1000010001`) wins.
- Verifies `is_anomalous == true` (multi-BBL BIN).
- Verifies no non-INFO parse errors.

### `test_invalid_bin_generates_error_severity` (Lines 144–175)
Feeds 3 rows with broken BINs:
- `1000000` → `BIN_ALL_ZEROS_AFTER_BOROUGH` (ERROR + quarantine)
- `6000001` → `BIN_INVALID_FORMAT` (ERROR + quarantine)
- Empty BIN → `BIN_MISSING` (ERROR + quarantine)

Verifies no buildings are created and all errors carry `raw_row` for quarantine.

### `test_invalid_bbl_generates_warn_severity` (Lines 177–197)
Feeds a row with valid BIN but invalid BBL (borough 0).
- Verifies WARN severity, not ERROR.
- Verifies `raw_row == None` (WARN = no quarantine).

### `test_temp_bin_generates_info_warning` (Lines 199–218)
Feeds a row with temporary BIN (`1900001`, 2nd digit = 9).
- Verifies building IS created (temp BINs are accepted).
- Verifies INFO-level warning with code `BIN_TEMP_GSS`.
- Verifies `raw_row == None` (INFO = no quarantine).

---

## Coverage Summary

| Scenario | Covered |
| :--- | :--- |
| Bin: Valid boroughs 1–5 | ✅ |
| Bin: Invalid boroughs 0, 6–9 | ✅ |
| Bin: All-zeros-after-borough | ✅ |
| Bin: Too small values | ✅ |
| Bin: Soft warnings (temp/dummy) | ✅ |
| BBL: Valid (padded + unpadded) | ✅ |
| BBL: Invalid borough | ✅ |
| BBL: Zero block/lot | ✅ |
| BBL: Empty components | ✅ |
| BBL: Non-numeric | ✅ |
| Pipeline: Tie-breaking (most frequent wins) | ✅ |
| Pipeline: Anomaly detection (multi-BBL) | ✅ |
| Pipeline: ERROR severity for bad BINs | ✅ |
| Pipeline: WARN severity for bad BBLs | ✅ |
| Pipeline: INFO severity for temp BINs | ✅ |
| DB: flush_buildings | ❌ Requires integration test |
| DB: flush_addresses_streaming | ❌ Requires integration test |
