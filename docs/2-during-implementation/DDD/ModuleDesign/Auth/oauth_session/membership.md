# Value Object: BungieMembershipId

**Module Path:** `crates/domain/src/auth/membership.rs`

## Description
Due to **ADR 005 (Frictionless SSO)**, the system no longer features a "Local User Account" Table bound via email and Bcrypt password. The sole identity of any Ghost Companion user is their Bungie Membership ID. 

This struct acts as a rigorously typed wrapper around that ID.

## Invariants & Rules
1. **Non-Empty String Constraint:** `BungieMembershipId::new()` will automatically fail if provided an empty or whitespace-only string.
2. **Primary Key Native:** This ID natively serves as the Primary Key for the backend. All JWTs issued to the frontend are strictly keyed against this ID in their `sub` claim.
