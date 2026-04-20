---
description: Quick status check on roadmap progress
---

# Roadmap Status Workflow

Use for a quick overview of project progress.

## 1. Read Roadmap Overview

// turbo
```bash
cat docs/roadmap/README.md
```

The overview table shows progress per component.

## 2. Check Blockers

Read `docs/PRODUCTION_STATUS.md`:

// turbo
```bash
cat docs/PRODUCTION_STATUS.md
```

List any ⚠️ MVP or ❌ Missing items that block progress.

## 3. Summary Report

Format:
```
## Roadmap Status

| App | Progress | Next Priority |
|-----|----------|---------------|
| Backend | 71% (20/28) | PDF generation |
| Dashboard | 64% (7/11) | Page enhancements |
| Owner Portal | 40% (4/10) | Auth |
| Mobile | 67% (8/12) | CI/TestFlight |
| Infrastructure | 60% (6/10) | Domain migration |

### Current Blockers
- [List any MVP items needing upgrade]

### Next Steps
- [First priority item from current focus area]
```

## 4. Deep Dive (Optional)

To see details for a specific component:

```bash
cat docs/roadmap/backend/README.md
cat docs/roadmap/dashboard/README.md
cat docs/roadmap/mobile/README.md
# etc.
```
