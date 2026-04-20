# BIN Value Object Specification

**Module:** CRM
**Parent Aggregate:** Building
**Role:** NYC Building Identification Number (Natural Key)
**Source:** DOB / Geosupport / PAD
**Version:** 1.3.0
**Status:** Approved

---

## 1. Purpose

- Uniquely identifies a physical building structure in NYC.
- Acts as the **Root Identity** for the Building Aggregate.
- Widely used across NYC building-related datasets (especially DOB/Geosupport) for building identity.

## 2. Canonical Representation

- **Canonical fields:** `value` (string)
- **Canonical value form:** The 7-digit string (e.g. "1234567").
- **Equality rule:** Exact match on normalized value (trimmed string).

## 3. Shape

```typescript
// Domain shape
export interface BIN {
  value: string; // 7 digits, starts with 1-5
}
```

> **Serialization note:** In code we model BIN as a VO object; at API boundaries we serialize as a plain string.

## 4. Invariants (Hard Validation Rules)

- [ ] **Format:** Must match regex `^[1-5]\d{6}$` (7 digits, first digit 1-5).
- [ ] **No All-Zeros:** Cannot match `^[1-5]0{6}$` (e.g. "1000000" = invalid/empty BIN per PAD/Geosupport).

**Source:** [Geosupport Appendix 1](https://nycplanning.github.io/Geosupport-UPG/appendices/appendix01/) - "A BIN is invalid if the digits beyond the first digit are all zeros."

## 5. Warnings (Soft Validation)

| Pattern | Warning Code | Meaning | Source |
|---------|--------------|---------|--------|
| 2nd digit = `9` | `TEMP_BIN_GSS` | Temporary BIN (will be replaced by GSS) | Geosupport Appendix 1 |
| 2nd digit = `8` | `DOB_DUMMY_BIN` | DOB-only BIN (not valid in Geosupport) | Geosupport Appendix 1 |

These warnings are **application-level flags**, not VO invariants. The BIN is still accepted.

## 6. Normalization Rules (Parsing / Import)

- Input accepted: Raw strings ("1234567"), Numbers (1234567).
- Steps:
  1. **Stringify:** Convert numbers to string.
  2. **Trim:** Remove whitespace.
  3. **No Padding:** DO NOT pad. If input length != 7, reject.

## 6a. System-Level Validation (Optional)

> **Valid format ≠ real building exists.**

- **Offline imports:** Accept format-valid BINs (current behavior). This is pure VO validation.
- **On-demand verification:** Optionally verify via Geoclient/Geosupport Function BN when needed.
  - Geosupport BN call returning "success" = proof the BIN exists.
  - This is application-level, not VO-level.

## 7. Derived Properties

- `boroughCode` = First digit of the BIN (1-5).
- Notes: Guaranteed valid by invariant. Convenience only; do not use for identity resolution.
- **OK for:**
  - Quick UI grouping ("show me all Manhattan buildings").
  - Sanity checks ("BIN borough doesn't match address borough").

## 8. Null / Unknown Policy

- Allowed to be missing? **No**. A Building Aggregate definitionally requires a BIN.
- If missing or invalid: **Do not create Building.** Quarantine row to `import_errors`.

## 9. Serialization

- **Domain:** `class BIN { value: string }`
- **JSON wire format:** `"1234567"` (string)
- **DB:** `bin VARCHAR(7)`

## 10. Persistence Mapping

| Domain Field | DB Column | Type | Notes |
| ------------ | --------- | ---- | ----- |
| `value`      | `bin`     | VARCHAR(7) | Unique Index |

## 11. Examples

- Valid:
  - `"1234567"` (Manhattan)
  - `"4123456"` (Queens)
  - `"1923456"` (Temp BIN → accepted with warning)
  - `"1823456"` (DOB Dummy → accepted with warning)

- Invalid (Hard Reject):
  - `"123"` (Too short)
  - `"A000000"` (Non-numeric)
  - `"6000000"` (Invalid borough prefix)
  - `"1000000"` (All zeros after borough = official "empty/invalid")

## 12. Edge Cases

- **Temporary BINs (2nd digit = 9):** These will be replaced by Geosupport. Accept but flag `TEMP_BIN_GSS`.
- **DOB Dummy BINs (2nd digit = 8):** These exist only in DOB files and are not valid in Geosupport. Accept but flag `DOB_DUMMY_BIN`.
- **Import Quarantine:** If BIN fails hard invariants, do NOT create Building. Route row to `import_errors` for manual review.

## 13. Non-goals

- **Ownership:** BIN does not define ownership (BBL does). Multiple owners can exist for one BIN (Condos).

## 14. Open Questions

- None.
