# ADR-0026: Professional Network — Cross-Tenant Connections Model

**Status:** Proposed  
**Date:** 2026-03-29  
**Deciders:** Marcus, AI Pair Programming  

## Context

PCD is built around tenant isolation: every entity (Job, Client, Building bookmark, LMP Credential) is scoped by `workspace_id` (see [ADR-0030](./0030-workspace-isolation-abstraction.md)). Each workspace's data is private by default.

However, real plumbing work is networked. A single plumber (User A) may:

1. Own his own LLC (Company A)
2. Work as a QI under an LMP friend's company (Company B)
3. Do subcontract work for a larger firm (Company C)

This creates scenarios that cross tenant boundaries:

- **Job transfer:** A plumber can't make a job → sends it to a connected plumber at another company
- **Job collaboration:** Two plumbers from different companies work a job together
- **LMP oversight:** An LMP tracks QIs across multiple companies
- **Credential sharing:** An LMP shares their license card with QIs who work under them

The workspace isolation model ([ADR-0030](./0030-workspace-isolation-abstraction.md)) provides per-workspace data isolation, but provides no mechanism for cross-workspace interaction between users at different companies.

## Decision

Introduce a **Professional Connections** layer that creates explicit, user-to-user links across tenant boundaries. The connection graph is between **people**, not companies. Company-to-company relationships are derived from the people who connect.

### Core Entity: Connection

```
connections(
    id UUID PK,
    requester_id UUID FK → users,     -- who initiated
    responder_id UUID FK → users,     -- who accepted
    connection_type TEXT,             -- COLLEAGUE, SUPERVISES, SUBCONTRACTS
    status TEXT,                      -- PENDING, ACCEPTED, DECLINED, REVOKED
    created_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ
)
```

### Design Principles

1. **Connections are opt-in.** No user can see another company's data without an explicit, accepted connection.
2. **The atomic unit is user-to-user.** Company A doesn't connect to Company B. User X at Company A connects to User Y at Company B.
3. **Tenant isolation is the default.** Connections create controlled, explicit holes in the boundary — not a general bypass.
4. **Each connection has a type** that determines what visibility it grants:

| Type | Meaning | Grants |
|------|---------|--------|
| `COLLEAGUE` | "We work together sometimes" | Can share/transfer jobs |
| `SUPERVISES` | "I'm the LMP, they're my QI" | LMP can view QI's jobs, share credentials |
| `SUBCONTRACTS` | "I send them work" | Can transfer/assign jobs cross-company |

### What This Enables

| Scenario | Mechanism |
|----------|-----------|
| Transfer a job to a connected user | Job `assigned_to` changes; job appears in target's portfolio via `job_participants` |
| Two plumbers work a job together | Both are `job_participants`; job visible in both portfolios |
| LMP tracks QIs across companies | Query via `SUPERVISES` connections → get connected users' jobs |
| LMP shares credential card | `lmp_credential_shares` links card to connected users' companies |

### What This Does NOT Do

- Does not merge companies or bypass tenant isolation for unconnected data
- Does not create shared billing, shared clients, or shared buildings
- Does not allow browsing another company's data — only explicitly shared items
- Does not change the workspace isolation model ([ADR-0030](./0030-workspace-isolation-abstraction.md)) — each workspace's data stays private unless explicitly shared

## Implications

### Cross-Cutting Concerns

This feature touches multiple existing domains:

| Domain | Impact |
|--------|--------|
| **Tenant (Users)** | New `connections` table + connection lifecycle |
| **Jobs** | New `job_participants` table; portfolio queries expand to include shared jobs |
| **LL152** | LmpCredential sharing via connections |
| **Auth** | No change to JWT/workspace scoping; connected data is fetched via explicit joins |
| **API** | New endpoints for connection management + modified portfolio queries |

### Phase 3A Compatibility

The Phase 3A design (workspace isolation per [ADR-0030](./0030-workspace-isolation-abstraction.md), `email UNIQUE` globally, `company_memberships` junction table) is **compatible** with this feature. Key reasons:

- `email UNIQUE` globally: enables finding users by email for connection requests
- Workspace model: users have personal workspaces + company workspaces; connections add cross-workspace bridges on top
- No schema changes required in Phase 3A to support future connections

### Deferred to Phase 3E/5

This ADR captures the architectural decision. Implementation is deferred until after Phase 3A-3D (identity, auth, RBAC) are complete. The connections layer sits on top of the identity foundation.

## Alternatives Considered

### Alternative: Multi-company membership (`user_company_memberships` junction table)

Where a user belongs to multiple companies simultaneously.

**Rejected for alpha.** This changes the fundamental auth model — every JWT claim, every query, every middleware needs to know "which company context am I acting in?" The Connections model is additive (new tables, new queries) rather than disruptive (changing existing queries).

### Alternative: Company-to-company relationships

Where companies formally link to each other.

**Rejected.** Real plumbing relationships are person-to-person. A plumber doesn't think "my LLC has a formal partnership with Danny's LLC." He thinks "I know Danny, he sends me work." The company-to-company link can be derived from the user-to-user connections if needed.

## References

- [ALPHA_PERSONAS_AND_SCOPE.md](../ALPHA_PERSONAS_AND_SCOPE.md) — User A and User B scenarios
- [PHASE_3A_DataFoundation.md](../roadmap/PHASE_3A_DataFoundation.md) — Users + Company data model
- [SFR-SR_security.md](../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) — RBAC matrix
