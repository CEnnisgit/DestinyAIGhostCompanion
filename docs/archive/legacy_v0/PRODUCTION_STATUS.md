# Production Status

> Complete inventory of backend features with readiness status

## Status Legend

| Badge | Meaning | Action Required |
|-------|---------|-----------------|
| ✅ **Production** | Real implementation, tested | None |
| ⚠️ **MVP** | Works but placeholder | Upgrade before prod |
| ❌ **Missing** | Not implemented | Build it |

---

## Feature Inventory

### Authentication & Authorization

| Feature | Status | Notes |
|---------|--------|-------|
| User Registration | ✅ | argon2 hashing, JWT issuance |
| User Login | ✅ | Validates credentials, returns tokens |
| JWT Access Tokens | ✅ | 15 min expiry, @fastify/jwt |
| JWT Refresh Tokens | ⚠️ | Stateless only - no revocation |
| Password Reset | ✅ | Email + 30 min token |
| Role-Based Access | ✅ | 4 roles enforced in middleware |
| Rate Limiting | ✅ | @fastify/rate-limit (5/10/3/100 per min) |

### Company Management

| Feature | Status | Notes |
|---------|--------|-------|
| Company CRUD | ✅ | Full Drizzle persistence |
| Technician Management | ✅ | Add/remove/list |
| Company Admin Assignment | ✅ | Link to users table |
| Service Areas | ✅ | Schema ready, config stored |

### Compliance Domain

| Feature | Status | Notes |
|---------|--------|-------|
| Building CRUD | ✅ | Owner-scoped access control |
| Job Creation | ✅ | Links company, building, tech |
| Job State Machine | ✅ | Enforced transitions |
| Technician Assignment | ✅ | Access control checks |
| LL152 Form Handling | ✅ | Create/update/submit |
| LL152 Validation | ✅ | Zod + business rules |
| PDF Generation | ⚠️ | Text-based, not real PDF |
| Report Storage | ⚠️ | Logs path only, no S3 |
| Report Versioning | ✅ | Version field in DB |
| Photo Upload | ❌ | Schema only, no endpoint |

### Notifications

| Feature | Status | Notes |
|---------|--------|-------|
| Email Service | ✅ | Resend integration |
| Password Reset Email | ✅ | Template ready |
| Job Notification Emails | ❌ | Not implemented |
| SMS Notifications | ❌ | Not implemented |

### Infrastructure

| Feature | Status | Notes |
|---------|--------|-------|
| PostgreSQL Setup | ✅ | Docker Compose |
| Database Migrations | ✅ | Drizzle Kit |
| Structured Logging | ✅ | pino with request IDs |
| Error Handling | ✅ | Custom error classes |
| CI/CD Pipeline | ✅ | GitHub Actions lint + test |
| Seed Script | ✅ | Test data for local dev |

### Company Dashboard (Frontend)

| Feature | Status | Notes |
|---------|--------|-------|
| Login Page | ✅ | Cookie-based auth |
| Logout | ✅ | Clears httpOnly cookies |
| Dashboard Home | ✅ | Job summary + stats |
| Job List | ✅ | Filters by status/technician |
| Job Detail | ✅ | Status timeline, assign modal |
| Create Job | ✅ | Building + law type form |
| Technician List | ✅ | View company technicians |
| Company Settings | ✅ | Read-only company info |

### Owner Portal (Frontend)
> **DEPRECATED**: Out of scope for Pilot. Archived to `apps/_deprecated`.


### Marketplace Domain

| Feature | Status | Notes |
|---------|--------|-------|
| Service Request Creation | ⚠️ | Via booking form |
| Auto-Job Creation | ⚠️ | Assigns first available company |
| Company Matching | ❌ | No algorithm yet |

### Technician Mobile App

| Feature | Status | Notes |
|---------|--------|-------|
| Login Screen | ✅ | JWT auth, verified on emulator |
| Jobs List | ✅ | Pull-refresh, status badges |
| Job Detail | ✅ | Building info, start/inspect |
| Inspection Form | ✅ | Full LL152 fields |
| Photo Capture | ✅ | Camera + gallery |
| Signature Pad | ✅ | Canvas-based |
| Metro Config | ✅ | pnpm monorepo compatible |
| Unit Tests | ❌ | Not implemented |
| CI/TestFlight | ❌ | Paused (iOS deferred) |

### Feature-Centric Modules (Refactor)

| Module | Status | Package |
|--------|--------|---------|
| Auth | ✅ | `@pcd/auth` |
| Jobs | ✅ | `@pcd/jobs` |
| Buildings | ✅ | `@pcd/buildings` |
| Bookings | ❌ | **DEPRECATED** |
| Reports | ✅ | `@pcd/reports` |
| Company | ✅ | `@pcd/company` |
| Compliance Forms | ✅ | `@pcd/compliance-forms` |
| **Command Center** | ✅ | `@pcd/job-dispatch` |

---

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Production | 31 | 81% |
| ⚠️ MVP | 4 | 9% |
| ❌ Missing | 3 | 10% |

---

## Upgrade Path for MVP Items

### 1. JWT Refresh Token Revocation
**Current:** Stateless tokens, can't be invalidated on logout
**Fix:** Store refresh tokens in DB, check `is_revoked` on /refresh
**Priority:** Medium

### 2. PDF Generation
**Current:** Returns text string disguised as PDF path
**Fix:** Install `pdfkit`, generate actual PDF with NYC DOB format
**Priority:** High (required for real inspections)

### 3. Report Storage
**Current:** Logs fake path, stores nothing
**Fix:** Add S3/Cloudflare R2, upload PDF, store real URL
**Priority:** High (pairs with PDF fix)

