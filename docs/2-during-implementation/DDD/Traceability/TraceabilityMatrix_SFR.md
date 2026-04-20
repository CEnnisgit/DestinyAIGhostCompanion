# Traceability Matrix: Functional Requirements (SFR)

> **Source of Truth:** [SRSD Directory](../../../1-pre-implementation/SRSD/README.md)

 Mapping **Functional Requirements** to **DDD Modules**.
 For implementation status and details, refer to the **TRACEABILITY.md** file in each [ModuleDesign](../ModuleDesign/) folder.

| SRSD Req ID | Statement (1 line) | Type | DDD Module(s) | Notes |
| :--- | :--- | :---: | :--- | :--- |
| [SFR-SRAC-01](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Technician Scope | SFR | `Jobs:Capture` |  |
| [SFR-SRAC-02](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Admin Scope | SFR | `Jobs:Dispatch` |  |
| [SFR-SRAC-10](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Action Logging | SFR | `SharedKernelModule` |  |
| [SFR-SRAN-01](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Email/Password Login | SFR | `AuthModule` |  |
| [SFR-SRAN-02](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Session Tokens | SFR | `AuthModule` |  |
| [SFR-SRAN-03](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Password Reset | SFR | `AuthModule` |  |
| [SFR-SRAN-04](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Logout | SFR | `AuthModule` |  |
| [SFR-SRAZ-01](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Create Job | SFR | `Jobs:Dispatch` |  |
| [SFR-SRAZ-02](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Dispatch Job | SFR | `Jobs:Dispatch` |  |
| [SFR-SRAZ-03](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | View Assigned Jobs | SFR | `Jobs:Dispatch` |  |
| [SFR-SRAZ-04](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Submit Findings | SFR | `Jobs:Capture` |  |
| [SFR-SRAZ-05](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Approve/Return | SFR | `Jobs:Compliance` |  |
| [SFR-SRAZ-06](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Generate Report | SFR | `ReportingModule` |  |
| [SFR-IODE-11](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Building Profile | SFR | `CRMModule:Assets` |  |
| [SFR-PRC-04](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Compliance Year | SFR | `CRMModule:Assets` |  |
| [SFR-BRC-01](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Single Assignment | SFR | `Jobs:Dispatch` |  |
| [SFR-BRC-02](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Inspection Date Required | SFR | `Jobs:Compliance` |  |
| [SFR-BRC-03](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Community District Required | SFR | `Jobs:Compliance` |  |
| [SFR-BRC-04](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | [TBD] Stop-Conditions | SFR | `Jobs:Capture` |  |
| [SFR-BRC-10](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | No Backward Transitions | SFR | `Jobs:Dispatch` |  |
| [SFR-BRC-11](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Return Only Before Finalize | SFR | `Jobs:Dispatch` |  |
| [SFR-BRV-01](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Required Fields Check | SFR | `Jobs:Compliance` |  |
| [SFR-BRV-02](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Photo Minimum | SFR | `Jobs:Compliance` |  |
| [SFR-BRV-03](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Inspection Date Valid | SFR | `Jobs:Compliance` |  |
| [SFR-BRV-10](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Address Required | SFR | `Jobs:Compliance` |  |
| [SFR-BRV-11](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Owner Contact Recommended | SFR | `Jobs:Compliance` |  |
| [SFR-BRW-01](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Intake → Dispatched | SFR | `Jobs:Dispatch` |  |
| [SFR-BRW-02](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Dispatched → In Progress | SFR | `Jobs:Dispatch` |  |
| [SFR-BRW-03](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | In Progress → Submitted | SFR | `Jobs:Capture` |  |
| [SFR-BRW-04](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Submitted → Finalized | SFR | `Jobs:Compliance` |  |
| [SFR-BRW-05](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Submitted → Returned | SFR | `Jobs:Compliance` |  |
| [SFR-BRW-06](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Finalized → Delivered | SFR | `Jobs` |  |
| [SFR-IODE-01](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | GPS1-Structured Capture | SFR | `Jobs:Capture` |  |
| [SFR-IODE-03](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Notes/Comments | SFR | `Jobs:Capture` |  |
| [SFR-IODE-04](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Stop-the-line Flags | SFR | `Jobs:Capture` |  |
| [SFR-IODE-10](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Job Header | SFR | `Jobs:Dispatch` |  |
| [SFR-IODE-12](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Dispatch Info | SFR | `Jobs:Dispatch` |  |
| [SFR-IODO-01](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Assigned Jobs List | SFR | `Jobs:Capture` |  |
| [SFR-IODO-02](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Job Detail View | SFR | `Jobs:Capture` |  |
| [SFR-IODO-03](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Submission Confirmation | SFR | `Jobs:Capture` |  |
| [SFR-IODO-10](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Job Queue | SFR | `Jobs:Dispatch` |  |
| [SFR-IODO-11](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Review Panel | SFR | `Jobs:Compliance` |  |
| [SFR-IODO-12](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Deadline Dashboard | SFR | `Jobs:Compliance` |  |
| [SFR-IRDX-01](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | Request/Response | SFR | `Jobs:Capture` |  |
| [SFR-IRDX-10](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | Online-First | SFR | `Jobs:Capture` |  |
| [SFR-IRI-01](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | Mobile App → Backend | SFR | `Jobs:Capture` |  |
| [SFR-IRI-02](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | Dashboard → Backend | SFR | `Jobs:Capture` |  |
| [SFR-IRI-10](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | DOB Portal | SFR | `Jobs:Compliance` |  |
| [SFR-IRIN-01](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | Mobile | SFR | `Jobs:Capture` |  |
| [SFR-IRIN-02](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | Desktop | SFR | `Jobs:Dispatch` |  |
| [SFR-PRC-01](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | GPS1 Due Date | SFR | `Jobs:Compliance` |  |
| [SFR-PRC-02](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | GPS2 Due Date | SFR | `Jobs:Compliance` |  |
| [SFR-PRC-03](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Correction Window | SFR | `Jobs:Compliance` |  |
| [SFR-PRC-05](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | [TBD] Sub-Cycle Map | SFR | `Jobs` |  |
| [SFR-PRC-10](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Time-to-Capture | SFR | `Jobs` |  |
| [SFR-PRDM-01](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Plumber Assignment | SFR | `Jobs` |  |
| [SFR-PRDM-02](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Auto-Routing (Future) | SFR | `Jobs` |  |
| [SFR-PRDM-10](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Completeness Check | SFR | `Jobs` |  |
| [SFR-PRDM-11](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Approve/Return Decision | SFR | `Jobs` |  |
| [SFR-PRDM-12](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Escalation Check | SFR | `Jobs` |  |
| [SFR-PRDP-01](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Sort by Scheduled Date | SFR | `Jobs` |  |
| [SFR-PRDP-02](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Filter by Status | SFR | `Jobs` |  |
| [SFR-PRDP-03](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Search by Address | SFR | `Jobs` |  |
| [SFR-BRW-10](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Dispatch Notification | SFR | `NotificationModule` |  |
| [SFR-BRW-11](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Submission Notification | SFR | `NotificationModule` |  |
| [SFR-BRW-12](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Return Notification | SFR | `NotificationModule` |  |
| [SFR-BRW-13](../../../1-pre-implementation/SRSD/SFR/SFR-BR_business-rules.md) | Deadline Reminder | SFR | `NotificationModule` |  |
| [SFR-IRI-11](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | Email Delivery | SFR | `NotificationModule` |  |
| [SFR-IODO-13](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Search/History | SFR | `ReportingModule` |  |
| [SFR-IOR-01](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | GPS1 Report Generation | SFR | `ReportingModule` |  |
| [SFR-IOR-02](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | GPS2 Draft Generation | SFR | `ReportingModule` |  |
| [SFR-IOR-03](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Owner Packet Export | SFR | `ReportingModule` |  |
| [SFR-IOR-04](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Archival Export | SFR | `ReportingModule` |  |
| [SFR-IRDX-03](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | Export Formats | SFR | `ReportingModule` |  |
| [SFR-IRIN-10](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | GPS1/GPS2 Format | SFR | `ReportingModule` |  |
| [SFR-PRDP-10](../../../1-pre-implementation/SRSD/SFR/SFR-PR_processing.md) | Funnel Counts | SFR | `ReportingModule` |  |
| [SFR-IODE-02](../../../1-pre-implementation/SRSD/SFR/SFR-IO_input-output.md) | Photo Attachments | SFR | `Jobs:Capture` |  |
| [SFR-IRDX-02](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | File Uploads | SFR | `StorageModule` |  |
| [SFR-IRI-03](../../../1-pre-implementation/SRSD/SFR/SFR-IR_integration.md) | File Upload | SFR | `StorageModule` |  |
| [SFR-SRAC-03](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Company Isolation | SFR | `UsersModule:Company` |  |
| [SFR-SRAZ-07](../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md) | Manage Users | SFR | `UsersModule:Employees` |  |
