---
description: Maintain sub-phase artifacts during an active work session (journal, matrix, audits)
---

# Maintain Sub-Phase Workflow

Run this during each work session to keep journals and the matrix in sync.
This workflow handles the **recurring cadence** — logging, tracking, syncing.

> **Prerequisite:** The sub-phase must already be scaffolded via `/start-subphase`.
> The session journal, daily journal, and implementation matrix must already exist.

---

## At Session Start

### 1. New Day? Create Today's Daily Journal

If `docs/journal/YYYY-MM-DD.md` doesn't exist yet, create it using the template
from `/start-subphase` Stage 2b.

### 2. New Session? Add a Session Block

If this is a new session (new conversation, or returning after a break),
add a new block to the existing `PHASE3{X}_SESSION_JOURNAL.md`:

```markdown
## Session N — IN PROGRESS 🔨

### Commits

| SHA | Message |
|-----|---------|

### Summary

- {Goals for this session}
```

### 3. Review Implementation Matrix

Open `docs/roadmap/phase3/PHASE3{X}_IMPLEMENTATION_MATRIX.md` and:

1. Identify the next entity/feature to work on.
2. Mark it as `🔨 In Progress`.
3. Confirm no blockers from previous sessions.

---

## During Session

### 4. Log Commits (Both Places)

After each commit, add it to BOTH:

**Session Journal:**
```markdown
| `abc1234` | feat(domain): add Session aggregate |
```

**Daily Journal** (Commits Today table):
```markdown
| `abc1234` | feat(domain): add Session aggregate |
```

Keep both up-to-date — don't batch at the end.
If you forget, run `git log --oneline -5` to recover.

### 5. Update Matrix on Completion

When you finish a layer for an entity (domain, db, api, or tests), update the matrix cell:

- `🔲` → `🔨` when starting
- `🔨` → `✅` when done and committed
- `🔨` → `⚠️` if blocked (add a note in the matrix)

### 6. Log Narrative in Daily Journal

As meaningful work completes, fill in the "What Got Done" section. Include:
- Tables for step-by-step progress
- Decisions made and why
- Problems solved
- Discoveries

The daily journal tells the STORY; the session journal just records the FACTS.

### 7. Commit Code and Docs Separately

This is a hard rule:

- Code changes → code commit
- Doc/spec changes → doc commit

Never mix them. The Session Journal and Matrix updates count as doc changes.

---

## At Session End

### 8. Finalize Session Journal Entry

Add session summary capturing:

- What was accomplished
- Any decisions made (reference ADR if significant)
- Any deferred items or blockers for next session
- Any spec drift discovered (queue for Stage 3 audit)
- Test count changes (e.g., "184 domain + 19 DB = 203 total ✅")

Mark session status: `— COMPLETE ✅` or `— PAUSED ⏸️`

### 9. Finalize Daily Journal

Update remaining sections:

- **Branch**: current branch + working tree state
- **Critical Path Status**: update the text diagram
- **Open Questions**: add any new carry-forward items

### 10. Snapshot Matrix Status

Verify the Implementation Matrix reflects current state:

- Count how many cells are ✅ vs 🔲.
- Update the header status if a milestone was reached.

### 11. Update Spec Audit

Open `docs/roadmap/phase3/{sub-phase}/SPEC_AUDIT.md` and:

1. Add a new section for any NEW code/specs touched this session.
2. For each new component, do a line-by-line spec ↔ code comparison.
3. Log any drift findings as ⚠️ with description.
4. Update the Resolution Summary and Final Scorecard if needed.
5. Update the header date and scope line.

> Drift is easiest to catch while the work is fresh. Don't defer this to close-out.

### 12. Update Traceability Matrix

Open `docs/roadmap/phase3/{sub-phase}/TRACEABILITY_MATRIX.md` and:

1. Add vertical-slice entries for any NEW components built this session.
2. Update file paths and line numbers if files were reorganized.
3. Update the Test Coverage Summary table with current counts.
4. Update the header date.

### 13. Queue Remaining Audit Notes (if any)

If you noticed drift that you couldn't fully audit in Steps 11–12, note it:

```markdown
> **Audit note:** {Entity} §{Section} may need update — {description}
```

These get resolved systematically in Stage 3 (post-implementation verification).

### 14. Commit Tracking Updates

```
git add docs/roadmap/phase3/{sub-phase}/SESSION_JOURNAL.md docs/roadmap/phase3/{sub-phase}/IMPLEMENTATION_MATRIX.md docs/roadmap/phase3/{sub-phase}/SPEC_AUDIT.md docs/roadmap/phase3/{sub-phase}/TRACEABILITY_MATRIX.md docs/journal/YYYY-MM-DD.md
git commit -m "docs: update Phase 3{X} session journal, matrix, audits, and daily journal"
```

---

## Sub-Phase Close-Out

When the sub-phase finishes (after Stage 3 verification), add a close-out entry
to the session journal:

```markdown
## Close-Out — {date}

> **Conversation:** `{conversation-id}`

### Summary

- **Spec Audit:** {N} findings, {N} resolved, {N} deferred
- **Traceability Matrix:** {N} entities traced end-to-end
- **Testing Matrix:** Updated to reflect {new counts}

### Final Gate Check

- [x] Implementation Matrix: All targeted cells ✅
- [x] Spec Audit: All findings resolved or accepted
- [x] Traceability Matrix: No empty cells
- [x] Session Journal: All sessions documented with commit SHAs
- [x] Specs updated: All affected specs show correct status

**Phase 3{X}: ✅ CLOSED**
```

End with lessons learned:

```markdown
## Lessons Learned

- {Gotcha that cost time}
- {Pattern that worked well}
- {Policy to carry forward}
```

---

## Session Journal vs Daily Journal

| Aspect | Session Journal | Daily Journal |
|--------|----------------|---------------|
| **Scope** | One sub-phase (may span days) | One day (may touch multiple sub-phases) |
| **File** | `PHASE3{X}_SESSION_JOURNAL.md` | `docs/journal/YYYY-MM-DD.md` |
| **Commits** | ✅ All commits for this sub-phase | ✅ All commits for this day |
| **Narrative** | Brief summary | Rich context + decisions + story |
| **Plans** | No | Yes ("Plan for Today") |
| **Close-out** | Yes (gate check + lessons) | No |

Both share commit data. Daily journal has the richer narrative and planning.
Session journal has the close-out and sub-phase lifecycle tracking.

---

## Quick Reference

| When | What | Files |
|------|------|-------|
| New day | Create daily journal (if needed) | `journal/YYYY-MM-DD.md` |
| New session | Add session block | `SESSION_JOURNAL.md` |
| Session start | Pick next task | `IMPLEMENTATION_MATRIX.md` |
| After each commit | Log SHA + message | `SESSION_JOURNAL.md`, `journal/YYYY-MM-DD.md` |
| After each layer done | Update cell | `IMPLEMENTATION_MATRIX.md` |
| During work | Log narrative | `journal/YYYY-MM-DD.md` |
| Session end | Add summary + decisions | `SESSION_JOURNAL.md` |
| Session end | Audit new specs/code for drift | `SPEC_AUDIT.md` |
| Session end | Add vertical slices for new components | `TRACEABILITY_MATRIX.md` |
| Day end | Update branch, critical path, open questions | `journal/YYYY-MM-DD.md` |
| Day/session end | Commit tracking docs | All 5 doc files |
