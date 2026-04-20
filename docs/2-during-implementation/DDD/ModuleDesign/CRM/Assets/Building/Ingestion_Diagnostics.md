# Ingestion Diagnostics & Anomalies

**Module:** `CRM`
**Scope:** Data ingestion pipelines (PAD bootstrap, DOB rosters, Geoclient verification) + batch verification jobs
**Version:** 3.0.0

---

## Objective

Standardize how we handle imperfect NYC data without guessing.

This spec defines:

1. A **partial-success** ingestion philosophy.
2. A uniform severity model (**ERROR / WARN / INFO**) and what each means.
3. A canonical list of **reason codes** (stable identifiers) used in logs and persistence.
4. Guardrails: **no silent overwrites**, no "auto-repair" of ambiguous identifiers.

---

## Source anchors (what these rules are grounded in)

* **Geoclient v2 API docs** (example BIN responses include `condominiumBillingBbl` and show `0000000000` as a possible value):

  * [https://maps.nyc.gov/geoclient/v2/doc](https://maps.nyc.gov/geoclient/v2/doc)

* **Geosupport User Programming Guide** (condo behavior + billing BBL semantics):

  * [https://maps.nyc.gov/geoclient/v1/download/geosupport-user-programming-guide-v10.1.pdf](https://maps.nyc.gov/geoclient/v1/download/geosupport-user-programming-guide-v10.1.pdf)

* **Geosupport UPG (web) appendices** (BIN validity details, dummy/temp BIN return codes):

  * [https://nycplanning.github.io/Geosupport-UPG/appendices/appendix01/](https://nycplanning.github.io/Geosupport-UPG/appendices/appendix01/)

* **Geosupport UPG overview** (Condo Base BBL field introduction and intent):

  * [https://nycplanning.github.io/Geosupport-UPG/overview/](https://nycplanning.github.io/Geosupport-UPG/overview/)

* **PAD (BYTES) guide/layout** (ADR parity/NAP and BBL condo/billing fields):

  * [https://www.nyc.gov/site/planning/data-maps/open-data/dwn-bytes.page](https://www.nyc.gov/site/planning/data-maps/open-data/dwn-bytes.page)

---

## 1) Core Principle: Partial Success

We rarely fail an entire import job. Instead, we handle issues at the **row/record** level.

| Severity               | Meaning                                                                                     | Outcome                                                                                                | Example                                                        |
| ---------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| **ERROR (Quarantine)** | **Identity failure** (cannot safely identify the target aggregate) OR unrecoverable parsing | **Reject row**; do not create/update aggregate. Save to quarantine with context.                       | Missing/invalid BIN on a roster row that requires BIN.         |
| **WARN (Anomaly)**     | **Attribute failure** (a specific VO can't be constructed) OR cross-source mismatch         | **Partial success**; aggregate may be created/updated but the field is omitted/unchanged. Log anomaly. | BBL invalid; Geoclient mismatch vs stored primaryBbl.          |
| **INFO**               | Expected edge case or operational instrumentation                                           | No corrective action; log for monitoring/debugging                                                     | Geoclient call OK; condo billing BBL missing sentinel handled. |

---

## 2) Reason Code Design Rules

* Reason codes are **stable identifiers**, not free text.
* Codes should name:

  * the **thing** that failed (BIN/BBL/ADDR/PAD/GEOCLIENT/ROSTER), and
  * the **failure mode** (MISSING/INVALID/PARSE_ERROR/MISMATCH/RATE_LIMIT/etc).
* A single anomaly record must be able to stand alone:

  * which pipeline, which field, which raw value, and what we did.

---

## 3) Canonical Reason Codes

### 3.1 Identity (Building / BIN)

**ERROR (Quarantine)**

* `BIN_MISSING`
* `BIN_INVALID_FORMAT` (fails `^[1-5]\d{6}$`)
* `BIN_ALL_ZEROS_AFTER_BOROUGH` (matches `^[1-5]0{6}$`)

**WARN (Accepted but flagged)**

* `BIN_TEMP_GSS` (temporary BIN pattern; replacement expected)
* `BIN_DOB_DUMMY` (DOB dummy BIN; not valid in Geosupport)

**INFO**

* `BIN_VALIDATED_BY_GEOSUPPORT` (optional: when a Function BN/BNX call succeeds)

### 3.2 BBL parsing (Value Object construction)

**WARN**

* `BBL_MISSING`
* `BBL_ALL_ZEROES_SENTINEL` (e.g., `0000000000`)
* `BBL_SCI_NOTATION` (string contains `e`/`E`)
* `BBL_NON_NUMERIC` (after cleanup, contains non-digits and is not a supported hyphenated form)
* `BBL_BOROUGH_UNRECOGNIZED`
* `BBL_BLOCK_INVALID`
* `BBL_LOT_INVALID`

### 3.3 Address (Address VO construction)

**WARN**

* `ADDR_MISSING_FIELD` (missing house number or street name)
* `ADDR_BOROUGH_UNRECOGNIZED`
* `ADDR_ZIP_INVALID`

### 3.4 PAD bootstrap & PAD ADR/BBL parsing

**WARN**

* `PAD_ROW_PARSE_ERROR` (fixed-width row cannot be parsed to required fields)
* `PAD_BBL_PARSE_ERROR`
* `PAD_ADR_PARSE_ERROR`
* `BIN_MULTIPLE_BBLS_PRIMARY_SELECTED` (deterministic primaryBbl selection required)

**INFO**

* `PAD_NAP_ADDRESS` (ADR parity indicates NAP; used for UX flags)

### 3.5 DOB roster import (LL152 and future rosters)

**ERROR (Quarantine)**

* `ROSTER_ROW_MISSING_BIN`
* `ROSTER_BIN_INVALID`
* `ROSTER_DEADLINE_MISSING` (when the roster row is required to provide a deadline)

**WARN**

* `ROSTER_DATE_PARSE_ERROR`
* `ROSTER_BBL_INVALID`
* `ROSTER_ROW_UNEXPECTED_SHAPE` (columns missing/renamed)

**INFO**

* `ROSTER_DUPLICATE_ROW_SKIPPED`

### 3.6 Geoclient verification (canonical truth + condo verification)

**INFO**

* `GEOCLIENT_OK`
* `GEOCLIENT_CONDO_CONFIRMED`
* `GEOCLIENT_NOT_CONDO_CONFIRMED`
* `GEOCLIENT_CONDO_BASE_BBL_CAPTURED` (if your client exposes it; evidence only)

**WARN**

* `GEOCLIENT_NOT_FOUND` (BIN not recognized / return code indicates no match)
* `GEOCLIENT_RETURN_CODE_WARNING` (non-00 return code; store return code and message)
* `GEOCLIENT_RATE_LIMIT` (429)
* `GEOCLIENT_TEMP_ERROR` (5xx/timeout)
* `PRIMARY_BBL_DIFFERS_FROM_GEOCLIENT_BBL` (mismatch logged; no silent overwrite)
* `CONDO_CONFIRMED_BILLING_BBL_ALL_ZEROES` (condo flag indicates condo but billing BBL is `0000000000`)

**ERROR**

* `GEOCLIENT_RESPONSE_INVALID` (missing required fields, malformed JSON)
* `GEOCLIENT_AUTH_FAILURE` (401/403)

### 3.7 Heuristic investigation signals (never authoritative)

These codes are allowed only as **investigation signals**. They must never write canonical fields.

**WARN**

* `LOT_CONVENTION_SUGGESTS_AIR_LOT` (lot starts with 9xxx)
* `LOT_CONVENTION_SUGGESTS_SUBTERRANEAN` (lot starts with 8xxx)
* `LOT_CONVENTION_SUGGESTS_CONDO_BILLING` (lot in 75xx)
* `PAD_CONDOFLAG_BUT_NOT_CONDO` (PAD condoflag suggests condo but Geoclient confirms not condo)

### 3.8 Condo verification batch pipeline (Pipeline D)

**INFO**

* `CONDO_VERIFY_OK` (verification successful)
* `CONDO_VERIFY_BBL_WITHOUT_FLAG` (billing BBL present but flag absent; still confirms condo)

**WARN**

* `CONDO_VERIFY_FLAG_WITHOUT_BBL` (`condominiumFlag=C` but no billing BBL returned)
* `CONDO_VERIFY_RATE_LIMIT` (API rate limited; backoff and retry later)
* `CONDO_VERIFY_TEMP_ERROR` (temporary API error: 5xx/timeout; retry later)
* `CONDO_VERIFY_BIN_NOT_FOUND` (BIN not recognized by Geoclient; may be temp BIN)

**ERROR**

* `CONDO_VERIFY_PERM_ERROR` (permanent failure: invalid response format; flag for manual review)
* `CONDO_VERIFY_RESPONSE_INVALID` (malformed/unexpected response; flag for investigation)

---

## 4) Deprecations / Backward Compatibility

If older code paths emitted these, map them as follows:

* `BBL_SENTINEL` → `BBL_ALL_ZEROES_SENTINEL`
* `BIN_INVALID` → `BIN_INVALID_FORMAT`
* `ADDR_MISSING_NUM_STREET` → `ADDR_MISSING_FIELD`
* `CONDO_VERIFY_BILLING_MISSING` → `CONDO_CONFIRMED_BILLING_BBL_ALL_ZEROES`

Avoid creating new synonyms.

---

## 5) Persistence Schema

We store anomalies to monitor quality trends and debug mismatches.

### 5.1 `import_anomalies`

```sql
CREATE TABLE import_anomalies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Run context
  import_run_id UUID,                 -- import job run id (PAD/roster)
  verification_run_id UUID,           -- verification job run id (Geoclient)
  pipeline_name TEXT,                 -- 'pad_bootstrap', 'll152_roster_import', 'geoclient_verification', ...

  -- Source row context
  source_row_index INTEGER,           -- line number (CSV/Excel) when applicable
  source_ref TEXT,                    -- file key, URL, or logical ref

  -- Target context
  building_id UUID,                   -- FK to buildings, if resolved
  building_bin VARCHAR(7),
  program_code TEXT,
  cycle_key TEXT,

  -- Issue details
  severity VARCHAR(10) NOT NULL,      -- 'INFO' | 'WARN' | 'ERROR'
  field_name VARCHAR(80),             -- e.g. 'primaryBbl', 'address', 'condo', 'window_end'
  reason_code VARCHAR(80) NOT NULL,
  raw_value TEXT,
  message TEXT,
  details JSONB,                      -- optional: structured extras (return codes, parsed tokens, etc.)

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_anomalies_reason ON import_anomalies(reason_code);
CREATE INDEX idx_anomalies_pipeline ON import_anomalies(pipeline_name);
CREATE INDEX idx_anomalies_building ON import_anomalies(building_id);
```

### 5.2 Quarantine store

For `ERROR` severity, store the raw row payload so it can be retried later.

Implementation options:

* `quarantined_rows` table (JSONB)
* object storage bucket keyed by `{import_run_id}/{row_index}`

---

## 6) Verification Runs (Optional)

If you batch Geoclient verification, track runs separately.

```sql
CREATE TABLE verification_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  run_type TEXT NOT NULL,             -- e.g. 'daily', 'backfill'
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,

  total_buildings INTEGER DEFAULT 0,
  verified_count INTEGER DEFAULT 0,
  condo_confirmed_count INTEGER DEFAULT 0,
  not_condo_confirmed_count INTEGER DEFAULT 0,
  failed_count INTEGER DEFAULT 0,
  rate_limit_count INTEGER DEFAULT 0,

  status TEXT NOT NULL DEFAULT 'running',
  error_message TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 7) Operational Guardrails

### 7.1 No silent overwrites

If an incoming value conflicts with a canonical field:

* do not overwrite
* log a `*_MISMATCH` anomaly with canonical + incoming values (in `details`)

### 7.2 No guessing on ambiguous identifiers

Reject (WARN) and omit field:

* scientific notation BBLs
* truncated identifiers
* identifiers with unexpected characters

### 7.3 Keep anomalies small and structured

* Put long payloads in quarantine storage.
* Put structured, queryable facts in `details`.

---

## 8) Minimal Required Anomalies per Pipeline

* PAD bootstrap: `PAD_ROW_PARSE_ERROR`, `BIN_MULTIPLE_BBLS_PRIMARY_SELECTED`
* Roster import: `ROSTER_ROW_MISSING_BIN`, `ROSTER_DEADLINE_MISSING`
* Geoclient verification: `GEOCLIENT_NOT_FOUND`, `CONDO_CONFIRMED_BILLING_BBL_ALL_ZEROES`, `PRIMARY_BBL_DIFFERS_FROM_GEOCLIENT_BBL`
