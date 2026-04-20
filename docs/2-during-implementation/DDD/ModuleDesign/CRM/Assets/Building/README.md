# Building Aggregate Documentation

**Module:** `CRM`
**Context:** `Assets` → Physical Buildings

---

## What this directory is

This directory contains the Domain Design specs and Value Objects for the **Building Aggregate**.

The system is designed to:

1. **Pre-populate the database** with NYC-wide building coverage before launch.
2. Deliver **great search UX** (global address search, aliases, and address ranges).
3. Support **many compliance programs** over time (LL152 first, more later).
4. Stay **assumption-free**: every canonical field has exactly one authority; everything else is evidence or search-support.

---

## Key architectural decisions

### 1) PAD Bootstrap

We populate the `buildings` table at city scale using NYC Planning's **Property Address Directory (PAD)**.

* PAD provides bulk coverage of buildings (BIN) and address-range records.
* PAD is used to power a global `building_addresses` search index.

### 2) Authority-per-VO (canonical writes)

Each canonical field is written by a single, explicit authority:

* `Building.bin` → **PAD** (bootstrap)
* `Building.primaryBbl` → **PAD** (bootstrap; parcel join context)
* `Building.address` → **Geoclient / Geosupport** verification (canonical dispatch address)
* `Building.communityDistrict` → **Geoclient / Geosupport** verification
* `Building.dofBuildingClass` → **Geoclient / Geosupport** verification (`rpadBuildingClassificationCode`)
* `Building.condo.status` + `Building.billingBbl` → **Geoclient / Geosupport** condo fields

Other sources (e.g., DOB rosters) may supply identifiers, but they do **not** overwrite canonical building truth.

### 3) Evidence vs canonical

We persist some raw source evidence fields (e.g., PAD `condoflag`, PAD billing BBL fields) so the system can explain decisions and surface anomalies.

Evidence fields:

* never overwrite canonical fields
* are allowed to contradict canonical fields (contradictions are logged, not "auto-fixed")

### 4) Derived concepts are not persisted

If a label is fully determined from persisted facts, it should be derived.

Example:

* `TaxLotClassification` (a derived view) is computed from `condo.status`, `billingBbl`, and `primaryBbl`.

---

## Pipeline overview (where data comes from)

### Pipeline A — PAD Bootstrap

**Purpose:** city-wide population.

* Upserts `buildings` (BIN identity + `primaryBbl` join context)
* Refreshes `building_addresses` for global search UX
* Stores PAD condo/billing fields as **evidence**

### Pipeline B — Program roster import (e.g., DOB LL152)

**Purpose:** program membership + obligation creation.

* Creates/updates `ComplianceObligation` records
* May create *stub* `Building` rows if PAD was not loaded yet
* Does **not** set canonical address or canonical BBL if PAD exists

### Pipeline C — Geoclient verification

**Purpose:** canonical truth.

* Fills `Building.address`, `communityDistrict`, `dofBuildingClass`
* Confirms condo status and sets `billingBbl` when condo confirmed

See **`02_data_sources_and_import_strategy_v2.md`** for the full no-assumptions import contract.

---

## Specs in this directory

### Core

* **`Building_Aggregate.md`** — aggregate boundaries, canonical fields, invariants, persistence contract
* **`02_data_sources_and_import_strategy_v2.md`** — source-by-source import rules and deferrals

### Value Objects

Identity & Location

* **`ValueObjects/BIN/BIN_VO_Spec.md`**
* **`ValueObjects/BBL/BBL_VO_Spec.md`**
* **`ValueObjects/Address/Address_VO_Spec.md`**
* **`ValueObjects/CD/CommunityDistrict_VO_Spec.md`**

Classification

* **`ValueObjects/DOF/DOFBuildingClass_VO_Spec.md`**

Condo & BBL adapters

* **`ValueObjects/BBL/BBL_Source_Adapters.md`** — parsing/normalization rules per source
* **`ValueObjects/BBL/TaxLotClassification.md`** — derived view (not persisted)
* **`ValueObjects/Condo/CondoStatus_VO_Spec.md`**

---

## BBL-specific notes (common pitfalls)

### `primaryBbl` vs `billingBbl`

* `primaryBbl` is the parcel join context (PAD bootstrap).
* `billingBbl` is a condo grouping context that is only set when condo is confirmed by Geosupport/Geoclient.

This separation prevents a common failure mode:

* Geosupport can return condo billing BBLs as the "output BBL" for condos, which is not the same concept as our parcel join context.

---

## External references (authorities)

```text
PAD (BYTES) guide / layout (NYC Planning):
- https://www.nyc.gov/site/planning/data-maps/open-data/dwn-bytes.page

Geoclient v2 API documentation:
- https://maps.nyc.gov/geoclient/v2/doc

Geosupport UPG (NYC Planning) — Condo Base BBL note:
- https://nycplanning.github.io/Geosupport-UPG/overview/

NYC GeoSearch (PAD-backed autocomplete reference implementation):
- https://geosearch.planninglabs.nyc/
```

---

## Release gate: "No assumptions" checklist

Before adding a new ingestion rule:

1. Identify the **exact source field(s)**.
2. Decide whether the field is **canonical** or **evidence**.
3. Assign a **single canonical authority** (or leave null/unknown and defer).
4. Define conflict behavior: **log anomalies**; do not silently overwrite.
