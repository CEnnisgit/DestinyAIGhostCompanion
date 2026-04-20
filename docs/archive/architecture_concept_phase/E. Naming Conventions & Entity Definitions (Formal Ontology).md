## E. Naming Conventions & Entity Definitions (Formal Ontology)

### E.1 Global Naming Conventions

**Code (TypeScript/Java/Go, etc.)**

* Classes / Types: `PascalCase` (e.g., `InspectionJob`)
* Variables / functions: `camelCase` (e.g., `createInspectionJob`)
* Enums: `PascalCase` with uppercase values (e.g., `JobStatus.COMPLETED`)

**Database (SQL)**

* Tables: `snake_case` plural noun (e.g., `inspection_jobs`)
* Columns: `snake_case` (e.g., `job_id`, `company_id`)
* Primary keys: `<entity>_id` as UUID, e.g., `job_id`, `company_id`

**API endpoints**

* Base path versioning: `/api/v1/...`
* Resource naming: plural nouns (e.g., `/api/v1/inspection-jobs`)
* Use hyphen-separated paths, query params in `camelCase` or `snake_case` (pick one and be consistent).

Example:

* `GET /api/v1/service-requests?status=received`
* `POST /api/v1/inspection-forms/{formId}/submit`

---

### E.2 Entity Catalog (Formal Definitions)

Below is a concise ontology for your domain.

#### 1. `User`

* **Role**: Generic system user (auth & identity).
* **Key attributes**:

  * `user_id` (PK)
  * `email`, `password_hash`
  * `role` (enum: `PLATFORM_ADMIN`, `COMPANY_ADMIN`, `TECHNICIAN`, `OWNER`)
* **Relationships**:

  * One `User` may be linked to exactly one `Owner` or one `Technician` (or neither, for platform admins).

#### 2. `PlumbingCompany`

* **Role**: Organization providing LL152 inspections.
* **Key attributes**:

  * `company_id`
  * `name`
  * `license_number`
  * `service_areas` (array or child table)
* **Relationships**:

  * One `PlumbingCompany` has many `Technicians`.
  * One `PlumbingCompany` has many `InspectionJobs`.

#### 3. `Technician`

* **Role**: Field user performing inspections.
* **Key attributes**:

  * `technician_id`
  * `user_id` (FK to `User`)
  * `company_id` (FK to `PlumbingCompany`)
* **Relationships**:

  * A `Technician` belongs to one `PlumbingCompany`.
  * A `Technician` performs many `InspectionJobs`.

#### 4. `Owner`

* **Role**: Person or entity requesting/receiving inspections.
* **Key attributes**:

  * `owner_id`
  * `user_id` (FK to `User`)
  * `organization_name` (optional)
* **Relationships**:

  * An `Owner` may be associated with multiple `Buildings`.

#### 5. `Building`

* **Role**: Physical property subject to LL152 inspections.
* **Key attributes**:

  * `building_id`
  * `owner_id`
  * `address_line1`, `address_line2`
  * `borough`, `zipcode`
  * `lat`, `lng`
* **Relationships**:

  * One `Building` belongs to one `Owner`.
  * One `Building` has many `ServiceRequests`.
  * One `Building` has many `InspectionJobs`.

#### 6. `ServiceRequest`

* **Role**: Demand-side object representing an owner’s request for LL152 inspection.
* **Key attributes**:

  * `request_id`
  * `building_id`
  * `owner_id`
  * `requested_date_window` (start/end)
  * `status` (`RECEIVED`, `MATCHED`, `CANCELLED`)
  * `matched_company_id` (nullable, once matched)
* **Relationships**:

  * A `ServiceRequest` is created by an `Owner`.
  * A `ServiceRequest` may lead to one `InspectionJob`.

#### 7. `InspectionJob`

* **Role**: Central work unit linking marketplace and compliance.
* **Key attributes**:

  * `job_id`
  * `company_id`
  * `technician_id` (nullable until assigned)
  * `building_id`
  * `service_request_id` (nullable if job created directly by company)
  * `scheduled_at`
  * `status` (`PENDING_ASSIGNMENT`, `SCHEDULED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`)
* **Relationships**:

  * One `InspectionJob` may originate from one `ServiceRequest`.
  * One `InspectionJob` is executed by one `Technician`.
  * One `InspectionJob` has exactly one `InspectionForm`.

#### 8. `InspectionForm`

* **Role**: Structured LL152 data captured during an inspection.
* **Key attributes**:

  * `form_id`
  * `job_id`
  * `status` (`IN_PROGRESS`, `COMPLETED`)
  * `form_payload` (JSON: gas piping condition, notes, etc.)
  * `submitted_at`
* **Relationships**:

  * One `InspectionForm` belongs to one `InspectionJob`.
  * One `InspectionForm` has exactly one `InspectionReport`.

#### 9. `InspectionReport`

* **Role**: Generated document (PDF or similar) for compliance and communication.
* **Key attributes**:

  * `report_id`
  * `form_id`
  * `storage_url`
  * `created_at`
  * `version` (for re-generation scenarios)
* **Relationships**:

  * One `InspectionReport` is derived from one `InspectionForm`.

#### 10. `Photo` (optional explicit entity)

* **Role**: Image evidence linked to inspection.
* **Key attributes**:

  * `photo_id`
  * `form_id`
  * `storage_url`
  * `taken_at`
* **Relationships**:

  * Many `Photo` records belong to one `InspectionForm`.

---

### E.3 Ontology – Relationships Summarized Formally

You can think of the relationships as triples:

* `Owner OWNS Building`
* `Owner CREATES ServiceRequest`
* `ServiceRequest TARGETS Building`
* `Marketplace MATCHES ServiceRequest TO PlumbingCompany`
* `PlumbingCompany EMPLOYS Technician`
* `PlumbingCompany OWNS InspectionJob`
* `InspectionJob ASSIGNED_TO Technician`
* `InspectionJob OCCURS_AT Building`
* `InspectionJob HAS InspectionForm`
* `InspectionForm PRODUCES InspectionReport`
* `InspectionForm HAS_MANY Photo`

This ontology is stable even if you:

* Add more laws (LL11, LL87).
* Add additional job types (not just LL152).

You would simply parameterize jobs/forms by `law_type` or `inspection_type`.