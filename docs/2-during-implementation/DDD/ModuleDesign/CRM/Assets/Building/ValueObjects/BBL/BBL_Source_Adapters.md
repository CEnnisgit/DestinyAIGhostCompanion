# BBL Source Adapters

**Module:** `CRM`
**Applies To:** Import adapters (PAD, DOB rosters) + enrichment adapters (Geoclient)
**Value Object:** `BBL` (Borough–Block–Lot)
**Version:** 2.0.0

---

## Objective

Adapters exist to translate **source-shaped BBL data** into the strict `BBL` Value Object without inventing meaning.

This document ensures:

1. **Authority-per-field**: each persisted BBL-like field has one canonical writer.
2. **No assumptions**: parsing rules are grounded in documented source formats or explicitly labeled as product decisions.
3. **Safety**: we never silently "repair" ambiguous values (e.g., scientific notation).

---

## Source References (what the rules are based on)

* **PAD (BYTES of the BIG APPLE) layouts + guide**

  * PAD `bbl.txt` provides `boro/block/lot`, `condoflag`, condo low/high range, and `billboro/billblock/billlot`.
  * PAD is released quarterly and is maintained by NYC Planning.
* **Geoclient / Geosupport documentation**

  * `condominiumFlag` indicates condo (`C`); Geosupport returns condo billing BBL in the output BBL field for condos.
  * Geosupport/Geoclient may return `condominiumBillingBbl = 0000000000` when a condo billing BBL is not assigned.
  * Geosupport provides a "Condo Base BBL" field (for condos without billing BBL) in newer releases.

> Note: Where we accept additional tokens beyond published docs (e.g., borough abbreviations), we label those as **Product Decisions** and make them optional.

---

## 1) Where BBL Appears in Our Domain

We use BBL in multiple roles. Adapters must **not** conflate these roles.

### 1.1 Canonical fields (persisted)

* `Building.primaryBbl` (parcel context for joins)
* `Building.billingBbl` (condo grouping context; only when condo confirmed)

### 1.2 Evidence fields (persisted)

* PAD evidence on Building (e.g., `padBillingBbl*`, `padCondoFlag`, condo low/high ranges)

### 1.3 Ephemeral lookups (not persisted)

* Geoclient response BBLs may be used for lookup/verification, but do not automatically overwrite canonical Building fields.

---

## 2) Authority Matrix (Write Policy)

> **Rule:** Only the canonical authority writes the canonical field. Other sources may be stored as evidence and/or used for linking.

| Field                     | Meaning                                   | Canonical writer                                                        | Other sources                                                                                         |
| ------------------------- | ----------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `Building.primaryBbl`     | Parcel context for joins (PLUTO/MapPLUTO) | **PAD Bootstrap**                                                       | DOB roster may seed only for stub Buildings when PAD missing (Product decision; never overwrites PAD) |
| `Building.billingBbl`     | Condo billing context                     | **Geoclient condo fields** (`condominiumFlag`, `condominiumBillingBbl`) | PAD `bill*` stored as evidence only                                                                   |
| `Building.padBillingBbl*` | PAD billing fields                        | **PAD**                                                                 | none                                                                                                  |

**Why Geoclient does not overwrite `primaryBbl`:**

* For condos, Geosupport/Geoclient returns the **billing BBL** in the output BBL field, which can be a `75xx` lot and not the physical/unit context. This is correct behavior for Geosupport, but it is not the same concept as our `primaryBbl`.

---

## 3) Adapter Responsibilities

### 3.1 Adapter vs VO

* **Adapter:** normalize inputs, detect sentinels/ambiguity, produce `BBL.create(...)` arguments.
* **VO:** enforce strict invariants:

  * borough code ∈ `{1,2,3,4,5}`
  * block > 0
  * lot > 0

### 3.2 Adapter outputs

Adapters return:

* `BBL` (valid)
* `undefined` (missing/sentinel/ambiguous)
* plus an **anomaly record** when the input was present but unusable.

> System rule: a Building import should not fail solely due to a bad BBL. The import pipeline decides whether to quarantine a row.

---

## 4) Supported Input Shapes

Adapters must support these shapes explicitly.

### Shape A — 10-digit BBL string

Example: `"1018890001"`

### Shape B — separated components

Example: `boro=1, block=1889, lot=1`

### Shape C — hyphenated display formats

Examples:

* `"1-01889-0001"`
* `"1-1889-1"`

### Shape D — spreadsheet-export artifacts (Product decision)

Examples:

* `"1018890001.0"` (trailing `.0`)
* `"1,018,890,001"` (commas)

> We accept these only because they commonly appear when spreadsheets/CSVs reformat numeric identifiers. If you want strict mode, disable these rewrites.

---

## 5) Sentinel & Ambiguity Rules

### 5.1 Universal "missing"

Treat as missing:

* `null`, empty string, whitespace-only

Diagnostics: `WARN: BBL_MISSING`

### 5.2 Geoclient "all zeroes"

Treat `"0000000000"` as a **missing condo billing BBL** (not a valid BBL).

Diagnostics: `INFO: BBL_ALL_ZEROES_SENTINEL`

### 5.3 Scientific notation (reject)

If the string contains `e` or `E` (e.g., `1.01889E9`), reject as ambiguous.

Diagnostics: `WARN: BBL_SCI_NOTATION`

Rationale: numeric formatting may lose leading zeros and/or digits. We do not guess.

---

## 6) Normalization Rules

### 6.1 Safe string cleanup (Product decision)

Apply in this order:

1. trim whitespace
2. remove commas (`,`) **only**
3. if endswith `.0` exactly, strip that suffix

Then proceed to parse.

If the value contains any non-digit characters after cleanup (except hyphens handled separately), reject.

Diagnostics: `WARN: BBL_NON_NUMERIC`

### 6.2 Parse strategy

**Strategy 1 (preferred): components**

* If the source provides `boro/block/lot` as separate fields, parse those.

**Strategy 2: 10-digit string**

* If the cleaned string is exactly 10 digits:

  * borough = first digit
  * block = next 5 digits
  * lot = last 4 digits

**Strategy 3: hyphenated**

* If matches `B-BLOCK-LOT` with hyphens:

  * split by `-`
  * parse borough/block/lot as integers

If block/lot are provided without leading zeros, that is fine; the VO stores numeric parts.

### 6.3 Borough parsing

**Documented inputs (strict mode)**

* numeric borough code: `1..5`
* full borough name (case-insensitive):

  * `Manhattan`, `Bronx`, `Brooklyn`, `Queens`, `Staten Island`

**Additional inputs (lenient mode; Product decision)**
Accepted only if enabled:

* `MN`, `BX`, `BK`, `QN`, `SI`
* `NEW YORK` (→ Manhattan)
* `KINGS` (→ Brooklyn)
* `RICHMOND` (→ Staten Island)

Diagnostics:

* unknown borough token → `WARN: BBL_BOROUGH_UNRECOGNIZED`

---

## 7) Source-Specific Adapters

### 7.1 PAD Adapter (PAD Bootstrap)

**Input shape:** PAD provides component fields as fixed-width character columns:

* `boro` (1)
* `block` (5)
* `lot` (4)

**Condo/billing evidence fields (BBL table):**

* `condoflag` (`C` indicates condo)
* `billboro`, `billblock`, `billlot`
* low/high condo unit range: `loboro/loblock/lolot` and `hiboro/hiblock/hilot`

**Rules:**

* Parse component fields as strings, then integers.
* Preserve PAD values as evidence exactly (even if condo is later disproven/confirmed).
* Do not set `Building.billingBbl` from PAD; store PAD billing fields in `padBillingBbl*` only.

Diagnostics:

* parse failure → `WARN: PAD_BBL_PARSE_ERROR`

### 7.2 DOB Roster Adapter (LL152)

**Role:** program membership + deadlines.

**Rules:**

* If a roster provides a BBL, parse it using the shared normalization rules.
* Do not overwrite `Building.primaryBbl` when PAD has already set it.
* If the Building is a stub created from roster (PAD not loaded yet), the pipeline may optionally seed `primaryBbl` from roster (Product decision) and mark provenance.

Diagnostics:

* unusable BBL provided → `WARN: ROSTER_BBL_INVALID`

### 7.3 Geoclient Adapter (verification)

Geoclient returns:

* `condominiumFlag` (`C` indicates condo)
* `condominiumBillingBbl` (10-digit string; can be `0000000000`)
* and also a `bbl`/`bblBoroughCode`/`bblTaxBlock`/`bblTaxLot` representing Geosupport output.

**Rules:**

* Condo truth uses `condominiumFlag`.
* If condo confirmed:

  * If `condominiumBillingBbl == 0000000000`: set `condoBillingBblMissing = true` and leave `billingBbl = null`.
  * Else set `billingBbl = parse(condominiumBillingBbl)`.
* Never overwrite `primaryBbl` from Geoclient.
* If Geoclient's returned output `bbl` differs from stored `primaryBbl`, emit an anomaly (reconciliation signal).

Diagnostics:

* `INFO: CONDO_CONFIRMED_BILLING_BBL_ALL_ZEROES`
* `WARN: PRIMARY_BBL_DIFFERS_FROM_GEOCLIENT_BBL`

**Note (future-proofing): Condo Base BBL**
Geosupport provides a "Condo Base BBL" field for condos without a billing BBL in newer releases. If exposed by the API you are calling, capture it as **evidence** (do not silently treat it as `billingBbl`).

---

## 8) Diagnostics Catalog

Suggested anomaly codes (consistent across pipelines):

* `BBL_MISSING`
* `BBL_ALL_ZEROES_SENTINEL`
* `BBL_SCI_NOTATION`
* `BBL_NON_NUMERIC`
* `BBL_BOROUGH_UNRECOGNIZED`
* `PAD_BBL_PARSE_ERROR`
* `ROSTER_BBL_INVALID`
* `PRIMARY_BBL_DIFFERS_FROM_GEOCLIENT_BBL`
* `CONDO_CONFIRMED_BILLING_BBL_ALL_ZEROES`

> **Reason codes must come from `Ingestion_Diagnostics.md`; do not invent new codes here.**

---

## 9) Examples (Test Vectors)

### 9.1 10-digit string

* input: `1018890001` → borough=1, block=1889, lot=1

### 9.2 hyphenated

* input: `1-1889-1` → borough=1, block=1889, lot=1

### 9.3 spreadsheet artifact

* input: `1018890001.0` → borough=1, block=1889, lot=1

### 9.4 Geoclient condo missing billing

* input: `condominiumFlag=C`, `condominiumBillingBbl=0000000000` → condo confirmed, billing missing
