# Clients Sub-Module (CRM)

> **Parent:** [CRMModule](../README.md)
> **Source of Truth:** Not yet implemented — Phase 1.5
> **ADR:** [ADR-0021: Client-Centric Portfolio](../../../../adr/0021-client-centric-portfolio.md)

## Purpose

This sub-module manages **the firm's clients** — the people and organizations that commission work. It answers the question: "Who are we doing work for?"

Per ADR-0021, the Client replaces the earlier `TenantAsset` concept. The tenant portfolio centers on clients, not buildings.

## Aggregates

### [Client](./Client_Aggregate.md)
**Identity:** UUID, scoped by `company_id`.
**Responsibility:** A contact card for the person or entity that commissions work.
- Name, phone, address
- Block/unblock for non-payment or unreliability
- Buildings and job history derived from `jobs` table, not stored on the client

## Relationships

- **Consumed by:** `JobsModule` — Jobs reference `client_id`.
- **Depends on:** `UsersModule/Company` — Client is scoped by `company_id`.
- **References:** Global `buildings` — indirectly, through job history.

## Data Structures

- `clients` table (see [Client_Aggregate.md](./Client_Aggregate.md) for schema).

## Research

- [Tenant Portfolio Research](../Operations/Research/TENANT_PORTFOLIO_RESEARCH.md) — domain evidence behind this design.
