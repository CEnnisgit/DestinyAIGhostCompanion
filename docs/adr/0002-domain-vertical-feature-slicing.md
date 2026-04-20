# ADR 002: Vertical Feature Slicing inside `crates/domain`

## Status
Accepted

## Context
In monolithic web applications, it is common to physically group code by its technical layer (e.g., all `controllers/`, all `services/`, all `models/`). However, in the context of the Destiny API, cross-pollination between the "Voice AI LLM parsing logic" and "Inventory Equipping logic" within a `services/` folder will inevitably lead back to the tangled mess present in the old `ghost/assistant.py`.

## Decision
Within our isolated `crates/domain` codebase, we will enforce **Vertical Feature Slicing**, rooted in Domain-Driven Design (DDD). 

The source tree will physically divide business capabilities rather than technical boundaries:
- `crates/domain/src/auth/`
- `crates/domain/src/inventory/`
- `crates/domain/src/voice_ai/`

Each of these directories acts as its own Bounded Context, exposing strict public traits (Hexagonal Ports). `voice_ai` is not allowed to peek directly into `inventory`'s structs. Note that this slicing occurs *inside* the single `domain` crate to prevent Cargo Workspace sprawling.

## Consequences
- **Positive:** Total logical isolation. A developer changing the Voice AI prompt parsing will have zero risk of accidentally breaking the Bungie Item Transfer workflows. 
- **Negative:** Minor boilerplate overhead when different domains need to communicate (e.g., Voice AI needing to request an Inventory Equip action via a formal `InventoryCommand` trait).
