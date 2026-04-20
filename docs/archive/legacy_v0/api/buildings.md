# Buildings API

> Status: ✅ Production Ready  
> Base URL: `/api/v1/buildings`

## Overview

Manage buildings/properties for LL152 inspections.

---

## Endpoints

### POST /buildings
> Status: ✅ Production

Create a new building.

**Auth:** 🔐 Requires JWT | Roles: `OWNER`

**Request:**
```json
{
  "addressLine1": "123 Main St",
  "addressLine2": "Suite 100",  // Optional
  "borough": "Manhattan",
  "zipcode": "10001",
  "lat": 40.7128,  // Optional
  "lng": -74.006   // Optional
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "buildingId": "uuid",
    "ownerId": "uuid",
    "addressLine1": "123 Main St",
    "borough": "Manhattan",
    "zipcode": "10001",
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

---

### GET /buildings
> Status: ✅ Production

List all buildings for current owner.

**Auth:** 🔐 Requires JWT | Roles: `OWNER`, `PLATFORM_ADMIN`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    { "buildingId": "uuid", "addressLine1": "123 Main St", ... }
  ]
}
```

---

### GET /buildings/:buildingId
> Status: ✅ Production

Get building details.

**Auth:** 🔐 Requires JWT

---

### PATCH /buildings/:buildingId
> Status: ✅ Production

Update building details.

**Auth:** 🔐 Requires JWT | Roles: `OWNER`, `PLATFORM_ADMIN`

**Request:**
```json
{
  "addressLine2": "Floor 2"
}
```

---

### DELETE /buildings/:buildingId
> Status: ✅ Production

Delete a building.

**Auth:** 🔐 Requires JWT | Roles: `OWNER`, `PLATFORM_ADMIN`

**Response:** `200 OK`
```json
{
  "success": true
}
```

**Errors:**
- `403` - Not owner of building
- `400` - Building has active jobs (cannot delete)
