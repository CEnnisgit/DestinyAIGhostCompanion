# CondoStatus Value Object Specification

**Module:** CRM
**Parent Aggregate:** Building
**Role:** Condo verification truth state (Geoclient-authoritative)
**Source:** Geoclient v2 (explicit condo flag)
**Version:** 1.3.0
**Status:** Draft

---

## 1. Purpose

- Represents the **verified condo status** of a building as determined by Geoclient.
- Enables "never wrong" condo handling by using explicit signals, not heuristics.
- Supports safe condo-aware UX (grouping, contact guidance) only when verified.

## 2. Canonical Representation

- **Canonical field:** `status` (enum)
- **Equality rule:** Exact match on status value.

## 3. Shape

```typescript
// Condo Status (tri-state)
export type CondoStatusValue = 
  | 'UNKNOWN'           // Not yet verified
  | 'CONDO_CONFIRMED'   // Geoclient says YES
  | 'NOT_CONDO_CONFIRMED'; // Geoclient says NO

// Evidence of how status was determined (Expanded Vocabulary)
export type CondoStatusEvidence = 
  | 'NONE'                              // Default for UNKNOWN
  | 'GEOCLIENT_CONDO_FLAG_C'            // Explicit "C" flag
  | 'GEOCLIENT_BILLING_BBL_PRESENT'     // Billing BBL present (no "C" flag)
  | 'GEOCLIENT_BILLING_BBL_ZERO_SENTINEL' // Explicit "0000000000" (Confirmed Not Condo)
  | 'GEOCLIENT_RESPONSE_UNCLEAR';       // Anomaly (ambiguous or missing fields)

export interface CondoStatus {
  status: CondoStatusValue;
  evidence: CondoStatusEvidence;
}
```

## 4. Invariants (Validation Rules)

* [ ] **Status Values:** Must be one of the three defined values.
* [ ] **Evidence Alignment:**
  * If `status = UNKNOWN`, then `evidence` MUST be `NONE` (or `GEOCLIENT_RESPONSE_UNCLEAR` if ambiguous).
  * If `status ∈ {CONDO_CONFIRMED, NOT_CONDO_CONFIRMED}`, then `evidence` MUST be one of the explicit GEOCLIENT types.

> [!IMPORTANT]
> **Never Wrong Rule:** Condo truth is set ONLY by explicit signals. `CONDO_CONFIRMED` requires `condominiumFlag="C"` or valid billing BBL. `NOT_CONDO_CONFIRMED` requires explicit **billing BBL zero sentinel** (`0000000000`). Absence of fields results in `UNKNOWN`. Heuristics (lot ranges, building class) may log anomalies but **never** set these truth values.

## 5. Factory Methods

### `CondoStatus.unknown()`
Returns default state for newly imported buildings:
- `status = UNKNOWN`
- `evidence = NONE`

### `CondoStatus.fromGeoclientResult(...)`
Creates verified status based on explicit fields:

1. **Flag="C"** → `status: CONDO_CONFIRMED`, `evidence: GEOCLIENT_CONDO_FLAG_C`
2. **Billing BBL present & non-zero** → `status: CONDO_CONFIRMED`, `evidence: GEOCLIENT_BILLING_BBL_PRESENT`
3. **Billing BBL = "0000000000"** → `status: NOT_CONDO_CONFIRMED`, `evidence: GEOCLIENT_BILLING_BBL_ZERO_SENTINEL`
4. **Both absent** → `status: UNKNOWN`, `evidence: NONE` (Wait for data)
5. **Ambiguous** → `status: UNKNOWN`, `evidence: GEOCLIENT_RESPONSE_UNCLEAR`

## 6. Derived Properties

### `isVerified(): boolean`
Returns `true` if `status !== 'UNKNOWN'`.

### `isCondo(): boolean | undefined`
- If `CONDO_CONFIRMED` → `true`
- If `NOT_CONDO_CONFIRMED` → `false`
- If `UNKNOWN` → `undefined`

## 7. Null / Unknown Policy

* **At import:** All buildings start as `UNKNOWN` with `evidence = NONE`.
* **After Pipeline D:** Buildings transition to verified status.
* **UX Rule:** Only show condo-specific features when `isVerified() = true`.

## 8. Serialization

* **JSON:** `{ "status": "CONDO_CONFIRMED", "evidence": "GEOCLIENT_CONDO_FLAG_C" }`
* **DB columns:** `condo_status`, `condo_status_evidence`

## 9. Persistence Mapping

| Domain Field | DB Column | Type | Notes |
| ------------ | --------- | ---- | ----- |
| `status` | `condo_status` | TEXT | `UNKNOWN`, `CONDO_CONFIRMED`, `NOT_CONDO_CONFIRMED` |
| `evidence` | `condo_status_evidence` | TEXT | See ENUM list above |

## 10. Examples

* **Newly imported:** `{ status: 'UNKNOWN', evidence: 'NONE' }`
* **Verified (Flag):** `{ status: 'CONDO_CONFIRMED', evidence: 'GEOCLIENT_CONDO_FLAG_C' }`
* **Verified (Billing Lots):** `{ status: 'CONDO_CONFIRMED', evidence: 'GEOCLIENT_BILLING_BBL_PRESENT' }`
* **Verified Non-Condo:** `{ status: 'NOT_CONDO_CONFIRMED', evidence: 'GEOCLIENT_BILLING_BBL_ZERO_SENTINEL' }`

## 11. Edge Cases

### Geoclient Returns Condo But Billing BBL is Zeros
This is a known edge case during condo conversion. The Building aggregate handles this via:
- `condoStatus = CONDO_CONFIRMED` (status is certain)
- `billingBbl = null` (BBL not available)
- `condoBillingBblMissing = true` (explicit flag for UX)

### Pipeline D Verification Failure
If Geoclient call fails (rate limit, network, etc.):
- `condoStatus` remains `UNKNOWN`
- `condo_verify_last_error_code` is set
- `condo_verify_attempt_count` is incremented
- Will be retried in weekly backstop run

## 12. Non-goals

* **Heuristic Detection:** We do NOT infer condo status from lot ranges (75xx) or building class (R0).
* **PLUTO-based Truth:** PLUTO is for enrichment, not condo oracle.
* **Manual Override:** No user-editable condo status (always Geoclient truth).

## 13. Open Questions

* None.
