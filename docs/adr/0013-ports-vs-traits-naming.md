# ADR 013: Hexagonal Ports vs Standard Rust Traits Naming

## Status
Accepted

## Context
During the physical scaffolding of the `crates/domain` boundary, we had to decide how to name the files that declare the external boundaries of the application (e.g., the interfaces that connect to the database or external APIs).

In standard "everyday" Rust, these interfaces are physically evaluated as `trait` or `async_trait` blocks and are commonly filed under `traits.rs` or directly alongside the primary data structs. However, in our system, we are adhering strictly to Domain-Driven Design and Hexagonal Architecture.

## Decision
We will name the files defining these external boundaries deeply-coupled to infrastructure as `ports.rs`. 

While the Rust compiler views a "Port" and a "Trait" as the physically identical concept, naming the file `ports.rs` carries extreme psychological weight for developers. It formally signals that the specific traits within the file are `Secondary Ports`—"holes in the wall" of the pure domain vault that strictly require external infrastructure adapters (like `crates/db/` or `crates/api/`) to plug into them. 

## Consequences
- **Positive:** Instantly communicates Enterprise architecture boundaries to any developer reading the repository. Prevents developers from casually implementing database logic inside the pure domain.
- **Negative:** Non-standard for pure grassroots Rust developers who may be unfamilar with Java/C# Enterprise DDD terminology.
- **Future Flexibility:** Because a Port is physically just a `trait`, if the maintenance team later decides that the DDD "Port" terminology is too heavy or confusing for new Rust hires, they can safely execute a global search-and-replace to rename `ports.rs` to `traits.rs` without altering a single line of compiled logic or architectural integrity.
