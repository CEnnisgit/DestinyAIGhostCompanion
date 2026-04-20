# Phase 3: Review + Report Generation (Lane B)

> **Status**: ⏳ Pending
> **Prerequisite**: Phase 2 Complete
> **Unlocks**: Phase 4

---

## Goal

LMP can review submissions, approve/return, and generate GPS1/GPS2 PDF reports.

---

## Main Functions (SGI-MF)

- **Review**: LMP reviews submission, approves or returns
- **Report Generation**: System generates GPS1/GPS2 PDF packet

---

## Checklist

### Backend API

- [ ] **3.1** Review Queue API
  - [ ] `GET /jobs?status=SUBMITTED` for pending reviews
  - [ ] Include submission data
- [ ] **3.2** Approve API
  - [ ] `POST /jobs/:id/approve`
  - [ ] Transition to FINALIZED
  - [ ] Trigger report generation
- [ ] **3.3** Return API
  - [ ] `POST /jobs/:id/return`
  - [ ] Include return_reason
  - [ ] Transition to RETURNED
- [ ] **3.4** Report Generation
  - [ ] `ReportingService.generateGPS1Report()`
  - [ ] `ReportingService.generateGPS2Draft()`
  - [ ] PDF template with inspection data
  - [ ] Store in StorageModule
- [ ] **3.5** Report Download API
  - [ ] `GET /jobs/:id/report`
  - [ ] Return signed URL

### Dashboard (Web)

- [ ] **3.6** Review Panel
  - [ ] List submitted jobs
  - [ ] Click to view inspection details
  - [ ] View attached photos
- [ ] **3.7** Approval Actions
  - [ ] Approve button
  - [ ] Return button with reason input
- [ ] **3.8** Report Access
  - [ ] Download GPS1 PDF
  - [ ] Download GPS2 Draft

### Export Features

- [ ] **3.9** Owner Packet Export
- [ ] **3.10** Archival Export

---

## Requirements Covered

| Module | Key SFRs |
| :--- | :--- |
| [InspectionsModule](../2-during-implementation/DDD/ModuleDesign/Inspections/README.md) | [SFR-BRW-04](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRW-05](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRW-06](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-IODO-11](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-PRDM-10](../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md), [SFR-PRDM-11](../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) |
| [ReportingModule](../2-during-implementation/DDD/ModuleDesign/Reporting/README.md) | [SFR-IOR-01](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IOR-02](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IOR-03](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IOR-04](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IRDX-03](../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md), [SFR-IRIN-10](../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md), [SFR-PRDP-10](../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) |

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
- [ ] LMP can review submitted jobs
- [ ] LMP can approve or return jobs
- [ ] GPS1 PDF generates correctly
- [ ] Phase marked complete in [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)
