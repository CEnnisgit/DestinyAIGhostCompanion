# Phase 4: Application & Presentation

> **Status:** 🔲 Not Started
> **Objective:** Wire the domain to real users — API, dashboards, mobile capture, reporting, and deadline tracking.

---

## Work Areas

By this phase, all domain aggregates and workflows are fully specced. Implementation becomes execution, not design.

### 1. API Layer

Stand up the Fastify server and expose REST endpoints for the domain.

**Scope:**
- Job CRUD + state transitions
- Auth endpoints (login, logout, refresh)
- Building search
- Photo upload
- Report generation endpoints

### 2. LMP Dashboard (Lane B — Web)

The company admin interface for managing the full job lifecycle.

**Scope:**
- Job intake form (create job, associate building)
- Dispatch panel (assign technician, schedule)
- Job queue view (filterable by status, sorted by deadline)
- Review panel (view findings, photos, approve/return)
- Deadline dashboard (approaching/past due alerts)
- Report access (download GPS1/GPS2 PDFs)
- Search/history by address

### 3. Plumber Capture (Lane A — Mobile-First)

The technician's field tool. Phone-first, minimal typing.

**Scope:**
- Assigned jobs list
- Job detail view (access notes, contacts, building info)
- GPS1 guided capture form (multi-section, progress indicator)
- Photo capture and labeling
- Draft auto-save (offline capable)
- Submit with completeness validation
- Confirmation screen

### 4. Reporting

GPS1/GPS2 PDF generation from finalized job data.

**Scope:**
- PDF template matching DOB GPS1/GPS2 form layout
- Auto-populated from inspection findings
- Owner packet bundling (GPS1 + GPS2 + photos)
- Archival export

### 5. Deadline Tracking

Compliance deadline calculation and alerting.

**Scope:**
- Deadline calculation service (30/60/120/180-day logic)
- Sub-cycle map (Community District → A/B/C/D mapping)
- Deadline dashboard view (approaching, past due, sorted by urgency)
- Reminder notifications (7 days before, 1 day before)

---

## Relevant Requirements (SRSD)

### Presentation & Integration

| Requirement | Description | Area |
|-------------|-------------|------|
| `SFR-IODO-01` | Assigned jobs list (plumber) | Lane A |
| `SFR-IODO-02` | Job detail view (plumber) | Lane A |
| `SFR-IODO-03` | Submission confirmation (plumber) | Lane A |
| `SFR-IODO-10` | Job queue (LMP) | Lane B |
| `SFR-IODO-11` | Review panel (LMP) | Lane B |
| `SFR-IODO-12` | Deadline dashboard (LMP) | Lane B |
| `SFR-IODO-13` | Search/history by address | Lane B |
| `SFR-IRI-01` | Mobile app → backend REST API | API |
| `SFR-IRI-02` | Dashboard → backend REST API | API |
| `SFR-IRI-03` | Photo upload multipart POST | API |
| `SFR-IRDX-01` | JSON request/response format | API |
| `SFR-IRDX-02` | Photo upload (JPEG/PNG, max 10MB) | API |
| `SFR-IRDX-03` | Export format (PDF, ZIP) | Reporting |
| `SFR-IRDX-10` | Online-first, local draft storage | Lane A |
| `SFR-PRDP-01` | Sort by scheduled date | Lane A |
| `SFR-PRDP-02` | Filter by status | Lane B |
| `SFR-PRDP-03` | Search by address | Lane B |
| `SFR-PRDP-10` | Funnel counts by status | Lane B |
| `SFR-BRW-10..13` | Notifications (dispatch, submit, return, deadline) | Notifications |
| `SFR-PRC-10` | Time-to-capture tracking (< 2 min target) | Instrumentation |

### Non-Functional

| Requirement | Description | Area |
|-------------|-------------|------|
| `SNFR-UEU-01..04` | Phone-first design, minimal typing, touch targets | Lane A |
| `SNFR-UE-01` | Time-to-value < 2 minutes for capture | Lane A |
| `SNFR-PRT-01..03` | API response times | API |
| `SNFR-RR-01..02` | Draft persistence, offline sync | Lane A |
| `SNFR-RAV-01..02` | System availability | Infrastructure |

---

## Dependencies

- Phase 1 (Job Engine) — aggregate and state machine specs
- Phase 2 (LL152 Workflow) — form schema, validation rules, output spec
- Phase 3 (People & Tenancy) — auth, roles, company isolation

---

## Deliverables

> These will be defined in more detail when Phase 4 begins. For now, high-level scope only.

- [ ] Fastify API server with domain module wiring
- [ ] Auth endpoints (login, logout, refresh, password reset)
- [ ] Job lifecycle endpoints
- [ ] LMP Dashboard (Next.js or React)
- [ ] Plumber capture UI (React Native or mobile-first web)
- [ ] GPS1/GPS2 PDF generation service
- [ ] Deadline calculation service
- [ ] Notification service (email at minimum)

---

## Exit Criteria

- [ ] LMP can create, dispatch, review, approve, and export a job end-to-end
- [ ] Plumber can view assigned jobs, capture GPS1 data, attach photos, and submit
- [ ] GPS1 PDF generates correctly from finalized data
- [ ] Deadline tracking shows approaching/past due jobs
- [ ] PRD §0.3 pilot success criteria achievable
