# Deferred Concept: Teams

> **Status:** Deferred to Beta  
> **Decided:** 2026-03-30  
> **Related ADRs:** [ADR-0030 (Workspace Abstraction)](../../adr/0030-workspace-isolation-abstraction.md), [ADR-0031 (Person-First Feature Gating)](../../adr/0031-person-first-feature-gating.md)  
> **Tier Required:** Pro personal subscription

---

## What Is a Team?

A Team is a **lightweight coordination group** for individual users who work together regularly but don't have (or need) a formal company entity.

Think of it as a middle ground between:
- **Connections** (peer-to-peer, one-off hand-offs, free tier)
- **Companies** (formal business entity, verified, employer/employee, paid company sub)

### Example

User B doesn't own an LLC, but he regularly works with 3 other plumbers. He creates a "Team" and adds them. When he gets a job he can't handle alone, he assigns it to a team member and tracks their progress — without needing to register a business or pay for a company subscription.

---

## Key Properties

| Property | Value |
|----------|-------|
| **Entity type** | Lightweight separate entity (not tagged connections) |
| **Business validation** | None required |
| **Admin** | The user who creates the team |
| **Members** | Individual users invited by the admin |
| **Multi-team membership** | Yes — a user can be on multiple teams |
| **Data ownership** | Teams are a **coordination layer only** — they do NOT own data |
| **Client scoping** | Clients belong to the team admin's personal workspace, not the team |
| **Job scoping** | Jobs dispatched via team belong to the admin's workspace; team members receive assignments |
| **Tracking level** | Lighter than company dispatch — admin sees member status and job completion, but not real-time location or detailed activity |

---

## How Teams Differ from Companies

| Aspect | Team | Company |
|--------|------|---------|
| Creation | Any Pro user can create one | Requires paid company sub + verification |
| Validation | None | License/business registration |
| Data ownership | NO — coordination layer only | YES — company workspace owns jobs/clients |
| Tracking | Light (status, completion) | Full (activity, location, arrivals, completion) |
| Roles | Admin + Member | ADMIN + TECHNICIAN (expandable) |
| Cost | Pro personal tier | Company subscription |

---

## How Teams Fit the Workspace Model

Per ADR-0030, every isolation context gets a workspace. When Teams are implemented:

- A Team gets a workspace with `workspace_type = 'TEAM'`
- **However**, since teams don't own data, the workspace may only be used for team coordination metadata (assignments, schedules) — not for jobs/clients themselves
- Jobs dispatched via a team remain in the **admin's personal workspace**
- This is an open design question to resolve during Beta planning

---

## Open Design Questions (For Beta)

1. **Does a team workspace hold any data?** Or is the team purely a membership/coordination structure without its own workspace?
2. **Assignment mechanism** — Is dispatching a job to a team member the same API as company dispatch, just with different permissions?
3. **Notification model** — How does a team member get notified of an assignment?
4. **Team lifecycle** — Can a team be archived? What happens to in-flight assignments?
5. **Team size limits** — Should there be a limit on team members (e.g., max 10 for Pro tier)?

---

## Why Deferred

- Alpha focuses on two users who don't need team coordination yet
- The workspace model (ADR-0030) was designed to accommodate teams — no schema changes needed when we build this
- Building connections (Phase 3E) first gives us the peer-to-peer foundation that teams extend
- Teams add product complexity that should be validated with real user feedback from alpha/early beta
