# CommunityDistrict Value Object Specification

**Module:** CRM
**Parent Aggregate:** Building
**Role:** NYC Community District Identifier
**Source:** DOB LL152 Properties; PLUTO/MapPLUTO CD field; DCP Geosupport UPG (Community District (CD) data item)
**Version:** 1.3.0
**Status:** Approved

---

## 1. Purpose
- Unifies NYC Community Districts into a single canonical identity.
- Handles both **NYC community districts (59 total)** and **Joint Interest Areas (12 total)**; district numbers are **1–18 within a borough**, and JIAs use special codes.
- Acts as the join key between disparate datasets (PLUTO, Geosupport, DOB).

## 2. Canonical Representation
- **Canonical Identity:** `boroCD` (3-digit integer).
    - Format: `B` + `NN` (Borough Code + CD/JIA Number).
    - Example: `101` (Manhattan 01), `164` (Manhattan Central Park).
- **Equality rule:** Strict equality of `boroCD`.

## 3. Shape
```typescript
export interface CommunityDistrict {
  // The Source of Truth
  boroCD: number;           // e.g. 101, 164

  // Derived / Convenience
  borough: Borough;         // Derived from 1st digit
  districtNumber: number;   // Derived from last 2 digits
}
```

## 4. Invariants (Validation Rules)

### A. Format & Borough Logic
*   `boroCD` must be a valid, positive, safe integer (`Number.isSafeInteger`).
*   First digit must be a valid Borough Code:
    *   1: Manhattan
    *   2: Bronx
    *   3: Brooklyn
    *   4: Queens
    *   5: Staten Island

### B. Valid Ranges (Strict Allowlist)
To prevent invalid codes (e.g., "Manhattan 99"), `boroCD` must match one of these sets:

1.  **Standard Community Districts (59 Total):**
    *   Manhattan: `101` – `112`
    *   Bronx: `201` – `212`
    *   Brooklyn: `301` – `318`
    *   Queens: `401` – `414`
    *   Staten Island: `501` – `503`

2.  **Joint Interest Areas (JIA) - Exact Allowlist:**
    *   `164` Central Park
    *   `226` Van Cortlandt Park
    *   `227` Bronx Park
    *   `228` Pelham Bay Park
    *   `355` Prospect Park
    *   `356` Brooklyn Gateway National Recreational Area
    *   `480` LaGuardia Airport
    *   `481` Flushing Meadows–Corona Park
    *   `482` Forest Park
    *   `483` JFK International Airport
    *   `484` Queens Gateway National Recreational Area
    *   `595` Staten Island Gateway National Recreational Area

*Note: JIA **codes** are authoritative; JIA **display names** vary slightly between sources (PLUTO vs Geosupport). Treat these names as non-normative labels/aliases.*

*Note: Some areas are legally in one borough but are assigned the community district of the borough that services them. Example: Marble Hill is legally Manhattan but serviced by the Bronx (CD 207/208); Rikers Island is legally Bronx but serviced by Queens (CD 401). This VO stores the authoritative `boroCD` as defined by the source datasets.*

## 5. Factory Methods

### `fromBoroCD(code: number): Result<CommunityDistrict>`
*   **Primary Factory.**
*   Validates `code` against the Ranges/Allowlist above.
*   Derives `borough` (1st digit) and `districtNumber` (last 2 digits).

### `fromSplit(borough: Borough, number: number): Result<CommunityDistrict>`
*   **Adapter Factory.**
*   Computes `boroCD = (boroughCode * 100) + number`.
*   Delegates validation to `fromBoroCD`.

## 6. Domain Helpers

### `ll152SubcycleHint(): 'A'|'B'|'C'|'D'|undefined`
*   **Role:** Non-authoritative hint for UI/QA.
*   **Rule:** SHOULD only return a value if `districtNumber` is **1–18**.
*   **Logic:**
    *   If `districtNumber` in `1, 3, 10` → 'A'
    *   If `districtNumber` in `2, 5, 7, 13, 18` → 'B'
    *   If `districtNumber` in `4, 6, 8, 9, 16` → 'C'
    *   If `districtNumber` in `11, 12, 14, 15, 17` → 'D'
    *   Else (including JIAs) → `undefined`

> **IMPORTANT:** This is a **hint**. Actual LL152 obligations come strictly from the DOB Roster columns.

## 7. Persistence Mapping

| Domain Field | DB Column | Type | Notes |
| ------------ | --------- | ---- | ----- |
| `boroCD` | `cd_full_code` | SMALLINT | Primary storage (optional) |
| `borough` | `cd_borough_code` | SMALLINT | 1-5 (Derived) |
| `districtNumber` | `cd_number` | SMALLINT | Stores 1-18 OR JIA suffixes (e.g. 26-28, 55-56, 64, 80-84, 95) |

*Note: Storing split parts allows easier querying by borough, but app logic should reconstruct the full VO.*

## 8. Test Vectors

*Sources: [Geosupport UPG](https://nycplanning.github.io/Geosupport-UPG/appendices/appendix03/), [PLUTO Data Dictionary](https://www.nyc.gov/assets/planning/download/pdf/data-maps/open-data/pluto_datadictionary.pdf), [DOB LL152 Schedule](https://www.nyc.gov/site/buildings/property-or-business-owner/gas-piping-inspections.page)*

### A) Valid — Full Allowlist (71 total)

**Standard Community Districts (59):**
- Manhattan: `101`–`112`
- Bronx: `201`–`212`
- Brooklyn: `301`–`318`
- Queens: `401`–`414`
- Staten Island: `501`–`503`

**Joint Interest Areas (12):**
`164`, `226`, `227`, `228`, `355`, `356`, `480`, `481`, `482`, `483`, `484`, `595`

### B) Derived Field & LL152 Hint Assertions

| boroCD | borough | districtNumber | ll152SubcycleHint |
|--------|---------|----------------|-------------------|
| `101` | Manhattan | 1 | `'A'` |
| `112` | Manhattan | 12 | `'D'` |
| `207` | Bronx | 7 | `'B'` |
| `318` | Brooklyn | 18 | `'B'` |
| `414` | Queens | 14 | `'D'` |
| `503` | Staten Island | 3 | `'A'` |
| `164` | Manhattan | 64 | `undefined` |
| `483` | Queens | 83 | `undefined` |

**LL152 Hint Mapping (districtNumber 1–18 only):**
- A: 1, 3, 10
- B: 2, 5, 7, 13, 18
- C: 4, 6, 8, 9, 16
- D: 11, 12, 14, 15, 17

### C) Invalid — Exhaustive Suite by Failure Category

**C1) Type / Numeric Integrity (safe integer + positivity):**
- `-101` (negative)
- `0` (non-positive)
- `NaN`, `Infinity`, `-Infinity` (not safe integer)
- `101.1` (not integer)
- `9007199254740992` (2^53, exceeds safe integer)

**C2) Borough Digit Invalid (not 1–5):**
- `601`, `901` (borough 6/9 invalid)
- `1`, `12` (not 3-digit code)

**C3) "District 00" Malformed:**
- `100`, `200`, `300`, `400`, `500` (district 00 invalid)

**C4) Standard Range Boundary Violations:**
- `113`, `199` (Manhattan > 112)
- `213` (Bronx > 212)
- `319` (Brooklyn > 318)
- `415` (Queens > 414)
- `504` (Staten Island > 503)

**C5) JIA Near-Misses (not in allowlist):**
- `165` (near 164)
- `225`, `229` (near 226–228)
- `354`, `357` (near 355–356)
- `485` (near 480–484)
- `594`, `596` (near 595)

**C6) Wrong Borough + JIA Suffix:**
- `264` (Bronx + 64, only 164 is Central Park)
- `495` (Queens + 95, only 595 is valid)
- `580` (SI + 80, only 480 is LGA)

### D) Factory Method Coverage

**fromSplit(borough, number) — Valid:**
- (Manhattan, 1) → `101`
- (Queens, 83) → `483` (JIA)
- (Manhattan, 64) → `164` (JIA)

**fromSplit(borough, number) — Invalid:**
- (Manhattan, 0) → `100` (district 00)
- (Queens, 15) → `415` (above max)
- (Staten Island, 80) → `580` (suffix not allowlisted)
