# Token Strategy Specification

**Module:** `Auth`
**Type:** Policy
**Source of Truth:** `pcd-api/src/middleware/auth.rs` (validation), `pcd-api/src/routes/auth.rs` (issuance)
**Version:** 1.0.0
**SFR:** SFR-SRAN-02 (JWT access + refresh), SNFR-SA-03 (token expiry)

---

## 1. Overview

PCD uses a **two-token strategy**: a short-lived access token for API authorization and a long-lived refresh token for session continuity. This balances security (short exposure window for access tokens) with usability (users don't re-enter passwords every 15 minutes).

---

## 2. Access Token (JWT)

| Property | Value |
|----------|-------|
| **Format** | JSON Web Token (RFC 7519) |
| **Algorithm** | HMAC-SHA256 (HS256) |
| **Signing Key** | `JWT_SECRET` environment variable |
| **Lifetime** | 15 minutes |
| **Transport** | `Authorization: Bearer <token>` request header |
| **Storage (client)** | In-memory (JavaScript variable) — NOT localStorage |

### Claims

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "iat": 1711843200,
  "exp": 1711844100
}
```

| Claim | Type | Description |
|-------|------|-------------|
| `sub` | UUID string | The user's ID (`users.id`) |
| `iat` | Unix timestamp | Issued at |
| `exp` | Unix timestamp | Expires at (iat + 15 minutes) |

### What Is NOT in the JWT

| Omitted | Why |
|---------|-----|
| `workspace_id` | Workspace context is per-request, not per-session (ADR-0033). Putting it in the JWT would require re-issuing tokens on workspace switch. |
| `company_id` | Same reason — derived at request time from `X-Workspace-Id` header |
| `role` | Role is per-membership, not per-user. Derived at request time. |
| `email` | Not needed for authorization. Reduces token size. |
| `name` | Not needed for authorization. |

> [!IMPORTANT]
> The JWT is intentionally minimal. It answers ONE question: "who is this person?" Everything else is resolved at request time by the middleware.

### Validation Steps

1. Decode the token using `JWT_SECRET`
2. Verify `exp > now()` (not expired)
3. Extract `sub` as `user_id: Uuid`
4. Verify user exists and `is_active = true` (DB lookup)

---

## 3. Refresh Token

| Property | Value |
|----------|-------|
| **Format** | 256-bit cryptographically random opaque string (base64url encoded) |
| **Storage (server)** | `refresh_tokens` table — SHA-256 hash of the token is stored, not the raw value |
| **Storage (client)** | HttpOnly, Secure, SameSite=Lax cookie |
| **Lifetime** | 7 days |
| **Rotation** | None for alpha (token reused until expiry) |

### Why Opaque (Not JWT)

Refresh tokens are DB-backed (Q6 decision). Since we look them up in the DB anyway, there's no benefit to making them self-contained JWTs. An opaque random string is:

- Simpler to generate
- Impossible to decode if intercepted (no claims to leak)
- Validated entirely server-side

### Generation

```rust
use rand::RngCore;
use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};

fn generate_refresh_token() -> String {
    let mut bytes = [0u8; 32]; // 256 bits
    rand::thread_rng().fill_bytes(&mut bytes);
    URL_SAFE_NO_PAD.encode(bytes)
}
```

### Storage

The raw token is sent to the client in a cookie. The SHA-256 hash is stored in the DB:

```rust
use sha2::{Sha256, Digest};

fn hash_token(token: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(token.as_bytes());
    hex::encode(hasher.finalize())
}
```

This means:

- If the DB is compromised, stored hashes can't be used as tokens
- Lookup is done by hashing the incoming cookie and matching against `token_hash`

---

## 4. Cookie Configuration

```rust
Set-Cookie: refresh_token=<token>;
    HttpOnly;      // JavaScript cannot read it
    Secure;        // Only sent over HTTPS
    SameSite=Lax;  // Sent with top-level navigations, not cross-site requests
    Path=/auth;    // Only sent to auth endpoints, not every API call
    Max-Age=604800 // 7 days in seconds
```

| Attribute | Value | Why |
|-----------|-------|-----|
| `HttpOnly` | Yes | Prevents XSS from stealing the refresh token |
| `Secure` | Yes | Prevents transmission over HTTP (enforce HTTPS) |
| `SameSite` | `Lax` | Prevents CSRF while allowing normal navigation |
| `Path` | `/auth` | Token only sent to `/auth/refresh` and `/auth/logout` — not attached to every API request |
| `Max-Age` | 604800 | 7 days — matches refresh token DB expiry |

> [!NOTE]
> **Development override:** In local development (`NODE_ENV=development` or equivalent), `Secure` may be disabled to allow HTTP on localhost. This MUST NOT be deployed to staging or production.

---

## 5. Token Lifecycle

```
Login
  │
  ├─ Issue access token (JWT, 15m)
  ├─ Issue refresh token (random, 7d)
  ├─ Store refresh hash in DB
  ├─ Set refresh cookie
  │
  ▼
Normal API usage (0-15 min)
  │  Authorization: Bearer <access_token>
  │  (refresh cookie not sent — Path=/auth)
  │
  ▼
Access token expires (15 min)
  │
  ▼
Client calls POST /auth/refresh
  │  Cookie: refresh_token=<token>
  │
  ├─ Validate refresh token in DB
  ├─ Issue NEW access token (15m)
  ├─ Refresh token stays the same
  │
  ▼
Normal API usage continues...
  │
  ▼
Logout (or 7 days pass)
  │
  ├─ Revoke refresh token in DB (revoked_at = NOW())
  ├─ Clear refresh cookie
  ├─ Access token expires naturally (max 15 min)
  │
  ▼
Session ended
```

---

## 6. Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET` | HMAC-SHA256 signing key | 64+ character random string |
| `JWT_ACCESS_LIFETIME_SECS` | Access token lifetime | `900` (15 min) |
| `REFRESH_TOKEN_LIFETIME_SECS` | Refresh token lifetime | `604800` (7 days) |

> [!WARNING]
> `JWT_SECRET` must be at least 256 bits (32 bytes) of cryptographic randomness. A weak secret enables token forgery. Generate with: `openssl rand -base64 64`

---

## 7. Crate Dependencies

```toml
# pcd-api/Cargo.toml
jsonwebtoken = "9"      # JWT creation and validation
rand = "0.8"            # Refresh token generation
sha2 = "0.10"           # SHA-256 hashing for refresh token storage
hex = "0.4"             # Hex encoding for token hashes
base64 = "0.22"         # Base64url encoding for refresh tokens
```
