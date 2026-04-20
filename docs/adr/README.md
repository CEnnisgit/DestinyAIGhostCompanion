# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for significant technical decisions.

## ADR Index (Chronological)

| # | Title | Status | Date |
|---|-------|--------|------|
| [0001](./0001-layered-architecture.md) | Layered Architecture with Hexagonal Target | Accepted | Dec 2024 |
| [0002](./0002-drizzle-orm.md) | Drizzle ORM for Database Layer | Accepted | Dec 2024 |
| [0003](./0003-container-wiring.md) | Container-based Dependency Wiring | Accepted | Dec 2024 |
| [0004](./0004-rate-limiting-strategy.md) | Rate Limiting Strategy | Accepted | Dec 2024 |
| [0005](./0005-hexagonal-migration-complete.md) | Hexagonal Migration Complete | Accepted | Dec 2024 |
| [0007](./ADR-007-job-status-delivery-tracking.md) | Job Status & Delivery Tracking | Accepted | Dec 2024 |
| [0008](./0008-feature-centric-slices.md) | Feature-Centric Vertical Slices | Accepted | Dec 2024 |
| [0009](./0009-command-center-cqrs.md) | Command Center CQRS Query Service | Accepted | Dec 2024 |
| [0010](./0010-pda-sdd-ci-enforcement.md) | PDA-SDD CI Enforcement | Accepted | Dec 2024 |
| [0011](./0011-pad-ingestion-rust-worker.md) | PAD Ingestion Rust Worker | Accepted | Jan 2026 |
| [0012](./0012-compliance-engine-extensions-and-roster-status.md) | Compliance Engine Extensions and Roster Status | Accepted | Jan 2026 |
| [0013](./0013-bin-lifecycle-and-pipeline-arrival-order.md) | BIN Lifecycle and Pipeline Arrival Order | Accepted | Mar 2026 |
| [0014](./0014-version-membership-junction-table.md) | Version Membership Junction Table | Accepted | Mar 2026 |
| [0015](./0015-event-history-first-seen-only.md) | Event History First Seen Only | Accepted | Mar 2026 |
| [0016](./0016-job-engine-pluggable-workflows.md) | Job Engine with Pluggable Workflow Types | Accepted | Mar 2026 |
| [0017](./0017-independent-plumber-tenancy.md) | Independent Plumber Tenancy | Accepted | Mar 2026 |
| [0018](./0018-client-account-vs-requester-contact.md) | Client Account vs Requester Contact | Accepted | Mar 2026 |
| [0019](./0019-camelcase-api-serialization.md) | camelCase API Serialization | Accepted | Mar 2026 |
| [0020](./0020-multi-tenancy-database-isolation.md) | Multi-Tenancy Database Isolation | Accepted | Mar 2026 |
| [0021](./0021-client-centric-portfolio.md) | Client-Centric Portfolio | Accepted | Mar 2026 |
| [0022](./0022-building-bookmarks.md) | Building Bookmarks | Accepted | Mar 2026 |
| [0023](./0023-address-first-job-creation.md) | Address-First Job Creation | Accepted | Mar 2026 |
| [0024](./0024-frontend-technology-stack.md) | Frontend Technology Stack | Accepted | Mar 2026 |
| [0025](./0025-dual-status-model.md) | Dual-Status Model (Generic + Workflow) | Accepted | Mar 2026 |
| [0026](./0026-professional-network-connections.md) | Professional Network Connections | Accepted | Mar 2026 |
| [0027](./0027-user-first-registration-rls-isolation.md) | User-First Registration, Multi-Membership, RLS | Accepted | Mar 2026 |
| [0028](./0028-iam-module-restructuring.md) | IAM Module Restructuring | Accepted | Mar 2026 |
| [0029](./0029-phase3-decomposition-membership-entitlements.md) | Phase 3 Decomposition — Membership, Entitlements, Payments | Accepted | Mar 2026 |
| [0030](./0030-workspace-isolation-abstraction.md) | Workspace Abstraction for Data Isolation | Accepted | Mar 2026 |
| [0031](./0031-person-first-feature-gating.md) | Person-First Feature Gating and Subscription Model | Accepted | Mar 2026 |
| [0032](./0032-derived-workspace-access.md) | Derived Workspace Access — No Memberships Table | Accepted | Mar 2026 |
| [0033](./0033-stateless-workspace-context.md) | Stateless Workspace Context via Request Header | Accepted | Mar 2026 |

---

## ADR Index (By Module)

> ADRs that affect multiple modules appear under each relevant module.

### Global / Cross-Cutting

| # | Title | Summary |
|---|-------|---------|
| 0001 | [Layered Architecture](./0001-layered-architecture.md) | Hexagonal-inspired layered architecture |
| 0002 | [Drizzle ORM](./0002-drizzle-orm.md) | Database layer technology choice |
| 0003 | [Container Wiring](./0003-container-wiring.md) | Dependency injection approach |
| 0004 | [Rate Limiting](./0004-rate-limiting-strategy.md) | API rate limiting strategy |
| 0005 | [Hexagonal Migration](./0005-hexagonal-migration-complete.md) | Hexagonal pattern adoption |
| 0008 | [Feature-Centric Slices](./0008-feature-centric-slices.md) | Vertical slice organization |
| 0009 | [Command Center CQRS](./0009-command-center-cqrs.md) | CQRS query service pattern |
| 0010 | [PDA-SDD CI](./0010-pda-sdd-ci-enforcement.md) | Documentation CI enforcement |
| 0017 | [Independent Plumber Tenancy](./0017-independent-plumber-tenancy.md) | Platform supports both companies and solo plumbers |

### CRM Module (Assets / Compliance / Clients)

| # | Title | Summary |
|---|-------|---------|
| 0012 | [Compliance Engine Extensions](./0012-compliance-engine-extensions-and-roster-status.md) | Engine + Programs pattern for compliance obligations |
| 0013 | [BIN Lifecycle](./0013-bin-lifecycle-and-pipeline-arrival-order.md) | Building identity lifecycle across pipelines |
| 0014 | [Version Membership](./0014-version-membership-junction-table.md) | Junction table for versioned building data |
| 0015 | [Event History](./0015-event-history-first-seen-only.md) | First-seen-only event history pattern |
| 0018 | [Client Account vs Requester](./0018-client-account-vs-requester-contact.md) | client_id is account-level, requester is person-level |

### Jobs Module (Engine / Workflows)

| # | Title | Summary |
|---|-------|---------|
| 0007 | [Job Status & Delivery](./ADR-007-job-status-delivery-tracking.md) | Job status semantics and report delivery tracking |
| 0016 | [Job Engine + Workflows](./0016-job-engine-pluggable-workflows.md) | Separates Job aggregate from pluggable workflow types |
| 0018 | [Client Account vs Requester](./0018-client-account-vs-requester-contact.md) | client_id is account-level, requester is person-level |
| 0023 | [Address-First Job Creation](./0023-address-first-job-creation.md) | Jobs created from address text, building resolved lazily |
| 0025 | [Dual-Status Model](./0025-dual-status-model.md) | Generic job_status + workflow-specific workflow_status |

### Tenant & Portfolio

| # | Title | Summary |
|---|-------|---------|
| 0017 | [Independent Plumber Tenancy](./0017-independent-plumber-tenancy.md) | Platform supports both companies and solo plumbers |
| 0020 | [Multi-Tenancy Database Isolation](./0020-multi-tenancy-database-isolation.md) | Partially superseded by ADR-0030 |
| 0021 | [Client-Centric Portfolio](./0021-client-centric-portfolio.md) | Client as primary portfolio entity |
| 0022 | [Building Bookmarks](./0022-building-bookmarks.md) | Save buildings to company portfolio |

### Frontend & API

| # | Title | Summary |
|---|-------|---------|
| 0019 | [camelCase API Serialization](./0019-camelcase-api-serialization.md) | Rust snake_case → JSON camelCase via serde |
| 0024 | [Frontend Technology Stack](./0024-frontend-technology-stack.md) | Vite+React (web), Expo (mobile), no Next.js SSR |

### Infrastructure (Pipelines / Data)

| # | Title | Summary |
|---|-------|---------|
| 0011 | [PAD Ingestion Rust Worker](./0011-pad-ingestion-rust-worker.md) | Rust-based pipeline for PAD data import |

### IAM Module (Identity / Membership / Entitlements)

| # | Title | Summary |
|---|-------|---------| 
| 0017 | [Independent Plumber Tenancy](./0017-independent-plumber-tenancy.md) | Platform supports both companies and solo plumbers |
| 0020 | [Multi-Tenancy Database Isolation](./0020-multi-tenancy-database-isolation.md) | Schema-level tenant isolation strategy |
| 0026 | [Professional Network Connections](./0026-professional-network-connections.md) | User-to-user connections for cross-company collaboration |
| 0027 | [User-First Registration](./0027-user-first-registration-rls-isolation.md) | Person-first identity, multi-company membership, RLS |
| 0028 | [IAM Module Restructuring](./0028-iam-module-restructuring.md) | IAM module structure (People, Company) |
| 0029 | [Phase 3 Decomposition](./0029-phase3-decomposition-membership-entitlements.md) | Separated membership, entitlements, and payments |
| 0030 | [Workspace Abstraction](./0030-workspace-isolation-abstraction.md) | Universal workspace-based data isolation with RLS |
| 0031 | [Person-First Feature Gating](./0031-person-first-feature-gating.md) | Jobs/clients are personal capabilities; two-dimensional subscription |
| 0032 | [Derived Workspace Access](./0032-derived-workspace-access.md) | Workspace access derived from domain relationships, no memberships table |
| 0033 | [Stateless Workspace Context](./0033-stateless-workspace-context.md) | `X-Workspace-Id` header, personal workspace default, portfolio UNION |

---

## What is an ADR?

An Architecture Decision Record captures a significant architectural decision along with its context and consequences. Each ADR describes a decision that has a significant effect on:

- The structure of the codebase
- Non-functional characteristics (performance, security, etc.)
- Dependencies
- Team workflows

## Template

When creating a new ADR, use this template:

```markdown
# ADR-XXXX: [Title]

**Status:** Proposed | Accepted | Deprecated | Superseded  
**Date:** YYYY-MM-DD  
**Deciders:** [Names]

## Context

What is the issue that we're seeing that is motivating this decision?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult because of this change?

### Positive
- ...

### Negative
- ...

## Alternatives Considered

What other options were considered and why were they rejected?
```

## Guidelines

1. **Number sequentially** - Use 4-digit numbers (0001, 0002, etc.)
2. **Keep them immutable** - Don't edit accepted ADRs; supersede them instead
3. **Be concise** - Focus on the decision, not the implementation
4. **Record context** - Future readers need to understand the "why"
