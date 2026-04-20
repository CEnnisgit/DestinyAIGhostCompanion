# PCD Testing Matrix

> **Version:** 1.0.0
> **Last Updated:** 2026-04-02
> **Status:** Active — update this document after implementing each testing phase
>
> Tracks test coverage per entity across all layers. Update ✅/🔲 markers as tests are added.

---

## Quick Stats

| Layer | Tests | Status |
|-------|------:|--------|
| **pcd-domain** | 184 | ✅ Complete |
| **pcd-db** | 0 → ~20 target | 🔲 Phase 3A (in progress) |
| **pcd-api** | 0 → ~9 target | 🔲 Phase 3B (deferred) |
| **E2E** | 0 → ~3 target | 🔲 Phase 3C (deferred) |

---

## Domain Layer — Unit Tests (184 total)

All complete. No gaps.

| Module | Entity | Tests | Status |
|--------|--------|------:|:------:|
| iam/people | User | 11 | ✅ |
| iam/people | Email | 17 | ✅ |
| iam/people | DisplayName | 13 | ✅ |
| iam/people | CompanyMembership | 7 | ✅ |
| iam/company | Company | 9 | ✅ |
| iam/lmp_credential | LmpCredential | 11 | ✅ |
| operations | Job | 53 | ✅ |
| operations | JobStatus | 9 | ✅ |
| operations | JobNumber | 5 | ✅ |
| operations | JobType | 4 | ✅ |
| operations | Priority | 5 | ✅ |
| operations | SourceKind | 3 | ✅ |
| operations | Client | 12 | ✅ |
| operations | SavedBuilding | 3 | ✅ |
| workflows/ll152 | WorkflowStatus | 10 | ✅ |
| workflows/ll152 | Commands | 15 | ✅ |
| workflows/ll152 | FindingCategory | 7 | ✅ |
| workflows/ll152 | Validation | 6 | ✅ |

---

## DB Layer — Integration Tests (target: ~20)

> **Phase:** 3A (current)
> **Infrastructure:** `#[sqlx::test]` + shared fixtures
> **Location:** `crates/pcd-db/tests/`

| Repository | Roundtrip | Queries | Constraints | Tests | Status |
|-----------|:---------:|:-------:|:-----------:|------:|:------:|
| SqlxUserRepository | 🔲 save+find | 🔲 find_by_email, list_all | 🔲 UNIQUE email | 0/4 | 🔲 |
| SqlxCompanyRepository | 🔲 save+find | — | 🔲 NOT NULL workspace_id | 0/2 | 🔲 |
| SqlxMembershipRepository | — | 🔲 find_by_user, find_by_company | 🔲 UNIQUE(user,company) | 0/3 | 🔲 |
| SqlxLmpCredentialRepository | 🔲 save+find | 🔲 list_by_user | 🔲 CHECK not_empty | 0/3 | 🔲 |
| SqlxJobRepository | 🔲 save+find | 🔲 find_by_job_number, next_number | — | 0/3 | 🔲 |
| SqlxClientRepository | 🔲 save+find | 🔲 find_by_name_and_phone | — | 0/2 | 🔲 |
| SqlxSavedBuildingRepository | 🔲 save+list | 🔲 is_saved | 🔲 remove | 0/3 | 🔲 |

---

## API Layer — Handler Tests (target: ~9)

> **Phase:** 3B (after auth is wired)
> **Infrastructure:** Axum `TestClient` + test pool
> **Location:** `crates/pcd-api/tests/`

| Route Group | Endpoints | Tests | Status |
|-------------|-----------|------:|:------:|
| Users | GET /api/users, GET /api/users/:id | 0/2 | 🔲 |
| Company | GET /api/company/:id, PATCH /api/company/:id | 0/2 | 🔲 |
| LmpCredential | POST + GET + PATCH + deactivate + reactivate | 0/3 | 🔲 |
| Jobs | POST + GET + lifecycle commands | 0/2 | 🔲 |

---

## End-to-End Tests (target: ~3)

> **Phase:** 3C (after authorization is wired)
> **Location:** workspace root `tests/e2e/`

| Test | What It Proves | Status |
|------|----------------|:------:|
| LL152 happy path | Create job → capture → submit → review → finalize → verify immutable | 🔲 |
| LMP credential attach | Create credential → create LL152 job → attach → verify FK | 🔲 |
| Cross-entity query | User memberships → workspace access → scoped job list | 🔲 |

---

## Risk Assessment

| Entity | Domain | DB | API | Overall Risk |
|--------|:------:|:--:|:---:|:------------:|
| User | 🟢 | 🔴 | 🔴 | 🟡 Medium |
| Email | 🟢 | — | — | 🟢 Low |
| DisplayName | 🟢 | — | — | 🟢 Low |
| CompanyMembership | 🟢 | 🔴 | — | 🟡 Medium |
| Company | 🟢 | 🔴 | 🔴 | 🟡 Medium |
| LmpCredential | 🟢 | 🔴 | 🔴 | 🟡 Medium |
| Job | 🟢 | 🔴 | 🔴 | 🔴 High |
| Client | 🟢 | 🔴 | 🔴 | 🟡 Medium |
| SavedBuilding | 🟢 | 🔴 | 🔴 | 🟡 Medium |
| LL152 Workflow | 🟢 | 🔴 | 🔴 | 🔴 High |

**Risk level logic:**
- 🟢 **Low**: Domain tests cover all logic, entity is simple (VOs, read-only)
- 🟡 **Medium**: Domain covered but DB/API untested. Simple CRUD, low chance of SQL bug
- 🔴 **High**: Complex entity with joins, FSM, or multi-step workflows. SQL bugs have high impact

---

## Changelog

| Date | Change |
|------|--------|
| 2026-04-02 | Initial matrix created. Domain layer complete (184 tests). DB/API/E2E at zero. |
