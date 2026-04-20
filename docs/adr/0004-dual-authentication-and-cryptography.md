# ADR 004: Dual Authentication and Security Primitives

## Status
Superseded by ADR 005

## Context
The application must authenticate two separate entities:
1. **The Human User:** The person using the Ghost Companion desktop/mobile app.
2. **The Bungie API:** The Destiny 2 servers which require OAuth tokens to modify player inventory.

The legacy Python system attempted to solve this with a mix of truncated Bcrypt passwords, vulnerable XOR "encryption" of tokens, and insecure filesystem storage. Furthermore, it blurred the lines between logging into the desktop app and authenticating with Bungie.

## Decision
We will enforce a strict **Dual Authentication** architecture in the Rust `crates/domain/src/auth/` module, coupled with hardened security primitives:

1. **User AuthN (Local API Access):** 
   - Users will authenticate with the local Rust API using a username/password.
   - Passwords will strictly be hashed using **Argon2id** (deprecating the older Bcrypt implementation to avoid the 72-byte truncation flaw).
   - Successful login issues a strictly validated JSON Web Token (`JWT`).

2. **Bungie OAuth (External App Access):**
   - The user initiates the Bungie OAuth flow, protected by a cryptographically secure, randomized `state` parameter to prevent CSRF attacks.
   - The returned Bungie `access_token` and `refresh_token` will be **encrypted at rest using AES-256-GCM**.
   - These encrypted tokens are saved in the SQLite/Postgres database and bound to the local User's ID via a `user_bungie_tokens` junction table.

## Consequences
- **Positive:** Enterprise-grade cryptography. Native multi-tenant support (multiple siblings can use the Ghost Companion on the same desktop PC with their own local accounts and separate Bungie accounts).
- **Negative:** Increased complexity in the `db` crate, as it now requires AES decryption layers when requesting an OAuth token from the database.
