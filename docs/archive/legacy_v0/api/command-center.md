# Command Center API

> CQRS Query endpoint for dashboard attention queues and KPIs.

Base URL: `/api/v1/command-center`

## Architecture

This API is powered by `@pcd/job-dispatch-backend`, a shared CQRS Query Service. See [job-dispatch README](../../packages/features/job-dispatch/README.md) for the architecture details.

---

## Endpoints

### Get Command Center

Calculates all attention queues and KPIs for the authenticated user's company.

`GET /`

| Attribute | Value |
|-----------|-------|
| **Auth Required** | ✅ Yes (`COMPANY_ADMIN` \| `PLATFORM_ADMIN`) |
| **Rate Limit** | 100/min |
| **Status** | ✅ Production |

#### Request

*No request body*

#### Response

**Status**: `200 OK`

```json
{
  "queues": {
    "noShow": [
      {
        "jobId": "uuid",
        "buildingId": "uuid",
        "technicianId": "uuid",
        "scheduledStart": "2025-12-15T09:00:00Z",
        "scheduledEnd": "2025-12-15T11:00:00Z",
        "age": 2,
        "status": "SCHEDULED"
      }
    ],
    "reportMissing": [],
    "readyToSend": [],
    "flagged": []
  },
  "kpis": {
    "scheduledThisWeek": 12,
    "completedThisWeek": 8,
    "emailPendingCount": 3
  }
}
```

---

## Queue Definitions

| Queue | Condition |
|-------|-----------|
| `noShow` | Job `SCHEDULED`, past `scheduledEnd + 15 min`, no form started |
| `reportMissing` | Form `COMPLETED`, no report after 5 minutes |
| `readyToSend` | Report exists, `sentAt` is null |
| `flagged` | Reserved for correction requests (future) |

---

## KPI Definitions

| KPI | Description |
|-----|-------------|
| `scheduledThisWeek` | Jobs with `SCHEDULED` status, `scheduledStart` in current week |
| `completedThisWeek` | Jobs with `COMPLETED` status, `updatedAt` in current week |
| `emailPendingCount` | Count of reports where `sentAt` is null |

---

## Errors

| Code | Meaning |
|------|---------|
| `401 Unauthorized` | Not logged in |
| `403 Forbidden` | User is not a company admin |

---

## TypeScript Types

Import from `@pcd/job-dispatch-core`:

```typescript
import type { CommandCenterResponse } from '@pcd/job-dispatch-core';
```
