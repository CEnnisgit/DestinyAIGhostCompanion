# ADR 0011: Out-of-Core Rust Worker for PAD Ingestion

**Date**: 2026-03-03  
**Status**: Accepted  
**Context**: Rebuilding the NYC Property Address Directory (PAD) Pipeline A (Bootstrap).

## Application Context
Our B2B plumbing compliance system requires city-wide building identities (1.1 million+ BINs) populated before launch. The raw data source for this is NYC Department of City Planning's PAD dataset, specifically `adr.txt` (Address Ranges) and `bbl.txt` (Tax Lots). 

The initial intuition was to use our primary application stack (Node.js/NestJS/TypeScript) to write a cron job or background worker. However, parsing a 1.1M+ row CSV file, aggregating tie-breaker data (multiple addresses mapped to a single BIN, resolving which BBL should be the `primaryBbl`), and maintaining a memory cache of the entire city's BBL relationships is extremely memory-bound and GC-heavy in JavaScript.

## Decision
We elected to implement Pipeline A as a standalone **Rust ETL CLI worker** (`apps/pad-ingestion`) rather than a TypeScript module inside the main Hexagonal architecture.

The worker communicates directly with the shared PostgreSQL database using `sqlx` (which verifies queries at compile-time against the live schema) and `drizzle-orm` concepts mapped to Rust structs.

## Rationale
1. **Memory Efficiency**: Rust's zero-cost abstractions and manual memory management allow us to use the `csv` crate to deserialize the PAD dataset almost instantaneously without crashing the V8 engine loop or requiring heavy batching workarounds in Node.js.
2. **Speed**: The entire ingestion pipeline across both `bbl.txt` (caching) and `adr.txt` (two passes: tallying tie-breakers and streaming DB inserts) processes in a matter of seconds.
3. **Type Safety and Bounds Checking**: The worker implements strict parsing logic reflecting the true Value Object invariants specified in our Domain Driven Design documentation (`BIN_VO_Spec.md`, `BBL_VO_Spec.md`, etc.). Rust's robust error handling ensures no silent corruption goes to Postgres. 
4. **Architectural Separation**: Ingestion logic is heavily infrastructural. Keeping it outside of our domain API prevents pollution of the core `buildings` module. 

## Consequences

**Positive:**
- Ingestion runs extraordinarily fast.
- Memory usage is flat and predictable.
- Strict compiler guarantees prevent runtime type crashes during CSV ingestion.

**Negative:**
- **Language Fragmentation:** The team now maintains a Rust workspace alongside the primary TypeScript monorepo. 
- **Duplicated Logic:** We must manually ensure that the domain invariants in `models.rs` mirror the TypeScript Value Object definitions in our Domain layer. 
- **DB Driver Split:** We are using `sqlx` in Rust but `drizzle-orm` in TypeScript. Schemas must stay in sync manually.

## Further Notes
To mitigate the schema drift issue, the Rust worker's DB connection queries the database directly based on the structure laid down by Drizzle migrations. To mitigate domain drift, we enforce the "Authority-per-VO" principle documented in our Data Sources Strategy.

> **Update (2026-03-25):** The Drizzle ORM layer (`packages/db`, `modules/crm`) has been removed. The DB driver split consequence (Negative #3) is resolved — all DB access now goes through Rust/SQLx (`crates/pcd-db`). References to "Drizzle migrations" and "drizzle-orm" above are historical context.
