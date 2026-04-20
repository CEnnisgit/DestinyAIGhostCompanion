# Data Sources & Import Strategy (v2)

**Module:** `CRM` → `Assets`
**Primary Aggregate:** `Building`
**Related Aggregates:** `LL152Program`, `ComplianceObligation`
**Version:** 2.0.0

---

## Objective

This document exists to prevent “spec drift” by making every ingestion rule traceable to a real dataset behavior.

We want:

1. **City-wide Building coverage** before launch (pre-populated from PAD).
2. **Great search UX** (global address search, aliases, and address ranges).
3. **One authority per Value Object** (canonical writes are never ambiguous).
4. **Explicit deferral** (if a field can’t be safely filled from a source, it stays empty until the authority pipeline runs).

---

## 1) Sources We Use

### 1.1 PAD (Property Address Directory)

**Owner:** NYC Planning (DCP)

**What PAD is best at:**

* City-scale coverage of **BINs** and **address-range/alias** records.
* Relationship structure between:

  * **Tax lots (BBL)**
  * **Buildings (BIN)**
  * **Address ranges / place-name entries** (ADR)

**Tables we rely on (BYTES PAD):**

* `bbl.txt` (tax-lot level + condo billing and range metadata)
* `adr.txt` (address-range level; includes BIN)

**What we do NOT use PAD for:**

* Canonical mailing/dispatch address.
* Condo “truth” (PAD has a `condoflag`, but it is treated as evidence only).

### 1.2 Geoclient (Geosupport via HTTP)

**Owner:** NYC OTI / DCP Geosupport

**What Geoclient is best at:**

* Canonical geocoding / geosupport results, including:

  * Condo flag
  * Condo billing BBL (including the “all zeroes” case)
  * Political districts (Community District)
  * RPAD building classification code (DOF building class code system)

**Important:** Geoclient is the only source allowed to **confirm condo status**.

### 1.3 DOB Program Rosters (LL152 roster imports)

**Owner:** NYC Department of Buildings

**What rosters are best at:**

* Defining **program membership** (who is in LL152).
* Providing a minimal key for joining (usually BIN; sometimes BBL and/or address fields exist but are not authoritative for our Building canonical data).

Rosters are authoritative for:

* **LL152 program + compliance obligation creation**, not for the building’s canonical address.

---

## 2) Authority Per Persisted Field

> Principle: **One authority writes the canonical field.** Everything else is evidence, join-support, or search-support.

### 2.1 Building Aggregate fields

| Field / VO                               | Canonical Authority                                           | Evidence / Support (no overwrite)                     | Deferred until…             |
| ---------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------- | --------------------------- |
| `bin` (BIN VO)                           | **PAD Bootstrap**                                             | DOB roster can create *stub* BIN                      | never                       |
| `primaryBbl` (BBL VO)                    | **PAD Bootstrap**                                             | DOB roster may seed only if PAD missing               | PAD loads or PAD later fill |
| `address` (Address VO)                   | **Geoclient verification**                                    | PAD `adr.txt` rows populate `building_addresses` only | Geoclient runs              |
| `communityDistrict` (CD VO)              | **Geoclient verification**                                    | none                                                  | Geoclient runs              |
| `dofBuildingClass` (DOFBuildingClass VO) | **Geoclient verification** (`rpadBuildingClassificationCode`) | DOB roster only if explicitly mapped and validated    | Geoclient runs              |
| `condo` (CondoStatus VO)                 | **Geoclient verification** (`condominiumFlag`)                | PAD `condoflag` stored as evidence only               | Geoclient runs              |
| `billingBbl` (BBL VO)                    | **Geoclient verification** (`condominiumBillingBbl`)          | PAD billing fields stored as evidence only            | condo confirmed             |
| `condoBillingBblMissing`                 | **Geoclient verification**                                    | none                                                  | condo confirmed             |

### 2.2 “Evidence fields” (debug + UX support)

Evidence fields are stored only to explain why the system is behaving the way it is (and to support a better ingestion UX). They never overwrite canonical truth.

Examples:

* `padCondoFlag`, `padBillingBbl*`, `padLowBblLot`, `padHighBblLot`
* `padVersion`, `padLastSeenAt`

---

## 3) Pipelines

## Pipeline A — PAD Bootstrap (City-wide Buildings + Search Index)

**Goal:** Populate `buildings` and `building_addresses` at NYC scale.

### A.1 Inputs

* `PAD bbl.txt`
* `PAD adr.txt`
* Pipeline parameter: `pad_version_label` (e.g., `25A`, `25B`, etc.)

### A.2 Outputs

* `buildings` (create or update)
* `building_addresses` (rebuild/refresh for the PAD version)

### A.3 What we capture

#### 1) Create/maintain Building rows by BIN

* For each ADR row, take `bin` and ensure `buildings.bin` exists.
* Set provenance:

  * `created_from_source = 'PAD'` for new rows
  * `created_from_version = pad_version_label`
  * `last_imported_from_source = 'PAD'`
  * `last_imported_from_version = pad_version_label`
  * `pad_last_seen_at = now()`

#### 2) Populate `building_addresses` for search UX

Insert ADR-derived rows:

* `bin`
* `pad_version`
* street text fields (`stname`)
* range fields (`lhnd`, `hhnd`, `lhns`, `hhns`)
* `addrtype` (raw)
* `parity` (raw)

Derived meanings belong to the query layer (not ingestion):

* **NAP detection:** `parity = '0'`

#### 3) Compute `primaryBbl` (PAD authority)

PAD ADR rows contain `boro/block/lot` (the ADR foreign key to the BBL table).

**Rule (explicit system decision, not a claim about “the one true parcel”):**

* Let `candidates(bin)` = distinct `(boro, block, lot)` values across ADR rows for that BIN.
* If `|candidates| == 1`: set `primaryBbl` to that single candidate.
* If `|candidates| > 1`:

  * Choose the candidate with the **largest ADR row count** for that BIN.
  * Tie-break by numeric ascending `(boro, block, lot)`.
  * Emit anomaly `BIN_MULTIPLE_BBLS_PRIMARY_SELECTED`.

This gives deterministic joins (PLUTO/MapPLUTO) without pretending the building can never span parcels.

#### 4) Store PAD condo/billing evidence

Join the selected `primaryBbl` to PAD `bbl.txt`:

* `padCondoFlag = bbl.condoflag`
* `padBillingBbl = (billboro, billblock, billlot)`
* `padLowBblLot / padHighBblLot` derived from `lolot/hilot` (lot-only evidence; boro/block exist too)

**Important:** these do **not** set `billingBbl`.

### A.4 What we defer

* Canonical `address` on Building (Geoclient authority)
* `condo` / `billingBbl` (Geoclient authority)
* `communityDistrict`, `dofBuildingClass` (Geoclient authority)

---

## Pipeline B — Program Roster Import (LL152)

**Goal:** Add obligations to known Buildings, without polluting canonical Building truth.

### B.1 Inputs

* DOB LL152 roster file(s) (format varies by release)

### B.2 Outputs

* `LL152Program` records (import versioning)
* `ComplianceObligation` records (one per building/program cycle)
* Possibly stub `Building` rows (when PAD hasn’t populated yet)

### B.3 What we capture

* Validate BIN (if present). If BIN is missing or invalid, quarantine the roster row.
* Upsert Building:

  * If `buildings.bin` exists: link to it.
  * If missing: create stub Building with `created_from_source = 'DOB_LL152'`.

    * Do **not** set `primaryBbl` or `address` from roster.

### B.4 What we defer

* All canonical Building enrichment (Geoclient pipeline)

---

## Pipeline C — Geoclient Verification (Canonical Truth)

**Goal:** Fill “canonical fields” that are unsafe to infer from PAD/rosters.

### C.1 Inputs

* A set of Buildings requiring verification.
* A Geoclient lookup method:

  * Preferred: `bin` endpoint by BIN.
  * Alternative: address endpoint using an address candidate (e.g., one PAD address range endpoint).

### C.2 Outputs

Writes canonical fields to `buildings`:

#### 1) Canonical Address

* Fill `buildings.address` from Geoclient-returned address components.

#### 2) Community District

* Fill `communityDistrict` from Geoclient fields.

#### 3) DOF Building Class (RPAD code)

* Fill `dofBuildingClass.code` from `rpadBuildingClassificationCode`.
* Do not treat DOF building class as condo truth.

#### 4) Condo verification + Billing BBL

* If `condominiumFlag == 'C'`:

  * Set `condo.status = CONDO_CONFIRMED`
  * Read `condominiumBillingBbl`:

    * If `0000000000`, set `condoBillingBblMissing = true` and leave `billingBbl = null`.
    * Else set `billingBbl = condominiumBillingBbl` and `condoBillingBblMissing = false`.
* Else:

  * Set `condo.status = NOT_CONDO_CONFIRMED`
  * Ensure `billingBbl = null` and `condoBillingBblMissing = false`.

### C.3 What we do NOT overwrite

* `primaryBbl` is PAD-authoritative and should not be overwritten by Geoclient.

  * If Geoclient-derived BBL differs, log anomaly `PRIMARY_BBL_DIFFERS_FROM_GEOCLIENT_BBL` (debug/reconciliation).

---

## 4) Derived Views (Not Persisted)

### 4.1 TaxLotClassification (derived)

`TaxLotClassification` (or `TaxLotKind`) is a **derived view** used for routing joins and UI.

It is derived from:

* `condo.status`
* `billingBbl` (when condo confirmed and billing BBL is present)
* otherwise `primaryBbl`

We do **not** persist `TaxLotClassification` because it is fully determined by persisted facts, and persisting it would risk divergence.

---

## 5) Diagnostics & Guardrails

### 5.1 Cross-source mismatch logging (no silent overwrite)

If an incoming value conflicts with a canonical field:

* Do not overwrite.
* Emit an anomaly record with:

  * field name
  * canonical value
  * incoming value
  * source + version

### 5.2 Required anomaly types

* `ROSTER_BIN_INVALID` (pipeline B)
* `BIN_MULTIPLE_BBLS_PRIMARY_SELECTED` (pipeline A)
* `PRIMARY_BBL_DIFFERS_FROM_GEOCLIENT_BBL` (pipeline C)
* `CONDO_CONFIRMED_BILLING_BBL_ALL_ZEROES` (pipeline C)
* `PAD_ROW_PARSE_ERROR` (pipeline A)
* `GEOCLIENT_NOT_FOUND` (pipeline C)
* `GEOCLIENT_RETURN_CODE_WARNING` (pipeline C)

> **Reason codes must come from `Ingestion_Diagnostics.md`; do not invent new codes here.**

---

## 6) “No assumptions” checklist (release gate)

Before implementing new rules:

1. **Name the field** and whether it’s canonical or evidence.
2. **Name the authority source** and point to the exact dataset field(s).
3. If multiple sources supply the field, explicitly state:

   * which one is authoritative,
   * which are evidence only,
   * whether conflicts are possible.
4. If the field can’t be safely set from the authority, it must remain null/unknown and be filled by a later pipeline.

---

## 7) Notes on Text/Number Parsing

* Treat all PAD `boro/block/lot` as strings during ingestion, then validate and convert.
* Preserve leading zeros.
* Any parse failures are quarantined and logged; do not guess.
