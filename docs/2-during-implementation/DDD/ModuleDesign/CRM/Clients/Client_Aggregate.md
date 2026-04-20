# Client Aggregate Specification

**Module:** `CRM`
**Sub-Module:** `Clients`
**Source of Truth:** `crates/pcd-domain/src/tenant/client.rs` (Implemented Phase 1.5, 2026-03-26)
**Version:** 1.0.0 (Initial Spec)

---

## 1. Objective

The Client aggregate exists to represent **a person or organization that commissions work from the plumbing company**.

It answers the following domain questions:

- Who is asking for the work?
- How do I contact them?
- Have I worked for them before?
- Should I refuse work from them?

The Client aggregate does **not** answer:

- What specific work is being done (that's the Job)
- Where the work happens (that's the Building, referenced by the Job)
- What compliance obligations exist (that's the ComplianceObligation)
- What inspection findings were captured (that's the LL152 Workflow)

---

## 2. Core Decisions

### 2.1 Client-Centric, Not Building-Centric

Per [ADR-0021](../../../../adr/0021-client-centric-portfolio.md), the tenant portfolio centers on **clients**, not buildings. The old `TenantAsset(FirmID, BIN)` model is retired.

A client may control one building (individual homeowner) or many buildings (property management company, campus like Snug Harbor). Buildings are referenced through Jobs, not stored on the Client.

### 2.2 Company-Scoped

Every client belongs to exactly one company (tenant). Client data is isolated per company via `company_id`. Firm A's clients are invisible to Firm B.

Per [ADR-0017](../../../../adr/0017-independent-plumber-tenancy.md), "company" includes solo practitioners. A solo plumber's clients are scoped to their one-person company.

### 2.3 Minimal for Alpha

The Client entity is a **contact card**, not a CRM. Based on domain research with an active LMP:

> "He retains their name + address + phone number."

No tags, statuses, pipeline stages, notes, or buckets. If these are needed later, they're trivial column additions.

### 2.4 Dual Creation Paths

Per domain research ([TENANT_PORTFOLIO_RESEARCH.md](../Operations/Research/TENANT_PORTFOLIO_RESEARCH.md)):

1. **Explicit:** User creates a client before creating a job (e.g., building owner calls to schedule an LL152 inspection next week).
2. **Implicit:** Creating a job with new client info auto-creates the Client record (e.g., emergency call — plumber accepts on the spot, enters name + phone + address).

Both paths produce the same Client entity.

---

## 3. What This Aggregate Is

A Client is:

- company-scoped (every client belongs to one tenant)
- a person or organization that commissions work
- a persistent record that outlives individual jobs
- a lightweight contact card (name, phone, address)
- optionally blockable (for non-payment or unreliability)

---

## 4. What This Aggregate Is Not

The Client aggregate is **not**:

- a building identity (buildings are global, client-independent)
- a user/employee of the plumbing company (that's the Users module)
- a billing/invoicing entity (future scope)
- a CRM pipeline stage or sales lead
- a property management system

### Important Negative Boundaries

The Client aggregate does **not** own:

- building-level data (addresses, BINs, BBLs, compliance obligations)
- job-level data (schedule, status, findings, site notes)
- the client-to-building relationship (derived from Jobs)
- outreach tracking, lead scoring, or prospecting workflows
- financial records (invoices, payment history)

---

## 5. Attributes

| Field | Type | Nullable | Description | Authority |
|---|---|---|---|---|
| `id` | UUID | No | PK | Generated |
| `company_id` | UUID | No | FK → companies. Tenant scope. | System (from auth context) |
| `name` | TEXT | No | Person or organization name. | User input |
| `phone` | TEXT | Yes | Primary contact phone number. | User input |
| `address` | TEXT | Yes | Primary mailing/physical address. Free-text for alpha (not a structured VO). | User input |
| `is_blocked` | BOOLEAN | No | Default: false. True = "don't accept work from this client." | User action |
| `blocked_reason` | TEXT | Yes | Why the client was blocked (e.g., "non-payment"). Only meaningful when `is_blocked = true`. | User input |
| `created_at` | TIMESTAMPTZ | No | When the client record was created. | System |
| `updated_at` | TIMESTAMPTZ | No | When the client record was last modified. | System |

### Fields NOT included (with rationale)

| Rejected Field | Reason |
|---|---|
| `nickname` | Client name serves as the informal reference ("Snug Harbor") |
| `internal_status` | No pipeline. Only `is_blocked` is needed. |
| `tags[]` | No validated real-world use case |
| `notes` | Notes belong on Jobs (site-specific per visit) |
| `email` | Not in the LMP's current workflow. Can be added later. |
| `building_ids[]` | Buildings are derived from job history, not stored on client |

---

## 6. Aggregate Behavior

### 6.1 Creation

`Client.create({ company_id, name, phone?, address? })`

- `name` is required. Phone and address are optional (emergency call may only have one).
- `is_blocked` defaults to `false`.
- Emits `CLIENT_CREATED` event.

**No uniqueness constraint on name.** Multiple clients can share a name (e.g., two "John Smith" clients). Identity is by UUID, not name.

### 6.2 Update Contact Info

`Client.updateContact({ name?, phone?, address? })`

- Any combination of fields can be updated.
- Emits `CLIENT_CONTACT_UPDATED` event.

### 6.3 Block

`Client.block({ reason })`

- Sets `is_blocked = true`.
- Requires a `reason` (non-empty text).
- Business rule: **should not block a client with active (OPEN or IN_PROGRESS) jobs.** The application layer should warn or prevent this.
- Emits `CLIENT_BLOCKED` event.

### 6.4 Unblock

`Client.unblock()`

- Sets `is_blocked = false`, clears `blocked_reason`.
- Emits `CLIENT_UNBLOCKED` event.

### 6.5 Invariants

- `blocked_reason` must be non-null when `is_blocked = true`.
- `blocked_reason` must be null when `is_blocked = false`.
- `name` must be non-empty.

---

## 7. Domain Events

| Event | Payload | When |
|---|---|---|
| `CLIENT_CREATED` | `{ client_id, company_id, name }` | New client record created |
| `CLIENT_CONTACT_UPDATED` | `{ client_id, changed_fields }` | Name, phone, or address updated |
| `CLIENT_BLOCKED` | `{ client_id, reason }` | Client blocked for non-payment/unreliability |
| `CLIENT_UNBLOCKED` | `{ client_id }` | Block removed |

---

## 8. Persistence

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    is_blocked BOOLEAN NOT NULL DEFAULT false,
    blocked_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Invariants
    CONSTRAINT chk_blocked_reason
        CHECK (
            (is_blocked = true AND blocked_reason IS NOT NULL)
            OR
            (is_blocked = false AND blocked_reason IS NULL)
        )
);

CREATE INDEX idx_clients_company ON clients(company_id);
```

---

## 9. Derived Views (Not Persisted)

These are queries against `jobs`, not fields on the Client:

| View | Query | Status |
|---|---|---|
| Client's buildings | `SELECT DISTINCT building_id, address FROM jobs WHERE client_id = $1 AND building_id IS NOT NULL` | ✅ Implemented via `GET /api/clients/:id/summary` |
| Client's job count | `SELECT COUNT(*) FROM jobs WHERE client_id = $1` | ✅ Implemented via `GET /api/clients/:id/summary` |
| Client's last job | `SELECT MAX(created_at) FROM jobs WHERE client_id = $1` | ✅ Implemented via `GET /api/clients/:id/summary` |
| Is client "active"? | Has a job within the last N months (application-defined) | ⏳ Deferred |

### Implementation Note (2026-03-27)

The `/api/clients/:id/summary` endpoint implements the first three views as a single read-side projection using direct SQL against `PgPool` (not through the `ClientRepository` trait). This was a deliberate choice — derived views are cross-aggregate reads that don't belong in the domain layer's repository contract.

---

## 10. Relationship to Job Aggregate

The Job aggregate has `client_id` (nullable UUID, FK → clients). Per [ADR-0018](../../../../adr/0018-client-account-vs-requester-contact.md):

- `client_id` = account-level (who the work is for)
- `requester_contact_id` = person-level (who initiated this specific job, when different from client)

### Job Creation with Auto-Client

When creating a Job with new client info:

1. Check if a client with matching `(company_id, name, phone)` exists.
2. If not, auto-create the Client.
3. Set `job.client_id` to the found-or-created Client.

This supports the "spontaneous emergency call" workflow — plumber accepts the job, enters name + phone, system creates the Client automatically.

---

## 11. Future Considerations (Not in Phase 1.5)

These are ideas that emerged during research but are explicitly deferred:

- **Email field** — add when digital communication becomes part of the workflow
- **Contact sub-entities** — for clients with multiple contacts (e.g., Snug Harbor has a facilities manager AND a super). Relates to `requester_contact_id` on Job.
- **Billing/invoicing** — client as the billable entity
- **Vendor list tracking** — flagging which clients have added the firm to their vendor list
- **Client notes** — free-text notes that persist across jobs
