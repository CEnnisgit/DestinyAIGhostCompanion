# ADR-0003: Container-based Dependency Wiring

**Status:** Accepted  
**Date:** December 2024  
**Deciders:** Development Team

## Context

Our backend had dependency wiring scattered across 7 route files. Each route instantiated its own repositories and services:

```typescript
// ❌ BEFORE: Each route file did its own wiring
export async function jobRoutes(fastify: FastifyInstance) {
    const jobRepository = new DrizzleJobRepository();
    const buildingRepository = new DrizzleBuildingRepository();
    const jobService = new JobService(jobRepository, buildingRepository);
    // ...
}
```

This caused several problems:
1. **No single source of truth** - Hard to see the full dependency graph
2. **Duplicate instances** - Multiple services creating the same repositories
3. **Testing friction** - Difficult to swap implementations
4. **Navigation overhead** - AI agents and developers had to search multiple files

## Decision

We introduce a **Composition Root** at `src/app/container.ts` that centralizes all dependency wiring.

### Container Structure

```typescript
// src/app/container.ts
export const repositories = {
    user: new DrizzleUserRepository(),
    job: new DrizzleJobRepository(),
    // ...all repositories
};

export const container = {
    repositories,
    services: {
        job: new JobService(repositories.job, repositories.building),
        // ...all services
    },
    factories: {
        createAuthService  // For request-scoped dependencies
    }
};

// Helper functions for common patterns
export async function getCompanyIdForUser(userId: string, role: string): Promise<string>;
export async function getTechnicianIdForUser(userId: string): Promise<string>;
```

### Route Usage

```typescript
// ✅ AFTER: Routes import from container
import { container, getCompanyIdForUser } from '../../container';

export async function jobRoutes(fastify: FastifyInstance) {
    const { job: jobService } = container.services;
    
    fastify.post('/', async (request, reply) => {
        const companyId = await getCompanyIdForUser(user.userId, user.role);
        const job = await jobService.createJob(companyId, data);
        return reply.send({ success: true, data: job });
    });
}
```

## Consequences

### Positive

- **Single authoritative source** - One file shows the entire object graph
- **Faster navigation** - "How is X constructed?" → check `container.ts`
- **Singleton guarantees** - Repositories instantiated once
- **Testability** - Can create test containers with mock adapters
- **Thinner routes** - Route files focus on HTTP concerns only

### Negative

- **Import distance** - Routes import from `../../container` instead of adjacent files
- **Migration work** - Need to update all 7 route files (in progress)
- **Factory pattern** - AuthService needs special handling for JWT signing

### Migration Status

| Route | Status |
|-------|--------|
| `jobRoutes.ts` | ✅ Migrated |
| `authRoutes.ts` | ⏳ Needs factory pattern |
| `companyRoutes.ts` | ⏳ Pending |
| `buildingRoutes.ts` | ⏳ Pending |
| `formRoutes.ts` | ⏳ Pending |
| `reportRoutes.ts` | ⏳ Pending |
| `bookingRoutes.ts` | ⏳ Pending |

## Alternatives Considered

### Full DI Framework (InversifyJS, tsyringe)

**Pros:** Automatic resolution, decorators  
**Rejected because:**
- Added complexity for our scale
- Decorator-based approach obscures wiring
- Manual wiring is explicit and readable

### Keep Wiring in Routes

**Rejected because:**
- Core problem that motivated this ADR
- Doesn't scale as codebase grows

### Factory Functions per Domain

**Considered but:** Single container is simpler for our current size. Could split later if container grows too large.

## Future Considerations

- **Test container** - Create `container.test.ts` with mock adapters
- **Environment-specific containers** - Production vs development configurations
- **Lazy initialization** - For heavy services that aren't always needed
