# PILOT SCOPE CONTEXT & ZOMBIE CODE WARNING

> **READ THIS FIRST**: This document exists to resolve the "Conundrum" between the existing codebase (which contains legacy MVP code) and the current active development scope.
>
> **Updated 2026-03-27**: The product scope has broadened beyond "LL152 Pilot" to a plumbing company operations platform. See [ALPHA_PERSONAS_AND_SCOPE.md](ALPHA_PERSONAS_AND_SCOPE.md) for the current user model and feature scope.

## 1. The Conundrum
The `apps/backend` and `packages/` directories contain code from a previous "Marketplace MVP" that is **OUT OF SCOPE** for the current product direction.
- **Legacy Code**: Built for a public marketplace where anyone requests a plumber.
- **Current Code**: Built for a B2B operations platform where plumbing companies manage their own jobs, clients, and compliance work.

**The Danger**: If you read the code to understand the system, you will see features (like "Service Requests") that **do not exist** in the current product. Documenting or building on top of these "Zombie" features will cause hallucinations and scope creep.

## 2. The Golden Rule
> **[ALPHA_PERSONAS_AND_SCOPE.md](ALPHA_PERSONAS_AND_SCOPE.md) defines who the product serves and what's in scope.**
> **The [DOMAIN_FIRST_ROADMAP.md](roadmap/DOMAIN_FIRST_ROADMAP.md) defines the implementation plan.**

- If a feature/table is in the code but NOT aligned with the personas and roadmap, it is **Zombie Code**.
- **DO NOT** document Zombie Code in the DDD (System Architecture, ERD, Module Design) as if it were active.
- **DO NOT** delete Zombie Code (unless instructed), but **IGNORE** it completely.

## 3. The Ignore List (Zombie Code)
Explicitly ignore the following files/tables/modules as they belong to the legacy marketplace concept:
*   **Table/Schema**: `service_requests` (Current product uses `jobs` created by company users, not open marketplace requests).
*   **Logic**: Any "Matching" or "Bidding" logic.
*   **Logic**: Public signup flows (users are invited/created by company admin).

## 4. The Active Core (White-List)
The following domain entities are valid for the current product scope:

### Shared Foundation (serves all users)
1.  `users` (Identity)
2.  `plumbing_companies` (Tenancy)
3.  `jobs` (The Work — generic engine, supports all job types)
4.  `buildings` (Asset — address and location data)
5.  `owners` / `client_accounts` (Clients)
6.  `password_reset_tokens` (Utility)

### LL152-Specific (serves QI and LMP roles)
7.  `ll152_job_details` (LL152 workflow extension table — Phase 2)
8.  `inspection_findings` (GPS1 structured data — Phase 2)
9.  `inspection_photos` (Evidence — Phase 2)

### People & Roles (Phase 3)
10. `technicians` (Employee profiles)
11. `company_admins` (Admin profiles)

### Compliance (Phase 0, already built)
12. `compliance_obligations` (LL152 compliance tracking)
13. `ll152_obligation_details` (LL152-specific compliance data)

## 5. Usage Instruction for Agents
When performing **Context Verification** or **Traceability** checks:
1.  Check this document first.
2.  Filter out any "Ignore List" items found in the codebase.
3.  Refer to [ALPHA_PERSONAS_AND_SCOPE.md](ALPHA_PERSONAS_AND_SCOPE.md) for user context.
4.  Report Gaps *only* if an "Active Core" item is missing or incomplete.
5.  Never suggest linking current features to `service_requests`.
