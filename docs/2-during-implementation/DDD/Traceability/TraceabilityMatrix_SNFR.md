# Traceability Matrix: Non-Functional Requirements (SNFR)

> **Source of Truth:** [SRSD Directory](../../../1-pre-implementation/SRSD/README.md)

 Mapping **Non-Functional Requirements** to **DDD Modules**.
 For implementation status and details, refer to the **TRACEABILITY.md** file in each [ModuleDesign](../ModuleDesign/) folder.

| SRSD Req ID | Statement (1 line) | Type | DDD Module(s) | Notes |
| :--- | :--- | :---: | :--- | :--- |
| [SNFR-SA-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Rate Limiting | SNFR | `AuthModule` |  |
| [SNFR-SA-03](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Token Expiry | SNFR | `AuthModule` |  |
| [SNFR-SC-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Password Storage | SNFR | `AuthModule` |  |
| [SNFR-RAC-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Compliance Cycle | SNFR | `CRMModule` |  |
| [SNFR-SC-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Owner PII | SNFR | `CRMModule` |  |
| [SNFR-UE-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Pre-filled Address | SNFR | `CRMModule` |  |
| [SNFR-PRT-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-P_performance.md) | Mobile Screen Load | SNFR | `Jobs` |  |
| [SNFR-PRT-03](../../../1-pre-implementation/SRSD/SNFR/SNFR-P_performance.md) | Form Field Interaction | SNFR | `Jobs` |  |
| [SNFR-PT-03](../../../1-pre-implementation/SRSD/SNFR/SNFR-P_performance.md) | Jobs per Day | SNFR | `Jobs` |  |
| [SNFR-RAC-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Deadline Calculation | SNFR | `Jobs` |  |
| [SNFR-RAC-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | No Data Loss on Submit | SNFR | `Jobs` |  |
| [SNFR-RR-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Draft Persistence | SNFR | `Jobs` |  |
| [SNFR-RR-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Sync on Reconnect | SNFR | `Jobs` |  |
| [SNFR-SI-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Inspection Immutability | SNFR | `Jobs` |  |
| [SNFR-UA-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | High Contrast Mode | SNFR | `Jobs` |  |
| [SNFR-UA-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Clean, Modern UI | SNFR | `Jobs` |  |
| [SNFR-UA-03](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Status Colors | SNFR | `Jobs` |  |
| [SNFR-UA-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Font Size | SNFR | `Jobs` |  |
| [SNFR-UA-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Touch Targets | SNFR | `Jobs` |  |
| [SNFR-UE-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Time-to-Capture | SNFR | `Jobs` |  |
| [SNFR-UE-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | No Retyping | SNFR | `Jobs` |  |
| [SNFR-UE-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Default Inspection Date | SNFR | `Jobs` |  |
| [SNFR-UEU-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Phone-First Design | SNFR | `Jobs` |  |
| [SNFR-UEU-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | One-Handed Operation | SNFR | `Jobs` |  |
| [SNFR-UEU-03](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Max Taps to Job | SNFR | `Jobs` |  |
| [SNFR-UEU-04](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Zero Training Start | SNFR | `Jobs` |  |
| [SNFR-UEU-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | At-a-Glance Status | SNFR | `Jobs` |  |
| [SNFR-UEU-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | Deadline Visibility | SNFR | `Jobs` |  |
| [SNFR-PRT-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-P_performance.md) | PDF Generation | SNFR | `ReportingModule` |  |
| [SNFR-MM-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Feature-Slice Architecture | SNFR | `SharedKernelModule` |  |
| [SNFR-MM-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Hexagonal/Ports-Adapters | SNFR | `SharedKernelModule` |  |
| [SNFR-MM-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | TypeScript Strict | SNFR | `SharedKernelModule` |  |
| [SNFR-MM-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | ESLint Compliance | SNFR | `SharedKernelModule` |  |
| [SNFR-MM-12](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Documentation | SNFR | `SharedKernelModule` |  |
| [SNFR-MP-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Frontend | SNFR | `SharedKernelModule` |  |
| [SNFR-MP-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Backend | SNFR | `SharedKernelModule` |  |
| [SNFR-MP-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Dev/Staging/Prod | SNFR | `SharedKernelModule` |  |
| [SNFR-MP-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Database Migration | SNFR | `SharedKernelModule` |  |
| [SNFR-MT-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Unit Test Coverage | SNFR | `SharedKernelModule` |  |
| [SNFR-MT-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Integration Tests | SNFR | `SharedKernelModule` |  |
| [SNFR-MT-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Lint Gate | SNFR | `SharedKernelModule` |  |
| [SNFR-MT-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Type Gate | SNFR | `SharedKernelModule` |  |
| [SNFR-MT-12](../../../1-pre-implementation/SRSD/SNFR/SNFR-M_maintainability.md) | Test Gate | SNFR | `SharedKernelModule` |  |
| [SNFR-PRT-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-P_performance.md) | API Response (p95) | SNFR | `SharedKernelModule` |  |
| [SNFR-PT-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-P_performance.md) | Concurrent Users | SNFR | `SharedKernelModule` |  |
| [SNFR-RAV-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | System Uptime | SNFR | `SharedKernelModule` |  |
| [SNFR-RAV-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Scheduled Maintenance | SNFR | `SharedKernelModule` |  |
| [SNFR-RAV-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Database Backups | SNFR | `SharedKernelModule` |  |
| [SNFR-RAV-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Recovery Time Objective (RTO) | SNFR | `SharedKernelModule` |  |
| [SNFR-RR-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Graceful Degradation | SNFR | `SharedKernelModule` |  |
| [SNFR-RR-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Retry Logic | SNFR | `SharedKernelModule` |  |
| [SNFR-SA-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | DDoS Protection | SNFR | `SharedKernelModule` |  |
| [SNFR-SC-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Data in Transit | SNFR | `SharedKernelModule` |  |
| [SNFR-SC-12](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | [TBD] Data Retention | SNFR | `SharedKernelModule` |  |
| [SNFR-SCI-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-SC_scalability.md) | Cloud Run Auto-Scaling | SNFR | `SharedKernelModule` |  |
| [SNFR-SCI-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-SC_scalability.md) | Database Connection Pooling | SNFR | `SharedKernelModule` |  |
| [SNFR-SCS-01](../../../1-pre-implementation/SRSD/SNFR/SNFR-SC_scalability.md) | Post-Pilot (3 companies) | SNFR | `SharedKernelModule` |  |
| [SNFR-SCS-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-SC_scalability.md) | Future Growth | SNFR | `SharedKernelModule` |  |
| [SNFR-SI-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Audit Trail | SNFR | `SharedKernelModule` |  |
| [SNFR-SI-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Input Validation | SNFR | `SharedKernelModule` |  |
| [SNFR-SI-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | CSRF Protection | SNFR | `SharedKernelModule` |  |
| [SNFR-PRT-10](../../../1-pre-implementation/SRSD/SNFR/SNFR-P_performance.md) | Photo Upload (per photo, on 4G) | SNFR | `StorageModule` |  |
| [SNFR-PT-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-P_performance.md) | Photo Uploads per Session | SNFR | `StorageModule` |  |
| [SNFR-RAC-11](../../../1-pre-implementation/SRSD/SNFR/SNFR-R_reliability.md) | Photo Integrity | SNFR | `StorageModule` |  |
| [SNFR-SC-02](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Data at Rest | SNFR | `StorageModule` |  |
| [SNFR-SC-03](../../../1-pre-implementation/SRSD/SNFR/SNFR-S_security.md) | Photo Storage | SNFR | `StorageModule` |  |
| [SNFR-UEU-05](../../../1-pre-implementation/SRSD/SNFR/SNFR-U_usability.md) | [TBD] Photo Standards | SNFR | `StorageModule` |  |
