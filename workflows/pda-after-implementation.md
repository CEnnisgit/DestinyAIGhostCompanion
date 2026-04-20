---
description: Run the PDA-SDD After-Implementation phase (SUMD + EULA + Delivery)
---

# PDA After-Implementation Workflow

This workflow executes Section 6 of the PDA-SDD Runbook: packaging deliverables for deployment.

## Prerequisites

- During-Implementation phase complete (DDD reflects reality)
- `pnpm run pda:check` passes
- Code is feature-complete for release

## Steps

### 1. Freeze Shipped Scope

1. Update SRSD to match as-built functionality.
2. Update DDD to match as-built architecture.
3. Mark any deferred requirements as "Out of Scope" or "Future".

### 2. Build SUMD (Software User Manual Document)

1. Create `docs/3-after-implementation/SUMD/README.md`.
2. Structure with sections:
   - Introduction (product overview)
   - Installation/Setup
   - Basic Usage (common tasks)
   - Advanced Usage (power features)
   - Troubleshooting (common issues)
   - Glossary (terms)
   - Appendix (reference)

3. For each user type (Plumber, LMP):
   - Document key workflows with screenshots.
   - Include step-by-step instructions.

### 3. Build EULA (End-User License Agreement)

1. Create `docs/3-after-implementation/EULA.md`.
2. Include standard 9-section framework:
   - Grant of License
   - Ownership
   - Restrictions
   - Disclaimer of Warranty
   - Indemnity
   - Termination
   - Governing Law and Jurisdiction
   - Entire Agreement
   - Severability

3. Have legal review if needed.

### 4. Package Technical Deliverables

1. Verify updated SRSD is committed.
2. Verify updated DDD is committed.
3. Verify source code is tagged for release.
4. Create `docs/3-after-implementation/RELEASE_NOTES.md` with:
   - Version number
   - Features included
   - Known issues
   - Upgrade instructions (if applicable)

### 5. Optional Deliverables

- Quick Start Guide (1-page getting started)
- Updated CLD (complete change history)
- Compliance certificates (if applicable)

### 6. Final Verification

// turbo
1. Run `pnpm run pda:check` to verify structure.
2. Verify all Must requirements are marked Implemented.
3. Verify SUMD covers all user-facing features.

### 7. Notify User for Review

Request user review of:
- `docs/3-after-implementation/SUMD/README.md`
- `docs/3-after-implementation/EULA.md`
- `docs/3-after-implementation/RELEASE_NOTES.md`

## Exit Criteria

- SUMD covers all user-facing functionality.
- EULA is complete and reviewed.
- Release notes document this version.
- All docs are committed and versioned.
- Ready for deployment.
