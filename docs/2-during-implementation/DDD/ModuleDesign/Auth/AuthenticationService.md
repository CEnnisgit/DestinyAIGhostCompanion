# Authentication Service Specification

**Module:** `Auth`
**Type:** Domain Service
**Source of Truth:** `pcd-api/src/routes/auth.rs` (endpoints) + `pcd-api/src/middleware/auth.rs` (middleware)
**Version:** 1.0.0
**ADRs:** [ADR-0030](../../../adr/0030-workspace-isolation-abstraction.md), [ADR-0032](../../../adr/0032-derived-workspace-access.md), [ADR-0033](../../../adr/0033-stateless-workspace-context.md)

---

## 1. Objective

The Authentication Service manages identity verification and workspace context resolution. It answers:

- Is this person who they claim to be? (login)
- Is this request from a verified person? (middleware)
- Which workspace is this request operating in? (context resolution)

It does **not** answer:

- What can this person do? (Phase 3C — Authorization)
- What features can they access? (Phase 3N — Entitlements)

---

## 2. Why This Is a Domain Service (Not an Aggregate)

Auth has no persisted entity with lifecycle. There is no "Auth" row in the database. It is an **operation** that:

1. Validates credentials against the `users` table
2. Issues tokens (access JWT + refresh in DB)
3. Resolves workspace context from request headers
4. Produces an `AuthContext` value object for downstream handlers

The only persistent state Auth owns is the `refresh_tokens` table — a session tracking mechanism, not a domain entity.

---

## 3. Flows

### 3.1 Login Flow

**Endpoint:** `POST /auth/login`
**Auth Required:** No (public)

**Request:**
```json
{
  "email": "john@example.com",
  "password": "correct-horse-battery-staple"
}
```

**Success Response (200):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Smith",
    "email": "john@example.com"
  },
  "workspaces": [
    {
      "id": "ws-personal-uuid",
      "name": "Personal",
      "type": "PERSONAL",
      "role": "OWNER"
    },
    {
      "id": "ws-company-uuid",
      "name": "Smith Plumbing LLC",
      "type": "COMPANY",
      "role": "ADMIN",
      "companyId": "company-uuid"
    }
  ]
}
```

**Additionally:** Sets `Set-Cookie` header with HttpOnly refresh token cookie.

**Failure Response (401):**
```json
{
  "error": "invalid_credentials"
}
```

> [!IMPORTANT]
> **Enumeration prevention:** The same 401 response is returned whether the email doesn't exist or the password is wrong. The error message is always `invalid_credentials` — never "email not found" or "wrong password." Response time must be constant regardless of failure reason (use constant-time comparison even for email lookup misses).

**Sequence:**

```
Client                    API                          DB
  │                        │                            │
  │  POST /auth/login      │                            │
  │  {email, password}     │                            │
  │───────────────────────>│                            │
  │                        │  SELECT * FROM users       │
  │                        │  WHERE email = $1          │
  │                        │───────────────────────────>│
  │                        │  user row (or null)        │
  │                        │<───────────────────────────│
  │                        │                            │
  │                        │  Verify password_hash      │
  │                        │  (Argon2, constant-time)   │
  │                        │                            │
  │                        │  Check user.is_active      │
  │                        │                            │
  │                        │  Generate access token JWT │
  │                        │  Generate refresh token    │
  │                        │                            │
  │                        │  INSERT refresh_tokens     │
  │                        │───────────────────────────>│
  │                        │                            │
  │                        │  Query workspaces          │
  │                        │  (derived access query)    │
  │                        │───────────────────────────>│
  │                        │  workspace list            │
  │                        │<───────────────────────────│
  │                        │                            │
  │  200 + Set-Cookie      │                            │
  │  {accessToken, user,   │                            │
  │   workspaces}          │                            │
  │<───────────────────────│                            │
```

**Login Validations (in order):**

1. Email format valid (reuse `Email` VO from User aggregate)
2. User exists with this email
3. User `is_active = true`
4. Password matches hash (Argon2 verify)
5. All checks pass → issue tokens

If any check fails → return 401 `invalid_credentials` (same response for all failures).

---

### 3.2 Refresh Flow

**Endpoint:** `POST /auth/refresh`
**Auth Required:** No (uses refresh cookie, not Bearer token)

**Request:** No body. The refresh token comes from the HttpOnly cookie.

**Success Response (200):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Failure Response (401):**
```json
{
  "error": "invalid_refresh_token"
}
```

**Sequence:**

```
Client                    API                          DB
  │                        │                            │
  │  POST /auth/refresh    │                            │
  │  Cookie: refresh=xxx   │                            │
  │───────────────────────>│                            │
  │                        │  SELECT FROM refresh_tokens│
  │                        │  WHERE token_hash = $1     │
  │                        │  AND expires_at > NOW()    │
  │                        │  AND revoked_at IS NULL    │
  │                        │───────────────────────────>│
  │                        │  token row (or null)       │
  │                        │<───────────────────────────│
  │                        │                            │
  │                        │  Check user.is_active      │
  │                        │───────────────────────────>│
  │                        │                            │
  │                        │  Generate new access token │
  │                        │                            │
  │  200 {accessToken}     │                            │
  │<───────────────────────│                            │
```

**Refresh Validations:**

1. Cookie present and non-empty
2. Token exists in `refresh_tokens` table
3. Token not expired (`expires_at > NOW()`)
4. Token not revoked (`revoked_at IS NULL`)
5. Associated user `is_active = true`

> [!NOTE]
> **No rotation on refresh for alpha.** The refresh token stays the same for its full 7-day lifetime. Rotation (issuing a new refresh token on each refresh) adds complexity and edge cases (race conditions with concurrent requests). Revisit post-alpha if needed.

---

### 3.3 Logout Flow

**Endpoint:** `POST /auth/logout`
**Auth Required:** Yes (Bearer token)

**Request:** No body.

**Success Response (200):**
```json
{
  "message": "logged_out"
}
```

**Sequence:**

```
Client                    API                          DB
  │                        │                            │
  │  POST /auth/logout     │                            │
  │  Authorization: Bearer │                            │
  │  Cookie: refresh=xxx   │                            │
  │───────────────────────>│                            │
  │                        │  UPDATE refresh_tokens     │
  │                        │  SET revoked_at = NOW()    │
  │                        │  WHERE token_hash = $1     │
  │                        │  AND user_id = $2          │
  │                        │───────────────────────────>│
  │                        │                            │
  │  200 + Clear-Cookie    │                            │
  │<───────────────────────│                            │
```

**Behavior:**

- Revokes the specific refresh token (soft delete via `revoked_at`)
- Clears the refresh cookie on the response
- The access token continues to work until it expires (15 min max) — this is acceptable for alpha
- Other sessions (other devices) are NOT affected

---

### 3.4 Workspace Context Resolution (Middleware)

This is not an endpoint — it runs on **every authenticated request** as Axum middleware.

**Sequence:**

```
Client                    Middleware                   DB
  │                        │                            │
  │  GET /api/jobs         │                            │
  │  Authorization: Bearer │                            │
  │  X-Workspace-Id: ws-x  │                            │
  │───────────────────────>│                            │
  │                        │                            │
  │                        │  1. Validate JWT            │
  │                        │     Extract user_id         │
  │                        │                            │
  │                        │  2. Extract X-Workspace-Id  │
  │                        │     (or default: personal)  │
  │                        │                            │
  │                        │  3. Run derived access query│
  │                        │───────────────────────────>│
  │                        │  [{ws_id, co_id, role}...] │
  │                        │<───────────────────────────│
  │                        │                            │
  │                        │  4. Find requested ws_id   │
  │                        │     in access list         │
  │                        │     (or 403 Forbidden)     │
  │                        │                            │
  │                        │  5. SET app.workspace_id   │
  │                        │───────────────────────────>│
  │                        │                            │
  │                        │  6. Hydrate AuthContext     │
  │                        │     Pass to handler         │
  │                        │                            │
  │                        │  Handler executes...       │
```

**Middleware Steps:**

1. **Extract JWT** from `Authorization: Bearer <token>` header. If missing or invalid → 401.
2. **Extract workspace** from `X-Workspace-Id` header. If absent → default to user's `personal_workspace_id` (from `users` table, included in derived access query result).
3. **Run derived access query** (ADR-0032) to get all workspaces user can access.
4. **Validate** that the requested `workspace_id` is in the access list. If not → 403 Forbidden.
5. **Set PostgreSQL session variable** `app.workspace_id` for RLS enforcement (ADR-0030).
6. **Hydrate AuthContext** with `user_id`, `workspace_id`, `company_id` (if company workspace), and `role`. Pass as Axum extension to the handler.

**Error Responses:**

| Condition | Status | Error |
|-----------|--------|-------|
| No `Authorization` header | 401 | `missing_auth_header` |
| Invalid/expired JWT | 401 | `invalid_token` |
| User `is_active = false` | 401 | `account_deactivated` |
| `X-Workspace-Id` not in user's access list | 403 | `workspace_access_denied` |

---

## 4. Refresh Tokens Table

```sql
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    token_hash  TEXT NOT NULL,           -- SHA-256 hash of the actual token
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked_at  TIMESTAMPTZ,            -- NULL = active, set = revoked
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_agent  TEXT                     -- optional: what device/browser
);

CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
```

**Key design choices:**

- **`token_hash` not `token`** — we store a hash of the refresh token, not the raw token. If the DB is compromised, the attacker can't use the tokens. Same pattern as password hashing, but SHA-256 is sufficient here (tokens are high-entropy random, not human passwords).
- **`revoked_at` instead of DELETE** — soft revocation for audit trail. A cleanup job can purge old rows periodically.
- **`user_agent` is optional** — nice-to-have for "active sessions" UI later, not required for alpha.
- **No workspace_id** — refresh tokens are user-level, not workspace-scoped. Workspace is a request concern.

---

## 5. Multiple Sessions

Multiple active refresh tokens can coexist for the same user. This supports:

- Using the app on phone and tablet simultaneously
- Browser and mobile app sessions
- No "you've been logged out from another device" frustration

Each login creates a new refresh token row. Logout revokes only the specific token used in that session.

---

## 6. Workspace List Query

The workspace list returned on login uses the same derived access query as the middleware (ADR-0032), but enriched with display names:

```sql
-- Personal workspace
SELECT
    w.id AS workspace_id,
    'Personal' AS name,
    'PERSONAL' AS workspace_type,
    'OWNER' AS role,
    NULL AS company_id
FROM users u
JOIN workspaces w ON u.personal_workspace_id = w.id
WHERE u.id = $1

UNION ALL

-- Company workspaces
SELECT
    w.id AS workspace_id,
    c.name AS name,
    'COMPANY' AS workspace_type,
    cm.role AS role,
    c.id AS company_id
FROM company_memberships cm
JOIN companies c ON cm.company_id = c.id
JOIN workspaces w ON c.workspace_id = w.id
WHERE cm.user_id = $1 AND cm.is_active = true
```

---

## 7. Future Considerations (Not in Alpha)

| Feature | When | Notes |
|---------|------|-------|
| Refresh token rotation | Post-alpha | Issue new refresh on each use; handle race conditions |
| Session management UI | Beta | "View active sessions", "Log out everywhere" |
| Token revocation on password change | Post-alpha | Revoke all refresh tokens when password changes |
| OAuth/SSO | Post-alpha | Would bypass password flow, issue tokens directly |
| Rate limiting on login | Post-alpha | Prevent brute force (SNFR-SA-01) |
