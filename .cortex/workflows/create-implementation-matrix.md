---
description: Create a comprehensive implementation matrix for a sub-phase
---

# Create Implementation Matrix

Use this workflow to scaffold a `PHASE3{X}_IMPLEMENTATION_MATRIX.md` for a new sub-phase.
The matrix is the comprehensive study guide + checklist that drives implementation.

> **When:** After the phase-level research and spec design are complete.
> The matrix reads FROM existing specs and roadmaps — it does not create them.

---

## Step 1: Gather Inputs

Before creating the matrix, read:

1. **Sub-phase roadmap:** `docs/roadmap/PHASE_3{X}_*.md`
   — What entities/features are in scope? What order?

2. **DDD specs** for each entity in scope:
   `docs/2-during-implementation/DDD/ModuleDesign/{Module}/{Entity}_Aggregate.md`
   — What fields, invariants, and repository methods exist?

3. **Relevant ADRs** from `docs/adr/README.md`
   — Which architectural decisions govern this sub-phase?

4. **Prior research** if it exists (brain directory or phase3 directory)
   — Resolved design questions? Dependencies on prior sub-phases?

5. **Prior sub-phase matrix** to understand exit state and carryover.

## Step 2: Create the File

File: `docs/roadmap/phase3/PHASE3{X}_IMPLEMENTATION_MATRIX.md`

Use the Phase 3A matrix as the reference pattern. The structure below mirrors it.

### 2.1 Header

```markdown
# Phase 3{X} Implementation Matrix — {Sub-Phase Name}

> Comprehensive map of specs, prerequisite reading, and current status.
> Use this as the study guide + checklist for implementation.
>
> **Updated:** {date} — {brief status summary}
```

### 2.2 Legend

```markdown
## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete (spec or implementation) |
| 📋 | Spec exists, not yet implemented |
| 🔲 | Not started |
| ⚠️ | Partially done / has issues |
| 🔗 | Cross-referenced (spec exists in another phase but relevant here) |
```

### 2.3 Sub-Phase Section

```markdown
### Phase 3{X}: {Name}

> **Branch:** `phase3{x}/{branch-name}`
> **Status:** 🔲 Not Started
> **Depends On:** Phase 3{prev} ✅ Complete ({why})
```

### 2.4 Exit Criteria

The most important section. Concrete, session-granular acceptance criteria:

```markdown
#### Exit Criteria — Session 1

| Criterion | Status | Notes |
|-----------|:------:|-------|
| {Specific testable outcome} | 🔲 | {where it will live / how to verify} |
| {Another outcome} | 🔲 | |

#### Exit Criteria — Session 2

| Criterion | Status | Notes |
|-----------|:------:|-------|
| {Specific testable outcome} | 🔲 | |
```

Exit criteria are **concrete and verifiable** — not vague goals. Each row should
describe something you can grep for, test, or inspect. Include the Notes column
to capture WHERE the implementation lives after it's done.

When a session is complete, update each row with a status and note:
```markdown
| `users` table has `password_hash` column | ✅ | Bootstrap in `iam::ensure_iam_tables` |
```

### 2.5 DB Integration Tests (when applicable)

```markdown
#### DB Integration Tests

| Test File | Tests | Status |
|-----------|------:|:------:|
| {entity}_repo | 0 | 🔲 |

#### Test Totals: {X} domain + {Y} DB integration = {total}
```

Track test counts as they grow during implementation.

### 2.6 Specs Table

Link every DDD spec that governs this sub-phase:

```markdown
#### Specs (DDD Module Design)

| Spec | Path | Type | Status |
|------|------|------|--------|
| {Entity} Aggregate | [{filename}](file:///path) | Aggregate | 📋 |
| {VO} | [{filename}](file:///path) | Value Object | 📋 |
| Module README | [{Module}/README.md](file:///path) | Module index | 📋 |
```

Use absolute `file:///` links so specs are clickable from the editor.

### 2.7 Architecture Reference

Link the structural and governance docs:

```markdown
#### Architecture Reference

| Document | Path | Why |
|----------|------|-----|
| Module Structure | [ModuleStructure.md](file:///path) | File placement map |
| Test Strategy | [TEST_STRATEGY.md](file:///path) | Testing patterns |
| {Relevant doc} | [{filename}](file:///path) | {why it matters} |
```

### 2.8 Prerequisites — Study Before Implementing

Prioritized reading list — what the agent MUST read before writing code:

```markdown
#### Prerequisites — Study Before Implementing

| Priority | Document | Why | Read? |
|----------|----------|-----|-------|
| 🔴 MUST | [ADR-XXXX: Title](file:///path) | {why this ADR matters} | 🔲 |
| 🔴 MUST | [{SpecName}](file:///path) | {what it governs} | 🔲 |
| 🟡 SHOULD | [{DocName}](file:///path) | {context it provides} | 🔲 |
| 🟢 NICE | [{DocName}](file:///path) | {supplementary info} | 🔲 |
```

This is the study guide. An agent running `/onboard` → `/start-subphase` should
read every 🔴 item before touching code.

### 2.9 ADR Index

```markdown
## ADR Index (Phase 3{X} relevant)

| ADR | Title | Phase(s) | Status |
|-----|-------|----------|--------|
| XXXX | {Title} | 3{X} | ✅ Accepted |
```

### 2.10 Changelog

```markdown
## Changelog

| Date | Change |
|------|--------|
| {date} | Initial matrix created |
```

Update this every time the matrix changes meaningfully.

## Step 3: Review

Present the completed matrix to the user. Key review points:

1. Are the exit criteria specific and verifiable?
2. Is the prerequisite reading list complete?
3. Are all spec links correct and clickable?
4. Does the scope match the roadmap?

---

## Maintenance During Implementation

As work proceeds:

- Update exit criteria: `🔲` → `✅` with notes explaining where it lives
- Update prerequisite reading: `🔲` → `✅` as docs are consumed
- Update spec statuses: `📋` → `✅ Implemented + spec updated`
- Update test counts after each test session
- Add changelog entries for significant updates
- Mark completion in the header when done:
  ```
  > **Updated:** {date} — Phase 3{X} fully complete. {summary}.
  ```
