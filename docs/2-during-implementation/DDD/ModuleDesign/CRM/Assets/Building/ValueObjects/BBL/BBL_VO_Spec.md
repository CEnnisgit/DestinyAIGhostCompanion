# BBL Value Object Specification

**Module:** CRM
**Parent Aggregate:** Building
**Role:** NYC Tax Lot Identifier
**Version:** 2.1.1 (Refined Integer & Sentinel Rules)

---

## 1. Purpose

- Uniquely identifies a parcel of real estate (Borough-Block-Lot).
- Acts as the primary join key for overlays (Ownership, PLUTO).
- **Pure Identifier:** Does not contain classification logic (Condo vs. Air Rights).

## 2. Canonical Representation

- **Fields:** `boroughCode` (1-5), `block` (int), `lot` (int).
- **String Key:** "1-00123-0045" (Standard).
- **10-Digit:** "1001230045" (GIS Join Key).
- **Equality:** Compound equality of all 3 components.

## 3. Domain Interface & API

```typescript
export interface BBL {
  boroughCode: 1 | 2 | 3 | 4 | 5;
  block: number;
  lot: number;
  bblString: string;  // Derived: "1-00123-0045"
  bbl10Digit: string; // Derived: "1001230045"
}
```

### 3.1. Factory Methods

* **`BBL.create({ boroughCode, block, lot })`**:
  * Returns `Result<BBL>`. Fails if invariants violated.
* **`BBL.parse(input)`**:
  * **Precedence:** Checks if input is strictly `"0000000000"` **first**; returns `Failure(Sentinel)`.
  * Returns `Result<BBL>`. Accepts canonical shapes ONLY:
    1. 10-digit string `"1001230045"` (`^[1-5]\d{9}$`)
    2. Formatted string `"1-00123-0045"` (`^[1-5]-\d{5}-\d{4}$`)
    3. Components object `{ boroughCode, block, lot }`
  * **Note:** Does NOT normalize source junk (commas, .0, "STATEN IS"). That is the job of **Adapters** (see `BBL_Source_Adapters.md`).

## 4. Invariants (Validation Rules)

| Rule | Condition | Failure Handling |
| :--- | :--- | :--- |
| **Borough** | Must be 1-5. | Return Failure |
| **Block** | `Number.isSafeInteger(x) && x >= 1`, max 5 digits (`1..99999`). | Return Failure |
| **Lot** | `Number.isSafeInteger(x) && x >= 1`, max 4 digits (`1..9999`). | Return Failure |
| **Sentinel** | Input `0000000000` | Return Failure (Sentinel) |

> **Note on Sentinel:** Geosupport may return a zero-BBL (`0000000000`) in specific condo billing contexts (unavailable data). We treat this as **invalid** for a persistence VO (it is not a real parcel).

> **Diagnostics:** If BBL creation fails (returns `Result.Failure`), the import pipeline should treat this as a **WARN (Anomaly)** and omit the BBL from the Building, logging a specific code (e.g. `BBL_BOROUGH_UNRECOGNIZED`). It should **not** crash the whole import.
>
> *See `../../Ingestion_Diagnostics.md` for details.*
>
> **Reason codes must come from `Ingestion_Diagnostics.md`; do not invent new codes here.**

## 5. Derived Properties

* `bblString` = `${boroughCode}-${pad(block, 5)}-${pad(lot, 4)}`
* `bbl10Digit` = `${boroughCode}${pad(block, 5)}${pad(lot, 4)}`

## 6. Null / Unknown Policy

* **Allowed to be missing?** Yes. (e.g. BIN exists but BBL is bad/unknown).
* **Impact:** No link to PLUTO/Owners if missing.

## 7. Persistence

* JSON: `{ "boroughCode": 1, "block": 123, "lot": 45 }`
* SQL (Embedded): `primary_bbl_borough_code`, `primary_bbl_block`, `primary_bbl_lot`

## 8. Examples

* Valid: `{ 1, 100, 50 }`
* Invalid: `{ 6, 100, 50 }` (Bad Boro)
* Invalid: `{ 1, 0, 50 }` (Bad Block)
* Invalid: `"0000000000"` (Sentinel)
