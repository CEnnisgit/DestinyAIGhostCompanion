---
description: Update API docs after route changes
---

# Update API Docs Workflow

Run after changing any API route to keep docs in sync.

## 1. Identify Changed Route File

Find which route file was modified:
- `authRoutes.ts` → `docs/api/authentication.md`
- `companyRoutes.ts` → `docs/api/companies.md`
- `buildingRoutes.ts` → `docs/api/buildings.md`
- `jobRoutes.ts` → `docs/api/jobs.md`
- `formRoutes.ts` → `docs/api/forms.md`
- `reportRoutes.ts` → `docs/api/reports.md`

## 2. Compare Endpoints

View the route file and list all endpoints:

```typescript
// Pattern: fastify.method('/path', ...)
fastify.post('/register', ...)
fastify.get('/me', ...)
```

Compare against the API doc. Each endpoint should have:
- [ ] Documented in API doc
- [ ] Correct HTTP method
- [ ] Correct path
- [ ] Status badge

## 3. Update Request/Response Schemas

For each endpoint, verify:
- [ ] Request body matches Zod schema
- [ ] Response matches actual return value
- [ ] All fields documented

## 4. Update Auth Requirements

Check each endpoint's `preHandler`:
- No preHandler → 🔓 Public
- `authenticate` → 🔐 Requires JWT
- `requireRoles(...)` → List roles

## 5. Update Error Codes

Document possible errors:
- From Zod validation → 400
- From `UnauthorizedError` → 401
- From `ForbiddenError` → 403
- From `NotFoundError` → 404
- From `ConflictError` → 409

## 6. Update Status Badge

If implementation changed:
- Placeholder → ⚠️ MVP
- Complete → ✅ Production
- Add "MVP Note" for incomplete features
