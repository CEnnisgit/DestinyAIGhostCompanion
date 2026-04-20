---
description: Generate a comprehensive status report for Lane A (Plumber workflow)
---

# Lane A Status Report (Plumber)

Generates a comprehensive status report for all Lane A (Plumber) requirements and implementation status.

## Lane A Scope

Lane A covers the **Plumber field workflow**:
- Mobile field capture of GPS1 inspection data
- Photo attachments
- Job viewing and submission

## Steps

### 1. Identify Lane A Requirements

Lane A requirements are identified by:
- **SFR-IODE-01 to SFR-IODE-04** (Plumber Data Entry)
- **SFR-IODO-01 to SFR-IODO-03** (Plumber Views)
- Related validation/workflow requirements

Search TraceabilityMatrix.md for requirements with:
- "Plumber" in description
- Module: `FieldCaptureModule`

### 2. Gather Data

For each Lane A requirement, extract from TraceabilityMatrix.md:
- Requirement ID
- Description
- Priority (Must/Should/Could)
- DDD Module
- Code Status
- Test Status

### 3. Check Module Design Status

Open `DDD/ModuleDesign/FieldCapture/README.md` and assess:
- [ ] Traceability section complete?
- [ ] Module Responsibilities documented?
- [ ] Module Structure (class diagram) present?
- [ ] Module Interactions (sequence diagram) present?
- [ ] Algorithms documented?

### 4. Check Interface Design Status

Open `DDD/InterfaceDesign/UI_Specs.md` and check for:
- [ ] Assigned Jobs List screen spec?
- [ ] Job Detail View screen spec?
- [ ] Inspection Capture screen spec?
- [ ] Submit Confirmation screen spec?

### 5. Check Data Design Status

Open `DDD/DataDesign/` and verify:
- [ ] InspectionForm entity in ERD?
- [ ] InspectionPhoto entity in ERD?
- [ ] inspection_forms table in DatabaseSchema?
- [ ] inspection_photos table in DatabaseSchema?

### 6. Check CLD for Recent Activity

Scan `CLD/FIELD_CAPTURE/` for:
- Recent entries
- Outstanding issues

### 7. Generate Report

Output a markdown report with:

```markdown
# Lane A (Plumber) Status Report
**Generated:** [Date]

## Summary
| Metric | Value |
|--------|-------|
| Total Requirements | X |
| Must Requirements | X |
| Implemented | X |
| In Progress | X |
| Not Started | X |
| Completion % | X% |

## Requirements Detail
| ID | Description | Priority | Status | Module |
|----|-------------|----------|--------|--------|
| ... | ... | ... | ... | ... |

## Module Design Status
- FieldCaptureModule: [Complete/Partial/TBD]

## Interface Design Status
- UI Screens: X/4 documented

## Data Design Status
- Entities: X/2 documented

## Blockers/Risks
- [List any blockers]

## Recent CLD Activity
- [List recent changes]
```
