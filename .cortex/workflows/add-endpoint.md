---
description: Add a new API endpoint with proper wiring and tests
---

# Add Endpoint Workflow

## When to Use

Use this workflow when:
- ✅ Adding a new HTTP endpoint
- ✅ The **use-case already exists** in a module
- ✅ Just need to wire route → use-case

Do NOT use when:
- ❌ The business logic doesn't exist yet → Use `/plan-feature` first
- ❌ Just understanding how an endpoint works → Use `/trace-request`

---

Use this workflow when adding a new API endpoint to the backend.

## 1. Determine Endpoint Details

Before proceeding, define:
- [ ] HTTP method (GET, POST, PATCH, DELETE)
- [ ] Path (e.g., `/api/v1/jobs/:id/assign`)
- [ ] Authentication required? (Yes/No)
- [ ] Required roles (OWNER, TECHNICIAN, COMPANY_ADMIN, PLATFORM_ADMIN)
- [ ] Request body schema (if POST/PATCH)
- [ ] Response format

## 2. Find Route Group

// turbo
```bash
ls apps/backend/src/app/http/routes/
```

| Path prefix | Route group |
|-------------|-------------|
| `/api/v1/auth/*` | `routes/auth/` |
| `/api/v1/companies/*` | `routes/companies/` |
| `/api/v1/buildings/*` | `routes/buildings/` |
| `/api/v1/jobs/*` | `routes/jobs/` |
| `/api/v1/jobs/:id/form*` | `routes/forms/` |
| `/api/v1/jobs/:id/form/report*` | `routes/reports/` |
| `/api/v1/booking/*` | `routes/bookings/` |

**Decision:**
- Fits existing group → Add to that `routes.ts`
- Needs new group → Create new folder (see step 6)

## 3. Check if Use-Case Exists

Read the module NAVIGATION.md for use-cases:

// turbo
```bash
cat apps/backend/src/modules/compliance/NAVIGATION.md
cat apps/backend/src/modules/auth/NAVIGATION.md
cat apps/backend/src/modules/company/NAVIGATION.md
```

**Decision:**
- Use-case exists → Use it directly
- Use-case needed → Run `/plan-feature` workflow first

## 4. Add Route Handler

Open the route file and add handler:

```typescript
// Example: POST /api/v1/jobs/:id/assign
fastify.post<{ Params: { jobId: string } }>('/:jobId/assign', {
    preHandler: [authenticate, requireRoles('COMPANY_ADMIN')]
}, async (request, reply) => {
    const { jobId } = request.params;
    const parsed = AssignJobSchema.safeParse(request.body);
    if (!parsed.success) {
        throw new ValidationError(parsed.error.errors[0]?.message || 'Invalid request');
    }
    
    const result = await container.compliance.useCases.jobs.assign.execute(
        jobId,
        parsed.data
    );
    return reply.send({ success: true, data: result });
});
```

**Checklist:**
- [ ] Type params and body
- [ ] Add auth middleware if needed
- [ ] Parse and validate request body
- [ ] Call use-case from container
- [ ] Return standardized response

## 5. Add Route Test

Open or create `routes.test.ts` in the same folder:

```typescript
describe('POST /api/v1/jobs/:id/assign', () => {
    it('should assign job to technician', async () => {
        vi.mocked(container.compliance.useCases.jobs.assign.execute)
            .mockResolvedValue({ ...mockJob, status: 'SCHEDULED' });

        const response = await app.inject({
            method: 'POST',
            url: '/api/v1/jobs/job-123/assign',
            payload: { technicianId: 'tech-123', scheduledDate: '2024-01-15' },
        });

        expect(response.statusCode).toBe(200);
        expect(response.json().data.status).toBe('SCHEDULED');
    });

    it('should return 400 for invalid payload', async () => {
        const response = await app.inject({
            method: 'POST',
            url: '/api/v1/jobs/job-123/assign',
            payload: {},
        });

        expect(response.statusCode).toBe(400);
    });
});
```

## 6. New Route Group (if needed)

If creating a new route group:

### 6.1 Create folder and files
```bash
mkdir apps/backend/src/app/http/routes/{name}
touch apps/backend/src/app/http/routes/{name}/routes.ts
touch apps/backend/src/app/http/routes/{name}/routes.test.ts
```

### 6.2 Create routes.ts
```typescript
import { FastifyInstance, FastifyPluginOptions } from 'fastify';
import { container } from '../../../container';
import { authenticate, requireRoles } from '../../middleware/auth';

export async function {name}Routes(
    fastify: FastifyInstance,
    _opts: FastifyPluginOptions
): Promise<void> {
    // Add routes here
}
```

### 6.3 Export from index.ts
```typescript
// In routes/index.ts
export { {name}Routes } from './{name}/routes';
```

### 6.4 Register in server.ts
```typescript
await app.register({name}Routes, { prefix: '/api/v1/{name}' });
```

## 7. Verify

// turbo
```bash
pnpm --filter backend test -- --run
```

## 8. Update Documentation

- [ ] Update `routes/README.md` route map if new group
- [ ] Update `CODEBASE_INDEX.md` route map if new group
