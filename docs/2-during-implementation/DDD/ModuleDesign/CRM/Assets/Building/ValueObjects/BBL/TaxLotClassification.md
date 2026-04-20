# Tax Lot Classification (Derived View)

**Module:** `CRM` → `Assets`
**Type:** Derived Concept (Not Persisted)
**Version:** 2.0.0
**Status:** Active

---

## Objective

Provide a **derived**, always-consistent way to describe what the Building's **BBL context** represents (normal lot vs condo complex grouping vs special lot conventions) **without persisting redundant labels**.

This view exists to:

1. Support **UX clarity** (why does this building have weird lots / why is it grouped?).
2. Support **safe grouping** decisions (e.g., condo complex rollups) without overwriting canonical fields.
3. Avoid assumptions: the classification is computed from **persisted facts** with clear authorities; any pattern-based signals are treated as **non-authoritative conventions** and never used to write condo truth.

---

## 1) Inputs (What we are allowed to use)

TaxLotClassification must only use:

### 1.1 Canonical facts (authoritative)

* `building.primaryBbl` (BBL VO)

  * **Authority:** PAD Bootstrap
* `building.condo.status` (CondoStatus VO)

  * **Authority:** Geoclient condo fields
* `building.billingBbl` (BBL VO, nullable)

  * **Authority:** Geoclient `condominiumBillingBbl` (only when condo confirmed)
* `building.condoBillingBblMissing` (boolean)

  * **Authority:** Geoclient verification pipeline (billing returned as all-zeroes)

### 1.2 Persisted evidence (informational; never overwrites canonical)

* `building.padCondoFlag`
* `building.padBillingBbl*`
* `building.padLowBblLot / building.padHighBblLot`
* (optional) `building.geoCondoBaseBbl` (if your Geosupport/Geoclient client exposes this field)

> If a field is not persisted on Building, it cannot be used here.

---

## 2) Output Structure

### 2.1 TaxLotKind (derived enum)

```ts
enum TaxLotKind {
  UNKNOWN = 'UNKNOWN',

  // Non-condo lots
  NORMAL = 'NORMAL',

  // Condo-related (based on condo.status)
  CONDO_CONFIRMED = 'CONDO_CONFIRMED',

  // Special-lot conventions (pattern-based; informational only)
  AIR_LOT_LIKELY = 'AIR_LOT_LIKELY',
  SUBTERRANEAN_LOT_LIKELY = 'SUBTERRANEAN_LOT_LIKELY',
  CONDO_BILLING_LOT_LIKELY = 'CONDO_BILLING_LOT_LIKELY'
}
```

### 2.2 TaxLotClassification (derived view object)

```ts
type TaxLotClassification = {
  kind: TaxLotKind;

  // The BBL you use for parcel joins/enrichment (always primaryBbl when present)
  joinBbl: BBL | null;

  // The BBL you use to represent the condo complex (if applicable)
  condoGroupBbl: BBL | null;

  // Traceability for UX/debug (never used to overwrite canonical data)
  evidence: {
    condoStatus: string;               // building.condo.status
    billingBblPresent: boolean;
    condoBillingBblMissing: boolean;
    padCondoFlag?: string | null;
    padBillingBblPresent?: boolean;
    padLowHighRangePresent?: boolean;
    geoCondoBaseBblPresent?: boolean;
  };
}
```

---

## 3) Derivation Rules (No Silent Guessing)

### 3.1 The condo decision is binary and authoritative

Condo truth is **only** taken from `building.condo.status`.

```ts
function deriveCondoGroupBbl(building: Building): BBL | null {
  if (building.condo.status !== 'CONDO_CONFIRMED') return null;

  if (building.billingBbl) return building.billingBbl;

  // Optional: if you persist the Geosupport "Condo Base BBL" as evidence, you may use it
  // for temporary grouping. This is still a derived value and should be treated as provisional.
  if (building.geoCondoBaseBbl) return building.geoCondoBaseBbl;

  return null;
}
```

### 3.2 Core kind derivation (authoritative-first)

```ts
function deriveTaxLotKind(building: Building): TaxLotKind {
  // Condo truth has priority
  if (building.condo.status === 'CONDO_CONFIRMED') return TaxLotKind.CONDO_CONFIRMED;

  if (building.condo.status === 'NOT_CONDO_CONFIRMED') {
    // Base assumption for non-condos: NORMAL
    return TaxLotKind.NORMAL;
  }

  // Unknown condo status: we do not guess
  return TaxLotKind.UNKNOWN;
}
```

### 3.3 Informational conventions (pattern signals)

NYC tax lot numbering conventions are useful for **labels and anomaly detection**, but they are not treated as authoritative "truth fields."

**Conventions (informational only):**

* Condo **billing** lot numbers commonly begin with `75`.
* Air lots commonly begin with `9`.
* Subterranean lots commonly begin with `8`.

> These conventions must never set `building.condo.status` or `building.billingBbl`.

You may optionally compute these *secondary* labels:

```ts
function deriveLotConventionLabel(primaryBbl: BBL | null): TaxLotKind | null {
  if (!primaryBbl) return null;

  const lot = primaryBbl.lot; // 1..9999
  const prefix = Math.floor(lot / 1000); // 0..9

  if (prefix === 9) return TaxLotKind.AIR_LOT_LIKELY;
  if (prefix === 8) return TaxLotKind.SUBTERRANEAN_LOT_LIKELY;

  // billing-lot convention (75xx)
  if (lot >= 7500 && lot <= 7599) return TaxLotKind.CONDO_BILLING_LOT_LIKELY;

  return null;
}
```

**Recommended usage:**

* display as a UI tag when condo status is unknown
* log anomalies when it contradicts authoritative condo status

---

## 4) Full Derived View

```ts
function deriveTaxLotClassification(building: Building): TaxLotClassification {
  const joinBbl = building.primaryBbl ?? null;
  const condoGroupBbl = deriveCondoGroupBbl(building);

  const coreKind = deriveTaxLotKind(building);
  const conventionKind = deriveLotConventionLabel(joinBbl);

  // Prefer authoritative kind; attach convention info via evidence/logging
  const kind = coreKind;

  return {
    kind,
    joinBbl,
    condoGroupBbl,
    evidence: {
      condoStatus: building.condo.status,
      billingBblPresent: Boolean(building.billingBbl),
      condoBillingBblMissing: Boolean(building.condoBillingBblMissing),
      padCondoFlag: building.padCondoFlag ?? null,
      padBillingBblPresent: Boolean(building.padBillingBblBorough && building.padBillingBblBlock && building.padBillingBblLot),
      padLowHighRangePresent: Boolean(building.padLowBblLot && building.padHighBblLot),
      geoCondoBaseBblPresent: Boolean(building.geoCondoBaseBbl)
    }
  };
}
```

---

## 5) Why Derived Instead of Persisted

Persisting `taxLotKind` creates risk:

* It becomes stale when condo verification is re-run.
* It diverges from authoritative evidence.

Deriving it guarantees:

* one source of truth (`condo.status`)
* consistent UI and grouping

If you need query performance, implement it as:

* a database **view**, or
* a cached denormalized field that is recomputed in a controlled reconciliation job.

---

## 6) Anomaly Rules (Recommended)

### 6.1 Convention contradicts condo truth

* If `condo.status = NOT_CONDO_CONFIRMED` and `primaryBbl.lot` is in `75xx`, log:

  * `LOT_CONVENTION_SUGGESTS_CONDO_BILLING` (with contradiction details in anomaly metadata)

### 6.2 PAD evidence contradicts Geoclient condo truth

* If `condo.status = NOT_CONDO_CONFIRMED` but `padCondoFlag == 'C'`, log:

  * `PAD_CONDOFLAG_BUT_NOT_CONDO`

> These are investigation signals only; they never override `condo.status`.
>
> **Reason codes must come from `Ingestion_Diagnostics.md`; do not invent new codes here.**

---

## 7) Notes for Future Expansion

If you later need true air-rights/subterranean semantics:

* Add explicit evidence fields sourced from a documented authority (Geosupport or a DOF map-based dataset).
* Introduce a tri-state status VO similar to `CondoStatus`.
* Keep `TaxLotKind` derived.
