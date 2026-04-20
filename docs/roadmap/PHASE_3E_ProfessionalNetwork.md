# Phase 3E: Professional Network (Connections)

> **Status:** 🔲 Not Started  
> **Objective:** Enable user-to-user connections across company boundaries for job sharing, LMP credential sharing, and collaborative work.  
> **Depends On:** Phase 3C ✅ (need auth + RBAC before cross-company visibility)  
> **ADR:** [ADR-0026](../adr/0026-professional-network-connections.md)  
> **Vision:** [PROFESSIONAL_NETWORK.md](../vision/PROFESSIONAL_NETWORK.md)  
> **Branch:** `phase3e/professional-network`

---

## Why This Sub-Phase Exists

Phases 3A-3D establish identity, auth, and permissions within a single company. But real plumbing work crosses company boundaries — plumbers work under other plumbers' licenses, share jobs with colleagues at other firms, and collaborate across companies on the same work.

This sub-phase adds the **Professional Network** layer: explicit, opt-in connections between users that create controlled visibility across tenant boundaries.

---

## Domain Concepts

### 1. Connection Entity

The atomic unit of the network. Two users explicitly link.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | PK |
| `requester_id` | UUID | FK → users (who initiated) |
| `responder_id` | UUID | FK → users (who accepted) |
| `connection_type` | TEXT | `COLLEAGUE`, `SUPERVISES`, `SUBCONTRACTS` |
| `status` | TEXT | `PENDING`, `ACCEPTED`, `DECLINED`, `REVOKED` |
| `created_at` | TIMESTAMPTZ | When requested |
| `accepted_at` | TIMESTAMPTZ | When accepted (null if pending) |

**Spec deliverable:** `Connection_Spec.md`

### 2. Job Participants (Extension to Job Aggregate)

Enable multiple users on a single job.

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | UUID | FK → jobs |
| `user_id` | UUID | FK → users |
| `role` | TEXT | `OWNER`, `COLLABORATOR`, `TRANSFERRED_FROM` |
| `added_at` | TIMESTAMPTZ | When attached |

**Impact:** Job portfolio queries expand to include jobs where the user is a participant, not just jobs in their company.

### 3. LMP Credential Sharing (Upgrade from 3A)

Connections unlock cross-company credential sharing:

| Field | Type | Description |
|-------|------|-------------|
| `credential_id` | UUID | FK → lmp_credentials |
| `shared_with_user_id` | UUID | FK → users (the QI receiving the card) |
| `shared_at` | TIMESTAMPTZ | When shared |

**Impact:** An LMP creates their card once. Connected QIs can attach it to jobs without manual data entry.

---

## Alpha Scope (Minimum Viable Network)

For alpha, only the essentials:

- [ ] Send/accept/decline connection requests
- [ ] View connected users list
- [ ] Transfer a job to a connected user
- [ ] Share an LMP credential with a connected QI

### Deferred to Post-Alpha

- Job collaboration (multi-participant on same job)
- LMP oversight dashboard
- Connection activity notifications
- Availability signaling

---

## Implementation Plan

### Domain Layer

| File | Action |
|------|--------|
| `src/tenant/connections/mod.rs` | New — Connection entity, lifecycle commands |
| `src/tenant/connections/connection_type.rs` | New — ConnectionType enum |
| `src/jobs/job.rs` | Update — add `transfer()` command, `job_participants` |
| `src/tenant/lmp_credential.rs` | Update — add sharing methods |

### DB Layer

| File | Action |
|------|--------|
| `src/connections/mod.rs` | New — SqlxConnectionRepository |
| `src/jobs/mod.rs` | Update — participant queries, cross-company job views |
| `src/tenant/lmp_credentials.rs` | Update — sharing queries |

### API Layer

| Endpoint | Method | Guard | Description |
|----------|--------|-------|-------------|
| `POST /api/connections` | POST | Auth | Send connection request |
| `GET /api/connections` | GET | Auth | List my connections |
| `PATCH /api/connections/{id}/accept` | PATCH | Auth | Accept a request |
| `PATCH /api/connections/{id}/decline` | PATCH | Auth | Decline a request |
| `POST /api/jobs/{id}/transfer` | POST | Auth | Transfer job to connected user |
| `POST /api/lmp-credentials/{id}/share` | POST | Auth | Share credential with connection |

### Schema

```sql
CREATE TABLE connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id UUID NOT NULL REFERENCES users(id),
    responder_id UUID NOT NULL REFERENCES users(id),
    connection_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    accepted_at TIMESTAMPTZ,
    CONSTRAINT chk_connection_type CHECK (connection_type IN ('COLLEAGUE', 'SUPERVISES', 'SUBCONTRACTS')),
    CONSTRAINT chk_status CHECK (status IN ('PENDING', 'ACCEPTED', 'DECLINED', 'REVOKED')),
    CONSTRAINT uq_connection UNIQUE (requester_id, responder_id)
);

CREATE TABLE job_participants (
    job_id UUID NOT NULL REFERENCES jobs(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role TEXT NOT NULL DEFAULT 'COLLABORATOR',
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (job_id, user_id),
    CONSTRAINT chk_participant_role CHECK (role IN ('OWNER', 'COLLABORATOR', 'TRANSFERRED_FROM'))
);

CREATE TABLE lmp_credential_shares (
    credential_id UUID NOT NULL REFERENCES lmp_credentials(id),
    shared_with_user_id UUID NOT NULL REFERENCES users(id),
    shared_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (credential_id, shared_with_user_id)
);
```

---

## Cross-Cutting Impact

| Existing System | What Changes |
|----------------|-------------|
| **Job portfolio query** | Must include `job_participants` in addition to `company_id` filter |
| **LMP credential list** | Must include shared credentials from other companies |
| **Tenant isolation** | Connections create explicit, controlled exceptions to the boundary |
| **Auth middleware** | No change — JWT carries `user_id` only; workspace context is per-request (ADR-0030). Cross-company data access is via explicit connection joins |

---

## Exit Criteria

- [ ] Users can send and accept connection requests
- [ ] Connected users can see each other in their connection list
- [ ] Jobs can be transferred to connected users
- [ ] LMP credentials can be shared via connections
- [ ] Cross-company data access is ONLY through explicit connections (no bypass)
- [ ] Connection specs written: Connection entity, sharing model
- [ ] Integration tests: transfer job across companies, verify isolation
