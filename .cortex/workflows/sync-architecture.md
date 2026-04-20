---
description: Sync architecture docs after major refactoring
---

# Sync Architecture Workflow

Run after major refactoring to ensure architecture docs reflect current code.

## 1. List Architecture Docs

// turbo
```bash
ls docs/architecture/
```

Current docs:
- `JOB_STATE_MACHINE.md`
- `LL152_VALIDATION.md`
- `ACCESS_CONTROL.md`
- `JWT_TOKEN_STRATEGY.md`
- `FORM_PAYLOAD_HANDLING.md`
- `REPOSITORY_PATTERN.md`

## 2. Verify Code Locations

For each doc, check that file paths are still valid:

Example from `JOB_STATE_MACHINE.md`:
- `domain/compliance/services/JobService.ts` exists?
- `app/http/routes/jobRoutes.ts` exists?
- `infrastructure/db/schema/inspectionJobs.ts` exists?

## 3. Verify Diagrams

Check Mermaid diagrams match code:

**JOB_STATE_MACHINE.md:**
- Compare state diagram to `VALID_TRANSITIONS` in `JobService.ts`

**ACCESS_CONTROL.md:**
- Compare role matrix to actual middleware checks

## 4. Verify Code Snippets

Check that code snippets in docs match actual code:
- Interfaces should match
- Type definitions should match
- Example patterns should match

## 5. Update Extension Guides

If patterns changed:
- Update "Adding New X" sections
- Verify example code compiles

## 6. Update Header Comments

If file locations changed, update `@see` links in service files:
- `JobService.ts`
- `LL152ValidationService.ts`
- `AuthService.ts`
- `auth.ts` middleware
