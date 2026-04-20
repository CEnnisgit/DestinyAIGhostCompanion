# ADR-0035: Compliance Boundary at Finalization, Not Role Permissions

> **Status:** Accepted
> **Date:** 2026-03-31
> **Deciders:** Marcus (product owner)
> **Relates To:** ADR-0034 (role-aware workspace interaction), Phase 3C.1 Authorization Core

## Context

The Phase 3C.1 permission matrix (PHASE_3C_Authorization.md) originally modeled separation of duties between TECHNICIAN and ADMIN roles for inspection workflows:

| Code | Action | TECHNICIAN | ADMIN |
|------|--------|-----------|-------|
| SFR-SRAZ-04 | Submit Findings | ✅ | ❌ |
| SFR-SRAZ-05 | Approve/Return Findings | ❌ | ✅ |

This created two problems:

1. **Solo operator breakage:** Both alpha users (User A and User B) are owner-operators who serve as ADMIN of their LLC AND perform fieldwork. Under the original matrix, they cannot submit findings on their own company jobs.

2. **Misplaced compliance pressure:** The separation assumes that restricting *who can submit* is the compliance-critical boundary. Research into NYC LL152 gas piping inspection rules revealed this is incorrect.

## Research Findings

NYC DOB LL152 rules ([nyc.gov/buildings](https://www.nyc.gov/site/buildings/property-or-business-owner/gas-piping-inspections.page), [GPS1 form](https://www.nyc.gov/assets/buildings/pdf/gps1.pdf)) govern the **official inspection artifact** (the signed report/certification filed with DOB), not internal app workflows.

What the law requires:

- Inspection performed by LMP or under LMP's direct supervision
- Report delivered to building owner within 30 days of inspection
- Owner files certification with DOB within 60 days
- Correction certifications within 120–180 days if defects found
- Immediate reporting of unsafe/hazardous conditions
- Records retained for at least 8 years
- False statements = criminal liability + loss of filing privileges

What the law does NOT require:

- A separate "submitter" and "approver" role in your software workflow
- Any specific internal role-based access control model

## Decision

### 1. ADMIN is a superset of TECHNICIAN for alpha

The SFR-SRAZ-04 restriction is removed. ADMINs can perform all TECHNICIAN actions plus ADMIN-only actions.

**Updated permission matrix:**

| Code | Action | TECHNICIAN | ADMIN |
|------|--------|-----------|-------|
| SFR-SRAZ-01 | Create Job | ❌ | ✅ |
| SFR-SRAZ-02 | Dispatch/Assign Job | ❌ | ✅ |
| SFR-SRAZ-03 | View Jobs | ✅ (assigned) | ✅ (all in workspace) |
| SFR-SRAZ-04 | Submit Findings | ✅ | ✅ |
| SFR-SRAZ-05 | Finalize/Sign Report | ❌ | ✅ |
| SFR-SRAZ-06 | Generate Report | ❌ | ✅ |
| SFR-SRAZ-07 | Manage Users | ❌ | ✅ |

### 2. The compliance boundary is at finalization

The inspection lifecycle has three stages with distinct mutability rules:

| Stage | Editable? | What happens |
|-------|----------|-------------|
| **Draft** | ✅ Yes | Findings, notes, photos, timestamps can change freely |
| **Finalized/Signed** | ❌ Locked | Content snapshot becomes the official inspection record |
| **After finalization** | New records only | Correction certification, addendum, or superseding inspection |

### 3. SFR-SRAZ-05 is reframed

"Approve/Return Findings" → **"Finalize/Sign Report"**

This is not an internal approval workflow step. It is the act that creates the official compliance artifact — the signed inspection report that carries legal weight.

## Consequences

### Positive

- Solo owner-operators can use the app without artificial role friction
- Compliance model matches what NYC law actually requires
- Clear, simple permission matrix — ADMIN ⊇ TECHNICIAN
- Finalization boundary is a single enforcement point with clear semantics
- Separation of duties can be reintroduced post-alpha as a business policy option, not a legal mandate

### Negative

- Alpha has no enforced separation of duties for submit/approve
- If a customer later requires SOD (e.g., enterprise compliance), it must be added as an optional business policy layer

### Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| ADMIN accidentally finalizes incomplete report | Finalization requires explicit confirmation UX (not a silent action) |
| Finalized record silently mutated | Immutability enforced at DB level; any post-finalization change creates a new correction record |
| Missing audit trail | All state transitions logged with actor, timestamp, and before/after snapshots |
| Future SOD requirement | Permission matrix is extensible — SOD can be added as a workspace-level policy toggle |

## Required Test Coverage

- **ADMIN superset:** Integration tests proving ADMIN can perform all TECHNICIAN actions (submit findings, view assigned jobs, etc.)
- **TECHNICIAN restrictions:** Tests proving TECHNICIAN cannot create jobs, finalize reports, or manage users
- **Finalization immutability:** Tests proving finalized records cannot be modified through any API endpoint
- **Correction workflow:** Tests proving post-finalization changes create new correction records, not mutations

## References

- [ADR-0034](./0034-role-aware-workspace-interaction.md) — Role-aware workspace interaction
- [NYC DOB Gas Piping Inspections](https://www.nyc.gov/site/buildings/property-or-business-owner/gas-piping-inspections.page) — LL152 rules
- [GPS1 Form](https://www.nyc.gov/assets/buildings/pdf/gps1.pdf) — Gas Piping System Periodic Inspection Report
- [LL152 Discovery 4](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/OPEN_DESIGN_QUESTIONS.md) — Finalization Boundary
