# ADR 001: Rust Cargo Workspace Breakdown

## Status
Accepted

## Context
The previous architecture of the Destiny AI Ghost Companion relied heavily on massive Python scripts (specifically a 286KB `ghost/assistant.py` and an 83KB `server.py`). These scripts contained tangled routing, Natural Language Processing, HTTP calls to LLMs, and direct dictionary manipulation for Bungie's API. This caused severe technical debt, made unit testing impossible, and introduced significant execution latency.

## Decision
We will execute a full rewrite of the backend into a **Rust Cargo Workspace** heavily enforcing separation of concerns. The workspace will be strictly limited to exactly three crates representing technical layers:

1. `crates/api`: The primary driver adapter (Axum). Exclusively handles network routing, JWT validation, and immediate hand-offs.
2. `crates/db`: The secondary driven adapter (SQLx). Explicitly manages the persistence of Bungie session tokens and the local caching of the Destiny Manifest.
3. `crates/domain`: The isolated core. This crate contains no network layer knowledge. It handles business validation (e.g., "Can the user afford to vault this?"), Intent Parsing, and Bungie workflow Saga orchestrations. 

## Consequences
- **Positive:** Massive latency reductions, type-safety protecting against Bungie API undocumented changes, and strict code isolation.
- **Negative:** Slower initial development time to recreate the Python bindings and build the strict type boundary mappings for Destiny Hashes.
