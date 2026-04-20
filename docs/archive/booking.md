# Booking API

> Public booking endpoints for owners to request LL152 inspections

## Endpoints

### Create Booking ⚠️ MVP

```http
POST /api/v1/booking
```

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "addressLine1": "123 Main Street",
  "addressLine2": "Apt 4B",
  "borough": "Manhattan",
  "zipcode": "10001",
  "contactName": "John Doe",
  "contactEmail": "john@example.com",
  "contactPhone": "555-123-4567",
  "propertyType": "residential",
  "preferredDateStart": "2024-01-15",
  "preferredDateEnd": "2024-01-20"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| addressLine1 | string | ✓ | Street address |
| addressLine2 | string | | Apt/unit/suite |
| borough | enum | ✓ | Manhattan/Brooklyn/Queens/Bronx/Staten Island |
| zipcode | string | ✓ | 5-digit ZIP code |
| contactName | string | ✓ | Owner/contact name |
| contactEmail | string | ✓ | Email address |
| contactPhone | string | ✓ | Phone number |
| propertyType | string | | residential/commercial/mixed-use |
| preferredDateStart | string | | ISO date for preferred start |
| preferredDateEnd | string | | ISO date for preferred end |

**Response (201):**
```json
{
  "success": true,
  "data": {
    "requestId": "uuid",
    "buildingId": "uuid",
    "jobId": "uuid",
    "status": "confirmed",
    "companyName": "NYC Premier Plumbing",
    "message": "Your LL152 inspection request has been received..."
  }
}
```

**Errors:**
| Code | Message |
|------|---------|
| VALIDATION_ERROR | Address, borough, and zipcode are required |
| VALIDATION_ERROR | Contact name, email, and phone are required |
| VALIDATION_ERROR | No plumbing companies available |

---

### Get Company Directory ⚠️ MVP

```http
GET /api/v1/booking/directory
```

**Authentication:** None (public endpoint)

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "companyId": "uuid",
      "name": "NYC Premier Plumbing",
      "licenseNumber": "LIC-12345",
      "serviceAreas": ["Manhattan", "Brooklyn"],
      "phone": "555-123-4567",
      "email": "info@nycplumbing.com"
    }
  ]
}
```

---

## MVP Notes

> [!WARNING]
> **Current Limitations:**
> - No owner authentication - bookings are anonymous
> - Jobs auto-assigned to first available company (no matching algorithm)
> - Uses seed owner record for building association
