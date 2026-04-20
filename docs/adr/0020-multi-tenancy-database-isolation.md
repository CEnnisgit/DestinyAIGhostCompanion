# ADR 0020: Multi-Tenancy Database Isolation Strategy

**Date**: 2026-03-26  
**Status**: Partially Superseded by [ADR-0030](./0030-workspace-isolation-abstraction.md)  
**Context**: Database architecture discussion during Phase 1 (Job Engine) dev-dashboard integration.

> [!IMPORTANT]
> **Supersession Note (2026-03-30):** The row-level → schema-level migration path described in this ADR has been replaced by the Workspace Abstraction model (ADR-0030). Data isolation is now based on `workspace_id` with RLS, not `company_id` with a future schema-per-tenant migration. The analysis of global vs tenant data categories remains valid.

## Problem

The platform stores two fundamentally different categories of data:

1. **Global data** — NYC buildings from PAD (~1M records), compliance obligations from DOB LL152 rosters, import anomalies, geoclient verification results. This data is public, shared by all tenants, and populated by automated pipelines.

2. **Tenant data** — Jobs, tenant assets (portfolio), contacts, notes, inspection forms, filing records. This data belongs to a specific plumbing company (scoped by `company_id`). Tenants must never access each other's data.

The concern: storing both global and tenant data in the same Postgres database risks cross-tenant data leakage and introduces scaling concerns as tenant count grows.

## Options Considered

### Option A: Shared DB, Row-Level Isolation
All tables in one database. Tenant data filtered by `WHERE company_id = $1` on every query.

- **Pro:** Simplest to build, deploy, and maintain. Free JOINs between global and tenant data.
- **Con:** One missing WHERE clause = data breach. All tenants share I/O. Harder to cleanly delete a tenant's data.

### Option B: Shared DB, Schema-Level Isolation
Global data in `public` schema. Each tenant gets a dedicated Postgres schema (`tenant_abc`, `tenant_xyz`). The `search_path` is set per request based on the authenticated user's `company_id`.

- **Pro:** Strong isolation without operational overhead of separate databases. Tenant data deletion is `DROP SCHEMA CASCADE`. Cross-schema JOINs to `public` data still work.
- **Con:** Schema provisioning on signup. Migrations must run per schema. Connection pooling requires schema-aware routing. Scales to ~hundreds of tenants.

### Option C: Separate Databases
One global database for PAD/LL152/pipeline data. One database per tenant for their jobs, assets, and operational data.

- **Pro:** Complete physical isolation. Independent backups, credentials, and scaling per tenant.
- **Con:** No cross-DB JOINs in Postgres — global data must be duplicated or accessed via foreign data wrappers. Two connection pools in the API. Highest operational complexity.

## Decision: Option A (Row-Level) for Alpha → Option B (Schema-Level) for Production

**For alpha and beta (< 10 tenants):** Use row-level isolation in a shared database. The Rust repository layer enforces `company_id` scoping on every query. This is sufficient when the codebase is small, the developer controls all queries, and the user count is single-digit.

**For production:** Migrate to schema-level isolation (Option B). This provides real isolation without the cross-DB JOIN pain of Option C. The global data (buildings, obligations, anomalies) remains in the `public` schema. Each tenant's private data (jobs, tenant_assets, contacts, inspection forms) moves to a tenant-specific schema.

**Option C (separate DBs) is not planned** unless a future compliance or contractual requirement demands physical data separation.

## Rationale

1. **Alpha pragmatism:** Row-level isolation works when there are 2 early adopters and one developer. The Rust repository pattern (`SqlxJobRepository`) already enforces company_id scoping.
2. **Production safety:** Schema-level isolation is the industry standard for multi-tenant SaaS at PCD's expected scale (dozens to low-hundreds of plumbing firms). It prevents the "missing WHERE clause" class of bugs entirely.
3. **Migration path:** Moving from row-level to schema-level is straightforward — create schemas, move rows, update the connection logic to set `search_path` per request. No domain model changes required.
4. **Global data stays global:** Buildings, obligations, and pipeline artifacts are never tenant-scoped. They stay in `public` and are read by all tenants via cross-schema JOINs.

## Consequences

### Immediate (Alpha)
- `list_all` in `SqlxJobRepository` must be updated to filter by `company_id` (currently returns all jobs regardless of tenant).
- Every new tenant-scoped query must include `company_id` filtering.
- The dev dashboard (which has no auth) operates as a single implicit tenant.

### Future (Production Migration)
- Schema provisioning logic needed on tenant signup.
- Migrations must be applied to all tenant schemas (tooling or CI step).
- API middleware must resolve `company_id` from JWT claims and set `search_path` before handling requests.
- Connection pooler (e.g., PgBouncer) must support schema-aware connection routing.

## Impact on Domain Model

- **No changes** — `company_id` scoping is already baked into the Job aggregate, Client aggregate, SavedBuilding entity, and all tenant-facing repositories.
- The split between global and tenant data maps directly to the existing module boundaries: CRM/Assets (global) vs tenant module + Jobs (tenant).

## References

- [ADR-0017: Independent Plumber Tenancy](0017-independent-plumber-tenancy.md)
- [Client Aggregate Spec](../2-during-implementation/DDD/ModuleDesign/CRM/Clients/Client_Aggregate.md)
- [ADR-0021: Client-Centric Portfolio](0021-client-centric-portfolio.md)
- [ADR-0022: Building Bookmarks](0022-building-bookmarks.md)
- [Database Schema Reference](../2-during-implementation/DDD/DataDesign/DatabaseSchema.md)
- [Auth Design Worksheet — Concept 9: Multi-Tenancy](../design-worksheets/auth.md)
