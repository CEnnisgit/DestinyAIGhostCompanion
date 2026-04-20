# ADR-0033: Stateless Workspace Context via Request Header

**Status:** Accepted  
**Date:** 2026-03-30  
**Deciders:** Marcus, AI Pair Programming  
**Supersedes:** None  
**Related:** [ADR-0030](./0030-workspace-isolation-abstraction.md) (workspace isolation), [ADR-0032](./0032-derived-workspace-access.md) (derived access)

## Context

[ADR-0030](./0030-workspace-isolation-abstraction.md) defines the workspace as the universal isolation boundary. [ADR-0032](./0032-derived-workspace-access.md) defines how workspace access is derived from domain relationships. Neither specifies **how the client communicates which workspace it's operating in** on a per-request basis.

This decision was driven by analyzing the two alpha users:

**User A** owns an LLC (Company A, ADMIN). He is also a QI at two other companies (Company B and C, TECHNICIAN). He has 4 workspaces: personal + 3 company workspaces. He creates jobs in his LLC's workspace, receives LL152 assignments in the other two, and views everything in a unified portfolio.

**User B** does not own a business. He operates entirely from his personal workspace. He creates all his jobs there, manages his own clients there, and receives hand-off jobs from User A via connections.

Key observations:
1. User B proves that **the personal workspace must be fully functional** — it's not a read-only dashboard, it's where he does all his work.
2. User A switches between company workspaces depending on what work he's doing, but views all his work in a unified portfolio.
3. Neither user should need to understand "workspaces" as a concept to use the app productively.

## Decision

### 1. Workspace Context via `X-Workspace-Id` Header (Stateless)

The client sends an `X-Workspace-Id` header on every API request that needs workspace scoping:

```
GET /api/jobs
Authorization: Bearer <jwt>              ← WHO you are (identity)
X-Workspace-Id: <workspace-uuid>         ← WHERE you're operating (context)
```

The JWT carries identity (`user_id`). The header carries context (`workspace_id`). Both are stateless.

**Why stateless (not server-side session state):**
- Workspace context is a request concern, not a session concern
- No stale state across browser tabs
- Easy to test — change the header, get different results
- No extra DB reads to look up "current workspace" on every request
- The frontend already manages UI state; workspace selection is just another piece of that

### 2. Default to Personal Workspace When No Header Sent

If the `X-Workspace-Id` header is omitted, the server defaults to the user's personal workspace. This means:

- **User B never sends a workspace header.** His personal workspace is used automatically.
- **User A omitting the header** gets his personal workspace, not an error.
- Free-tier users who don't know about workspaces just work — their personal workspace handles everything.

### 3. Personal Workspace is Fully Functional

The personal workspace supports creating and managing all operational data: jobs, clients, building bookmarks, credentials. It is NOT a read-only aggregation view.

| Capability | Personal Workspace | Company Workspace |
|------------|:------------------:|:-----------------:|
| Create jobs | ✅ | ✅ |
| Manage clients | ✅ | ✅ |
| Track credentials | ✅ | ✅ |
| Manage team members | ❌ (Teams — Beta) | ✅ (ADMIN/TECHNICIAN roles) |
| Company dispatch | ❌ | ✅ |
| Full worker tracking | ❌ | ✅ |

### 4. Portfolio is a Cross-Workspace UNION Query

The portfolio/dashboard view is NOT scoped to a single workspace. It queries all workspaces the user has access to:

```
Portfolio = UNION(
    personal workspace jobs,
    Company A jobs (where user is member),
    Company B jobs (where user is member),
    ...
)
```

This means the user's landing page shows their complete picture without switching. Single-workspace scoping only applies when **creating or managing** data within a specific context.

**API pattern for portfolio:**

```
GET /api/me/jobs            ← All jobs across all workspaces (no workspace header)
GET /api/jobs                ← Jobs in the active workspace (requires X-Workspace-Id)
```

### 5. Middleware Validates Access

On every request with `X-Workspace-Id`, the middleware:

1. Extracts `user_id` from JWT
2. Extracts `workspace_id` from header (or defaults to personal workspace)
3. Runs the derived access query ([ADR-0032](./0032-derived-workspace-access.md)) to confirm user has access
4. Sets `app.workspace_id` as a PostgreSQL session variable for RLS
5. Proceeds with the request (or returns 403 if access denied)

## Consequences

### Positive

- Zero shared server-side state — scales trivially
- Free-tier and solo users never encounter workspace complexity
- Portfolio view gives a complete picture without workspace switching
- Clean separation: JWT = identity, header = context
- Aligns with person-first model (ADR-0027) — personal workspace works out of the box

### Negative

- Frontend must track "current workspace" in local state and send the header
- Portfolio UNION queries are more complex than single-workspace queries (acceptable at alpha scale)
- If frontend has a bug and omits the header, user silently gets personal workspace data (safe default, but could confuse)

### Neutral

- The `X-Workspace-Id` header pattern is the same regardless of workspace type (personal, company, team) — no special cases per type

## Alpha User Flows

### User A (LLC owner, QI at 2 companies)

```
Opens app → Portfolio (UNION of all 4 workspaces)
Creates a job for his LLC → switches to Company A workspace → X-Workspace-Id: company-a-ws
Views LL152 from Danny → switches to Company B workspace → X-Workspace-Id: company-b-ws
Checks his credentials → personal workspace → X-Workspace-Id: personal-ws (or omit header)
```

### User B (solo plumber, no company)

```
Opens app → Portfolio (just personal workspace — only one)
Creates a job → personal workspace → no header needed (default)
Receives hand-off from User A → job lands in personal workspace
Everything just works — never sees a workspace switcher
```

## References

- [ADR-0030](./0030-workspace-isolation-abstraction.md) — Workspace isolation abstraction
- [ADR-0031](./0031-person-first-feature-gating.md) — Person-first feature gating
- [ADR-0032](./0032-derived-workspace-access.md) — Derived workspace access
- [REGISTRATION_AND_TENANCY.md](../vision/REGISTRATION_AND_TENANCY.md) — Registration and tenancy vision
- [TEAMS.md](../vision/deferred/TEAMS.md) — Deferred teams concept
