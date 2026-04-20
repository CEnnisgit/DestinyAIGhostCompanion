---
description: Quick guide to choosing the right workflow
---

# Workflow Guide

Start here to find the right workflow for your task.

## Decision Tree

```mermaid
flowchart TD
    A[What do you need?] --> B{New API endpoint?}
    B -->|Yes| C{Use-case exists?}
    B -->|No| D{Understanding code?}
    
    C -->|Yes| E[/add-endpoint]
    C -->|No| F[/plan-feature]
    F --> E
    
    D -->|Request flow| G[/trace-request]
    D -->|Architecture check| H[/audit-module]
    D -->|No| I{Planning feature?}
    
    I -->|Yes| F
    I -->|No| J[Check other workflows]
```

## Quick Reference

| I want to... | Use |
|--------------|-----|
| Start a work session | `/start-work` |
| Plan a new feature | `/plan-feature` |
| Add an endpoint (use-case exists) | `/add-endpoint` |
| Understand how a request flows | `/trace-request` |
| Check if a module follows patterns | `/audit-module` |
| Find missing ADRs in recent work | `/adr-check` |
| Draft an ADR from context | `/adr-capture` |
| Make a well-formed commit | `/commit` |
| Promote dev to staging | `/release-staging` |

## Workflow Descriptions

### `/plan-feature`
**When:** Starting a new feature from scratch.

Validates:
- Module placement
- Cross-cutting concerns
- Shared utility reuse
- Transaction boundaries
- Route placement

**Output:** Validated implementation plan

---

### `/add-endpoint`
**When:** Adding an HTTP endpoint where the use-case already exists.

Steps:
- Find route group
- Add handler with middleware
- Add test
- Wire up if new group

**Prereq:** Use-case exists. If not, run `/plan-feature` first.

---

### `/trace-request`
**When:** Debugging or understanding request flow.

Produces:
- Route → Use-case → Repository chain
- Sequence diagram
- Data transformations
- Error paths

---

### `/audit-module`
**When:** Verifying architecture compliance.

Checks:
- Folder structure
- Domain purity
- Port/adapter separation
- Documentation completeness

---

## Workflow Chains

Some tasks need multiple workflows:

| Task | Workflow Chain |
|------|----------------|
| New feature with endpoint | `/plan-feature` → `/add-endpoint` |
| Refactor + verify | Make changes → `/audit-module` |
| Debug failing request | `/trace-request` → fix → test |
