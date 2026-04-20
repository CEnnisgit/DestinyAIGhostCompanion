# CRM Operations Sub-Module

> **Scope:** Tenant-Specific Data & Relationships
> **Role:** The "Firm's View" — client relationships and saved buildings.

## Purpose

This sub-module manages data that is private to a specific firm (tenant), while referencing global data from the `Assets` sub-module.

## Current State (Phase 1.5)

The Operations module is now implemented through the **tenant domain module** in Rust:

- **Client** — person/org that commissions work (name, phone, address, block/unblock)
  - See: [Client Aggregate Spec](../Clients/Client_Aggregate.md)
  - ADR: [0021 — Client-Centric Portfolio](../../../../adr/0021-client-centric-portfolio.md)

- **Saved Building** — bookmark a building from the Explorer (no client required)
  - ADR: [0022 — Building Bookmarks](../../../../adr/0022-building-bookmarks.md)

## Historical Context

The original design proposed `TenantAsset(FirmID, BIN)` as the core entity. Domain research revealed this was the wrong abstraction — plumbers manage relationships with **clients**, not buildings. Buildings are global locations referenced through job history.

See: [Tenant Portfolio Research](Research/TENANT_PORTFOLIO_RESEARCH.md) for the full analysis.

## Relationships

- **Depends On:** `Assets` (for Building identity)
- **Used By:** `Jobs` (jobs reference `client_id` and `building_id`)
