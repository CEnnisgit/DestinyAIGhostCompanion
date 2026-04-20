# Companies API

> Status: ✅ Production Ready  
> Base URL: `/api/v1/companies`

## Overview

Manage plumbing companies and their technicians.

---

## Endpoints

### POST /companies
> Status: ✅ Production

Create a new company (links current user as admin).

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`

**Request:**
```json
{
  "companyName": "ABC Plumbing",
  "contactEmail": "contact@abcplumbing.com",
  "contactPhone": "+1-555-123-4567",
  "serviceAreas": ["10001", "10002"],  // Optional
  "address": "123 Main St, NY"  // Optional
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "companyId": "uuid",
    "companyName": "ABC Plumbing",
    "contactEmail": "contact@abcplumbing.com",
    "contactPhone": "+1-555-123-4567",
    "serviceAreas": ["10001", "10002"],
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

---

### GET /companies/:companyId
> Status: ✅ Production

Get company details.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN` (own company), `PLATFORM_ADMIN`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "companyId": "uuid",
    "companyName": "ABC Plumbing",
    "contactEmail": "contact@abcplumbing.com",
    "contactPhone": "+1-555-123-4567",
    "serviceAreas": ["10001", "10002"],
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

---

### PATCH /companies/:companyId
> Status: ✅ Production

Update company details.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN` (own company), `PLATFORM_ADMIN`

**Request:**
```json
{
  "companyName": "ABC Plumbing LLC",
  "serviceAreas": ["10001", "10002", "10003"]
}
```

---

### GET /companies/:companyId/technicians
> Status: ✅ Production

List all technicians for a company.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN` (own company)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "technicianId": "uuid",
      "userId": "uuid",
      "licenseNumber": "PL12345",
      "user": {
        "email": "tech@example.com",
        "role": "TECHNICIAN"
      }
    }
  ]
}
```

---

### POST /companies/:companyId/technicians
> Status: ✅ Production

Add technician to company.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN` (own company)

**Request:**
```json
{
  "userId": "uuid",
  "licenseNumber": "PL12345"  // Optional
}
```

**Errors:**
- `404` - User not found
- `409` - User already a technician

---

### DELETE /companies/:companyId/technicians/:technicianId
> Status: ✅ Production

Remove technician from company.

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN` (own company)

---

## GET /me/company
> Status: ✅ Production  
> Base URL: `/api/v1/me/company`

Get current user's company (for dashboard bootstrap).

**Auth:** 🔐 Requires JWT | Roles: `COMPANY_ADMIN`, `TECHNICIAN`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "companyId": "uuid",
    "companyName": "ABC Plumbing",
    ...
  }
}
```
