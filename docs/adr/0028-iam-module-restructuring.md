# ADR-0028: IAM Module — Identity & Access Management Restructuring

**Status:** Accepted
**Date:** 2026-03-29
**Deciders:** Marcus, AI Pair Programming

## Context

PCD's module structure has evolved organically through four phases. The current state has naming and scoping problems that will cause drift if not resolved before Phase 3A implementation.

### The Problem

The Rust `tenant` module was created in Phase 1.5 as a home for "company-scoped operational entities" — Client and SavedBuilding. The word "tenant" was inherited from the retired `TenantAsset(FirmID, BIN)` concept ([ADR-0021](./0021-client-centric-portfolio.md)), even after the entity it described was superseded.

Phase 3A introduces User, Company (enriched from stub), CompanyMembership, and LmpCredential. These are **identity and access** concepts — fundamentally different from operational entities like Client and Job. They need their own module, and the existing `tenant` module's name and scope need clarification.

### What exists today

| Rust Module | Contains | ADRs |
|---|---|---|
| `crm` | Building (global reference data) | — |
| `tenant` | Client, SavedBuilding, Company (stub) | 0017, 0020, 0021, 0022 |
| `jobs` | Job aggregate | 0016 |
| `ll152` | LL152 workflow details, findings, photos | — |

### What Phase 3A adds

| Entity | What it is | ADRs |
|---|---|---|
| User | A person — the durable identity | 0027 |
| Company (enriched) | The tenant container — isolation boundary | 0017, 0027 |
| CompanyMembership | Links a user to a company with a role | 0027 |
| LmpCredential | User-owned professional license card | 0027 |

## Decision: Create an `iam` Module for Identity & Access

### 1. New `iam` module

A new Rust module `iam` (Identity & Access Management) is created to hold all identity and relationship entities:

```
pcd-domain/src/iam/
├── mod.rs
├── user.rs              ← User entity (Person)
├── company.rs           ← Company aggregate (Tenant container)
├── membership.rs        ← CompanyMembership + MembershipRole
├── lmp_credential.rs    ← LmpCredential entity (Session 2)
├── repository.rs        ← UserRepository, CompanyRepository, etc.
└── tests.rs
```

**What `iam` owns:**
- Who you are (User)
- What organizations exist (Company)
- How people relate to organizations (CompanyMembership)
- What professional credentials a person holds (LmpCredential)

**What `iam` does NOT own:**
- Authentication mechanics (password hash, JWT, sessions) — Phase 3B
- Authorization rules (RBAC policies, permissions) — Phase 3C
- Operational data scoped to a company (jobs, clients, saved buildings)

### 2. Existing `tenant` module is unchanged (for now)

Client and SavedBuilding remain in the `tenant` Rust module. They are company-scoped operational entities — "things a company works with" — not identity concepts.

The Company stub currently in `tenant` (the `companies` table and its `ensure_companies_table` function) will be **migrated** to `iam` during Phase 3A implementation. After migration, `tenant` contains only Client and SavedBuilding.

> **Future consideration:** `tenant` may eventually be renamed to `crm_operations` or merged into `crm` to align with the DDD documentation structure (`CRM/Operations`). This is a separate decision, not blocked by Phase 3A.

### 3. DDD documentation folder matches Rust module

The documentation folder name **must** match the Rust module name. This is the single-name rule that prevents drift.

| Rust module | DDD docs folder | After-implementation docs |
|---|---|---|
| `iam` | `ModuleDesign/IAM/` | `Modules/iam/` |
| `tenant` | `ModuleDesign/CRM/Operations/` + `CRM/Clients/` | `Modules/tenant/` |
| `jobs` | `ModuleDesign/Jobs/` | `Modules/jobs/` |
| `crm` | `ModuleDesign/CRM/Assets/` | `Modules/crm/` |

**Action:** Rename the existing `ModuleDesign/Users/` folder to `ModuleDesign/IAM/`. All specs created today (User_Profile, Company_Aggregate, etc.) move with it.

## Why "IAM" and not other names

| Candidate | Verdict |
|---|---|
| `users` | Doesn't encompass Company. "Company" inside a module called "users" is a semantic stretch. |
| `tenant` | Already taken. Also, "tenant" means Company specifically (the isolation boundary), not the broader identity layer. |
| `identity` | Good but less standard. Doesn't convey the "access" dimension (memberships, roles). |
| `org` | Short but ambiguous. Could mean the GitHub org, the company, or organizational structure. |
| `iam` | Industry-standard term. Clearly scoped: identity (who) + access (how they connect to tenants). Not overloaded in this codebase. |

## Alternatives Considered

### Keep everything in `tenant`

Move User, Membership, and LmpCredential into the existing `tenant` module alongside Client and SavedBuilding.

**Rejected.** The `tenant` module would become a grab-bag of unrelated entities. Client (who commissions work) and User (who performs work) have different lifecycles, different aggregate boundaries, and different reasons to change. Mixing them violates the single-responsibility principle at the module level.

### Split into `users` + `companies`

Two separate Rust modules — one for person entities, one for company entities.

**Rejected.** User and Company are tightly coupled through CompanyMembership. Splitting them across modules would force cross-module coordination for every membership operation. They should live together.

## Implications

### For Phase 3A Implementation

1. Create `crates/pcd-domain/src/iam/` with User, Company, Membership, LmpCredential
2. Create `crates/pcd-db/src/iam/` with SQLx implementations
3. Migrate the Company stub out of `tenant` into `iam`
4. `tenant` module continues to work unchanged (Client + SavedBuilding)

### For DDD Documentation

1. Rename `ModuleDesign/Users/` → `ModuleDesign/IAM/`
2. Update `ModuleDesign/README.md` module index
3. All existing specs (User_Profile, Company_Aggregate, etc.) keep their content, just move

### For Existing Code

- No changes to `tenant`, `jobs`, `ll152`, or `crm` modules
- No database schema changes (this ADR is about module structure, not data)
- API routes for IAM entities will be under `/api/iam/` or `/api/users/` (route naming is a separate decision)

## References

- [ADR-0017: Independent Plumber Tenancy](./0017-independent-plumber-tenancy.md) — *partially superseded by ADR-0027*
- [ADR-0021: Client-Centric Portfolio](./0021-client-centric-portfolio.md) — why Client is operational, not identity
- [ADR-0027: User-First Registration](./0027-user-first-registration-rls-isolation.md) — the identity model this module implements
- [Tenant Portfolio Research](../2-during-implementation/DDD/ModuleDesign/CRM/Operations/Research/TENANT_PORTFOLIO_RESEARCH.md) — historical context on "tenant" naming
