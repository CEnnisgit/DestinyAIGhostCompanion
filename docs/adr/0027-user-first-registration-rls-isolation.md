# ADR-0027: User-First Registration, Multi-Company Membership, and RLS Tenant Isolation

**Status:** Accepted (RLS section evolved by [ADR-0030](./0030-workspace-isolation-abstraction.md))  
**Date:** 2026-03-29  
**Deciders:** Marcus, AI Pair Programming  

## Context

PCD needs a registration model, a business model, and a data isolation strategy. These three concerns are interrelated — the registration flow determines the User-Company relationship, the business model determines who can create companies, and the isolation strategy determines how tenant data is protected.

### The Story

Marcus's father is a plumber who works across three companies:

1. His own LLC (he is the owner/ADMIN)
2. His friend Danny's LMP company (he is a QI/TECHNICIAN working under Danny's license)
3. A larger plumbing firm (subcontract work)

This means the system must support **one person belonging to multiple companies** with different roles in each. Additionally, PCD handles NYC DOB compliance data — tenant isolation must be robust enough that a bug in application code cannot leak Company A's inspection data to Company B.

## Decision

### 1. User-First Registration

The **User** is the anchor entity. A person creates an account first, then creates or joins companies.

```text
Sign Up (person)
    │
    ├──→ Free Tier: browse buildings, view obligations
    │
    └──→ Upgrade: create a company (paid subscription)
         OR accept invite to join existing company
```

- Users exist independently of companies
- A free-tier user has no company context — they can use basic features (building search, compliance lookup)
- Company creation requires a paid subscription
- Company creation will require verification (future: license validation against NYC DOB)

### 2. Multi-Company Membership

Users relate to companies through a **membership junction table**, not a direct FK:

```sql
CREATE TABLE company_memberships (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    company_id  UUID NOT NULL REFERENCES companies(id),
    role        TEXT NOT NULL DEFAULT 'TECHNICIAN',
    is_primary  BOOLEAN NOT NULL DEFAULT false,
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, company_id),
    CONSTRAINT chk_role CHECK (role IN ('ADMIN', 'TECHNICIAN'))
);
```

- A user can be ADMIN in one company and TECHNICIAN in another
- `is_primary` marks the user's default company context
- When logging in, the user operates in their primary company context by default
- Context switching (selecting a different company) updates the active session

### 3. RLS Tenant Isolation

> [!NOTE]
> **Evolution (2026-03-30):** This section originally used `company_id` as the RLS isolation key. [ADR-0030](./0030-workspace-isolation-abstraction.md) introduces the Workspace Abstraction, which replaces `company_id` with `workspace_id` as the universal isolation boundary. This supports personal workspaces (for users with no company) alongside company workspaces.

Tenant data isolation is enforced at the **database level** using PostgreSQL Row-Level Security, not just application-level query filters.

```sql
-- Enable RLS on tenant-scoped tables
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_buildings ENABLE ROW LEVEL SECURITY;

-- Policy: rows are only visible for the active workspace context
CREATE POLICY workspace_isolation ON jobs
    USING (workspace_id = current_setting('app.workspace_id')::uuid);
```

**How it works in practice:**

1. User authenticates → JWT contains `user_id`
2. User selects context (personal / Company A / Company B) → API resolves the corresponding `workspace_id`
3. API middleware sets `app.workspace_id` PostgreSQL session variable for RLS
4. All queries automatically filtered by RLS — even if application code forgets the filter
5. Phase 3E Connections can create controlled exceptions via policy additions

## Alternatives Considered

### Database-per-tenant

Each company gets its own PostgreSQL database for maximum physical isolation.

**Rejected.** The operational cost (N databases, N migration runs, N connection pools) is disproportionate for the current scale. Cross-company queries (Phase 3E Connections) become extremely complex — jobs in different databases can't be JOINed. RLS provides equivalent isolation guarantees without the operational burden.

### Direct `users.company_id` FK (singular)

User belongs to exactly one company via a direct foreign key.

**Rejected for the full model.** This blocks multi-company membership. For alpha, the implementation may use a simplified model with a single membership per user, but the schema should use the junction table from the start to avoid a migration.

### Company-first registration

The company is created first, then users are invited into it.

**Rejected.** A solo plumber IS their company — forcing them to register a "company" entity before they can do anything feels bureaucratic. User-first is more natural: sign up, use basic features, upgrade when you need company features.

## Implications

### For Phase 3A (Data Foundation)

- `users` table has NO `company_id` column — the relationship goes through `company_memberships`
- `company_memberships` table is created alongside `users` and `companies`
- For alpha: each seeded user gets exactly one membership
- `subscription_tier` on users is a future consideration (post-alpha, when paid tiers are implemented)

### For Phase 3B (Authentication)

- JWT contains `user_id` (the person) — NOT `company_id` or `workspace_id`
- Active workspace context is determined by: UI selection, default personal workspace, or request header
- API middleware sets `app.workspace_id` PostgreSQL session variable for RLS

### For Phase 3C (Authorization)

- RBAC role comes from `workspace_memberships` context (via `company_memberships` for company workspaces)
- A user can be ADMIN in Company A's workspace and TECHNICIAN in Company B's workspace
- RLS policies applied to all tenant-scoped tables using `workspace_id`
- Role checks must be scoped to the active workspace context

### For Phase 3E (Professional Network)

- Connections remain user-to-user (unchanged)
- Cross-company visibility via connections uses RLS policy exceptions
- Multi-company membership and connections are complementary but distinct:
  - **Membership** = "I work at this company" (has a role, sees all company data)
  - **Connection** = "I know this person" (selective sharing of specific items)

## References

- [ADR-0017: Independent Plumber Tenancy](./0017-independent-plumber-tenancy.md) — *partially superseded by this ADR*
- [ADR-0026: Professional Network Connections](./0026-professional-network-connections.md)
- [Vision: Registration and Tenancy](../vision/REGISTRATION_AND_TENANCY.md)
- [Phase 3A: Data Foundation](../roadmap/PHASE_3A_DataFoundation.md)
