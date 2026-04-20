# Value Objects & Entities: OAuth Session

Based on the invariants enforced by the `OAuthSession`, the Domain mandates the following data structures.

## Value Objects (VO)
- **`BearerToken` (String)**: Encrypted internal token payload.
- **`ExpirationTimestamp` (i64)**: Unix timestamp determining if the token is valid.
- **`BungieMembershipId` (i64)**: The unique ID resolving to the logged-in user.

## Entities
- **`UserSession`**: The entity bridging the local application user with their saved database tokens.
