# ADR-0001: Layered Architecture with Hexagonal Target

**Status:** Accepted *(Migration completed - see ADR-0005)*  
**Date:** December 2024  
**Deciders:** Development Team

## Context

We're building a SaaS platform for NYC plumbing compliance (Local Law 152 inspections). The MVP needed to ship quickly while maintaining code quality that would support future growth.

The team considered several architectural patterns:
- Monolithic MVC
- Clean Architecture (Uncle Bob)
- Hexagonal Architecture (Ports & Adapters)
- CQRS/Event Sourcing

## Decision

We adopt a **Layered Architecture** with **Repository Pattern** as the immediate implementation, with a clear migration path toward **Hexagonal Architecture**.

### Current Structure

```
src/
├── app/           # HTTP layer (driving adapters)
├── domain/        # Business logic + repository interfaces (ports)
├── infrastructure # Database + external services (driven adapters)
└── shared/        # Cross-cutting concerns
```

### Key Patterns

1. **Repository interfaces in domain** - Services depend on abstractions
2. **Infrastructure implements interfaces** - Drizzle repositories implement domain contracts
3. **Constructor injection** - Explicit dependencies for testability
4. **Composition root** - Centralized wiring in `container.ts`

### Hexagonal Alignment (~80%)

| Hexagonal Concept | Our Implementation |
|-------------------|-------------------|
| Driving Adapters | Fastify routes in `app/http/routes/` |
| Domain Core | `domain/*/services/` |
| Driven Ports | Repository interfaces in `domain/*/repositories/` |
| Driven Adapters | `infrastructure/db/repositories/` |
| Composition Root | `src/app/container.ts` |

### Known Gaps (Technical Debt)

1. **Domain type leakage** - Repository interfaces reference Drizzle schema types
2. **Implicit use cases** - Routes call services directly, no explicit use case layer

## Consequences

### Positive

- **Fast MVP delivery** - Less abstraction overhead than full hexagonal
- **Clear upgrade path** - Can introduce pure domain entities incrementally
- **Good testability** - Services are mockable via interfaces
- **Team familiarity** - Layered architecture is well-understood

### Negative

- **Schema coupling** - Refactoring DB schema requires touching domain layer
- **Navigation complexity** - Without pure domain entities, understanding business rules requires reading infrastructure
- **Partial hexagonal** - Some hexagonal benefits (complete isolation) not yet realized

## Alternatives Considered

### Full Hexagonal from Day One

**Rejected because:**
- Higher upfront abstraction cost
- MVP timeline pressure
- Can be introduced incrementally later

### Monolithic MVC

**Rejected because:**
- Poor testability
- Business logic scattered across controllers
- Difficult to evolve

### CQRS/Event Sourcing

**Rejected because:**
- Overkill for current domain complexity
- Team learning curve
- Can add later for specific bounded contexts if needed

## Migration Path

See [Backend Architecture Guide](../architecture/BACKEND_ARCHITECTURE.md#migration-path-to-hexagonal) for detailed migration phases.
