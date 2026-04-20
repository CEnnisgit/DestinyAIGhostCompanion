# ADR-0029: Phase 3 Decomposition — Membership Lifecycle, Entitlements, and Payments

**Status:** Accepted
**Date:** 2026-03-30
**Deciders:** Marcus, AI Pair Programming (with cross-agent validation)
**Supersedes:** Partially updates [ADR-0027](./0027-user-first-registration-rls-isolation.md) (membership scope) and the Phase 3 sub-phase index

## Context

During the design review of the User aggregate (Phase 3A), three distinct concepts were identified that had been conflated under "membership" and "user-company relationship":

1. **Organizational membership** — "I work at this company" (role, joining/leaving, context switching)
2. **Subscription / entitlements** — "What features are allowed?" (personal tier, company tier, feature gating)
3. **Payments** — "How money is collected" (Stripe, billing cycles, invoices)

The original Phase 3 structure (3A → 3B → 3C → 3D/3E) treated membership lifecycle behavior as part of 3A (Data Foundation) and subscription as a vague "future consideration." This created two problems:

1. **Premature domain behavior.** The User aggregate spec defined membership management commands (`add_membership`, `remove_membership`, `set_primary_membership`) with auto-promote policies and lifecycle rules that depend on designs that don't exist yet: invitation flows, subscription gating, UX for context switching.

2. **Authorization blocked on billing.** The implicit chain 3M → 3S → 3C would mean authorization couldn't be fully implemented until the pricing model was finalized — but RBAC (admin vs. technician) is needed much earlier than billing.

### Key insight from review

> "The `company_memberships` table exists in 3A as structural infrastructure. Membership lifecycle behavior is deferred to Phase 3M."

The junction table is load-bearing from day one (RLS depends on it), but the domain behavior on top of it is not.

### Additional insight: subscription is two-level

Subscription/entitlements apply at **both** the person level and the company level:

| Level | Free | Paid |
|---|---|---|
| **Person** | Browse buildings, view compliance data, professional profile | Premium features (TBD) |
| **Company** | N/A (companies require paid creation) | Job management, client portfolio, dispatching, GPS reports |

A person's paid tier doesn't unlock company features, and a company subscription doesn't upgrade the person's tier. These are independent.

## Decision

### 1. Three new sub-phases are added to Phase 3

| Phase | Name | Focus |
|---|---|---|
| **3M** | Membership Lifecycle | Invitation, acceptance, pending/active/suspended states, role changes, join/leave/remove, primary context switching UX |
| **3N** | Entitlements | Person tier, company tier, feature resolution rules, "can use X?" plan logic |
| **3P** | Payments | Stripe integration, checkout, webhooks, renewals, downgrades |

### 2. Authorization is built in two passes

| Pass | Name | What it checks |
|---|---|---|
| **3C.1** | Authorization Core (RBAC) | Authenticated user + company context + membership existence + membership role |
| **3C.2** | Full Authorization | RBAC + entitlement-based gating (person tier + company tier) |

3C.1 is needed for alpha. 3C.2 comes after 3N (Entitlements).

### 3. Membership in 3A is infrastructure-only

The `company_memberships` table is created in Phase 3A with the full schema (user_id, company_id, role, is_primary, joined_at), but:

- **No domain behavior** is modeled in 3A (no `add_membership`, `remove_membership`, etc.)
- Data is seeded via scripts
- The table is used by 3B/3C.1 middleware to resolve company context and check roles
- Full lifecycle design happens in 3M

### 4. User aggregate is identity-only in 3A

The User aggregate root in Phase 3A owns:
- Identity fields (name via DisplayName VO, email via Email VO)
- Active state (deactivate/reactivate)

It does **not** own CompanyMembership as a child entity in 3A. That aggregate boundary expansion happens in 3M when membership lifecycle is properly designed.

## Revised Phase Ordering

### Alpha critical path

```text
3A (Identity Foundation)
 → 3B (Authentication)
   → 3C.1 (Authorization Core — RBAC)
```

**3C.1 for alpha means concretely:**
- Authenticated user required on protected routes
- Company context resolved (from primary membership or request header)
- Membership existence validated ("does this user belong to this company?")
- Membership role checked where needed (admin vs. technician)
- Request-scoped `app.company_id` set for RLS

### Post-alpha ordering

```text
3M (Membership Lifecycle)
 → 3C.1 full (RBAC with all role-checked endpoints)
   → 3N (Entitlements — feature gating, tier model)
     → 3C.2 (Full authorization — role + plan gating)
       → 3P (Payments — Stripe integration)
```

### Parallel work (after identity + auth are stable)

- **3D** (Profile Enrichment) — can happen any time after 3B
- **3E** (Professional Network) — can happen any time after 3C.1

### Full dependency graph

```text
Phase 2 ✅
    │
    ▼
3A: Identity Foundation
  (User, Company, company_memberships infrastructure, LmpCredential)
    │
    ├──────────────────────────────┐
    ▼                              ▼
3B: Authentication              (3M can be designed in parallel,
  (JWT, login, session)          but implementation needs 3B)
    │                              │
    ▼                              ▼
3C.1: Authorization Core    3M: Membership Lifecycle
  (RBAC + company context)   (invitation, roles, context switching)
    │                              │
    ├──────────┬───────────────────┘
    ▼          ▼
3D: Profiles  3E: Professional Network
    │
    ▼
3N: Entitlements
  (person tier, company tier, feature gating)
    │
    ▼
3C.2: Full Authorization
  (RBAC + entitlement gating)
    │
    ▼
3P: Payments
  (Stripe, billing, webhooks)
    │
    ▼
Phase 4: Application & Presentation
```

## Implications

### For the User aggregate spec (immediate)

- Remove membership management commands (add/remove/set_primary)
- Remove CompanyMembership as a child entity
- Add note: "company_memberships exists in 3A as structural infrastructure. Membership lifecycle behavior is deferred to Phase 3M."
- User remains an aggregate root (owns identity invariants)

### For ADR-0027

ADR-0027 defined the `company_memberships` schema and the multi-company model. That decision stands — the **schema** is correct. What this ADR changes is **when the domain behavior** on top of that schema is designed.

### For the roadmap files

- `PHASE_3_PeopleTenancy.md` — update dependency chain and sub-phase index
- `PHASE_3A_DataFoundation.md` — clarify that membership is infrastructure-only
- New files needed: `PHASE_3M_MembershipLifecycle.md`, `PHASE_3N_Entitlements.md`, `PHASE_3P_Payments.md`

### For CompanyMembership spec

The spec becomes a **schema specification** in 3A (table structure, constraints, indexes) with a forward reference: "Full lifecycle behavior designed in Phase 3M."

## Alternatives Considered

### Keep membership behavior in 3A

Rejected. The membership lifecycle (invitation, acceptance, role transitions, primary switching) depends on designs that don't exist: subscription model, invitation UX, and the distinction between persistent primary and session-level context. Designing these now produces speculative behavior that will need to be rewritten.

### Make authorization wait for entitlements

Rejected. RBAC (admin vs. technician, company context) is needed for alpha security. Entitlement-based gating (free vs. paid features) is not needed until the pricing model is decided. Authorization should be built in two passes to avoid blocking security on business decisions.

### Combine entitlements and payments into one phase

Rejected. Entitlements ("what features are allowed") can be implemented with manual flags and no billing integration. Payments ("how money is collected") requires Stripe, webhooks, and significant external integration. Decoupling them means feature gating can ship before billing, which is valuable for beta testing.

## References

- [ADR-0027](./0027-user-first-registration-rls-isolation.md) — user-first registration, multi-company membership, RLS
- [ADR-0028](./0028-iam-module-restructuring.md) — IAM module structure
- [Vision: Registration and Tenancy](../vision/REGISTRATION_AND_TENANCY.md)
- [Vision: Professional Network](../vision/PROFESSIONAL_NETWORK.md)
- [Phase 3 Index](../roadmap/PHASE_3_PeopleTenancy.md)
