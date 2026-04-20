# Database Schema Reference

> **Source of Truth:** SQL queries in `crates/pcd-db/src/` (sqlx raw SQL)
> **Scope:** [Pilot Core (LL152)](file:///c:/github/pcd/docs/PILOT_SCOPE_CONTEXT.md)

---

## Tenant Tables (Phase 1.5)

### `companies`

Stub table for tenant identity. Seeded with dev company.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `name` | TEXT | No | Company name |
| `company_type` | TEXT | No | Default: `'independent'` |
| `created_at` | Timestamp | No | Default: now() |
| `updated_at` | Timestamp | No | Default: now() |

### `clients`

Company-scoped contact cards. See [Client_Aggregate.md](../ModuleDesign/CRM/Clients/Client_Aggregate.md).

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `company_id` | UUID | No | FK → companies |
| `name` | TEXT | No | Client name |
| `phone` | TEXT | Yes | Contact phone |
| `address` | TEXT | Yes | Default address |
| `is_blocked` | BOOLEAN | No | Default: false |
| `blocked_reason` | TEXT | Yes | Required when is_blocked=true (CHECK) |
| `created_at` | Timestamp | No | Default: now() |
| `updated_at` | Timestamp | No | Default: now() |

### `saved_buildings`

Company-scoped building bookmarks. See [SavedBuilding](../../../3-after-implementation/Modules/tenant/domain.md).

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `company_id` | UUID | No | FK → companies |
| `building_id` | UUID | No | FK → buildings |
| `created_at` | Timestamp | No | Default: now() |

UNIQUE constraint on `(company_id, building_id)`.

---

## CRM / Assets Tables

### `buildings`

| Column | Type | Nullable | Description | Authority |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK | Generated |
| `bin` | VARCHAR(7) | No | Root Identity (UNIQUE) | PAD Bootstrap |
| `house_number` | Text | Yes | Canonical Address | Geoclient |
| `street_name` | Text | Yes | Canonical Address | Geoclient |
| `borough` | Text | Yes | Canonical Address | Geoclient |
| `zip_code` | VARCHAR(5) | Yes | Canonical Address | Geoclient |
| `primary_bbl_borough_code` | SmallInt | Yes | Canonical Primary BBL | PAD Bootstrap |
| `primary_bbl_block` | Integer | Yes | Canonical Primary BBL | PAD Bootstrap |
| `primary_bbl_lot` | Integer | Yes | Canonical Primary BBL | PAD Bootstrap |
| `cd_borough_code` | SmallInt | Yes | Canonical Metadata | Geoclient |
| `cd_number` | Integer | Yes | Canonical Metadata | Geoclient |
| `dof_building_class_code` | Text | Yes | Canonical Metadata | Geoclient |
| `condo_status` | Text | No | Default: 'UNKNOWN' | Geoclient |
| `condo_status_evidence` | Text | No | Default: 'NONE' | Geoclient |
| `condo_verified_at` | Timestamp | Yes | | Geoclient |
| `billing_bbl_borough_code` | SmallInt | Yes | Condo Billing BBL | Geoclient |
| `billing_bbl_block` | Integer | Yes | Condo Billing BBL | Geoclient |
| `billing_bbl_lot` | Integer | Yes | Condo Billing BBL | Geoclient |
| `pad_version` | Text | Yes | PAD Evidence | PAD |
| `pad_last_seen_at` | Timestamp | Yes | PAD Evidence | PAD |
| `pad_condo_flag` | Text | Yes | PAD Evidence | PAD |
| `pad_billing_bbl_borough` | SmallInt | Yes | PAD Evidence | PAD |
| `pad_billing_bbl_block` | Integer | Yes | PAD Evidence | PAD |
| `pad_billing_bbl_lot` | Integer | Yes | PAD Evidence | PAD |
| `pad_low_bbl_lot` | Integer | Yes | PAD Evidence | PAD |
| `pad_high_bbl_lot` | Integer | Yes | PAD Evidence | PAD |
| `created_from_source` | Text | Yes | Provenance | |
| `created_from_version` | Text | Yes | Provenance | |
| `last_imported_from_source` | Text | Yes | Provenance | |
| `last_imported_from_version` | Text | Yes | Provenance | |

### `building_addresses`

| Column | Type | Nullable | Description | Authority |
| :--- | :--- | :--- | :--- | :--- |
| `id` | BigSerial | No | PK | Generated |
| `bin` | VARCHAR(7) | No | FK -> buildings(bin) | PAD Bootstrap |
| `pad_version` | Text | No | | PAD |
| `borough_code` | SmallInt | No | Normalized Search Key | PAD |
| `street_name` | Text | No | Normalized Search Key | PAD |
| `house_number_display` | Text | No | Display Form | PAD |
| `lhnd` | Text | Yes | PAD Range Support | PAD |
| `hhnd` | Text | Yes | PAD Range Support | PAD |
| `lhns` | Text | Yes | PAD Range Support | PAD |
| `hhns` | Text | Yes | PAD Range Support | PAD |
| `address_type` | Text | Yes | e.g. R (Real), P (Pseudo) | PAD |
| `parity` | Text | Yes | '0' indicates NAP | PAD |

### `building_events`

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK |
| `bin` | VARCHAR(7) | No | FK -> buildings(bin) |
| `event_type` | VARCHAR | No | e.g. `PAD_SUPERSEDED`, `GEOCLIENT_VERIFY` |
| `changed_fields` | JSONB | No | Differential payload `{"condo_status": {"old": "C", "new": "NONE"}}` |
| `created_at` | Timestamp | No | Default: now() |

### `building_pad_versions`

Junction table tracking which PAD versions a building appears in. See [ADR-0014](../../adr/0014-version-membership-junction-table.md).

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | BigSerial | No | PK |
| `bin` | VARCHAR(7) | No | FK -> buildings(bin) |
| `pad_version` | Text | No | e.g. `'25A'`, `'25B'` |
| `first_seen_at` | Timestamp | No | When this building was first observed in this version |

---

## CRM / Compliance Tables

### `compliance_obligations`

Generic engine table for tracking per-building compliance duties across multiple NYC programs. See [ComplianceObligation_Aggregate.md](../ModuleDesign/CRM/Compliance/Obligations/ComplianceObligation_Aggregate.md).

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `building_id` | UUID | No | FK -> buildings |
| `program_code` | TEXT | No | Enum-like (e.g., `'LL152'`) |
| `cycle_key` | TEXT | No | Stable cycle identifier |
| `window_start` | DATE | Yes | Inspection window start |
| `window_end` | DATE | Yes | Inspection window end |
| `status` | TEXT | No | Derived summary (e.g., `'OPEN'`, `'SATISFIED'`) |
| `roster_status` | TEXT | No | Indicates presence on current DOB roster (`'ACTIVE'`, `'INACTIVE'`) |
| `created_from_source` | TEXT | Yes | Provenance (e.g., `'DOB_LL152'`) |

### `obligation_events`

Tracks historical changes to obligations. See [ComplianceObligation_Aggregate.md](../ModuleDesign/CRM/Compliance/Obligations/ComplianceObligation_Aggregate.md).

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `obligation_id` | UUID | No | FK -> compliance_obligations |
| `event_type` | TEXT | No | e.g., `'ROSTER_STATUS_CHANGED'`, `'OBLIGATION_CREATED'` |
| `old_value` | TEXT | Yes | |
| `new_value` | TEXT | Yes | |
| `import_run_id` | UUID | Yes | FK -> import_runs |
| `occurred_at` | Timestamp | No | Default: now() |

### `ll152_obligation_details`

Program-specific 1:1 extension table for LL152. See [LL152_Program_Spec.md](../ModuleDesign/CRM/Compliance/Programs/LL152/LL152_Program_Spec.md).

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `obligation_id` | UUID | No | PK, FK -> compliance_obligations (Cascade) |
| `subcycle` | VARCHAR(1) | No | `'A'`, `'B'`, `'C'`, or `'D'` |

---

## Ingestion Tables

### `import_runs`

Tracks ingestion provenance per pipeline execution.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `pipeline_name` | TEXT | No | e.g. `'ll152_ingestion'`, `'pad_bootstrap'` |
| `source_file` | TEXT | Yes | Original file path/URL |
| `source_version` | TEXT | Yes | The version string for provenance |
| `rows_parsed` | INTEGER | Yes | Total rows read |
| `rows_inserted` | INTEGER | Yes | Rows successfully upserted |
| `rows_quarantined` | INTEGER | Yes | Rows failed/errored |
| `started_at` | Timestamp | No | Default: now() |
| `completed_at` | Timestamp | Yes | Set when the run finishes |

### `import_anomalies`

Matches the schema defined in [Ingestion_Diagnostics.md](../ModuleDesign/CRM/Assets/Building/Ingestion_Diagnostics.md) §5.1.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `import_run_id` | UUID | Yes | Groups anomalies to a single pipeline execution |
| `verification_run_id` | UUID | Yes | Groups anomalies to a Geoclient verification run |
| `pipeline_name` | TEXT | Yes | `'pad_bootstrap'`, `'ll152_roster_import'`, etc. |
| `source_row_index` | INTEGER | Yes | CSV line number for debugging |
| `source_ref` | TEXT | Yes | File path or logical reference |
| `building_id` | UUID | Yes | FK to buildings (when resolved) |
| `building_bin` | VARCHAR(7) | Yes | BIN context |
| `program_code` | TEXT | Yes | e.g. `'LL152'` |
| `cycle_key` | TEXT | Yes | e.g. `'2025-cycle-1'` |
| `severity` | VARCHAR(10) | No | `'INFO'` / `'WARN'` / `'ERROR'` |
| `field_name` | VARCHAR(80) | Yes | e.g. `'primaryBbl'`, `'address'` |
| `reason_code` | VARCHAR(80) | No | Stable identifier, e.g. `'BIN_MULTIPLE_BBLS_PRIMARY_SELECTED'` |
| `raw_value` | TEXT | Yes | The raw input that caused the issue |
| `message` | TEXT | Yes | Human-readable explanation |
| `details` | JSONB | Yes | Structured extras (return codes, parsed tokens, etc.) |
| `created_at` | Timestamp | No | Default: now() |

### `quarantined_rows`

Stores raw CSV row payloads for ERROR-severity rows. See [Ingestion_Diagnostics.md](../ModuleDesign/CRM/Assets/Building/Ingestion_Diagnostics.md) §5.2.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `import_run_id` | UUID | Yes | Groups rows to a single pipeline execution |
| `pipeline_name` | TEXT | Yes | `'pad_bootstrap'`, etc. |
| `source_row_index` | INTEGER | Yes | CSV line number for debugging |
| `source_ref` | TEXT | Yes | File path or logical reference |
| `reason_code` | VARCHAR(80) | No | Stable identifier |
| `raw_payload` | JSONB | No | Full raw CSV row as JSON for manual review/retry |
| `created_at` | Timestamp | No | Default: now() |

---

## Jobs Tables

### `jobs`

Central job aggregate table. See [Job_Aggregate.md](../ModuleDesign/Jobs/Engine/Job_Aggregate.md).

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK |
| `job_number` | TEXT | No | Human-facing identifier (e.g., `JOB-00001`), unique per company |
| `company_id` | UUID | No | FK → companies |
| `job_type` | TEXT | No | e.g. `'LL152_INSPECTION'`, `'EMERGENCY'`, `'REPAIR'` |
| `address` | TEXT | No | Freeform address text (always required, address-first per ADR-0023) |
| `building_id` | UUID | Yes | FK → buildings (resolved lazily from address) |
| `building_unresolved` | BOOLEAN | No | Default: true. False when building_id is resolved |
| `client_id` | UUID | Yes | FK → clients |
| `compliance_obligation_id` | UUID | Yes | FK → compliance_obligations |
| `requester_contact_id` | UUID | Yes | FK → contacts (future) |
| `title` | TEXT | No | Auto-generated or user-provided |
| `summary` | TEXT | Yes | Job description / notes |
| `source_kind` | TEXT | Yes | How the job was sourced (see DataStructures.md) |
| `priority` | TEXT | Yes | `NORMAL`, `HIGH`, `URGENT` |
| `site_notes` | TEXT | Yes | Site-specific instructions |
| `assigned_to` | UUID | Yes | FK → users (dispatched technician) |
| `created_by_user_id` | UUID | No | FK → users (who opened the job) |
| `job_status` | TEXT | No | `OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELED` |
| `created_at` | Timestamp | No | |
| `started_at` | Timestamp | Yes | Set when status -> IN_PROGRESS |
| `completed_at` | Timestamp | Yes | Set when status -> COMPLETED |
| `canceled_at` | Timestamp | Yes | Set when status -> CANCELED |
| `cancellation_reason` | TEXT | Yes | Required when canceling |
| `updated_at` | Timestamp | No | |

### `job_events`

Domain events emitted by the Job aggregate, persisted per transaction.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK |
| `job_id` | UUID | No | FK -> jobs |
| `event_type` | TEXT | No | e.g. `'JOB_OPENED'`, `'JOB_STARTED'` |
| `payload` | JSONB | No | Event-specific data |
| `actor_user_id` | UUID | No | Who triggered the event |
| `created_at` | Timestamp | No | |

---

## LL152 Workflow Tables (Phase 2)

### `ll152_job_details`

1:1 extension of `jobs` for LL152 inspections. Per [ADR-0025](../../adr/0025-dual-status-model.md) (Dual-Status Model).

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `job_id` | UUID | No | PK, FK → jobs (Cascade) |
| `branch_discriminator` | TEXT | No | Default: `'STANDARD_INSPECTION'` |
| `workflow_status` | TEXT | No | Default: `'DRAFT'` |
| `inspection_date` | DATE | Yes | Date of on-site inspection |
| `inspection_start_time` | TIME | Yes | When inspection started |
| `inspection_end_time` | TIME | Yes | When inspection ended |
| `additional_comments` | TEXT | Yes | GPS1 §5 freeform notes |
| `snapshot_address` | TEXT | Yes | GPS1 §1 — frozen at capture start |
| `snapshot_bin` | VARCHAR(7) | Yes | GPS1 §1 — frozen at capture start |
| `snapshot_borough` | TEXT | Yes | GPS1 §1 — frozen at capture start |
| `snapshot_block` | INTEGER | Yes | GPS1 §1 — frozen at capture start |
| `snapshot_lot` | INTEGER | Yes | GPS1 §1 — frozen at capture start |
| `snapshot_community_board` | TEXT | Yes | GPS1 §1 — frozen at capture start |
| `snapshot_number_of_stories` | INTEGER | Yes | QI-entered |
| `snapshot_total_meters` | INTEGER | Yes | QI-entered |
| `snapshot_active_meters` | INTEGER | Yes | QI-entered |
| `created_at` | Timestamp | No | Default: now() |
| `updated_at` | Timestamp | No | Default: now() |

### `inspection_findings`

Child entities of LL152 jobs — one per GPS1 category (5 per job).

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `job_id` | UUID | No | FK → jobs (Cascade) |
| `category` | TEXT | No | GPS1 §4 category |
| `observation_result` | TEXT | No | Default: `'NOT_OBSERVED'` |
| `narrative_detail` | TEXT | Yes | QI's field notes (unconstrained, AI-readable) |
| `requires_correction` | BOOLEAN | No | Default: false. Stored, not derived |
| `requires_immediate_reporting` | BOOLEAN | No | Default: false. Stored, not derived |
| `recorded_at` | Timestamp | Yes | When the QI recorded this finding |
| `recorded_by_user_id` | UUID | Yes | Who recorded the finding |
| `created_at` | Timestamp | No | Default: now() |
| `updated_at` | Timestamp | No | Default: now() |

UNIQUE constraint on `(job_id, category)`.

**Finding Categories** (GPS1 §4, DOB-defined):
1. `IMPROPER_USE_OF_FLEX_HOSE`
2. `ILLEGAL_CONNECTION_OR_NON_CODE_COMPLIANT_INSTALLATION`
3. `GAS_LEAK_0_1_PERCENT_OR_MORE_IN_AIR`
4. `WORN_PART_AFFECTING_SAFE_AND_RELIABLE_OPERATION`
5. `OTHER_UNSAFE_CONDITION`

### `inspection_photos`

Evidence attachments — finding-level or job-level.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | No | PK, default: `gen_random_uuid()` |
| `job_id` | UUID | No | FK → jobs (Cascade) |
| `finding_id` | UUID | Yes | FK → inspection_findings (SET NULL). Null = job-level photo |
| `storage_path` | TEXT | No | GCS object path |
| `file_size` | INTEGER | Yes | Bytes |
| `content_type` | TEXT | Yes | MIME type |
| `caption` | TEXT | Yes | Optional description |
| `taken_at` | Timestamp | Yes | When the photo was taken |
| `uploaded_by_user_id` | UUID | Yes | Who uploaded |
| `created_at` | Timestamp | No | Default: now() |

### `companies` ALTER (Phase 2 addition)

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `lmp_name` | TEXT | Yes | Licensed Master Plumber name (GPS1 §2) |
| `lmp_license_number` | TEXT | Yes | LMP license number (GPS1 §2) |

---

## Future Tables *(not yet implemented)*

The following tables are planned but do not yet exist in the database:

| Table | Module | Purpose |
| :--- | :--- | :--- |
| `users` | Auth | Authentication & role-based access |
| `technicians` | Users | Field operators |
| `company_admins` | Users | Office managers |
| `inspection_reports` | Jobs / Workflows | Generated PDF deliverables |
| `password_reset_tokens` | Auth | Security utility |

---

## Constraints

- Foreign Keys are enforced on all reference columns.
- `buildings.bin` is UNIQUE.
- `building_pad_versions(bin, pad_version)` is UNIQUE.
- `jobs(company_id, job_number)` is implicitly unique (enforced by `nextJobNumber` logic).
- `inspection_findings(job_id, category)` is UNIQUE (one finding per GPS1 category per job).
- `ll152_job_details.job_id` cascades on delete from `jobs`.
- `inspection_photos.finding_id` SET NULL on delete from `inspection_findings`.

## Indexes

- `buildings(bin)` — primary lookup
- `building_addresses(bin)` — address search
- `import_anomalies(import_run_id)` — anomaly grouping
- `compliance_obligations(building_id)` — obligation lookup by building
- `clients(company_id)` — tenant-scoped client listing
- `jobs(company_id)` — tenant-scoped job listing
- `inspection_findings(job_id)` — findings by job
- `inspection_photos(job_id)` — photos by job

