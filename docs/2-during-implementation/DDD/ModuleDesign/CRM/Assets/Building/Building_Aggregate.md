# Building Aggregate Specification

**Module:** `CRM` (The Target)
**Sub-Module:** `Assets`
**Source of Truth:** `crates/pcd-domain/src/crm/building.rs` + `crates/pcd-db/src/crm/buildings.rs`
**Version:** 3.3.0 (PAD Bootstrap + Authority-per-VO)

---

## Objective

This spec exists to make the system:

1. **Pre-populated before launch** (city-wide coverage from PAD).
2. **Great UX** (global address search + aliases + ranges).
3. **Scalable to many obligations** (LL152 first; future programs later).
4. **Assumption-free** (each persisted field has a defined authority; other sources are treated as evidence or search support only).

---

## 1. Core Decisions

### 1.1 BIN-centric identity

The Aggregate Root is **Building**, representing a physical building entity.

* **Primary identity:** `BIN` (Building Identification Number).
* The Building aggregate **does not** track program deadlines or compliance status (that lives in `ComplianceObligation`).

### 1.2 PAD Bootstrap Population

* **Pipeline A (PAD Bootstrap)** creates/maintains the `buildings` table at city scale.
* Program rosters (e.g., LL152) attach obligations to already-known buildings; they may create **stubs** when PAD is missing.

---

## 2. Terminology (Critical)

### 2.1 `primaryBbl` vs `billingBbl`

BBL is **not** Building identity; it is parcel context.

* **`primaryBbl` (parcel context):** the default BBL we store on a Building for joins/enrichment (e.g., PLUTO/MapPLUTO).

  * **Authority:** PAD (bootstrap). DOB roster may seed only when PAD row is missing.

* **`billingBbl` (condo grouping context):** the condo billing BBL, stored **only** when condo is explicitly confirmed.

  * **Authority:** Geoclient condo fields.

* **PAD condo/billing fields are stored as evidence** (see `pad_*` columns) and do **not** directly set `billingBbl`.

### 2.2 Canonical Address vs Search Addresses

* **`buildings.address` (Address VO):** a single canonical **dispatch** address.

  * **Authority:** Geoclient.

* **`building_addresses` table:** many-to-one, raw-ish addresses used for search/UX.

  * **Authority:** PAD ADR table.
  * Includes aliases + ranges; supports global typeahead.

---

## 3. Attributes

See [Value Objects Directory](./ValueObjects/) for detailed definitions.

### 3.1 Core identity & metadata

| Field               | Type / VO               | Meaning                             | Authority (writes canonical)     | Supporting sources (do not overwrite canonical)                    |
| ------------------- | ----------------------- | ----------------------------------- | -------------------------------- | ------------------------------------------------------------------ |
| `id`                | UUID                    | Internal persistent ID              | Generated                        | -                                                                  |
| `bin`               | BIN (VO)                | Root identity                       | **PAD Bootstrap**                | DOB roster may create stub if missing                              |
| `address`           | Address? (VO)           | Canonical dispatch address (single) | **Geoclient**                    | PAD/DOB provide search/display only (via `building_addresses`)     |
| `primaryBbl`        | BBL? (VO)               | Parcel context for joins            | **PAD Bootstrap**                | DOB roster seeds only when PAD missing; Geoclient never overwrites |
| `communityDistrict` | CommunityDistrict? (VO) | Geosupport-style CD code            | **Geoclient** (when/if verified) | PLUTO/DOF values stored as **evidence only**; canonical field remains Geoclient-owned |
| `dofBuildingClass`  | DOFBuildingClass? (VO)  | DOF class code (e.g., R0)           | **Geoclient** (when/if verified) | PLUTO/DOF values stored as **evidence only**; canonical field remains Geoclient-owned |

### 3.2 Condo verification (Authority-per-VO)

> **Never-wrong rule:** Condo truth is set only from explicit Geoclient condo fields.

| Field                    | Type / VO        | Meaning                                                  | Authority                           |
| ------------------------ | ---------------- | -------------------------------------------------------- | ----------------------------------- |
| `condo`                  | CondoStatus (VO) | `{ status, evidence }`                                   | Geoclient                           |
| `condoVerifiedAt`        | Timestamp?       | When condo verification ran                              | Geoclient pipeline                  |
| `billingBbl`             | BBL? (VO)        | Condo billing lot (only when condo confirmed)            | Geoclient (`condominiumBillingBbl`) |
| `condoBillingBblMissing` | boolean          | Condo confirmed but billing BBL returned as `0000000000` | Geoclient pipeline                  |

> **Note on TaxLotKind:** `TaxLotKind` is a **derived view**, not persisted. See `./ValueObjects/BBL/TaxLotClassification.md`.

### 3.3 PAD evidence

These fields store PAD facts that help UX and debugging, but do not override canonical truth fields.

| Field                            | Type                    | Meaning                                               | Authority |
| -------------------------------- | ----------------------- | ----------------------------------------------------- | --------- |
| `padVersion`                     | text                    | PAD snapshot label (e.g., 25A)                        | PAD       |
| `padLastSeenAt`                  | timestamptz             | Last import timestamp that included this BIN          | PAD       |
| `padCondoFlag`                   | text?                   | Raw `condoflag` (e.g., 'C')                           | PAD       |
| `padBillingBbl`                  | BBL components nullable | Raw billing BBL fields (`billboro/billblock/billlot`) | PAD       |
| `padLowBblLot` / `padHighBblLot` | int?                    | Raw condo lot-range support                           | PAD       |

### 3.4 Provenance

| Field                     | Type        | Meaning                                                           |
| ------------------------- | ----------- | ----------------------------------------------------------------- |
| `createdFromSource`       | text        | Source that first created the Building row (e.g., PAD, DOB_LL152) |
| `createdFromVersion`      | text?       | Source version (e.g., PAD 25A, DOB roster date)                   |
| `lastImportedFromSource`  | text        | Last pipeline that wrote canonical fields                         |
| `lastImportedFromVersion` | text?       | Version of that pipeline’s source                                 |
| `lastImportedAt`          | timestamptz | When that pipeline last wrote canonical fields                    |

---

## 4. Aggregate Behavior

### 4.1 Creation

`Building.create({ bin })`

* **Primary trigger:** Pipeline A (PAD bootstrap).
* **Secondary trigger:** Pipeline B (program roster) may create a **stub** if PAD is not loaded or BIN not found.
* On create:

  * validate BIN
  * set `condo = CondoStatus.unknown()`

### 4.2 Updates (write policy)

* **Fill-if-missing** for canonical optional fields unless an operator explicitly approves a correction.
* **No silent overwrites across authorities.** If a canonical field differs from incoming authority value, log an anomaly and require an explicit reconciliation policy.
* **Timeline Auditing:** Any automated pipeline (like PAD updates) that modifies a canonical field MUST emit a JSONB diff payload to the `building_events` table. This Hybrid Event Sourcing guarantees the frontend can render an accurate historical timeline UX.

### 4.3 Invariants

* `billingBbl` can only be non-null when `condo.status = CONDO_CONFIRMED`.
* `condoBillingBblMissing` can only be true when `condo.status = CONDO_CONFIRMED`.
* `condoVerifiedAt` must be set whenever `condo.status != UNKNOWN`.
* `condo.status` and `condo.evidence` must satisfy CondoStatus VO invariants.

---

## 5. Persistence Strategy (SQL)

> Note: This SQL is a *spec*, not a migration file. Keep it consistent with actual migrations.

```sql
CREATE TABLE buildings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bin VARCHAR(7) UNIQUE NOT NULL,

  -- Canonical Address (Geoclient-verified)
  house_number TEXT,
  street_name TEXT,
  borough TEXT,
  zip_code VARCHAR(5),

  -- Canonical Primary BBL (PAD-first parcel context)
  primary_bbl_borough_code SMALLINT,
  primary_bbl_block INTEGER,
  primary_bbl_lot INTEGER,

  -- Canonical Metadata (optional; typically Geoclient-verified when present)
  cd_borough_code SMALLINT,
  cd_number INTEGER,
  dof_building_class_code TEXT,

  -- Condo Verification (Geoclient)
  condo_status TEXT NOT NULL DEFAULT 'UNKNOWN',
  condo_status_evidence TEXT NOT NULL DEFAULT 'NONE',
  condo_verified_at TIMESTAMPTZ,

  billing_bbl_borough_code SMALLINT,
  billing_bbl_block INTEGER,
  billing_bbl_lot INTEGER,
  condo_billing_bbl_missing BOOLEAN NOT NULL DEFAULT FALSE,

  -- Condo verification ops (batch reliability)
  condo_verify_last_attempt_at TIMESTAMPTZ,
  condo_verify_attempt_count INTEGER NOT NULL DEFAULT 0,
  condo_verify_last_error_code TEXT,

  -- PAD Evidence
  pad_version TEXT,
  pad_last_seen_at TIMESTAMPTZ,
  pad_condo_flag TEXT,
  pad_billing_bbl_borough SMALLINT,
  pad_billing_bbl_block INTEGER,
  pad_billing_bbl_lot INTEGER,
  pad_low_bbl_lot INTEGER,
  pad_high_bbl_lot INTEGER,

  -- Provenance
  created_from_source TEXT,
  created_from_version TEXT,
  last_imported_from_source TEXT,
  last_imported_from_version TEXT,
  last_imported_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_buildings_primary_bbl ON buildings(primary_bbl_borough_code, primary_bbl_block, primary_bbl_lot);
CREATE INDEX idx_buildings_billing_bbl ON buildings(billing_bbl_borough_code, billing_bbl_block, billing_bbl_lot);
CREATE INDEX idx_buildings_borocd ON buildings(cd_borough_code, cd_number);
CREATE INDEX idx_buildings_condo_status ON buildings(condo_status);

-- Condo invariants
ALTER TABLE buildings ADD CONSTRAINT chk_condo_evidence_required
  CHECK (
    (condo_status = 'UNKNOWN' AND condo_status_evidence = 'NONE')
    OR
    (condo_status != 'UNKNOWN' AND condo_status_evidence != 'NONE')
  );

ALTER TABLE buildings ADD CONSTRAINT chk_condo_verified_at_required
  CHECK (
    (condo_status = 'UNKNOWN' AND condo_verified_at IS NULL)
    OR
    (condo_status != 'UNKNOWN' AND condo_verified_at IS NOT NULL)
  );

ALTER TABLE buildings ADD CONSTRAINT chk_billing_bbl_only_for_condo
  CHECK (
    (condo_status != 'CONDO_CONFIRMED'
     AND billing_bbl_borough_code IS NULL
     AND billing_bbl_block IS NULL
     AND billing_bbl_lot IS NULL)
    OR
    (condo_status = 'CONDO_CONFIRMED')
  );

ALTER TABLE buildings ADD CONSTRAINT chk_billing_bbl_missing_only_for_condo
  CHECK (
    (condo_status != 'CONDO_CONFIRMED' AND condo_billing_bbl_missing = FALSE)
    OR
    (condo_status = 'CONDO_CONFIRMED')
  );

ALTER TABLE buildings ADD CONSTRAINT chk_condo_status_enum
  CHECK (condo_status IN ('UNKNOWN', 'CONDO_CONFIRMED', 'NOT_CONDO_CONFIRMED'));
```

### Secondary table: PAD address index

```sql
CREATE TABLE building_addresses (
  id BIGSERIAL PRIMARY KEY,
  bin VARCHAR(7) NOT NULL REFERENCES buildings(bin),

  -- PAD versioning
  pad_version TEXT NOT NULL,

  -- Normalized search keys
  borough_code SMALLINT NOT NULL,
  street_name TEXT NOT NULL,

  -- Display form (what user typed / sees)
  house_number_display TEXT NOT NULL,

  -- Ranges (raw-ish PAD ADR fields)
  lhnd TEXT,
  hhnd TEXT,
  lhns TEXT,
  hhns TEXT,

  -- PAD metadata
  address_type TEXT,   -- e.g., 'R' real / 'P' pseudo (store raw)
  parity TEXT,         -- PAD parity; '0' indicates NAP

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_building_addresses_bin ON building_addresses(bin);
CREATE INDEX idx_building_addresses_search ON building_addresses(borough_code, street_name, lhns);

-- Derived meanings (app/query layer):
-- is_nap := (parity = '0')
-- is_naub := (no building_addresses rows exist for the BIN)
```

---

## 6. Pipeline Integration

* **Pipeline A (PAD Bootstrap):** creates buildings and refreshes `building_addresses` and PAD evidence fields.
* **Pipeline B (DOB rosters):** attaches obligations; may create a stub Building if BIN not present.
* **Pipeline C (Geoclient verification):** fills canonical `address`, `communityDistrict`, `dofBuildingClass`, and performs condo verification to populate `condo` + `billingBbl`.
