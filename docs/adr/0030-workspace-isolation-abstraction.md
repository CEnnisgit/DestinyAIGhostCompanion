# ADR-0030: Workspace Abstraction for Data Isolation

**Status:** Accepted  
**Date:** 2026-03-30  
**Deciders:** Marcus, AI Pair Programming  
**Supersedes:** [ADR-0020](./0020-multi-tenancy-database-isolation.md) (row-level → schema-level migration path replaced by workspace + RLS)

## Context

PCD is a **person-centric** application. A plumber signs up as an individual, creates their own jobs and clients from day one, and may optionally create or join companies. The app supports three distinct contexts that can own operational data:

1. **Personal** — a solo plumber's own jobs, clients, and work
2. **Company** — a verified, licensed business entity with employees
3. **Team** — a lightweight coordination group of individual users (Beta, deferred)

The previous isolation model assumed `company_id` as the universal tenant boundary (ADR-0020, ADR-0027). This is architecturally wrong because:

- A free-tier user with no company can create jobs and manage clients. Those jobs have no `company_id`.
- Adding `owner_user_id` as a second isolation column creates branching RLS policies that grow in complexity with each new context type.
- When Teams arrive (Beta), a third isolation column would be needed, compounding the problem.

### The Story

Marcus's father:
- Has personal jobs he creates for his own work (no company context)
- Has jobs from his own LLC (Company A)
- Has jobs assigned to him by Danny's firm (Company B)
- Has jobs from a larger firm (Company C)

His portfolio aggregates across **four distinct contexts**. The isolation model must support all of them with a single, uniform mechanism.

## Decision

Introduce a **Workspace** as the universal data isolation boundary. Every piece of tenant-scoped data belongs to exactly one workspace.

### Core Entity

```sql
CREATE TABLE workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_type  TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_workspace_type CHECK (workspace_type IN ('PERSONAL', 'COMPANY', 'TEAM'))
);
```

### Workspace Lifecycle

- **Every user** gets a personal workspace automatically on signup (`workspace_type = 'PERSONAL'`)
- **Every company** gets a company workspace on registration (`workspace_type = 'COMPANY'`)
- **Every team** (Beta) gets a team workspace on creation (`workspace_type = 'TEAM'`)

### Data Isolation

All tenant-scoped tables use `workspace_id` as their isolation FK:

```sql
-- Example: jobs table
CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id),
    -- ... other fields
);

-- Single, uniform RLS policy
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY workspace_isolation ON jobs
    USING (workspace_id = current_setting('app.workspace_id')::uuid);
```

### Workspace Access

Workspace access is **derived from domain relationships**, not stored in a separate table (see [ADR-0032](./0032-derived-workspace-access.md)):

- **Personal workspace:** Found via `users.personal_workspace_id`
- **Company workspace:** Found via `company_memberships` → `companies.workspace_id`
- **Team workspace (Beta):** Found via `team_memberships` → `teams.workspace_id`

### Portfolio Query

A user's full portfolio = all data across all their workspaces:

```sql
SELECT j.*
FROM jobs j
WHERE j.workspace_id IN (
    -- Personal workspace
    SELECT u.personal_workspace_id FROM users u WHERE u.id = $1
    UNION ALL
    -- Company workspaces
    SELECT c.workspace_id FROM company_memberships cm
    JOIN companies c ON c.id = cm.company_id
    WHERE cm.user_id = $1
);
```

### Job Transfer Between Contexts

Moving a job from personal to company (or vice versa) = updating `workspace_id`. This is a simple FK update, not a complex migration. The detailed transfer flow (confirmation, audit trail, permissions) is deferred to Phase 3E.

## Alternatives Considered

### Alternative A: Dual-Column RLS (`company_id` nullable + `owner_user_id`)

Every tenant-scoped table has both `company_id` (nullable) and `owner_user_id`. RLS policy branches on which is set.

**Rejected.** This works for two contexts (personal + company), but adding Teams requires a third nullable FK and another OR branch in every RLS policy. The complexity compounds with each new context type. The RLS policies become fragile and hard to audit.

### Alternative B: Context Enum + Multiple Nullable FKs

Add `context_type TEXT` to each table and branch on it.

**Rejected.** Same fundamental problem as Alternative A — multiple nullable FKs, branching logic, growing complexity. The enum adds explicitness but doesn't reduce the structural problem.

### Alternative C: Deterministic Workspace IDs (no table)

Use `user_id` as the personal workspace_id and `company_id` as the company workspace_id. No `workspaces` table — just a convention.

**Rejected.** Clever but fragile. Loses the ability to query workspace metadata, enforce type constraints, or extend the pattern cleanly. The cost of an explicit table is minimal; the benefit is significant.

## Implications

### For Phase 3A (Data Foundation)

- `workspaces` table is created alongside `users` and `companies`
- Every user gets a personal workspace on creation (`users.personal_workspace_id`)
- Every company gets a company workspace on creation (`companies.workspace_id`)
- No `workspace_memberships` table — access is derived (ADR-0032)
- Existing tenant-scoped tables (`jobs`, `clients`, `saved_buildings`) will use `workspace_id` instead of `company_id` when IAM migration runs

### For Phase 3B (Authentication)

- JWT contains `user_id` (unchanged)
- Active workspace context determined by: UI selection, default personal workspace, or request header
- API middleware sets `app.workspace_id` PostgreSQL session variable for RLS

### For Phase 3C (Authorization)

- Role comes from workspace membership context, not a global user role
- A user can have different roles in different workspaces
- RLS policies use `workspace_id` uniformly

### For Phase 3E (Professional Network)

- Job hand-offs between connections = transferring `workspace_id` from one personal workspace to another
- Cross-workspace collaboration uses RLS policy exceptions (same mechanism as before, but on workspace_id instead of company_id)

### For Beta (Teams)

- A Team gets a `TEAM` workspace
- No schema changes to `jobs`, `clients`, etc. — they already use `workspace_id`
- Team access derived via `team_memberships` → `teams.workspace_id` (same pattern as companies)
- The pattern is already in place

### What the Workspace Is NOT

- **Not a god object.** It is a thin isolation boundary: id, type, timestamps. Features live on User, Company, Team — not on Workspace.
- **Not replacing Company or User.** Companies and users are domain entities with their own attributes, behavior, and specs. Workspace is infrastructure.
- **Not a UI concept.** Users don't think in "workspaces." They think in "my jobs," "Company A's jobs," "my team's jobs." The workspace is the backend mechanism that makes those views work.

## References

- [ADR-0020: Multi-Tenancy Database Isolation](./0020-multi-tenancy-database-isolation.md) — superseded migration path
- [ADR-0027: User-First Registration](./0027-user-first-registration-rls-isolation.md) — user-first model this builds on
- [ADR-0032: Derived Workspace Access](./0032-derived-workspace-access.md) — no workspace_memberships table
- [Vision: Registration and Tenancy](../vision/REGISTRATION_AND_TENANCY.md)
