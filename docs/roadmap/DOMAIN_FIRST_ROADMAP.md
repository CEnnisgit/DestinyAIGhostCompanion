# Domain-First Roadmap: PCD LL152 Pilot

> **Principle:** Design from the domain core outward. Research first, spec second, implement third.
> **Source of truth:** [PRD_LL152_PILOT.md](../PRD_LL152_PILOT.md)
> **Key ADRs:** [ADR-0012](../adr/0012-compliance-engine-extensions-and-roster-status.md) (Compliance Engine), [ADR-0016](../adr/0016-job-engine-pluggable-workflows.md) (Job Engine + Workflows), [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md) (Phase 3 Decomposition)

---

## How This Roadmap Works

Each phase identifies **domain concepts that need spec work** — the same kind of deep research + aggregate design you did for Building and ComplianceObligation. When you reach a phase, you will:

1. **Research** — Understand the real-world domain (forms, rules, edge cases)
2. **Spec** — Write aggregate specs, ValueObjects, invariants in `docs/2-during-implementation/DDD/ModuleDesign/`
3. **Implement** — Use the specs as guidance with your coding agent

Phases are ordered by **domain dependency** — each phase's concepts depend on the previous phase being understood.

---

## Phase 0: Foundation Data ✅ DONE — [details](./PHASE_0_Foundation.md)

> *"What are we inspecting?"*

You've already done the deep research here. This phase answered: what is a NYC building, how do we identify one, and what compliance obligations exist?

### Aggregates Designed

| Aggregate | Spec Depth | Key Outputs |
|-----------|-----------|-------------|
| **Building** (CRM/Assets) | ✅ Deep | Aggregate spec, 6 ValueObject specs, Authority-per-VO rules, 3 pipeline designs |
| **ComplianceObligation** (CRM/Compliance) | ✅ Deep | Generic engine + LL152 program spec, obligation lifecycle, roster import rules |

### Artifacts Produced
- Database schema (11 tables via SQLx / `crates/pcd-db`)
- PAD ingestion pipeline (Rust)
- LL152 ingestion pipeline (Rust)
- Dev dashboard for visualization

---

## Phase 1: The Job Engine ✅ DONE — [details](./PHASE_1_JobEngine.md)

> *"What is the work, and how does it flow?"*
>
> **See:** [ADR-0016](../adr/0016-job-engine-pluggable-workflows.md)

The **Job aggregate** is the core engine — a generic work container that manages the lifecycle of any field assignment. Per ADR-0016, the Job is separated from the type-specific workflow (LL152 Inspection) that plugs into it, mirroring the Compliance Engine + Programs pattern.

### Implementation Summary

| Component | Status | Key Output |
|-----------|--------|------------|
| **Job Aggregate** | ✅ | 387-line aggregate root with factory, reconstitution, 8 commands, terminal-state guards |
| **State Machine** | ✅ | 4 engine-level states (OPEN → IN_PROGRESS → COMPLETED/CANCELED) with domain events |
| **5 Value Objects** | ✅ | JobStatus, JobNumber, JobType, SourceKind, Priority — all with specs and Rust code |
| **11 Domain Events** | ✅ | Typed payloads, emitted by every command |
| **Repository + DB** | ✅ | SQLx adapter, transactional save, `jobs` + `job_events` tables |
| **13 API Endpoints** | ✅ | CRUD + lifecycle commands + field updates + obligation linking |
| **Handoff Contract** | ⏭️ | Correctly deferred to Phase 2 (workflow-specific, not engine-level) |

---

## Phase 2: LL152 Inspection Workflow ✅ DONE — [details](./PHASE_2_LL152Workflow.md)

> *"What does an LL152 inspection actually look like?"*
>
> This is the first **workflow type** that plugs into the Job engine (ADR-0016).

### Implementation Summary

| Component | Status | Key Output |
|-----------|--------|------------|
| **Workflow State Machine** | ✅ | 5 states (DRAFT → CAPTURING → READY_FOR_REVIEW → UNDER_REVIEW → FINALIZED) |
| **Branch Discriminator** | ✅ | 3 branches (StandardInspection, NoGasPiping, GasPipingNotSupplied) |
| **Aggregate Behavior** | ✅ | 6 command methods with state validation + event returns |
| **Inspection Findings** | ✅ | 5 GPS1 categories, each as a child entity with observation/flags |
| **Photo Evidence** | ✅ | Dual-level (finding + job), metadata-only for alpha |
| **Submission Validation** | ✅ | Date + 5-category completeness gate (422 on failure) |
| **Event Emission** | ✅ | 10 event types (all transitions + CRUD operations) |
| **DB Layer** | ✅ | All transitions in transactions with event emission |
| **API Layer** | ✅ | 11 endpoints (overview, details, transitions, findings, photos) |
| **Tests** | ✅ | 116 domain tests including 17 command + 6 validation |

### Deferred Items
- GPS1/GPS2 PDF generation → Phase 4 (Reporting)
- LMP company fields → Phase 3 (People & Tenancy)
- Binary photo upload (GCS) → Post-Alpha

---

## Phase 3: People & Tenancy 🔲 — [index](./PHASE_3_PeopleTenancy.md)

> *"Who are the users, how does multi-company isolation work, and how are features gated?"*
>
> Phase 3 has been decomposed into **eight sub-phases** per [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md). The alpha critical path is 3A→3B→3C.1. Post-alpha phases add membership lifecycle, entitlements, and payments.

### Alpha Critical Path

| Sub-Phase | Focus | Status | Details |
|-----------|-------|--------|---------| 
| **3A: Identity Foundation** | User + Company + LMP Credential + membership infra | 🔲 | [details](./PHASE_3A_DataFoundation.md) |
| **3B: Authentication** | JWT login, Argon2, auth middleware | 🔲 | [details](./PHASE_3B_Authentication.md) |
| **3C.1: Authorization Core** | RBAC, company context, RLS | 🔲 | [details](./PHASE_3C_Authorization.md) |

### Post-Alpha

| Sub-Phase | Focus | Status | Details |
|-----------|-------|--------|---------| 
| **3M: Membership Lifecycle** | Invitation, roles, context switching | 🔲 | [details](./PHASE_3M_MembershipLifecycle.md) |
| **3N: Entitlements** | Person/company tier, feature gating | 🔲 | [details](./PHASE_3N_Entitlements.md) |
| **3C.2: Full Authorization** | RBAC + entitlement gating | 🔲 | [details](./PHASE_3C_Authorization.md) |
| **3P: Payments** | Stripe, billing, webhooks | 🔲 | [details](./PHASE_3P_Payments.md) |

### Parallel Work

| Sub-Phase | Focus | Status | Details |
|-----------|-------|--------|---------| 
| **3D: Profile Enrichment** | Extended fields, user management API | 🔲 | [details](./PHASE_3D_ProfileEnrichment.md) |
| **3E: Professional Network** | Cross-company connections, job sharing | 🔲 | [details](./PHASE_3E_ProfessionalNetwork.md) |

### Key Design Decisions (from research)
- **Membership ≠ Subscription ≠ Payments** — three separate concepts ([ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md))
- **Client aggregate:** ✅ Already implemented in Phase 1.5
- **LMP credential:** Standalone entity (reusable license card attached to jobs)
- **Roles:** ADMIN + TECHNICIAN (per SFR-SRAZ)
- **Professional network:** User-to-user connections, not company-to-company ([ADR-0026](../adr/0026-professional-network-connections.md))
- **Alpha personas:** 2 ADMINs + 2-4 TECHNICIANs (see [ALPHA_PERSONAS_AND_SCOPE](../ALPHA_PERSONAS_AND_SCOPE.md))

---

## Phase 4: Application & Presentation 🔲 — [details](./PHASE_4_ApplicationPresentation.md)

> *"Wire the domain to real users."*

This is where specs become running software. By this point, you'll have full domain specs for every aggregate and ValueObject. Implementation becomes mechanical.

### Work Areas

| Area | Objective |
|------|-----------|
| **API Layer** | Wire domain modules, expose REST endpoints |
| **LMP Dashboard** (Lane B) | Web UI for job intake, dispatch, review, report access |
| **Plumber Capture** (Lane A) | Mobile-first UI for assigned jobs, GPS1 form, photo capture, submit |
| **Reporting** | GPS1/GPS2 PDF generation from finalized inspection data |
| **Deadlines** | Calculation service + dashboard view (schema already supports this) |

### Why This Is Last
Not because it's less important — but because with solid domain specs, this phase becomes **execution, not design.** The specs tell you exactly what tables to create, what endpoints to expose, what validation to enforce, and what state transitions to allow.

---

## Phase Dependency Map

```text
Phase 0: Foundation ✅
  Building, ComplianceObligation
      │
      ▼
Phase 1: Job Engine ✅
  Job Aggregate, State Machine
      │
      ├──────────────────────┐
      ▼                      ▼
Phase 1.5: Tenant ✅    Phase 2: LL152 ✅
  Company (stub)           Workflow, Findings
  Client, SavedBuilding    Photos, Validation
      │                      │
      └──────────┬───────────┘
                 ▼
      ┌─────────────────────────────────────────────┐
      │          ALPHA CRITICAL PATH                │
      │                                             │
      │  3A: Identity Foundation 🔲                 │
      │    User + Company + LmpCredential + infra   │
      │                 │                           │
      │                 ▼                           │
      │  3B: Authentication 🔲                      │
      │    JWT + Login + Middleware                  │
      │                 │                           │
      │        ┌────────┼──────────────┐            │
      │        ▼        │              ▼            │
      │  3C.1: Authz    │        3D: Profiles       │
      │   (RBAC) 🔲     │         (Extended) 🔲     │
      │        │        │                           │
      │        ▼        │                           │
      │  3E: Network    │                           │
      │   (Connect) 🔲  │                           │
      └─────────────────┼───────────────────────────┘
                        │
      ┌─────────────────┼───────────────────────────┐
      │        POST-ALPHA                           │
      │                 ▼                           │
      │  3M: Membership Lifecycle 🔲                │
      │    Invitation, roles, context switching     │
      │                 │                           │
      │                 ▼                           │
      │  3N: Entitlements 🔲                        │
      │    Person + company tier, feature gating    │
      │                 │                           │
      │                 ▼                           │
      │  3C.2: Full Authorization 🔲                │
      │    RBAC + entitlement gating                │
      │                 │                           │
      │                 ▼                           │
      │  3P: Payments 🔲                            │
      │    Stripe, billing, webhooks                │
      └─────────────────┼───────────────────────────┘
                        │
                        ▼
      Phase 4: Application & Presentation 🔲
        API Polish, Dashboard, Reports
```

---

## What About the SRSD Freshness Check?

The SRSD was designed to cover the PRD comprehensively, and the [PRD_EXTRACTION_NOTES.md](../1-pre-implementation/PRD_EXTRACTION_NOTES.md) already verified alignment. The 5 gaps identified (GPS1 fields, sub-cycle mapping, stop conditions, photo standards, data retention) will naturally be resolved as you work through Phases 1-2.

**Recommendation:** Don't do a separate SRSD freshness pass right now. Instead, as you spec each phase's domain concepts, cross-reference the relevant SFRs/SNFRs to confirm they still match your understanding. This keeps the freshness check grounded in real design work rather than abstract document review.
