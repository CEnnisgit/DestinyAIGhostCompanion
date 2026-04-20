# IAM Module (Identity & Access Management)

> **Source of Truth:** `crates/pcd-domain/src/iam/` (Phase 3A)
> **Scope:** Phase 3A–3D
> **ADRs:** [ADR-0027](../../../adr/0027-user-first-registration-rls-isolation.md), [ADR-0028](../../../adr/0028-iam-module-restructuring.md), [ADR-0030](../../../adr/0030-workspace-isolation-abstraction.md), [ADR-0031](../../../adr/0031-person-first-feature-gating.md), [ADR-0032](../../../adr/0032-derived-workspace-access.md)

## Traceability

> **Refer to:** [TraceabilityMatrix_SFR.md](./TRACEABILITY_SFR.md)

This module manages the **identity and access** layer of PCD. It answers: who are you, what organizations do you belong to, and what professional credentials do you hold?

A User is a person — the durable entity that outlives any single company. Companies are something a User creates or joins. Memberships link the two.

## Sub-Modules

### 1. [Company](./Company/README.md)
**Responsibility:** The Tenant Container.
*   Company Profile (name, contact info).
*   Workspace-based Data Isolation (`workspace_id` scoping via RLS — [ADR-0030](../../../adr/0030-workspace-isolation-abstraction.md)).
*   Subscription tier (free vs paid, future).

### 2. [People](./People/README.md)
**Responsibility:** The People.
*   **User Entity**: A person who can act in the system.
*   **CompanyMembership**: Links users to companies with a role (ADMIN, TECHNICIAN).
*   Multi-company support — one person, multiple company contexts.

### 3. [LmpCredential](./LmpCredential/) *(Session 2)*
**Responsibility:** Professional License Cards.
*   LMP license number, name, expiry, contact info.
*   User-owned (the license belongs to the person, not the company).
*   Attachable to LL152 jobs (replaces text columns on `ll152_job_details`).

## Module Interactions

- **Consumes**: `AuthModule` (Identity verification, Phase 3B).
- **Produces**: `User` + `CompanyMembership` for `Jobs` (actor context, workspace scoping via ADR-0032).
- **Produces**: `LmpCredential` for `LL152` (authorizing LMP on inspection jobs).
- **Produces**: `Workspace` for tenant-scoped data isolation (ADR-0030).
- **Related**: [Professional Network](../../../vision/PROFESSIONAL_NETWORK.md) (Phase 3E) — user-to-user connections.
