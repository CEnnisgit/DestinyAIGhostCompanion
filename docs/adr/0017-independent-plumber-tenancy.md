# ADR 0017: Independent Plumber Tenancy

**Date**: 2026-03-18
**Status**: Partially Superseded by [ADR-0027](./0027-user-first-registration-rls-isolation.md)
**Context**: Product scope clarification during Job Aggregate design review (Phase 1).

> [!IMPORTANT]
> **Supersession Note (2026-03-29):** The "company of one" model and "user holds both roles" assumptions in this ADR have been replaced by ADR-0027's user-first registration model. See [§ What Changed](#what-changed-adr-0027) below.

## Application Context

The platform was originally conceived around **plumbing companies** — a Licensed Master Plumber (LMP) runs a firm, employs technicians, and manages jobs through the dashboard. The `company_id` field scopes all data (jobs, buildings, clients) to a single organizational tenant.

During Job Aggregate review, it became clear that the platform must also support **independent plumbers** — solo practitioners who manage their own work without a company structure. This is a common reality in the NYC plumbing trades.

## Decision: Tenancy Supports Both Companies and Independents

The `company_id` scoping model remains, but the concept of "company" is broadened to include solo practitioners:

- A **company** is any organizational unit that owns data — whether it's a 10-person firm or a single plumber working independently.
- ~~An **independent plumber** is a company of one, where the same person is both the admin (LMP) and the field technician.~~ → **Superseded.** An independent plumber is a *person* first. They may create a company (their LLC) or operate on the free tier without one. See ADR-0027.
- The tenancy model does not enforce a minimum headcount or require distinct LMP and technician roles.

## Rationale

1. **Market reality:** Many LL152 inspections are performed by independent plumbers, not large firms. Excluding them limits the platform's addressable market.
2. **Minimal model impact:** The `company_id` scoping model works unchanged — a solo plumber simply has a company with one member. ~~who holds all roles.~~ → The member is ADMIN; ADMIN is a superset of TECHNICIAN capabilities.
3. ~~**Role flexibility:** The RBAC model (TECHNICIAN, ADMIN) should allow a single user to hold both roles simultaneously, enabling solo practitioners to both create/dispatch jobs and perform field capture.~~ → **Superseded.** Per ADR-0027, each membership has ONE role. ADMIN includes all TECHNICIAN capabilities. A solo plumber is simply ADMIN of their own company.
4. **UX implications:** The dashboard should adapt for solo users — e.g., auto-assigning the logged-in user as the technician, skipping dispatch steps when there's only one worker. *(Still valid.)*

## Consequences

**Positive:**
- Broader market appeal — captures both firms and independents.
- Forces cleaner role model — roles become capabilities, not rigid job titles.
- ~~Simpler onboarding for solo plumbers — they don't need to set up a fake "company" with employees.~~ → Replaced by: A solo plumber signs up as a person (free tier) and creates a company when they need operational features.

**Negative:**
- UX complexity — the dashboard must handle both multi-user (LMP dispatches to N plumbers) and single-user (plumber manages own jobs) modes gracefully.
- Phase 3 scope increase — the Users/Company design must account for the solo practitioner case when defining profiles, roles, and onboarding flows.

## Impact on Domain Model

- **Job Aggregate:** No change — `company_id` still scopes every job. The aggregate is agnostic to whether the company has 1 or 100 members.
- **Users Module (Phase 3):** ~~Must support a user who holds both ADMIN and TECHNICIAN roles.~~ → Per ADR-0027, a solo plumber gets one ADMIN membership. ADMIN is a superset of TECHNICIAN. Company setup accommodates solo practitioners naturally — a one-person company with one ADMIN membership.
- **Auth/RBAC (Phase 3):** Roles should be treated as capabilities, not mutually exclusive positions. ADMIN includes all TECHNICIAN capabilities. *(Refined, not reversed.)*

---

## What Changed (ADR-0027)

ADR-0027 (2026-03-29) made two changes to this ADR's assumptions:

### 1. Person First, Not "Company of One"

**Old thinking:** An independent plumber is modeled as a company of one — making the plumber a company felt like the simplest path.

**New thinking:** An independent plumber is a *person* who may or may not have a company. Per ADR-0027:
- A user can exist with no company (free tier — browse buildings, view compliance data)
- A user creates a company when they need operational features (jobs, clients, dispatching)
- A solo plumber's LLC is still a Company entity — but the *person* exists independently of it

The distinction matters because a plumber's identity (name, email, LMP credentials, professional connections) persists even if they leave or close a company.

### 2. One Role Per Membership, ADMIN ⊇ TECHNICIAN

**Old thinking:** A solo plumber needs to hold both ADMIN and TECHNICIAN roles simultaneously.

**New thinking:** Each `company_memberships` row has exactly one role. ADMIN is a superset — an ADMIN can do everything a TECHNICIAN can do, plus company management actions (invite users, edit company profile, manage billing). A solo plumber is simply ADMIN.

This is simpler and aligns with standard RBAC: higher roles inherit lower role capabilities.

## References

- [ADR-0027: User-First Registration, Multi-Company Membership, and RLS Tenant Isolation](./0027-user-first-registration-rls-isolation.md)
- [Vision: Registration and Tenancy](../vision/REGISTRATION_AND_TENANCY.md)
