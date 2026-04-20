# Hexagonal Ports

**Module Path:** `crates/domain/src/auth/ports.rs`

## 1. TokenStoragePort (Secondary/Driven)
This port bridges the Pure Domain to `crates/db`. 
- **Method:** `save_token(membership_id, token)`
- **Rule:** The underlying SQLx implementation in `crates/db` must transparently AES-GCM encrypt the tokens before executing the SQL `INSERT`.

## 2. BungieIdentityProviderPort (Secondary/Driven)
This port bridges the Pure Domain to HTTP Bungie APIs.
- **Method:** `resolve_user_identity(token)`
- **Rule:** Takes a freshly minted `BungieOAuthToken` and hits the `/User/GetMembershipsForCurrentUser/` endpoint. Returns the user's canonical `BungieMembershipId`, acting as the critical "Identity Resolution" handshake for SSO.
