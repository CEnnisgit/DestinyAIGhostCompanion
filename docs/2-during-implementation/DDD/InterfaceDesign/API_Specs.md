# Interface Design: API Specifications

> **Source of Truth:** `crates/pcd-api/src/routes/` (Axum route handlers)
> **Scope:** [Pilot Core (LL152)](file:///c:/github/pcd/docs/PILOT_SCOPE_CONTEXT.md)
> **Naming Convention:** [ADR-0019](../../adr/0019-camelcase-api-serialization.md) — all JSON responses use camelCase keys

## Overview

REST API specifications for the backend, hosted via Axum (Rust).

## Implemented Endpoints

### CRM Routes (`/api`)

**Source:** `crates/pcd-api/src/routes/crm.rs`

| Method | Path | Handler | Description |
| :--- | :--- | :--- | :--- |
| GET | `/buildings` | `search_buildings` | Paginated search with filters (BIN, address, borough, padVerified, introducedIn, hasObligations, identity timeline) |
| GET | `/buildings/:bin` | `get_building_profile` | Full building profile: addresses, obligations, timeline, lineage, isSuperseded |
| GET | `/obligations` | `list_obligations` | Filtered obligation list |
| GET | `/obligations/summary` | `get_obligation_summary` | Aggregate stats (by status, program) |
| GET | `/anomalies` | `list_anomalies` | Filtered anomaly list with totalCount |
| GET | `/anomalies/severity-counts` | `get_severity_counts` | Anomaly counts by severity |
| GET | `/import-runs` | `list_import_runs` | Paginated import runs with totalCount |
| GET | `/import-runs/summary` | `get_import_runs_summary` | Aggregate stats (total rows parsed/inserted/quarantined) |

### Jobs Routes (`/api/jobs`)

**Source:** `crates/pcd-api/src/routes/jobs.rs`

| Method | Path | Handler | Description |
| :--- | :--- | :--- | :--- |
| POST | `/` | `create_job` | Open a new job (calls `Job::open()`) |
| GET | `/` | `list_jobs` | List all jobs (company-scoped, newest first) |
| GET | `/:id` | `get_job` | Get a job by ID |
| PATCH | `/:id/start` | `start_job` | Transition OPEN → IN_PROGRESS |
| PATCH | `/:id/complete` | `complete_job` | Transition IN_PROGRESS → COMPLETED |
| PATCH | `/:id/cancel` | `cancel_job` | Transition to CANCELED |
| PATCH | `/:id/summary` | `update_summary` | Update job summary text |
| PATCH | `/:id/site-notes` | `update_site_notes` | Update site notes |
| PATCH | `/:id/priority` | `update_priority` | Update priority |
| PATCH | `/:id/client` | `attach_client` | Attach client reference |
| PATCH | `/:id/ownership` | `assign_ownership` | Assign responsible user |
| PATCH | `/:id/obligation` | `link_obligation` | Link compliance obligation |
| DELETE | `/:id/obligation` | `unlink_obligation` | Unlink compliance obligation |

### Tenant Routes (`/api`)

**Source:** `crates/pcd-api/src/routes/tenant.rs`

| Method | Path | Handler | Description |
| :--- | :--- | :--- | :--- |
| POST | `/clients` | `create_client` | Create or deduplicate client (200/201) |
| GET | `/clients` | `list_clients` | List all clients (company-scoped) |
| GET | `/clients/:id` | `get_client` | Get single client by ID |
| PATCH | `/clients/:id` | `update_client` | Update name/phone/address |
| POST | `/clients/:id/block` | `block_client` | Block with reason |
| POST | `/clients/:id/unblock` | `unblock_client` | Remove block |
| GET | `/clients/:id/summary` | `client_summary` | Derived views (job count, buildings, last job) |
| POST | `/saved-buildings` | `save_building` | Bookmark a building |
| GET | `/saved-buildings` | `list_saved_buildings` | List bookmarks (with BIN join) |
| DELETE | `/saved-buildings/:id` | `remove_saved_building` | Remove bookmark |

## Response Format

All responses are JSON. Field names use **camelCase** per [ADR-0019](../../adr/0019-camelcase-api-serialization.md).

### Success Response

```json
{
  "bin": "1234567",
  "houseNumber": "123",
  "createdFromSource": "PAD Bootstrap",
  "hasObligations": true
}
```

### Paginated Response

Endpoints with pagination return a `totalCount` alongside the data array:

```json
{
  "data": [...],
  "totalCount": 42
}
```

### Error Response

Axum returns standard HTTP status codes with a JSON error body:

```json
{
  "error": "Job not found"
}
```

## Standard Patterns

### Authentication

Not yet implemented. All endpoints are currently unauthenticated. Auth pattern is documented in [SecurityStrategy.md](../SystemArchitecture/SecurityStrategy.md) for future implementation.

### CORS

Configured to allow `http://localhost:3000` (dev dashboard) during development.
