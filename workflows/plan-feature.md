---
description: Validate feature plans against architecture before implementation
---

# Plan Feature Workflow

## When to Use

Use this workflow when:
- ✅ Starting a **new feature** from scratch
- ✅ Feature requires new use-cases or domain logic
- ✅ Unsure which module a feature belongs in

Do NOT use when:
- ❌ Just adding an endpoint (use-case already exists) → Use `/add-endpoint`
- ❌ Debugging or understanding code → Use `/trace-request`
- ❌ Checking architecture compliance → Use `/audit-module`

---

Use this workflow when planning a new backend feature to validate placement, dependencies, and reuse opportunities.

## 1. Gather Feature Requirements

Before proceeding, ensure you have:
- [ ] Clear description of what the feature does
- [ ] Who uses it (API consumer, internal service, etc.)
- [ ] What data it operates on

## 2. Read Architecture Context

Read these files to understand current architecture:

```
// turbo
view_file apps/backend/CODEBASE_INDEX.md
view_file apps/backend/src/modules/README.md
view_file apps/backend/src/modules/auth/NAVIGATION.md
view_file apps/backend/src/modules/company/NAVIGATION.md
view_file apps/backend/src/modules/compliance/NAVIGATION.md
view_file apps/backend/src/shared/README.md
```

## 3. Determine Module Placement

Answer these questions:

### 3.1 Does it fit an existing module?

| Module | Belongs here if... |
|--------|-------------------|
| `auth` | User identity, authentication, password management |
| `company` | Company, technicians, admins, ownership |
| `compliance` | Jobs, forms, buildings, reports, inspections |

**Decision:**
- If YES → Place in existing module's `application/` folder
- If NO → Create new module (proceed to 3.2)

### 3.2 New module checklist (if needed)

- [ ] Module name is a noun (singular or plural)
- [ ] Module has clear bounded context
- [ ] Module doesn't duplicate existing domain concepts
- [ ] Create folder structure:
  ```
  src/modules/{name}/
  ├── domain/
  ├── ports/
  ├── adapters/drizzle/
  ├── application/
  ├── moduleFactory.ts
  ├── index.ts
  └── NAVIGATION.md
  ```

## 4. Check for Cross-Cutting Concerns

### 4.1 Does it need data from other modules?

| Needs access to | Resolution |
|-----------------|------------|
| User data | Import from `auth` module |
| Company data | Import from `company` module |
| Job/Form data | Import from `compliance` module |

**Rule:** Dependencies flow → inward. A new module CAN depend on existing modules.

### 4.2 Does it modify multiple entities in one operation?

If YES, this is an **orchestration use-case**:
- [ ] Needs `UnitOfWork` for transaction boundaries
- [ ] See `docs/architecture/TRANSACTION_BOUNDARIES.md`

### 4.3 Cross-module orchestration

If the feature orchestrates across modules:
- Place use-case in the module that **owns the primary action**
- Inject dependencies from other modules via ports
- Do NOT import adapters directly from other modules

## 5. Check for Shared Reuse

### 5.1 Error handling

| Need | Use |
|------|-----|
| Invalid input | `ValidationError` from `shared/errors` |
| Resource not found | `NotFoundError` from `shared/errors` |
| Permission denied | `ForbiddenError` from `shared/errors` |
| Not authenticated | `UnauthorizedError` from `shared/errors` |
| Duplicate/conflict | `ConflictError` from `shared/errors` |

### 5.2 Logging

```typescript
import { logger } from '../../../shared/logger';
```

### 5.3 Transaction boundaries

If updating multiple repositories atomically:
```typescript
import { UnitOfWork } from '../../../shared/ports';
```

## 6. Route Placement

### 6.1 Does it need an HTTP endpoint?

If YES:

| Question | Answer |
|----------|--------|
| Fits existing route group? | Add to `routes/{group}/routes.ts` |
| Needs new route group? | Create `routes/{name}/routes.ts` + `routes.test.ts` |
| Requires authentication? | Add `preHandler: [authenticate, requireRoles(...)]` |
| Public endpoint? | No auth middleware |

### 6.2 New route group checklist

- [ ] Create `routes/{name}/routes.ts`
- [ ] Create `routes/{name}/routes.test.ts`
- [ ] Export from `routes/index.ts`
- [ ] Register in `server.ts`
- [ ] Add to route map in `CODEBASE_INDEX.md`

## 7. Test Strategy

| Component | Test Type | Location |
|-----------|-----------|----------|
| Use-case logic | Unit/Integration | `modules/{name}/{name}.test.ts` |
| Route handler | E2E (inject) | `routes/{name}/routes.test.ts` |
| Repository | Via use-case tests | Mocked in tests |

## 8. Generate Plan Output

Create a plan summary:

```markdown
# Feature Plan: [Feature Name]

## Placement
- **Module:** [auth/company/compliance/NEW: name]
- **Reason:** [Why it belongs here]

## Components to Create

### Use-Cases
| Name | File | Purpose |
|------|------|---------|
| ... | modules/.../application/...UseCase.ts | ... |

### Ports (if new)
| Name | File |
|------|------|
| ... | modules/.../ports/...Repository.ts |

### Adapters (if new)
| Name | Implements |
|------|------------|
| ... | ...Repository |

### Routes
| Method | Path | Handler |
|--------|------|---------|
| ... | /api/v1/... | routes/.../routes.ts |

## Dependencies
- [ ] Wire in moduleFactory.ts
- [ ] Wire in container.ts
- [ ] Export from module index.ts

## Cross-Cutting Concerns
- [ ] Needs UnitOfWork: [Yes/No]
- [ ] Imports from other modules: [List]

## Shared Reuse
- [x] Using shared errors
- [x] Using shared logger
- [ ] Other: ...

## Test Plan
- [ ] Module tests: X tests
- [ ] Route tests: X tests
```

## 9. Validation Checklist

Before proceeding to implementation:

- [ ] Feature has a clear home (one module)
- [ ] No circular dependencies between modules
- [ ] Dependencies flow inward (new → existing)
- [ ] Using shared utilities instead of recreating
- [ ] Transaction boundaries identified
- [ ] Route placement determined
- [ ] Test strategy defined
- [ ] Plan documented

## 10. Consider ADR Need

> [!TIP]
> If this feature involves architectural decisions (new patterns, technology choices, trade-offs), flag it for ADR capture after implementation. Run `/adr-check` when the feature is complete.

## 11. Proceed to Implementation

Once plan is validated:
- Create implementation_plan.md artifact with the plan summary
- Request user review before implementing
- Follow CONTRIBUTING.md checklists during implementation
