# Architectural Patterns: Security Strategy

> **Parent:** [Technology Stack](TechnologyStack.md)

This document explains the **Authentication and Authorization patterns** employed across the system components.

## 1. Authentication Pattern: JWT (Stateless)

The system uses JSON Web Tokens (JWT) for stateless authentication across the API.

### Token Strategy
- **Access Token:** Short-lived (e.g., 15 min). Sent in HTTP Headers (`Authorization: Bearer <token>`).
- **Refresh Token:** Long-lived (e.g., 7 days). Securely stored (HTTPOnly Cookie or Secure Storage on Mobile). Used to obtain new Access Tokens.

### Payload Standard
The JWT payload claims carry essential identity and context information to minimize database lookups for basic authorization.

```typescript
interface TokenPayload {
  userId: string;       // Unique System ID
  email: string;        // Login Identifier
  role: string;         // High-level Scope (ADMIN, TECH, OWNER)
  contextId?: string;   // CompanyId or TechnicianId context
}
```

## 2. Authorization Pattern: RBAC (Role-Based)

Access control is enforced via Role-Based Access Control (RBAC) at the Application Layer.

### Roles
- **PLATFORM_ADMIN:** Full system access.
- **COMPANY_ADMIN:** Full access within their specific `Company` scope.
- **TECHNICIAN:** Access to assigned `Jobs` and capture features.
- **OWNER:** Read-only access to their `Properties` and `Inspections`.

### Enforcement
- **Route Guards:** Middleware checks `role` claim in JWT before processing request.
- **Resource Guards:** Services check `contextId` against requested resource ownership (e.g., checking if `CompanyId` matches the Job's owner).
