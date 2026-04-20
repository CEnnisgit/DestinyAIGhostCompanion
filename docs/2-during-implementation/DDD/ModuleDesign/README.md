# Module Design

> **Parent:** [DDD](../README.md)
> **Roadmap:** [Domain-First Roadmap](../../../roadmap/DOMAIN_FIRST_ROADMAP.md)

Per-module documentation following PDA-SDD structure:
- Responsibilities
- Structure (Class Diagrams)
- Interactions (Sequence Diagrams)
- Algorithms
- Data Structures

## Modules (Pilot Scope)

| Module | Description | Spec Depth | Roadmap Phase |
|--------|-------------|------------|---------------|
| **[Auth](./Auth/README.md)** | Authentication and identity verification | Stub | Phase 3B |
| **[CRM](./CRM/README.md)** | External world (buildings, clients, obligations) | ✅ Deep (Assets + Clients + Compliance) | Phase 0 ✅ / Phase 1.5 ✅ |
| **[IAM](./IAM/README.md)** | Identity & access (users, companies, memberships, credentials) | In Progress | Phase 3A |
| **[Jobs](./Jobs/README.md)** | The work (job lifecycle + workflows) | ✅ Deep | Phase 1 ✅ / Phase 2 ✅ |
| **[SharedKernel](./SharedKernel/README.md)** | Shared config and utilities | Stable | — |
| **[Storage](./Storage/README.md)** | File storage | Stub | Phase 4 |
| **[Reporting](./Reporting/README.md)** | GPS1/GPS2 PDF generation | Stub | Phase 4 |
| **[Notification](./Notification/README.md)** | Email/SMS delivery | Stub | Phase 4 |
| **[Presentation](./Presentation/README.md)** | Web dashboard (the UI) | ✅ Prototype v3 | All Phases |

## Key ADRs

- [ADR-0012](../../adr/0012-compliance-engine-extensions-and-roster-status.md) — Compliance Engine + Extensions pattern
- [ADR-0016](../../adr/0016-job-engine-pluggable-workflows.md) — Job Engine + Pluggable Workflows pattern
- [ADR-0027](../../adr/0027-user-first-registration-rls-isolation.md) — User-First Registration + RLS Isolation
- [ADR-0028](../../adr/0028-iam-module-restructuring.md) — IAM Module Restructuring
