# SNFR-M: Maintainability Requirements

> **Parent:** [SNFR Index](../README.md) | **Prev:** [SNFR-R](./SNFR-R_reliability.md)

## Sub-Types
- [SNFR-MM (Modifiability)](#snfr-mm-modifiability)
- [SNFR-MT (Testability)](#snfr-mt-testability)
- [SNFR-MP (Portability)](#snfr-mp-portability)

---

## SNFR-MM: Modifiability

### Architecture

| Code | Description | PRD Ref |
|------|-------------|---------|
| `SNFR-MM-01` | **Feature-Slice Architecture:** Code organized by feature (`packages/features/*`) for isolated changes. | ADR-008 |
| `SNFR-MM-02` | **Hexagonal/Ports-Adapters:** Business logic separated from infrastructure for testability. | ADR-009 |

### Code Quality

| Code | Description | Target |
|------|-------------|--------|
| `SNFR-MM-10` | **TypeScript Strict:** 100% TypeScript with strict mode; no `any` in production. | Yes |
| `SNFR-MM-11` | **ESLint Compliance:** Zero lint warnings in CI. | Yes |
| `SNFR-MM-12` | **Documentation:** JSDoc for all public API functions. | Yes |

---

## SNFR-MT: Testability

### Test Coverage

| Code | Description | Target |
|------|-------------|--------|
| `SNFR-MT-01` | **Unit Test Coverage:** Core business logic modules. | > 70% |
| `SNFR-MT-02` | **Integration Tests:** Key flows (create job, submit, approve) have end-to-end tests. | Yes |

### CI/CD Gates

| Code | Description |
|------|-------------|
| `SNFR-MT-10` | **Lint Gate:** CI fails if lint errors present. |
| `SNFR-MT-11` | **Type Gate:** CI fails if TypeScript errors present. |
| `SNFR-MT-12` | **Test Gate:** CI fails if unit/integration tests fail. |

---

## SNFR-MP: Portability

### Platform Independence

| Code | Description |
|------|-------------|
| `SNFR-MP-01` | **Frontend:** React-based; runs in any modern browser or WebView. |
| `SNFR-MP-02` | **Backend:** Node.js on Cloud Run; containerized for platform-agnostic deployment. |

### Environment Parity

| Code | Description |
|------|-------------|
| `SNFR-MP-10` | **Dev/Staging/Prod:** Same Docker image deployed across environments with env-specific config. |
| `SNFR-MP-11` | **Database Migration:** Drizzle ORM migrations run consistently across environments. |
