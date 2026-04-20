# Photo Evidence Specification

> **Parent:** [LL152 Inspection Workflow](./LL152_Inspection_Workflow.md)
> **Domain Code:** `crates/pcd-domain/src/ll152/photos.rs`
> **DB Table:** `inspection_photos` ([DatabaseSchema.md](../../DataDesign/DatabaseSchema.md))
> **API:** `POST/DELETE /api/jobs/:id/ll152/photos[/:photoId]`

---

## 1. Overview

Photo evidence is a required component of every LL152 gas piping inspection. Photos serve two roles:

1. **Finding-level evidence** — visual proof of an observed condition (e.g., improper flex hose, gas leak indicator)
2. **Job-level documentation** — general building context (meter room overview, boiler room entrance, equipment plates)

Per GPS1 §4, the QI (Qualified Inspector) captures photos during the inspection to substantiate each finding category. The LMP reviews these photos alongside the narrative detail when deciding to approve or return the submission.

---

## 2. Attachment Model (Design Q7)

Photos attach at **two levels**, distinguished by the `finding_id` field:

| Level | `finding_id` | Use Case |
|---|---|---|
| **Finding-level** | Set (FK → `inspection_findings`) | Evidence for a specific GPS1 category observation |
| **Job-level** | `NULL` | General building context, overview shots, equipment labels |

If a finding is deleted (future), the photo's `finding_id` is set to `NULL` (SQL `SET NULL` on FK delete), preserving the photo as job-level evidence.

---

## 3. Alpha Photo Requirements

### 3.1 Mandatory Photos (Alpha)

For alpha, the minimum requirements are intentionally lightweight:

| Requirement | Rule |
|---|---|
| **Minimum per job** | At least **1 photo** per job overall |
| **Per observed finding** | At least **1 photo** for each finding category marked `OBSERVED` |
| **Unobserved findings** | No photo required when `observation_result = 'NOT_OBSERVED'` |

> [!NOTE]
> The submit validation (`validate_for_submission`) does **not** enforce photo minimums in alpha. This is a documented soft requirement, not a hard gate. The plumber is expected to provide photos, but the system won't block submission without them. Photo validation will be tightened in beta after user feedback.

### 3.2 Recommended Photos (Best Practice)

Based on real-world LL152 inspections, the following are recommended but not enforced:

- **Meter room overview** — shows general condition and access
- **Each meter** — individual gas meter with visible label
- **Boiler/water heater** — gas-fired equipment connected to the piping
- **Defects** — close-up of any observed condition (flex hose, corrosion, leak indicator)
- **Equipment plates** — manufacturer labels for gas-fired appliances

---

## 4. Photo Metadata

Each photo carries the following metadata:

| Field | Type | Required | Source |
|---|---|---|---|
| `storage_path` | String | Yes | System-generated GCS path |
| `file_size` | Integer | No | Client-measured on upload |
| `content_type` | String | No | MIME type from client (e.g., `image/jpeg`) |
| `caption` | String | No | QI-entered description |
| `taken_at` | DateTime | No | EXIF extraction or device clock |
| `uploaded_by_user_id` | UUID | No | Auth context (hard-coded in alpha) |

### 4.1 Storage Path Convention

```
gs://pcd-photos/{company_id}/jobs/{job_id}/{photo_id}.{ext}
```

For alpha, the `storage_path` field stores the intended GCS path, but **actual GCS upload is deferred**. The API accepts metadata-only `POST` requests. Real file upload (multipart) will be implemented in Phase 4 per SFR-IRDX-02.

---

## 5. Format and Size Constraints

Per SFR-IRDX-02:

| Constraint | Value |
|---|---|
| **Accepted formats** | JPEG, PNG |
| **Maximum file size** | 10 MB per photo |
| **Maximum photos per job** | No hard limit (practical: ~50) |
| **Minimum resolution** | None enforced (device default expected) |

---

## 6. Lifecycle

Photos may be attached and removed at any time while the workflow is in a non-terminal state:

| Workflow Status | Attach | Remove |
|---|---|---|
| DRAFT | ✅ | ✅ |
| CAPTURING | ✅ | ✅ |
| READY_FOR_REVIEW | ✅ | ✅ |
| UNDER_REVIEW | ❌ (read-only for LMP) | ❌ |
| FINALIZED | ❌ | ❌ |

> [!NOTE]
> In alpha, the API does **not** enforce workflow-status guards on photo attach/remove. All photo operations succeed regardless of status. Status-based guards will be added when the review flow is fully implemented.

---

## 7. Events

Photo operations emit domain events to the `job_events` table:

| Operation | Event Type | Payload |
|---|---|---|
| Attach photo | `LL152_PHOTO_ATTACHED` | `{ job_id, photo_id, level: "finding"|"job" }` |
| Remove photo | `LL152_PHOTO_REMOVED` | `{ job_id, photo_id }` |

---

## 8. Deferred (Post-Alpha)

| Feature | Deferral Reason |
|---|---|
| Multipart file upload (GCS) | Requires cloud infrastructure (Phase 4) |
| EXIF auto-extraction | Nice-to-have, not essential for alpha |
| Photo reordering | UI concern, not domain |
| Thumbnail generation | Infrastructure concern |
| Photo annotations (circles, arrows) | Future mobile feature |
| Mandatory photo enforcement | Wait for alpha user feedback on friction |
