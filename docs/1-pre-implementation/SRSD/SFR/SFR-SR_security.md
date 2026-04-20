# Functional Requirements: Security (SFR-SR)

## Authentication (SFR-SRAN)
- **`SFR-SRAN-01` (Bungie OAuth2 Flow)**: The system must securely broker the Bungie.net Authorization Code flow. Users must be redirected to `bungie.net/en/oauth/authorize` to explicitly grant the Ghost Companion permission to edit their inventory.
- **`SFR-SRAN-02` (Token Refresh Lifecycle)**: The system must silently handle the automated refreshing of the Bungie OAuth Bearer Token using the securely stored Refresh Token.
- **`SFR-SRAN-03` (AES Encryption Storage)**: The resulting OAuth tokens must be stored locally on the user's disk (e.g., in a `~/.ghost_tokens` file) encrypted via AES block ciphers tied to a local machine key or an `.env` secret.

## Authorization (SFR-SRAZ)
- **`SFR-SRAZ-01`**: The application operates strictly as a single-tenant executor. The locally executing user instance is authorized to manipulate only the Bungie account attached to the active OAuth session. There are no multi-tenant permission matrices.
