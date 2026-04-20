# Phase 3: People & Tenancy (Index)

> **Status:** 🔲 In Progress
> **Objective:** Design the user, company, and authentication domain — who uses the system, how workspace-based isolation works, and how features are gated.
> **ADR:** [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md) — Phase 3 decomposition, [ADR-0030](../adr/0030-workspace-isolation-abstraction.md) — workspace isolation, [ADR-0031](../adr/0031-person-first-feature-gating.md) — person-first gating, [ADR-0032](../adr/0032-derived-workspace-access.md) — derived access

---

## ⚠️ This Phase Has Been Decomposed

Phase 3 is split into eight sub-phases organized by domain concern.

### Alpha Critical Path (strictly ordered)

These three sub-phases are required for alpha launch:

| Sub-Phase | Focus | Depends On | Status |
|-----------|-------|-----------|--------|
| **[3A: Identity Foundation](./PHASE_3A_DataFoundation.md)** | Workspace + User + Company + LMP Credential + membership infrastructure | Phase 2 ✅ | 🔲 In Progress (spec) |
| **[3B: Authentication](./PHASE_3B_Authentication.md)** | JWT login, Argon2, auth middleware | 3A | 🔲 Not Started |
| **[3C.1: Authorization Core](./PHASE_3C_Authorization.md)** | RBAC enforcement, company context, RLS | 3B | 🔲 Not Started |

### Post-Alpha (ordered by domain dependencies)

| Sub-Phase | Focus | Depends On | Status |
|-----------|-------|-----------|--------|
| **[3M: Membership Lifecycle](./PHASE_3M_MembershipLifecycle.md)** | Invitation, acceptance, role transitions, context switching | 3B | 🔲 Not Started |
| **[3N: Entitlements](./PHASE_3N_Entitlements.md)** | Person tier, company tier, feature gating | 3M | 🔲 Not Started |
| **[3C.2: Full Authorization](./PHASE_3C_Authorization.md)** | RBAC + entitlement-based gating | 3N | 🔲 Not Started |
| **[3P: Payments](./PHASE_3P_Payments.md)** | Stripe, billing, checkout, webhooks | 3N | 🔲 Not Started |

### Parallel Work (after identity + auth are stable)

| Sub-Phase | Focus | Depends On | Status |
|-----------|-------|-----------|--------|
| **[3D: Profile Enrichment](./PHASE_3D_ProfileEnrichment.md)** | Extended fields, user management API, audit | 3B | 🔲 Not Started |
| **[3E: Professional Network](./PHASE_3E_ProfessionalNetwork.md)** | Cross-company connections, job sharing, credential sharing | 3C.1 | 🔲 Not Started |

---

## Dependency Chain

```text
Phase 2 ✅
    │
    ▼
3A: Identity Foundation
  (Workspace, User, Company, company_memberships infra, LmpCredential)
    │
    ├────────────────────────────────────┐
    ▼                                    │
3B: Authentication                   (3M design can start
  (JWT + Login + Middleware)           in parallel, but
    │                                  implementation needs 3B)
    ├──────────┬───────────┐             │
    ▼          ▼           ▼             ▼
3C.1: Authz  3D: Profiles  3M: Membership Lifecycle
  (RBAC)      (Extended)     (Invitation, roles, context)
    │                              │
    ▼                              │
3E: Professional Network           │
  (Connections + Sharing)           │
                                    ▼
                              3N: Entitlements
                                (Person + company tier)
                                    │
                                    ▼
                              3C.2: Full Authorization
                                (RBAC + entitlement gating)
                                    │
                                    ▼
                              3P: Payments
                                (Stripe, billing)
                                    │
                         ┌──────────┘
                         ▼
               Phase 4: Application & Presentation
```

---

## Key Terms

| Term | Definition | Phase |
|------|-----------|-------|
| **Identity** | Who you are — name, email, active status | 3A |
| **Authentication** | Proving who you are — login, JWT, session | 3B |
| **Authorization** | Whether you're allowed to do something | 3C.1 (RBAC), 3C.2 (full) |
| **Organizational Membership** | Your relationship to a company — role, joining/leaving | 3M |
| **Entitlements** | What features you/your company can use — tier, plan | 3N |
| **Payments** | How money is collected — Stripe, billing, invoices | 3P |
| **Connection** | A user-to-user link for cross-company collaboration | 3E |

> [!IMPORTANT]
> **Membership ≠ Subscription.** "Membership" in this project means "I work at this company" (organizational relationship). "Entitlements" means "what features are allowed" (plan/tier). "Payments" means "how money is collected" (billing). These are three separate concepts with separate lifecycles. See [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md).

---

## Key Design Decisions (from research)

- **Client aggregate:** ✅ Already implemented in Phase 1.5
- **LMP credential:** Standalone entity (reusable license card attached to jobs)
- **Roles:** ADMIN + TECHNICIAN (per SFR-SRAZ)
- **Workspace abstraction:** Universal data isolation boundary ([ADR-0030](../adr/0030-workspace-isolation-abstraction.md))
- **Person-first model:** Jobs/clients are personal capabilities, not company-gated ([ADR-0031](../adr/0031-person-first-feature-gating.md))
- **Derived access:** Workspace access computed from domain relationships, no workspace_memberships table ([ADR-0032](../adr/0032-derived-workspace-access.md))
- **Professional network:** User-to-user connections, not company-to-company ([ADR-0026](../adr/0026-professional-network-connections.md))
- **Alpha personas:** 2 ADMINs + 2–4 TECHNICIANs (see [ALPHA_PERSONAS_AND_SCOPE](../ALPHA_PERSONAS_AND_SCOPE.md))
- **Phase decomposition:** 3M/3N/3P added per [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md)

---

## Relevant Requirements (applies across all sub-phases)

### Functional (SFR)

| Requirement | Description | Sub-Phase |
|-------------|-------------|-----------|
| `SFR-SRAN-01` | Email/password login | 3B |
| `SFR-SRAN-02` | JWT tokens (15m access + 7d refresh) | 3B |
| `SFR-SRAN-03` | Password reset via email | Deferred |
| `SFR-SRAN-04` | Logout | 3B |
| `SFR-SRAZ-01..07` | Permission matrix (TECHNICIAN vs ADMIN) | 3C.1 |
| `SFR-SRAC-01` | Technician scope (own assigned jobs) | 3C.1 |
| `SFR-SRAC-02` | Admin scope (all company jobs) | 3C.1 |
| `SFR-SRAC-03` | Company isolation (multi-tenancy) | 3C.1 + 3E |

### Non-Functional (SNFR)

| Requirement | Description | Sub-Phase |
|-------------|-------------|-----------|
| `SNFR-SC-11` | Password storage (Argon2) | 3B |
| `SNFR-SA-01` | Rate limiting | Deferred |
| `SNFR-SA-03` | Token expiry | 3B |

---

## Alpha Personas (Reference)

See [ALPHA_PERSONAS_AND_SCOPE.md](../ALPHA_PERSONAS_AND_SCOPE.md) for full details.

- **User A:** Solo owner + QI. ADMIN role. Works under external LMP. Works across multiple companies.
- **User B:** Small team owner + dispatcher. ADMIN role. Has 2-4 TECHNICIAN employees.
- **LMP:** Not an alpha user. LMP credential info entered as reusable cards, potentially shared via connections.
