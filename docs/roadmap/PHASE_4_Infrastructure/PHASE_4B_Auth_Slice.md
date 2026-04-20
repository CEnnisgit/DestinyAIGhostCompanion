# Phase 4B: Auth Slice

> **Status:** 🔲 Not Started
> **Objective:** Implement concrete adapters so the `OAuthSessionSaga` can persist tokens to Postgres and resolve user identity from Bungie.
> **Crates:** `crates/db`, `crates/api`
> **Depends On:** Phase 4A (Postgres must be running)

---

## Context for the Agent

The Domain layer already contains a fully tested `OAuthSessionSaga` at `crates/domain/src/auth/saga.rs`. It orchestrates the login flow by calling two **Ports** (Rust traits):

1. **`TokenStoragePort`** — defined in `crates/domain/src/auth/ports.rs`
   - `save_token(&self, membership_id, token) -> Result<()>`
   - `get_token(&self, membership_id) -> Result<Option<BungieOAuthToken>>`

2. **`BungieIdentityProviderPort`** — defined in `crates/domain/src/auth/ports.rs`
   - `resolve_user_identity(&self, token) -> Result<BungieMembershipId>`

Your job is to write the concrete structs that implement these traits.

## Deliverables

### 1. `crates/db/src/postgres_token_storage.rs`
Implement `TokenStoragePort` using `sqlx::PgPool`:
- `save_token`: UPSERT into the `bungie_tokens` table (created in Phase 4A migration).
- `get_token`: SELECT by `membership_id`. Map the row to `BungieOAuthToken`.
- The `BungieOAuthToken` struct is defined in `crates/domain/src/auth/token.rs`. Do NOT modify the domain.

### 2. `crates/api/src/bungie_identity_client.rs`
Implement `BungieIdentityProviderPort` using `reqwest`:
- After the user completes the OAuth flow, Bungie gives us an `access_token`.
- Hit the Bungie endpoint: `GET https://www.bungie.net/Platform/User/GetMembershipsForCurrentUser/`
  - Headers: `Authorization: Bearer {access_token}`, `X-API-Key: {BUNGIE_API_KEY}`
- Parse the response JSON to extract the primary `membershipId`.
- Return a `BungieMembershipId` (defined in `crates/domain/src/auth/membership.rs`).

### 3. `crates/api/src/bungie_oauth_routes.rs`
Implement the Bungie OAuth2 callback route using `axum`:
- **`GET /auth/callback?code={code}`**: Bungie redirects here after user approves.
  - Exchange the `code` for an `access_token` via `POST https://www.bungie.net/Platform/App/OAuth/Token/`
  - Construct a `BungieOAuthToken` from the response.
  - Call `OAuthSessionSaga::process_new_login(token)`.
  - Return the `BungieMembershipId` as a JSON response (or set a session cookie).
- **`GET /auth/login`**: Redirect the user to Bungie's OAuth consent screen.
  - URL: `https://www.bungie.net/en/OAuth/Authorize?client_id={BUNGIE_CLIENT_ID}&response_type=code`

### 4. Composition Root (`crates/api/src/main.rs` or `src/main.rs`)
Wire the adapters together:
```rust
let pool = PgPool::connect(&database_url).await?;
let token_storage = Arc::new(PostgresTokenStorageAdapter::new(pool.clone()));
let identity_provider = Arc::new(BungieIdentityClient::new(reqwest_client, api_key));
let auth_saga = OAuthSessionSaga::new(token_storage, identity_provider);
```

## Bungie API Reference
- OAuth Token Exchange: `POST https://www.bungie.net/Platform/App/OAuth/Token/`
  - Body: `grant_type=authorization_code&code={code}&client_id={id}&client_secret={secret}`
  - Returns: `{ "access_token": "...", "refresh_token": "...", "expires_in": 3600, "membership_id": "..." }`
- Get Memberships: `GET https://www.bungie.net/Platform/User/GetMembershipsForCurrentUser/`
  - Returns: `{ "Response": { "primaryMembershipId": "...", ... } }`

## Verification
- [ ] `docker compose up -d` is running Postgres.
- [ ] Navigate to `http://localhost:8080/auth/login` → redirects to Bungie.
- [ ] After Bungie approval, callback lands at `/auth/callback` → token is persisted in the `bungie_tokens` table.
- [ ] `SELECT * FROM bungie_tokens;` shows a row with the user's `membership_id`.

## ADR References
- **ADR 005**: Delegated Authentication — Bungie OAuth2 SSO, no password storage.

## Next Phase
Once verified, proceed to → [Phase 4C: Conversation Slice](./PHASE_4C_Conversation_Slice.md)
