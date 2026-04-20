# **PRODUCT REQUIREMENTS DOCUMENT (PRD) – v1.0**

## **NYC Local Law 152 Dispatch & Directory Platform (MVP)**

---

# 1. **Product Overview**

### **1.1 Product Summary**

The platform is a **vertical SaaS + marketplace** built for **NYC Local Law 152 (LL152) gas inspections**, providing:

1. A **Directory & Booking Portal** for property owners to find and schedule LL152 inspections.
2. A **Dispatch & Field Operations SaaS** for plumbers and plumbing companies to manage LL152 inspection jobs.
3. A **Workflow Engine** that digitizes the LL152 inspection process, including forms, photos, signatures, and automated reports.

The MVP focuses exclusively on LL152.

---

# 2. **Objectives & Success Metrics**

### **2.1 Business Objectives (MVP)**

* Enable plumbers to conduct LL152 inspections digitally using a purpose-built mobile workflow.
* Provide a basic directory and intake form for property owners to request LL152 inspections.
* Launch a functioning marketplace flow (simple version) that routes inspection requests to plumbers.
* Monetize initially through SaaS subscriptions.

### **2.2 Success Metrics**

**Plumber-side metrics**

* At least 10–20 plumbers actively using dispatch and inspection workflows.
* 90% of LL152 inspections conducted without external tools or paperwork.

**Demand-side metrics**

* At least 100 property owners submitting LL152 inspection requests.

**Platform metrics**

* Time from booking → completed inspection < 7 days median.
* <5% of jobs abandoned or incomplete due to workflow issues.

---

# 3. **Scope of MVP**

### **3.1 In Scope (Must-Have)**

#### **A. Directory & Booking Layer**

* Public landing page for LL152 education (what it is, deadlines).
* Searchable directory of LL152-qualified plumbers (simple profiles).
* Request Inspection form:

  * Building address (Google Maps autocomplete preferred)
  * Contact info
  * Property type
  * Preferred dates
  * Notes / special instructions
* Routing logic sends job request to a plumber (rules detailed later).

#### **B. Plumber SaaS – Web Interface**

* Company onboarding (add business name, license info, service areas).
* Create/manage jobs.
* Assign jobs to technicians.
* Daily job list.
* Customer and property record storage.

#### **C. Technician Mobile App**

* Job list for the day.
* Job details: address, client info, assignment time window.
* LL152 inspection form:

  * Mandatory DOB fields
  * Photo capture
  * Notes
  * Pass/Fail indicators
  * Client signature
* Submit inspection data.

#### **D. Automated Report Generation**

* PDF report automatically generated upon inspection completion.
* Includes:

  * Technician info
  * Company license
  * Building information
  * Findings summary
  * Pass/fail documentation
  * Photos (embeds or appendices)

#### **E. Marketplace (Simple Version)**

* Incoming job request routed to:

  * The nearest available plumber (distance + availability heuristic), OR
  * A single preselected plumber during MVP to simplify operations.

#### **F. Admin Console (Internal Only)**

* View all plumbers, jobs, inspection submissions.
* Override job routing if needed.

### **3.2 Out of Scope (For Now, Future Versions)**

* Multi-law expansion (LL11, LL87, etc.).
* Complex bidding or auction marketplace.
* Multi-technician routing algorithms.
* Integration with NYC DOB systems.
* Full CRM for plumbers.
* Building portfolio analytics.
* Payment processing.

---

# 4. **User Profiles**

### **4.1 Property Owner / Building Manager**

Needs:

* To learn what LL152 is.
* To find a qualified plumber.
* To book an inspection.
* To receive documentation.

Pain Points:

* Complexity of NYC compliance.
* Lack of easy discovery.

### **4.2 Plumbing Company Owner**

Needs:

* To receive LL152 job requests.
* To manage technicians.
* To complete jobs digitally.
* To keep compliance-grade records.

Pain Points:

* Manual processes.
* Reliance on generic form builders.

### **4.3 Field Technician**

Needs:

* Simple mobile workflow for each job.
* Preloaded LL152 form fields.
* Ability to take photos, notes, and get signatures.

Pain Points:

* Switching between tools.
* Manual paperwork errors.

### **4.4 Platform Admin**

Needs:

* Oversight into jobs and users.
* Ability to troubleshoot issues.

---

# 5. **User Flows**

### **5.1 Property Owner Flow**

1. Lands on LL152 learning page.
2. Clicks “Request LL152 Inspection.”
3. Provides building/address/contact details.
4. Submission triggers:

   * Email confirmation.
   * Internal marketplace routing logic.
5. Matched plumber receives job inquiry.
6. Owner receives scheduled appointment confirmation.
7. Owner receives completed inspection report.

---

### **5.2 Plumber (Company Owner) Flow**

1. Signs up via onboarding form:

   * Company info
   * License # and documentation
   * Boroughs served
2. Creates or accepts incoming LL152 job.
3. Assigns job to a technician.
4. Tracks job status as technician completes the form.
5. Reviews the final PDF report.
6. Sends report to property owner (automatic or manual).

---

### **5.3 Field Technician Flow**

1. Logs into mobile app.
2. Sees today’s scheduled jobs.
3. Selects a job → sees address + instructions.
4. Opens LL152 inspection form.
5. Fills required fields.
6. Takes photos.
7. Obtains tenant/owner signature.
8. Submits inspection.
9. Job marked as completed.

---

# 6. **Functional Requirements**

## **6.1 Directory & Booking**

### **R1 – Search Directory**

* Users can search by ZIP code or borough.
* Results show plumbers with license verification badge (manual in MVP).

### **R2 – Book Inspection**

Fields:

* Name
* Email
* Phone
* Building address (with geocoding)
* Property type (drop-down)
* Message/Notes
* Preferred date/time window

### **R3 – Confirmation Notifications**

* Email to property owner.
* Notification to selected plumber.

---

## **6.2 Plumber SaaS (Web)**

### **R4 – Company Onboarding**

* Add company name, license, and service area.
* Add technician accounts.

### **R5 – Job Dashboard**

* List of open, scheduled, in-progress, completed jobs.
* Job detail page containing:

  * Owner contact
  * Building info
  * Assignment status

### **R6 – Technician Assignment**

* Owner can choose a technician from list.
* Job appears on technician’s mobile app.

---

## **6.3 Technician Mobile App**

### **R7 – Login & Authentication**

* Phone number + password or email + password.

### **R8 – Job List**

* Each job shows:

  * Address
  * Customer name
  * Time window
  * Status

### **R9 – LL152 Form**

Mandatory Inputs:

* Inspection date
* Building address auto-filled
* Inspector name / license no.
* Gas piping condition fields
* Defect reporting
* Pass/Fail
* Notes

Actions:

* Photo capture (min 2 required)
* Signature capture (touchscreen)

### **R10 – Submit Inspection**

* Locks job from further edits.
* Triggers PDF generation.

---

## **6.4 Reporting Engine**

### **R11 – PDF Generator**

* Pulls all submitted fields.
* Formats into standardized LL152 layout.
* Embeds photos.
* Generates two versions:

  * Client Report (clean, branded)
  * Internal Record (more detailed)

### **R12 – Delivery**

* Email to property owner.
* Stored in plumber’s dashboard.

---

## **6.5 Marketplace Logic (Basic)**

### **R13 – Single-Assignment Routing**

* All job requests during MVP are routed to:

  * A single plumber (configuration), OR
  * The nearest plumber (service radius + availability).

### **R14 – Router Logic**

Inputs:

* Building address (lat/long)
* Plumbing company service areas
* Active status (on/off availability toggle)

Outcome:

* Assign job to a single plumber and notify them.

---

# 7. **Non-Functional Requirements**

### **Performance**

* Mobile app loads daily jobs within <1 second on standard LTE.
* PDF generation within <30 seconds of form submission.

### **Security**

* Store all customer and inspection data in encrypted storage.
* Role-based access: technicians cannot see other technicians’ jobs.

### **Compliance**

* PDF output must meet LL152 documentation standards.
* All image capture must validate timestamp.

### **Scalability**

* MVP supports 1,000 total inspections without degradation.

---

# 8. **Assumptions & Dependencies**

* Plumbers provide license documentation voluntarily; auto-verification may come later.
* Property owners do not pay during MVP.
* Payment processing not required before marketplace 2.0.
* Platform initially supports **only NYC LL152**.

---

# 9. **Risks**

1. **Regulatory correctness risk**
   LL152 form fields need to be 100% accurate; must confirm with licensed experts (like your dad).

2. **Adoption risk**
   Plumbers accustomed to basic tools may resist onboarding without clear benefit.

3. **Operational load**
   Manual verification of plumbers and job matching may be needed early.

4. **Data reliability risk**
   Need to ensure correct timestamping and geolocation for legal purposes.

---

# 10. **MVP Milestones & Roadmap**

### Phase 1 – Foundation (Weeks 1–6)

* Plumber onboarding
* Basic dispatcher web app
* Technician mobile app skeleton
* LL152 form draft

### Phase 2 – Workflow Completion (Weeks 7–12)

* Job assignment
* Full LL152 form
* PDF report generator
* Directory landing pages

### Phase 3 – Marketplace Lite (Weeks 13–16)

* Booking form
* Basic routing engine
* Notifications & email flows

### Phase 4 – Stabilization & Launch (Weeks 17–20)

* QA + bug fixes
* Performance tuning
* Launch to first set of plumbers (including your dad)

---

# Next Step Options

I can now produce any of the following:

A. **Functional Specification** (detailed screens, API endpoints, data models)
B. **User Stories & Acceptance Criteria**
C. **Wireframes / UI flow** for each key screen (web + mobile)
D. **Technical Architecture Draft** (frontend, backend, database, hosting, integrations)
E. **Go-to-Market + Business Plan**
F. **Brand positioning + naming exploration**

Tell me which direction you’d like to go next.
