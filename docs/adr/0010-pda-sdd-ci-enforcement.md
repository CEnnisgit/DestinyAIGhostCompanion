# ADR 010: PDA-SDD Documentation Enforcement via CI/CD

**Date:** 2026-01-06  
**Status:** Accepted  
**Deciders:** Development Team

---

## Context

After implementing the Pre-During-After Software Development Documentation (PDA-SDD) model across our documentation (`docs/1-pre-implementation`, `docs/2-during-implementation`, `docs/3-after-implementation`), we needed a mechanism to:

1. **Enforce structural integrity** of the documentation (required folders, files, sections)
2. **Prevent documentation drift** (code changes without corresponding CLD updates)
3. **Maintain compliance** with the PDA-SDD specification (Figure 4, 5, 6 from the research paper)

Without automation, we risk:
- Incomplete Change Log Documents (CLD) missing the required 8 fields
- Code changes merged without documentation updates
- Structural deviations from the PDA-SDD model
- Loss of traceability between code and requirements (SRSD)

---

## Decision

We will implement **automated CI/CD enforcement** of the PDA-SDD model using:

### 1. Documentation Linter (`scripts/pda-lint.js`)
A Node.js script that validates:
- **Folder structure**: Required folders exist (`SRSD/SGI`, `SRSD/SFR`, `DDD`, `CLD`, etc.)
- **Required files**: Essential files present (`RLD.md`, `TraceabilityMatrix.md`, etc.)
- **CLD format**: Every log entry contains all 8 required fields (Significance, Results, Date, Summary, Details, References, Issue Tracking, Author)
- **DDD module structure**: Module design docs follow Figure 5 (Responsibilities, Structure, Interactions, Algorithms, Data Structures)

### 2. GitHub Actions Workflow (`.github/workflows/pda-enforce.yml`)
Two jobs:
- **`pda-lint`**: Runs the linter on every PR to `dev`, `staging`, `main`
- **`pda-staleness-check`**: Ensures code changes (`packages/`, `apps/`) are accompanied by CLD updates (can be bypassed with `skip-docs` label for non-functional changes)

### 3. Feature-to-CLD Mapping (`.github/pda-mapping.json`)
A configuration file that maps code directories to their corresponding CLD sections:
```json
{
  "packages/features/job-dispatch": ["JOB_INTAKE", "DISPATCH"],
  "packages/features/compliance-forms": ["FIELD_CAPTURE", "SUBMISSION"],
  // ...
}
```

This enables **targeted enforcement** rather than generic "any CLD file changed" checks.

---

## Consequences

### Positive
- **Guaranteed compliance**: PRs cannot merge without passing PDA-SDD validation
- **Living documentation**: CLD stays synchronized with code changes
- **Early feedback**: Developers know immediately if they forgot to update docs
- **Audit trail**: Every code change has a corresponding CLD log entry
- **Onboarding**: New developers learn the doc structure through CI failures

### Negative
- **Friction**: Developers must update docs for every functional change (mitigated by `skip-docs` label for refactors)
- **Maintenance**: The mapping file needs updates when new features are added
- **False positives**: Cross-cutting changes might trigger multiple CLD update requirements

### Neutral
- **CI time**: Adds ~30 seconds to PR checks (acceptable overhead)
- **Learning curve**: Team must understand PDA-SDD structure (one-time cost)

---

## Alternatives Considered

### 1. Manual Reviews
**Rejected**: Too error-prone, relies on reviewer diligence, doesn't scale.

### 2. Commit Hooks (Pre-commit)
**Rejected**: Only runs locally, can be bypassed with `--no-verify`.

### 3. Periodic Audits
**Rejected**: Reactive rather than preventive, creates documentation debt.

---

## Implementation Notes

### Bypassing Staleness Check
For non-functional changes (refactors, dependency updates, config tweaks), add the `skip-docs` label to the PR.

### Adding New Features
When creating a new package in `packages/features/`:
1. Add it to `.github/pda-mapping.json`
2. Map it to the appropriate CLD section(s) based on SRSD Main Functions (SGI-MF)

### CLD Log Entry Template
```markdown
### Log XXX: <Title>
- **Significance:** [Major/Minor] | [Requirements/Design/Code]
- **Results:** Success | Failure | Approved Modification
- **Date:** YYYY-MM-DD HH:mm
- **Change Summary:** <one-line>
- **Detailed Changes:**
  - <bullet>
- **References:** SFR-IODE-01, etc.
- **Issue Tracking:** #123
- **Author:** <name>
```

---

## References

- [PDA-SDD Specification](../docs/PDA_SDD_SPEC.md)
- [Computers 2024, 13, 378](../docs/computers-14-00378-v3.pdf) — Original research paper
- [Change Log Document (CLD) README](../docs/2-during-implementation/CLD/README.md)
