# Phase 2: Field Capture + Submission (Lane A)

> **Status**: ⏳ Pending
> **Prerequisite**: Phase 1 Complete
> **Unlocks**: Phase 3

---

## Goal

Plumber can view job details, complete GPS1 form, attach photos, and submit findings.

---

## Main Functions (SGI-MF)

- **Field Capture**: Plumber completes GPS1-structured form on mobile
- **Photo Evidence**: Plumber attaches photos to inspection
- **Submission**: Plumber submits findings to LMP for review

---

## Checklist

### Backend API

- [ ] **2.1** Job Detail API
  - [ ] `GET /jobs/:id` with full job data
  - [ ] Include building details
  - [ ] Include existing inspection data (if resuming)
- [ ] **2.2** Inspection Data API
  - [ ] `PUT /jobs/:id/inspection` for saving draft
  - [ ] `POST /jobs/:id/submit` for final submission
  - [ ] Validate required fields before submission
- [ ] **2.3** Photo Upload API
  - [ ] `POST /jobs/:id/photos` with multipart upload
  - [ ] Validate file type/size per PhotoStandards
  - [ ] Store in StorageModule
  - [ ] Return photo URLs

### Mobile App

- [ ] **2.4** Job Detail View
  - [ ] Display building address
  - [ ] Display access notes
  - [ ] "Start Inspection" button
- [ ] **2.5** GPS1 Inspection Form
  - [ ] Multi-section form structure
  - [ ] Progress indicator
  - [ ] Auto-save draft locally
- [ ] **2.6** Form Fields
  - [ ] Date picker (inspection date)
  - [ ] Dropdowns for conditions
  - [ ] Text inputs for notes
  - [ ] Stop-condition triggers
- [ ] **2.7** Photo Capture
  - [ ] Camera integration
  - [ ] Photo preview
  - [ ] Multiple photo support
  - [ ] Photo labeling
- [ ] **2.8** Submission Flow
  - [ ] Validation before submit
  - [ ] Confirmation dialog
  - [ ] Submit button
  - [ ] Success/error feedback

### Validation Logic

- [ ] **2.9** Required Fields Check ([SFR-BRV-01](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md))
- [ ] **2.10** Photo Minimum ([SFR-BRV-02](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md))
- [ ] **2.11** Stop Conditions ([SFR-BRC-04](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md))

---

## Requirements Covered

| Module | Key SFRs |
| :--- | :--- |
| [InspectionsModule](../2-during-implementation/DDD/ModuleDesign/Inspections/README.md) | [SFR-IODE-01](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IODE-03](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IODE-04](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-BRC-02](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRC-03](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRC-04](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRV-01](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRV-02](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRW-03](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) |
| [StorageModule](../2-during-implementation/DDD/ModuleDesign/Storage/README.md) | [SFR-IODE-02](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IRDX-02](../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md), [SFR-IRI-03](../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) |

---

## Verification

```bash
pnpm --filter @pcd/backend build
pnpm run pda:check

# After each feature
/pda-sync-feature
```

---

## Completion Criteria

- [ ] All checklist items marked complete
- [ ] Plumber can view job details
- [ ] Plumber can complete GPS1 form
- [ ] Plumber can attach photos
- [ ] Plumber can submit inspection
- [ ] Phase marked complete in [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)
