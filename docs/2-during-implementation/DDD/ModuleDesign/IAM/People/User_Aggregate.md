# User Aggregate Specification

**Module:** `IAM`
**Sub-Module:** `People`
**Source of Truth:** `crates/pcd-domain/src/iam/user.rs` (Phase 3A, not yet implemented)
**Version:** 3.0.0 (Identity-only — membership deferred to Phase 3M per ADR-0029)
**ADRs:** [ADR-0027](../../../../adr/0027-user-first-registration-rls-isolation.md), [ADR-0028](../../../../adr/0028-iam-module-restructuring.md), [ADR-0029](../../../../adr/0029-phase3-decomposition-membership-entitlements.md), [ADR-0030](../../../../adr/0030-workspace-isolation-abstraction.md), [ADR-0031](../../../../adr/0031-person-first-feature-gating.md), [ADR-0032](../../../../adr/0032-derived-workspace-access.md)

---

## 1. Objective

The User aggregate represents **a person who can act in the system**. It is the anchor identity — a person exists independently of any company and can belong to multiple companies with different roles in each.

It answers:

- Who is performing this action?
- What is their name and contact email?
- Are they allowed to log in?

It does **not** answer:

- Which workspace context they're operating in right now (resolved by auth middleware from membership data + personal workspace)
- What role they have (that's CompanyMembership — role is per-company, not per-user)
- Whether they're authenticated (Phase 3B Auth)
- What permissions they have (Phase 3C Authorization)
- What features they can access (Phase 3N Entitlements)
- Who they're connected to (Phase 3E Professional Network)

---

## 2. Why This Is an Aggregate Root

Even without membership management commands (deferred to Phase 3M), User is an aggregate root because:

- It enforces identity invariants (name non-empty, email valid and unique)
- It manages its own active/deactivated lifecycle
- It will own CompanyMembership as a child entity when Phase 3M expands the aggregate boundary

In Phase 3A, the aggregate boundary is drawn tightly around **identity only**. Phase 3M will expand it to include membership lifecycle management.

---

## 3. Core Decisions

### 3.1 User-First Registration (ADR-0027)

A person creates an account first, then creates or joins companies:

- Users exist independently of companies
- A free-tier user has zero memberships — they can create jobs, manage clients, and hand off work (ADR-0031)
- A user can belong to multiple companies simultaneously

### 3.2 No Role on User

The ADMIN/TECHNICIAN role lives on `CompanyMembership`, not on the User. Marcus's father is ADMIN of his own LLC but TECHNICIAN under Danny's company. Same person, different roles.

### 3.3 Email as Identity

Email is the user's login identity. It is globally unique across the system — one account per email address. Email uses the `Email` value object, which enforces format, lowercasing, and trimming at construction time. See [Email VO Spec](./ValueObjects/Email/Email_VO_Spec.md).

### 3.4 Seed-Only Creation (Current)

User accounts are currently created via seed scripts. No registration endpoint, no password storage (deferred to Phase 3B). This sub-phase creates only the **data model**, not auth infrastructure.

### 3.5 Membership Is Infrastructure in 3A (ADR-0029)

The `company_memberships` junction table exists in Phase 3A as **structural infrastructure** — it is needed for RLS tenant isolation and company context resolution. However, no membership lifecycle behavior (invitation, acceptance, role transitions, primary switching) is modeled in the domain layer until Phase 3M.

Data is seeded. The table is queried by auth middleware. The domain model does not manage it.

---

## 4. Attributes

| Field                    | Type / VO              | Nullable | Description                                    | Source     |
| :----------------------- | :--------------------- | :------- | :--------------------------------------------- | :--------- |
| `id`                     | UUID                   | No       | PK                                             | Generated  |
| `name`                   | DisplayName (VO)       | No       | Display name (full name). Trimmed.             | User input |
| `email`                  | Email (VO)             | No       | Login identity. Globally unique. Lowercased.   | User input |
| `personal_workspace_id`  | UUID                   | No       | FK → workspaces. Created on signup. (ADR-0030) | System     |
| `is_active`              | BOOLEAN                | No       | Default: true. False = deactivated.            | Admin action |
| `created_at`             | TIMESTAMPTZ            | No       | When the account was created                   | System     |
| `updated_at`             | TIMESTAMPTZ            | No       | When the account was last modified             | System     |

### PII Classification

| Field   | PII? | Sensitivity          | Retention Policy                                         |
| :------ | :--- | :------------------- | :------------------------------------------------------- |
| `name`  | Yes  | Medium               | Retained while account exists. Anonymized on deletion request. |
| `email` | Yes  | High (login identity) | Retained while account exists. Purged on deletion request.     |

### Fields NOT included (with rationale)

| Rejected Field      | Reason                                                                                   | Revisited When             |
| :------------------- | :--------------------------------------------------------------------------------------- | :------------------------- |
| `company_id`        | Relationship goes through `company_memberships` junction table (ADR-0027)                | Never — architectural      |
| `role`              | Role is per-membership, not per-user                                                     | Never — architectural      |
| `password_hash`     | Authentication concern, not identity                                                     | Phase 3B                   |
| `phone`             | Extended profile field, not core identity                                                 | Phase 3D                   |
| `avatar_url`        | Extended profile field                                                                   | Phase 3D                   |
| `subscription_tier` | Entitlement concern, not identity (ADR-0029)                                             | Phase 3N                   |

---

## 5. Value Objects

| VO              | Spec                                                                    | Used On        | Purpose                             |
| :-------------- | :---------------------------------------------------------------------- | :------------- | :----------------------------------- |
| `Email`         | [Email_VO_Spec.md](./ValueObjects/Email/Email_VO_Spec.md)              | `User.email`   | Validated, lowercased, trimmed email |
| `DisplayName`   | [DisplayName_VO_Spec.md](./ValueObjects/DisplayName/DisplayName_VO_Spec.md) | `User.name` | Trimmed, non-empty display name      |

---

## 6. Aggregate Behavior

### 6.1 Creation

`User::new(name: DisplayName, email: Email) -> Result<User, UserError>`

- `name` is a `DisplayName` VO (already validated: trimmed, non-empty).
- `email` is an `Email` VO (already validated: trimmed, lowercased, structurally valid).
- `is_active` defaults to `true`.
- Uniqueness of `email` is enforced at the database level (UNIQUE constraint on lowercased value).

### 6.2 Update Name

`User::update_name(name: DisplayName) -> Result<(), UserError>`

- Accepts a pre-validated `DisplayName` VO.
- **No deactivated guard.** See §6.6.

### 6.3 Update Email

`User::update_email(email: Email) -> Result<(), UserError>`

- Accepts a pre-validated `Email` VO.
- Uniqueness re-checked at DB level on save.
- **No deactivated guard.** See §6.6.

### 6.4 Deactivate

`User::deactivate() -> Result<(), UserError>`

- Sets `is_active = false`.
- Returns `Err(UserError::AlreadyDeactivated)` if already inactive.
- A deactivated user cannot log in (enforced in Phase 3B auth middleware).
- Does **not** delete memberships — the user can be reactivated.

> **Phase 3B requirement:** Deactivation must invalidate any existing sessions. Auth middleware must check `is_active` on every authenticated request, not just at login.

### 6.5 Reactivate

`User::reactivate() -> Result<(), UserError>`

- Sets `is_active = true`.
- Returns `Err(UserError::AlreadyActive)` if already active.

### 6.6 Why No Deactivated Guard on Updates

`update_name` and `update_email` intentionally do **not** check `is_active`. Deactivation means "this person cannot log in" — it is an authentication gate (enforced in Phase 3B middleware), not a data freeze.

A deactivated user cannot call these methods on themselves because they cannot authenticate. The only caller is an admin correcting a record. Guarding against it would force an unnecessary reactivate → fix → deactivate workflow.

---

## 7. Invariants

| # | Invariant | Enforced By |
| :--- | :--- | :--- |
| 1 | `name` must be a valid DisplayName VO (non-empty after trim) | Domain (VO constructor) + DB (CHECK constraint) |
| 2 | `email` must be a valid Email VO | Domain (VO constructor) |
| 3 | `email` must be globally unique | DB (UNIQUE constraint) |
| 4 | `email` must be stored lowercased | Domain (VO normalization) + DB (CHECK constraint) |

---

## 8. Errors

```rust
pub enum UserError {
    AlreadyActive,
    AlreadyDeactivated,
}
```

> **Note:** `EmptyName` and `EmailError` variants are handled by the VO constructors (`DisplayName::new()` and `Email::new()`), not by `UserError`. The aggregate only deals with aggregate-level errors.

---

## 9. Why No Events

Job has events (11 types) because it has a complex state machine with an audit trail persisted to `job_events`. Every state transition (Opened → Started → Completed) is a meaningful domain event that other parts of the system consume.

User has no state machine. It has a boolean active flag and CRUD on identity fields. There is no consumer for "user was created" or "email was updated" today, and adding event infrastructure with no consumer produces dead code.

When a cross-cutting event bus is needed (e.g., audit logging, notification system), events should be retrofitted onto User, Client, and Company together as a consistent pattern — not bolted onto one aggregate in isolation.

---

## 10. Persistence

```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    personal_workspace_id UUID NOT NULL REFERENCES workspaces(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Invariant #1: name must be non-empty and trimmed
    CONSTRAINT chk_user_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT chk_user_name_trimmed CHECK (name = trim(name)),
    CONSTRAINT chk_user_name_max_length CHECK (length(name) <= 200),

    -- Invariant #3: email uniqueness
    CONSTRAINT uq_user_email UNIQUE (email),

    -- Invariant #4: email lowercase defense-in-depth
    CONSTRAINT chk_user_email_lowercase CHECK (email = lower(email)),
    CONSTRAINT chk_user_email_max_length CHECK (length(email) <= 254)
);
```

> **Note:** `personal_workspace_id` references the `workspaces` table (ADR-0030). The workspace must be created before the user. Workspace access is derived — no `workspace_memberships` table exists (ADR-0032).

---

## 11. Membership Infrastructure (3A — Not Domain Behavior)

The `company_memberships` table is created alongside the `users` table as structural infrastructure for RLS and company context resolution:

```sql
CREATE TABLE IF NOT EXISTS company_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    company_id UUID NOT NULL REFERENCES companies(id),
    role TEXT NOT NULL DEFAULT 'TECHNICIAN',
    is_primary BOOLEAN NOT NULL DEFAULT false,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_membership_user_company UNIQUE (user_id, company_id),
    CONSTRAINT chk_membership_role CHECK (role IN ('ADMIN', 'TECHNICIAN'))
);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON company_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_company ON company_memberships(company_id);
```

> **This table is infrastructure in Phase 3A.** It is seeded, queried by auth middleware for company context resolution and workspace access derivation (ADR-0032), and checked for role-based access in 3C.1. Full membership lifecycle behavior (invitation, acceptance, role transitions, primary switching, join/leave UX) is designed in **Phase 3M** (Membership Lifecycle). See [ADR-0029](../../../../adr/0029-phase3-decomposition-membership-entitlements.md).

---

## 12. Phase 3A ↔ 3B Dependency Log

The following aspects of the User spec require Phase 3B (Authentication) completion:

| Dependency | Where in this spec | What 3B must provide |
| :--- | :--- | :--- |
| Deactivation invalidates sessions | §6.4 | Auth middleware checks `is_active` on every request, not just login |
| Email change requires re-authentication | §6.3 | Email update gated by password confirmation |
| Email enumeration prevention | §3.3 | Constant-time responses ("wrong credentials" vs "user not found") |
| Login identity binding | §3.3 | JWT issued using `email` as the lookup key |

---

## 13. Relationship to Other Aggregates

### To Workspace (via personal_workspace_id — ADR-0030)

Every user has a personal workspace (`workspace_type = 'PERSONAL'`). This is where their personal jobs, clients, and saved buildings live. The `personal_workspace_id` FK is set on user creation and never changes.

Workspace access to company workspaces is **derived** from `company_memberships` → `companies.workspace_id` (ADR-0032). There is no separate workspace_memberships table.

### To Company (via company_memberships infrastructure)

A User belongs to zero or more companies through `company_memberships`. When operating in a company context, the user's active workspace is the company's workspace (enforced by RLS in Phase 3C via `app.workspace_id`).

### To Jobs (via `actor_user_id`)

The Job aggregate and LL152 workflow use `actor_user_id` to track who performed an action. Currently `Option<Uuid>` — Phase 3A makes it reference a real row in the `users` table.

### To LmpCredential (Phase 3A Session 2)

A User can hold LMP credentials (`lmp_credentials.user_id`). The LMP license belongs to the person, not the company.

### To Professional Network (Phase 3E)

User-to-user connections are a separate entity. See [ADR-0026](../../../../adr/0026-professional-network-connections.md).

---

## 14. Future Considerations

These are scoped to later phases with clear rationale:

- **Password hash field** — Phase 3B (authentication, not identity)
- **Phone, avatar, bio** — Phase 3D (profile enrichment)
- **Subscription tier** — Phase 3N (entitlements, not identity — per ADR-0029)
- **Last login timestamp** — Phase 3B (auth system tracks this)
- **Notification preferences** — Phase 3D or later
- **Multiple email addresses** — not planned (one email = one identity)
- **Domain events** — when a cross-cutting event bus is built (see §9)
- **Membership lifecycle commands** — Phase 3M (invitation, acceptance, role transitions — per ADR-0029)
- **Account deletion (GDPR)** — requires anonymization strategy for `actor_user_id` references across Jobs, LL152 events, and other audit trail records. Deletion cannot simply DELETE the user row. Users should have an option to export their data before deletion, and potentially import it if they create a new account.
