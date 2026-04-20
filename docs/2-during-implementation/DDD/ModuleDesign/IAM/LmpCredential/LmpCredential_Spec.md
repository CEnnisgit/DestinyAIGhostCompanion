# LmpCredential Entity Specification

**Module:** `IAM`
**Sub-Module:** `LmpCredential`
**Source of Truth:** `crates/pcd-domain/src/iam/lmp_credential.rs` (Phase 3A Session 2, not yet implemented)
**Version:** 1.0.0
**ADRs:** [ADR-0027](../../../../adr/0027-user-first-registration-rls-isolation.md), [ADR-0030](../../../../adr/0030-workspace-isolation-abstraction.md)

---

## 1. Objective

The LmpCredential entity represents a **reusable license card** for a Licensed Master Plumber (LMP). It captures the LMP's professional identity — who they are, their license number, and contact info — so it can be attached to LL152 inspection jobs.

It answers:

- Which LMP authorized this inspection?
- What is their license number?
- Is their credential still active/valid?

It does **not** answer:

- Whether the LMP is a system user (they may not be — external relationship)
- Which company the LMP works for (the credential belongs to the person who entered it, not a company)
- Whether the QI is authorized to work under this LMP (that's a future Connections concern, Phase 3E)

---

## 2. Why This Is an Entity (Not an Aggregate Root)

LmpCredential is a standalone entity, not an aggregate root, because:

- It has no child entities or invariants that span multiple objects
- Its lifecycle is simple CRUD — create, update fields, deactivate
- It does not own a state machine or event history
- It is referenced by LL152 job details but does not own them

In future phases, if credential verification, expiry notifications, or sharing rules add complexity, it could be promoted. For now, CRUD is sufficient.

---

## 3. Core Decisions

### 3.1 User-Owned, Not Company-Owned (ADR-0027)

An LMP license belongs to a person, not a company. User A (a QI) may work under multiple LMPs across different companies. The credential is created by a user and belongs to that user's personal workspace.

There is no `company_id` on `lmp_credentials`. The credential is scoped to the user who created it, via `created_by_user_id`.

### 3.2 External LMP (Not a System User)

The LMP referenced by a credential may not be a PCD user. User A enters their LMP's info as a reusable card. The LMP does not need an account.

If the LMP becomes a system user in the future, the credential could be linked via Professional Network connections (Phase 3E). For now, it is purely data entry by the QI.

### 3.3 Attached to Jobs, Not Embedded

Currently, `companies.lmp_name` and `companies.lmp_license_number` are text columns bolted onto the company table by the LL152 extension. This is wrong for several reasons:

- A QI may work under different LMPs on different jobs
- The LMP belongs to the person, not the company
- Text columns can't be validated or reused

Phase 3A replaces this with:
1. A standalone `lmp_credentials` table (user-owned)
2. An `lmp_credential_id` FK on `ll152_job_details`
3. The old text columns remain until data migration is complete (backward compatibility)

### 3.4 Workspace Scoping

Each LmpCredential exists in the creating user's **personal workspace** (via `created_by_user_id` → `users.personal_workspace_id`). When the user operates in a company context, they can still see and attach their personal credentials to company jobs.

> **Note:** The credential is NOT scoped to `workspace_id` directly. It is scoped to the user. This is because credentials follow the person, not the workspace — if a user joins a new company, they bring their credential cards with them.

### 3.5 Sharing Model (Future — Phase 3E)

Via Professional Network connections, an LMP could share their credential card with connected QIs. This is deferred entirely. For alpha, each user enters their own LMP's info.

---

## 4. Attributes

| Field | Type | Nullable | Description | Source |
|---|---|---|---|---|
| `id` | UUID | No | PK | Generated |
| `created_by_user_id` | UUID | No | FK → users. Who entered this credential. | System |
| `lmp_name` | TEXT | No | Full name of the LMP (e.g., "John Smith"). | User input |
| `license_number` | TEXT | No | LMP license number (e.g., "LMP-12345"). | User input |
| `license_expiry` | DATE | Yes | When the license expires. Null = no expiry known. | User input |
| `phone` | TEXT | Yes | LMP contact phone. | User input |
| `email` | TEXT | Yes | LMP contact email. | User input |
| `is_active` | BOOL | No | Default: true. False = expired/revoked/deleted. | User action |
| `created_at` | TIMESTAMPTZ | No | When the credential was created. | System |
| `updated_at` | TIMESTAMPTZ | No | When the credential was last modified. | System |

### PII Classification

| Field | PII? | Sensitivity | Retention Policy |
|---|---|---|---|
| `lmp_name` | Yes | Low | Retained while credential active. Anonymizable on request. |
| `license_number` | Yes | Medium (professional) | Retained while credential active. |

> **Deferred:** License number format validation is deferred to post-alpha. Requires domain research on NYC DOB license number formats.
| `phone` | Yes | Medium | Anonymizable on request. |
| `email` | Yes | Medium | Anonymizable on request. |

### Fields NOT included (with rationale)

| Rejected Field | Reason | When Revisited |
|---|---|---|
| `company_id` | Credential belongs to person, not company (ADR-0027) | Never — architectural |
| `workspace_id` | Scoped via user, not directly on workspace | Never — follows user |
| `verified` | No verification system exists | Phase 3D or later |
| `license_type` | All LMP licenses are the same type in NYC | If expanding beyond NYC |
| `insurance_info` | Not relevant to LMP credential | Phase 3D company profile |

---

## 5. Aggregate Behavior

### 5.1 Creation

`LmpCredential::new(created_by_user_id: Uuid, lmp_name: String, license_number: String) -> Result<LmpCredential, LmpCredentialError>`

- `lmp_name` must be non-empty after trimming.
- `license_number` must be non-empty after trimming.
- `is_active` defaults to `true`.
- `created_by_user_id` must reference a valid user (enforced at DB level via FK).

### 5.2 Update Fields

`LmpCredential::update(lmp_name?, license_number?, license_expiry?, phone?, email?) -> Result<(), LmpCredentialError>`

- Any combination of fields can be updated.
- `lmp_name` must be non-empty if provided.
- `license_number` must be non-empty if provided.
- No deactivated guard — same rationale as User (§6.6 in User_Aggregate.md).

### 5.3 Deactivate

`LmpCredential::deactivate() -> Result<(), LmpCredentialError>`

- Sets `is_active = false`.
- Returns `Err(LmpCredentialError::AlreadyDeactivated)` if already inactive.
- Deactivated credentials can still be viewed on historical jobs but cannot be attached to new jobs.

### 5.4 Reactivate

`LmpCredential::reactivate() -> Result<(), LmpCredentialError>`

- Sets `is_active = true`.
- Returns `Err(LmpCredentialError::AlreadyActive)` if already active.

---

## 6. Invariants

| # | Invariant | Enforced By |
|---|---|---|
| 1 | `lmp_name` must be non-empty after trim | Domain (constructor) + DB (CHECK constraint) |
| 2 | `license_number` must be non-empty after trim | Domain (constructor) + DB (CHECK constraint) |
| 3 | `created_by_user_id` must reference a valid user | DB (FK constraint) |

---

## 7. Errors

```rust
pub enum LmpCredentialError {
    EmptyName,
    EmptyLicenseNumber,
    AlreadyActive,
    AlreadyDeactivated,
}
```

---

## 8. Why No Events

Same rationale as User and Company — LmpCredential has no state machine, no consumers for "credential was created" or "credential was updated" today. Events will be added across all aggregates when a cross-cutting event bus is needed.

---

## 9. Persistence

```sql
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
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Invariant #1: name must be non-empty
    CONSTRAINT chk_lmp_name_not_empty CHECK (length(trim(lmp_name)) > 0),

    -- Invariant #2: license number must be non-empty
    CONSTRAINT chk_lmp_license_not_empty CHECK (length(trim(license_number)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_lmp_creds_user ON lmp_credentials(created_by_user_id);
```

---

## 10. LL152 Migration Strategy

### Current State

The `companies` table has two LMP text columns added by the LL152 extension (`pcd-db/src/ll152/mod.rs`):

```sql
ALTER TABLE companies ADD COLUMN lmp_name TEXT;
ALTER TABLE companies ADD COLUMN lmp_license_number TEXT;
```

These are on the wrong table (company vs. user) and are not reusable.

### Migration Plan

1. **Session 2:** Add `lmp_credential_id UUID REFERENCES lmp_credentials(id)` to `ll152_job_details`
2. **Session 2:** Keep old text columns on `companies` — they are not removed yet
3. **Data migration (seeding):** For alpha, seed LMP credentials for each user's known LMP, then link to existing jobs
4. **Future cleanup:** Once all jobs reference `lmp_credential_id`, the old text columns on `companies` can be dropped (post-alpha)

> [!IMPORTANT]
> **Backward compatibility:** The old `companies.lmp_name` and `companies.lmp_license_number` columns are NOT removed in Phase 3A. They remain as read-only legacy columns. Cleanup is deferred to post-alpha. The domain model ignores them.

### ll152_job_details FK Addition

```sql
ALTER TABLE ll152_job_details ADD COLUMN IF NOT EXISTS lmp_credential_id UUID REFERENCES lmp_credentials(id);
```

This is an optional FK — existing jobs without a credential are valid (they predate the credential system). New jobs should reference a credential.

---

## 11. Relationship to Other Entities

### To User (via created_by_user_id)

The user who entered this credential. This is the QI who works under this LMP, not the LMP themselves.

### To LL152 Job Details (via lmp_credential_id FK)

Each LL152 job can reference one LMP credential. This tells the system "this inspection was authorized by this LMP."

### To Professional Network (Phase 3E — Future)

An LMP who is also a system user could share their credential with connected QIs, eliminating duplicate data entry.

---

## 12. Future Considerations

- **License verification** — validate against NYC DOB database (Phase 3D or later)
- **Expiry notifications** — alert when `license_expiry` is approaching (notification system needed)
- **Credential sharing** — via Professional Network connections (Phase 3E)
- **Multiple license types** — if expanding beyond NYC LMP licenses
- **Audit trail** — who changed what on a credential (when event bus exists)
