## F. User Permissions and RBAC Model

Here we define:

1. **Roles and their meaning.**
2. **Permissions by resource (RBAC matrix).**
3. **Scoping rules (very important in a multi-tenant marketplace/SaaS).**
4. **Implementation notes.**

### F.1 Roles

We will start with **four primary roles**:

1. `PLATFORM_ADMIN`

   * Internal staff. Full visibility and override across the system.

2. `COMPANY_ADMIN`

   * Plumbing company owner/manager. Manages company, technicians, jobs, and reports *within their company*.

3. `TECHNICIAN`

   * Field user. Can view and complete only jobs assigned to them; limited visibility elsewhere.

4. `OWNER`

   * Property owner/manager. Can request inspections and view reports for buildings they own.

You can later add `SUPPORT` or `READ_ONLY_AUDITOR` roles if needed.

---

### F.2 RBAC Matrix (Resources vs. Roles)

Let us define access in terms of typical CRUD-like verbs:

* **R** – Read
* **C** – Create
* **U** – Update
* **D** – Delete (hard or soft; often restricted)

Resources:

* `User`
* `PlumbingCompany`
* `Technician`
* `Owner`
* `Building`
* `ServiceRequest`
* `InspectionJob`
* `InspectionForm`
* `InspectionReport`

#### High-Level Matrix

(Assume all actions are also constrained by **scope**, which I will define in F.3.)

| Resource         | PLATFORM_ADMIN | COMPANY_ADMIN                                   | TECHNICIAN                                         | OWNER                                        |
| ---------------- | -------------- | ----------------------------------------------- | -------------------------------------------------- | -------------------------------------------- |
| User             | R/C/U/D (all)  | R (self + company users)                        | R (self)                                           | R (self)                                     |
| PlumbingCompany  | R/C/U/D (all)  | R/U (own company)                               | R (own company)                                    | None                                         |
| Technician       | R/C/U/D (all)  | R/C/U/D (technicians in own company)            | R (self)                                           | None                                         |
| Owner            | R/C/U/D (all)  | R (owners linked to their jobs, for contact)    | R (limited – contact info for assigned jobs)       | R/U (self)                                   |
| Building         | R/C/U/D (all)  | R/C/U (buildings where their company has jobs)* | R (buildings for assigned jobs only)               | R/C/U (buildings they own)                   |
| ServiceRequest   | R/C/U/D (all)  | R (requests matched to their company)           | R (requests for jobs assigned to them, limited)    | R/C/U (their own requests)                   |
| InspectionJob    | R/C/U/D (all)  | R/C/U (jobs for their company)                  | R/U (jobs assigned to them, limited fields)        | R (jobs for their buildings; no U)           |
| InspectionForm   | R/C/U/D (all)  | R (forms for their company’s jobs)              | R/C/U (for jobs assigned to them; submit/complete) | R (read-only, via report or selected fields) |
| InspectionReport | R/C/U/D (all)  | R (reports for their company’s jobs)            | R (reports for jobs they worked on)                | R (reports for their buildings/requests)     |

* For `COMPANY_ADMIN` and Buildings: they may not own buildings, but need to manage jobs for buildings where they have active or historical jobs. You can implement this as indirect access via jobs.

---

### F.3 Scoping Rules (Critical for Clean Security)

RBAC is **role-based**, but you also need **scope-based** checks (ABAC-style) to keep tenants isolated.

Key rules:

1. **Company scope**

   * `COMPANY_ADMIN` and `TECHNICIAN` may only access:

     * `InspectionJobs` where `inspection_jobs.company_id = their company_id`.
     * `InspectionForms` and `InspectionReports` linked to those jobs.
     * `Buildings` indirectly through their jobs (do not give them global building access).
   * `COMPANY_ADMIN` may only manage `Technicians` in their own company.

2. **Owner scope**

   * `OWNER` may only access:

     * `Buildings.owner_id = their owner_id`
     * `ServiceRequests.owner_id = their owner_id`
     * `InspectionJobs` where `building_id` is one of their buildings.
     * `Reports` linked to those jobs.

3. **Technician scope**

   * `TECHNICIAN` may only access:

     * `InspectionJobs` where `technician_id = their technician_id`
     * `InspectionForms` for those jobs.
     * `Reports` for those jobs.
     * `Buildings` only in the context of those jobs (read-only).

4. **Platform admin scope**

   * `PLATFORM_ADMIN` is global (for operations and debugging). You may still log and audit their actions separately.

These scope checks should be implemented at the **service level**, not just the HTTP layer, to avoid bypass via internal calls.

---

### F.4 Implementation Notes

1. **Token contents (JWT / session claims)**

   * Include:

     * `user_id`
     * `role`
     * `company_id` (if user is company-linked)
     * `technician_id` (if applicable)
     * `owner_id` (if applicable)

   This avoids repeated DB lookups just to resolve context.

2. **Authorization middleware**

   * For each route, define required roles and common scope checks.
   * Example:

     * `GET /api/v1/inspection-jobs/:id`

       * Allowed roles: `PLATFORM_ADMIN`, `COMPANY_ADMIN`, `TECHNICIAN`, `OWNER`
       * Then:

         * If `PLATFORM_ADMIN` → allow.
         * If `COMPANY_ADMIN` → check job.company_id == user.company_id.
         * If `TECHNICIAN` → check job.technician_id == user.technician_id.
         * If `OWNER` → check job.building.owner_id == user.owner_id.

3. **Policy layer**

   * Encapsulate these checks in a policy service/per-domain policy helper:

     * `CompliancePolicy.canViewJob(user, job)`
     * `CompliancePolicy.canEditForm(user, form)`
   * This will keep controllers thin and make changes easier later.

4. **Auditing**

   * For legal/compliance: log key actions:

     * Inspection form creation/submission.
     * Report generation.
     * Job status changes.
   * Store `performed_by_user_id` in audit tables.

---
