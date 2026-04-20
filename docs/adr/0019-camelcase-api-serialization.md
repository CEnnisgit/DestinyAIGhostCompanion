# ADR-0019: camelCase API Serialization at the Rust Boundary

**Status:** Accepted  
**Date:** 2026-03-20  
**Deciders:** Development Team  
**Relates to:** [ADR-0011](0011-pad-ingestion-rust-worker.md) (Rust migration)

## Context

During the TS → Rust migration, the Rust backend introduced snake_case field names in API responses because Rust structs use snake_case by convention and `serde` serializes field names as-is by default. The Next.js dev dashboard (and any future frontend) expects camelCase, matching JavaScript conventions.

This mismatch was initially handled **inconsistently**:

- Some dashboard query files manually mapped snake_case → camelCase (e.g., `building.house_number` → `building.houseNumber`)
- Others used a generic `snakeToCamel()` utility
- Some just accessed fields directly and got `undefined`

This caused multiple bugs during dashboard testing: empty building profiles, blank obligation details, and missing import run data — all traced to naming mismatches.

## Decision

**All Rust structs that serialize to JSON for API responses use `#[serde(rename_all = "camelCase")]`.** The Rust API is the single boundary where naming convention translation happens.

```rust
#[derive(Debug, Serialize, sqlx::FromRow)]
#[serde(rename_all = "camelCase")]
pub struct BuildingSearchResult {
    pub bin: String,
    pub house_number: Option<String>,    // serializes as "houseNumber"
    pub created_from_source: Option<String>, // serializes as "createdFromSource"
    pub has_obligations: bool,           // serializes as "hasObligations"
}
```

Frontend code accesses fields using camelCase directly, with no mapping layer.

### Scope

This applies to:

- All structs in `crates/pcd-db/src/crm/types.rs` (8 structs)
- All structs in `crates/pcd-domain/src/crm/` (3 domain structs)
- All structs in `crates/pcd-domain/src/crm/import_run.rs` (2 structs)
- All future API-serialized structs

This does **not** apply to:

- Inline `serde_json::json!()` macros — these must use camelCase keys manually (the `rename_all` attribute does not affect inline JSON construction)
- Database column names — these remain snake_case in PostgreSQL
- Internal Rust code — fields remain snake_case per Rust convention

## Alternatives Considered

### 1. Frontend maps snake_case → camelCase (rejected)

Every dashboard query file would need a mapping function. This is what we had initially, and it:

- Created bugs when mappings were forgotten or incomplete
- Duplicated effort across every query file
- Made the frontend responsible for backend naming decisions

### 2. Axum middleware transforms all response JSON (rejected)

A generic middleware could walk the JSON tree and rename all keys. This:

- Adds latency for deep/large responses
- Can't distinguish intentional snake_case keys (e.g., database column names in error messages) from struct fields
- Is fragile and hard to debug

### 3. Shared codegen from OpenAPI spec (rejected for now)

Generate TypeScript types from an OpenAPI spec that defines camelCase names. This:

- Adds tooling complexity we don't need yet
- Only one consumer exists (dev dashboard)
- Can be adopted later without changing this decision

## Consequences

### Positive

- **Single source of truth** — naming convention is decided once, at the serialization boundary
- **Zero frontend boilerplate** — no mapping functions, no `snakeToCamel` utilities
- **Self-documenting** — the `rename_all` attribute makes the contract visible in code
- **Idiomatic on both sides** — Rust code stays snake_case, JS code stays camelCase

### Negative

- **Inline JSON is a trap** — `serde_json::json!()` macros are not affected by `rename_all`. Developers must remember to use camelCase keys manually in inline JSON (e.g., timeline event details). This has already caused one bug.
- **Grep mismatch** — searching for `programCode` in Rust code won't find the field declaration (`program_code`). Developers need to understand the rename.

### Mitigation

- Add a compile-time or CI lint that flags `serde_json::json!()` macros containing snake_case keys in API-facing code (future improvement).
- Document this convention in the [LayerDefinitions.md](../2-during-implementation/DDD/SystemArchitecture/LayerDefinitions.md) system architecture doc.
