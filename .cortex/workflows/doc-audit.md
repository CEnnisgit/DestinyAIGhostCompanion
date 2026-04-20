---
description: Audit docs for staleness and missing coverage
---

# Doc Audit Workflow

Run periodically to find stale or missing documentation.

## 1. Audit Domain READMEs

For each folder in `apps/backend/src/domain/`:

// turbo
```bash
ls apps/backend/src/domain/*/README.md
```

Check each README has:
- [ ] All services listed in "Key Files"
- [ ] Correct doc links
- [ ] Up-to-date "Quick Reference"

## 2. Audit API Docs

For each route file in `apps/backend/src/app/http/routes/`:

// turbo
```bash
ls apps/backend/src/app/http/routes/*.ts
```

Compare against `docs/api/`:

// turbo
```bash
ls docs/api/*.md
```

Report any route file without corresponding API doc.

## 3. Verify PRODUCTION_STATUS.md

1. Open `docs/PRODUCTION_STATUS.md`
2. For each feature listed, verify:
   - Feature still exists
   - Status is accurate (✅/⚠️/❌)
   - Upgrade path is still valid

## 4. Check Architecture Docs

For each doc in `docs/architecture/`:

// turbo
```bash
ls docs/architecture/*.md
```

Verify:
- [ ] Code locations are valid
- [ ] Diagrams match current code
- [ ] Extension guides are accurate

## 5. Report Gaps

List any findings:
- Missing domain READMEs
- Missing API docs
- Stale status badges
- Broken doc links
