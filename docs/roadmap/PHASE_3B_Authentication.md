# Phase 3B: Authentication

> **Status:** 🔲 Not Started
> **Objective:** Users can prove who they are. JWT-based login replaces all hardcoded IDs.
> **Depends On:** Phase 3A ✅ (users must exist to authenticate)
> **ADRs:** [ADR-0030](../adr/0030-workspace-isolation-abstraction.md) (workspace context), [ADR-0032](../adr/0032-derived-workspace-access.md) (derived access), [ADR-0033](../adr/0033-stateless-workspace-context.md) (stateless workspace header)
> **Branch:** `phase3b/authentication`

---

## Why This Sub-Phase Exists

Phase 3A creates the User entity, but users have no way to log in. Every API call currently uses hardcoded UUIDs:

| Location | Current State |
|----------|--------------|
| `ll152.rs:21` | `DEV_USER_ID = "000...001"` |
| `tenant.rs:183` | `company_id = "000...001"` (list clients) |
| `tenant.rs:285` | `company_id = "000...001"` (list saved buildings) |
| `actor_user_id` everywhere | `Option<Uuid>` — often `None` |

This sub-phase replaces **all** of those with real identity from JWT tokens.

---

## Scope

### 1. Password Storage

- Hash passwords with **Argon2** (`argon2` crate)
- `users` table gains `password_hash TEXT NOT NULL`
- Seed alpha accounts with dev passwords

### 2. JWT Token Strategy (per SFR-SRAN-02)

| Token | Lifetime | Storage | Purpose |
|-------|----------|---------|---------|
| Access token | 15 min | Bearer header | API authorization |
| Refresh token | 7 days | HttpOnly cookie | Rotate access tokens |

- Signing: HMAC-SHA256 with `JWT_SECRET` env var
- Claims: `{ sub: user_id, exp, iat }`

> [!NOTE]
> **Neither `company_id` nor `workspace_id` is in the JWT.** The JWT only carries user identity. Workspace context is resolved at request time via the derived access query ([ADR-0032](../adr/0032-derived-workspace-access.md)) — either the user's personal workspace (default) or a company workspace specified by request header. This supports workspace switching without re-issuing tokens.

### 3. Auth Endpoints

| Endpoint | Method | Description | SFR |
|----------|--------|-------------|-----|
| `/auth/login` | POST | Email + password → access token + refresh cookie | SFR-SRAN-01 |
| `/auth/refresh` | POST | Refresh cookie → new access token | SFR-SRAN-02 |
| `/auth/logout` | POST | Invalidate refresh token | SFR-SRAN-04 |

### 4. Axum Auth Middleware

- Tower layer or extractor that validates JWT from `Authorization: Bearer <token>`
- Resolves workspace context via derived access query ([ADR-0032](../adr/0032-derived-workspace-access.md)):
  - Default: user's personal workspace (person-first)
  - Override: `X-Workspace-Id` request header for company workspace
  - Validates user has access to the requested workspace
- Checks `is_active` on the user
- Hydrates `AuthContext { user_id: Uuid, workspace_id: Uuid, company_id: Option<Uuid>, role: MembershipRole }`
  - `company_id` is `None` when operating in personal workspace
  - `role` is `OWNER` for personal workspace, membership role for company workspace
- Sets `app.workspace_id` PostgreSQL session variable for RLS ([ADR-0030](../adr/0030-workspace-isolation-abstraction.md))
- All existing handlers receive `AuthContext` instead of hardcoded values

### 5. Replace All Hardcoded IDs

Every existing endpoint that uses a hardcoded `company_id` or `DEV_USER_ID` gets updated to pull from `AuthContext`. Routes that currently filter by `company_id` will resolve the company from `AuthContext.workspace_id` → workspace → company association.

---

## Dependencies from User Spec (Phase 3A ↔ 3B)

Per the [User Aggregate Spec v3.0.0](../2-during-implementation/DDD/ModuleDesign/IAM/People/User_Aggregate.md):

| Dependency | What 3B must provide |
|---|---|
| Deactivation invalidates sessions | Auth middleware checks `is_active` on every request |
| Email change requires re-authentication | Email update gated by password confirmation |
| Email enumeration prevention | Constant-time responses for login failures |
| Login identity binding | JWT issued using `email` as the lookup key |

---

## Deferred (Not in 3B)

| Item | Deferred To | Reason |
|------|-------------|--------|
| Password reset (SFR-SRAN-03) | Post-alpha | Seed passwords for alpha; no self-service reset needed yet |
| User registration | Post-alpha | Admin creates users via API or seed |
| Rate limiting (SNFR-SA-01) | Post-alpha | 2-6 users don't need rate limiting |
| Token revocation list | Post-alpha | Simple expiry is sufficient for alpha |

## Resolved Design Decisions

These questions were resolved during the research phase (2026-03-30). See [ADR-0033](../adr/0033-stateless-workspace-context.md) for Q1 and Q2.

| # | Question | Decision | Rationale |
|---|----------|----------|----------|
| Q1 | How does the frontend select workspace context? | **Stateless `X-Workspace-Id` header** (ADR-0033) | Request concern, not session concern. No server-side state. |
| Q2 | What happens when no workspace header is sent? | **Default to personal workspace** (ADR-0033) | Person-first. User B (no company) never sends a header. Free-tier just works. |
| Q3 | Validate workspace access every request or cache? | **Query every request** (alpha) | 2-6 users, ~1ms with index, always fresh. Re-evaluate at scale. |
| Q4 | `password_hash` on users table or separate credentials table? | **Column on `users`** (alpha) | Email/password only. Refactor to `auth_credentials` table if OAuth/SSO added. |
| Q5 | Where does auth code live? | **Split across `pcd-domain` + `pcd-api`** | Types/hashing in domain, middleware/JWT/endpoints in API. No new crate. |

---

## Implementation Plan

### Domain Layer

| File | Action |
|------|--------|
| `src/auth/mod.rs` | New — `AuthContext` struct, token types |
| `src/auth/claims.rs` | New — JWT claims struct, validation logic |

### DB Layer

| File | Action |
|------|--------|
| `ALTER TABLE users ADD COLUMN password_hash` | Schema change |
| `src/iam/mod.rs` | Add `find_by_email` to UserRepository |

### API Layer

| File | Action |
|------|--------|
| `src/middleware/auth.rs` | New — JWT validation extractor + company context resolution |
| `src/routes/auth.rs` | New — login, refresh, logout endpoints |
| `src/routes/jobs.rs` | Update — use `AuthContext` for company_id + actor_user_id |
| `src/routes/tenant.rs` | Update — use `AuthContext` for company_id |
| `src/routes/ll152.rs` | Update — replace `DEV_USER_ID` with `AuthContext` |

### Dependencies (Cargo.toml)

```toml
argon2 = "0.5"
jsonwebtoken = "9"
```

---

## Exit Criteria

- [ ] Users can log in with email + password and receive a JWT
- [ ] All API endpoints validate JWT and extract AuthContext
- [ ] Workspace context resolved via derived access query (not JWT claims, ADR-0032)
- [ ] Personal workspace is the default when no `X-Workspace-Id` header is sent
- [ ] No hardcoded UUIDs remain in the API layer
- [ ] `actor_user_id` is always populated from auth context (no more `None`)
- [ ] `is_active` check on every authenticated request
- [ ] `app.workspace_id` set for RLS on every request (ADR-0030)
- [ ] Refresh token rotation works
- [ ] Logout invalidates the session
- [ ] Auth decision doc written (library choices, token strategy)

---

## Relevant Requirements

| Req ID | Description | Status |
|--------|-------------|--------|
| SFR-SRAN-01 | Email/password login | 🎯 This phase |
| SFR-SRAN-02 | JWT access (15m) + refresh (7d) | 🎯 This phase |
| SFR-SRAN-03 | Password reset | ⏳ Deferred |
| SFR-SRAN-04 | Logout | 🎯 This phase |
| SNFR-SA-01 | Rate limiting | ⏳ Deferred |
| SNFR-SA-03 | Token expiry | 🎯 This phase |
| SNFR-SC-11 | Password storage (Argon2) | 🎯 This phase |
