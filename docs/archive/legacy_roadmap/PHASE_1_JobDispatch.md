# Phase 1: Job Intake + Dispatch (Lane B)

> **Status**: ⏳ Pending
> **Prerequisite**: Phase 0 Complete
> **Unlocks**: Phase 2

---

## Goal

LMP can create jobs, assign technicians, and manage job queue. Plumber can see assigned jobs in mobile app.

---

## Main Functions (SGI-MF)

- **Job Intake**: LMP creates new LL152 job with address and access details
- **Dispatch**: LMP assigns technician and schedules job

---

## Checklist

### Backend API

- [ ] **1.1** Job Creation API
  - [ ] `POST /jobs` endpoint
  - [ ] Request validation (building_id, access_notes)
  - [ ] Creates `inspection_jobs` record with status `PENDING`
- [ ] **1.2** Job List API
  - [ ] `GET /jobs` with company isolation
  - [ ] Pagination support
  - [ ] Filter by status
- [ ] **1.3** Dispatch API
  - [ ] `POST /jobs/:id/dispatch` endpoint
  - [ ] Assigns technician_id
  - [ ] Sets scheduled_start/scheduled_end
  - [ ] Transitions status to `SCHEDULED`
- [ ] **1.4** Job State Machine
  - [ ] Valid transitions: PENDING → SCHEDULED
  - [ ] Reject invalid transitions
  - [ ] SFR-BRC-01: Single Assignment enforced

### Dashboard (Web)

- [ ] **1.5** Job Queue View
  - [ ] List jobs with status badges
  - [ ] Sort by scheduled date
  - [ ] Filter by status
- [ ] **1.6** Job Creation Form
  - [ ] Building selector
  - [ ] Access notes input
  - [ ] Submit creates job
- [ ] **1.7** Dispatch Panel
  - [ ] Technician selector
  - [ ] Date/time picker
  - [ ] Dispatch button

### Mobile App

- [ ] **1.8** Assigned Jobs List
  - [ ] Fetch jobs for logged-in technician
  - [ ] Display job cards with address/status
  - [ ] Pull to refresh

---

## Requirements Covered

| Module | Key SFRs |
| :--- | :--- |
| [InspectionsModule](../2-during-implementation/DDD/ModuleDesign/Inspections/README.md) | [SFR-BRW-01](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRW-02](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRC-01](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-IODE-10](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IODE-12](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IODO-01](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md), [SFR-IODO-10](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) |
| [UsersModule](../2-during-implementation/DDD/ModuleDesign/Users/README.md) | [SFR-SRAC-03](../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) (Company Isolation) |
| [CRMModule](../2-during-implementation/DDD/ModuleDesign/CRM/README.md) | [SFR-IODE-11](../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) (Building Profile) |

---

## Verification

```bash
# Build
pnpm --filter @pcd/backend build

# PDA Check
pnpm run pda:check

# After each feature
/pda-sync-feature
```

---

## Completion Criteria

- [ ] All checklist items marked complete
- [ ] LMP can create a job via Dashboard
- [ ] LMP can dispatch job to technician
- [ ] Technician sees job in Mobile app
- [ ] Phase marked complete in [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)
