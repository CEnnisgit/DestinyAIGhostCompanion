# Rust Migration — Deferred Backlog

> Created: 2026-03-20 after CRM + Jobs audit on `refactor/rust-backend`
> Context: TS → Rust migration complete. All parity fixes merged. These items remain.

---

## Low Priority — Do When Convenient

### M9: Anomaly Sort Direction
- **Where**: `crates/pcd-db/src/crm/anomalies.rs`
- **What**: The old TS had `sortDate` param (asc/desc). Rust defaults to insertion order.
- **Effort**: Add one `ORDER BY` clause + one query param. ~5 lines.

### J1: Typed Event Payload Structs
- **Where**: `crates/pcd-domain/src/jobs/events.rs`
- **What**: Only `JobOpenedPayload` has a typed struct. The other 10 job events use `serde_json::json!()`.
- **Risk**: Compile-time type safety on event shapes. Currently works fine with JSON.
- **Effort**: Add 10 small structs, update event emission sites. ~80 lines.

### J3: Extract OpenJobUseCase
- **Where**: `crates/pcd-api/src/routes/jobs.rs` → new `crates/pcd-api/src/use_cases/`
- **What**: `create_job` handler inlines the use case logic. Extract to separate struct when a second caller needs it (CLI, worker, etc).
- **Effort**: ~30 lines.

---

## Do When Building Jobs UI

### J4: 7 Missing Jobs API Endpoints
- **Where**: `crates/pcd-api/src/routes/jobs.rs`
- **What**: Domain commands exist but have no HTTP routes:
  - `PATCH /{id}/summary` → `job.update_summary()`
  - `PATCH /{id}/site-notes` → `job.update_site_notes()`
  - `PATCH /{id}/priority` → `job.update_priority()`
  - `PATCH /{id}/client` → `job.attach_client()`
  - `PATCH /{id}/assign` → `job.assign_ownership()`
  - `PATCH /{id}/link-obligation` → `job.link_obligation()`
  - `PATCH /{id}/unlink-obligation` → `job.unlink_obligation()`
- **Note**: The TS adapter was a stub — these never worked in either stack. Not a regression.

---

## Future Roadmap (Phase 1 Inspection)

### J5: LL152 Workflow Module
- **ADR**: ADR-0016 (Pluggable Workflows)
- **What**: Engine/workflow separation requires `ll152_job_details` extension table and LL152 workflow program. Neither TS nor Rust had any implementation.
- **When**: Phase 1 Inspection work begins.

---

## Separate PRs (Not Migration Scope)

### Drizzle Schema Removal
- **Where**: `packages/crm/` (Drizzle ORM schema)
- **What**: Old TS Drizzle schema still exists. Dev dashboard seed/wipe uses it. Rewrite as raw SQL.
- **Risk**: Low — doesn't interfere with Rust stack. Creates confusion for new contributors.

### Condo CHECK Constraints
- **Where**: SQL migration
- **What**: 5 CHECK constraints on `condo_status`, `condo_status_evidence`, etc. documented in Building_Aggregate.md but not enforced at DB level.
- **Risk**: Low — only controlled pipelines write data. But should be added for correctness.

### Stale Doc Paths
- **Files**: 3 doc files reference old TS module paths that no longer exist.
- **Effort**: ~10 minutes of find-replace.
