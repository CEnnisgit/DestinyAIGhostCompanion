---
description: Refresh agent workspace docs after significant changes
---

# Workspace Refresh Workflow

Run this after completing major milestones or significant changes to keep agent context files up to date.

## When to Run

- After scaffolding new apps or packages
- After adding new domain modules
- After database schema changes
- After adding new major features
- At the end of significant work sessions

## Steps

### 1. Update ARCHITECTURE.md

Update `.agent/context/ARCHITECTURE.md` with:
- Current project structure (use `list_dir` to verify)
- Status indicators for each component (✅ complete, 📦 configured, 📁 folder only)
- Available commands
- Tech stack status

### 2. Update DATABASE_SCHEMA.md

If database changes were made, update `.agent/context/DATABASE_SCHEMA.md` with:
- Current tables and their schema files
- Enums defined
- Indexes
- Migration commands

### 3. Update CHANGELOG.md

Add entry to `.agent/progress/CHANGELOG.md` with:
- Date and session description
- What was created/changed
- Key files affected
- Status indicators

### 4. Verify Context Files Are Accurate

Quick checks:
- [ ] ARCHITECTURE.md reflects actual folder structure
- [ ] DATABASE_SCHEMA.md matches schema files
- [ ] CHANGELOG.md has latest session
- [ ] BUSINESS_OVERVIEW.md still accurate (rarely changes)
- [ ] RBAC_MODEL.md still accurate (rarely changes)

## File Locations

```
.agent/
├── context/
│   ├── ARCHITECTURE.md      # Project structure & tech stack
│   ├── BUSINESS_OVERVIEW.md # Business model (stable)
│   ├── DATABASE_SCHEMA.md   # DB tables & migrations
│   └── RBAC_MODEL.md        # Permissions (stable)
├── progress/
│   └── CHANGELOG.md         # Session history
└── workflows/
    └── workspace-refresh.md # This file
```
