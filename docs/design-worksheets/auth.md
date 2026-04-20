# Auth Design Worksheet

> A guided learning journey for designing authentication from scratch.
> Adapted for Destiny AI Ghost Companion — Bungie OAuth2 SSO.

---

## Concept 1: Identity vs Authentication vs Authorization

| Term | What It Means | Destiny Ghost Example |
|------|---------------|----------------------|
| **Identity** | Who is this person? | Bungie Membership ID, platform type |
| **Authentication (AuthN)** | Prove you are who you claim to be | Bungie OAuth2 SSO callback |
| **Authorization (AuthZ)** | What are you allowed to do? | Bungie API scopes (MoveEquipItems) |

### Our Decision
- [x] This module handles: Authentication only (AuthZ is handled by Bungie scopes)

---

## Concept 2: Credential Types

| Method | How It Works | Trade-offs |
|--------|--------------|------------|
| **Password** | User knows a secret | Simple, but weak if passwords are bad |
| **Magic Link** | Email a login link | No password to forget, but requires email access |
| **OAuth/SSO** | Delegate to Bungie | Convenient; user trusts Bungie, not us |
| **API Key** | Long-lived secret token | Good for machines, bad for humans |

### Our Decision
Primary method: **Bungie OAuth2 SSO** (ADR 005)
Secondary/future: None planned — single identity provider

---

## Concept 3: Password Storage

**Not applicable.** We never handle user passwords. Bungie handles credential verification entirely. We only store OAuth tokens (access + refresh).

---

## Concept 4: Session Management

### Option B: Stateless Tokens (OAuth2)
- Bungie issues a signed access token containing scopes
- Client sends token with every Bungie API request
- Token expires after ~60 minutes; refresh token used to obtain new one

### Our Decision
- [x] Stateless OAuth2 tokens (Bungie-issued, not self-signed JWTs)

Rationale: We are a consumer of Bungie's identity system, not a provider. We store their tokens, we don't mint our own.

---

## Concept 5: Token Lifetimes

### Access Token
- Bungie access tokens: **~60 minutes**
- Used for every Bungie API call (equip, transfer, profile fetch)

### Refresh Token
- Bungie refresh tokens: **~90 days**
- Used only to get new access tokens
- Stored securely in local SQLite (ADR 004 — encrypted at rest)

### Our Decision
Access token lifetime: **~60 min** (Bungie-controlled)
Refresh token lifetime: **~90 days** (Bungie-controlled)
Refresh token storage: **Local encrypted SQLite** (never localStorage)

---

## Concept 6: Token Storage (Client-Side)

| Location | Security | XSS Vulnerable? | CSRF Vulnerable? |
|----------|----------|-----------------|------------------|
| **localStorage** | Low | ✅ Yes | No |
| **sessionStorage** | Low | ✅ Yes | No |
| **HttpOnly Cookie** | High | No | ✅ Needs protection |
| **Memory only** | Highest | No | No |
| **Encrypted SQLite** | High | No | No |

### Our Decision
Access token stored in: **Rust backend memory** (never exposed to JS)
Refresh token stored in: **Encrypted SQLite** via `crates/db` TokenStoragePort
CSRF protection approach: **N/A** — tokens never sent via cookies; API is localhost-only

---

## Concept 7: Password Reset Flow

**Not applicable.** Bungie handles all credential recovery. If a user forgets their Bungie password, they go to bungie.net.

---

## Concept 8: Rate Limiting

| Attack | What Happens | Mitigation |
|--------|--------------|------------|
| **Brute force** | N/A — no passwords | N/A |
| **Token abuse** | Excessive Bungie API calls | ADR 010: Serial mutations, no parallel requests |
| **Enumeration** | N/A — no user registration | N/A |

### Our Decision
Bungie API rate limit: **25 requests/sec** (Bungie-enforced)
Our self-imposed limit: **Serial execution only** (ADR 010)

---

## Concept 9: Multi-Tenancy

### Our Decision
- [x] Single tenant (no org boundaries)

Rationale: This is a single-player desktop companion app. Each user has 1 Bungie account. There are no organizational boundaries.

---

## Concept 10: What Goes in the Token?

Bungie's OAuth tokens contain scopes. We store:

### Stored Claims (in our SQLite)
- [x] Bungie Membership ID
- [x] Membership Platform Type (Xbox, PSN, Steam, etc.)
- [x] Access Token (encrypted)
- [x] Refresh Token (encrypted)
- [x] Expiration Timestamp

---

## Summary: Critical Decisions Checklist

- [x] No password storage — delegated to Bungie SSO
- [x] Session strategy — stateless Bungie OAuth2 tokens
- [x] Access token lifetime — ~60 min (Bungie-controlled)
- [x] Refresh token lifetime — ~90 days (Bungie-controlled)
- [x] Client-side token storage — encrypted SQLite, never browser
- [x] Rate limiting strategy — serial execution (ADR 010)
- [x] Single-tenant model — one player, one Bungie account
