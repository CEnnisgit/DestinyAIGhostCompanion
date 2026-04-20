# Development Roadmap

> Last Updated: 2025-12-12
> Status: **MVP Complete** - Phases 1-4.1 done, mobile app running on emulator

---

## Current Progress ✅

- [x] Monorepo scaffolding (apps, packages, infra)
- [x] Database schema (Drizzle ORM, 10 tables)
- [x] Documentation (READMEs, GETTING_STARTED, CONTRIBUTING)
- [x] Backend entry point (Fastify server)
- [x] Shared types package

---

## 🎯 MVP Definition

> **MVP = Phases 1–4 + minimal Phase 5 slice**
> 
> Goal: End-to-end flow from "create job" → "complete in mobile" → "see report"

### MVP Must-Haves
- ✅ Auth + roles (login, JWT, RBAC)
- ✅ Company + technician management
- ✅ Buildings CRUD
- ✅ Job lifecycle (create → assign → start → complete)
- ✅ LL152 inspection form (save, submit, validate)
- ✅ Basic PDF report generation
- ✅ Company dashboard (login, jobs, assign, view reports)
- ✅ Technician mobile app (login, jobs, form, photos, signature, submit)
- ✅ Minimal booking form → creates service_request + auto-creates job

### Post-MVP (Defer)
- ❌ Offline support (non-trivial, add after stable online app)
- ❌ Full directory search
- ❌ Matching algorithm (start with single-company routing)
- ❌ SMS notifications
- ❌ Rate limiting
- ❌ Advanced reporting features

---

## Phase 1: Foundation 🏗️ ✅
> Goal: Working backend with auth, company management, and dev infrastructure

### 1.1 Infrastructure Setup
- [x] Docker Compose (PostgreSQL + pgAdmin)
- [x] Run database migrations
- [x] Environment configuration (.env handling)
- [x] **Basic CI workflow** (lint + tests on push)
- [x] **Seed script** for local dev data
- [x] **Structured logging** (pino/winston)
- [x] **Basic error handling middleware**

### 1.2 Auth Domain
- [x] User registration (email/password)
- [x] Login + JWT token issuance
- [x] Password hashing (argon2)
- [x] **Refresh token strategy** (clear pattern for frontends)
- [x] Auth middleware (protect routes)
- [x] Role-based access control

### 1.3 Company Domain
- [x] Company CRUD (create, read, update)
- [x] Technician management (add/remove/list)
- [x] Company admin assignment
- [x] Service area configuration
- [x] **`/me/company` endpoint** (dashboard bootstrap)

---

## Phase 2: Core Compliance Engine ⚙️ ✅
> Goal: Build the heart of the business – inspection workflow

### 2.1 Compliance Domain
- [x] Building CRUD
- [x] Inspection job lifecycle
  - [x] Create job
  - [x] Assign technician
  - [x] **Explicit state machine**:
    ```
    PENDING_ASSIGNMENT → SCHEDULED → IN_PROGRESS → COMPLETED
           ↓                ↓            ↓
        CANCELLED       CANCELLED    CANCELLED
    ```
  - [x] Prevent illegal state transitions
- [x] Inspection form handling
  - [x] Create/update form
  - [x] Submit form
  - [x] **LL152 validation service** (separate from handlers)

### 2.2 Reporting Domain
- [x] **Simple PDF template** (don't over-engineer initially) ⚠️ MVP
- [x] Store reports in object storage ⚠️ MVP
- [x] Versioning (optional, add when needed)

### 2.3 API Routes
- [x] `/api/v1/auth/*`
- [x] `/api/v1/companies/*`
- [x] `/api/v1/buildings/*`
- [x] `/api/v1/jobs/*`
- [x] `/api/v1/forms/*`
- [x] `/api/v1/reports/*`

### 2.4 Minimal Email Integration
- [x] Basic email service setup (SendGrid/Resend)
- [x] Password reset email (at minimum)
- [x] "Test email" for verification

---


## Phase 3: Company Dashboard 💻 ✅
> Goal: Web interface for plumbing companies

### 3.1 Dashboard MVP
- [x] Login page
- [x] Dashboard home (job summary)
- [x] Job list + **filters** (status, technician, date)
- [x] Job detail view
  - [x] Status timeline
  - [x] Assignment info
  - [x] **View/download inspection report**
- [x] Create job manually
- [x] Assign technician modal

### 3.2 Company Management
- [x] Technician list/add/remove
- [x] Company settings page

> ⚠️ Don't over-polish UI initially. Focus on making job lifecycle + form submission **observable**.

---

## Phase 3.5: Minimal Owner Booking 🌐 ✅
> Goal: Exercise full end-to-end flow early

- [x] Simple landing page
- [x] Booking form (address, contact, property type)
- [x] Creates `service_request` record
- [x] **Auto-creates job** for single test company (no matching algorithm yet)
- [x] Basic confirmation page

> This allows testing the complete pipeline before building full owner portal.

---

## Phase 4: Technician Mobile App 📱 ✅
> Goal: Field app for completing inspections (ONLINE ONLY for MVP)

### 4.1 Mobile MVP ✅
- [x] Login screen
- [x] Jobs list (today's jobs)
- [x] Job detail screen
- [x] LL152 inspection form
- [x] Photo capture
- [x] Signature capture
- [x] Submit inspection

### 4.2 CI & Distribution (Future)
- [ ] GitHub Actions → EAS Build
- [ ] TestFlight deployment for iOS testing
- [ ] Play Store internal testing track

### 4.3 Offline Support ❌ POST-MVP
- [ ] Cache jobs locally
- [ ] Queue submissions when offline
- [ ] Background sync
- [ ] Conflict resolution

> ⚠️ Offline is complex. Defer until online app is stable.

---

## Phase 5: Full Owner Portal & Marketplace 🌐
> Goal: Complete public site for property owners (POST-MVP)

### 5.1 Owner Portal
- [ ] Landing page (polished)
- [ ] LL152 education page
- [ ] Plumber directory (search by ZIP/borough)
- [ ] Plumber profile pages
- [ ] Enhanced booking flow

### 5.2 Marketplace Logic
- [ ] Directory listings management
- [ ] **Matching algorithm** (start simple: nearest + available)
- [ ] Service request → company routing
- [ ] Automatic notifications

---

## Phase 6: Notifications & Production 📧
> Goal: Communication and production readiness

### 6.1 Notifications
- [ ] Full email templates
- [ ] SMS service integration (Twilio)
- [ ] Trigger on key events:
  - [ ] Job assigned
  - [ ] Inspection complete
  - [ ] Report ready

### 6.2 Production Prep
- [ ] Rate limiting
- [ ] Security audit
- [ ] Performance testing
- [ ] Deployment pipeline (CI/CD)
- [ ] Monitoring & alerting

---

## Stack Decisions (Confirmed)

| Layer | Technology | Status |
|-------|------------|--------|
| Backend | Fastify + TypeScript | ✅ Committed |
| ORM | Drizzle ORM | ✅ Committed |
| Database | PostgreSQL | ✅ Committed |
| Web Apps | Next.js / React | ✅ Committed |
| Mobile | React Native | ✅ Committed |
| Package Mgr | pnpm workspaces | ✅ Committed |

### Still to Decide
- Email: SendGrid vs Resend vs SES?
- Object Storage: S3 vs Cloudflare R2?
- Hosting: Vercel vs Railway vs Fly.io?

---

## Development Approach

**Vertical slices over horizontal layers**

Instead of building all of auth, then all of company, etc., we'll work in vertical slices:

```
Create job in dashboard → Assign technician → Complete in mobile → See report
```

This ensures end-to-end functionality is validated early.

---

## Notes

*Space for ongoing notes as we build*

- Matching algorithm starts as: "always route to test company" (your dad's)
- Offline support is explicitly deferred - easier to add to stable online app
- Basic logging/monitoring from Phase 1 so we're not flying blind
