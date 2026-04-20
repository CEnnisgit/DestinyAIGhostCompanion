# Backend API Reference

> Base URL: `http://localhost:3001/api/v1`

## Quick Status

| API | Status | Endpoints |
|-----|--------|-----------|
| [Authentication](./authentication.md) | ✅ Production | 6 |
| [Companies](./companies.md) | ✅ Production | 6 |
| [Buildings](./buildings.md) | ✅ Production | 4 |
| [Jobs](./jobs.md) | ✅ Production | 7 |
| [Forms](./forms.md) | ✅ Production | 4 |
| [Reports](./reports.md) | ⚠️ MVP | 3 |
| [Booking](./booking.md) | ⚠️ MVP | 2 |

See [PRODUCTION_STATUS.md](../PRODUCTION_STATUS.md) for detailed feature inventory.

---

## Authentication

All protected endpoints require `Authorization: Bearer <token>` header.

**Roles:**
- `PLATFORM_ADMIN` - Full system access
- `COMPANY_ADMIN` - Company-scoped access
- `TECHNICIAN` - Assigned job access
- `OWNER` - Own buildings/requests

---

## Common Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format"
  }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `CONFLICT` | 409 | Duplicate resource |
| `INTERNAL_ERROR` | 500 | Server error |
