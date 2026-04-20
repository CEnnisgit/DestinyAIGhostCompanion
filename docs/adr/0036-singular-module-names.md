# ADR-0036: Singular Module Names Across All Crates

> **Status:** Accepted
> **Date:** 2026-04-02
> **Deciders:** Marcus (product owner)
> **Relates To:** ADR-0028 (IAM module restructuring)

## Context

During Phase 3A implementation, the `pcd-db` crate had accumulated plural module names (`jobs.rs`, `clients.rs`, `saved_buildings.rs`) — a convention borrowed from Rails/Django where files map to database tables (which are named as collections).

Meanwhile, `pcd-domain` used singular names (`job.rs`, `client.rs`, `email.rs`) — consistent with Rust convention where a module represents a single concept, not a collection.

This inconsistency would proliferate as new IAM repository files were added, creating confusion about which convention to follow.

## Decision

**All Rust module files use singular names.** A module represents the concept it encapsulates, not a collection of instances.

### Naming Rules

| What | Convention | Example |
|------|-----------|---------|
| Domain entity files | Singular | `user.rs`, `company.rs`, `email.rs` |
| Repository trait files | `_repository` suffix | `user_repository.rs`, `membership_repository.rs` |
| DB adapter files | Singular (matches domain) | `user.rs`, `company.rs`, `job.rs` |
| Test files | `tests.rs` (co-located) | `company/tests.rs` |
| API route files | Singular | `user.rs`, `company.rs` |

### Rationale

1. **Rust convention:** The standard library uses singular names (`std::collections::hash_map`, not `hash_maps`). Major crates follow the same pattern.
2. **Semantic accuracy:** `pcd_db::iam::user` contains `SqlxUserRepository` — a single adapter for the User entity, not a collection of users.
3. **Cross-crate consistency:** `pcd_domain::iam::people::user` and `pcd_db::iam::user` now share the same naming logic, making it intuitive to navigate between layers.

## Changes Applied

Renamed all existing plural `pcd-db` files to singular:

| Before | After |
|--------|-------|
| `pcd-db/src/operations/jobs.rs` | `pcd-db/src/operations/job.rs` |
| `pcd-db/src/operations/clients.rs` | `pcd-db/src/operations/client.rs` |
| `pcd-db/src/operations/saved_buildings.rs` | `pcd-db/src/operations/saved_building.rs` |

New IAM files created with singular names from the start:

- `pcd-db/src/iam/user.rs`
- `pcd-db/src/iam/company.rs`
- `pcd-db/src/iam/membership.rs`
- `pcd-db/src/iam/lmp_credential.rs`

## Consequences

### Positive

- One clear rule for all contributors: singular, always
- Cross-crate navigation is intuitive (domain `user.rs` → db `user.rs`)
- Consistent with Rust ecosystem conventions

### Negative

- Git history shows renames for 3 existing files (minor, one-time cost)

## References

- [ADR-0028](./0028-iam-module-restructuring.md) — IAM module restructuring
- [Rust API Guidelines: Naming](https://rust-lang.github.io/api-guidelines/naming.html) — community conventions
