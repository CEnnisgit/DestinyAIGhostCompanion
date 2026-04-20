# Phase 3A: Identity Foundation (Company + User + Workspace + LMP Credential)

> **Status:** 🔲 Not Started
> **Objective:** Create the identity anchor — users, companies, workspaces, and their structural links. Pure domain modeling + data seeding — no auth, no membership lifecycle, no billing.
> **Depends On:** Phase 2 ✅ Complete
> **Branch:** `phase3a/data-foundation`
> **ADRs:** [ADR-0027](../adr/0027-user-first-registration-rls-isolation.md) (user-first registration, multi-membership, RLS), [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md) (phase decomposition), [ADR-0030](../adr/0030-workspace-isolation-abstraction.md) (workspace isolation), [ADR-0031](../adr/0031-person-first-feature-gating.md) (person-first feature gating), [ADR-0032](../adr/0032-derived-workspace-access.md) (derived workspace access)

---

## Why This Sub-Phase Exists

Phase 1.5 created a Company *stub* (just `name + type`) and the Client aggregate. But there are no users, no company profile fields, no workspace isolation layer, and LMP license info is bolted onto each job as raw text columns.

This sub-phase lays the **identity foundation** before any auth, membership lifecycle, or billing work begins. The deliverables here are prerequisites for everything else in Phase 3.

> [!IMPORTANT]
> **Membership in 3A is infrastructure, not domain behavior.** The `company_memberships` junction table is created and seeded here because RLS and auth middleware need it. But membership lifecycle commands (invitation, acceptance, role transitions, primary switching) are deferred to [Phase 3M](./PHASE_3M_MembershipLifecycle.md). See [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md).

---

## Sessions

| Session | Scope | Status |
|---------|-------|--------|
| **Session 1** | Workspaces + Company aggregate + User entity + company_memberships infrastructure | 🔲 Not Started |
| **Session 2** | LmpCredential entity + LL152 migration | 🔲 Not Started |

---

## Domain Concepts

### 1. Workspaces (New — per ADR-0030, ADR-0032)

The universal data isolation boundary. Every piece of tenant-scoped data belongs to exactly one workspace. Workspaces are **thin infrastructure** — id, type, timestamps. All domain behavior lives on User, Company, and Team (Beta).

**Fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | UUID | No | PK |
| `workspace_type` | TEXT | No | `PERSONAL` or `COMPANY` (Beta adds `TEAM`) |
| `created_at` | TIMESTAMPTZ | No | System |

**Key design decisions (per ADR-0030 + ADR-0032):**

- Every user gets a personal workspace on signup
- Every company gets a company workspace on registration
- Workspace access is **derived**, not stored — no `workspace_memberships` table
- Personal workspace: `users.personal_workspace_id`
- Company workspace: `company_memberships` → `companies.workspace_id`
- All tenant-scoped tables (`jobs`, `clients`, `saved_buildings`) will use `workspace_id` as isolation FK

**Spec deliverable:** No standalone spec — workspace is infrastructure documented in ADR-0030/0032

---

### 2. Company Aggregate (Enrich Existing Stub)

**Current state:** `companies(id, name, company_type, created_at, updated_at)` — no phone, no address.

**Fields to add for alpha:**

| Field | Type | Nullable | Source |
|-------|------|----------|--------|
| `phone` | TEXT | Yes | User input |
| `address` | TEXT | Yes | User input |
| `email` | TEXT | Yes | User input |
| `workspace_id` | UUID | No | FK → workspaces. Created automatically with the company. |

> [!NOTE]
> Company registration fields (LLC number, DOB business license, insurance) are deferred to Phase 3D (Profile Enrichment). Alpha companies are seeded — no registration flow.

**Spec deliverable:** `Company_Aggregate.md`

---

### 3. User Aggregate Root (New)

A person who can act in the system. Users exist independently of companies (per ADR-0027). In Phase 3A, the User aggregate is **identity-only** — name (DisplayName VO), email (Email VO), and active status.

**Fields:**

| Field | Type / VO | Nullable | Description |
|-------|-----------|----------|-------------|
| `id` | UUID | No | PK |
| `name` | DisplayName (VO) | No | Display name. Trimmed, non-empty. |
| `email` | Email (VO) | No | Login identity (globally unique). Lowercased, validated. |
| `personal_workspace_id` | UUID | No | FK → workspaces. Created automatically on signup. |
| `is_active` | BOOL | No | Default true. False = deactivated. |
| `created_at` | TIMESTAMPTZ | No | System |
| `updated_at` | TIMESTAMPTZ | No | System |

**Key decisions (per ADR-0027 + ADR-0029 + ADR-0031):**

- ❌ No `company_id` on users — relationship goes through `company_memberships`
- ❌ No `role` on users — role is per-membership, not per-user
- ❌ No membership management commands — deferred to Phase 3M
- ❌ No `subscription_tier` — deferred to Phase 3N
- ✅ `personal_workspace_id` — every user gets a personal workspace (ADR-0030)

**Spec deliverable:** [User_Aggregate.md](../2-during-implementation/DDD/ModuleDesign/IAM/People/User_Aggregate.md) (v3.0.0)

---

### 4. Company Memberships Infrastructure (New — per ADR-0027)

The junction table linking users to companies. **Structural infrastructure in 3A — not a domain entity with lifecycle behavior.**

**Fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | UUID | No | PK |
| `user_id` | UUID | No | FK → users |
| `company_id` | UUID | No | FK → companies |
| `role` | TEXT | No | `ADMIN` or `TECHNICIAN` (per SFR-SRAZ) |
| `is_primary` | BOOL | No | Default false. User's default company context. |
| `joined_at` | TIMESTAMPTZ | No | System |

**Constraints:**

- `UNIQUE (user_id, company_id)` — one membership per user-company pair
- `CHECK (role IN ('ADMIN', 'TECHNICIAN'))`

**Role definitions (from SFR-SRAZ):**

| Role | Description | Alpha Users |
|------|-------------|-------------|
| `ADMIN` | Company owner. Can create jobs, dispatch, review, manage users. | User A, User B |
| `TECHNICIAN` | Field plumber. Can view assigned jobs, submit findings. | User B's employees |

**What middleware uses this table for (3B/3C.1):**

- Resolve which companies a user can access
- Derive company workspace access via `companies.workspace_id` (ADR-0032)
- Set `app.workspace_id` PostgreSQL session variable for RLS (ADR-0030)
- Check role for admin vs. technician permission enforcement

**What this table does NOT do in Phase 3A:**

- No invitation/acceptance flow (Phase 3M)
- No lifecycle commands in domain model (Phase 3M)
- No status field (INVITED/ACTIVE/SUSPENDED) (Phase 3M)
- No primary context switching UX (Phase 3M)

> [!IMPORTANT]
> For alpha, both real users (A and B) are `ADMIN` with exactly one membership each. Data is seeded — no domain behavior needed. Full membership lifecycle is designed in [Phase 3M](./PHASE_3M_MembershipLifecycle.md).

**Spec deliverable:** [CompanyMembership.md](../2-during-implementation/DDD/ModuleDesign/IAM/People/CompanyMembership.md) (v3.0.0 — schema spec)

---

### 5. LMP Credential Entity (New — Session 2)

A reusable "license card" representing an LMP's authority. Attached to the **user** who holds the license (per ADR-0027 research: "LMP license belongs to the person, not the company").

**Domain rationale:**

- A QI (like User A) may work under multiple LMPs
- Each LL152 job needs to know which LMP authorized it
- The LMP may not be a system user (external relationship)
- LMP info is needed on GPS1/GPS2 reports and future job type extensions

**Fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | UUID | No | PK |
| `created_by_user_id` | UUID | No | FK → users (who entered the info) |
| `lmp_name` | TEXT | No | Full name of the LMP |
| `license_number` | TEXT | No | LMP license number |
| `license_expiry` | DATE | Yes | When the license expires |
| `phone` | TEXT | Yes | LMP contact phone |
| `email` | TEXT | Yes | LMP contact email |
| `is_active` | BOOL | No | Default true. False = expired/revoked. |
| `created_at` | TIMESTAMPTZ | No | System |
| `updated_at` | TIMESTAMPTZ | No | System |

**Key change:** No `company_id` on lmp_credentials — the credential belongs to the user who created it. Company-scoped visibility comes through the user's memberships.

**Sharing model (future):** Via Phase 3E Connections — an LMP can share their credential card with connected QIs.

**Spec deliverable:** `LmpCredential_Spec.md`

---

## Implementation Plan — Session 1

### Domain Layer (`crates/pcd-domain/`)

| File | Action |
|------|--------|
| `src/iam/workspace.rs` | New — Workspace entity (thin: id, type) |
| `src/iam/user.rs` | New — User aggregate root (identity-only, includes `personal_workspace_id`) |
| `src/iam/email.rs` | New — Email value object |
| `src/iam/display_name.rs` | New — DisplayName value object |
| `src/iam/mod.rs` | New — IAM module |
| `src/company/mod.rs` | New module — Company aggregate with enriched fields + `workspace_id` |
| `src/company/repository.rs` | New — CompanyRepository trait |
| `src/lib.rs` | Update — add `pub mod iam; pub mod company;` |

### DB Layer (`crates/pcd-db/`)

| File | Action |
|------|--------|
| `src/iam/workspace.rs` | New — ensure_workspaces_table |
| `src/company/mod.rs` | New — SqlxCompanyRepository + ensure_companies_table |
| `src/iam/mod.rs` | New — SqlxUserRepository |

### API Layer (`crates/pcd-api/`)

| File | Action |
|------|--------|
| `src/routes/company.rs` | New — `GET /api/company/:id`, `PATCH /api/company/:id` |
| `src/routes/users.rs` | New — `GET /api/users` (read-only for 3A — management API in 3D) |

### Schema (Session 1)

```sql
-- NEW: workspaces (universal isolation boundary — ADR-0030)
CREATE TABLE IF NOT EXISTS workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_type  TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_workspace_type CHECK (workspace_type IN ('PERSONAL', 'COMPANY'))
);

-- Enrich companies (add workspace reference)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id);

-- New: users (with personal workspace FK)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    personal_workspace_id UUID NOT NULL REFERENCES workspaces(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_user_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT chk_user_name_trimmed CHECK (name = trim(name)),
    CONSTRAINT chk_user_name_max_length CHECK (length(name) <= 200),
    CONSTRAINT uq_user_email UNIQUE (email),
    CONSTRAINT chk_user_email_lowercase CHECK (email = lower(email)),
    CONSTRAINT chk_user_email_max_length CHECK (length(email) <= 254)
);

-- New: company_memberships (infrastructure for RLS + auth context)
CREATE TABLE IF NOT EXISTS company_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    role TEXT NOT NULL DEFAULT 'TECHNICIAN',
    is_primary BOOLEAN NOT NULL DEFAULT false,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, company_id),
    CONSTRAINT chk_membership_role CHECK (role IN ('ADMIN', 'TECHNICIAN'))
);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON company_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_company ON company_memberships(company_id);
```

### Seeding (Session 1)

```sql
-- For each alpha company: create a company workspace first
INSERT INTO workspaces (id, workspace_type) VALUES
    ('{{company_a_ws_id}}', 'COMPANY'),
    ('{{company_b_ws_id}}', 'COMPANY');

-- Link companies to their workspaces
UPDATE companies SET workspace_id = '{{company_a_ws_id}}' WHERE id = '{{company_a_id}}';
UPDATE companies SET workspace_id = '{{company_b_ws_id}}' WHERE id = '{{company_b_id}}';

-- For each alpha user: create a personal workspace first
INSERT INTO workspaces (id, workspace_type) VALUES
    ('{{user_a_personal_ws_id}}', 'PERSONAL'),
    ('{{user_b_personal_ws_id}}', 'PERSONAL');

-- Create users with personal workspace FKs
INSERT INTO users (id, name, email, personal_workspace_id) VALUES
    ('{{user_a_id}}', 'User A', 'usera@example.com', '{{user_a_personal_ws_id}}'),
    ('{{user_b_id}}', 'User B', 'userb@example.com', '{{user_b_personal_ws_id}}');

-- Create company memberships
INSERT INTO company_memberships (user_id, company_id, role, is_primary) VALUES
    ('{{user_a_id}}', '{{company_a_id}}', 'ADMIN', true),
    ('{{user_b_id}}', '{{company_b_id}}', 'ADMIN', true);
```

> [!NOTE]
> No `workspace_memberships` table needed — workspace access is derived from `users.personal_workspace_id` and `company_memberships` → `companies.workspace_id` (ADR-0032).

---

## Implementation Plan — Session 2

### Domain Layer

| File | Action |
|------|--------|
| `src/iam/lmp_credential.rs` | New — LmpCredential entity |
| `src/iam/repository.rs` | Add LmpCredentialRepository trait |

### DB Layer

| File | Action |
|------|--------|
| `src/iam/lmp_credentials.rs` | New — SqlxLmpCredentialRepository |

### API Layer

| File | Action |
|------|--------|
| `src/routes/lmp_credentials.rs` | New — CRUD for LMP credential cards |
| `src/routes/ll152.rs` | Update — reference `lmp_credential_id` instead of text |

### Schema (Session 2)

```sql
-- New: lmp_credentials (user-owned, not company-owned)
CREATE TABLE IF NOT EXISTS lmp_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    lmp_name TEXT NOT NULL,
    license_number TEXT NOT NULL,
    license_expiry DATE,
    phone TEXT,
    email TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_lmp_creds_user ON lmp_credentials(created_by_user_id);

-- Update ll152_job_details: add FK to credential
ALTER TABLE ll152_job_details ADD COLUMN IF NOT EXISTS lmp_credential_id UUID REFERENCES lmp_credentials(id);
-- Note: old lmp_name and lmp_license_number text columns remain until data migrated
```

---

## Exit Criteria

### Session 1

- [ ] `workspaces` table exists with type constraint
- [ ] Company aggregate has real profile fields (phone, address, email) + `workspace_id` FK
- [ ] `users` table exists with Email VO + DisplayName VO constraints + `personal_workspace_id` FK
- [ ] `company_memberships` table exists as infrastructure (seeded, no domain behavior)
- [ ] Domain tests pass for Company, User (identity-only), Workspace
- [ ] API endpoints for company profile and user listing (read-only)
- [ ] Alpha data seeded: workspaces + companies + users + memberships

### Session 2

- [ ] `lmp_credentials` table exists (user-owned)
- [ ] `ll152_job_details` references `lmp_credential_id`
- [ ] CRUD API for LMP credential cards
- [ ] Domain tests pass for LmpCredential
- [ ] Aggregate specs written: Company, User (v3.0.0 ✅), LmpCredential

---

## Research Questions

- [x] How many alpha users? → 2 owners + User B's 2-4 employees *(from ALPHA_PERSONAS_AND_SCOPE.md)*
- [x] What roles? → ADMIN + TECHNICIAN *(from SFR-SRAZ)*
- [x] LMP credential: user-owned card, attachable to jobs *(decided in conversation, ADR-0027)*
- [x] User-Company relationship? → Junction table, not direct FK *(ADR-0027)*
- [x] Tenant isolation? → Workspace abstraction with RLS *(ADR-0030)*
- [x] Workspace access model? → Derived from domain relationships, no memberships table *(ADR-0032)*
- [x] Feature gating model? → Person-first, jobs/clients not company-gated *(ADR-0031)*
- [x] Membership lifecycle scope? → Infrastructure in 3A, domain behavior in 3M *(ADR-0029)*
- [ ] Company registration fields (LLC #, insurance)? → Deferred to Phase 3D
