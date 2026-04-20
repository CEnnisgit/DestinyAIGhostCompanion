# Phase 3C.1 Authorization Core — Research & Open Questions

> **Status:** ✅ Spec-complete — All design questions resolved, specs written (PermissionGuard, RoleVisibility)
> **Depends On:** Phase 3B (spec-complete ✅, not yet implemented)
> **Roadmap:** [PHASE_3C_Authorization.md](../../../roadmap/PHASE_3C_Authorization.md)

---

## 1. What the 3C Roadmap Says

The roadmap is well-structured for 3C.1 (alpha RBAC). It covers:

- Route guards (`require_admin()`, `require_any_role()`)
- Permission matrix (SFR-SRAZ-01..07): ADMIN vs TECHNICIAN per action
- Query scoping: TECHNICIAN sees only assigned jobs, ADMIN sees all
- Job assignment: `assigned_to` field + assignment API
- Tenant isolation audit: migrate existing `company_id` scoping to workspace RLS

### What's Already Right (Post-Drift Fix)

- ✅ RLS via `workspace_id` (not `company_id` WHERE clauses)
- ✅ "Personal workspace has no RBAC" note
- ✅ ADR-0033 reference added
- ✅ Input counting fixed (3C.1 uses first four inputs)

---

## 2. Current Codebase State

### Jobs currently have `company_id`, not `workspace_id`

The Job aggregate (domain + DB) uses `company_id` for ownership scoping:

```rust
// pcd-domain/src/jobs/job.rs
pub struct Job {
    pub company_id: Uuid,       // ← will need workspace_id migration
    pub responsible_user_id: Option<Uuid>,  // ← NOT the same as assigned_to
    // ...
}
```

### No `assigned_to` field exists yet

The roadmap calls for `assigned_to: Option<Uuid>` on jobs. This doesn't exist in the codebase or the Job aggregate spec. The existing `responsible_user_id` is a **lightweight current owner** (who's in charge of this job right now), which is different from `assigned_to` (who's dispatched to execute the fieldwork).

### Existing query scoping is by `company_id` parameter

All current repository methods take `company_id` as a function parameter:

```rust
async fn list_by_company(company_id: Uuid) -> Vec<Client>
async fn find_by_job_number(company_id: Uuid, job_number: &str) -> Option<Job>
async fn next_job_number(company_id: Uuid) -> String
```

These will be replaced by RLS + workspace_id session variable. The repository methods won't need the `company_id` parameter anymore — RLS handles it transparently.

---

## 3. Resolved Design Decisions

### Q1: RESOLVED — Workspace Interaction Model + RLS Scope

> **Decision Date:** 2026-03-31
> **Two paired decisions that reinforce each other.**

#### Decision 1: TECHNICIAN Unified View (Model B)

**TECHNICIANs do NOT switch workspaces.** They see a single unified "My Jobs" view that aggregates:
- Their personal jobs (from personal workspace)
- All jobs assigned to them across every company they belong to

The frontend organizes by source (tabs, labels, sections), but the TECHNICIAN never sees a "switch workspace" dropdown. When they tap a specific job, the frontend silently sets `X-Workspace-Id` behind the scenes so the API can resolve context.

**Only ADMINs switch workspaces.** ADMINs need to operate WITHIN a company context to manage data: create jobs, manage clients, assign technicians, review findings. Workspace switching is an ADMIN tool, not a TECHNICIAN tool.

**Why this is right:**
- Matches how field workers actually think: "show me my jobs" — not "let me switch to my company's context"
- A plumber looks at his schedule and sees all his jobs. The company label tells him who he's working for today. He doesn't "enter" that company.
- Eliminates the confusing scenario of "a TECHNICIAN is viewing the company workspace — what should they see?" — they never do this.

#### Decision 2: Simple RLS (Q1 Option A)

**RLS enforces workspace isolation ONLY.** Role-based visibility is handled in application code.

```sql
-- RLS policy: one line, same pattern for every table
CREATE POLICY workspace_isolation ON jobs
  USING (workspace_id = current_setting('app.workspace_id')::uuid);
```

**Why this is right (reinforced by Model B):**
- TECHNICIANs never explicitly browse a company workspace → the scenario of "a TECHNICIAN sees unassigned jobs because RLS didn't filter by role" doesn't exist in the UX.
- The portfolio query already applies `assigned_to` filtering per workspace (application code).
- When a TECHNICIAN taps a specific job, it's a job from their pre-filtered portfolio — they're accessing something already authorized.
- RLS = security boundary (workspace isolation). Role visibility = business rule (application layer). Clean separation.

**What a crafted API call could bypass:**
- A TECHNICIAN who manually sets `X-Workspace-Id` to a company workspace and queries all jobs would see all jobs in that workspace (RLS only checks workspace access, not assignment).
- This is acceptable for alpha: the data is within a workspace they legitimately belong to, and the frontend never exposes this path.
- For production, this can be addressed with an API-level guard (not RLS) if needed.

---

## 4. More Resolved Design Decisions

### Q2: RESOLVED — Single Smart UNION for Portfolio Query

> **Decision Date:** 2026-03-31

The portfolio query uses a **single dynamically-built UNION ALL query** with per-workspace role scoping. The derived access query (ADR-0032) provides the workspace list with roles. Each UNION arm applies the appropriate filter:

```sql
-- OWNER/ADMIN workspaces — all jobs
SELECT ... FROM jobs WHERE workspace_id = $ws_id
UNION ALL
-- TECHNICIAN workspaces — assigned only
SELECT ... FROM jobs WHERE workspace_id = $ws_id AND assigned_to = $user_id
```

**Why Option A:**

- ADR-0034 makes this query the TECHNICIAN's primary and only interface — it must get scoping right
- Single DB round trip, clean pagination over one result set
- Derived access query already has workspace + role data — the UNION arms are a direct translation
- This is where the app-level role filtering from ADR-0034 lives: the portfolio query IS the technician-scoping implementation

**Rejected alternatives:**

- **N separate queries** — awkward pagination, multiple round trips, no benefit
- **Defer scoping** — unacceptable per ADR-0034 security review (TECHNICIANs would see unassigned jobs)

---

### Q3: RESOLVED — Replace `responsible_user_id` with `assigned_to`

> **Decision Date:** 2026-03-31

**Remove `responsible_user_id` from the Job aggregate. Add `assigned_to: Option<Uuid>`.**

`responsible_user_id` was a premature abstraction defined before the authorization model was designed. Now that 3C.1 defines the actual need — TECHNICIAN scoping requires knowing who's dispatched to do the fieldwork — the field should reflect that single, clear purpose.

**Why Option C (Replace):**

- One field, one meaning: "who is dispatched to execute this job's fieldwork?"
- Single source of truth for the TECHNICIAN scoping query (`WHERE assigned_to = $user_id`)
- The "who's accountable/overseeing" question is answered by context: the ADMIN who created the job in the company workspace. No second field needed.
- For solo operators (User A): `assigned_to = self` — he assigns jobs to himself
- For dispatchers (User B): `assigned_to = technician_id` — he assigns to his workers
- Two overlapping nullable UUIDs is a bug factory — "which field do I query?" is a question that shouldn't exist

**Migration impact:**

- Job aggregate spec: update field name and semantics
- DB migration: `ALTER TABLE jobs RENAME COLUMN responsible_user_id TO assigned_to` (or drop + add if semantics differ enough)
- Repository methods: update any queries referencing `responsible_user_id`
- If an explicit "overseer" concept is needed later (post-alpha), add it then — YAGNI

## 5. More Resolved Design Decisions (cont.)

### Q4: RESOLVED — ADMIN Can Submit Findings (No Legal Barrier)

> **Decision Date:** 2026-03-31
> **Research Source:** NYC DOB LL152 gas piping inspection rules ([nyc.gov/buildings](https://www.nyc.gov/site/buildings/property-or-business-owner/gas-piping-inspections.page)), GPS1 form requirements ([GPS1 PDF](https://www.nyc.gov/assets/buildings/pdf/gps1.pdf))

**Decision: ADMIN is a superset of TECHNICIAN for alpha.** The SFR-SRAZ-04 restriction (ADMIN ❌ for Submit Findings) is removed.

**Updated permission matrix:**

| Code | Action | TECHNICIAN | ADMIN |
|------|--------|-----------|-------|
| SFR-SRAZ-01 | Create Job | ❌ | ✅ |
| SFR-SRAZ-02 | Dispatch/Assign Job | ❌ | ✅ |
| SFR-SRAZ-03 | View Jobs | ✅ (assigned only) | ✅ (all in workspace) |
| SFR-SRAZ-04 | Submit Findings | ✅ | ✅ |
| SFR-SRAZ-05 | Finalize/Sign Report | ❌ | ✅ |
| SFR-SRAZ-06 | Generate Report | ❌ | ✅ |
| SFR-SRAZ-07 | Manage Users | ❌ | ✅ |

**Key change:** SFR-SRAZ-05 was "Approve/Return" — reframed to "Finalize/Sign Report" to reflect the actual compliance boundary (see below).

**Legal rationale:**

NYC LL152 rules govern the **official inspection artifact** (the signed report/certification filed with DOB), not internal app workflows. The law requires:

- Inspection by LMP or under LMP's direct supervision
- Report delivered to building owner within 30 days
- Owner files certification with DOB within 60 days
- Correction certifications within 120-180 days if needed
- Immediate reporting of unsafe/hazardous conditions
- Records retained for at least 8 years
- False statements = criminal liability + loss of filing privileges

**What the law does NOT require:** A separate "submitter" and "approver" in your software workflow. The submit/approve split was a business workflow choice, not a statutory requirement.

**The real compliance boundary: Finalization, not role permissions.**

The original permission matrix put compliance pressure on the wrong boundary (who can submit) when the real legal pressure belongs at a different boundary (when does a draft become an official record):

```
Draft (editable) ──→ Finalized/Signed (immutable) ──→ Correction/Addendum (new record)
```

| Stage | Editable? | What happens |
|-------|----------|-------------|
| **Draft** | ✅ Yes | Findings, notes, attachments can change freely |
| **Finalized/Signed** | ❌ Locked | Content becomes the official inspection record. Immutable snapshot. |
| **After finalization** | New records only | Correction certification, addendum, or superseding inspection. Never silent mutation of the original. |

This principle is captured separately in the LL152 workflow docs (see `OPEN_DESIGN_QUESTIONS.md` — Finalization Boundary Discovery).

---

## 6. Non-Questions (Derivable, No Discussion Needed)

| Topic | Answer | Source |
|-------|--------|--------|
| Does 3C.1 need its own DDD module? | No — authz specs live in `Auth/` module (closely related to authn) | Auth README already references 3C |
| Route guard pattern? | Axum extractors that check `AuthContext.role` | Standard Axum pattern |
| Personal workspace RBAC? | None — user is OWNER, all actions allowed | Roadmap line 41 |
| `company_id` → `workspace_id` migration | 3A handles the schema migration, 3C.1 handles the query migration | Phase dependencies |
| Error response for forbidden action? | 403 with `{ "error": "forbidden", "required_role": "ADMIN" }` | Standard REST |

---

## 7. Summary of All Resolved Decisions

| Q | Question | Decision | Rationale |
|---|----------|----------|-----------|
| Q1 | RLS scope | Simple RLS (workspace only) + app-level role filtering | ADR-0034. Workspace isolation = security (RLS). Role visibility = business rule (app code). |
| Q1b | TECHNICIAN UX model | Unified "My Jobs" view, no workspace switching | ADR-0034. Matches how field workers actually think. |
| Q2 | Portfolio query | Single smart UNION ALL with per-workspace scoping | Derived access query drives UNION arms. One round trip, clean pagination. |
| Q3 | assigned_to vs responsible_user_id | Replace — drop premature field, add `assigned_to` | YAGNI. One field, one meaning, one scoping query. |
| Q4 | ADMIN submit findings | ADMIN is superset of TECHNICIAN | NYC LL152 law doesn't require submit/approve role split. Compliance lives at finalization boundary. |

---

## 8. Next Steps

All design questions resolved. Ready for spec writing:

1. Write specs:
   - `PermissionGuard.md` — route guard spec (extractors + policy)
   - `RoleVisibility.md` — query scoping rules per workspace type + role
   - Update `Job_Aggregate.md` — replace `responsible_user_id` with `assigned_to`
2. Update the 3C roadmap permission matrix to match the resolved Q4 table
3. Update traceability files
