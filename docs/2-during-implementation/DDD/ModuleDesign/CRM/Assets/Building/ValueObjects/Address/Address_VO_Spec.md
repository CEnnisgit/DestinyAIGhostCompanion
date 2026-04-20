# Address Value Object Specification

**Module:** CRM
**Parent Aggregate:** Building
**Role:** Primary physical street address (if one exists)
**Source:** DOB roster / PAD / Geoclient (Geosupport)
**Version:** 1.1.0
**Status:** Approved

---

## 1. Purpose
- Represents the **primary street address** for dispatch and display.
- Stores a normalized, displayable site address for dispatch/UI. Not used as identity.
- Enables mailing lists, routing inspectors, and display on UI.

## 2. Canonical Representation
- **Canonical fields:** `houseNumber`, `streetName`, `borough`, `zipCode?`.
- **Display string:** `fullAddressString` (for UI only).
- **Not a key:** Never use address string for joins/uniqueness.
- **Equality rule:** Exact match of normalized fields (because we normalize on construction).

## 3. Shape
```typescript
// Canonical serialized shape
export interface Address {
  houseNumber: string; // "123-A" or "45-20" (Queens)
  streetName: string;  // "BROADWAY"
  borough: "MANHATTAN" | "BRONX" | "BROOKLYN" | "QUEENS" | "STATEN_ISLAND";
  zipCode?: string;    // Optional. "10001"
}
```

## 4. Invariants (Validation Rules)

* [ ] **houseNumber:** Required, non-empty (trimmed).
* [ ] **streetName:** Required, non-empty (trimmed).
* [ ] **Borough:** Must be valid Enum.
* [ ] **zipCode:** Optional. If present, must be 5 digits. If ZIP+4 provided, normalize to first 5.

## 5. Normalization Rules (Parsing / Import)

* Input accepted: Raw strings.
* Steps:
  1. **Trim:** Trim all fields.
  2. **Uppercase:** Uppercase Street, House Number.
  3. **Collapse Whitespace:** Normalize internal whitespace.
  4. **Queens Hyphens:** Preserve Queens hyphenated house numbers exactly (e.g. "45-20"). DO NOT split on "-".
  5. **Preserve Punctuation:** Keep internal punctuation as-is (e.g., "123-A", "45-20"). Do not strip `-` or letters.
  6. **ZIP Normalization:** If ZIP+4 provided ("10001-1234"), extract first 5 digits.

## 6. Derived Properties

* `fullAddressString`:
  * If zipCode present: `${houseNumber} ${streetName}, ${borough}, NY ${zipCode}`
  * If zipCode missing: `${houseNumber} ${streetName}, ${borough}, NY`

## 7. Null / Unknown Policy

* The Address VO is **strict**: it cannot be partially filled.
* The parent **Building aggregate may omit Address** in rare NYC cases (NAUBs / unresolved records).
* Any workflow that requires routing/dispatch **must require Address** (or a separately modeled PlaceName) at the job layer.

## 8. Serialization

* JSON: `{ "houseNumber": "123", "streetName": "BROADWAY", "borough": "MANHATTAN" }`
* DB columns: `house_number`, `street_name`, `borough`, `zip_code`.

## 9. Persistence Mapping

| Domain Field | DB Column | Type | Notes |
| ------------ | --------- | ---- | ----- |
| `houseNumber`| `house_number` | TEXT | Nullable at DB level |
| `streetName` | `street_name`  | TEXT | Nullable at DB level |
| `borough`    | `borough`      | TEXT | Stores enum token (e.g. "STATEN_ISLAND", not "Staten Island") |
| `zipCode`    | `zip_code`     | VARCHAR(5) | Nullable |

## 10. Examples

* Valid:
  * `{ houseNumber: "123", streetName: "BROADWAY", borough: "MANHATTAN", zipCode: "10012" }`
  * `{ houseNumber: "45-20", streetName: "23RD STREET", borough: "QUEENS" }` (No ZIP)

* Invalid:
  * `{ streetName: "BROADWAY", borough: "MANHATTAN" }` (Missing houseNumber)
  * `{ houseNumber: "123", borough: "Gotham" }` (Invalid Borough)

## 11. Edge Cases

* **Queens Hyphens:** "45-20" is a single House Number. Both sides together are meaningful; DO NOT split.
* **Place Names:** Place names (e.g., "EMPIRE STATE BUILDING", "One Bryant Park") are **not** modeled as Address. They are handled by the identity resolution/search layer (Geoclient PLACE search) and only stored as Address after resolution to a street address.
* **NAUBs:** Buildings with No Address and Unidentifiable by Building name exist in NYC. These have a BIN but no Address VO.

## 12. Non-goals

* **Geocoding:** Does not store Lat/Long. That is a separate GIS concern.
* **Place/Building Name Resolution:** This VO only stores resolved street addresses, not search inputs.

## 13. Open Questions

* None.
