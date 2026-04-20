# Authentication API

> Status: ✅ Production Ready  
> Base URL: `/api/v1/auth`

## Overview

Handles user registration, login, token refresh, and password reset.

## Rate Limiting

All auth endpoints have stricter rate limits for brute-force protection:

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /register | 5 | 1 minute |
| POST /login | 10 | 1 minute |
| POST /forgot-password | 3 | 1 minute |
| All others | 100 | 1 minute |

> [!NOTE]
> Exceeding rate limits returns `429 Too Many Requests`

---

## Endpoints

### POST /register
> Status: ✅ Production

Create a new user account.

**Auth:** 🔓 Public

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "role": "OWNER"  // Optional, defaults to OWNER
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGc...",
    "refreshToken": "eyJhbGc...",
    "expiresIn": 900,
    "user": {
      "userId": "uuid",
      "email": "user@example.com",
      "role": "OWNER"
    }
  }
}
```

**Errors:**
- `400` - Invalid email/password format
- `409` - Email already registered

---

### POST /login
> Status: ✅ Production

Authenticate and get tokens.

**Auth:** 🔓 Public

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGc...",
    "refreshToken": "eyJhbGc...",
    "expiresIn": 900,
    "user": {
      "userId": "uuid",
      "email": "user@example.com",
      "role": "OWNER"
    }
  }
}
```

**Errors:**
- `400` - Invalid request
- `401` - Invalid credentials or deactivated account

---

### POST /refresh
> Status: ⚠️ MVP (no revocation)

Get new tokens using refresh token.

**Auth:** 🔓 Public

**Request:**
```json
{
  "refreshToken": "eyJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGc...",
    "refreshToken": "eyJhbGc...",
    "expiresIn": 900
  }
}
```

**⚠️ MVP Note:** Currently stateless. Cannot revoke tokens on logout. For production, store tokens in DB and check `is_revoked`.

---

### POST /logout
> Status: ✅ Production

Clear authentication cookies.

**Auth:** 🔓 Public

**Request:** No body required

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Note:** Clears `accessToken` and `refreshToken` httpOnly cookies. Also supports cookie-based authentication where tokens are automatically passed via cookies.

---

### POST /forgot-password
> Status: ✅ Production

Request password reset email.

**Auth:** 🔓 Public

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "If an account exists with that email, a password reset link has been sent."
}
```

**Note:** Always returns success to prevent email enumeration.

---

### POST /reset-password
> Status: ✅ Production

Complete password reset with token from email.

**Auth:** 🔓 Public

**Request:**
```json
{
  "token": "uuid-from-email-link",
  "newPassword": "newSecurePassword123"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Password has been reset successfully."
}
```

**Errors:**
- `400` - Invalid token format or password too short
- `400` - Token expired (30 min) or already used

---

### GET /me
> Status: ✅ Production

Get current user info.

**Auth:** 🔐 Requires JWT

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "userId": "uuid",
    "email": "user@example.com",
    "role": "OWNER",
    "isActive": true,
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

---

## Token Expiry

| Token | Expiry | Configurable |
|-------|--------|--------------|
| Access Token | 15 min | `JWT_ACCESS_EXPIRY` |
| Refresh Token | 7 days | `JWT_REFRESH_EXPIRY` |
| Password Reset | 30 min | Hardcoded |
