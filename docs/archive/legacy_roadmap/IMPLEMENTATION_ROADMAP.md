# Implementation Roadmap: LL152 Pilot

> **Approach**: Option E (Hybrid — Dependency-Based + Feature-Slices)
> **Status**: Active

---

## Overview

This roadmap organizes implementation into 5 phases, balancing **dependency order** (foundation first) with **vertical slices** (end-to-end value delivery).

---

## Phase Index

| Phase | Document | Status | Focus |
| :---: | :--- | :---: | :--- |
| **0** | [PHASE_0_Foundation.md](./PHASE_0_Foundation.md) | ⏳ Pending | Verify Auth/Config stable |
| **1** | [PHASE_1_JobDispatch.md](./PHASE_1_JobDispatch.md) | ⏳ Pending | LMP: Job Intake + Dispatch |
| **2** | [PHASE_2_FieldCapture.md](./PHASE_2_FieldCapture.md) | ⏳ Pending | Plumber: Field Capture + Submission |
| **3** | [PHASE_3_Reporting.md](./PHASE_3_Reporting.md) | ⏳ Pending | LMP: Review + Report Generation |
| **4** | [PHASE_4_Polish.md](./PHASE_4_Polish.md) | ⏳ Pending | Notifications, Deadline Alerts |

---

## Dependency Graph

```mermaid
    flowchart TD
        subgraph Phase0[Phase 0: Foundation]
            Auth[AuthModule]
            Shared[SharedKernelModule]
        end
        
        subgraph Phase1[Phase 1: Support + Job Intake]
            Users[UsersModule]
            CRM[CRMModule]
            Inspections[InspectionsModule]
        end
        
        subgraph Phase2[Phase 2: Field Capture]
            Storage[StorageModule]
        end
        
        subgraph Phase3[Phase 3: Review + Reporting]
            Reporting[ReportingModule]
        end
        
        subgraph Phase4[Phase 4: Polish]
            Notification[NotificationModule]
        end
        
        Auth --> Users
        Auth --> CRM
        Users --> Inspections
        CRM --> Inspections
        Inspections --> Storage
        Inspections --> Reporting
        Inspections --> Notification
    ```

---

## Rules for Agents

> [!IMPORTANT]
> **One phase at a time.** Do not jump ahead to the next phase until the current phase document is marked complete.

1. Open the **current phase document** (see index above)
2. Work through the checklist in that document
3. Run `/pda-sync-feature` after each feature
4. Mark tasks complete in the phase document
5. Only proceed to next phase when explicitly approved

---

## Quick Links

- [PRD](../PRD_LL152_PILOT.md)
- [SRSD](../1-pre-implementation/SRSD/README.md)
- [DDD](../2-during-implementation/DDD/README.md)
- [Agent Onboarding](../../.agent/ONBOARDING.md)
