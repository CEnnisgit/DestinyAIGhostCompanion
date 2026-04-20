---
description: Scaffold and execute a new sub-phase (3A, 3B, 3C, etc.) with the 4-artifact lifecycle
---

# Phase 3 Sub-Phase Workflow

This workflow orchestrates the full lifecycle of a sub-phase.
Each stage delegates to a dedicated workflow for artifact creation.

> **Prerequisite:** Run `/onboard` first if this is a fresh conversation.
> The agent must understand PCD's domain, architecture, and current roadmap
> position before starting a new sub-phase.

## Naming Convention

All artifacts use the pattern: `PHASE3{X}_{ARTIFACT_TYPE}.md`

Example for Phase 3B:
- `PHASE3B_IMPLEMENTATION_MATRIX.md`
- `PHASE3B_SESSION_JOURNAL.md`
- `PHASE3B_SPEC_AUDIT.md`
- `PHASE3B_TRACEABILITY_MATRIX.md`

---

## Stage 1: Pre-Implementation (Scope & Matrix)

**Goal:** Understand what this sub-phase covers and build the implementation plan.

Research and spec design are already complete by this point — they happen during
the pre-implementation phase (PRD/SRSD). This stage reads existing artifacts
to build the matrix.

1. Read the sub-phase roadmap file in `docs/roadmap/PHASE_3{X}_*.md`.
   - Understand the scope: what entities and features are in this sub-phase.
   - Verify it reflects current ADRs and architectural decisions.

2. Read the DDD specs for each entity in scope:
   `docs/2-during-implementation/DDD/ModuleDesign/{Module}/{Entity}_Aggregate.md`
   - Specs should already exist. If they don't, stop and flag to the user —
     spec design is a pre-implementation activity, not a sub-phase activity.

3. Check for prior research artifacts (brain directory or `docs/roadmap/phase3/`).
   - Earlier sub-phases often produce research docs for future phases.

4. **Run `/create-implementation-matrix`** to build the matrix for this sub-phase.

5. Present the matrix to the user for confirmation before proceeding.

---

## Stage 2: During Implementation

**Goal:** Build each entity/feature, tracking progress and commits.

### 2a. Create the Session Journal (one-time per sub-phase)

Create `docs/roadmap/phase3/PHASE3{X}_SESSION_JOURNAL.md`:

```markdown
# Phase 3{X} Session Journal — {Sub-Phase Name}

> **Branch:** `phase3{x}/{branch-name}` | **Conversation:** `{conversation-id}`

## Session 1 — IN PROGRESS 🔨

### Commits

| SHA | Message |
|-----|---------|

### Summary

- {Goals for this session}
```

### 2b. Create today's Daily Journal (one-time per day)

Create `docs/journal/YYYY-MM-DD.md`:

```markdown
# {date} — {Title: what's being worked on today}

## Context

{1-2 sentences: where we left off, what the goal is today}

## Plan for Today

{Concise list of intended work — ordered by priority}

## What Got Done

*(filled during work)*

## Commits Today

| Hash | Description |
|------|-------------|

## Branch

`{branch}` — {test status}

## Alpha Critical Path Status

\`\`\`text
3A: Identity Foundation    → {status}
3B: Authentication         → {status}
3C.1: Authorization Core   → {status}
\`\`\`

## Open Questions (Carry Forward)

{Any unresolved questions from prior sessions}
```

### 2c. Implement

1. **Follow `/maintain-subphase`** for the ongoing session cadence
   (logging commits, updating matrix, syncing journals, session wrap-up).

2. Work through the Implementation Matrix entity by entity.

3. **Follow the correct stack sequence:**
   **If Backend Sub-Phase:**
   - Domain first (pure logic, no dependencies).
   - DB second (repository implementations against real Postgres).
   - API third (route handlers that wire domain + DB).
   - Tests last (verify each layer's contract).
   
   **If Frontend Sub-Phase:**
   - Route/Layout first (navigation skeleton).
   - React Components second (stateless UI views).
   - Hooks/State third (wiring local state).
   - API Consumption last (connecting frontend to OpenAPI definitions).

4. **Build policy:** Never auto-run `cargo build -p pcd-api` — it's resource-intensive (~30s). Ask the user.
5. **Test policy:** Always use `--test-threads=1` for DB integration tests.

---

## Stage 3: Post-Implementation (Verification)

**Goal:** Prove that every spec field exists in code and every code path traces back to a spec.

1. **Run `/create-spec-audit`** to build the spec audit for this sub-phase.

2. **Run `/create-traceability-matrix`** to build the traceability matrix.

3. Fix all findings from the Spec Audit:
   - Code fixes get their own commits.
   - Doc fixes get their own commits.
   - Update the audit to mark items as resolved.

4. **Gate:** The sub-phase is complete when:
   - All entities in the Implementation Matrix show ✅ across all columns.
   - The Spec Audit shows all findings resolved (or explicitly deferred with rationale).
   - The Traceability Matrix has no empty cells.

---

## Stage 4: Wrap-Up

1. Add the **Close-Out** and **Lessons Learned** sections to the session journal
   (see `/maintain-subphase` for the close-out template).

2. Update the `ARCHIVED_RESEARCH_INDEX.md` with any research docs that were consumed.

3. Update project-wide artifacts if they exist:
   - `TESTING_MATRIX.md` — add new entities, update coverage counts.
   - `TEST_STRATEGY.md` — only if new testing patterns were established.

4. Check if any ADRs written during this sub-phase should update `EVOLUTION.md`.

5. Final commit with all doc changes.

6. Record final status in the Implementation Matrix header:
   ```
   > **Status:** ✅ Complete — {date}
   ```

---

## Artifact Summary

| Artifact | Created In | Maintained By | Purpose |
|----------|-----------|---------------|---------|
| **Implementation Matrix** | Stage 1 | `/maintain-subphase` | Task tracker — what to build, what's done |
| **Session Journal** | Stage 2a | `/maintain-subphase` | Commit log — what happened each session |
| **Daily Journal** | Stage 2b | `/maintain-subphase` | Narrative + planning — the story of each day |
| **Spec Audit** | Stage 3 | `/create-spec-audit` | Compliance check — code vs spec |
| **Traceability Matrix** | Stage 3 | `/create-traceability-matrix` | Proof of completeness — end-to-end wiring |
