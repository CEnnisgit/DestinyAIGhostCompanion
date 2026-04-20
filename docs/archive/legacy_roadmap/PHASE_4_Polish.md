# Phase 4: Polish + Alerts

> **Status**: ⏳ Pending
> **Prerequisite**: Phase 3 Complete
> **Unlocks**: Production Readiness

---

## Goal

Add notifications, deadline tracking, and handle edge cases for production readiness.

---

## Main Functions (SGI-MF)

- **Deadline Tracking**: System calculates and alerts on compliance deadlines

---

## Checklist

### Deadline Tracking

- [ ] **4.1** DeadlineService Implementation
  - [ ] `calculateGPS1DueDate()` logic
  - [ ] `calculateGPS2DueDate()` logic
  - [ ] Correction window calculation
- [ ] **4.2** Sub-Cycle Map Population
  - [ ] Full Community District → Cycle mapping
  - [ ] Compliance year calculation
- [ ] **4.3** Deadline Dashboard View
  - [ ] "Approaching Deadline" queue
  - [ ] "Past Due" alerts
  - [ ] Sort by urgency

### Notifications

- [ ] **4.4** Dispatch Notification
  - [ ] Email to technician when job assigned
  - [ ] Include job details and schedule
- [ ] **4.5** Submission Notification
  - [ ] Email to LMP when job submitted
  - [ ] Include job summary
- [ ] **4.6** Return Notification
  - [ ] Email to technician when job returned
  - [ ] Include return reason
- [ ] **4.7** Deadline Reminder
  - [ ] Scheduled job to check deadlines
  - [ ] Email LMP for approaching deadlines
  - [ ] Configurable reminder window

### Edge Cases

- [ ] **4.8** Stop Conditions Handling
  - [ ] Abort job flow
  - [ ] Reschedule flow
  - [ ] Proper status transitions
- [ ] **4.9** Returned Job Resubmission
  - [ ] Technician can re-open returned job
  - [ ] Edit and resubmit
  - [ ] Track revision history

---

## Requirements Covered

| Module | Key SFRs |
| :--- | :--- |
| [InspectionsModule](../2-during-implementation/DDD/ModuleDesign/Inspections/README.md) | [SFR-PRC-01](../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md), [SFR-PRC-02](../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md), [SFR-PRC-03](../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md), [SFR-PRC-04](../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md), [SFR-PRC-05](../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) |
| [NotificationModule](../2-during-implementation/DDD/ModuleDesign/Notification/README.md) | [SFR-BRW-10](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRW-11](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRW-12](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-BRW-13](../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md), [SFR-IRI-11](../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) |

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
- [ ] Deadline calculations verified
- [ ] Notifications sending correctly
- [ ] Edge cases handled
- [ ] Phase marked complete in [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)
- [ ] Ready for production deployment review
