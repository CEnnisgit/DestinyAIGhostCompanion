# Saga Root: OAuthSessionSaga

**Module Path:** `crates/domain/src/auth/saga.rs`

## Description
The state-machine / process manager orchestrating the Frictionless Single Sign-On (SSO) event.

## Core Process Flow
The Saga strictly governs the `process_new_login` event sequence:
1. *API receives an OAuth Code and asks Bungie for the raw tokens.*
2. *API passes raw tokens into `OAuthSessionSaga`.*
3. Saga invokes `BungieIdentityProviderPort` to resolve who the tokens belong to.
4. Saga invokes `TokenStoragePort` to securely persist the token to the newly resolved `BungieMembershipId`.
5. Saga yields the `BungieMembershipId` back to the API so it can mint a standard Local JWT for the frontend.

By centralizing this flow in the Saga, `crates/api` remains completely agnostic of Bungie's identity resolution pipeline.
