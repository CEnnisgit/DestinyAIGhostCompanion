---
description: Wrap up roadmap app work with verification and documentation
---

# Complete App Workflow

Use when finishing work on an app to ensure clean handoff.

## 1. Review App Items

Open the app roadmap and verify all targeted items are done:

```bash
cat docs/roadmap/<app>/README.md
```

For component-level work, also check the component file.

## 2. Run Full Verification

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

## 3. Update App Roadmap

Change completed items from `[ ]` to `[x]`.

## 4. Update Progress Counts

Update `docs/roadmap/README.md` with new counts for this app:
- Increment ✅ Done count
- Decrement ⏳ Pending count
- Recalculate Progress %

## 5. Update PRODUCTION_STATUS.md

For each new feature:
- Add to feature inventory table
- Set appropriate status (✅/⚠️)
- Add upgrade path if MVP

## 6. Run /document-feature

For each major feature added, run the `/document-feature` workflow.

## 7. Update CHANGELOG

Add entry to `.agent/progress/CHANGELOG.md`:
- Date
- App/component worked on
- Features added
- Tests added

## 8. Check for ADR Candidates

Run `/adr-check` to identify any architectural decisions made that should be documented.

## 9. Commit Summary

Prepare commit message summarizing:
- App name
- Key features
- Test coverage
- Any new ADRs added
