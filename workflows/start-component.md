---
description: Begin work on a roadmap app with proper context
---

# Start App Workflow

Use when beginning work on a specific app (backend, dashboard, mobile, owner-portal, etc.).

## 1. Read App Roadmap

```bash
cat docs/roadmap/<app>/README.md
```

Replace `<app>` with: `backend`, `dashboard`, `owner-portal`, `mobile`, or `infrastructure`.

For component-level work within an app:
```bash
cat docs/roadmap/dashboard/jobs.md
cat docs/roadmap/mobile/ios.md
# etc.
```

## 2. List Pending Items

Extract all uncompleted `[ ]` items from the app or component roadmap.

## 3. Check Production Status

// turbo
```bash
cat docs/PRODUCTION_STATUS.md
```

Identify any MVP items for this app that should be upgraded first.

## 4. Check Dependencies

Review the main roadmap for cross-app dependencies:

// turbo
```bash
cat docs/roadmap/README.md
```

## 5. Create Implementation Plan

Create `implementation_plan.md` with:
- Goal for this work session
- Proposed changes (files to create/modify)
- Verification plan

## 6. Set Up Task Tracking

Update your `task.md` with items as checklist.

## 7. Review Relevant Docs

For the app, review:
- `.agent/context/` for domain context
- `docs/api/` for existing endpoints (if backend)
- `docs/architecture/` for patterns to follow
