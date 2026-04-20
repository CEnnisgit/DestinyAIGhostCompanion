# ADR 014: Asynchronous In-Memory Lore Caching

## Status
Accepted

## Context
When analyzing the legacy `ghost/lore.py` module, a Senior Systems Engineer identified a critical concurrency failure. The Python script used synchronous disk I/O (`read_text()`) to crawl the hard drive and load raw text snippets during runtime whenever the user asked a question.

In Enterprise Rust, the `Tokio` runtime relies on asynchronous, non-blocking threads. If we ported the Python code verbatim and executed `std::fs::read_to_string()` inside a server endpoint, it would physically block the Tokio worker thread for the entire duration of the disk read. 

Since Destiny 2 players execute critical inventory actions (e.g. swapping raid loadouts) in the heat of combat, any thread-blocking caused by someone asking a Lore question would queue up and bottleneck the Inventory actions, causing the server architecture to grind to a halt.

## Decision
We enforce **Global Asynchronous In-Memory Caching**.

When the application boots, the `crates/db/` layer must undergo a one-time Async Initialization Phase. It will asynchronously read the Bungie Manifest, construct the RAG retrieval space (detailed in ADR 015), and load it into a highly-concurrent, thread-safe memory container (e.g., `Arc<RwLock<...>>`).

The `GrimoireDatabasePort` is strictly forbidden from executing blocking disk I/O during an active user Request lifecycle. It must access RAM linearly.

## Consequences
- **Positive:** Mathematically guarantees sub-millisecond response times for RAG retrievals, preserving the Tokio thread-pool to immediately service Inventory equipping requests without delay.
- **Negative:** Increased passive RAM overhead on the deployment server, as the entire Destiny 2 Grimoire library index must be held in memory 24/7.
