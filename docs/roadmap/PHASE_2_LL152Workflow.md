# Phase 2: LL152 Inspection Workflow

> **Status:** ✅ Complete (Alpha Implementation)
> **Objective:** Design and implement the first pluggable workflow type — what an LL152 inspection actually looks like, what gets captured, and what gets produced.
> **ADR:** [ADR-0016](../adr/0016-job-engine-pluggable-workflows.md)
> **Resolves:** GAP-01, GAP-03 (partial), GAP-04 (partial)

---

## Implementation Summary

Phase 2 implements the complete LL152 inspection workflow across all three layers (domain, DB, API) with the following capabilities:

### Domain Layer (`pcd-domain/src/ll152/`)

| Module | Purpose | Status |
|--------|---------|--------|
| `workflow_status.rs` | State machine: DRAFT → CAPTURING → READY_FOR_REVIEW → UNDER_REVIEW → FINALIZED | ✅ |
| `branch.rs` | BranchDiscriminator (Standard / NoGasPiping / GasPipingNotSupplied) | ✅ |
| `details.rs` | `Ll152JobDetails` aggregate with command methods + event returns | ✅ |
| `findings.rs` | InspectionFinding entity (5 GPS1 categories) + ObservationResult | ✅ |
| `photos.rs` | InspectionPhoto entity with dual-level (finding + job) support | ✅ |
| `events.rs` | Typed event payloads for all workflow transitions | ✅ |
| `validation.rs` | Pre-submit completeness checks (date + 5 findings) | ✅ |

### Database Layer (`pcd-db/src/ll152/`)

| Function | Transition | Event Emitted | Status |
|----------|-----------|--------------|--------|
| `start_capture()` | DRAFT → CAPTURING | LL152_CAPTURE_STARTED | ✅ |
| `submit_for_review()` | CAPTURING → READY_FOR_REVIEW | LL152_SUBMITTED_FOR_REVIEW | ✅ |
| `recall()` | READY_FOR_REVIEW → CAPTURING | LL152_RECALLED | ✅ |
| `open_review()` | READY_FOR_REVIEW → UNDER_REVIEW | LL152_REVIEW_OPENED | ✅ |
| `finalize()` | UNDER_REVIEW → FINALIZED | LL152_FINALIZED | ✅ |
| `return_for_corrections()` | UNDER_REVIEW → CAPTURING | LL152_RETURNED_FOR_CORRECTIONS | ✅ |
| `update_details()` | (metadata only) | LL152_DETAILS_UPDATED | ✅ |
| `update_finding()` | (finding data) | LL152_FINDING_UPDATED | ✅ |
| `attach_photo()` | (photo attach) | LL152_PHOTO_ATTACHED | ✅ |
| `remove_photo()` | (photo delete) | LL152_PHOTO_REMOVED | ✅ |

### API Layer (`pcd-api/src/routes/ll152.rs`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/jobs/{id}/ll152` | GET | Full overview (details + findings + photos) |
| `/api/jobs/{id}/ll152/details` | PUT | Update inspection metadata |
| `/api/jobs/{id}/ll152/start-capture` | POST | DRAFT → CAPTURING |
| `/api/jobs/{id}/ll152/submit-for-review` | POST | CAPTURING → READY_FOR_REVIEW (validates) |
| `/api/jobs/{id}/ll152/recall` | POST | READY_FOR_REVIEW → CAPTURING |
| `/api/jobs/{id}/ll152/open-review` | POST | READY_FOR_REVIEW → UNDER_REVIEW |
| `/api/jobs/{id}/ll152/finalize` | POST | UNDER_REVIEW → FINALIZED |
| `/api/jobs/{id}/ll152/return-for-corrections` | POST | UNDER_REVIEW → CAPTURING |
| `/api/jobs/{id}/ll152/findings/{findingId}` | PUT | Update a finding |
| `/api/jobs/{id}/ll152/photos` | POST | Attach a photo |
| `/api/jobs/{id}/ll152/photos/{photoId}` | DELETE | Remove a photo |

### Test Coverage

- **116 domain tests pass** including:
  - 17 command behavior tests (happy path, invalid state, terminal guards, full lifecycle)
  - 6 validation tests (date, findings, edge cases)
  - Existing workflow, branch, finding, and event tests

---

## Deferred to Later Phases

| Item | Deferred To | Reason |
|------|-------------|--------|
| GPS1/GPS2 PDF generation | Phase 4 (Reporting) | Requires PDF library + DOB layout research |
| LMP company fields (lmp_name, lmp_license) | Phase 3 (People & Tenancy) | Part of company/user domain |
| GCS photo upload (binary) | Post-Alpha | Alpha uses metadata-only; actual upload deferred |
| Stop-the-line notification push | Post-Alpha | Needs notification infrastructure |
| Photo minimums enforcement | Post-Alpha | Requires more field research with plumber |

---

## Spec Documents

- [LL152 Inspection Workflow](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/LL152_Inspection_Workflow.md)
- [LL152 State Machine](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/LL152_StateMachine.md)
- [Photo Evidence Spec](../2-during-implementation/DDD/ModuleDesign/Jobs/Workflows/LL152/PhotoEvidence_Spec.md)
