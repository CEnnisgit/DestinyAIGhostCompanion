# RoleVisibility Specification

**Module:** `Auth`
**Type:** Application-Level Query Scoping
**Version:** 1.0.0
**ADRs:** [ADR-0034](../../../adr/0034-role-aware-workspace-interaction.md), [ADR-0033](../../../adr/0033-stateless-workspace-context.md)
**Depends On:** [AuthContext_VO](./AuthContext_VO.md), [PermissionGuard](./PermissionGuard.md)

---

## 1. Objective

RoleVisibility defines **what data each role sees** within their authorized workspaces. This is the application-level filtering that ADR-0034 explicitly places in app code rather than in RLS policies.

**The two layers:**

| Layer | What it does | Where it lives |
|-------|-------------|----------------|
| RLS (workspace isolation) | Prevents cross-workspace data access | PostgreSQL policies |
| RoleVisibility (this spec) | Filters data within an authorized workspace by role | Application code (Rust) |

RLS is the safety net. RoleVisibility is the business rule.

---

## 2. Scoping Matrix

This matrix defines what each role can see when querying workspace-scoped data.

### Jobs

| Workspace Type | Role | Scoping Rule |
|---------------|------|-------------|
| Personal | OWNER | All jobs: `WHERE workspace_id = $ws_id` |
| Company | ADMIN | All jobs: `WHERE workspace_id = $ws_id` |
| Company | TECHNICIAN | Assigned only: `WHERE workspace_id = $ws_id AND assigned_to = $user_id` |

### Clients

| Workspace Type | Role | Access |
|---------------|------|--------|
| Personal | OWNER | Full list: `WHERE workspace_id = $ws_id` |
| Company | ADMIN | Full list: `WHERE workspace_id = $ws_id` |
| Company | TECHNICIAN | **No direct access.** Client data visible only through job detail view. Route guarded by `RequireAdmin` (see [PermissionGuard](./PermissionGuard.md)). |

### Saved Buildings

| Workspace Type | Role | Access |
|---------------|------|--------|
| Personal | OWNER | Full list: `WHERE workspace_id = $ws_id` |
| Company | ADMIN | Full list: `WHERE workspace_id = $ws_id` |
| Company | TECHNICIAN | **No direct access.** Route guarded by `RequireAdmin`. |

### Building Explorer (Global PAD Data)

| Workspace Type | Role | Access |
|---------------|------|--------|
| Any | Any | **Full access.** Not workspace-scoped. Global municipal data browsable by all authenticated users. |

---

## 3. Portfolio Query Specification

The portfolio query aggregates data across all workspaces a user has access to. It is the implementation mechanism for the TECHNICIAN "My Jobs" unified view (ADR-0034 §1).

### 3.1 Input

The derived access query ([ADR-0032](../../../adr/0032-derived-workspace-access.md)) returns the user's workspace list:

```sql
SELECT workspace_id, role FROM derived_workspace_access
WHERE user_id = $user_id;
```

Result example:

| workspace_id | role |
|-------------|------|
| ws-personal | OWNER |
| ws-company-a | ADMIN |
| ws-company-b | TECHNICIAN |

### 3.2 UNION Construction

The portfolio query builder constructs a single `UNION ALL` query with per-workspace arms. Each arm applies the appropriate role-based scoping:

```sql
-- Arm 1: Personal workspace (OWNER) — all jobs
SELECT j.*, 'personal' as source_label
FROM jobs j
WHERE j.workspace_id = $ws_personal

UNION ALL

-- Arm 2: Company A workspace (ADMIN) — all jobs
SELECT j.*, 'Company A' as source_label
FROM jobs j
WHERE j.workspace_id = $ws_company_a

UNION ALL

-- Arm 3: Company B workspace (TECHNICIAN) — assigned only
SELECT j.*, 'Company B' as source_label
FROM jobs j
WHERE j.workspace_id = $ws_company_b
  AND j.assigned_to = $user_id

ORDER BY created_at DESC
LIMIT $page_size OFFSET $offset;
```

### 3.3 Construction Rules

1. **OWNER/ADMIN arms:** No `assigned_to` filter — see all jobs in workspace
2. **TECHNICIAN arms:** Always include `AND assigned_to = $user_id`
3. **Source labeling:** Each arm includes a `source_label` column so the frontend can organize by origin (e.g., tabs, group headings)
4. **Ordering:** The final `ORDER BY` applies across the entire UNION result
5. **Pagination:** Standard offset-based pagination over the UNION result

### 3.4 Edge Cases

**User with zero company memberships (solo plumber):**
- Derived access returns 1 row: personal workspace, OWNER
- UNION collapses to a single SELECT — no performance concern
- Per ADR-0033 §Alpha User Flows (User B scenario)

**User with zero assigned jobs as TECHNICIAN:**
- TECHNICIAN arm returns 0 rows — UNION still works correctly
- Other arms (personal, other companies) may return data

**User who is ADMIN at one company and TECHNICIAN at another:**
- Separate arms with separate scoping — ADMIN arm sees all, TECHNICIAN arm sees assigned only
- Per ADR-0034 §Portfolio Query Tests

---

## 4. Repository Method Changes

### Existing Methods Requiring Role-Aware Variants

#### `list_jobs`

**Current:** Returns all jobs for the workspace.

**Change:** Accept `AuthContext` and apply role-based filtering:

```rust
pub async fn list_jobs(
    pool: &PgPool,
    auth: &AuthContext,
    pagination: &Pagination,
) -> Result<Vec<Job>, Error> {
    match auth.role {
        MembershipRole::Owner | MembershipRole::Admin => {
            // All jobs in workspace (RLS handles workspace isolation)
            sqlx::query_as!(Job, "SELECT * FROM jobs ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                pagination.limit, pagination.offset)
                .fetch_all(pool).await
        }
        MembershipRole::Technician => {
            // Only assigned jobs
            sqlx::query_as!(Job,
                "SELECT * FROM jobs WHERE assigned_to = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                auth.user_id, pagination.limit, pagination.offset)
                .fetch_all(pool).await
        }
    }
}
```

#### `get_job` (Single Job Access)

**Current:** Returns job by ID.

**Change:** After fetching, verify visibility:

```rust
pub async fn get_job(pool: &PgPool, auth: &AuthContext, job_id: Uuid) -> Result<Job, Error> {
    let job = sqlx::query_as!(Job, "SELECT * FROM jobs WHERE id = $1", job_id)
        .fetch_optional(pool).await?
        .ok_or(Error::NotFound)?;

    // RLS already ensures workspace isolation.
    // For TECHNICIAN, additionally check assignment.
    if auth.role == MembershipRole::Technician && job.assigned_to != Some(auth.user_id) {
        return Err(Error::Forbidden);
    }

    Ok(job)
}
```

### New Methods

#### `list_jobs_portfolio`

**Purpose:** Cross-workspace job aggregation using the UNION ALL pattern.

```rust
pub async fn list_jobs_portfolio(
    pool: &PgPool,
    user_id: Uuid,
    workspaces: &[(Uuid, MembershipRole)], // from derived access query
    pagination: &Pagination,
) -> Result<Vec<PortfolioJob>, Error> {
    // Build dynamic UNION ALL query per §3.2
    // Each arm sets app.workspace_id and applies role-appropriate filtering
}
```

**Note:** This method must manage PostgreSQL session variables (`app.workspace_id`) per arm, or use a different isolation strategy (subqueries with explicit `workspace_id` predicates instead of relying on RLS for the UNION). The implementation should evaluate both approaches for correctness — RLS session variables are connection-scoped and may not compose well with UNION across workspaces. The recommended approach is explicit `WHERE workspace_id = $x` predicates in each arm, bypassing RLS for the portfolio query (since authorization is already handled by the derived access query).

### Methods NOT Changing

- **Client and Saved Building list methods** — These endpoints are already guarded by `RequireAdmin` at the route level. No role-based filtering needed in the repository layer; the guard prevents TECHNICIAN access entirely.
- **Building Explorer methods** — These are global queries, not workspace-scoped. No role check needed.

---

## 5. RLS vs Application Layer Boundary

This is the definitive boundary statement per ADR-0034 §4.

### RLS Handles

| Concern | Policy Pattern |
|---------|---------------|
| Workspace isolation | `USING (workspace_id = current_setting('app.workspace_id')::uuid)` |

**Applied to:** `jobs`, `clients`, `saved_buildings`, and all future tenant-scoped tables.

### Application Code Handles

| Concern | Implementation |
|---------|---------------|
| TECHNICIAN job filtering | `WHERE assigned_to = $user_id` in repository |
| Client/building access for TECHNICIANs | Route-level `RequireAdmin` guard |
| Portfolio cross-workspace aggregation | Dynamic UNION ALL with per-role scoping |
| Resource-level ownership checks | Handler-level validation (e.g., "is this my submission to recall?") |

### What Neither Layer Handles (Deferred)

| Concern | Why Deferred |
|---------|-------------|
| Field-level visibility (hiding salary, contact info) | Not needed for alpha |
| Time-based access expiry | No requirement |
| Delegation / impersonation | Not needed for alpha |

---

## 6. Required Test Matrix

Per ADR-0034 §Required Test Coverage, the following test scenarios **must** have integration test coverage before 3C.1 is considered implementation-complete.

### RLS Integration Tests

| # | Scenario | Expected Result |
|---|----------|----------------|
| R1 | User A queries with `app.workspace_id = ws_B` (workspace they belong to) | Returns ws_B data |
| R2 | User A queries with `app.workspace_id = ws_C` (workspace they do NOT belong to) | Returns 0 rows |
| R3 | RLS applies to `jobs` table | Verified |
| R4 | RLS applies to `clients` table | Verified |
| R5 | RLS applies to `saved_buildings` table | Verified |

### Technician Scoping Tests

| # | Scenario | Expected Result |
|---|----------|----------------|
| T1 | TECHNICIAN calls `GET /jobs` — has 2 assigned jobs, 5 total in workspace | Returns 2 jobs |
| T2 | TECHNICIAN calls `GET /jobs` — has 0 assigned jobs | Returns empty list |
| T3 | TECHNICIAN calls `GET /jobs/{id}` for an assigned job | Returns job |
| T4 | TECHNICIAN calls `GET /jobs/{id}` for an unassigned job in same workspace | Returns 403 |
| T5 | TECHNICIAN calls `GET /clients` | Returns 403 (route guard) |
| T6 | TECHNICIAN calls `GET /saved-buildings` | Returns 403 (route guard) |

### Admin Scoping Tests

| # | Scenario | Expected Result |
|---|----------|----------------|
| A1 | ADMIN calls `GET /jobs` | Returns all jobs in workspace |
| A2 | ADMIN calls `POST /jobs` | Creates job successfully |
| A3 | ADMIN calls `GET /clients` | Returns all clients in workspace |
| A4 | ADMIN in personal workspace calls `GET /jobs` | Returns all personal jobs |
| A5 | ADMIN calls `POST /ll152/submit-for-review` | Succeeds (ADMIN superset) |

### Portfolio Query Tests

| # | Scenario | Expected Result |
|---|----------|----------------|
| P1 | User is ADMIN at Company A, TECHNICIAN at Company B | UNION returns all Company A jobs + only assigned Company B jobs |
| P2 | User has personal workspace only (no company memberships) | Returns personal jobs only (single SELECT) |
| P3 | User is ADMIN at 2 companies + personal workspace | Returns all jobs from all 3 workspaces |
| P4 | TECHNICIAN arm returns 0 assigned jobs | Other arms still return their jobs correctly |

### Permission Guard Tests

| # | Scenario | Expected Result |
|---|----------|----------------|
| G1 | TECHNICIAN calls `POST /jobs` (RequireAdmin) | Returns 403 |
| G2 | ADMIN calls `POST /jobs` (RequireAdmin) | Succeeds |
| G3 | OWNER (personal ws) calls `POST /jobs` (RequireAdmin) | Succeeds |
| G4 | Unauthenticated call to any guarded route | Returns 401 |
| G5 | TECHNICIAN calls `GET /buildings/search` (RequireAuthenticated) | Succeeds |

---

## 7. References

- [PermissionGuard](./PermissionGuard.md) — Route-level guards that complement visibility rules
- [AuthContext_VO](./AuthContext_VO.md) — The value object carrying role and workspace context
- [ADR-0034](../../../adr/0034-role-aware-workspace-interaction.md) — Architectural decision placing role visibility in app code
- [ADR-0033](../../../adr/0033-stateless-workspace-context.md) — Stateless workspace context and portfolio UNION pattern
- [ADR-0032](../../../adr/0032-derived-workspace-access.md) — Derived workspace access query
- [Job_Aggregate.md](../Jobs/Engine/Job_Aggregate.md) — `assigned_to` field definition
- [PHASE_3C_Authorization.md](../../../roadmap/PHASE_3C_Authorization.md) — SFR-SRAZ permission matrix
