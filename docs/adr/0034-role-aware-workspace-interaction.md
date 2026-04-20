# ADR-0034: Role-Aware Workspace Interaction Model

**Status:** Accepted  
**Date:** 2026-03-31  
**Deciders:** Marcus, AI Pair Programming  
**Supersedes:** None  
**Related:** [ADR-0030](./0030-workspace-isolation-abstraction.md) (workspace isolation), [ADR-0033](./0033-stateless-workspace-context.md) (stateless workspace context)

## Context

[ADR-0033](./0033-stateless-workspace-context.md) defines HOW workspace context is communicated (stateless `X-Workspace-Id` header). It does not define WHO uses workspace switching or HOW different roles interact with workspace scoping. Two questions surfaced during 3C.1 authorization design:

1. **Do TECHNICIANs need workspace switching?** A TECHNICIAN doesn't manage company data — they receive assigned jobs, do fieldwork, and submit findings. Forcing them to "switch to Company B's workspace" to see their Company B jobs creates unnecessary cognitive overhead.

2. **Where does role-based visibility live?** RLS (Row-Level Security) can enforce both workspace isolation AND role-based visibility, or it can enforce workspace isolation only with role filtering in application code. These are meaningfully different architectural choices.

### The Scenarios That Drove This Decision

**User A (Marcus's father)** — ADMIN of his LLC, TECHNICIAN at two external companies:
- When he opens his phone, he wants to see ALL his jobs: personal, his LLC, and jobs assigned to him from the other two companies
- He doesn't think "let me switch to Danny's workspace" — he thinks "let me see my jobs"
- He DOES explicitly switch workspaces when he needs to create a job under his LLC or manage LLC clients

**User B's employees** — TECHNICIANs at User B's company:
- They don't create jobs, don't manage clients, don't oversee other workers
- Their entire interaction with company data is: "here are the jobs assigned to me"
- Forcing them to switch workspaces to see their assignments is unnecessary friction

## Decision

### 1. Only ADMINs Use Workspace Switching

**TECHNICIANs see a unified "My Jobs" view.** This is the portfolio query — it aggregates:
- Their personal jobs (from personal workspace, if any)
- All jobs assigned to them across every company they belong to

The frontend organizes by source (labels, tabs, or sections so they can tell which company a job came from), but the TECHNICIAN never sees a workspace switcher. When they tap a specific job from Company B, the frontend silently sets `X-Workspace-Id` for subsequent API calls related to that job.

**ADMINs use workspace switching because they MANAGE within a company context.** Creating jobs, managing clients, assigning technicians, reviewing findings — these are company-scoped operations that require an explicit workspace context.

```
TECHNICIAN experience:
  Opens app → "My Jobs" (unified) → Taps job → works on it
  (X-Workspace-Id set silently by frontend)

ADMIN experience:
  Opens app → Portfolio (unified, all contexts) → Switches to Company A workspace
  → Creates job, assigns tech, manages clients
  (X-Workspace-Id set explicitly via workspace switcher)
```

### 2. RLS Enforces Workspace Isolation ONLY

RLS policies enforce a single, simple rule: **you can only access data in the workspace the middleware set for this request.**

```sql
CREATE POLICY workspace_isolation ON jobs
  USING (workspace_id = current_setting('app.workspace_id')::uuid);
```

Role-based visibility (e.g., "TECHNICIANs only see their assigned jobs") is enforced in **application code**, not in RLS policies.

### 3. Why These Decisions Are Paired

They reinforce each other:

| Concern | What Could Go Wrong | Why It's Mitigated |
|---------|--------------------|--------------------|
| "Simple RLS lets a TECHNICIAN see all jobs in a company workspace" | True — if they set `X-Workspace-Id` directly | Backend technician-facing endpoints must apply `assigned_to` filtering. RLS blocks cross-workspace leaks; app code blocks within-workspace over-exposure. |
| "App-level role filter could be forgotten on a new endpoint" | True — a developer could miss the `WHERE assigned_to = ` filter | Integration tests verify every technician job-listing endpoint returns only assigned jobs (see Required Test Coverage). |
| "What if someone crafts a direct API call?" | They'd see all jobs in a workspace they legitimately belong to | The data is within their authorized workspace. It's an inconvenience, not a data breach. Acceptable for alpha. |

> The absence of a workspace switcher for TECHNICIANs is a **UX choice, not a security boundary**. Backend endpoints remain responsible for applying technician-scoped filtering regardless of how the frontend is built.

### 4. What RLS Is and Isn't

| Layer | Responsibility | Tool |
|-------|---------------|------|
| **Workspace isolation** | "You MUST NOT see another workspace's data" | RLS — safety net, catches mistakes, prevents cross-tenant leaks |
| **Role-based visibility** | "TECHNICIANs should only see their assigned jobs" | Application code — business rule, expected to evolve, easy to test and debug |

**Why not put both in RLS?**

- Mixing them makes RLS policies complex (branching logic, multiple session variables)
- Role visibility rules will change over time (new roles, new scoping rules) — application code is easier to modify
- A TECHNICIAN seeing an unassigned job within their own company is not a security incident
- Debugging "RLS silently filtered my query to 0 rows" is significantly harder than debugging application-level WHERE clauses

## Consequences

### Positive

- TECHNICIAN UX is simplified — one screen, all their work
- RLS policies are trivial — one line per table, same pattern everywhere
- Role visibility logic is visible, testable, and in application code
- Clean separation: security (RLS) vs business rules (application)
- Personal workspace users (like User B) never encounter workspace complexity

### Negative

- A crafted API call from a TECHNICIAN could bypass role visibility within their authorized workspace — acceptable for alpha, addressable with API guards later
- Frontend must be smart about inferring workspace from job context for TECHNICIANs
- Role visibility is not enforced at the DB level — requires discipline in application code

### Neutral

- This decision does not affect ADMINs — they still switch workspaces via the `X-Workspace-Id` header as described in ADR-0033
- The portfolio UNION query pattern (described in ADR-0033 §4) is the implementation mechanism for the TECHNICIAN unified view

## Required Test Coverage

This decision places role-based visibility in application code rather than in the database. That trade-off demands explicit test coverage:

### RLS Integration Tests
- Prove cross-workspace access is impossible: a user with access to Workspace A must receive zero rows when `app.workspace_id` is set to Workspace B
- Verify RLS applies to all tenant-scoped tables (jobs, clients, saved_buildings, and any future tables)

### Technician Scoping Tests
- Every technician-facing job-listing endpoint must have integration tests proving only assigned jobs are returned
- Tests must cover: TECHNICIAN with 0 assigned jobs → empty result, TECHNICIAN with some assigned jobs → only those returned, unassigned jobs in same workspace → excluded

### Admin Scoping Tests
- Admin endpoints must have tests proving full workspace-scoped access works correctly
- Tests must cover: ADMIN sees all jobs in workspace, ADMIN in personal workspace sees all personal jobs

### Portfolio Query Tests
- Test the cross-workspace UNION query with mixed roles (ADMIN in one workspace, TECHNICIAN in another)
- Verify correct per-workspace scoping is applied (ADMIN workspaces return all jobs, TECHNICIAN workspaces return assigned-only)

## References

- [ADR-0030](./0030-workspace-isolation-abstraction.md) — Workspace isolation abstraction
- [ADR-0032](./0032-derived-workspace-access.md) — Derived workspace access
- [ADR-0033](./0033-stateless-workspace-context.md) — Stateless workspace context
- [PHASE_3C1_Research.md](../2-during-implementation/DDD/ModuleDesign/Auth/PHASE_3C1_Research.md) — Q1 discussion and resolution
