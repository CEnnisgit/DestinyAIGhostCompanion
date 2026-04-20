# Value Object: BungieOAuthToken

**Module Path:** `crates/domain/src/auth/token.rs`

## Description
This struct encapsulates the direct OAuth outputs from Bungie.net. Due to **ADR 005**, this token represents the ultimate authorization for the user, removing the need for a separate local password system.

## Invariants & Rules
1. **At-Rest Encryption:** Before being passed to `TokenStoragePort`, the `access_token` and `refresh_token` members must be structurally enforced for AES-256-GCM encryption at the DB boundary.
2. **Strict Expiration Checking:** The token object intrinsically tracks `expires_at` and `refresh_expires_at` using `chrono::DateTime<Utc>`. A saga cannot yield this token to the `inventory` slice if the system clock contradicts the timestamp.
