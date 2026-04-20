# Access Control

> Role-based authorization and company-scoped data access

## Roles

| Role | Description | Typical User |
|------|-------------|--------------|
| `PLATFORM_ADMIN` | Full system access | PCD staff |
| `COMPANY_ADMIN` | Manages one company | Plumbing company owner |
| `TECHNICIAN` | Assigned job access only | Field inspector |
| `OWNER` | Own buildings/requests only | Property owner |

---

## Permission Matrix

| Resource | PLATFORM_ADMIN | COMPANY_ADMIN | TECHNICIAN | OWNER |
|----------|----------------|---------------|------------|-------|
| All companies | ✅ | ❌ | ❌ | ❌ |
| Own company | ✅ | ✅ | 👁️ (read) | ❌ |
| All jobs | ✅ | ❌ | ❌ | ❌ |
| Company jobs | ✅ | ✅ | 👁️ (assigned) | ❌ |
| All buildings | ✅ | ❌ | ❌ | ❌ |
| Own buildings | ✅ | ❌ | ❌ | ✅ |
| User management | ✅ | ❌ | ❌ | ❌ |

---

## Middleware Stack

Three levels of authorization:

### 1. `authenticate`
Verifies JWT token, injects `request.jwtUser`:
```typescript
fastify.get('/protected', { preHandler: [authenticate] }, handler);
```

### 2. `requireRoles(...roles)`
Checks user has one of specified roles:
```typescript
fastify.post('/admin-only', { 
  preHandler: [authenticate, requireRoles('PLATFORM_ADMIN')] 
}, handler);
```

### 3. `requireCompanyAccess`
Ensures user belongs to the company in the request:
```typescript
fastify.get('/companies/:companyId/jobs', {
  preHandler: [authenticate, requireCompanyAccess]
}, handler);
```

---

## Code Location

| File | Responsibility |
|------|----------------|
| [auth.ts](file:///c:/github/pcd/apps/backend/src/app/http/middleware/auth.ts) | All middleware |
| Service files | Additional business logic checks |

---

## Protecting New Endpoints

```typescript
// Public endpoint
fastify.get('/public', handler);

// Requires login
fastify.get('/private', { preHandler: [authenticate] }, handler);

// Requires specific role
fastify.post('/admin', { 
  preHandler: [authenticate, requireRoles('PLATFORM_ADMIN')] 
}, handler);

// Requires company membership
fastify.get('/companies/:companyId/data', {
  preHandler: [authenticate, requireCompanyAccess]
}, handler);
```

---

## Company-Scoping Logic

Most resources are scoped to a company:

```typescript
// In JobService
async getJob(jobId: string, companyId: string): Promise<Job> {
  const job = await this.jobRepo.findById(jobId);
  if (job.companyId !== companyId) {
    throw new ForbiddenError('Cannot access this job');
  }
  return job;
}
```

> [!CAUTION]
> Always pass `companyId` from `request.jwtUser` or middleware, never from request body (user could forge it).
