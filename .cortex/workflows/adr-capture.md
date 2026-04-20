---
description: Generate a draft ADR from conversation or commit context
---

# ADR Capture Workflow

Use this workflow to generate a draft ADR for a specific architectural decision.

## Prerequisites

- Clear understanding of the decision to document
- Context: conversation history, git diff, or verbal description

## 1. Gather Decision Context

Ask/determine:
- **What was decided?** (the actual choice made)
- **What problem did it solve?** (context/motivation)
- **What alternatives were considered?** (rejected options)
- **What are the trade-offs?** (pros and cons)

## 2. Determine ADR Number

Check `docs/adr/README.md` — the **Next ADR** line at the bottom has the next number.

## 3. Generate Draft

Create file at `docs/adr/XXXX-title-slug.md` using this template:

```markdown
# ADR-XXXX: [Decision Title]

**Status:** Proposed
**Date:** [Today's date]
**Deciders:** Development Team

## Context

[What is the issue that motivated this decision?]
[Background, constraints, requirements]

## Decision

[What change are we making?]
[Key patterns or approaches chosen]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Trade-off 1]
- [Trade-off 2]

## Alternatives Considered

### [Alternative 1 Name]

**Rejected because:** [Reason]

### [Alternative 2 Name]

**Rejected because:** [Reason]
```

## 4. Request Review

Present draft to user with:

```markdown
## Draft ADR Ready for Review

**File:** `docs/adr/XXXX-title.md`
**Status:** Proposed (awaiting approval)

### Summary
[1-2 sentence summary of what the ADR captures]

### Review Questions
1. Does this accurately capture the decision?
2. Are there alternatives I missed?
3. Should the status be "Accepted" or stay "Proposed"?
```

## 5. Finalize

After user approval:
1. Update status to "Accepted" if approved
2. Commit the ADR file: `docs: add ADR-XXXX [title]`

## 6. Update README Index

After the ADR is committed:

1. Add a row to the **chronological index** table in `docs/adr/README.md`
2. Add a row to the appropriate **module section** (iam, operations, workflows, directory, global)
3. If the ADR affects multiple modules, add it to each relevant section
4. Increment the **Next ADR** number at the bottom of the file
5. Commit separately: `docs(adr): update README index for ADR-XXXX`


> **Note:** `docs/adr/EVOLUTION.md` tracks how ADRs evolve over time across
> architectural arcs. It is updated at phase boundaries (via `/finish-subphase`),
> not per-ADR. If this ADR is clearly part of an arc, you may update EVOLUTION.md
> now — but it's not required as part of capture.

## Quick Capture Mode

For rapid ADR creation when context is clear, skip questions and generate directly from:
- Recent git commits
- Conversation summary
- User-provided one-liner

Example:
```
/adr-capture "Chose rate limiting with sliding window instead of fixed window for better burst handling"
```

Quick capture still requires step 6 (README index update).
