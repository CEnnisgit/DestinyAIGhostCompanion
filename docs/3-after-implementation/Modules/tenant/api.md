# Tenant API — Code Walkthrough

> **Crate:** `pcd-api/src/routes/tenant.rs`
> **Router:** `tenant::router()` mounted at `/api/` prefix

## Route Table

### Client Routes

| Method | Path | Handler | Description |
|---|---|---|---|
| `POST` | `/api/clients` | `create_client` | Create or deduplicate client (200/201) |
| `GET` | `/api/clients` | `list_clients` | List all clients for dev company |
| `GET` | `/api/clients/:id` | `get_client` | Get single client by ID |
| `PATCH` | `/api/clients/:id` | `update_client` | Update name/phone/address |
| `POST` | `/api/clients/:id/block` | `block_client` | Block with reason |
| `POST` | `/api/clients/:id/unblock` | `unblock_client` | Remove block |
| `GET` | `/api/clients/:id/summary` | `client_summary` | Derived views (job count, buildings, last job) |

### Saved Building Routes

| Method | Path | Handler | Description |
|---|---|---|---|
| `POST` | `/api/saved-buildings` | `save_building` | Bookmark a building |
| `GET` | `/api/saved-buildings` | `list_saved_buildings` | List bookmarks (with BIN join) |
| `DELETE` | `/api/saved-buildings/:id` | `remove_saved_building` | Remove bookmark |

## Shared State

```rust
pub struct TenantState {
    pub clients: SqlxClientRepository,
    pub saved_buildings: SqlxSavedBuildingRepository,
    pub pool: PgPool,  // For cross-aggregate read-side queries
}
```

The `pool` field enables the `/summary` endpoint to run direct SQL for derived views without going through aggregate repositories.

## Key Behaviors

### Idempotent Client Creation (`POST /api/clients`)

Returns `200 OK` if a client with matching `(company_id, name, phone)` already exists. Returns `201 Created` for genuinely new clients. This makes the job creation flow safe to call repeatedly.

### Client Summary (`GET /api/clients/:id/summary`)

Read-side projection implemented via direct SQL (not aggregate methods):

```json
{
  "job_count": 3,
  "buildings": [
    { "building_id": "uuid", "address": "123 Main St" }
  ],
  "last_job_at": "2026-03-27T12:00:00Z"
}
```

Uses `to_char()` for timestamp formatting to avoid adding `chrono` dependency to `pcd-api`.

### Saved Buildings List with BIN

`list_saved_buildings` uses `list_by_company_with_bin()` which JOINs to the buildings table to include the BIN in the response without a separate lookup.

## TODO (Phase 3)

- Replace hardcoded `company_id` in `list_clients` and `list_saved_buildings` with auth context
- Add pagination to client and saved building list endpoints
