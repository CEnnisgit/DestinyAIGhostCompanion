# Detailed Design: Functional Traceability Matrix

> **Source SRSD Codes:** Phase 1 `SFR`
> **Target Architecture:** Phase 2 Cargo Workspace

| SRSD Code | Description | Target Module Crate | Rationale |
|-----------|-------------|---------------------|-----------|
| `SFR-IODE-01..04` | Voice capture & UI interactions | `apps/frontend` | All raw user interactions happen identically within the Electron/React client. |
| `SFR-IODO-01..06` | TTS execution & visual output | `apps/frontend` | The Electron layer speaks the text returned by the API. |
| `SFR-PRC-01..03` | Speech-to-Text & Fallbacks | `apps/frontend` | Web Speech API is used by the client for parsing raw audio to text before sending. |
| `SFR-PRDM-01..02` | Intent Classification & Translation | `crates/domain` | Core rust business logic validates the text and calls the LLM for strict intent derivation. |
| `SFR-PRDP-01..04` | Fuzzy item resolution & Lore | `crates/domain` | Rust logic compares strings against local SQLite Bungie manifest. |
| `SFR-BRC-01..06` | Strict Rules (No dismantling, LLM isolation) | `crates/domain` | Type-safe Rust boundaries explicitly prevent generating "delete" JSON payloads. |
| `SFR-BRW-01..05` | Equip, Vault, Postmaster Workflows | `crates/domain` | Rust algorithms calculate deterministic transfer steps (Vault -> Char -> Equip). |
| `SFR-SRAN-01..02` | OAuth2 brokering & Token Refresh | `crates/api` | Axum middleware and callback routes intercept Bungie.net HTTP codes. |
| `SFR-SRAN-03` | Encrypted AES Token Storage | `crates/db` | Postgres/SQLx writes the encrypted payload to disk asynchronously. |
| `SFR-SRAZ-01` | Single-tenant rule | `crates/api` | Axum rejects requests spanning out of the authenticated user's ID bounds. |
| `SFR-IRI-01..03` | Internal Client API, Ollama & Grok fetch | `crates/api` | API exposes routes to React. Domain interacts with local/external LLM proxies. |
| `SFR-IRDX-01` | Manifest SQLite caching | `crates/db` | Database crate parses and saves the `.content` Sqlite file from Bungie. |
| `SFR-IRDX-02` | Bungie OAuth Header injection | `crates/domain` | Rust standard `reqwest` client builds the authorized headers securely. |
