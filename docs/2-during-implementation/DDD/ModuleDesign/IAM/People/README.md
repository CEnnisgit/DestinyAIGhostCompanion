# IAM / People Sub-Module

> **Scope:** Person identity and company membership infrastructure.

## Specs

| Document | Type | Phase | Description |
| :--- | :--- | :--- | :--- |
| [User_Aggregate.md](./User_Aggregate.md) | Aggregate Root | 3A | Person identity — name (VO), email (VO), active status |
| [CompanyMembership.md](./CompanyMembership.md) | Schema (infrastructure) | 3A infra / 3M domain | Junction table linking users to companies. Infrastructure-only in 3A; full entity in 3M. |

## Value Objects

| VO | Spec | Used By |
| :--- | :--- | :--- |
| Email | [Email_VO_Spec.md](./ValueObjects/Email/Email_VO_Spec.md) | `User.email` — login identity |
| DisplayName | [DisplayName_VO_Spec.md](./ValueObjects/DisplayName/DisplayName_VO_Spec.md) | `User.name` — human-readable label |

## Phase Boundary

Per [ADR-0029](../../../../adr/0029-phase3-decomposition-membership-entitlements.md):

- **Phase 3A** — User identity (this spec) + `company_memberships` table as infrastructure
- **Phase 3M** — Membership lifecycle (invitation, acceptance, role transitions, primary context switching)
- **Phase 3N** — Entitlements (person tier, company tier, feature gating)
