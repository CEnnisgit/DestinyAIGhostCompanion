Below is a **clean, rigorous conceptual framework** for your platform *Plumbers Compliance & Dispatch* (plumberscompliance.com).

You are absolutely correct that you have **two sides**, **three personas**, and **multiple layers of value**. If you do not impose order now, your tech stack, data model, and domain architecture will become chaotic.

The goal here is to **create a taxonomy and system model** that can later map cleanly into:

* Domain-driven design
* Microservice boundaries or modular monolith structure
* Database schema
* API design
* Clear UX flows

This is not just theory—this will simplify feature planning, naming, permissions, and long-term scalability.

---

# 1. Foundational Insight

Your platform operates at the intersection of:

### **A. A Two-Sided Marketplace**

* **Supply side**: Plumbers / Plumbing companies.
* **Demand side**: Property owners (or managers).

### **B. A SaaS Platform**

Used **only by the supply side**, for:

* Dispatch
* Field operations
* Compliance documentation

### **C. A Compliance Knowledge Layer**

Used by everyone.

Because of this, the system has **three dimensions**:

1. **User roles** (plumber, plumbing company admin, plumbing technician, property owner).
2. **Business entities** (jobs, buildings, inspections, companies, technicians).
3. **Product surfaces** (directory, booking, SaaS dispatcher, technician app, admin).

If you define these dimensions cleanly, everything falls into place.

---

# 2. Ontology: The Real “Entities” in Your Universe

Instead of thinking about “three types of people,” think about **domain entities**.

Below is the correct domain model:

## **Core Entities**

1. **Plumbing Company** (organization)
2. **Plumber / Technician** (user belonging to company)
3. **Property Owner / Building Manager** (user)
4. **Building** (address with compliance attributes)
5. **Inspection Job** (unit of work)
6. **Inspection Form** (submission)
7. **Report** (artifact generated)
8. **Service Request** (lead from owner → system)

Everything in the platform is a variation, relationship, or action performed on these entities.

This set maps cleanly to a domain-driven design architecture.

---

# 3. User Roles vs. User Archetypes (Very Important Distinction)

You have **roles** and **archetypes**, and they are not the same.

### **Archetypes (Business Personas)**

1. Plumbing Company Owner
2. Technician / Plumber
3. Property Owner / Manager

These are *humans with motivations*.

### **Roles (System Permissions)**

1. **Company Admin** – manages company settings, jobs, technicians.
2. **Technician** – completes field inspection workflows.
3. **Building Owner** – requests inspections and receives reports.
4. **Platform Admin** – internal ops.

Why this matters:

* System permissions should not be tied to "plumber" or "owner" as archetypes.
* They should be tied to what a user can do in the platform.

This separation prevents chaos later.

---

# 4. The Two-Sided Marketplace Model

### **Side 1: Supply (Producers of compliance)**

* Plumbing companies
* Their technicians

They produce:

* Inspections
* Reports
* Availability

### **Side 2: Demand (Consumers of compliance)**

* Property owners
* Building managers
* Real estate firms

They consume:

* Inspections
* Reports
* Regulatory clarity

---

# 5. Product Surfaces (Three Products in One)

Your app is not one app.
It is **three interlocking products**, each with its own purpose.

## **Product 1: Compliance Directory + Booking**

Purpose:

* Educate owners about LL152
* Help them find and request inspectors

Actors:

* Property owners
* Plumbers (as listed vendors)

## **Product 2: Dispatch & Company Dashboard (SaaS)**

Purpose:

* Manage jobs, technicians, schedules
* Maintain building/customer records
* Oversee inspection output

Actors:

* Plumbing company admin
* Dispatcher
* Technician

## **Product 3: Technician Field App**

Purpose:

* Execute LL152 inspections in the field
* Capture photos, notes, signatures
* Submit inspection for report generation

Actors:

* Technicians / Plumbers

When you structure by product surface, your engineering teams can eventually mirror these boundaries.

---

# 6. The Core Philosophy You’re Looking For

Here is the conceptual formula for order:

### **1. Producers vs. Consumers**

* **Producers** generate compliance (plumbers, technicians).
* **Consumers** need compliance (property owners).

### **2. Marketplace vs. SaaS**

Think of two value loops:

#### Marketplace Loop

Owner → Service Request → Plumbing Company → Completed Job

#### SaaS Loop

Plumbing Company → Manage Jobs → Dispatch Technician → Generate Report

These loops overlap **only at the “Inspection Job” entity**, which is the central bridge between the two sides.

### **3. Domain-Driven Core Domains**

Your platform cleanly splits into three DDD domains:

#### **A. Compliance Domain (Core Domain)**

Entities:

* Building
* Inspection Job
* Inspection Form
* Report

This domain is the heart of the business.

#### **B. Supply Domain**

Entities:

* Plumbing Company
* Technician
* Company Admin

This domain powers the SaaS features.

#### **C. Marketplace Domain**

Entities:

* Service Request
* Directory Listing
* Ranking/Matching Logic

This domain powers discovery and job flow.

If you enforce these boundaries in your system architecture, your tech stack will stay clean.

---

# 7. The Taxonomy (Final Ordered System)

Below is the formal taxonomy you can incorporate into engineering documentation.

---

## **I. Actors (User Roles)**

* Platform Admin
* Company Admin
* Technician
* Building Owner

---

## **II. Organizations**

* Plumbing Company
* Building Ownership Entity (optional future feature)

---

## **III. Compliance Objects**

* Building
* Compliance Cycle (LL152 audit cycle)
* Inspection Job
* Inspection Form (in-progress or completed)
* Inspection Report (generated artifact)

---

## **IV. Marketplace Objects**

* Service Request
* Directory Listing
* Routing Assignment

---

## **V. System Services**

* Dispatch Engine
* Technician Workflow Engine
* Report Generator
* Matching Engine
* Notification System
* Document Storage

---

# 8. Mapping This to Tech Stack Decisions

When you start designing your backend and frontend, use this taxonomy to define:

### **A. Microservices or Modular Monolith Folders**

* compliance/
* marketplace/
* company/
* technicians/
* owners/
* jobs/
* documents/

### **B. Database Schema**

Tables (or collections) map directly to domain entities.

Example:

* companies
* technicians
* buildings
* inspection_jobs
* inspection_forms
* inspection_reports
* service_requests
* users
* roles

### **C. API Boundaries**

Start with domain-driven endpoints:

* /companies
* /jobs
* /technicians
* /owners
* /buildings
* /inspections
* /reports
* /marketplace

### **D. Frontend Modules**

* Public site (directory + booking)
* Company dashboard (SaaS web app)
* Technician mobile app

This is a *stable* architecture that will scale even if you expand to other NYC local laws.

---

# 9. The Philosophy (Answering Your Core Question)

To rationalize everything into a single coherent worldview:

### **Your platform is the digital infrastructure that connects:**

* **People who produce compliance** (plumbers)
* **People who need compliance** (property owners)

### **Through:**

* A **marketplace** (matching demand to supply)
* A **SaaS system** (enabling supply to execute the work)
* A **compliance engine** (structuring and documenting inspections)

This triad—**Marketplace + SaaS + Compliance Engine**—is the core philosophy of your product.

Once internalized, every feature you build can be placed in one of these three pillars.

---

# Next Step Options

I can now help you with any of the following:

A. **Visual architecture diagram** (logical + DDD bounded contexts)
B. **Database schema (first pass)**
C. **System-level UML diagrams**
D. **Directory and file structure for backend + frontend**
E. **Naming conventions and entity definitions (formal ontology)**
F. **User permissions and RBAC model**

Which would you like next?
