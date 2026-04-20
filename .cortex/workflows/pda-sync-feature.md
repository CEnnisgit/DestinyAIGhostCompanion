---
description: Sync DDD documentation for a single feature (cyclical During-Implementation)
---

# PDA Sync Feature Workflow

Lightweight, repeatable workflow for updating DDD documentation after implementing a feature or fixing a bug.

## Prerequisites

- Feature/change is implemented in code
- You know which SRSD requirement(s) it addresses

## Inputs

Ask user for:
1. **Feature/Change Description** - What was implemented?
2. **SRSD Requirement ID(s)** - Which requirements does this address?

## Steps

### 1. Update Traceability Matrix

1. Open `DDD/TraceabilityMatrix.md`.
2. Find the SRSD requirement row(s).
3. Update:
   - **DDD Module** (if not already set)
   - **Status** (e.g., "In Progress" → "Implemented")
   - **Notes** (if relevant)

### 2. Update Affected Module Design

1. Identify the owning module from TraceabilityMatrix.
2. Open `DDD/ModuleDesign/[Module]/README.md`.
3. Update sections as needed:
   - `## Module Responsibilities` - Add new responsibility if applicable
   - `## Module Structure` - Update class diagram if new classes/functions
   - `## Module Interactions` - Update sequence diagram if new flows
   - `## Algorithm Descriptions` - Document any new algorithms

### 3. Update Data Design (If Schema Changed)

If the feature added/modified database tables:
1. Open `DDD/DataDesign/DatabaseSchema.md` - Update table definitions.
2. Open `DDD/DataDesign/ERD.md` - Update entity diagram.
3. Open `DDD/DataDesign/DataStructures.md` - Update shared types.

### 4. Update Interface Design (If API/UI Changed)

If the feature added/modified endpoints or screens:
1. Open `DDD/InterfaceDesign/API_Specs.md` - Document new endpoints.
2. Open `DDD/InterfaceDesign/UI_Specs.md` - Document new screens/flows.

### 5. Log to CLD

1. Identify the CLD feature folder (or create one).
2. Add entry to `docs/2-during-implementation/CLD/[FEATURE]/README.md`:

```markdown
## [Date] - [Summary]

**Significance:** Major/Minor
**Domain:** Code/Design/Requirements
**SRSD Refs:** SFR-XXX-NN
**Author:** [Name]

### Changes
- [Bullet list of changes]
```

### 6. Verify

// turbo
1. Run `pnpm run pda:check` to verify structural integrity.

## Output

- Updated TraceabilityMatrix with current status
- Updated Module Design (if applicable)
- Updated Data/Interface Design (if applicable)
- CLD entry documenting the change
