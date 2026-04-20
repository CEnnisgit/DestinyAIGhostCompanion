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

// turbo
```bash
ls docs/adr/*.md | tail -1
```

Next number = last number + 1 (use 4-digit format: 0004, 0005, etc.)

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
2. Update `docs/adr/README.md` index table
3. Commit with message: `docs: add ADR-XXXX [title]`

## Quick Capture Mode

For rapid ADR creation when context is clear, skip questions and generate directly from:
- Recent git commits
- Conversation summary
- User-provided one-liner

Example:
```
/adr-capture "Chose rate limiting with sliding window instead of fixed window for better burst handling"
```
