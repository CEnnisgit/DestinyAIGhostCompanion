# Auth Module

> **Source of Truth:** `pcd-domain/src/auth/` (types) + `pcd-api/src/middleware/auth.rs` (impl)
> **Scope:** Phase 3B (Authentication) + Phase 3C.1 (Authorization Core)
> **Roadmap:** [PHASE_3B_Authentication.md](../../../roadmap/PHASE_3B_Authentication.md), [PHASE_3C_Authorization.md](../../../roadmap/PHASE_3C_Authorization.md)
> **Research:** [PHASE_3B_Research.md](./PHASE_3B_Research.md), [PHASE_3C1_Research.md](./PHASE_3C1_Research.md)
> **ADRs:** [ADR-0030](../../../adr/0030-workspace-isolation-abstraction.md), [ADR-0032](../../../adr/0032-derived-workspace-access.md), [ADR-0033](../../../adr/0033-stateless-workspace-context.md), [ADR-0034](../../../adr/0034-role-aware-workspace-interaction.md), [ADR-0035](../../../adr/0035-compliance-boundary-at-finalization.md)

## Traceability

> **Refer to:** [TRACEABILITY_SFR.md](./TRACEABILITY_SFR.md), [TRACEABILITY_SNFR.md](./TRACEABILITY_SNFR.md)

- **Primary Responsibility**: Authentication (`SFR-SRAN-*`) and workspace context resolution
- **Key Requirements**:
  - `SFR-SRAN-01`: Email/Password Login
  - `SFR-SRAN-02`: JWT access (15m) + refresh (7d HttpOnly cookie)
  - `SFR-SRAN-04`: Logout / session invalidation
  - `SNFR-SC-11`: Password storage (Argon2)

> [!NOTE]
> Authorization (`SFR-SRAZ-*`) is handled by Phase 3C.1 specs within this module:
> - [PermissionGuard.md](./PermissionGuard.md) — Route-level guards enforcing the permission matrix
> - [RoleVisibility.md](./RoleVisibility.md) — Application-level query scoping per role

## Module Responsibilities

1. **Authentication**: Validates credentials (email/password) using Argon2 (`argon2` crate)
2. **Token Management**: Issues and validates JWT access tokens (HMAC-SHA256); manages refresh tokens via HttpOnly cookie
3. **Workspace Context Resolution**: Resolves which workspace a request operates in via `X-Workspace-Id` header (ADR-0033)
4. **AuthContext Hydration**: Produces `AuthContext` struct for downstream handlers — contains `user_id`, `workspace_id`, optional `company_id`, and `role`
5. **Permission Guards** (3C.1): Route-level extractors that enforce role-based access per the SFR-SRAZ matrix
6. **Role Visibility** (3C.1): Application-level query scoping that filters workspace data by role

## AuthContext Struct

```rust
pub struct AuthContext {
    pub user_id: Uuid,
    pub workspace_id: Uuid,
    pub company_id: Option<Uuid>,  // None when operating in personal workspace
    pub role: MembershipRole,      // OWNER for personal, membership role for company
}
```

- `user_id` — extracted from JWT `sub` claim
- `workspace_id` — resolved from `X-Workspace-Id` header (default: personal workspace)
- `company_id` — `Some(id)` when workspace is a company workspace, `None` for personal
- `role` — `OWNER` for personal workspace, `ADMIN`/`TECHNICIAN` for company workspaces

## Workspace Context Resolution Flow

```
Request arrives
    │
    ├─ Extract JWT from Authorization: Bearer <token>
    │   └─ Validate → extract user_id
    │
    ├─ Check X-Workspace-Id header
    │   ├─ Present → use as workspace_id
    │   └─ Absent  → default to user's personal workspace
    │
    ├─ Run derived access query (ADR-0032)
    │   └─ Verify user has access to workspace_id
    │   └─ Retrieve company_id + role for this workspace
    │
    ├─ Check user.is_active
    │
    ├─ SET app.workspace_id = '<workspace_uuid>' (PostgreSQL session var for RLS)
    │
    └─ Hydrate AuthContext → pass to handler
```

## Code Location (Resolved — Q5)

| What | Crate | Path |
|------|-------|------|
| `AuthContext` struct | `pcd-domain` | `src/auth/mod.rs` |
| `MembershipRole` enum | `pcd-domain` | `src/auth/mod.rs` |
| JWT claims struct | `pcd-domain` | `src/auth/claims.rs` |
| Password hashing | `pcd-domain` | `src/auth/password.rs` |
| Auth middleware (Tower layer) | `pcd-api` | `src/middleware/auth.rs` |
| Login/refresh/logout endpoints | `pcd-api` | `src/routes/auth.rs` |
| `X-Workspace-Id` extraction | `pcd-api` | `src/middleware/auth.rs` |

## API Endpoints

| Endpoint | Method | Description | SFR |
|----------|--------|-------------|-----|
| `/auth/login` | POST | Email + password → access token + refresh cookie | SFR-SRAN-01 |
| `/auth/refresh` | POST | Refresh cookie → new access token | SFR-SRAN-02 |
| `/auth/logout` | POST | Invalidate refresh token | SFR-SRAN-04 |

## Schema Changes

```sql
ALTER TABLE users ADD COLUMN password_hash TEXT;  -- nullable for future OAuth/SSO
```

> No separate `credentials` or `password_reset_tokens` table for alpha. Password reset is deferred to post-alpha.

## Dependencies

```toml
# pcd-domain
argon2 = "0.5"

# pcd-api
jsonwebtoken = "9"
# axum-extra — for typed headers, cookie handling (refresh token)
# tower — for middleware layer (transitive via axum)
```

## Module Interactions

- **Consumes**: `users` table (email lookup, `is_active` check, `personal_workspace_id`), `company_memberships` + `companies` tables (workspace access derivation)
- **Produces**: `AuthContext` — consumed by **all** downstream route handlers
- **Sets**: `app.workspace_id` PostgreSQL session variable for RLS (ADR-0030)

## Deferred (Not in Auth Module for Alpha)

| Item | Deferred To | Reason |
|------|-------------|--------|
| Password reset (SFR-SRAN-03) | Post-alpha | Seed passwords; no self-service reset yet |
| User registration endpoint | Post-alpha | Admin creates users via seed |
| Rate limiting (SNFR-SA-01) | Post-alpha | 2-6 users don't need it |
| Token revocation list | Post-alpha | Simple expiry is sufficient |
| OAuth/SSO/Passkeys | Post-alpha | Email/password only for alpha |

## Design Decisions

All 5 design questions have been resolved. See [PHASE_3B_Research.md](./PHASE_3B_Research.md) for full rationale and the [3B roadmap](../../../roadmap/PHASE_3B_Authentication.md) for the summary table.

| # | Question | Decision |
|---|----------|----------|
| Q1 | Workspace context mechanism | Stateless `X-Workspace-Id` header (ADR-0033) |
| Q2 | No header behavior | Default to personal workspace (ADR-0033) |
| Q3 | Workspace access validation | Query every request (alpha) |
| Q4 | Password storage | Column on `users` table |
| Q5 | Code location | Split: `pcd-domain` (types) + `pcd-api` (middleware/routes) |
