# Phase 3B Authentication — Research & Open Questions

> **Status:** Research phase — all design questions RESOLVED ✅
> **Depends On:** Phase 3A (spec-complete ✅, not yet implemented)
> **Roadmap:** [PHASE_3B_Authentication.md](../../../roadmap/PHASE_3B_Authentication.md)

---

## 1. What the 3B Roadmap Currently Says

The roadmap is well-structured and covers:
- Argon2 password hashing
- JWT access (15m) + refresh (7d HttpOnly cookie)
- Login / refresh / logout endpoints
- Auth middleware that hydrates `AuthContext`
- Replacing all hardcoded IDs in API routes

### Hardcoded IDs in the Codebase (confirmed)

| Location | Current Hardcoded Value |
|----------|------------------------|
| `routes/ll152.rs:21` | `DEV_USER_ID = "000…001"` |
| `routes/tenant.rs:183` | `company_id = "000…001"` (list clients) |
| `routes/tenant.rs:285` | `company_id = "000…001"` (list saved buildings) |

---

## 2. What Changed Since the Roadmap Was Written

The roadmap was written **before** ADR-0030 (workspace abstraction) and ADR-0032 (derived workspace access). Several assumptions have been updated in the roadmap (see commit `c0bbe12`).

---

## 3. Design Questions — ALL RESOLVED ✅

### Q1: How does the frontend select workspace context? → RESOLVED

> **Decision:** Option A — Stateless `X-Workspace-Id` header
> **ADR:** [ADR-0033](../../../adr/0033-stateless-workspace-context.md)

The JWT carries identity (`user_id`). The header carries context (`workspace_id`). Both are stateless. No server-side session state.

**Rationale from discussion:**
- Workspace context is a request concern, not a session concern
- Easy to test — change the header, get different results
- Frontend already manages UI state; workspace selection is just another piece
- Scales trivially — no shared state between servers

### Q2: What happens when no workspace header is sent? → RESOLVED

> **Decision:** Option A — Default to personal workspace
> **ADR:** [ADR-0033](../../../adr/0033-stateless-workspace-context.md)

Aligns with person-first model (ADR-0027). User B (solo plumber, no company) never sends a header — his personal workspace is used automatically. Free-tier users who don't know about workspaces just work.

### Q3: Validate workspace access every request, or cache? → RESOLVED

> **Decision:** Option A — Query every request (for alpha)

**Rationale:**
- 2-6 users at alpha — zero optimization needed
- ~1ms with proper index on `company_memberships.user_id`
- Always fresh — no stale cache if membership changes
- Simple — one code path, no cache invalidation logic
- Re-evaluate at scale (100+ concurrent users)

**The query (from ADR-0032):**
```sql
-- Personal workspace
SELECT personal_workspace_id AS workspace_id, NULL AS company_id, 'OWNER' AS role
FROM users WHERE id = $1
UNION ALL
-- Company workspaces
SELECT c.workspace_id, c.id AS company_id, cm.role
FROM company_memberships cm
JOIN companies c ON cm.company_id = c.id
WHERE cm.user_id = $1 AND cm.is_active = true
```

### Q4: `password_hash` — users table or separate credentials table? → RESOLVED

> **Decision:** Column on `users` table for alpha

**Rationale:**
- Alpha is email/password only — no OAuth, SSO, or passkeys
- Adding a column is simpler than a join for every auth check
- If additional auth methods are needed post-alpha, refactor to `auth_credentials` table
- The `User` entity spec already treats `users` as lean identity — one nullable column doesn't change that
- `password_hash TEXT` — nullable to support future passwordless/OAuth users

### Q5: Where does auth code live? → RESOLVED

> **Decision:** Split across existing crates — no new crate

| What | Where | Why |
|------|-------|-----|
| `AuthContext` struct | `pcd-domain` | Domain type, used by domain logic |
| `MembershipRole` enum | `pcd-domain` | Domain concept (ADMIN, TECHNICIAN) |
| Password hashing (Argon2) | `pcd-domain` | Domain logic — validating credentials |
| JWT creation/validation | `pcd-api` | Infrastructure concern — token format |
| Auth middleware | `pcd-api` | Axum-specific request handling |
| Login/refresh/logout endpoints | `pcd-api` | API routes |
| `X-Workspace-Id` header extraction | `pcd-api` | Request-level concern |

**Rationale:**
- No new crate for alpha — 2 crates is enough for 2-6 users
- Clean split: domain types vs. infrastructure wiring
- If auth grows complex enough to justify a crate, extract then (YAGNI for now)

---

## 4. Module Scaffold Status

The `Auth/README.md` scaffold is **stale**. It currently references:
- `@pcd/auth-backend` (old NestJS package)
- `packages/features/auth` (old structure)
- Roles: `PLATFORM_ADMIN`, `COMPANY_ADMIN`, `TECHNICIAN`, `OWNER` (old role set)
- `password_reset_tokens` table
- `request.user` hydration (Express/NestJS pattern)

**Needs full rewrite** to reflect Rust/Axum/SQLx and workspace model before any spec work.

---

## 5. Crate Dependencies Needed

```toml
argon2 = "0.5"
jsonwebtoken = "9"
```

Additional considerations:
- `tower` — for middleware layer (may already be transitive via axum)
- `axum-extra` — for typed headers, cookie handling (refresh token)
- `rand` — for token generation (may already be available)

---

## 6. Roadmap Updates Applied

| Section | Update | Status |
|---------|--------|--------|
| §4 Axum Auth Middleware | `app.company_id` → `app.workspace_id`, workspace resolution | ✅ Done |
| §4 AuthContext struct | Added `workspace_id`, `company_id` optional | ✅ Done |
| §2 JWT Claims | Workspace NOT in JWT (request concern per ADR-0033) | ✅ Confirmed |
| ADR references | Added ADR-0030, ADR-0032, ADR-0033 | ✅ Done |
| Resolved Design Decisions | Q1–Q5 table added to roadmap | ✅ Done |

---

## 7. Next Steps

1. ~~Discuss Q1–Q5~~ → ✅ **All resolved**
2. **Rewrite `Auth/README.md` scaffold** — current one is actively misleading
3. ~~Update 3B roadmap~~ → ✅ Workspace model incorporated
4. ~~Lock in Q1–Q5 in roadmap~~ → ✅ Resolved Design Decisions table added
5. **Write Auth module specs** — once scaffold is rewritten
6. **Then implement** — not before all specs are done

> [!NOTE]
> All 5 design questions have been resolved through discussion. The decisions are captured in:
> - **ADR-0033** — Q1 (stateless header) and Q2 (personal workspace default)
> - **This document** — Q3 (query every request), Q4 (column on users), Q5 (split across crates)
> - **3B Roadmap** — Summary table under "Resolved Design Decisions"
