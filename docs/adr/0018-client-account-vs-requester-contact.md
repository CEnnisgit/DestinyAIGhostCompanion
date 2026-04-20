# ADR 0018: Client Account vs Requester Contact

**Date**: 2026-03-18  
**Status**: Accepted  
**Context**: Clarifying the relationship between `client_id` and `requester_contact_id` on the Job aggregate during Phase 1 design review.

## Application Context

The Job aggregate has two optional references to "people" outside the company:

- `client_id` — who the job is *for*
- `requester_contact_id` — who *initiated* this specific job

During design review, the question arose: when are these different, and is `requester_contact_id` redundant?

## Decision: client_id Is Account-Level, requester_contact_id Is Person-Level

### `client_id` = the account

Points to the **entity the work is being done for** — the billable party, the relationship owner. This is typically:

- A property management company
- A condo board
- A landlord / building owner
- An individual homeowner

This is the entity that persists across many jobs. "ABC Property Management" is a client whether they have 1 job or 50.

### `requester_contact_id` = the initiator (when distinct)

Points to the **specific person who triggered this particular job**, when that person is meaningfully different from the client account. Examples:

| `client_id` | `requester_contact_id` | Scenario |
|---|---|---|
| ABC Property Management | Mike the super | Super called requesting the inspection |
| 123 Main Condo Board | Board secretary | Secretary emailed the office |
| Landlord LLC | Tenant liaison | Liaison flagged the issue on-site |
| Building owner | Property manager | Manager asked to get it scheduled |

### When they're the same

In small shops and simple cases, the client *is* the person who called. In these cases, `requester_contact_id` is left null — `client_id` alone is sufficient.

## Rationale

1. **`requester_contact_id` is not always needed.** Many jobs in small plumbing shops have a simple client who is also the requester. Forcing a separate contact would be friction without value.
2. **But when they differ, it matters.** Knowing *who called* for a specific job (vs who the account is) is operationally useful — for callbacks, scheduling coordination, and access instructions.
3. **This shapes the CRM model.** `client_id` must point to an account/entity-level record in CRM/Clients, not a contact-level record. This means the CRM/Clients module needs to support both account entities and individual contacts within them.

## Design Rules

- `requester_contact_id` must **never** replace or duplicate `client_id`.
- `requester_contact_id` is **optional and secondary** — the Job aggregate does not collapse without it.
- If `client_id` already captures a person-level contact (e.g., individual homeowner), `requester_contact_id` is typically null.

## Status for Pilot

`requester_contact_id` is **deferred** for v1 pilot implementation unless intake research reveals it is frequently needed. It remains in the spec as a documented optional field.

## Impact

- **Job Aggregate:** No structural change — both fields remain optional references.
- **CRM/Clients (Phase 3):** Must model clients at the **account level**, not just as individual contacts. This enables the account-vs-person distinction that makes `requester_contact_id` meaningful.
