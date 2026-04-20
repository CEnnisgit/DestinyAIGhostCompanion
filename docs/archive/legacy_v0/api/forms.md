# Forms API

> Status: ✅ Production Ready  
> Base URL: `/api/v1/jobs/:jobId/form`

## Overview

Handle LL152 inspection forms - create, update, validate, and submit.

---

## Endpoints

### GET /jobs/:jobId/form
> Status: ✅ Production

Get or create form for job.

**Auth:** 🔐 Requires JWT | Company-scoped access

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "formId": "uuid",
    "jobId": "uuid",
    "status": "IN_PROGRESS",
    "formPayload": {
      "inspectorName": "John Smith",
      "gasPipingCondition": "GOOD",
      ...
    },
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

---

### PATCH /jobs/:jobId/form
> Status: ✅ Production

Update form payload (partial merge).

**Auth:** 🔐 Requires JWT | Roles: `TECHNICIAN` (assigned only)

**Request:**
```json
{
  "formPayload": {
    "inspectorName": "John Smith",
    "gasPipingCondition": "GOOD"
  }
}
```

**Note:** Merges with existing payload, doesn't replace.

---

### GET /jobs/:jobId/form/validate
> Status: ✅ Production

Validate form without submitting.

**Auth:** 🔐 Requires JWT | Company-scoped access

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "ready": false,
    "errors": ["photos: Minimum 2 photos required"],
    "warnings": ["notes: Notes are recommended for documentation"]
  }
}
```

---

### POST /jobs/:jobId/form/submit
> Status: ✅ Production

Submit form (runs full validation).

**Auth:** 🔐 Requires JWT | Roles: `TECHNICIAN` (assigned only)

**Errors:**
- `400` - Validation failed (returns errors)
- `400` - Form already submitted

---

## LL152 Form Schema

### Required Fields
```json
{
  "inspectorName": "string",
  "inspectorLicense": "string",
  "inspectionDate": "2024-01-15",
  "gasPipingCondition": "GOOD | FAIR | POOR",
  "overallResult": "PASS | FAIL",
  "defects": [
    {
      "location": "Basement",
      "description": "Corroded pipe",
      "severity": "MINOR | MAJOR | CRITICAL"
    }
  ],
  "photos": ["url1", "url2"],  // Minimum 2
  "clientSignature": "base64..."
}
```

### Business Rules
- `CRITICAL` defects require `FAIL` result
- `FAIL` result should have documented defects
- Minimum 2 photos required
