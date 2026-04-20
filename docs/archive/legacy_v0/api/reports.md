# Reports API

> Status: ⚠️ MVP (PDF generation is text-based)  
> Base URL: `/api/v1/jobs`

## Overview

Generate, retrieve, and send PDF inspection reports.

---

## Endpoints

### POST /jobs/:jobId/form/report
> Status: ⚠️ MVP

Generate PDF report from completed form.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`, `TECHNICIAN`, `PLATFORM_ADMIN`

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "reportId": "uuid",
    "formId": "uuid",
    "storageUrl": "/reports/uuid-v1.pdf",
    "version": 1,
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

**Errors:**
- `400` - Form not completed (must submit first)

**⚠️ MVP Note:** Currently generates text content, not actual PDF. For production:
1. Install `pdfkit` or `@react-pdf/renderer`
2. Create NYC DOB-compliant PDF template
3. Store to S3/R2 instead of local path

---

### GET /jobs/:jobId/form/report
> Status: ✅ Production

Get latest report for form.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`, `TECHNICIAN`, `PLATFORM_ADMIN`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "reportId": "uuid",
    "formId": "uuid",
    "storageUrl": "/reports/uuid-v1.pdf",
    "version": 1,
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

**Errors:**
- `404` - No report generated yet

---

### GET /jobs/:jobId/form/reports
> Status: ✅ Production

List all report versions for a form.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`, `PLATFORM_ADMIN`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    { "reportId": "uuid", "version": 2, "createdAt": "..." },
    { "reportId": "uuid", "version": 1, "createdAt": "..." }
  ]
}
```

---

### POST /report/:reportId/send
> Status: ✅ Production

Send report via email to building owner.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`, `PLATFORM_ADMIN`

**Request:**
```json
{
  "recipientEmail": "owner@example.com",
  "resend": false  // Optional, set true to resend
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "reportId": "uuid",
    "sentAt": "2024-01-15T11:00:00Z"
  }
}
```

**Errors:**
- `400` - recipientEmail is required

---

## Upgrade Path to Production

### 1. Real PDF Generation
```bash
pnpm --filter @pcd/backend add pdfkit
```

Then update `PDFGenerator.ts` to use pdfkit with NYC DOB template.

### 2. Cloud Storage
```bash
pnpm --filter @pcd/backend add @aws-sdk/client-s3
# or
pnpm --filter @pcd/backend add @cloudflare/r2
```

Then update `ReportService.ts` to:
1. Upload PDF to S3/R2
2. Return signed download URL
3. Store real URL in `storageUrl` field
