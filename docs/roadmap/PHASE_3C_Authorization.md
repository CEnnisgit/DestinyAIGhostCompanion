# Phase 3C: Authorization (Two-Pass Model)

> **Status:** 🟡 Research ✅, Spec ⏳
> **Objective:** Enforce who can do what. Built in two passes: 3C.1 (RBAC — alpha) and 3C.2 (full authorization with entitlement gating — post-alpha).
> **Depends On:** Phase 3B ✅ (need auth context to check permissions)
> **ADRs:** [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md) (two-pass model), [ADR-0030](../adr/0030-workspace-isolation-abstraction.md) (workspace-based isolation), [ADR-0032](../adr/0032-derived-workspace-access.md) (derived access), [ADR-0033](../adr/0033-stateless-workspace-context.md) (stateless workspace header), [ADR-0034](../adr/0034-role-aware-workspace-interaction.md) (role-aware interaction), [ADR-0035](../adr/0035-compliance-boundary-at-finalization.md) (compliance boundary at finalization)
> **Branch:** `phase3c/authorization`

---

## Why Two Passes

Authorization requires multiple inputs that mature at different times:

| Input | Available When | Source |
|-------|---------------|--------|
| Authenticated user identity | Phase 3B | JWT `sub` claim |
| Workspace context | Phase 3A infrastructure + 3B middleware | Derived access query (ADR-0032) — personal or company workspace |
| Company context (within company workspace) | Phase 3A infrastructure + 3B middleware | Resolved from `workspace_id` → `companies.workspace_id` |
| Membership role (ADMIN/TECHNICIAN) | Phase 3A infrastructure | `company_memberships.role` (only in company workspace) |
| Entitlement tier (person + company) | Phase 3N | Entitlement model |

**3C.1** uses the first four — available for alpha.
**3C.2** adds the fifth — available after entitlements are designed.

---

## 3C.1: Authorization Core (Alpha)

> **This pass is on the alpha critical path: 3A → 3B → 3C.1**

### What 3C.1 enforces (concretely)

1. **Authenticated user required** — all protected routes reject unauthenticated requests
2. **Workspace context resolved** — personal workspace default, or company workspace via `X-Workspace-Id` header
3. **Membership validated (company workspace only)** — "does this user belong to the company that owns this workspace?"
4. **Membership role checked (company workspace only)** — admin vs. technician per SFR-SRAZ
5. **RLS context set** — `SET app.workspace_id = ?` on every request ([ADR-0030](../adr/0030-workspace-isolation-abstraction.md))

> [!NOTE]
> **Personal workspace has no RBAC.** When a user operates in their personal workspace, they are the sole owner. The ADMIN/TECHNICIAN permission matrix only applies within company workspaces.


### Permission Matrix (from SFR-SRAZ)

| Code | Action | TECHNICIAN | ADMIN |
|------|--------|-----------|-------|
| SFR-SRAZ-01 | Create Job | ❌ | ✅ |
| SFR-SRAZ-02 | Dispatch/Assign Job | ❌ | ✅ |
| SFR-SRAZ-03 | View Jobs | ✅ (assigned only) | ✅ (all in workspace) |
| SFR-SRAZ-04 | Submit Findings | ✅ | ✅ |
| SFR-SRAZ-05 | Finalize/Sign Report | ❌ | ✅ |
| SFR-SRAZ-06 | Generate Report | ❌ | ✅ |
| SFR-SRAZ-07 | Manage Users | ❌ | ✅ |

### Access Control Rules (from SFR-SRAC)

| Code | Rule | Implementation |
|------|------|----------------|
| SFR-SRAC-01 | Technician scope: only assigned jobs | `WHERE assigned_to = $user_id AND workspace_id = $workspace_id` |
| SFR-SRAC-02 | Admin scope: all company jobs | `WHERE workspace_id = $workspace_id` |
| SFR-SRAC-03 | Workspace isolation | All queries filtered by `workspace_id` from auth context (ADR-0030) |
| SFR-SRAC-10 | Audit trail | All actions logged with `actor_user_id` (done in Phase 3A/3B) |

### Scope — 3C.1

#### 1. Route Guards

Axum middleware or extractors that enforce role requirements per route:
- `require_admin()` — rejects TECHNICIAN with 403
- `require_any_role()` — allows any authenticated user
- Applied to each endpoint per the permission matrix above

#### 2. Query Scoping

RLS policies filter all queries by `workspace_id` automatically (ADR-0030). Role-based visibility adds an application-level filter on top:

- **ADMIN (company workspace):** RLS filters by `workspace_id` → sees all company jobs. No additional filter.
- **TECHNICIAN (company workspace):** RLS filters by `workspace_id` → application adds `WHERE assigned_to = $auth.user_id` to scope to assigned jobs only.
- **PERSONAL workspace:** RLS filters by `workspace_id` → sees all personal jobs. No additional filter (user is OWNER).

#### 3. Job Assignment

Prerequisite for TECHNICIAN scoping — jobs need an `assigned_to` field:
- `ALTER TABLE jobs ADD COLUMN assigned_to UUID REFERENCES users(id)`
- API: `POST /api/jobs/{id}/assign` (ADMIN only, per SFR-SRAZ-02)
- Domain: `Job.assign(user_id, actor)` command method

#### 4. Tenant Isolation Audit

Verify every existing query filters by `workspace_id` (via RLS policies, ADR-0030):

| Query Location | Currently Scoped? | Action |
|---------------|-------------------|--------|
| `SqlxJobRepository::list_all` | ✅ Yes (company_id param) | Migrate to workspace_id RLS |
| `SqlxClientRepository::list_by_company` | ✅ Yes | Migrate to workspace_id RLS |
| `SqlxSavedBuildingRepository::list_by_company` | ✅ Yes | Migrate to workspace_id RLS |
| LL152 details/findings/photos | ⚠️ By job_id only | Add workspace_id check via RLS |
| Client summary (direct SQL) | ⚠️ By client_id only | Add workspace_id cross-check via RLS |

---

## 3C.2: Full Authorization (Post-Alpha)

> **Depends On:** Phase 3N (Entitlements) — needs tier model to check feature access
> **This is NOT on the alpha critical path.**

### What 3C.2 adds

Extends every authorization check to include entitlement-based gating:

```text
Can this authenticated user perform action X
while operating in workspace W
  (which may be a company workspace with role R)
under personal tier P
and company tier C (if in company context)?
```

### New capabilities

- **Feature gating:** deny actions if the user's personal tier or company tier doesn't include the feature
- **Usage limits:** enforce per-tier usage caps (e.g., max jobs per month for free tier)
- **Upgrade prompts:** return structured 403 responses that include upgrade paths

### Design dependency

3C.2 cannot be fully designed until [Phase 3N (Entitlements)](./PHASE_3N_Entitlements.md) defines:
- What tiers exist (person and company)
- What features each tier includes
- How feature resolution works (person tier vs. company tier — union? intersection? company wins?)

---

## Implementation Plan — 3C.1

### Domain Layer

| File | Action |
|------|--------|
| `src/jobs/job.rs` | Add `assigned_to: Option<Uuid>` field + `assign()` command |
| `src/auth/permissions.rs` | New — role-based permission checks |

### API Layer

| File | Action |
|------|--------|
| `src/middleware/require_role.rs` | New — role guard extractors |
| `src/routes/jobs.rs` | Update — apply guards, scope queries by role |
| `src/routes/tenant.rs` | Update — apply guards |
| `src/routes/ll152.rs` | Update — apply guards (SRAZ-04, SRAZ-05) |
| `src/routes/users.rs` | Update — apply admin-only guard (SRAZ-07) |

### DB Layer

| File | Action |
|------|--------|
| `src/jobs/mod.rs` | Update queries with `assigned_to` + role-scoped listing |

---

## Exit Criteria

### 3C.1 (Alpha)
- [ ] Route guards enforce ADMIN vs TECHNICIAN access per SFR-SRAZ matrix (company workspace only)
- [ ] TECHNICIAN users can only see their assigned jobs
- [ ] ADMIN users see all company jobs
- [ ] Personal workspace users see only their own personal jobs/clients
- [ ] Cross-workspace data access returns 403 or empty results
- [ ] `assigned_to` field exists on Jobs with assignment API
- [ ] All existing queries verified for `workspace_id` scoping (via RLS)
- [ ] Permission matrix tests (attempt forbidden action → 403)

### 3C.2 (Post-Alpha)
- [ ] Authorization checks include entitlement tier
- [ ] Feature gating works for both person and company tiers
- [ ] Structured 403 responses with upgrade path info
- [ ] Integration tests for tier-based feature access

---

## Alpha User Impact

| User | Role | What Changes |
|------|------|-------------|
| User A (solo owner) | ADMIN | Sees all his jobs. No change in experience. |
| User B (team owner) | ADMIN | Can assign jobs to his employees. Sees all jobs. |
| User B's employees | TECHNICIAN | See only their assigned jobs. Can submit findings. |

---

## Relevant Requirements

| Req ID | Description | Pass |
|--------|-------------|------|
| SFR-SRAZ-01..07 | Permission matrix (TECHNICIAN vs ADMIN) | 3C.1 |
| SFR-SRAC-01 | Technician scope (own assigned jobs) | 3C.1 |
| SFR-SRAC-02 | Admin scope (all company jobs) | 3C.1 |
| SFR-SRAC-03 | Company isolation (multi-tenancy) | 3C.1 |
| SFR-SRAC-10 | Audit trail | 3A/3B (prerequisite) |
