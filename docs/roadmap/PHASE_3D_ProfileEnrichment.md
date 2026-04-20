# Phase 3D: Profile Enrichment

> **Status:** 🔲 Not Started
> **Objective:** Rich user and company profiles for production readiness. Extended fields, user management API, and audit enrichment.
> **Depends On:** Phase 3B ✅ (need authenticated users to manage profiles)
> **Branch:** `phase3d/profile-enrichment`

---

## Why This Sub-Phase Exists

Phases 3A-3B establish the core identity and authentication system. This sub-phase adds the **detail fields** that make profiles production-ready but aren't blockers for alpha testing.

> [!TIP]
> This is a parallel sub-phase. It depends on 3B (auth) but is independent of 3C (authorization), 3M (membership), 3N (entitlements), and 3P (payments). It can be done whenever identity + auth are stable.

---

## Scope

### 1. Technician Profile Extension

Extended fields for field staff beyond the basic User entity:

| Field | Type | Description |
|-------|------|-------------|
| `license_number` | TEXT | Technician's personal plumbing license (if applicable) |
| `certifications` | TEXT[] | e.g., ["Gas", "Backflow", "Medical Gas"] |
| `availability_status` | TEXT | `AVAILABLE`, `ON_JOB`, `OFF_DUTY` |
| `phone` | TEXT | Direct contact number |

**Design choice:** These can be additional columns on `users`, or a separate `technician_profiles` table. Note: role is per-company-membership (a user can be ADMIN at one company and TECHNICIAN at another per ADR-0029), so a `WHERE role = 'TECHNICIAN'` guard on the user table is not correct. Decision to be made during research.

### 2. Company Settings

| Setting | Type | Description |
|---------|------|-------------|
| `timezone` | TEXT | e.g., "America/New_York" |
| `notification_prefs` | JSONB | Future: email/SMS notification settings |

### 3. User Management API (SFR-SRAZ-07)

Complete CRUD for admin user management:

| Endpoint | Method | Guard | Description |
|----------|--------|-------|-------------|
| `GET /api/users` | GET | ADMIN | List all company users |
| `POST /api/users` | POST | ADMIN | Create new user (with temp password) |
| `GET /api/users/{id}` | GET | ADMIN | Get user details |
| `PATCH /api/users/{id}` | PATCH | ADMIN | Update user profile |
| `POST /api/users/{id}/deactivate` | POST | ADMIN | Deactivate account |
| `POST /api/users/{id}/reactivate` | POST | ADMIN | Reactivate account |

> [!NOTE]
> If 3C.1 is complete by the time 3D is worked on, use `require_admin` guards. If not, use basic auth guards and add role guards later.

### 4. Audit Enrichment

Ensure all domain events have actor names (not just UUIDs) for readable reporting:
- Enrich event queries with JOIN to `users.name`
- Or denormalize `actor_name` into event payload

### 5. LMP Credential Sharing (Future Foundation)

If validated by alpha feedback:
- Person-to-person credential sharing model (per ADR-0027, credentials follow the person)
- `lmp_credential_shares(credential_id, shared_with_user_id)` table
- API for LMP to share their card with connected users (see [Phase 3E](./PHASE_3E_ProfessionalNetwork.md))

---

## Exit Criteria

- [ ] Technician profiles have extended fields (license, certifications, availability)
- [ ] Company settings model exists (timezone at minimum)
- [ ] Full user management API (CRUD + activate/deactivate)
- [ ] Audit events include actor names in reporting
- [ ] All new endpoints tested with auth guards

---

## Deferred Beyond Phase 3D

| Concept | Why Deferred |
|---------|-------------|
| Cross-company LMP sharing | No alpha use case yet (User A manually creates cards) |
| User avatar/photo | Cosmetic |
| Notification preferences | No notification system yet |
| Onboarding flow | Alpha users are seeded manually |
