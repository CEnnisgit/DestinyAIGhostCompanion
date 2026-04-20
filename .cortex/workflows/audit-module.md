---
description: Audit a module for architectural compliance
---

# Audit Module Workflow

## When to Use

Use this workflow when:
- ✅ Verifying a module follows hexagonal architecture
- ✅ After major refactoring
- ✅ Reviewing code quality before release
- ✅ Onboarding to understand module structure

Do NOT use when:
- ❌ Adding new features → Use `/plan-feature`
- ❌ Understanding request flow → Use `/trace-request`

---

Use this workflow to verify a module follows hexagonal architecture patterns.

## 1. Select Module

Which module are you auditing?
- [ ] auth
- [ ] company
- [ ] compliance
- [ ] Other: ___

## 2. Verify Folder Structure

// turbo
```bash
ls -la apps/backend/src/modules/{module}/
```

**Required folders:**
- [ ] `domain/` - Pure types (entities, value objects)
- [ ] `ports/` - Repository interfaces
- [ ] `adapters/` - Database implementations
- [ ] `application/` - Use-cases

**Required files:**
- [ ] `moduleFactory.ts` - Dependency wiring
- [ ] `index.ts` - Public API exports
- [ ] `NAVIGATION.md` - Module documentation

## 3. Check Domain Purity

Domain folder should have NO imports from:
- ❌ `infrastructure/`
- ❌ `drizzle-orm`
- ❌ `fastify`
- ❌ Other modules' internals

// turbo
```bash
grep -r "from.*infrastructure\|from.*drizzle\|from.*fastify" apps/backend/src/modules/{module}/domain/
```

**Expected:** No matches

## 4. Verify Ports

Check that ports are interfaces, not implementations:

// turbo
```bash
cat apps/backend/src/modules/{module}/ports/index.ts
```

Each port should:
- [ ] Be a TypeScript interface
- [ ] Define method signatures only
- [ ] Have no implementation details
- [ ] Be exported from `ports/index.ts`

## 5. Verify Adapters Implement Ports

Check adapter imports:
```bash
cat apps/backend/src/modules/{module}/adapters/drizzle/*.ts | head -20
```

Each adapter should:
- [ ] Import its corresponding port interface
- [ ] Implement all port methods
- [ ] Only import from `infrastructure/` and `ports/`

## 6. Check Use-Case Dependencies

Use-cases should only depend on ports, not adapters:

// turbo
```bash
grep -r "from.*adapters\|from.*Drizzle" apps/backend/src/modules/{module}/application/
```

**Expected:** No matches (use-cases import ports, not adapters)

## 7. Verify Module Factory

Check `moduleFactory.ts`:

```bash
cat apps/backend/src/modules/{module}/moduleFactory.ts
```

Should:
- [ ] Accept repository implementations as parameters
- [ ] Create and wire all use-cases
- [ ] Export typed module interface
- [ ] NOT instantiate adapters directly

## 8. Verify Public API (index.ts)

Check `index.ts`:

```bash
cat apps/backend/src/modules/{module}/index.ts
```

Should export:
- [ ] Module factory function
- [ ] Module type
- [ ] Domain types (entities, DTOs)
- [ ] Port interfaces
- [ ] Adapter implementations (for container wiring)

Should NOT export:
- ❌ Internal implementation details
- ❌ Use-case internals

## 9. Check NAVIGATION.md

Read documentation:
```bash
cat apps/backend/src/modules/{module}/NAVIGATION.md
```

Should include:
- [ ] Use-case table with inputs/outputs
- [ ] Ports table with methods
- [ ] Adapters table
- [ ] Domain types table
- [ ] File structure

## 10. Verify Container Wiring

Check that module is properly wired in container:

```bash
grep -A 10 "{module}" apps/backend/src/app/container.ts
```

Should:
- [ ] Import module factory
- [ ] Import adapter implementations
- [ ] Create module instance
- [ ] Export via container object

## 11. Generate Audit Report

```markdown
# Module Audit: {module}

## Structure Compliance

| Check | Status | Notes |
|-------|--------|-------|
| Folder structure | ✅/❌ | |
| Domain purity | ✅/❌ | |
| Ports defined | ✅/❌ | |
| Adapters implement ports | ✅/❌ | |
| Use-cases depend on ports | ✅/❌ | |
| Module factory correct | ✅/❌ | |
| Public API clean | ✅/❌ | |
| Documentation complete | ✅/❌ | |
| Container wiring | ✅/❌ | |

## Issues Found

| Severity | Issue | Location | Fix |
|----------|-------|----------|-----|
| 🔴 High | | | |
| 🟡 Medium | | | |
| 🟢 Low | | | |

## Recommendations

1. ...
2. ...
```

## 12. Fix Issues

For each issue found:
1. Create fix in appropriate file
2. Run tests to verify no regressions
3. Update NAVIGATION.md if needed
