# Company Aggregate Specification

**Module:** `IAM`
**Sub-Module:** `Company`
**Source of Truth:** `crates/pcd-domain/src/iam/company.rs` (Phase 3A, not yet implemented)
**Version:** 1.1.0 (Updated for Workspace model)
**ADR:** [ADR-0027](../../../../adr/0027-user-first-registration-rls-isolation.md), [ADR-0030](../../../../adr/0030-workspace-isolation-abstraction.md), [ADR-0032](../../../../adr/0032-derived-workspace-access.md)

---

## 1. Objective

The Company aggregate represents **the tenant container** — an organization (or solo practitioner's LLC) that scopes all operational data. Jobs, clients, saved buildings, and findings all belong to a company.

It answers the following domain questions:

- What is the name and contact info for this business?
- Which workspace isolates this company's operational data?

The Company aggregate does **not** answer:

- Who works at this company (that's User + CompanyMembership)
- What subscription tier the company is on (future business model concern)
- What licenses the company holds (deferred to Phase 3D)
- How data isolation is enforced (that's RLS policy, Phase 3C)

---

## 2. Core Decisions

### 2.1 Enriching an Existing Stub

The `companies` table already exists as a stub with `id`, `name`, `company_type`. This spec adds contact info fields. The Company aggregate in the Rust domain layer is **new** — no domain struct exists today.

### 2.2 Minimal for Alpha

Company registration is not an alpha feature. Alpha companies are seeded manually. Per ADR-0027, registration fields (LLC number, DOB business license, insurance) are deferred to Phase 3D (Profile Enrichment).

### 2.3 Workspace-Based Data Isolation

Every company gets a dedicated **workspace** (`workspace_type = 'COMPANY'`). All company-scoped tables (jobs, clients, saved_buildings, findings, photos) use `workspace_id` as their isolation FK. In Phase 3C, RLS policies enforce isolation at the database level. For now, isolation is application-level (query filters). See [ADR-0030](../../../../adr/0030-workspace-isolation-abstraction.md).

---

## 3. What This Aggregate Is

A Company is:

- a tenant container that scopes operational data
- an organization or solo practitioner's LLC
- a basic profile (name, type, contact info)
- the target of RLS policies for data isolation

---

## 4. What This Aggregate Is Not

The Company aggregate is **not**:

- a user directory (users are independent entities linked via memberships)
- a billing entity (subscription/payment is a future concern)
- a license holder (company registration fields are Phase 3D)
- a node in a network (connections are user-to-user per ADR-0026)

---

## 5. Attributes

| Field | Type | Nullable | Description | Authority |
|---|---|---|---|---|
| `id` | UUID | No | PK | Generated |
| `name` | TEXT | No | Company or LLC name. | User input |
| `company_type` | TEXT | No | Type of company (e.g., `PLUMBING_COMPANY`). | User input |
| `workspace_id` | UUID | No | FK → workspaces. Company workspace for data isolation. (ADR-0030) | System |
| `phone` | TEXT | Yes | Business phone number. | User input |
| `address` | TEXT | Yes | Business address. Free-text for alpha. | User input |
| `email` | TEXT | Yes | Business contact email. | User input |
| `created_at` | TIMESTAMPTZ | No | When the company was created. | System |
| `updated_at` | TIMESTAMPTZ | No | When the company was last modified. | System |

### Fields NOT included (with rationale)

| Rejected Field | Reason | When Revisited |
|---|---|---|
| `license_number` | Company registration fields deferred — not alpha scope | Phase 3D |
| `insurance_policy` | Not alpha scope | Phase 3D |
| `website` | Not alpha scope | Phase 3D |
| `timezone` | Settings concern, not identity | Phase 3D |
| `subscription_tier` | Business model concern | Post-alpha |
| `lmp_name` / `lmp_license_number` | Currently on `companies` table via LL152 ALTER — will migrate to user-owned `lmp_credentials` in Session 2 | Phase 3A Session 2 |

---

## 6. Aggregate Behavior

### 6.1 Creation

`Company.create({ name, company_type })`

- `name` is required, must be non-empty after trimming.
- `company_type` is required.

### 6.2 Update Profile

`Company.update_profile({ name?, phone?, address?, email? })`

- Any combination of fields can be updated.
- `name` must be non-empty if provided.

### 6.3 Invariants

- `name` must be non-empty.
- `company_type` must be non-empty.

---

## 7. Why No Events

Company has no domain events in Phase 3A. The same rationale applies as for the User aggregate (see [User_Aggregate.md §9](../People/User_Aggregate.md)):

- Company has no state machine — it has CRUD on profile fields.
- No consumer exists for "company was created" or "profile was updated" today.
- When a cross-cutting event bus is needed (e.g., audit logging, notification system), events should be retrofitted onto User, Client, and Company together as a consistent pattern — not bolted onto one aggregate in isolation.

---

## 8. Persistence

```sql
-- Existing table, enriched with new columns
ALTER TABLE companies ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS email TEXT;
```

The `companies` table already exists with `id`, `name`, `company_type`, `created_at`, `updated_at`. Phase 3A adds `workspace_id` (ADR-0030) and contact fields.

> **Note:** `workspace_id` must reference a row in the `workspaces` table with `workspace_type = 'COMPANY'`. The workspace is created before the company. Company workspace access is **derived** from `company_memberships` — no `workspace_memberships` table exists (ADR-0032).

---

## 9. Relationship to Users (via CompanyMembership)

Users belong to companies through the `company_memberships` junction table. A company can have many members with different roles:

- **ADMIN** — company owner, can create jobs, dispatch, review, manage users
- **TECHNICIAN** — field plumber, can view assigned jobs, submit findings

See [User_Aggregate.md](../People/User_Aggregate.md) and [CompanyMembership.md](../People/CompanyMembership.md) for the full membership spec.

---

## 10. Relationship to Scoped Data

All of the following entities are scoped to a company via its **workspace**:

| Entity | Module | Relationship |
|---|---|---|
| Job | Jobs/Engine | `jobs.workspace_id → company workspace` |
| Client | CRM/Clients | `clients.workspace_id → company workspace` |
| SavedBuilding | CRM/Operations | `saved_buildings.workspace_id → company workspace` |
| LL152 Job Details | Jobs/Workflows/LL152 | Via parent Job's workspace |

---

## 11. Future Considerations (Not in Phase 3A)

- **Company registration flow** — paid subscription required to create a company (ADR-0027 vision)
- **Company verification** — license validation against NYC DOB database
- **Extended profile fields** — LLC number, insurance, timezone, branding (Phase 3D)
- **Company settings** — notification preferences, default timezone
- **LMP fields migration** — `lmp_name` and `lmp_license_number` columns on `companies` will be migrated to user-owned `lmp_credentials` in Phase 3A Session 2
