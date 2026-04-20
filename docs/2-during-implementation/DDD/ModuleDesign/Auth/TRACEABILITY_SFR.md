# AuthModule Traceability: Functional Requirements

| Req ID | Sub-Module | Statement | Interface | Impl Link | Verif Method | Verif Link | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [SFR-SRAN-01](../../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md#sfr-sran-01) | Auth (3B) | Email/Password Login |  |  |  |  | ⏳ Pending |
| [SFR-SRAN-02](../../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md#sfr-sran-02) | Auth (3B) | Session Tokens |  |  |  |  | ⏳ Pending |
| [SFR-SRAN-03](../../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md#sfr-sran-03) | Auth (3B) | Password Reset |  |  |  |  | ⏳ Pending |
| [SFR-SRAN-04](../../../../1-pre-implementation/SRSD/SFR/SFR-SR_security.md#sfr-sran-04) | Auth (3B) | Logout |  |  |  |  | ⏳ Pending |
| SFR-SRAZ-01 | Authz (3C.1) | Create Job | [PermissionGuard](./PermissionGuard.md) — `RequireAdmin` | | Integration test G1, G2, G3 | | 📋 Spec'd |
| SFR-SRAZ-02 | Authz (3C.1) | Dispatch/Assign Job | [PermissionGuard](./PermissionGuard.md) — `RequireAdmin` | | Integration test G1, G2 | | 📋 Spec'd |
| SFR-SRAZ-03 | Authz (3C.1) | View Jobs (role-scoped) | [RoleVisibility](./RoleVisibility.md) §2 | | Integration tests T1-T4, A1, P1-P4 | | 📋 Spec'd |
| SFR-SRAZ-04 | Authz (3C.1) | Submit Findings | [PermissionGuard](./PermissionGuard.md) — `RequireAuthenticated` | | Integration test A5 | | 📋 Spec'd |
| SFR-SRAZ-05 | Authz (3C.1) | Finalize/Sign Report | [PermissionGuard](./PermissionGuard.md) — `RequireAdmin` | | Integration test G1, G2 | | 📋 Spec'd |
| SFR-SRAZ-06 | Authz (3C.1) | Generate Report | [PermissionGuard](./PermissionGuard.md) — `RequireAdmin` | | Integration test G1, G2 | | 📋 Spec'd |
| SFR-SRAZ-07 | Authz (3C.1) | Manage Users | [PermissionGuard](./PermissionGuard.md) — `RequireAdmin` | | Integration test G1, G2 | | 📋 Spec'd |
