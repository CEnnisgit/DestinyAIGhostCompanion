# ADR-0005: Hexagonal Migration Complete

**Status:** Accepted  
**Date:** December 2024  
**Deciders:** Development Team  
**Supersedes:** Partial aspects of ADR-0001

## Context

ADR-0001 established hexagonal architecture as the **target**, but acknowledged gaps:
- Domain type leakage (repository interfaces referenced Drizzle types)
- Implicit use cases (routes called services directly)
- Legacy services in `domain/*/services/`

The migration is now complete. This ADR documents the final state.

## Decision

We completed the hexagonal migration with the following structure:

### Module Structure (per Bounded Context)

```
src/modules/{context}/
├── domain/           # Pure types (entities, value objects)
├── ports/            # Repository interfaces (no infra deps)
├── adapters/         # Drizzle implementations
├── application/      # Use-cases (orchestration)
├── moduleFactory.ts  # Dependency wiring
├── index.ts          # Public API exports
└── NAVIGATION.md     # Developer docs
```

### Migrated Modules

| Module | Status | Use Cases |
|--------|--------|-----------|
| auth | ✅ | register, login, getMe, forgotPassword, resetPassword |
| company | ✅ | create/get/update company, technician management |
| compliance | ✅ | jobs, buildings, forms, reports, bookings |

### Deleted Legacy Code

```
src/domain/compliance/services/  # 13 files deleted
├── BookingService.ts
├── BuildingService.ts
├── FormService.ts
├── JobService.ts
├── ReportService.ts
└── ... (all tests)
```

### ESLint Enforcement

Added architectural guard rules:
- Domain layer cannot import infrastructure/adapters/Drizzle
- Application layer cannot import adapters
- Modules cannot import from legacy `src/domain/**`

## Consequences

### Positive

- **Pure domain layer** - No infrastructure dependencies in domain types
- **Explicit use cases** - Testable, single-responsibility orchestration
- **Container-based wiring** - Dependencies injected at composition root
- **Cross-module boundaries** - Only public API exports cross module boundaries
- **Lint-enforced** - Architecture violations caught at build time

### Negative

- **More files per feature** - Hexagonal requires more structure
- **Learning curve** - Team must understand ports/adapters pattern

## Migration Path Reference

| Phase | Commit | Changes |
|-------|--------|---------|
| Phase 0 | 20fa322 | Hexagonal skeleton |
| Phase 1 | b8a11db | Compliance module |
| Phase 2 | 69cd802 | Auth module |
| Phase 3 | 734a057 | Company module |
| Phase 4 | 5c4d142 | Container wiring |
| Cleanup | bbd4479 | Delete legacy services |

## Relationship to ADR-0001

ADR-0001 described the **target architecture**. This ADR confirms:
- The target has been achieved
- The "Known Gaps" from ADR-0001 are resolved
- ESLint guards prevent regression
