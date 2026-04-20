# Modular Vertical Slice Roadmap: "The Pipe"

**Goal:** Implement the "First Vertical Slice" (Intake → Capture → Review → Output) by strictly sequencing work one module at a time. This ensures each layer is verifiable before building atop it.

**Strategy:** "One Module, One Deliverable." We do not context switch between modules. We finish one, verify it, and then unlock the next.

## Phases

### Phase 1: The Gatekeeper (`modules/auth` & `modules/users`) [CURRENT]
- **Modules**: `Users`, `Auth`
- **Goal**: Register users (Owner, Inspector, Manager).
- **Scope**:
  - `UsersModule`: Tenant isolation, User profiles.
  - `AuthModule`: RBAC (Roles: Owner, Inspector, Manager).
- **Mapped ModuleDesign:** [`AuthModule`](../2-during-implementation/DDD/ModuleDesign/Auth/README.md) & [`UsersModule`](../2-during-implementation/DDD/ModuleDesign/Users/README.md)
*   **1.1 Identity Foundation:** JWT, Password Hashing, Session Management.
*   **1.2 Plumber Login:** Mobile-optimized login endpoint.
*   **1.3 LMP Login:** Dashboard-optimized login endpoint.
*   **1.4 Password Reset:** Secure email flow (using `shared-kernel`).
*   **Verification:** `curl` login returns a valid JWT with correct roles.

### Phase 2: The Staff (`modules/crm`)
- **Modules**: `CRM`
- **Goal**: Ingest building data from external sources (or manual entry) and manage Owner/Staff data.
- **Scope**:
  - `CRMModule`: Properties, Owners, Contacts.
  - *Note*: We are combining Building and Owner logic into `CRM`.
- **Mapped ModuleDesign:** [`CRMModule`](../2-during-implementation/DDD/ModuleDesign/CRM/README.md)
*   **2.1 Company Tenancy:** `plumbing_companies` table. Link users to a company.
*   **2.2 Technician Profile:** `technicians` table. Link `auth_id` to `technician_id`.
*   **2.3 LMP Profile:** `company_admins` table.
*   **Verification:** Admin can "Invite Technician" -> Technician appears in DB.

### Phase 3: The Target (`modules/crm`)
**Goal:** We have the *External World*.
**Prerequisite:** `users` exists (LMP needs to create owners).
**Mapped ModuleDesign:** [`CRMModule`](../2-during-implementation/DDD/ModuleDesign/CRM/README.md)
*   **3.1 Owner Client:** `owners` table (Contact info).
*   **3.2 Building Asset:** `buildings` table (Address, BIN, Community District). Use `owner_id`.
*   **Verification:** LMP can "Create Owner" and "Add Building" to that owner.

### Phase 4: The Job (`modules/inspections`) [CORE]

**Goal:** The *Work* happens here. This is the biggest phase.

**Prerequisite:** `users` and `crm` exist.

- **Modules**: `Inspections`
- **Goal**: Create and Assign jobs to Inspectors.
- **Scope**:
  - `InspectionsModule`: Job creation, Dispatch logic (manual/auto), tracking status, Forms, Photos, Offline capabilities.
  - *Note*: `JobDispatch`, `FieldCapture`, `Compliance` are now under `Inspections`.
- **Mapped ModuleDesigns:**
  - [`InspectionsModule`](../2-during-implementation/DDD/ModuleDesign/Inspections/README.md)
*   **4.1 Job Intake:** LMP creates `inspection_job` linked to a Building (CRM) and Tech (Users).
*   **4.2 Dispatch:** LMP updates `inspection_job` to assign a Technician.
*   **4.3 The Packet (GPS1):** Define the JSON schema for the Inspection Form (Questions/Answers).
*   **4.4 Field Capture:** Endpoints for Technicians to `GET /jobs` and `POST /jobs/:id/submit`.
*   **4.5 Review Status:** LMP endpoints to `approve` or `reject` (return for fixes).
*   **Verification:** Full circle: Create Job -> Assign -> Submit -> Approve -> Job is `FINALIZED`.

### Phase 5: The Trophy (`modules/reporting`)
**Goal:** The *Customer* gets value.
**Prerequisite:** `inspections` are `FINALIZED`.
**Mapped ModuleDesign:** [`ReportingModule`](../2-during-implementation/DDD/ModuleDesign/Reporting/README.md)
*   **5.1 PDF Generator:** Template engine (e.g., `pdfmake` or `puppeteer`) to render GPS1.
*   **5.2 Export Endpoint:** `GET /jobs/:id/report`.
*   **Verification:** Clicking "Download" produces a valid PDF matching the input data.

## Verification Plan

### Automated Tests
*   **Unit**: Each module will have local unit tests (Jest/Vitest) for business logic.
*   **E2E**: We will write a "Super Test" script that simulates the entire flow using `curl` or a test runner:
    1.  Login as Admin.
    2.  Create Tech & Building.
    3.  Create Job & Assign Tech.
    4.  Login as Tech.
    5.  Submit Job.
    6.  Login as Admin.
    7.  Approve Job.
    8.  Download PDF.

### Manual Verification
*   **Database Check**: Inspect Postgres to ensure foreign keys are strictly enforced between modules (e.g., `inspection_jobs.technician_id` -> `technicians.id`).
