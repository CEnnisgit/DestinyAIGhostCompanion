# Phase 3M: Membership Lifecycle

> **Status:** 🔲 Not Started
> **Objective:** Design and implement the full organizational membership model — how users join, leave, and operate within companies.
> **Depends On:** Phase 3B ✅ (need authenticated subjects for membership actions)
> **ADRs:** [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md), [ADR-0030](../adr/0030-workspace-isolation-abstraction.md) (workspace context), [ADR-0032](../adr/0032-derived-workspace-access.md) (derived access)
> **Branch:** `phase3m/membership-lifecycle`

---

## Why This Sub-Phase Exists

Phase 3A created the `company_memberships` junction table as infrastructure — seeded data, no domain behavior. Phase 3B added auth. But there is no way to:

- Invite someone to join a company
- Accept or decline an invitation
- Change someone's role
- Leave a company
- Switch your active workspace context (personal ↔ company)

This sub-phase designs and implements the **full membership lifecycle** as a first-class domain concept.

---

## Prerequisite: What Already Exists from 3A

| Component | State | Used By |
|-----------|-------|---------|
| `company_memberships` table | Schema exists, data seeded | Auth middleware (workspace access derivation), RLS, role checks |
| `role` column (ADMIN/TECHNICIAN) | Seeded values | 3C.1 authorization guards (company workspace only) |
| `is_primary` column | Seeded (one membership per user in alpha) | Workspace default selection (may be replaced by `users.default_workspace_id`) |

This phase takes ownership of the `CompanyMembership` entity at the domain level and expands the User aggregate boundary to include membership management.

---

## Domain Concepts to Design

### 1. Membership Lifecycle States

The current schema has no `status` field. This phase adds a formal lifecycle:

```text
INVITED → ACTIVE → (SUSPENDED → ACTIVE) → REMOVED
                                            or DEPARTED (voluntary)
```

| State | Meaning | Who transitions |
|-------|---------|-----------------|
| `INVITED` | Invitation sent, not yet accepted | ADMIN invites |
| `ACTIVE` | Full member with access | User accepts, or seeded |
| `SUSPENDED` | Temporarily paused (e.g., leave of absence) | ADMIN suspends |
| `REMOVED` | Involuntarily removed by admin | ADMIN removes |
| `DEPARTED` | Voluntarily left | User leaves |

### 2. Invitation Flow

- ADMIN sends invitation (by email or user lookup)
- Invitee receives notification (out-of-scope for this phase — can be simple API poll)
- Invitee accepts → membership becomes ACTIVE
- Invitee declines → membership becomes DECLINED (no row persisted, or marked declined)

### 3. Role Transitions

- ADMIN can promote TECHNICIAN → ADMIN (within the same company)
- ADMIN can demote ADMIN → TECHNICIAN (with safeguard: company must have at least one ADMIN)
- Self-demotion: TBD (probably not — admin should ask another admin)

### 4. Workspace Context Switching

Per [ADR-0030](../adr/0030-workspace-isolation-abstraction.md), users operate in workspaces, not companies directly. Context switching means:

- **Personal workspace:** Every user has one. Default when no header sent. No company context.
- **Company workspace:** Selected via `X-Workspace-Id` header. Requires active membership.

Two options to evaluate during research:

| Option | Where stored | Semantics |
|--------|-------------|-----------|
| **Persistent default** | `users.default_workspace_id` | User sets once, persists across sessions. Falls back to personal workspace. |
| **Session-level** | Client sends `X-Workspace-Id` header | User selects on each session, or switches mid-session |

Recommendation from audit: keep it stateless. Client sends the header, server validates access via derived access query (ADR-0032). Personal workspace is always the default.

### 5. Membership Invariants

- A company must have at least one ADMIN at all times
- A user can only have one ACTIVE membership per company (no duplicates)
- A user can have ACTIVE memberships at multiple companies simultaneously
- Default workspace must point to a workspace the user has access to (personal or active membership)

---

## Research Questions (to resolve before implementation)

- [ ] Should invitation create a pending membership row, or use a separate `invitations` table?
- [ ] Can a TECHNICIAN see other members in their company, or only ADMINs?
- [ ] What happens to a user's jobs when they leave a company? (reassignment policy)
- [ ] Should SUSPENDED members retain read-only access, or full lockout?
- [ ] Is there a limit on how many companies a user can join?
- [ ] Does the "last admin" guard prevent the admin from leaving, or just prevent demotion/removal?

---

## Implementation Plan (draft — pending design research)

### Schema Changes

```sql
ALTER TABLE company_memberships ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE';
ALTER TABLE company_memberships ADD CONSTRAINT chk_membership_status
    CHECK (status IN ('INVITED', 'ACTIVE', 'SUSPENDED', 'REMOVED', 'DEPARTED'));

-- Optional: invitations table if we separate invitation from membership
```

### Domain Layer

| File | Action |
|------|--------|
| `src/iam/membership.rs` | Evolve from schema struct to domain entity with lifecycle commands |
| `src/iam/user.rs` | Expand aggregate boundary to include membership management |
| `src/iam/membership_role.rs` | Rust enum `MembershipRole { Admin, Technician }` with `From<String>` |

### API Layer

| Endpoint | Method | Guard | Description |
|----------|--------|-------|-------------|
| `POST /api/companies/{id}/invite` | POST | ADMIN | Send invitation |
| `POST /api/invitations/{id}/accept` | POST | Auth | Accept invitation |
| `POST /api/invitations/{id}/decline` | POST | Auth | Decline invitation |
| `POST /api/memberships/{id}/change-role` | POST | ADMIN | Change member's role |
| `POST /api/memberships/{id}/suspend` | POST | ADMIN | Suspend a member |
| `POST /api/memberships/{id}/remove` | POST | ADMIN | Remove a member |
| `POST /api/companies/{id}/leave` | POST | Auth | Leave a company |
| `PUT /api/me/default-workspace` | PUT | Auth | Set default workspace (personal or company) |

---

## Exit Criteria

- [ ] Membership has formal lifecycle states (INVITED → ACTIVE → etc.)
- [ ] ADMIN can invite users to join their company
- [ ] Users can accept/decline invitations
- [ ] Role changes work with "last admin" safeguard
- [ ] Users can leave a company voluntarily
- [ ] ADMINs can remove members
- [ ] Workspace context switching works (personal ↔ company workspaces)
- [ ] All membership transitions have domain tests
- [ ] CompanyMembership spec upgraded from schema-only to full entity spec
