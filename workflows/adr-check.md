---
description: Mine conversations and commits for missing ADR candidates
---

# ADR Check Workflow

Use this workflow mid-conversation or at any time to identify decisions that should be recorded as ADRs.

## When to Use

- ✅ After a complex feature implementation
- ✅ When you realize "we made a lot of decisions here"
- ✅ At the end of any conversation involving architectural work
- ✅ Before merging a feature branch to dev

## 1. Gather Context

### 1.1 Review conversation summary

If running mid-conversation, review what was discussed:
- What problems were we solving?
- What alternatives did we consider?
- What trade-offs did we make?

### 1.2 Check git diff (optional)

```bash
git diff dev --stat
```

Look for:
- New modules or directories
- New configuration files
- Changes to container.ts or moduleFactory.ts
- Schema changes

## 2. ADR Trigger Checklist

Check if ANY of these apply:

| Trigger | Examples |
|---------|----------|
| **New pattern introduced** | Rate limiting strategy, caching layer, error handling approach |
| **Technology choice** | New library, framework, or external service |
| **Architectural refactor** | Module split, layer changes, new bounded context |
| **Cross-cutting concern** | Auth changes, logging strategy, transaction boundaries |
| **Trade-off decision** | MVP shortcut with future debt, performance vs simplicity |
| **Integration choice** | API design, database schema, external service contract |

### NOT ADR-worthy (skip):
- Bug fixes within existing patterns
- CRUD additions following established patterns
- Dependency updates (unless forcing arch changes)
- Renames, moves, code cleanup

## 3. Evaluate Candidates

For each potential ADR, ask:

> "Would someone 6 months from now ask 'why did we do it this way?'"

If YES → Proceed to draft
If NO → Skip, it's implementation detail

## 4. Generate ADR Draft

For each candidate that passes evaluation:

1. Determine the next ADR number:
```bash
ls docs/adr/*.md | tail -1
```

2. Run `/adr-capture` with context:
   - Decision title
   - The problem it solved
   - Alternatives considered
   - Why this approach was chosen

## 5. Output

Present findings to user:

```markdown
## ADR Check Results

### Candidates Found: [N]

| # | Proposed Title | Trigger | Confidence |
|---|----------------|---------|------------|
| 1 | [Title] | [Which trigger] | High/Medium/Low |

### Recommended Action
- [ ] Draft ADR for #1: [brief reason]
- [ ] Skip #2: [why not ADR-worthy]

Shall I draft any of these?
```

## 6. If No Candidates

Report:
```markdown
## ADR Check Results

No ADR candidates found. Work appears to follow established patterns.
```
