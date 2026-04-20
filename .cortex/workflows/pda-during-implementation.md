---
description: Run the PDA-SDD During-Implementation phase (DDD + CLD population)
---

# PDA During-Implementation Workflow

This workflow executes Section 4 of the PDA-SDD Runbook: populating the DDD and maintaining the CLD.

## Prerequisites

- Pre-Implementation phase complete (SRSD baseline stable)
- `pnpm run pda:check` passes
- DDD folder structure exists (`docs/2-during-implementation/DDD/`)

## Steps

### 1. Traceability Matrix Audit (First Non-Negotiable)

1. Open `DDD/TraceabilityMatrix.md`.
2. For each SRSD requirement:
   - Verify a DDD Module is assigned (no `TBD` on active items).
   - Verify module name matches `valid-modules.json`.
3. Update status columns as needed.

// turbo
4. Run `pnpm run pda:check --strict` to validate.

### 2. System Architecture

1. Open `DDD/SystemArchitecture/HighLevelDiagram.md`.
2. Update/create Mermaid diagram reflecting current code structure.
3. Verify component names match TraceabilityMatrix module names.
4. Open `DDD/SystemArchitecture/TechnologyStack.md`.
5. Verify versions match `package.json`.

### 3. Data Design

1. Open `DDD/DataDesign/ERD.md`.
2. Update entity tables from current Drizzle schema files.
3. Update Mermaid ER diagram.
4. Document any SRSD Gap Analysis (required fields missing from code).
5. Open `DDD/DataDesign/DatabaseSchema.md`.
6. Update table definitions from `apps/backend/src/infrastructure/db/schema/`.

### 4. Interface Design

1. Open `DDD/InterfaceDesign/UI_Specs.md`.
2. Document screens from mobile app and dashboard.
3. Add user flows with diagrams.
4. Open `DDD/InterfaceDesign/API_Specs.md`.
5. Document endpoints from backend routes.
6. Include request/response shapes.

### 5. Module Design

For each module in `ModuleDesign/`:
1. Open `ModuleDesign/[Name]/README.md`.
2. Update `## Traceability` with SRSD requirement links.
3. Update `## Module Responsibilities` with actual responsibilities.
4. Update `## Module Structure` with class diagrams from code.
5. Update `## Module Interactions` with sequence diagrams.
6. Update `## Algorithm Descriptions` for key algorithms.
7. Update `## Data Structure Selection` referencing DataDesign.

### 6. CLD Logging

For any changes made during this phase:
1. Create a CLD entry in the appropriate feature folder.
2. Include: Date, Summary, Detailed Changes, SRSD References, Author.

### 7. Verify Exit Gates

// turbo
1. Run `pnpm run pda:check` to verify structure.
2. Verify Traceability Matrix has no `TBD` on active items.
3. Verify CLD has entries for major changes.
4. Verify DDD reflects actual code (not stale plans).

### 8. Notify User for Review

Request user review of:
- `DDD/TraceabilityMatrix.md`
- Updated module READMEs

## Exit Criteria

- Every implemented requirement is mapped in TraceabilityMatrix.
- CLD is current with recent changes logged.
- DDD architecture/interfaces/modules match what was actually built.
- `pnpm run pda:check` passes.
