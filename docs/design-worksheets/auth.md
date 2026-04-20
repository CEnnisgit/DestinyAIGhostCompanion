# Auth Design Worksheet

> A guided learning journey for designing authentication from scratch.  
> Use this as a reference while researching. Capture your decisions as you learn.

---

## Concept 1: Identity vs Authentication vs Authorization

Before designing, understand what you're actually building:

| Term | What It Means | Example |
|------|---------------|---------|
| **Identity** | Who is this person? | User ID, email, profile |
| **Authentication (AuthN)** | Prove you are who you claim to be | Login with password |
| **Authorization (AuthZ)** | What are you allowed to do? | Role-based access |

> **Why it matters:** Many systems conflate these. Keeping them separate makes your design cleaner. Your "auth module" might only handle AuthN, with AuthZ handled elsewhere.

### Your Decision
- [ ] This module handles: Authentication only
- [ ] This module handles: Authentication + Authorization
- [ ] This module handles: Identity + Authentication + Authorization

---

## Concept 2: Credential Types

How do users prove their identity?

| Method | How It Works | Trade-offs |
|--------|--------------|------------|
| **Password** | User knows a secret | Simple, but weak if passwords are bad |
| **Magic Link** | Email a login link | No password to forget, but requires email access |
| **OAuth/SSO** | Delegate to Google, etc. | Convenient, but you depend on external providers |
| **API Key** | Long-lived secret token | Good for machines, bad for humans |
| **Passkey/WebAuthn** | Cryptographic key on device | Most secure, but newer/complex |

> **Research prompt:** Search "passwordless authentication pros cons" if considering alternatives to passwords.

### Your Decision
Primary method: _____________  
Secondary/future: _____________

---

## Concept 3: Password Storage

**NEVER store plain-text passwords.** You store a *hash* — a one-way transformation.

| Algorithm | Status | Notes |
|-----------|--------|-------|
| **MD5, SHA1** | ❌ Broken | Never use for passwords |
| **bcrypt** | ✅ Good | Battle-tested, widely supported |
| **scrypt** | ✅ Good | Memory-hard (resists GPU attacks) |
| **Argon2** | ✅ Best | Winner of Password Hashing Competition (2015) |

> **Why it matters:** If your database leaks, attackers try to reverse hashes. Modern algorithms are intentionally slow to make this impractical.

> **Research prompt:** "Argon2 vs bcrypt 2024" for current recommendations.

### Your Decision
Algorithm: _____________  
Rationale: _____________

---

## Concept 4: Session Management

After login, how do you "remember" the user is authenticated?

### Option A: Server-Side Sessions
- Server stores session data (in memory, Redis, DB)
- Client gets a session ID cookie
- Every request: server looks up session

| Pros | Cons |
|------|------|
| Easy to revoke (delete session) | Requires server storage |
| Can store arbitrary data | Harder to scale horizontally |

### Option B: Stateless Tokens (JWT)
- Server issues a signed token containing user data
- Client sends token with every request
- Server verifies signature, trusts the data

| Pros | Cons |
|------|------|
| No server storage needed | Can't revoke without extra work |
| Scales horizontally easily | Token size can grow |
| Works well for APIs | Must handle expiration carefully |

> **Research prompt:** "JWT vs session cookies" and "JWT security best practices"

### Your Decision
- [ ] Server-side sessions
- [ ] Stateless JWT
- [ ] Hybrid (short JWT + refresh mechanism)

Rationale: _____________

---

## Concept 5: Token Lifetimes

If using tokens, how long should they live?

### Access Token
- Used for every API request
- **Short-lived** = more secure (less time for stolen token to be used)
- **Long-lived** = better UX (fewer refreshes)

| Duration | Use Case |
|----------|----------|
| 5-15 min | High security (banking) |
| 15-60 min | Standard web apps |
| Hours/days | Low-risk internal tools |

### Refresh Token
- Used only to get new access tokens
- Lives longer than access token
- **Critical:** Must be stored securely (HttpOnly cookie, not localStorage)

> **Why it matters:** If an access token is stolen, damage is limited to its lifetime. Refresh tokens are higher-value targets.

### Your Decision
Access token lifetime: _____________  
Refresh token lifetime: _____________  
Refresh token storage: _____________

---

## Concept 6: Token Storage (Client-Side)

Where does the client keep tokens?

| Location | Security | XSS Vulnerable? | CSRF Vulnerable? |
|----------|----------|-----------------|------------------|
| **localStorage** | Low | ✅ Yes | No |
| **sessionStorage** | Low | ✅ Yes | No |
| **HttpOnly Cookie** | High | No | ✅ Needs protection |
| **Memory only** | Highest | No | No |

> **Key insight:** HttpOnly cookies can't be read by JavaScript, so XSS can't steal them. But you need CSRF protection.

> **Research prompt:** "XSS vs CSRF attacks" and "HttpOnly cookie security"

### Your Decision
Access token stored in: _____________  
Refresh token stored in: _____________  
CSRF protection approach: _____________

---

## Concept 7: Password Reset Flow

How do users recover access?

### Standard Flow
1. User requests reset → you send email with token
2. User clicks link → lands on reset page with token in URL
3. User submits new password → you verify token, update password

### Critical Security Questions
- **Token lifetime?** Too long = insecure. Too short = bad UX. (Typically 1-24 hours)
- **One-time use?** Should token be invalid after use? (Yes)
- **Rate limiting?** Prevent enumeration attacks (Yes, strict)
- **Generic responses?** Don't reveal if email exists ("If account exists, email sent")

> **Research prompt:** "password reset token security best practices"

### Your Decision
Token lifetime: _____________  
Token storage: [ ] DB / [ ] Signed URL / [ ] Other  
Email reveals account existence: [ ] Yes / [ ] No

---

## Concept 8: Rate Limiting

Authentication endpoints are attack targets.

| Attack | What Happens | Mitigation |
|--------|--------------|------------|
| **Brute force** | Try many passwords | Rate limit per account |
| **Credential stuffing** | Try leaked password lists | Rate limit per IP + CAPTCHA |
| **Enumeration** | Discover valid emails | Generic error messages |

### Your Decision
Login rate limit: _____ attempts per _____ window  
Register rate limit: _____ per _____  
Password reset rate limit: _____ per _____

---

## Concept 9: Multi-Tenancy

Does your auth need to understand organizational boundaries?

| Model | Description |
|-------|-------------|
| **Single tenant** | One organization, simple |
| **Multi-tenant (shared)** | Multiple orgs share DB, isolated by tenant ID |
| **Multi-tenant (isolated)** | Separate DB per org |

> **Why it matters:** If Company A's admin shouldn't see Company B's users, you need tenant isolation from day one.

### Your Decision
- [ ] Single tenant (no org boundaries)
- [ ] Multi-tenant (tenant ID in token claims)

---

## Concept 10: What Goes in the Token?

JWT payload contains "claims" — data about the user.

### Standard Claims
- `sub` (subject): user ID
- `iat` (issued at): timestamp
- `exp` (expires at): timestamp

### Custom Claims
- Role? Company ID? Permissions?

> **Trade-off:** More data = bigger token, but fewer DB lookups. Less data = smaller token, but more lookups.

### Your Decision
Token will include:
- [ ] userId
- [ ] email
- [ ] role
- [ ] companyId (if multi-tenant)
- [ ] Other: _____________

---

## Summary: Critical Decisions Checklist

Before coding, you should have answers for:

- [ ] Password hashing algorithm
- [ ] Session strategy (stateful vs stateless)
- [ ] Access token lifetime
- [ ] Refresh token lifetime and storage
- [ ] Client-side token storage approach
- [ ] Password reset token lifetime
- [ ] Rate limiting strategy
- [ ] What claims go in the token
- [ ] Multi-tenancy model (if applicable)

---

## Research Queue

Topics to look up as you work through this:

- [ ] _____________
- [ ] _____________
- [ ] _____________
