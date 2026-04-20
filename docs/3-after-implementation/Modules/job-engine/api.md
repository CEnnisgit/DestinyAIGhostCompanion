# API Layer — Walkthrough

**File:** `crates/pcd-api/src/routes/jobs.rs` (315 lines)

## Overview

The API layer exposes 13 HTTP endpoints via Axum. All handlers depend on `Arc<dyn JobRepository>` (the trait, not the concrete adapter). A generic `command_handler` function eliminates boilerplate for the 10 PATCH/DELETE endpoints.

## Router

```rust
pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", post(create_job).get(list_jobs))
        .route("/{id}", get(get_job))
        .route("/{id}/start", patch(start_job))
        .route("/{id}/complete", patch(complete_job))
        .route("/{id}/cancel", patch(cancel_job))
        .route("/{id}/summary", patch(update_summary))
        .route("/{id}/site-notes", patch(update_site_notes))
        .route("/{id}/priority", patch(update_priority))
        .route("/{id}/client", patch(attach_client))
        .route("/{id}/ownership", patch(assign_ownership))
        .route("/{id}/obligation", patch(link_obligation).delete(unlink_obligation))
}
```

All routes are nested under `/api/jobs` in `main.rs`.

## Endpoint Catalog

| Route | Method | Handler | Body Type | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/jobs` | POST | `create_job` | `CreateJobRequest` | 201, 400, 500 |
| `/api/jobs` | GET | `list_jobs` | — | 200, 500 |
| `/api/jobs/{id}` | GET | `get_job` | — | 200, 404, 500 |
| `/api/jobs/{id}/start` | PATCH | `start_job` | `ActorBody` | 200, 404, 422, 500 |
| `/api/jobs/{id}/complete` | PATCH | `complete_job` | `ActorBody` | 200, 404, 422, 500 |
| `/api/jobs/{id}/cancel` | PATCH | `cancel_job` | `CancelBody` | 200, 404, 422, 500 |
| `/api/jobs/{id}/summary` | PATCH | `update_summary` | `TextBody` | 200, 404, 422, 500 |
| `/api/jobs/{id}/site-notes` | PATCH | `update_site_notes` | `TextBody` | 200, 404, 422, 500 |
| `/api/jobs/{id}/priority` | PATCH | `update_priority` | `TextBody` | 200, 404, 422, 500 |
| `/api/jobs/{id}/client` | PATCH | `attach_client` | `UuidBody` | 200, 404, 422, 500 |
| `/api/jobs/{id}/ownership` | PATCH | `assign_ownership` | `UuidBody` | 200, 404, 422, 500 |
| `/api/jobs/{id}/obligation` | PATCH | `link_obligation` | `UuidBody` | 200, 404, 422, 500 |
| `/api/jobs/{id}/obligation` | DELETE | `unlink_obligation` | `ActorBody` | 200, 404, 422, 500 |

## Request Types

```rust
// Full creation payload (3 required + 9 optional fields)
// Phase 1.5 change: address is required, building_id is optional (address-first per ADR-0023)
CreateJobRequest { company_id, job_type, address, created_by_user_id,
                   building_id?, title?, summary?, source_kind?, priority?,
                   client_id?, compliance_obligation_id?, requester_contact_id?, site_notes? }

// Mutation with just an actor
ActorBody { actor_user_id? }

// Cancel with reason
CancelBody { reason?, actor_user_id? }

// Text field update
TextBody { value, actor_user_id? }

// UUID reference update
UuidBody { id, actor_user_id? }
```

## Response Type: `JobResponse`

Implements `From<&Job>` for ergonomic conversion. All timestamps are serialized as RFC 3339 strings. VOs are serialized to their string representations.

22 fields returned — mirrors the aggregate's public state.

## The `command_handler` Pattern

The most important architectural pattern in this file:

```rust
async fn command_handler<F>(repo: AppState, id: Uuid, command: F) -> impl IntoResponse
where
    F: FnOnce(&mut Job) -> Result<(), JobError>,
{
    // 1. Load: find_by_id
    // 2. Mutate: call the command closure
    // 3. Save: persist job + events
    // 4. Respond: JobResponse JSON
}
```

**Why it matters:** 10 of the 13 endpoints use this pattern. The closure captures the specific command call (e.g., `|job| job.start(actor_id)`), while the surrounding logic (load, save, error mapping) is shared.

**Error mapping:**
- 404 — Job not found
- 422 — Domain error (invalid transition, terminal state, etc.)
- 500 — Database error

## `create_job` Handler (special case)

Does NOT use `command_handler` because it doesn't load an existing job. Instead:

1. Call `repo.next_job_number(company_id)` to generate the next number
2. Build `OpenJobParams` from request body
3. Call `Job::open(params)` factory
4. Call `repo.save(&mut job)`
5. Return 201 + JobResponse
