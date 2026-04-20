# ADR 005: Frictionless Bungie SSO and the Deprecation of Local Passwords

## Status
Accepted

## Context (The Expert's Complaint)
During a structural audit of ADR 004 (Dual Authentication), a core design flaw was identified by a Domain Expert. ADR 004 required users to manually register an email and password to create a "Local Account" on the Ghost backend *before* being allowed to pair their Bungie OAuth tokens. 

The domain expert presented a critical complaint: **"If the entire purpose of the Ghost Companion is to proxy Destiny inventories, why are we soliciting and securing user passwords? Forcing the user to create an arbitrary local account introduces severe UX friction, increases our security liability (storing passwords), and fundamentally misunderstands the core utility of the app."**

## Decision
We will entirely scrap the concept of "Local User Accounts with Passwords" (deprecating ADR 004) and pivot to a true **Single Sign-On (SSO)** architecture driven entirely by Bungie.net.

1. **The Auth Flow:** The Ghost Companion front-end will have exactly one button: "Login with Bungie".
2. **Implicit Local Accounts:** When Bungie successfully returns the OAuth tokens, our Rust `crates/api` will make a server-side request to `/User/GetMembershipsForCurrentUser/`. We will use the returned unique `bungieGlobalDisplayName` or `membershipId` as the Primary Key for the user in our SQLite database.
3. **Frictionless JWTs:** The Rust backend will mint a local JWT for that `membershipId` and hand it to the client. The client is now fully locally authenticated, without ever typing an email or password.

## Consequences
- **Positive:** Massive reduction in UX friction. We no longer have to implement password reset flows, Argon2id hashing, or email verification routines. We completely offload identity validation liability to Bungie.
- **Negative:** If Bungie.net's authorization servers go down, users will not be able to log into the Ghost Companion. However, since the app cannot manipulate inventories when Bungie is down anyway, this negative is entirely mitigated by the domain's natural physics.
