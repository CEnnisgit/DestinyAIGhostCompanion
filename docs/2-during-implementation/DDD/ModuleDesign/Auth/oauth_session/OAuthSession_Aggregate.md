# Aggregate Root: OAuthSession

**Bounded Context:** Auth
**Feature Slice:** `oauth_session`

## 1. Description
The `OAuthSession` is the aggregate root protecting the user's connection to Bungie.net. It ensures that the rest of the application never attempts to send expired tokens.

## 2. Core Invariants (Rules)
1. **Hard Expiration Check**: If the stored `BearerToken` is expired, the system MUST automatically negotiate a new one using the `RefreshToken` before delegating to the `Inventory` slice.
2. **Refresh Expiration Block**: If the `RefreshToken` is also expired (or missing), the system must halt and return a strict `UNAUTHORIZED_FLOW_REQUIRED` error to force the user back to the Bungie.net login screen.
3. **Token Secrecy**: Raw tokens must never be returned to the Presentation layer. The Presentation layer receives a generic system-level JWT cookie.

## 3. Hexagonal Ports
- **Driver Port**: Handled by the generic system JWT validator.
- **Driven Port (`BungieOAuthAdapter`)**: The interface for executing `POST /Platform/App/OAuth/Token/`.
