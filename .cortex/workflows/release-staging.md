---
description: Promote dev to staging with proper checks and versioning
---

# Release to Staging Workflow

Use when ready to promote `dev` → `staging`.

## Prerequisites

- All feature branches merged to `dev`
- CI green on `dev`
- No open blockers

## 1. Verify Dev Is Stable

// turbo
```bash
git checkout dev && git pull origin dev
```

// turbo
```bash
pnpm --filter @pcd/backend run lint
```

// turbo
```bash
pnpm --filter @pcd/backend run test -- --run
```

// turbo
```bash
pnpm --filter @pcd/backend run build
```

## 2. Determine Version

Check current version:
```bash
cat apps/backend/package.json | grep version
```

Decide version bump:

| Changes since last release | Bump |
|---------------------------|------|
| Breaking changes | Major (x.0.0) |
| New features | Minor (0.x.0) |
| Bug fixes only | Patch (0.0.x) |

For MVP phase, stay on `0.1.x` (patch bumps).

## 3. Update Version

Update version in `apps/backend/package.json`:
```json
"version": "0.1.X"
```

Commit on dev:
```bash
git add apps/backend/package.json
git commit -m "chore(release): bump version to 0.1.X"
git push origin dev
```

## 4. Create Release PR

Create PR: `dev` → `staging`

**PR Title:**
```
chore(release): promote dev to staging v0.1.X
```

**PR Body Template:**
```markdown
## Release v0.1.X

### Changes in this release
- feat(scope): description
- fix(scope): description
- refactor(scope): description

### Checklist
- [ ] CI green on dev
- [ ] Version bumped
- [ ] DB migrations reviewed (if any)
- [ ] Breaking changes documented (if any)
- [ ] Smoke test plan ready

### Rollback plan
If issues discovered: revert merge commit on staging
```

## 5. Review Checklist

Before merging, verify:

- [ ] All tests passing
- [ ] No console errors in build output
- [ ] Database migrations are backward-compatible
- [ ] Environment variables documented (if new)
- [ ] API changes documented (if any)

## 6. Merge and Deploy

1. **Squash and merge** the PR
2. CI should auto-deploy to staging
3. Run smoke tests on staging environment

## 7. Post-Release

After successful staging deployment:

- [ ] Smoke test critical paths
- [ ] Monitor logs for errors
- [ ] Update `PRODUCTION_STATUS.md` if needed
- [ ] Run `/adr-check` for any ADR candidates

## Quick Release (If Everything Is Ready)

```bash
# From dev, verified clean
git checkout dev && git pull

# Bump version
# (edit apps/backend/package.json)
git add -A && git commit -m "chore(release): bump version to 0.1.X"
git push origin dev

# Create PR via GitHub CLI (if installed)
gh pr create --base staging --head dev \
  --title "chore(release): promote dev to staging v0.1.X" \
  --body "Release v0.1.X - see commits for changes"
```
