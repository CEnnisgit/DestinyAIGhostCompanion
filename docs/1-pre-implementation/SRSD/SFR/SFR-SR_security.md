# SFR-SR: Security Requirements (Functional)

> **Parent:** [SFR Index](../README.md) | **Prev:** [SFR-BR](./SFR-BR_business-rules.md) | **Next:** [SFR-IR](./SFR-IR_integration.md)

## Sub-Types
- [SFR-SRAN (Authentication)](#sfr-sran-authentication)
- [SFR-SRAZ (Authorization)](#sfr-sraz-authorization)
- [SFR-SRAC (Access Control)](#sfr-srac-access-control)

---

## SFR-SRAN: Authentication

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-SRAN-01` | **Email/Password Login:** Users authenticate with email and password. | Implicit |
| `SFR-SRAN-02` | **Session Tokens:** JWT-based access tokens (15 min) with refresh tokens (7 days). | ADR-001 |
| `SFR-SRAN-03` | **Password Reset:** User can request password reset via email. | Implicit |
| `SFR-SRAN-04` | **Logout:** User can log out, invalidating refresh token. | Implicit |

---

## SFR-SRAZ: Authorization

### Role Definitions

| Role | Description |
|------|-------------|
| **TECHNICIAN** | Plumber in the field. Can view assigned jobs and submit findings. |
| **ADMIN** | LMP / Company Admin. Can create jobs, dispatch, review, generate reports. |

### Permission Matrix

| Code | Action | TECHNICIAN | ADMIN |
|------|--------|------------|-------|
| `SFR-SRAZ-01` | Create Job | ❌ | ✅ |
| `SFR-SRAZ-02` | Dispatch Job | ❌ | ✅ |
| `SFR-SRAZ-03` | View Assigned Jobs | ✅ (own) | ✅ (all) |
| `SFR-SRAZ-04` | Submit Findings | ✅ | ❌ |
| `SFR-SRAZ-05` | Approve/Return | ❌ | ✅ |
| `SFR-SRAZ-06` | Generate Report | ❌ | ✅ |
| `SFR-SRAZ-07` | Manage Users | ❌ | ✅ |

---

## SFR-SRAC: Access Control

### Data Scoping

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-SRAC-01` | **Technician Scope:** Technicians can ONLY see jobs explicitly assigned to their user ID. | Implicit |
| `SFR-SRAC-02` | **Admin Scope:** Admins can see ALL jobs within their company. | Implicit |
| `SFR-SRAC-03` | **Company Isolation:** Users cannot access jobs from other companies (multi-tenancy). | Implicit |

### Audit Trail

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SFR-SRAC-10` | **Action Logging:** All state transitions (dispatch, submit, approve, return) are logged with user ID and timestamp. | §5.2 |
