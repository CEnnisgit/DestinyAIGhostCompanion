# ADR-0032: Derived Workspace Access — No Workspace Memberships Table

**Status:** Accepted  
**Date:** 2026-03-30  
**Deciders:** Marcus, AI Pair Programming  
**Related:** [ADR-0030](./0030-workspace-isolation-abstraction.md) (Workspace Abstraction)

## Context

ADR-0030 establishes the Workspace as the universal data isolation boundary. Every user gets a personal workspace, every company gets a company workspace, and all tenant-scoped tables use `workspace_id` for RLS.

The initial design proposed a `workspace_memberships` table to map users to their accessible workspaces. However, workspace access is entirely derivable from existing domain relationships:

- **Personal workspace:** The user who owns it (stored as `users.personal_workspace_id`)
- **Company workspace:** Users who are members of the company (stored in `company_memberships` + `companies.workspace_id`)
- **Team workspace (Beta):** Users who are members of the team (stored in `team_memberships` + `teams.workspace_id`)

Storing this derived data in a separate table creates a **synchronization problem**: every time a `company_membership` is added or removed, a corresponding `workspace_membership` must also be updated. If they fall out of sync, a user could have a role but no data access, or data access but no role.

## Decision

**Do not create a `workspace_memberships` table.** Workspace access is computed at query time from existing domain relationships.

### Schema

```sql
-- Workspaces: thin isolation boundary
CREATE TABLE IF NOT EXISTS workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_type  TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_workspace_type CHECK (workspace_type IN ('PERSONAL', 'COMPANY'))
);

-- Users reference their personal workspace
ALTER TABLE users ADD COLUMN personal_workspace_id UUID NOT NULL REFERENCES workspaces(id);

-- Companies reference their company workspace
ALTER TABLE companies ADD COLUMN workspace_id UUID NOT NULL REFERENCES workspaces(id);
```

### Workspace Access Query

To resolve "what workspaces can this user access?" — used by middleware and portfolio queries:

```sql
-- All workspaces accessible to a given user
SELECT u.personal_workspace_id AS workspace_id, 'OWNER' AS role, 'PERSONAL' AS workspace_type
FROM users u
WHERE u.id = $user_id

UNION ALL

SELECT c.workspace_id, cm.role, 'COMPANY' AS workspace_type
FROM company_memberships cm
JOIN companies c ON c.id = cm.company_id
WHERE cm.user_id = $user_id;
```

When Teams are implemented (Beta), add:

```sql
UNION ALL

SELECT t.workspace_id, tm.role, 'TEAM' AS workspace_type
FROM team_memberships tm
JOIN teams t ON t.id = tm.team_id
WHERE tm.user_id = $user_id;
```

### Portfolio Query

To fetch all jobs across all of a user's workspaces:

```sql
SELECT j.*
FROM jobs j
WHERE j.workspace_id IN (
    SELECT u.personal_workspace_id FROM users u WHERE u.id = $user_id
    UNION ALL
    SELECT c.workspace_id FROM company_memberships cm
    JOIN companies c ON c.id = cm.company_id
    WHERE cm.user_id = $user_id
);
```

## Alternatives Considered

### Dedicated `workspace_memberships` table

A separate table mapping users to workspaces with access roles.

**Rejected.** Creates a synchronization problem — every domain membership change (company join/leave, team join/leave) must be mirrored in `workspace_memberships`. If they fall out of sync, the system has invisible bugs. The data is fully derivable from existing relationships, so storing it separately adds risk without benefit.

### Database VIEW for workspace access

Create a `user_workspace_access` VIEW that unions the domain tables automatically.

**Deferred, not rejected.** This is a valid optimization if the UNION query becomes a performance hotspot. For alpha scale (2 users, 2-3 companies), the raw query is fine. A VIEW or materialized view can be introduced later without schema changes.

## Implications

### For Phase 3A

- `workspaces` table created in Session 1 (before `users` and `companies`)
- `users` gets `personal_workspace_id` FK
- `companies` gets `workspace_id` FK
- No `workspace_memberships` table
- Seeding creates personal workspaces for each user and company workspaces for each company

### For Phase 3B (Middleware)

- Middleware resolves workspace context by running the access query above
- Sets `app.workspace_id` session variable from the result
- Default context = personal workspace (if no company context specified)

### For Beta (Teams)

- `teams` table gets a `workspace_id` FK
- `team_memberships` table maps users to teams
- The access query gains another `UNION ALL` — no schema changes to existing tables

### Design Principle

> **Domain tables own relationships. Workspace access is derived, not stored.**
>
> `company_memberships` answers "who works where?" (domain question).  
> Workspace access answers "what data can they see?" (infrastructure question).  
> The second is always computable from the first.

## References

- [ADR-0030: Workspace Abstraction](./0030-workspace-isolation-abstraction.md)
- [ADR-0027: User-First Registration](./0027-user-first-registration-rls-isolation.md)
