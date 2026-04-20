# AuthContext Value Object Specification

**Module:** `Auth`
**Type:** Value Object
**Source of Truth:** `pcd-domain/src/auth/mod.rs`
**Version:** 1.0.0
**ADRs:** [ADR-0033](../../../adr/0033-stateless-workspace-context.md)

---

## 1. Objective

`AuthContext` is the value object that carries the authenticated user's identity and workspace context through every request handler. It answers:

- **Who** is making this request? (`user_id`)
- **Where** are they operating? (`workspace_id`)
- **In what capacity?** (`role`, `company_id`)

It is the **only** way downstream handlers should learn the identity and context of the caller. No handler should parse JWTs, read headers, or query the DB for this information — it's all in the `AuthContext`.

---

## 2. Definition

```rust
/// The authenticated identity and workspace context for the current request.
/// Constructed exclusively by auth middleware — never by application code.
#[derive(Debug, Clone)]
pub struct AuthContext {
    /// The authenticated user's ID (from JWT `sub` claim)
    pub user_id: Uuid,

    /// The workspace this request operates in (from X-Workspace-Id header or default)
    pub workspace_id: Uuid,

    /// The company associated with this workspace, if it's a company workspace.
    /// `None` when operating in a personal workspace.
    pub company_id: Option<Uuid>,

    /// The user's role in the current workspace context.
    /// `OWNER` for personal workspace, membership role for company workspaces.
    pub role: MembershipRole,
}
```

---

## 3. Field Semantics

### `user_id: Uuid`

- Extracted from the JWT `sub` claim after token validation
- Always present — there is no anonymous `AuthContext`
- References `users.id` in the database
- Does NOT change based on workspace context — identity is constant

### `workspace_id: Uuid`

- Resolved from the `X-Workspace-Id` request header
- Defaults to `users.personal_workspace_id` when the header is absent (ADR-0033)
- Validated against the derived access query — the middleware confirms the user has access
- Used to set `app.workspace_id` PostgreSQL session variable for RLS
- References `workspaces.id` in the database

### `company_id: Option<Uuid>`

- `Some(uuid)` when the workspace belongs to a company
- `None` when operating in a personal workspace
- Handlers that need company context (e.g., dispatching) should check this field and return an appropriate error if `None`
- References `companies.id` in the database

### `role: MembershipRole`

- `OWNER` when operating in a personal workspace (the user owns their personal space)
- The membership role (`ADMIN`, `TECHNICIAN`) when operating in a company workspace
- Used by authorization checks (Phase 3C) to determine what the user can do

---

## 4. Construction Rules

### 4.1 Only Middleware Constructs AuthContext

`AuthContext` is **never** constructed by application code — only by the auth middleware. This guarantees:

- The JWT has been validated
- The workspace access has been verified
- The RLS session variable has been set
- All security checks have passed

### 4.2 Construction Fails Fast

If any validation step fails, no `AuthContext` is created — the middleware returns an error response directly:

| Failure | Response |
|---------|----------|
| No JWT / invalid JWT | 401 |
| User deactivated | 401 |
| Workspace not in access list | 403 |

### 4.3 Always Non-Empty After Middleware

If a handler has an `AuthContext`, all fields are populated and valid. There is no "partial" or "anonymous" `AuthContext`.

---

## 5. Axum Integration

`AuthContext` is injected as an Axum extension via the middleware layer:

```rust
// In middleware — after all validations pass:
request.extensions_mut().insert(auth_context);

// In handler — extract as a typed extension:
async fn list_jobs(
    Extension(auth): Extension<AuthContext>,
    State(pool): State<PgPool>,
) -> Result<Json<Vec<Job>>, AppError> {
    // auth.user_id is guaranteed valid
    // auth.workspace_id is guaranteed accessible
    // app.workspace_id is already set for RLS
    let jobs = sqlx::query_as!(Job, "SELECT * FROM jobs")
        .fetch_all(&pool)
        .await?;
    Ok(Json(jobs))
}
```

---

## 6. MembershipRole Enum

```rust
/// The user's role in a workspace context.
#[derive(Debug, Clone, Copy, PartialEq, Eq, sqlx::Type)]
#[sqlx(type_name = "membership_role", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum MembershipRole {
    /// Personal workspace owner — the user owns this space
    Owner,
    /// Company administrator — full access to company workspace
    Admin,
    /// Company technician — limited to assigned work
    Technician,
}
```

> [!NOTE]
> `OWNER` is not a real DB-stored role — it's a synthetic role assigned by the middleware when the workspace is personal. The `company_memberships.role` column only contains `ADMIN` or `TECHNICIAN`.

---

## 7. Relationship to RLS

The `workspace_id` field in `AuthContext` is the same value that gets set as `app.workspace_id` in PostgreSQL. This means:

```
AuthContext.workspace_id == current_setting('app.workspace_id')::uuid
```

Every RLS policy on tenant-scoped tables filters by this value. The `AuthContext` and the RLS enforcement are always in sync because the middleware sets both from the same source.

---

## 8. What AuthContext Does NOT Contain

| Omitted Field | Why |
|---------------|-----|
| `email` | Not needed for request processing — use `user_id` to look up if needed |
| `name` | Not needed for request processing |
| `is_active` | Already verified by middleware — if AuthContext exists, user is active |
| `password_hash` | Never leaves the auth boundary |
| `permissions` | Phase 3C — authorization is a separate concern |
| `entitlements` | Phase 3N — feature gating is a separate concern |
