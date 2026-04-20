## C. System-level UML Diagrams

I will use text-based UML (PlantUML style) so you can paste it directly into tools like PlantUML, Mermaid (with small adjustments), or other UML editors.

### C.1 Component Diagram – High-Level System

This shows the main subsystems and how they interact.

```plantuml
@startuml
title Plumbers Compliance & Dispatch - Component Diagram (High Level)

package "Client Applications" {
  [Owner Web Portal]
  [Company Admin Dashboard]
  [Technician Mobile App]
}

package "Backend Platform" {
  [API Gateway / BFF]

  package "Domain Services" {
    [Auth & Identity Service]
    [Company Service]
    [Marketplace Service]
    [Compliance Service]
    [Reporting Service]
    [Notification Service]
  }
}

package "Data Stores" {
  [Primary Relational DB]
  [Object Storage (Reports, Photos)]
}

package "External Integrations" {
  [Email Provider]
  [SMS Provider]
  [Geocoding / Maps API]
}

[Owner Web Portal] --> [API Gateway / BFF]
[Company Admin Dashboard] --> [API Gateway / BFF]
[Technician Mobile App] --> [API Gateway / BFF]

[API Gateway / BFF] --> [Auth & Identity Service]
[API Gateway / BFF] --> [Company Service]
[API Gateway / BFF] --> [Marketplace Service]
[API Gateway / BFF] --> [Compliance Service]
[API Gateway / BFF] --> [Reporting Service]
[API Gateway / BFF] --> [Notification Service]

[Company Service] --> [Primary Relational DB]
[Marketplace Service] --> [Primary Relational DB]
[Compliance Service] --> [Primary Relational DB]
[Reporting Service] --> [Object Storage (Reports, Photos)]
[Compliance Service] --> [Object Storage (Reports, Photos)]

[Notification Service] --> [Email Provider]
[Notification Service] --> [SMS Provider]
[Marketplace Service] --> [Geocoding / Maps API]

@enduml
```

This aligns with the earlier philosophy:

* **Marketplace domain** → Marketplace Service
* **Supply/company domain** → Company Service
* **Compliance domain** → Compliance & Reporting Services

---

### C.2 Sequence Diagram – “Owner Requests LL152 Inspection”

This captures the cross-boundary flow and is useful for API design and service responsibility.

```plantuml
@startuml
title Sequence - Owner Requests LL152 Inspection

actor Owner as O
participant "Owner Web Portal" as OW
participant "API Gateway" as API
participant "Marketplace Service" as MS
participant "Company Service" as CS
participant "Notification Service" as NS
database "DB" as DB

O -> OW: Open plumberscompliance.com LL152 page
O -> OW: Fill Request Inspection form
OW -> API: POST /service-requests
API -> MS: createServiceRequest(payload)
MS -> DB: INSERT ServiceRequest
MS -> MS: Run matching algorithm (find suitable PlumbingCompany)
MS -> CS: notifyCompanyOfNewServiceRequest(companyId, requestId)
CS -> DB: CREATE InspectionJob (status=PENDING_ASSIGNMENT)

MS -> NS: sendOwnerConfirmation(ownerContact, requestId)
NS -> Owner: Email/SMS confirmation

CS -> NS: sendCompanyNotification(companyContact, jobId)
NS -> "Company Admin": Email/SMS: New LL152 job

@enduml
```

Key design consequence:

* **ServiceRequest** is created first (marketplace domain), then **InspectionJob** (compliance domain) is created once a company is selected.

---

### C.3 Sequence Diagram – “Technician Completes LL152 Inspection”

This covers the technician workflow and report generation.

```plantuml
@startuml
title Sequence - Technician Completes LL152 Inspection

actor Technician as T
participant "Technician Mobile App" as TM
participant "API Gateway" as API
participant "Compliance Service" as CS
participant "Reporting Service" as RS
participant "Notification Service" as NS
database "DB" as DB
collections "Object Storage" as OS

T -> TM: Open app and log in
TM -> API: GET /jobs?technicianId=...
API -> CS: getAssignedJobs(technicianId)
CS -> DB: SELECT InspectionJobs
CS --> API: jobs list
API --> TM: jobs list

T -> TM: Open specific job, start inspection
TM -> API: POST /inspection-forms (partial or full)
API -> CS: saveInspectionForm(data)
CS -> DB: INSERT/UPDATE InspectionForm (status=IN_PROGRESS)

T -> TM: Capture photos & finalize form
TM -> API: POST /inspection-forms/{id}/submit
API -> CS: submitInspectionForm(formId)
CS -> DB: UPDATE InspectionForm (status=COMPLETED)
CS -> DB: UPDATE InspectionJob (status=COMPLETED)

CS -> OS: Store photos (via upload endpoints)

CS -> RS: generateReport(inspectionFormId)
RS -> DB: READ InspectionForm, Job, Building
RS -> OS: Create PDF and store report
RS -> DB: INSERT InspectionReport (link to object storage)

RS -> NS: notifyOwnerAndCompany(reportId)
NS -> "Owner": Email with report link
NS -> "Company Admin": Email with report link

@enduml
```

Design consequence:

* **InspectionForm** is the authoritative record of inspection data.
* **InspectionReport** is derived, versioned, and stored as an artifact.

---

### C.4 UML Class Diagram – Core Domain (Skeleton)

This ties directly to your ontology in section E.

```plantuml
@startuml
title Core Domain Class Diagram (Simplified)

class User {
  + userId: UUID
  + email: string
  + role: UserRole
}

enum UserRole {
  PLATFORM_ADMIN
  COMPANY_ADMIN
  TECHNICIAN
  OWNER
}

class PlumbingCompany {
  + companyId: UUID
  + name: string
  + licenseNumber: string
  + serviceAreas: string[]
}

class Technician {
  + technicianId: UUID
  + userId: UUID
  + companyId: UUID
}

class Owner {
  + ownerId: UUID
  + userId: UUID
}

class Building {
  + buildingId: UUID
  + addressLine1: string
  + borough: string
  + zipcode: string
}

class ServiceRequest {
  + requestId: UUID
  + buildingId: UUID
  + ownerId: UUID
  + status: RequestStatus
}

enum RequestStatus {
  RECEIVED
  MATCHED
  CANCELLED
}

class InspectionJob {
  + jobId: UUID
  + companyId: UUID
  + technicianId: UUID
  + buildingId: UUID
  + status: JobStatus
}

enum JobStatus {
  PENDING_ASSIGNMENT
  SCHEDULED
  IN_PROGRESS
  COMPLETED
  CANCELLED
}

class InspectionForm {
  + formId: UUID
  + jobId: UUID
  + status: FormStatus
  + submittedAt: datetime
}

enum FormStatus {
  IN_PROGRESS
  COMPLETED
}

class InspectionReport {
  + reportId: UUID
  + formId: UUID
  + storageUrl: string
  + createdAt: datetime
}

User "1" -- "0..1" Owner
User "1" -- "0..1" Technician
PlumbingCompany "1" -- "0..*" Technician
Owner "1" -- "0..*" Building
Building "1" -- "0..*" ServiceRequest
ServiceRequest "1" -- "0..1" InspectionJob
PlumbingCompany "1" -- "0..*" InspectionJob
Technician "1" -- "0..*" InspectionJob
Building "1" -- "0..*" InspectionJob
InspectionJob "1" -- "1" InspectionForm
InspectionForm "1" -- "1" InspectionReport

@enduml
```

---
