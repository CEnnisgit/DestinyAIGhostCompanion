# ADR 009: Command Center CQRS Query Service

**Status:** Accepted
**Date:** 2025-12-19
**Deciders:** Development Team

## Context

The "Command Center" dashboard requires aggregating data from multiple domains (**Jobs**, **Compliance Forms**, **Reports**) into specific "Attention Queues" (e.g., "No Show", "Report Missing") and KPIs.

The initial implementation ("Lite") was embedded directly in the `apps/backend` layer as a UseCase (`GetCommandCenterUseCase.ts`). This approach had several issues:
1.  **Coupling**: Business logic for queue criteria (e.g., "15 min grace period", "5 min report threshold") was mixed with repository fetching logic.
2.  **Untestable**: Testing required spinning up the full backend or complex database mocks.
3.  **Contract Drift**: The Frontend (`web-company-dashboard`) manually redefined the API response types, leading to potential mismatches.

## Decision

We will implement the Command Center as a dedicated **CQRS Query Service** within the shared `@pcd/job-dispatch` feature package.

### 1. Feature-Centric Package
The logic moves to `packages/features/job-dispatch/`:
-   **`core`**: Defines the Read Models (`CommandCenterQueues`, `KPIs`) and shared constants/types.
-   **`backend`**: Implements the `CommandCenterQueryService`.

### 2. Port-Based Data Access
The Query Service defines its own **Query Ports** (`CommandCenterJobQueryPort`, etc.) optimized for reading specific data. It does **not** depend on the shared Domain Repositories directly.
-   The backend application (`apps/backend`) acts as the **Adapter**, wrapping existing TypeORM/Drizzle repositories to match these ports.

### 3. Read-Only (CQRS)
This service is strictly for **Queries**. It never mutates state. It computes views on the fly based on the current state of the system.

## Consequences

### Positive
*   **Single Source of Truth**: Both the Backend (implementation) and Frontend (consumer) import response types from `@pcd/job-dispatch-core`.
*   **Testable**: The complex queue logic (e.g., "is this job a no-show?") can be unit tested by injecting mock ports, without a real database.
*   **Decoupled**: The query logic is independent of the persistence layer. We could switch the underlying DB without changing the dashboard logic.

### Negative
*   **Boilerplate**: Requires writing "Adapter" functions in the backend to map existing Entities to the new Read Models.
*   **Memory Overhead**: Currently computes queues in-memory on every request. (Acceptable for current scale; can be cached later).

## Alternatives Considered

### 1. Stay with Inline UseCase ("Lite")
**Rejected because:** As the logic grew (adding more queues like "Ready to Send"), the UseCase became a "God Class" and testing became difficult.

### 2. Materialized Views (SQL)
**Rejected because:** Creating dedicated SQL views or tables for the dashboard would duplicate domain logic (e.g., "what constitutes a completed form") into SQL layer, splitting business rules across languages. On-the-fly aggregation is easier to maintain for now.
