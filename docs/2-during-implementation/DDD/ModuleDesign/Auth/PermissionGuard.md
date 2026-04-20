# PermissionGuard Specification

**Module:** `Auth`
**Type:** Middleware / Axum Extractors
**Version:** 1.0.0
**ADRs:** [ADR-0034](../../../adr/0034-role-aware-workspace-interaction.md), [ADR-0035](../../../adr/0035-compliance-boundary-at-finalization.md)
**Depends On:** [AuthContext_VO](./AuthContext_VO.md)

---

## 1. Objective

PermissionGuard provides Axum route-level extractors that enforce the SFR-SRAZ permission matrix. Each guard:

1. Reads the `AuthContext` from request extensions (already constructed by auth middleware)
2. Checks if the user's `role` satisfies the required permission
3. Returns `403 Forbidden` if the check fails, with a machine-readable error body

Guards are composable: they wrap the `AuthContext` and can be used as Axum extractors alongside it.

---

## 2. Guard Types

### `RequireAdmin`

Enforces that the user has ADMIN-level access in the current workspace.

```rust
/// Extracts AuthContext and verifies the user has ADMIN or OWNER role.
/// Returns 403 if the user is a TECHNICIAN in a company workspace.
pub struct RequireAdmin(pub AuthContext);
```

**Passes when:**

- Personal workspace (`role == OWNER`) — the user owns this workspace
- Company workspace + `role == ADMIN`

**Rejects when:**

- Company workspace + `role == TECHNICIAN` → 403

### `RequireAuthenticated`

Allows any authenticated user regardless of role. This is the default — most endpoints that just need a valid user use this.

```rust
/// Extracts AuthContext without additional role checks.
/// Equivalent to using AuthContext directly as an extractor.
pub struct RequireAuthenticated(pub AuthContext);
```

**Passes when:** AuthContext exists (always, for any authenticated request)

### `RequireCompanyContext`

Enforces that the current workspace is a company workspace (not personal). Used for operations that require a company context (e.g., dispatching technicians).

```rust
/// Extracts AuthContext and verifies company_id is present.
/// Returns 403 if operating in a personal workspace.
pub struct RequireCompanyContext(pub AuthContext);
```

**Passes when:** `auth_context.company_id.is_some()`

**Rejects when:** Personal workspace (`company_id == None`) → 403

---

## 3. Error Response

All guard rejections return a consistent error shape:

```json
{
  "error": "forbidden",
  "message": "This action requires ADMIN access",
  "required_role": "ADMIN",
  "current_role": "TECHNICIAN",
  "workspace_id": "uuid-of-workspace"
}
```

HTTP status: `403 Forbidden`

> Note: Unauthenticated requests (no valid JWT) are handled by the auth middleware with `401 Unauthorized` before guards are ever invoked.

---

## 4. Axum Integration Pattern

Guards implement the `FromRequestParts` trait, extracting `AuthContext` from extensions and performing the role check:

```rust
#[async_trait]
impl<S> FromRequestParts<S> for RequireAdmin
where
    S: Send + Sync,
{
    type Rejection = ApiError;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        let auth = parts.extensions.get::<AuthContext>()
            .cloned()
            .ok_or(ApiError::Unauthorized)?;

        match auth.role {
            MembershipRole::Owner | MembershipRole::Admin => Ok(RequireAdmin(auth)),
            MembershipRole::Technician => Err(ApiError::Forbidden {
                required_role: "ADMIN",
                current_role: "TECHNICIAN",
            }),
        }
    }
}
```

**Handler usage:**

```rust
// Requires ADMIN — create job, manage clients, assign technicians
async fn create_job(
    RequireAdmin(auth): RequireAdmin,
    Json(body): Json<CreateJobRequest>,
) -> Result<Json<JobResponse>, ApiError> {
    // auth is the verified AuthContext
}

// Any authenticated user — view job detail, submit findings
async fn get_job(
    RequireAuthenticated(auth): RequireAuthenticated,
    Path(id): Path<Uuid>,
) -> Result<Json<JobResponse>, ApiError> {
    // ...
}
```

---

## 5. Route → Guard Mapping

### Job Engine Routes (`/api/v1/jobs`)

| Route | Method | Guard | SFR | Rationale |
|-------|--------|-------|-----|-----------|
| `/` | POST | `RequireAdmin` | SFR-SRAZ-01 | Job creation is an admin action |
| `/` | GET | `RequireAuthenticated` | SFR-SRAZ-03 | List jobs — role-based filtering in app code (see RoleVisibility) |
| `/{id}` | GET | `RequireAuthenticated` | SFR-SRAZ-03 | View single job — ownership check in handler |
| `/{id}/start` | PATCH | `RequireAuthenticated` | — | Lifecycle transition — assigned tech or admin |
| `/{id}/complete` | PATCH | `RequireAuthenticated` | — | Lifecycle transition |
| `/{id}/cancel` | PATCH | `RequireAdmin` | — | Cancellation is an admin decision |
| `/{id}/summary` | PATCH | `RequireAuthenticated` | — | Field update |
| `/{id}/site-notes` | PATCH | `RequireAuthenticated` | — | Field update |
| `/{id}/priority` | PATCH | `RequireAdmin` | — | Priority is an admin concern |
| `/{id}/client` | PATCH | `RequireAdmin` | — | Client attachment is an admin concern |
| `/{id}/ownership` | PATCH | `RequireAdmin` | SFR-SRAZ-02 | Job assignment/dispatch |
| `/{id}/obligation` | PATCH/DELETE | `RequireAdmin` | — | Compliance linkage |

### LL152 Workflow Routes (`/api/v1/jobs/{id}/ll152`)

| Route | Method | Guard | SFR | Rationale |
|-------|--------|-------|-----|-----------|
| `/` | GET | `RequireAuthenticated` | SFR-SRAZ-03 | View LL152 overview |
| `/details` | PUT | `RequireAuthenticated` | SFR-SRAZ-04 | Update inspection details — tech or admin |
| `/start-capture` | POST | `RequireAuthenticated` | SFR-SRAZ-04 | Begin data capture |
| `/submit-for-review` | POST | `RequireAuthenticated` | SFR-SRAZ-04 | Submit findings — both roles allowed (per ADR-0035) |
| `/recall` | POST | `RequireAuthenticated` | — | Recall own submission — tech or admin |
| `/open-review` | POST | `RequireAdmin` | SFR-SRAZ-05 | Review is an admin action |
| `/finalize` | POST | `RequireAdmin` | SFR-SRAZ-05 | Finalization boundary (ADR-0035) |
| `/return-for-corrections` | POST | `RequireAdmin` | SFR-SRAZ-05 | Return for corrections |
| `/findings/{finding_id}` | PUT | `RequireAuthenticated` | SFR-SRAZ-04 | Update finding — tech or admin |
| `/photos` | POST | `RequireAuthenticated` | SFR-SRAZ-04 | Attach photo to inspection |
| `/photos/{photo_id}` | DELETE | `RequireAuthenticated` | — | Remove photo |

### Tenant Routes (`/api/v1/tenant`)

| Route | Method | Guard | SFR | Rationale |
|-------|--------|-------|-----|-----------|
| `/clients` | POST | `RequireAdmin` | — | Client creation is admin |
| `/clients` | GET | `RequireAdmin` | — | Client list — TECHNICIANs access through jobs (ADR-0034) |
| `/clients/{id}` | GET | `RequireAdmin` | — | Client detail — same rationale |
| `/clients/{id}` | PATCH | `RequireAdmin` | — | Client update |
| `/clients/{id}/block` | POST | `RequireAdmin` | — | Client management |
| `/clients/{id}/unblock` | POST | `RequireAdmin` | — | Client management |
| `/clients/{id}/summary` | GET | `RequireAdmin` | — | Client summary |
| `/saved-buildings` | POST | `RequireAdmin` | — | Save building to workspace |
| `/saved-buildings` | GET | `RequireAdmin` | — | List saved buildings |
| `/saved-buildings/{id}` | DELETE | `RequireAdmin` | — | Remove saved building |

### CRM/Building Explorer Routes (`/api/v1/crm`)

| Route | Method | Guard | SFR | Rationale |
|-------|--------|-------|-----|-----------|
| `/buildings` | GET | `RequireAuthenticated` | — | Global building explorer — not workspace-scoped |
| `/buildings/search` | GET | `RequireAuthenticated` | — | Global search |
| `/buildings/bin/{bin}` | GET | `RequireAuthenticated` | — | Global lookup |
| `/buildings/bin/{bin}/profile` | GET | `RequireAuthenticated` | — | Global lookup |
| `/obligations` | GET | `RequireAdmin` | — | Workspace-scoped compliance data |
| `/obligations/summary` | GET | `RequireAdmin` | — | Workspace-scoped compliance data |
| `/import-runs` | GET | `RequireAdmin` | — | Admin data management |
| `/import-runs/summary` | GET | `RequireAdmin` | — | Admin data management |
| `/anomalies` | GET | `RequireAdmin` | — | Admin data management |
| `/anomalies/severity-counts` | GET | `RequireAdmin` | — | Admin data management |

---

## 6. Edge Cases

### ADMIN Accessing TECHNICIAN Endpoints

ADMIN is a superset of TECHNICIAN for alpha (3C.1 Q4 resolution). All `RequireAuthenticated` endpoints are accessible to both roles. No endpoint is TECHNICIAN-only.

### Personal Workspace

In a personal workspace, `role == OWNER`. OWNER passes all guards including `RequireAdmin`. Personal workspace users are never restricted by role guards — they own everything in their workspace.

### Portfolio Query

The portfolio endpoint (cross-workspace aggregate) does NOT use a workspace-level guard. Instead, it uses `RequireAuthenticated` and builds per-workspace UNION arms with appropriate scoping (see [RoleVisibility](./RoleVisibility.md)).

### Unauthenticated Requests

Handled by auth middleware before guards execute → `401 Unauthorized`. Guards never see unauthenticated requests.

### Health Check

`/health` is outside the auth middleware layer entirely — no guard needed.

---

## 7. Implementation Notes

- Guards are lightweight — they only read `AuthContext` from extensions and check the role enum. No DB queries.
- The auth middleware is responsible for constructing `AuthContext` (JWT validation, workspace resolution, role lookup). Guards consume the finished result.
- Guards do NOT enforce resource-level ownership (e.g., "is this MY job?"). That's a handler concern using `auth.user_id` and `assigned_to`.
- Future: If new roles are added (e.g., `MANAGER`), add new guard variants or extend the role check logic. The guard pattern scales cleanly.

---

## 8. References

- [AuthContext_VO](./AuthContext_VO.md) — The value object guards consume
- [RoleVisibility](./RoleVisibility.md) — Application-level query scoping that complements guards
- [ADR-0034](../../../adr/0034-role-aware-workspace-interaction.md) — Why role visibility is in app code, not RLS
- [ADR-0035](../../../adr/0035-compliance-boundary-at-finalization.md) — Why ADMIN can submit findings
- [PHASE_3C_Authorization.md](../../../roadmap/PHASE_3C_Authorization.md) — SFR-SRAZ permission matrix
