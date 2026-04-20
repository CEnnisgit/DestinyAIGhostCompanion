# ADR 006: Idiomatic Rust Module Naming vs Tactical DDD Naming

## Status
Accepted

## Context
During the physical scaffolding of the `crates/domain` boundary, initial files were named directly after tactical Domain-Driven Design (DDD) patterns (e.g., `value_objects.rs`, `aggregate.rs`, `adapters.rs`). A Senior Rust Engineering review highlighted that this violates idiomatic Rust conventions. In Rust, the module (`mod`) tree is designed to organize code by the **domain concept it represents** (e.g., `token`, `membership`, `saga`), not the architectural category.

Using tactical names results in highly unidiomatic import statements such as:
`use crate::auth::value_objects::BungieOAuthToken;`

## Decision
While we will strictly maintain Domain-Driven Design logically, we will enforce **Idiomatic Rust Module Naming**. 
We will never name a file `aggregate.rs` or `value_object.rs`. Instead, files will be named after the conceptual entity, or generic application architectures common to Rust:

- `value_objects.rs` -> split into conceptual files (e.g., `token.rs`, `membership.rs`).
- `aggregate.rs` -> renamed to `saga.rs` or named after the orchestrator.
- `adapters.rs` -> renamed to `ports.rs` (to define the trait boundaries clearly).

## Consequences
- **Positive:** Rust imports become significantly cleaner and more idiomatic (`use crate::auth::token::BungieOAuthToken;`). Developers familiar with Rust but unfamiliar with Java-style DDD will experience much less friction.
- **Negative:** Identifying whether an object is a Value Object or an Entity requires looking at the struct definition rather than relying on the file name.
