# Phase 1.5: Tenant Foundation

> **Status:** ✅ Complete (2026-03-27)
> **Objective:** Introduce the minimal tenant concepts needed to make Jobs client-aware and give firms a building save feature — without implementing auth, RBAC, or user profiles.
> **ADRs:** [0017 (Independent Plumber)](../adr/0017-independent-plumber-tenancy.md), [0018 (Client vs Requester)](../adr/0018-client-account-vs-requester-contact.md), [0020 (DB Isolation)](../adr/0020-multi-tenancy-database-isolation.md), [0021 (Client-Centric Portfolio)](../adr/0021-client-centric-portfolio.md), [0022 (Building Bookmarks)](../adr/0022-building-bookmarks.md)

---

## Why Phase 1.5 Exists

Phase 1 built the Job Engine with `company_id` and `client_id` fields — but nothing in the system represents a company or a client. Phase 2 will add the LL152 workflow, which inherits tenant scope from the parent Job. Phase 3 adds full auth and RBAC.

The gap: **between Phase 1 and Phase 3, there's no Client entity, no Company table, and no way for firms to track buildings of interest.**

Phase 1.5 fixes this with three lightweight concepts:

| Concept | What it does | ADR |
|---|---|---|
| **Company (stub)** | Gives `company_id` referential integrity | [0017](../adr/0017-independent-plumber-tenancy.md) |
| **Client** | Person/org that commissions work (name, phone, address) | [0021](../adr/0021-client-centric-portfolio.md) |
| **Saved Building** | Bookmark a building from the Explorer, no client required | [0022](../adr/0022-building-bookmarks.md) |

---

## What Stays in Phase 3

| Concept | Why it's deferred |
|---|---|
| Auth (JWT, password reset) | Not needed for dev dashboard testing |
| RBAC (roles as capabilities) | Not needed until multi-user scenarios |
| User profiles (Technician, LMP) | Not needed for 2 alpha users |
| Company settings, license info | Alpha-later concern |
| Client contacts sub-entities | Keep it simple — one phone number for now |

---

## Domain Model

### Company (Stub)

Per ADR-0017, "company" = firm or solo plumber. The stub gives `company_id` a real table.

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    company_type TEXT NOT NULL DEFAULT 'independent', -- 'firm' | 'independent'
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Dev seed
INSERT INTO companies (id, name, company_type)
VALUES ('00000000-0000-0000-0000-000000000001', 'Dev Test Company', 'firm');
```

### Client

Per ADR-0021 and the [Client Aggregate spec](../2-during-implementation/DDD/ModuleDesign/CRM/Clients/Client_Aggregate.md).

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    is_blocked BOOLEAN NOT NULL DEFAULT false,
    blocked_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_blocked_reason CHECK (
        (is_blocked = true AND blocked_reason IS NOT NULL) OR
        (is_blocked = false AND blocked_reason IS NULL)
    )
);
CREATE INDEX idx_clients_company ON clients(company_id);
```

### Saved Building (Bookmark)

Per ADR-0022. No aggregate spec — just a junction entity.

```sql
CREATE TABLE saved_buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    building_id UUID NOT NULL REFERENCES buildings(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(company_id, building_id)
);
CREATE INDEX idx_saved_buildings_company ON saved_buildings(company_id);
```

---

## Implementation Plan

### Rust Domain (`crates/pcd-domain/src/tenant/`)

```
mod.rs               ← module exports
client.rs            ← Client struct, create/update/block/unblock
saved_building.rs    ← SavedBuilding struct
repository.rs        ← ClientRepository + SavedBuildingRepository traits
```

### Rust Persistence (`crates/pcd-db/src/tenant/`)

```
mod.rs
companies.rs         ← SqlxCompanyRepository (minimal)
clients.rs           ← SqlxClientRepository
saved_buildings.rs   ← SqlxSavedBuildingRepository
```

### Rust API (`crates/pcd-api/src/routes/`)

```
tenant.rs
  GET    /api/clients              ← list by company_id
  POST   /api/clients              ← create
  PATCH  /api/clients/:id          ← update contact info
  POST   /api/clients/:id/block    ← block with reason
  POST   /api/clients/:id/unblock  ← unblock

  GET    /api/saved-buildings          ← list by company_id
  POST   /api/saved-buildings          ← save (company_id, building_id)
  DELETE /api/saved-buildings/:id      ← remove
```

### Impact on Existing Code

| Area | Change |
|---|---|
| `SqlxJobRepository::list_all` | Add `WHERE company_id = $1` filter |
| Job creation flow | Auto-create Client if new client info provided |
| `jobs.client_id` FK | Wire to `clients(id)` once table exists |

---

## Dev Dashboard Testing Plan

1. **Seed dev company** via migration
2. **Create clients** — test name + phone + address input
3. **Create job with new client** — verify auto-creation
4. **Block/unblock client** — verify blocked_reason constraint
5. **Save building from Explorer** — verify bookmark appears in saved list
6. **Remove saved building** — verify deletion
7. **View client's buildings** — derived from job history

---

## Exit Criteria

- [x] `companies`, `clients`, `saved_buildings` tables exist
- [x] Client aggregate implemented in Rust domain
- [x] SavedBuilding entity implemented
- [x] API routes for clients + saved buildings
- [x] `SqlxJobRepository::list_all` filters by `company_id`
- [x] Job creation auto-creates Client when needed
- [x] Dev dashboard can create clients and bookmark buildings
- [x] Existing Phase 0/1 functionality unaffected

