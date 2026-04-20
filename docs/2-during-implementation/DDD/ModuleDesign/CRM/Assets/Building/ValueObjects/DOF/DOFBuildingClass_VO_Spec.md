# DOFBuildingClass Value Object Specification

**Module:** CRM
**Parent Aggregate:** Building
**Role:** NYC DOF Building Classification (not Tax Class)
**Source:** Geoclient v2 `rpadBuildingClassificationCode` (preferred) or DOB Roster
**Version:** 1.2.0
**Status:** Approved

---

## 1. Purpose

- Represents the **Department of Finance (DOF) Building Classification** (e.g., `R0`, `GW`, `C1`).
- Enables segmentation, search, and reporting logic.
- Distinguishes clearly from "Tax Class" (1-4).

## 2. Pure DOF Policy

> [!IMPORTANT]
> **Pure DOF Only:** This VO stores **only** DOF building classification codes as defined by the [NYC Department of Finance](https://www.nyc.gov/assets/finance/jump/hlpbldgcode.html). Do NOT store PLUTO summary codes in this field.

### Why "Pure DOF" Matters

PLUTO uses a different code system that includes **condo summary codes** (RM, RD, RI, RX, RZ, RC) created by NYC Planning for billing lots. These are operationally meaningful but are **not DOF codes**. Mixing systems in a field named "DOFBuildingClass" creates semantic ambiguity.

**Pure means:** The code stored comes from one specific code system (DOF), and nothing else is allowed to masquerade as that system.

### If PLUTO Enrichment is Needed Later

Create a separate `PlutoBuildingClass` VO. Do not mix systems in this field.

### Source Context Requirement

> [!NOTE]
> **Parser must know source.** The parser cannot distinguish a PLUTO code from a DOF code by format alone (both are 2-char). The calling code must pass source context:
> ```typescript
> DOFBuildingClass.fromGeoclient(code)  // ✓ Allowed
> DOFBuildingClass.fromPLUTO(code)      // ✗ Throws - use PlutoBuildingClass
> ```

## 3. Canonical Representation

- **Canonical identifier:** `code`
- **Denormalized display:** `description?` (optional, not used for equality/logic)
- **Canonical string/key form:** The `code` (e.g., "R0").
- **Equality rule:** Exact match on the *normalized* code.

## 4. Shape

```typescript
// Canonical serialized shape (no methods)
export interface DOFBuildingClass {
  code: string;        // Never null within VO (VO may be omitted on Building)
  description?: string; // Descriptive text
}
```

## 5. Invariants (Validation Rules)

- [ ] **Strict Existence:** This VO **CANNOT** exist without a valid `code`. If `code` is missing/invalid, the VO instance itself must be `undefined` (omitted) on the parent Aggregate.
- [ ] **Code Format:** Code must match regex `^[A-Z][A-Z0-9]$` (Two characters: First is A-Z, Second is A-Z or 0-9).
- [ ] **Pure DOF Enforcement:** Code must pass one of:
  - **DOF Allowlist (preferred):** Membership check against DOF allowlist (see Section 5.1)
  - **PLUTO Blocklist (fallback):** PLUTO condo summary blocklist (see Section 5.2)

### 5.1 DOF Code Allowlist (Recommended)

Validate against the official DOF building class categories. First character determines category:

| Category | First Char | Valid Second Chars | Description |
| --- | --- | --- | --- |
| One Family Dwellings | `A` | `0-9` | Cape Cod, Colonial, etc. |
| Two Family | `B` | `1-3, 9` | Two-family homes |
| Walk-Up Apartments | `C` | `0-9` | Walk-up residential |
| Elevator Apartments | `D` | `0-9` | Elevator residential |
| Warehouses | `E` | `1-9` | Storage/warehouse |
| Factory/Industrial | `F` | `1-9` | Manufacturing |
| Garages | `G` | `0-9, A-W` | Parking/garage |
| Hotels | `H` | `1-9, A-Z` | Hotels/motels |
| Hospitals | `I` | `1-9` | Healthcare facilities |
| Theatres | `J` | `1-9` | Entertainment |
| Stores | `K` | `1-9` | Retail |
| Lofts | `L` | `1-9` | Loft buildings |
| Churches | `M` | `1-9` | Religious |
| Asylums | `N` | `1-9` | Institutional |
| Offices | `O` | `1-9` | Office buildings |
| Indoor Recreation | `P` | `1-9` | Recreation |
| Outdoor Recreation | `Q` | `0-9` | Parks/outdoor |
| **Condos** | `R` | **`0-9` only** | Condo classes (R0-R9) |
| Residence Multi-Use | `S` | `0-9` | Mixed residential |
| Transportation | `T` | `1-9` | Transit facilities |
| Utility | `U` | `1-9` | Utilities |
| Vacant Land | `V` | `0-9` | Vacant |
| Educational | `W` | `1-9` | Schools |
| Government | `Y` | `1-9` | City/govt buildings |
| Miscellaneous | `Z` | `1-9` | Other |

### 5.2 PLUTO Condo Summary Blocklist (Fallback)

If full allowlist isn't implemented, at minimum block known PLUTO-only codes:

```typescript
const PLUTO_CONDO_SUMMARY_CODES = ['RC', 'RD', 'RI', 'RM', 'RX', 'RZ'];

function isPlutoSummaryCode(code: string): boolean {
  return PLUTO_CONDO_SUMMARY_CODES.includes(code.toUpperCase());
}

// Validation rule
if (isPlutoSummaryCode(code)) {
  return Failure('PLUTO_SUMMARY_CODE_NOT_ALLOWED');
}
```

**Why this works for condos:** All PLUTO condo summary codes follow the pattern `R[A-Z]` (R + letter). Official DOF condo codes are `R[0-9]` (R + digit). So the rule is:

> **If code starts with `R`, second character must be `0-9`.**

```typescript
if (code[0] === 'R' && !/[0-9]/.test(code[1])) {
  return Failure('PLUTO_CONDO_SUMMARY_CODE_NOT_DOF');
}
```

## 6. Normalization Rules (Parsing / Import)

- Input accepted: Separate fields only (`code`, `description`).
- Steps:
  1. **Trim:** Trim whitespace from code and description.
  2. **Uppercase:** Uppercase the code (`"gw"` -> `"GW"`).
  3. **Validate Format:** Check against `^[A-Z][A-Z0-9]$`.
  4. **Validate Pure DOF:** Check against allowlist OR blocklist.
  5. **Decision:** 
     - **If Valid:** Create VO `{ code: "GW", ... }`.
     - **If Invalid/Missing:** **OMIT** the VO entirely. Log anomaly. Do NOT fail the import.

## 7. Derived Properties

- `categoryLetter` = The first letter of the code (index 0).
- `isCondoClass` = `categoryLetter === 'R'` (R0-R9 are condo-related codes).
- Notes: Safe to compute because VO only exists if code is valid.

## 8. Null / Unknown Policy

- Allowed to be missing? **Yes**.
- If missing:
  - Represent as: `undefined` (Parent Aggregate field is empty).
  - Meaning in domain: The source data was missing or invalid.

## 9. Serialization

- JSON: `{ "code": "GW", "description": "GARAGES" }`
- DB columns: `dof_building_class_code`, `dof_building_class_description`.

## 10. Persistence Mapping

| Domain Field | DB Column | Type | Notes |
| --- | --- | --- | --- |
| `code` | `dof_building_class_code` | TEXT | Primary storage. Indexed. Nullable in DB (if VO is missing). |
| `description` | `dof_building_class_description` | TEXT | Display only. |

## 11. Examples

- Valid:
  - `{ code: "R0", description: "CONDOMINIUMS" }`
  - `{ code: "GW" }`
  - `{ code: "gw" }` (Normalizes to `{ code: "GW" }`)

- Resulting in Omission (No VO created):
  - Input `{ code: "12" }` -> Result: `undefined` (Invalid format)
  - Input `{ code: "" }` -> Result: `undefined` (Missing)
  - Input `{ code: "Office" }` -> Result: `undefined` (Invalid format)
  - Input `{ code: "RM" }` -> Result: `undefined` + anomaly (PLUTO summary code, not DOF)
  - Input `{ code: "RD" }` -> Result: `undefined` + anomaly (PLUTO summary code, not DOF)

## 12. Edge Cases

- **Invalid Codes in Import:** We prefer to have *no* classification rather than a *broken* classification.
- **Letter Codes:** Codes like "GW", "CC" are valid DOF codes.
- **R0 and Condo Status:** `R0` (Special Condominium Billing Lot) may correlate with condo status, but does NOT determine it. Use `condo.status` for condo truth.

## 13. Non-goals

- **LL152 Obligation:** Use `ComplianceObligation` aggregate.
- **Tax Rate Logic:** Use Tax Class.
- **PLUTO Codes:** Use separate `PlutoBuildingClass` VO if needed.
- **Condo Determination:** Use `condo.status` (Geoclient condo flag is the oracle, not building class).

## 14. Open Questions

- None.
