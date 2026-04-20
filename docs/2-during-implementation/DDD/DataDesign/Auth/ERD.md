# Entity-Relationship Diagram: Auth Bounded Context

## Context
This diagram represents the strict relational database schema explicitly designed for the `auth` domain slice, governed by **ADR 005 (Frictionless SSO)**. Because there are no local passwords or emails, the database operates solely as a proxy mapping cache for Bungie.net profiles.

## Diagram

```mermaid
erDiagram
    %% Core Identity Table
    BungieIdentity {
        string membership_id PK "The canonical Bungie.net ID"
        string display_name "e.g., Guardian#1234"
        datetime last_login "Timestamp of last JWT minting"
    }

    %% Sensitive OAuth Table
    BungieOAuthToken {
        string membership_id FK "References BungieIdentity"
        bytearray access_token_enc "AES-256-GCM Encrypted Access Token"
        bytearray refresh_token_enc "AES-256-GCM Encrypted Refresh Token"
        datetime expires_at "System expiration clock"
        datetime refresh_expires_at "Maximum refresh lifetime"
    }

    %% Relationships
    BungieIdentity ||--o| BungieOAuthToken : "secures"
```

## Security Invariants
1. **Separation of Secrets:** Identifiable public data (`display_name`) is stored in `BungieIdentity` to be safely read by frontend profiles. Highly sensitive tokens are shoved into a 1:1 mapped separate table `BungieOAuthToken` to prevent accidental `SELECT * FROM` leakage.
2. **AES-GCM Requirement:** As defined by the Data Structure rules, the `_enc` fields in the database are stored as Raw BLOBs (byte arrays). They are physically unreadable if the `.sqlite` or Postgres row is compromised, because the Rust backend holds the decryption key in memory, outside the database.
