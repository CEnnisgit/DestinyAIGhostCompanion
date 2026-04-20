# LmpCredential Sub-Module (IAM)

> **Parent:** [IAM Module](../README.md)
> **Status:** ✅ Specced (Phase 3A Session 2 — not yet implemented)

## Responsibilities

**Professional License Cards**: Reusable LMP credential records.

- User-owned — the LMP license belongs to the person, not the company (ADR-0027).
- Attached to LL152 jobs via `ll152_job_details.lmp_credential_id` (replaces `lmp_name` + `lmp_license_number` text columns on `companies`).
- Shareable via Professional Network connections (Phase 3E, future).

## Spec

- [LmpCredential_Spec.md](./LmpCredential_Spec.md) — Entity specification (v1.0.0)

## Data Structures

- `lmp_credentials` table — license card (name, number, expiry, contact).
- FK from `ll152_job_details.lmp_credential_id` (replaces text columns).
- Scoped to user via `created_by_user_id`, not workspace-scoped directly.

## Migration

- Old `companies.lmp_name` and `companies.lmp_license_number` columns remain for backward compatibility
- New jobs reference `lmp_credential_id` on `ll152_job_details`
- See [Migration Strategy](./LmpCredential_Spec.md#10-ll152-migration-strategy) in the entity spec
