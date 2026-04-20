# Functional Requirements: Integration (SFR-IR)

## Interface Operations (SFR-IRI)
- **`SFR-IRI-01` (Client Interface Contract)**: The core Python backend must expose purely decoupled HTTP API routes so that the React SPA, iOS SwiftUI client, and vanilla Webapp can interact with the engine identically without duplicating execution logic.
- **`SFR-IRI-02` (LLM Provider Interface)**: The conversational logic must integrate with local LLM instances by sending properly formatted JSON requests to Ollama running generically at `http://localhost:11434`.
- **`SFR-IRI-03` (External LLM Fallback)**: The architecture must support API request structures for fallback processing against cloud-hosted models, primarily xAI's Grok API endpoint.

## Data Exchange Requirements (SFR-IRDX)
- **`SFR-IRDX-01` (Manifest Data Caching)**: The system must download and cache the massive Destiny 2 SQLite Manifest database locally. A Time-To-Live (TTL) configuration must dictate when the engine fetches an updated manifest structure.
- **`SFR-IRDX-02` (Inventory Execution Headers)**: Action requests sent to the Bungie.net `Destiny2` endpoints must strict-adhere to the formatting requirements, injecting the `X-API-Key` and the active OAuth `Bearer` token into the HTTPS headers.
