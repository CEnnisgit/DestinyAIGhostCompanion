# ADR 010: Strict Serial Inventory Mutations

## Status
Accepted

## Context
When migrating from Python's synchronous `requests` loop to Rust's heavily asynchronous and concurrent `Tokio` runtime, there is a tremendous risk associated with Bungie's edge network throttling. 
If an LLM parses a command like *"Equip my entire endgame Warlock loadout"* (which results in ~8 `TransferItem` and `EquipItem` HTTP POST actions), a naive Rust implementation might attempt to fire all 8 mutating HTTP POST requests concurrently using `futures::join_all!`.

**The Senior Domain Expert Complaint:**
"You cannot concurrency-blast the Destiny 2 inventory system. If you attempt 8 parallel mutations on a single Bungie Profile at the exact same millisecond, Bungie's CDN will either immediately panic and throw a `429 Too Many Requests` error, or worse, cause an internal database desync where the user's weapon gets permanently locked in transit. Mutating the user's profile must be physically serialized."

## Decision
We will enforce **Strict Serial Execution** inside `crates/domain/src/inventory/`. 
The `EquipItemSaga` will iterate over multiple-item targets synchronously via standard `for` loops and `await` boundary calls. It will completely forbid `join_all!` or parallel Tokio threads for any sequence involving `TransferItem`, `EquipItem`, or `PullFromPostmaster`. 

It must physically `await` Bungie's `HTTP 200 OK` from the first item transfer before it is legally allowed to spawn the HTTP request for the second item. 

## Consequences
- **Positive:** Mathematically protects the user's Destiny 2 inventory from lock-states and guarantees compliance with Bungie API throttling rules.
- **Negative:** The application will feel marginally slower when equipping 8 weapons compared to a theoretical parallel execution environment (total execution time might take 3-4 seconds instead of 0.5 seconds).
