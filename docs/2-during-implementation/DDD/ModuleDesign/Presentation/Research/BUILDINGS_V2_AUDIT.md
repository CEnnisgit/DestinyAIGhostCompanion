# V2 Audit: Buildings Rail — Prototype vs. Domain

## The Core Problem

The v1 prototype treats buildings as **user-owned records** — 9 hardcoded buildings that "belong to" the plumber. The actual domain works fundamentally differently:

> Buildings exist in a **city-wide registry** bootstrapped from PAD (~1M records). Users don't create buildings — they **discover** them and **adopt** them into their operational inventory.

This audit documents the specific disconnects and the emerging "tenant inventory" concept.

---

## Disconnect 1: Where Buildings Come From

| | V1 Prototype | Actual Domain |
|---|---|---|
| **Source** | Hardcoded in `mock-data.ts` | PAD Bootstrap (Pipeline A) seeds ~1M buildings from NYC Planning |
| **Creation** | Implicitly "owned" by user | System-populated; user never creates a Building |
| **Discovery** | No discovery — all buildings pre-assigned | DOB LL152 roster (Pipeline B) reveals which buildings need inspection |
| **Enrichment** | Static mock fields | Geoclient (Pipeline C) fills canonical address, CD, condo status |
| **User's role** | Passive consumer of pre-loaded list | Active searcher/explorer of a huge municipal dataset |

### What the domain actually does:

```
PAD (bbl.txt + adr.txt)  →  Pipeline A  →  ~1M buildings in DB
                                              ↓
DOB LL152 roster (Excel)  →  Pipeline B  →  ComplianceObligation attached to buildings
                                              ↓
                              Pipeline C  →  Geoclient fills canonical address, condo, CD
```

The user's relationship with a building starts when they **discover it through the DOB LL152 roster** (it has an inspection obligation) or **search for it** in the PAD-backed building explorer.

---

## Disconnect 2: No Two-Tier Architecture

V1 conflates two very different concepts:

### Tier 1: Global Building Registry (the "PAD layer")
- ~1M buildings, populated by system, never user-created
- BIN-centric identity with authority-per-VO rules
- Addresses, BBL, condo status, community district
- What the dev-dashboard Building Explorer already browses

### Tier 2: Tenant Inventory (the "my buildings" layer)
- Buildings the user has **adopted** for operational use
- Only a tiny subset of the global registry (~10-200 buildings per firm)
- Has user-owned overlay: contacts (owner, super), notes, job history, prospect status
- This layer **doesn't exist yet in the domain model** — it's implied but undefined

V1 prototype smashed these together into one flat list.

---

## Disconnect 3: Building Data Model

The actual `Building` aggregate is much richer and more complex than the prototype's `MockBuilding`:

| V1 `MockBuilding` | Actual `Building` Aggregate |
|---|---|
| `address: string` | `Address` VO (house_number + street_name + borough + zip) with Geoclient authority |
| `bin: string` | `BIN` VO (validated 7-digit, 1-5 prefix) |
| `borough: string` | Derived from canonical address (Geoclient-verified) |
| `communityDistrict: string` | `CommunityDistrict` VO (borough_code + number, Geoclient authority) |
| `obligationStatus: string` | Separate `ComplianceObligation` aggregate (program, cycle, subcycle, window, roster_status) |
| `gasStatus: string` | **Doesn't exist in domain** — this was prototype invention |
| `ownerName/Phone, superName/Phone` | **Not in Building aggregate** — belongs in a future Clients sub-module |
| `nextDueDate, lastInspectionDate` | **Lives on ComplianceObligation**, not Building |
| `priorFilingsCount` | Derived from Job history, not a Building field |
| `isProspect` | **No domain equivalent** — concept of "my building" vs "not my building" is the tenant inventory problem |
| — | `primaryBbl`, `billingBbl` (BBL VO with parcel context) |
| — | `condoStatus` (CondoStatus VO with evidence chain) |
| — | `dofBuildingClass` (DOFBuildingClass VO) |
| — | PAD evidence fields (condoFlag, billing BBL, lot ranges) |
| — | Provenance tracking (createdFromSource, lastImportedAt, etc.) |
| — | `building_addresses` table (many-to-one for search UX) |

---

## Disconnect 4: The Building Explorer Pattern

The dev-dashboard already has a Building Explorer that's fundamentally different from the v1 prototype's list:

| Feature | Dev-Dashboard Explorer | V1 Prototype |
|---|---|---|
| **Search** | Full-text search by BIN or address against `building_addresses` | No search |
| **Filters** | Borough, has-obligations, PAD-verified, introduced-in-version, identity lifecycle | Borough, gas status, due window, client type |
| **Detail view** | Identity (BIN, BBL, borough, CD), Condo Verification (status + evidence), Provenance (PAD evidence), Obligations table, Addresses table, Event timeline | Simplified compliance status + contacts |
| **Data source** | Live PostgreSQL queries against PAD-bootstrapped data | Hardcoded `mock-data.ts` |
| **Scale** | Paginated, handles ~1M records | 9 static records |

The dev-dashboard explorer is essentially a **power-user tool for browsing municipal data**. The v2 prototype needs to bring this into the production dashboard — but with the user-centric framing of "find a building, adopt it, work it."

---

## Disconnect 5: ComplianceObligation — Separate but Deeply Linked

In v1, obligation/compliance data lives directly on `MockBuilding` as flat fields (`obligationStatus`, `nextDueDate`). In the actual domain, `ComplianceObligation` is a **separate aggregate** — but NOT an unrelated one. Per the Compliance README: *"These are not two unrelated aggregates. The engine is the stable domain model."*

`ComplianceObligation` is identified by `(building_id, program_code, cycle_key)` and is **far richer** than the prototype suggests:

| Concern | V1 Prototype | Actual `ComplianceObligation` |
|---|---|---|
| **Identity** | `obligationStatus: string` on MockBuilding | `(building_id, program_code, cycle_key)` — supports multiple programs × cycles per building |
| **Deadline** | `nextDueDate` (single date) | `windowStart`/`windowEnd` inspection window + filing windows (30/60/120/180-day relative deadlines) |
| **Filing chain** | Visual-only step tracker | Actual fields: `inspection_date`, `report_delivered_at`, `cert_filed_at`, `correction_cert_filed_at`, `final_correction_cert_filed_at` |
| **Branching** | None | `conditions_requiring_correction` → 120-day path; `additional_time_needed` → 180-day path |
| **Not-required paths** | None | `no_gas_piping_cert_filed_at`, `no_gas_service_statement_filed_at` |
| **Extensions** | None | `extension_requested_at`, `extension_granted_at`, `extension_deadline` |
| **Status** | Flat string | Derived enum: UNKNOWN → OPEN → DUE_SOON → OVERDUE → SATISFIED → AT_RISK → NOT_REQUIRED |
| **Satisfaction** | None | Tracks HOW satisfied: INSPECTION_CERTIFICATION, NO_GAS_PIPING, NO_GAS_SERVICE |

The LL152 Program spec adds further structure: subcycle routing (A/B/C/D by community district), 4-year repeating cycle windows, and a full `ll152_obligation_details` extension table.

**Key takeaway:** The v1 compliance chain tracker was *directionally right* (Inspection → GPS1 → GPS2) but the actual domain has complex branching (correction paths, not-required paths, extensions) that makes a linear step tracker insufficient.

---

## The Emerging Concept: Tenant Inventory

The user's idea of a "tenant inventory" is the missing piece. Here's how it could work:

```
Global Registry (PAD)          Tenant Inventory (User's scope)
─────────────────────          ────────────────────────────────
~1M buildings                  ~10-200 buildings
System-populated               User-adopted (via roster or manual search)
BIN, address, BBL, condo       + Owner/Super contacts
ComplianceObligation            + prospect/active status
                                + jobs
                                + notes, documents
                                + user tags/labels
```

### How a building enters tenant inventory:

1. **LL152 roster import** → System flags buildings with obligations → user reviews and "claims" them
2. **Manual search** → User searches global registry (like DOB NOW) → finds a building → adds to inventory
3. **Job creation** → User creates a job, selects building from global search → building auto-adopted

### Key UX distinction:

- **Buildings Rail (global)** = "Find buildings in NYC" — an explorer backed by PAD data
- **My Buildings / Inventory** = "Buildings I'm actively working" — the user's operational subset
- These might be tabs, or the same view with a filter, or separate rails entirely

---

## Questions for V2 Design

1. Should "My Buildings" and "Building Explorer" be the **same rail** with a toggle, or **separate rails**?
2. When a building is adopted, what "overlay" fields does the tenant own? (contacts, tags, notes?)
3. Should the prototype surface PAD-level detail (provenance, condo evidence, address aliases) or keep that for power users?
4. How does the "prospect" concept map? Is a prospect a building from the LL152 roster that the user hasn't claimed yet?
5. Is there a concept of an "unclaimed obligation" — a building on the LL152 roster that no plumber has taken yet?
