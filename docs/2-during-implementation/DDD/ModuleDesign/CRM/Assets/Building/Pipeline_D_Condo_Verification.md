# Pipeline D: Condo Verification Batch

**Module:** CRM
**Sub-Module:** Assets / Building
**Type:** Batch Pipeline (Scheduled)
**Version:** 1.2.3 (Final Polish)
**Status:** Draft

---

## 1. Purpose

Bulk verification of condo status for buildings via NYC Geoclient v2 API. This pipeline implements **Geoclient-authoritative condo verification** — proactive bulk verification so the system can safely offer condo-aware UX without "unknowns everywhere."

> [!IMPORTANT]
> **Condo Oracle:** Geoclient is the **only** source of condo truth. PLUTO is for enrichment, not condo verification.

## 2. Trigger & Cadence

### Daily Run

**Target:** Buildings that need verification soon.

- Newly imported buildings (since last run)
- Buildings with `condo.status = UNKNOWN` and upcoming compliance deadlines (due within 90 days)
- Buildings with `condo_verify_last_error_code` set (retry failed verifications)

### Weekly Backstop Run

**Target:** Catch-all for remaining unknowns.

- All buildings where `condo.status = UNKNOWN`
- Buildings where `condo_billing_bbl_missing = true` (re-check if billing BBL now available)
- Buildings with `condo_verify_attempt_count >= 3` and no success (log for manual review)

## 3. Source: Geoclient v2 API

### Endpoint

```http
GET https://api.nyc.gov/geoclient/v2/bin?bin={BIN}
```

### Authentication

Header-based (preferred):

```http
Ocp-Apim-Subscription-Key: {YOUR_KEY}
```

Query parameter (fallback):

```http
?key={YOUR_KEY}
```

### Key Response Fields

Per [NYC Geoclient documentation](https://maps.nyc.gov/geoclient/v2/doc):

| Geoclient Field | Type | Description | Our Usage |
| --- | --- | --- | --- |
| `condominiumFlag` | string | `"C"` when property is a condo, absent otherwise | Condo confirmation |
| `condominiumBillingBbl` | string | Billing BBL for condo complex (10-digit) | Sets `billingBbl` |
| `bbl` | string | Primary tax lot BBL (WA2) | Sets `primaryBbl` (not billing!) |
| `rpadBuildingClassificationCode` | string | DOF building class (e.g., "R0") | Sets `dofBuildingClass` |
| `buildingIdentificationNumber` | string | Echoed BIN | Verification |

> [!CAUTION]
> **Do NOT confuse `bbl` with `condominiumBillingBbl`!**
> - `bbl` = primary tax lot context (the physical parcel)
> - `condominiumBillingBbl` = condo billing lot (virtual lot for condo complex)

### Condo Flag Interpretation

Per Geoclient documentation:

- `condominiumFlag = "C"` → Property **is** a condominium
- `condominiumFlag` absent or empty → **Condo status unknown from this field**

> [!IMPORTANT]
> **Safe Interpretation Rule:** If `condominiumFlag` is absent, do NOT assume "not a condo." 
> Instead, check for `condominiumBillingBbl` as secondary evidence.

## 4. Output: Building Updates

### Decision Logic

```typescript
function interpretCondoStatus(response: GeoclientBINResponse): CondoVerificationResult {
  const hasCondoFlag = response.condominiumFlag === 'C';
  // Check for sentinel: billing BBL is strictly "0000000000" (distinct from missing/empty string)
  const isSentinel = response.condominiumBillingBbl === '0000000000';

  // Check if billing BBL is valid (exists and is NOT sentinel)
  const hasValidBillingBbl = response.condominiumBillingBbl 
    && response.condominiumBillingBbl.length > 0
    && !isSentinel;
  
  // CASE 1: Explicit Flag Present
  if (hasCondoFlag) {
    return {
      condo: { status: 'CONDO_CONFIRMED', evidence: 'GEOCLIENT_CONDO_FLAG_C' },
      billingBbl: hasValidBillingBbl ? parseBBL(response.condominiumBillingBbl) : null,
      condoBillingBblMissing: !hasValidBillingBbl // True if missing OR sentinel (if flag=C)
    };
  }
  
  // CASE 2: No Flag, BUT Valid Billing BBL Present
  // (Treat as confirmed condo based on explicit billing field)
  if (!hasCondoFlag && hasValidBillingBbl) {
    return {
      condo: { status: 'CONDO_CONFIRMED', evidence: 'GEOCLIENT_BILLING_BBL_PRESENT' },
      billingBbl: parseBBL(response.condominiumBillingBbl),
      condoBillingBblMissing: false
    };
  }
  
  // CASE 3: Explicit Zero Sentinel (Confirmed NOT Condo)
  if (!hasCondoFlag && isSentinel) {
    return {
      condo: { status: 'NOT_CONDO_CONFIRMED', evidence: 'GEOCLIENT_BILLING_BBL_ZERO_SENTINEL' },
      billingBbl: null,
      condoBillingBblMissing: false
    };
  }
  
  // CASE 4: Absence of Evidence (Neither Flag, nor Valid BBL, nor Sentinel)
  // Strict "Never Wrong" -> UNKNOWN
  return {
    condo: { status: 'UNKNOWN', evidence: 'NONE' },
    anomaly: null // Not an anomaly, just insufficient data
  };
}
```

### On Successful Verification

```typescript
// Condo confirmed (flag=C)
{
  condo: { status: 'CONDO_CONFIRMED', evidence: 'GEOCLIENT_CONDO_FLAG_C' },
  condoVerifiedAt: now(),
  billingBbl: parseBBL(response.condominiumBillingBbl),
  condoBillingBblMissing: !response.condominiumBillingBbl || response.condominiumBillingBbl === '0000000000',
  dofBuildingClass: parseDOFClass(response.rpadBuildingClassificationCode),
  condo_verify_last_attempt_at: now(),
  condo_verify_attempt_count: 0, 
  condo_verify_last_error_code: null
}

// Non-condo confirmed
{
  condo: { status: 'NOT_CONDO_CONFIRMED', evidence: 'GEOCLIENT_BILLING_BBL_ZERO_SENTINEL' },
  condoVerifiedAt: now(),
  billingBbl: null,
  condoBillingBblMissing: false,
  dofBuildingClass: parseDOFClass(response.rpadBuildingClassificationCode),
  condo_verify_last_attempt_at: now(),
  condo_verify_attempt_count: 0,
  condo_verify_last_error_code: null
}
```

### On Verification Failure

```typescript
{
  // condo remains UNCHANGED (stays UNKNOWN)
  condo_verify_last_attempt_at: now(),
  condo_verify_attempt_count: prev + 1,
  condo_verify_last_error_code: errorCode
}
```

## 5. Error Handling & Anomaly Codes

| Code | Severity | Description | Action |
| --- | --- | --- | --- |
| `CONDO_VERIFY_OK` | INFO | Verification successful | Log |
| `CONDO_VERIFY_BILLING_MISSING` | WARN | Condo confirmed but `condominiumBillingBbl` is zeros | Set flag, log |
| `CONDO_VERIFY_FLAG_WITHOUT_BBL` | WARN | `condominiumFlag=C` but no billing BBL | Set `condoBillingBblMissing=true` |
| `CONDO_VERIFY_BBL_WITHOUT_FLAG` | INFO | Billing BBL present but flag absent | Still confirm condo |
| `CONDO_VERIFY_RATE_LIMIT` | WARN | API rate limited | Backoff, retry later |
| `CONDO_VERIFY_TEMP_ERROR` | WARN | Temporary API error (5xx, timeout) | Retry later |
| `CONDO_VERIFY_BIN_NOT_FOUND` | WARN | BIN not recognized by Geoclient | Log, may be temp BIN |
| `CONDO_VERIFY_PERM_ERROR` | ERROR | Permanent failure (invalid response) | Flag for manual review |
| `CONDO_VERIFY_RESPONSE_INVALID` | ERROR | Malformed/unexpected response | Flag for investigation |

## 6. Rate Limiting Strategy

### Per-Call Limits

> [!WARNING]
> **Placeholder Values Below!** Actual Geoclient v2 limits must be confirmed from [NYC API Portal](https://api-portal.nyc.gov) after obtaining API key. These numbers are examples only.

| Limit Type | Placeholder Value | Config Key |
| --- | --- | --- |
| Requests/second | ~10 (example) | `GEOCLIENT_RATE_LIMIT_PER_SEC` |
| Requests/day | ~10,000 (example) | `GEOCLIENT_RATE_LIMIT_PER_DAY` |
| Batch size | 5,000 per run | `CONDO_VERIFY_BATCH_SIZE` |
| Delay between calls | 100ms (example) | `GEOCLIENT_CALL_DELAY_MS` |

**Implementation requirement:** All rate limiting values must be configurable via environment variables, not hardcoded.

### Batch Strategy

1. **Fetch target BINs** from database (max 5,000 per run)
2. **Queue with delay** (100ms between calls = ~10 req/sec)
3. **Exponential backoff** on rate limit responses
4. **Checkpoint progress** every 100 buildings (resumable)

### Monitoring

- Track `verified_count`, `failed_count`, `rate_limit_count` per run
- Alert if `failed_count / total > 10%`

## 7. Precedence Rules

> [!IMPORTANT]
> **Geoclient explicit > PAD > Heuristic**

1. **Geoclient explicit fields** (`condominiumFlag`, `condominiumBillingBbl`) are the ONLY sources that can set `condo.status` to a verified state.
2. **PAD** may provide hints but does NOT set condo truth.
3. **Heuristics** (lot range 75xx, building class R0) may:
   - Log anomalies for investigation
   - **Never** set `condo` or `billingBbl`

## 8. UX Implications

### When `condo.status = CONDO_CONFIRMED`

- Show condo banner: "Condominium complex: building-wide compliance is typically coordinated by management/board."
- Enable "View condo complex" grouping by `billingBbl`
- If `condoBillingBblMissing = true`: "Billing BBL not yet available in city records."

### When `condo.status = NOT_CONDO_CONFIRMED`

- Show as standard building
- No condo-specific UI elements

### When `condo.status = UNKNOWN`

- Show subtle "Verification pending" indicator
- Offer "Verify now" button (triggers on-demand call)
- Do NOT guess or imply condo/non-condo status

## 9. Field Mapping Summary

| Geoclient Field | Domain Property | Notes |
| --- | --- | --- |
| `condominiumFlag` | → `condo.status` | "C" = CONDO_CONFIRMED |
| `condominiumBillingBbl` | → `billingBbl` | Only when condo confirmed |
| `bbl` | → `primaryBbl` | Tax lot context (NOT billing!) |
| `rpadBuildingClassificationCode` | → `dofBuildingClass.code` | Pure DOF code |

## 10. Future Considerations

- **PLUTO Integration:** After condo verification, PLUTO can be used for enrichment (unit counts, floor area) keyed by `billingBbl`.
- **Condo Base BBL:** Geosupport exposes a `condoBaseBbl` field when billing BBL is unavailable. May add support if edge case is common.
- **On-Demand Verification:** Could add on-demand verification as supplement to batch (user clicks "Verify" → immediate API call).
