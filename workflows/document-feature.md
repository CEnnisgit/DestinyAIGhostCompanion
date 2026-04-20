---
description: Document a new feature after implementation
---

# Document Feature Workflow

Run this after implementing a new feature to ensure all doc layers are updated.

## 1. Identify Affected Layers

Check which layers the feature touches:
- [ ] Domain (business logic in `domain/`)
- [ ] Infrastructure (DB, email in `infrastructure/`)
- [ ] API routes (in `app/http/routes/`)

## 2. Update Domain README

If you added a new service or modified domain logic:

1. Open `apps/backend/src/domain/<domain>/README.md`
2. Add the new file to the "Key Files" table
3. Update "Quick Reference" if new concepts added

## 3. Update API Documentation

If you added or changed API endpoints:

1. Open `docs/api/<domain>.md`
2. Add new endpoint with:
   - Status badge (✅ Production / ⚠️ MVP)
   - Request/response schemas
   - Auth requirements
   - Error codes

## 4. Update Architecture Docs

If the feature has complex logic:

1. Check if it fits existing docs in `docs/architecture/`
2. If new pattern, create new architecture doc
3. Add link to domain README

## 5. Add Header Comment

For the main service file:

```typescript
/**
 * [Service Name] - [purpose]
 * 
 * @see docs/architecture/[DOC].md for [topic]
 * @see docs/api/[domain].md for API reference
 */
```

## 6. Update Production Status

1. Open `docs/PRODUCTION_STATUS.md`
2. Add feature to appropriate table
3. Set status: ✅ Production / ⚠️ MVP / ❌ Missing

## 7. Update Agent Context

If major new capability:

1. Open `.agent/context/[DOMAIN]_DOMAIN.md`
2. Add to "Key Concepts" or "Files to Understand"
