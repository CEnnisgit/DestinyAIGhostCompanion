# ADR 008: Feature-Centric Vertical Slices

**Date:** 2025-12-18
**Status:** Accepted

## Context
Our monorepo was originally structured as a "Control Tower" (Backend) vs "Clients" (Web, Mobile). As the business logic grew, we faced "Layer Fatigue" and contract drift. The mobile app and backend were manually duplicating form schemas (`Record<string, unknown>` vs typed interfaces), leading to bugs and synchronization issues.

We need a way to:
1.  Share business logic (validation, schemas, state machines) between Mobile and Backend.
2.  Maintain strict boundaries so the Mobile app doesn't accidentally dependent on Backend infrastructure.
3.  Scale the team by allowing developers to work on a full feature (vertical slice) without context switching across the entire repo.

## Decision
We will adopt a **Feature-Centric Vertical Slice** architecture using shared packages.

### 1. The Structure
We will move domain logic out of `apps/` and into `packages/features/<feature>/`. Each feature package is split into three strict sub-packages:

*   **`core`**: Pure business logic (Hexagon).
    *   *Contains*: Zod schemas, Types, Pure Functions, State Machines.
    *   *Dependencies*: ZERO framework dependencies. No React, No Node, No Drizzle.
*   **`backend`**: Backend Adapters.
    *   *Contains*: API Validation helpers, DTO mappers.
    *   *Dependencies*: Can depend on `core`.
*   **`mobile`**: Mobile Adapters.
    *   *Contains*: React Native Hooks, State helpers, UI-agnostic logic.
    *   *Dependencies*: Can depend on `core`.

### 2. The "Thin App Shell"
Applications (`apps/*`) become thin shells responsible for:
*   Routing
*   Dependency Injection (Wiring)
*   Platform-specific UI (React/React Native components)
*   Hosting the "Adapters" (Repositories, API Handlers)

### 3. Drift Prevention
To prevent contract drift:
*   **Single Source of Truth**: Both Apps must import types/schemas from the `core` package.
*   **Strict Validation**: The Backend must use the shared Zod schema to validate incoming payloads. `Record<string, unknown>` is banned.

## Consequences
### Positive
*   **No Drift**: Mobile and Backend share the exact same validation logic.
*   **Locality**: Related logic is co-located in `packages/features/<feature>`.
*   **Reusability**: Core logic can be unit tested in isolation (fast tests).

### Negative
*   **Boilerplate**: Creating a new feature requires creating 3 `package.json` files.
*   **Versioning**: We must now manage versioning if the mobile app and backend diverge (solved via Versioning Policy).

## References
*   [Backend Roadmap](../roadmap/backend_roadmap.md)
