# Tenant Foundation — After-Implementation

> **Phase:** 1.5 (Tenant Foundation)
> **Crates:** `pcd-domain/src/tenant/`, `pcd-db/src/tenant/`, `pcd-api/src/routes/tenant.rs`
> **ADRs:** [0017](../../adr/0017-independent-plumber-tenancy.md), [0021](../../adr/0021-client-centric-portfolio.md), [0022](../../adr/0022-building-bookmarks.md)

## Overview

The Tenant module introduces the minimal company-scoped entities needed to make Jobs client-aware and give firms a building bookmark feature. It does not implement auth, RBAC, or user profiles (deferred to Phase 3).

### Three Concepts

| Entity | What It Does | Aggregate? |
|---|---|---|
| **Company** (stub) | Gives `company_id` referential integrity | No — seed-only table |
| **Client** | Person/org that commissions work | Yes — full aggregate with commands |
| **SavedBuilding** | Bookmark a building from the Explorer | No — simple entity (save/remove) |

## Module Docs

| Document | Covers |
|---|---|
| [Domain](./domain.md) | Client aggregate, SavedBuilding entity, company stub |
| [API](./api.md) | REST routes for clients and saved buildings |
| [Repository](./repository.md) | Repository traits and Sqlx implementations |
