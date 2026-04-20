# Phase 3A: Rust Module Structure

> **Purpose:** Agree on exact file locations before writing any code.
> Maps Rust modules → DDD specs. Shows current state (post-reorg), Session 0 changes, and Sessions 1-3 additions.
>
> **Updated:** 2026-04-01 — Reflects completed module reorg (`phase3a/data-foundation` branch).

---

## Current State (Post-Reorg)

```
crates/pcd-domain/src/
├── lib.rs                    (pub mod: shared, iam, operations, directory, workflows)
├── shared/                   ← Shared Kernel (ADR-0030) — NEW in reorg
│   ├── mod.rs
│   └── workspace.rs          Workspace, WorkspaceId, WorkspaceType
├── iam/                      ← EMPTY SHELL — Phase 3A entities go here
│   └── mod.rs                (doc comments reference ADRs 0028/0031/0032)
├── operations/               ← Merged from jobs/ + tenant/ in reorg
│   ├── mod.rs                (re-exports Job + Client + SavedBuilding)
│   ├── job.rs                ⚠️ has company_id
│   ├── job_number.rs
│   ├── job_status.rs
│   ├── job_type.rs
│   ├── priority.rs
│   ├── source_kind.rs
│   ├── events.rs             ⚠️ has company_id
│   ├── job_repository.rs     ⚠️ has company_id (was jobs/repository.rs)
│   ├── job_tests.rs          ⚠️ has company_id (was jobs/tests.rs)
│   ├── client.rs             ⚠️ has company_id (was tenant/client.rs)
│   ├── saved_building.rs     ⚠️ has company_id (was tenant/saved_building.rs)
│   ├── client_repository.rs  ⚠️ has company_id (was tenant/repository.rs)
│   └── client_tests.rs       ⚠️ has company_id (was tenant/tests.rs)
├── directory/                ← Renamed from crm/ in reorg
│   ├── mod.rs
│   ├── building.rs
│   ├── compliance_obligation.rs
│   └── import_run.rs
└── workflows/                ← Parent module — NEW in reorg
    └── ll152/                ← Nested from top-level ll152/ in reorg
        ├── mod.rs
        ├── details.rs
        ├── findings.rs
        ├── photos.rs
        ├── branch.rs
        ├── events.rs
        ├── validation.rs
        ├── workflow_status.rs
        └── tests.rs

crates/pcd-db/src/
├── lib.rs                    (pub mod: bootstrap, directory, iam, operations, workflows)
├── bootstrap.rs              ← NEW — ensure_schema() entry point for all table init
├── iam/                      ← EMPTY SHELL
│   └── mod.rs
├── operations/               ← Merged from jobs/ + tenant/ in reorg
│   ├── mod.rs                (re-exports SqlxJobRepo, SqlxClientRepo, SqlxSavedBuildingRepo)
│   ├── jobs.rs               ⚠️ has company_id in SQL (was jobs/mod.rs)
│   ├── clients.rs            ⚠️ has company_id in SQL (was tenant/clients.rs)
│   └── saved_buildings.rs    ⚠️ has company_id in SQL (was tenant/saved_buildings.rs)
├── directory/                ← Renamed from crm/ in reorg
│   ├── mod.rs                (SqlxDirectoryRepository — was SqlxCrmRepository)
│   ├── buildings.rs
│   ├── anomalies.rs
│   ├── import_runs.rs
│   ├── obligations.rs
│   ├── timeline.rs
│   └── types.rs
└── workflows/
    └── ll152/
        ├── mod.rs            (ensure_ll152_tables — creates companies table!)
        ├── details.rs
        ├── findings.rs
        └── photos.rs

crates/pcd-api/src/
├── main.rs                   (composition root — bootstrap, repos, router wiring)
└── routes/
    ├── mod.rs                (pub mod: clients, directory, jobs, saved_buildings, workflows)
    ├── clients.rs            ⚠️ hardcoded company_id (was tenant.rs — split in review)
    ├── saved_buildings.rs    ⚠️ hardcoded company_id (was tenant.rs — split in review)
    ├── directory.rs          (was crm.rs; DirectoryState — was CrmState)
    ├── jobs.rs               ⚠️ hardcoded company_id
    └── workflows/
        ├── mod.rs
        └── ll152.rs          ⚠️ hardcoded DEV_USER_ID
```

> ⚠️ = Files that Session 0 modifies (company_id → workspace_id)

---

## After Session 0: company_id → workspace_id

**No new files.** Same structure, but every ⚠️ above has its `company_id` fields/params/SQL renamed to `workspace_id`.

Additionally, `pcd-db/src/workflows/ll152/mod.rs` (which currently creates the `companies` table) gets a new `workspaces` table created before `companies`, and `companies` gets a `workspace_id` FK.

---

## After Sessions 1-3: IAM Module Populated

```
crates/pcd-domain/src/
├── lib.rs                    (unchanged — iam already declared)
├── shared/                   (unchanged — workspace.rs already exists)
├── iam/                      ← POPULATED (was empty shell)
│   ├── mod.rs                (sub-module declarations + re-exports)
│   ├── user.rs               (User aggregate root)
│   ├── email.rs              (Email value object)
│   ├── display_name.rs       (DisplayName value object)
│   ├── company.rs            (Company aggregate — enriched)
│   ├── membership.rs         (CompanyMembership struct + MembershipRole enum)
│   ├── lmp_credential.rs     (LmpCredential entity — Session 2)
│   ├── repository.rs         (trait: UserRepo, CompanyRepo, MembershipRepo, LmpCredentialRepo)
│   └── tests.rs              (unit tests for all IAM domain types)
├── operations/               (unchanged — workspace_id from S0)
├── directory/                (unchanged)
└── workflows/                (unchanged)

crates/pcd-db/src/
├── lib.rs                    (unchanged — iam already declared)
├── bootstrap.rs              (updated — add ensure_iam_tables call)
├── iam/                      ← POPULATED (was empty shell)
│   ├── mod.rs                (ensure_iam_tables + re-exports)
│   ├── users.rs              (SqlxUserRepository)
│   ├── companies.rs          (SqlxCompanyRepository — enriched queries)
│   ├── memberships.rs        (SqlxCompanyMembershipRepository)
│   └── lmp_credentials.rs    (SqlxLmpCredentialRepository — Session 2)
├── operations/               (unchanged — workspace_id from S0)
├── directory/                (unchanged)
└── workflows/                (unchanged)

crates/pcd-api/src/
├── main.rs                   (add: iam route wiring)
└── routes/
    ├── mod.rs                (add: pub mod users; pub mod company; pub mod lmp_credentials;)
    ├── clients.rs            (unchanged — workspace_id from S0)
    ├── saved_buildings.rs    (unchanged — workspace_id from S0)
    ├── directory.rs          (unchanged)
    ├── jobs.rs               (unchanged — workspace_id from S0)
    ├── users.rs              ← NEW (GET /api/users, GET /api/users/{id})
    ├── company.rs            ← NEW (GET /api/company/{id}, PATCH /api/company/{id})
    ├── lmp_credentials.rs    ← NEW (Session 2: CRUD API)
    └── workflows/
        ├── mod.rs
        └── ll152.rs          (Session 2: add lmp_credential_id FK)
```

---

## DDD → Rust Module Mapping

| DDD ModuleDesign Path | Rust Module | Spec File |
|---|---|---|
| `IAM/People/User_Aggregate.md` | `iam::user` | [User_Aggregate.md](file:///c:/github/pcd/docs/2-during-implementation/DDD/ModuleDesign/IAM/People/User_Aggregate.md) |
| `IAM/People/ValueObjects/Email/` | `iam::email` | [Email_VO_Spec.md](file:///c:/github/pcd/docs/2-during-implementation/DDD/ModuleDesign/IAM/People/ValueObjects/Email/Email_VO_Spec.md) |
| `IAM/People/ValueObjects/DisplayName/` | `iam::display_name` | [DisplayName_VO_Spec.md](file:///c:/github/pcd/docs/2-during-implementation/DDD/ModuleDesign/IAM/People/ValueObjects/DisplayName/DisplayName_VO_Spec.md) |
| `IAM/People/CompanyMembership.md` | `iam::membership` | [CompanyMembership.md](file:///c:/github/pcd/docs/2-during-implementation/DDD/ModuleDesign/IAM/People/CompanyMembership.md) |
| `IAM/Company/Company_Aggregate.md` | `iam::company` | [Company_Aggregate.md](file:///c:/github/pcd/docs/2-during-implementation/DDD/ModuleDesign/IAM/Company/Company_Aggregate.md) |
| `IAM/LmpCredential/LmpCredential_Spec.md` | `iam::lmp_credential` | [LmpCredential_Spec.md](file:///c:/github/pcd/docs/2-during-implementation/DDD/ModuleDesign/IAM/LmpCredential/LmpCredential_Spec.md) |
| *(infrastructure — ADR-0030)* | `shared::workspace` | Already implemented in reorg |
| `Jobs/Engine/Job_Aggregate.md` | `operations::job` | [Job_Aggregate.md](file:///c:/github/pcd/docs/2-during-implementation/DDD/ModuleDesign/Jobs/Engine/Job_Aggregate.md) |
| `CRM/Clients/Client_Aggregate.md` | `operations::client` | Implemented (Phase 1.5) |
| `CRM/Assets/Building/` | `directory::building` | Implemented (Phase 0) |
| `Jobs/Workflows/LL152/` | `workflows::ll152::*` | Implemented (Phase 2) |

---

## Open Design Question: `companies` Table Creation

Currently, the `companies` table is created inside `pcd-db/src/workflows/ll152/mod.rs::ensure_ll152_tables()`. This was a pragmatic shortcut from Phase 1.5.

**Options:**
- **A)** Move `CREATE TABLE companies` into `pcd-db/src/iam/mod.rs::ensure_iam_tables()` where it logically belongs. Update `ensure_ll152_tables` to only ALTER (add LMP columns).
- **B)** Leave it in `ll152` and just add new columns from `iam`. More scattered but less churn.

**Recommendation:** Option A — move it. The Company aggregate now lives in IAM per ADR-0028. The table creation should follow the domain module. The centralized `bootstrap.rs` makes ordering easy: call `ensure_iam_tables()` before `ensure_ll152_tables()`.

---

## Naming Alignment Summary

| Rust Module | DDD Module | Aligned? |
|---|---|---|
| `shared` | *(infrastructure — ADR-0030)* | ✅ |
| `iam` | IAM/ | ✅ |
| `operations` | Jobs/Engine + CRM/Clients | ✅ (workspace-scoped portfolio) |
| `directory` | CRM/Assets | ✅ (global building catalog) |
| `workflows::ll152` | Jobs/Workflows/LL152 | ✅ |
| `auth` (Phase 3B) | Auth/ | ✅ (planned) |

> All module names now align with their DDD bounded contexts. No cosmetic mismatches remain.
