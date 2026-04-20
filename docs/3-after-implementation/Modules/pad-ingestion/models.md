# models.rs — Domain Types

> Source: [`apps/pad-ingestion/src/models.rs`](file:///c:/github/pcd/apps/pad-ingestion/src/models.rs)

## Purpose
Defines the strongly typed domain models for the PAD Bootstrap pipeline. Contains both Value Objects (`Bin`, `Bbl`) and CSV deserialization structs for the PAD data files.

---

## Value Objects

### `Bin` — 7-digit Building Identification Number (Lines 4–51)
```rust
pub struct Bin(pub u32);
```
Exactly the same as in `ll152-ingestion`, but with an additional `warning_code()` method for soft warnings.

#### `is_valid()` (Lines 18–23)
Same invariants as LL152: borough 1–5, non-zero suffix.

#### `warning_code()` (Lines 27–34)
Returns soft warnings per `BIN_VO_Spec.md §5`:

| 2nd Digit | Warning Code | Meaning |
| :--- | :--- | :--- |
| `9` | `BIN_TEMP_GSS` | Temporary BIN, will be replaced by Geosupport |
| `8` | `BIN_DOB_DUMMY` | DOB-only BIN, not valid in Geosupport |

#### `rejection_reason()` (Lines 38–44)
Same as LL152: returns `BIN_ALL_ZEROS_AFTER_BOROUGH` or `BIN_INVALID_FORMAT`.

---

### `Bbl` — 10-digit Borough-Block-Lot (Lines 53–148)
```rust
pub struct Bbl(pub String);
```
A newtype wrapper around the canonical 10-digit string representation (e.g., `"1001230045"`).

#### `Bbl::new()` (Lines 66–103)
Factory constructor that validates and formats from component strings:

| Validation | Rule |
| :--- | :--- |
| Borough | Must be 1–5 |
| Block | Must be 1–99999 |
| Lot | Must be 1–9999 |
| Sentinel | `"0000000000"` is rejected |
| Format | `format!("{}{:05}{:04}", boro, block, lot)` |

Returns `None` if any invariant fails. Accepts both padded (`"00123"`) and unpadded (`"123"`) inputs.

#### `Bbl::rejection_reason()` (Lines 107–141)
Static method that determines the specific reason code for a BBL parse failure:

| Code | Condition |
| :--- | :--- |
| `BBL_MISSING` | Any component is empty |
| `BBL_BOROUGH_UNRECOGNIZED` | Borough outside 1–5 |
| `BBL_NON_NUMERIC` | Non-numeric component |
| `BBL_BLOCK_INVALID` | Block is 0 or > 99999 |
| `BBL_LOT_INVALID` | Lot is 0 or > 9999 |
| `PAD_BBL_PARSE_ERROR` | Catch-all fallback |

---

## CSV Deserialization Structs

### `PadAdrRow` — Address Range Record (Lines 151–174)
```rust
pub struct PadAdrRow {
    pub boro: String,
    pub block: String,
    pub lot: String,
    pub bin: String,
    pub lhnd: String,   // Low house number
    pub hhnd: String,   // High house number
    pub stname: String,  // Street name
    pub lhns: String,   // Low house number sort
    pub hhns: String,   // High house number sort
    pub addrtype: String,
    pub parity: String,
}
```
Deserialized directly from `adr.txt`. All fields are `String` since PAD CSV data is whitespace-padded. Helper methods:
- `get_bin()` → `Option<Bin>` (trims + parses)
- `get_bbl()` → `Option<Bbl>` (delegates to `Bbl::new()`)

### `PadBblRow` — BBL Evidence Record (Lines 177–198)
```rust
pub struct PadBblRow {
    pub boro: String,
    pub block: String,
    pub lot: String,
    pub billboro: String,
    pub billblock: String,
    pub billlot: String,
    pub condoflag: String,
    pub lolot: String,
    pub hilot: String,
}
```
Deserialized from `bbl.txt`. Helper methods:
- `get_bbl()` → `Option<Bbl>` (primary BBL)
- `get_billing_bbl()` → `Option<Bbl>` (billing BBL for condos)
