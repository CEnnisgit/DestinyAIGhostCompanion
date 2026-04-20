# Jobs API

> Status: ✅ Production Ready  
> Base URL: `/api/v1/jobs`

## Overview

Manage inspection jobs with state machine lifecycle.

## State Machine

```
PENDING_ASSIGNMENT → SCHEDULED → IN_PROGRESS → COMPLETED
        ↓               ↓            ↓
     CANCELLED       CANCELLED    CANCELLED
```

**Transition Rules:**
- `PENDING_ASSIGNMENT` → `SCHEDULED` (when tech assigned via `/schedule`)
- `SCHEDULED` → `PENDING_ASSIGNMENT` (when unscheduled via `/unschedule`)
- `SCHEDULED` → `IN_PROGRESS` (when tech starts via `/start`)
- `IN_PROGRESS` → `COMPLETED` (when form submitted via `/complete`)
- Any state → `CANCELLED` (except COMPLETED, via `/cancel`)

---

## Endpoints

### POST /jobs
> Status: ✅ Production

Create a new inspection job.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`, `PLATFORM_ADMIN`

**Request:**
```json
{
  "buildingId": "uuid",
  "lawType": "LL152",
  "technicianId": "uuid",  // Optional - assigns immediately
  "scheduledAt": "2024-02-01T09:00:00Z"  // Optional
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "jobId": "uuid",
    "companyId": "uuid",
    "buildingId": "uuid",
    "status": "PENDING_ASSIGNMENT",
    "lawType": "LL152",
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

---

### GET /jobs
> Status: ✅ Production

List jobs (filtered by company or technician).

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`, `TECHNICIAN`, `PLATFORM_ADMIN`

**Query Params:**
- `status` - Filter by status
- `technicianId` - Filter by technician
- `buildingId` - Filter by building

---

### GET /jobs/:jobId
> Status: ✅ Production

Get job details.

**Auth:** 🔐 Requires JWT | Company-scoped access

---

### PATCH /jobs/:jobId
> Status: ✅ Production

Update job details.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`, `PLATFORM_ADMIN`

**Request:**
```json
{
  "lawType": "LL152",
  "notes": "Updated notes"
}
```

---

## State Transition Endpoints

### POST /jobs/:jobId/schedule
> Status: ✅ Production

Schedule job with technician and time.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`

**Request:**
```json
{
  "technicianId": "uuid",
  "scheduledStart": "2024-02-01T09:00:00Z",
  "scheduledEnd": "2024-02-01T11:00:00Z"
}
```

**Result:** Status changes to `SCHEDULED`

---

### POST /jobs/:jobId/unschedule
> Status: ✅ Production

Remove scheduling, return to pending.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`

**Result:** Status changes to `PENDING_ASSIGNMENT`

---

### POST /jobs/:jobId/start
> Status: ✅ Production

Start job (technician begins work).

**Auth:** 🔐 Requires JWT | Roles: `TECHNICIAN` (assigned only)

**Result:** Status changes to `IN_PROGRESS`

---

### POST /jobs/:jobId/complete
> Status: ✅ Production

Complete job (after form submitted).

**Auth:** 🔐 Requires JWT | Roles: `TECHNICIAN` (assigned only)

**Result:** Status changes to `COMPLETED`

---

### POST /jobs/:jobId/cancel
> Status: ✅ Production

Cancel job.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`, `PLATFORM_ADMIN`

**Request:**
```json
{
  "reason": "Optional cancellation reason"
}
```

**Errors:**
- `400` - Cannot cancel completed job
