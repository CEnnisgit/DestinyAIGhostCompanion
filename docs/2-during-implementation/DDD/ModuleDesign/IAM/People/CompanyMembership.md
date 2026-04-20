# CompanyMembership — Schema Specification

**Module:** `IAM`
**Sub-Module:** `People`
**Source of Truth:** `crates/pcd-db/src/iam/` (Phase 3A, not yet implemented)
**Version:** 3.0.0 (Infrastructure-only — lifecycle deferred to Phase 3M per ADR-0029)
**ADRs:** [ADR-0027](../../../../adr/0027-user-first-registration-rls-isolation.md), [ADR-0029](../../../../adr/0029-phase3-decomposition-membership-entitlements.md), [ADR-0030](../../../../adr/0030-workspace-isolation-abstraction.md), [ADR-0032](../../../../adr/0032-derived-workspace-access.md)

---

## 1. What This Is in Phase 3A

CompanyMembership is a **junction table** that links users to companies. In Phase 3A, it is **structural infrastructure** — not a domain entity with lifecycle behavior.

It exists because:

- **Workspace access derivation needs it.** Company workspace access is derived from this table: `company_memberships` → `companies.workspace_id` (ADR-0032). The middleware queries this to resolve which workspaces a user can access.
- **RLS needs it.** The auth middleware derives the active workspace, then sets `app.workspace_id` for PostgreSQL Row-Level Security (ADR-0030).
- **Role checks need it.** Phase 3C.1 authorization checks the `role` column to enforce admin vs. technician permissions.
- **Company context needs it.** The `is_primary` column determines which company a user sees by default after login.

It does **not** have domain behavior in Phase 3A:

- No invitation/acceptance flow
- No lifecycle commands (add, remove, role change)
- No domain events
- No aggregate root ownership

Data is **seeded** via scripts. The table is **queried** by middleware. The domain model does **not** manage it.

---

## 2. Schema

| Field        | Type   | Nullable | Description                                    | Source          |
| :----------- | :----- | :------- | :--------------------------------------------- | :-------------- |
| `id`         | UUID   | No       | PK                                             | Generated       |
| `user_id`    | UUID   | No       | FK → users. The person.                        | Seed / System   |
| `company_id` | UUID   | No       | FK → companies. The tenant container.          | Seed / System   |
| `role`       | TEXT   | No       | `ADMIN` or `TECHNICIAN`.                       | Seed / Admin    |
| `is_primary` | BOOLEAN | No      | Default: false. User's default company context. | Seed / User     |
| `joined_at`  | TIMESTAMPTZ | No  | When the membership was created.               | System          |

### Role Semantics (for authorization middleware)

| Role         | Capabilities                                                     |
| :----------- | :--------------------------------------------------------------- |
| `ADMIN`      | Everything TECHNICIAN can do, plus: invite users, edit company profile, manage billing, create/dispatch jobs |
| `TECHNICIAN` | View assigned jobs, submit findings, capture photos              |

ADMIN is a superset of TECHNICIAN.

---

## 3. Persistence

```sql
CREATE TABLE IF NOT EXISTS company_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    role TEXT NOT NULL DEFAULT 'TECHNICIAN',
    is_primary BOOLEAN NOT NULL DEFAULT false,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_membership_user_company UNIQUE (user_id, company_id),
    CONSTRAINT chk_membership_role CHECK (role IN ('ADMIN', 'TECHNICIAN'))
);

CREATE INDEX IF NOT EXISTS idx_memberships_user ON company_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_company ON company_memberships(company_id);
```

---

## 4. Read Queries (used by middleware and projections)

| Query | Used By | SQL |
| :--- | :--- | :--- |
| Resolve all workspaces for user | Auth middleware (3B) | `SELECT u.personal_workspace_id ... UNION ALL SELECT c.workspace_id FROM company_memberships cm JOIN companies c ...` (ADR-0032) |
| Resolve company context for user | Auth middleware (3B/3C.1) | `SELECT company_id, role, is_primary FROM company_memberships WHERE user_id = ?` |
| Check if user belongs to company | Authorization (3C.1) | `SELECT EXISTS(SELECT 1 FROM company_memberships WHERE user_id = ? AND company_id = ?)` |
| Get user's role in company | Authorization (3C.1) | `SELECT role FROM company_memberships WHERE user_id = ? AND company_id = ?` |
| List members of a company | Read projection | `SELECT u.* FROM users u JOIN company_memberships cm ON u.id = cm.user_id WHERE cm.company_id = ?` |

---

## 5. What Phase 3M Will Add

When Phase 3M (Membership Lifecycle) is designed, this spec will expand to include:

- **Domain entity status:** CompanyMembership becomes a child entity of the User aggregate
- **MembershipRole enum:** Rust enum replacing the TEXT column at the domain level
- **Lifecycle states:** INVITED → ACTIVE → SUSPENDED (possible)
- **Domain behavior:** invitation, acceptance, role change, join/leave/remove
- **Actor tracking:** who performed each membership action
- **Primary context switching UX:** persistent vs. session-level context
- **Membership cardinality limits:** if needed for abuse prevention

> See [ADR-0029](../../../../adr/0029-phase3-decomposition-membership-entitlements.md) for the full rationale.

---

## 6. Cross-References

- **Related:** [User Aggregate](./User_Aggregate.md) — identity anchor
- **Related:** [Company Aggregate](../Company/Company_Aggregate.md) — the tenant container
- **ADR:** [ADR-0027](../../../../adr/0027-user-first-registration-rls-isolation.md) — user-first, multi-company membership model
- **ADR:** [ADR-0029](../../../../adr/0029-phase3-decomposition-membership-entitlements.md) — membership behavior deferred to Phase 3M
- **ADR:** [ADR-0030](../../../../adr/0030-workspace-isolation-abstraction.md) — workspace isolation boundary
- **ADR:** [ADR-0032](../../../../adr/0032-derived-workspace-access.md) — workspace access derived from this table
