---
description: Upgrade an MVP feature to production-ready
---

# MVP to Production Workflow

Use to upgrade a ⚠️ MVP feature to ✅ Production.

## 1. List MVP Items

// turbo
```bash
cat docs/PRODUCTION_STATUS.md
```

Look for items with ⚠️ status.

## 2. Select Target

Choose one MVP item to upgrade. Current MVP items:
- JWT Refresh Token Revocation
- PDF Generation
- Report Storage

## 3. Review Upgrade Path

Read the "Upgrade Path" section in PRODUCTION_STATUS.md for the selected item.

## 4. Create Implementation Plan

Document:
- What needs to change
- Dependencies to add
- Files to modify
- Tests to add

## 5. Implement Upgrade

Follow the upgrade path steps.

## 6. Verify

// turbo
```bash
pnpm --filter @pcd/backend run test -- --run
```

// turbo
```bash
pnpm --filter @pcd/backend run build
```

## 7. Update Documentation

1. Update PRODUCTION_STATUS.md:
   - Change status from ⚠️ to ✅
   - Remove upgrade path (now complete)

2. Update relevant API docs if behavior changed

3. Update architecture docs if pattern changed
