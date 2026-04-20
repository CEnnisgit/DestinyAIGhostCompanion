# Pipeline C: Geoclient Verification (TODO)

## Context
Pipeline A (PAD Bootstrap) and Pipeline B (Program Roster Import) are completed.
Pipeline C is deferred until further notice.

## Goal
Fill “canonical fields” that are unsafe to infer from PAD/rosters using Geoclient.

## Inputs
* A set of Buildings requiring verification.
* A Geoclient lookup method (preferred: `bin` endpoint by BIN).

## Outputs
Writes canonical fields to `buildings`:
1. **Canonical Address:** `buildings.address` from Geoclient-returned address components.
2. **Community District:** `communityDistrict` from Geoclient fields.
3. **DOF Building Class:** `dofBuildingClass.code` from `rpadBuildingClassificationCode`.
4. **Condo verification + Billing BBL:**
   - If `condominiumFlag == 'C'`:
     - Set `condo.status = CONDO_CONFIRMED`
     - Read `condominiumBillingBbl`:
       - If `0000000000`, set `condoBillingBblMissing = true` and `billingBbl = null`.
       - Else set `billingBbl = condominiumBillingBbl` and `condoBillingBblMissing = false`.
   - Else:
     - Set `condo.status = NOT_CONDO_CONFIRMED`
     - Ensure `billingBbl = null` and `condoBillingBblMissing = false`.

## Constraints
* Do **NOT** overwrite `primaryBbl` (it is PAD-authoritative).
* If Geoclient-derived BBL differs from `primaryBbl`, log anomaly `PRIMARY_BBL_DIFFERS_FROM_GEOCLIENT_BBL`.

## Required Anomaly Types
- `PRIMARY_BBL_DIFFERS_FROM_GEOCLIENT_BBL`
- `CONDO_CONFIRMED_BILLING_BBL_ALL_ZEROES`
- `GEOCLIENT_NOT_FOUND`
- `GEOCLIENT_RETURN_CODE_WARNING`
