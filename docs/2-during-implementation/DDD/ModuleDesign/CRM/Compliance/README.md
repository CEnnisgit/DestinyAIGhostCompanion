# Compliance Obligations (Engine + Programs)

This folder contains:

1) A **generic obligations engine** (`ComplianceObligation`)
2) One or more **program specifications** (starting with `LL152`) that plug into the engine

These are **not two unrelated aggregates**. The engine is the stable domain model; each program defines how its roster/source data populates the engine.

---

## 1) The Engine: `ComplianceObligation`

**Doc:** `Obligations/ComplianceObligation_Aggregate.md`

The engine defines the shared rules and storage model for all compliance programs:

- **Identity:** `(building_id, program_code)`
- **Roster truth:** obligations come only from authoritative program rosters (no guessing)
- **Shared fields:** `rosterStatus`, `nextDeadline`, `provenance`, etc.
- **Import pipeline:** upsert Building first, then upsert the obligation

Think of this as the reusable “compliance obligations platform” inside the domain.

---

## 2) Programs: `LL152` (and future services)

**Doc:** `Programs/LL152/LL152_Program_Spec.md`

A program spec defines **how a specific NYC rule/program** populates the engine:

- authoritative source dataset(s)
- mapping from roster columns → engine fields
- program-specific validations and edge cases
- optional program-specific extension tables

Example: `LL152` defines `LL152Subcycle (A|B|C|D)` and stores it in `ll152_obligation_details` as a 1:1 extension of `compliance_obligations`.

*Note: While programs may use identifiers like BIN for data lookup, the specific obligation is always stored linked to the internal `building_id`.*

---

## 3) How to add a new service/program

When adding a new program (e.g., `BOILER`, `BACKFLOW`, etc.):

1. Create a `<PROGRAM>_Program_Spec.md`
2. Define the authoritative roster/source and field mapping
3. Reuse the engine table `compliance_obligations`
4. Add a `<program>_obligation_details` extension table only if needed

The goal is to keep the engine stable while allowing programs to evolve independently.

---

## 4) Important semantic note: “Not on roster”

The engine decides the global interpretation of “not on roster”.

**Current Policy:** We use `roster_status = INACTIVE` to track when a building drops off a roster. This ensures we maintain an audit trail of historical obligations rather than deleting rows.

Program specs must follow this policy to avoid drift.
