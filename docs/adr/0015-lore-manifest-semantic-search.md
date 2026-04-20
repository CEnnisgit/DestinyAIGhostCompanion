# ADR 015: Retrieval-Augmented Generation (RAG) for Lore Searches

## Status
Accepted

## Context
The legacy Python `ghost/lore.py` script suffered from two fatal architectural flaws:
1. **The "PC-Bound" Flaw:** It relied on a hardcoded local directory (`data/lore/*.md`) managed by a single developer on their personal PC. In a production environment or cloned repository, this system would immediately crash. 
2. **The Primitive Pipeline Flaw:** It attempted to find Lore by stripping punctuation and simply counting how many exact words overlapped between the user's voice prompt and the `.md` files. This is not semantic AI; it would completely fail if a user asked about "the big white sphere" instead of "The Traveler".

To build a true, bleeding-edge generative AI companion, the backend requires highly-contextualized knowledge retrieval.

## Decision
We are completely tearing down the custom `.md` crawler and standardizing on **Retrieval-Augmented Generation (RAG)** as the core architectural pattern for all Lore intents.

1. **The Universal Data Source:** Instead of local PC text files, the `crates/db/` adapter will execute RAG against the **Bungie Manifest** (specifically `DestinyLoreDefinition`), which contains the entire universe of Destiny text globally. It will automatically download on any machine.
2. **The RAG Pipeline:** The `GrimoireDatabasePort` implementation must act as a true RAG orchestrator. It must leverage semantic search capabilities (either via SQLite's FTS5 Full-Text Search integration or a lightweight local Vector Embedding model) to map the user's intent to the *meaning* of the lore, not just string overlaps. It will retrieve the semantically-relevant lore stubs, and inject them into the `GenerativeAiPort` context window.

## Consequences
- **Profound Upgrade to AI Intelligence:** By mandating a RAG architecture natively, the `lore` slice transforms from a brittle keyword search into an intelligent entity that understands Destiny synonyms, concepts, and themes natively.
- **Universal Portability:** The backend is no longer "PC Bound." It can be deployed via Docker to any cloud server, and the RAG pipeline will automatically construct its knowledge base from the Bungie servers.
