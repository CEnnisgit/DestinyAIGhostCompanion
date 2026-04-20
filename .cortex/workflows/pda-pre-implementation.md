---
description: Run the PDA-SDD Pre-Implementation phase (PRD → SRSD + RLD)
---

# PDA Pre-Implementation Workflow

This workflow executes Section 2 of the PDA-SDD Runbook: converting a PRD into a complete SRSD baseline.

## Prerequisites

- PRD document exists (e.g., `docs/PRD_LL152_PILOT.md`)
- PDA-SDD folder structure is in place (`docs/1-pre-implementation/`)

## Steps

### 1. PRD Extraction Pass

1. Read the PRD thoroughly.
2. Extract and document:
   - Goals and scope boundaries
   - Main user flows (lanes)
   - Functional requirements (features/behaviors)
   - Non-functional requirements (performance/security/usability)
   - Integrations, data entities, constraints
3. Create `docs/1-pre-implementation/PRD_EXTRACTION_NOTES.md` with findings.

### 2. Gap Scan

1. Identify missing or ambiguous items in the PRD:
   - Response-time targets
   - Data retention policies
   - Auth model (JWT? OAuth?)
   - Integration protocols
2. Document in an "Open Questions / Blockers" section.
3. Notify user of blockers before proceeding.

### 3. Build SGI (General Info)

1. Create/update `SRSD/SGI/SGI-S_scope.md` with:
   - In-Scope items
   - Out-of-Scope items (explicit)
2. Create/update `SRSD/SGI/SGI-OJ_objectives.md` with product goals.
3. Create/update `SRSD/SGI/SGI-MF_main-functions.md` with main functions.

### 4. Code Functional Requirements (SFR)

For each PRD feature, create a requirement with:
- **ID:** `SFR-[Category]-NN` (unique)
- **Statement:** "The system shall..."
- **Rationale:** 1-2 lines from PRD
- **Acceptance Criteria:** measurable checks
- **Priority:** Must/Should/Could
- **PRD Ref:** Section reference

Organize into:
- `SFR-IO_input-output.md` (Data Entry, Data Output, Reporting)
- `SFR-PR_processing.md` (Processing logic)
- `SFR-BR_business-rules.md` (Validation, Workflow, Constraints)
- `SFR-SR_security.md` (Functional security)
- `SFR-IR_integration.md` (Integrations)

### 5. Code Non-Functional Requirements (SNFR)

For each NFR, create a requirement with measurable targets:
- `SNFR-P_performance.md` (response time, throughput)
- `SNFR-U_usability.md` (mobile-first, accessibility)
- `SNFR-R_reliability.md` (uptime, error handling)
- `SNFR-S_security.md` (encryption, auth)
- `SNFR-SC_scalability.md` (concurrent users)
- `SNFR-M_maintainability.md` (code standards)

### 6. Build RLD (Resource List)

1. Create/update `docs/1-pre-implementation/RLD.md` with:
   - Team roles and counts
   - Key tools and technologies
   - Development environment

### 7. Verify Exit Gates

Before declaring Pre-Implementation complete:

// turbo
1. Run `pnpm run pda:check` to verify structure.
2. Verify all major PRD features have SFR/SNFR IDs.
3. Verify critical ambiguities are resolved or documented as blockers.
4. Verify RLD is complete enough for planning.

### 8. Notify User for Review

Request user review of:
- `docs/1-pre-implementation/SRSD/README.md`
- `docs/1-pre-implementation/RLD.md`
- Any documented blockers

## Exit Criteria

- All PRD features are expressed as coded requirements (SFR/SNFR).
- Main Functions (SGI-MF) are defined.
- Critical ambiguities are resolved or explicitly accepted.
- RLD is complete.
- `pnpm run pda:check` passes.
