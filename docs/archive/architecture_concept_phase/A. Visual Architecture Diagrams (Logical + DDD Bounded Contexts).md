## A. Visual Architecture Diagrams (Logical + DDD Bounded Contexts)

I will give you **two complementary diagrams** in text/PlantUML form:

1. **Logical architecture** – how clients, backend services, storage, and integrations fit together.
2. **Domain/bounded context map** – how your core domains (Marketplace, Compliance, Company, etc.) relate.

You can paste these into any PlantUML-compatible renderer.

### A.1 Logical Architecture Diagram

```plantuml
@startuml
title Plumbers Compliance & Dispatch - Logical Architecture

cloud "Client Applications" {
  [Owner Web Portal]
  [Company Admin Dashboard]
  [Technician Mobile App]
}

node "Backend Platform" {
  [API Gateway / BFF]

  node "Domain Services" {
    [Auth & Identity Service]
    [Company Service]
    [Marketplace Service]
    [Compliance Service]
    [Reporting Service]
    [Notification Service]
  }
}

database "Primary DB (PostgreSQL)" as DB
collections "Object Storage (Reports, Photos)" as OS

node "External Services" {
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

[Auth & Identity Service] --> DB
[Company Service] --> DB
[Marketplace Service] --> DB
[Compliance Service] --> DB
[Reporting Service] --> DB

[Compliance Service] --> OS
[Reporting Service] --> OS

[Notification Service] --> [Email Provider]
[Notification Service] --> [SMS Provider]

[Marketplace Service] --> [Geocoding / Maps API]

@enduml
```

This diagram assumes a **single codebase** with domain modules that could later be factored out into microservices if desired.

---

### A.2 Domain-Driven Design (DDD) Bounded Context Map

This shows **which domain owns which concepts**, and who depends on whom.

```plantuml
@startuml
title Plumbers Compliance & Dispatch - Bounded Contexts

package "User & Identity Context" {
  [Auth & Identity BC]
}

package "Company Context" {
  [Company BC\n(PlumbingCompany, Technician)]
}

package "Marketplace Context" {
  [Marketplace BC\n(ServiceRequest, Matching)]
}

package "Compliance Context" {
  [Compliance BC\n(Building, InspectionJob, InspectionForm)]
}

package "Reporting & Documents Context" {
  [Reporting BC\n(InspectionReport)]
}

package "Notification Context" {
  [Notification BC\n(Email/SMS)]
}

[Auth & Identity BC] -[#gray]-> [Company BC] : Users authenticate\nthen act as CompanyAdmin/Technician
[Auth & Identity BC] -[#gray]-> [Marketplace BC] : Owners authenticate\nas Owners

[Company BC] --> [Compliance BC] : Assign jobs to technicians
[Marketplace BC] --> [Compliance BC] : Create InspectionJobs\nfrom ServiceRequests

[Compliance BC] --> [Reporting BC] : Generate reports\nfrom completed forms
[Reporting BC] --> [Notification BC] : Notify stakeholders\nwith report links

[Marketplace BC] --> [Notification BC] : Confirm service requests

@enduml
```

Key points:

* **Compliance BC** is your core domain (heart of the business).
* **Marketplace BC** and **Company BC** depend on it for actual work execution.
* **Reporting BC** is a supporting subdomain (derived artifacts).
* **Notification BC** is a generic subdomain used by several contexts.
* **Auth & Identity BC** is a generic supporting context.

These boundaries are exactly what you will mirror in code modules and services.

---

