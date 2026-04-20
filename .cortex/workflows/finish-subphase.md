---
description: Close out a sub-phase with spec audit, traceability proof, and artifact promotion
---

# Finish Sub-Phase Workflow

Run this when all entities in the Implementation Matrix are built (domain + db + api + tests).
This workflow shifts from **building** to **verifying** — proving that what was built matches
what was specified, and packaging the results for posterity.

**Prerequisite:** All Implementation Matrix cells should be ✅ or explicitly deferred with rationale.

---

## Step 1: Create the Spec Audit

Create `docs/roadmap/phase3/PHASE3{X}_SPEC_AUDIT.md`.

For **each entity/feature** in the sub-phase, audit its implementation across dimensions appropriate for its stack:

### Backend Dimensions (For API/Domain Sub-Phases)

#### Dimension 1: Fields/Types
Compare every field in the spec's attributes table against the domain struct:
```markdown
| Spec Field | Spec Type | Code Field | Code Type | Match |
|------------|-----------|------------|-----------|:-----:|
| `id`       | UUID      | `id`       | `Uuid`    | ✅    |
```

#### Dimension 2: Invariants
For each business rule in the spec, verify enforcement in **both** domain code and DB constraints:
```markdown
| # | Invariant | Domain Enforces | DB Enforces | Match |
|---|-----------|-----------------|-------------|:-----:|
| 1 | name non-empty | `new()` trims + checks | `CHECK length(trim(name)) > 0` | ✅ |
```

#### Dimension 3: Aggregate Behavior
Compare factory signatures, command methods, and error variants.

#### Dimension 4: Repository Contract
If the spec defines a repository section, verify trait methods exist.

#### Dimension 5: Persistence (Bootstrap SQL)
Compare the spec's persistence section against the actual bootstrap SQL in `pcd-db`.

### Frontend Dimensions (For Web/Mobile Sub-Phases)

#### Dimension 1: UI Requirements
Compare the rendered React components against the InterfaceDesign/UI_Specs.md.
```markdown
| Spec Screen | Spec Elements | React Component | Match |
|-------------|---------------|-----------------|:-----:|
| Job Queue   | Filter, Sort  | `JobQueue.tsx`  | ✅    |
```

#### Dimension 2: API Consumption
Verify that the frontend consumes the correct OpenAPI types without manually duplicating types.
```markdown
| API Endpoint | OpenAPI Type Used | Hook/Query File | Match |
|--------------|-------------------|-----------------|:-----:|
| `GET /jobs`  | `paths["/jobs"]`  | `useJobs.ts`    | ✅    |
```

#### Dimension 3: Workspace Isolation
Verify that the frontend feature strictly respects Workspace routing isolation bounds (e.g., pulling `workspaceId` from the route and passing it via headers/query parameters).

### Audit Legend

Use consistently across all entities:

| Symbol | Meaning |
|--------|---------|
| ✅ | Perfect match |
| ⚠️ | Drift — spec and code disagree (must fix) |
| 📋 | Spec gap — code does something spec doesn't mention (note, low priority) |
| 🔲 | Missing — spec says something that doesn't exist in code (must fix) |

### Summary Table

End the audit with a numbered findings table:

```markdown
| # | Feature | Category | Finding | Severity |
|---|---------|----------|---------|----------|
| 1 | User    | Spec drift | §6.1 factory sig missing param | Low |
| 7 | JobQueue| API Gap | Component uses `any` instead of OpenAPI type | **High** |
```

---

## Step 2: Fix All Findings

Work through the summary table by priority:

1. **High** findings first — code changes (e.g., missing DB constraints)
2. **Medium** findings — spec rewrites (e.g., stale persistence sections)
3. **Low** findings — spec tweaks (e.g., factory signature updates)
4. **Cosmetic** findings — status updates, metadata fixes

**Hard rules:**
- Code fixes get their own commit(s).
- Doc/spec fixes get their own commit(s).
- Never mix code and doc changes in the same commit.

After fixing, update the audit to mark each finding as resolved with the commit SHA.

---

## Step 3: Create the Traceability Matrix

Create `docs/roadmap/phase3/PHASE3{X}_TRACEABILITY_MATRIX.md`.

For each feature, trace the full implementation path depending on the stack:

**Backend Sub-Phases:**
```markdown
| Entity | Spec | Domain Struct | Domain File | Repo Trait | Repo Impl | DB Table | API Route | API File |
|--------|------|---------------|-------------|------------|-----------|----------|-----------|----------|
| User   | User_Aggregate.md | `User` | user.rs | `UserRepository` | user_repo.rs | `users` | `/api/users` | users.rs |
```

**Frontend Sub-Phases:**
```markdown
| Feature | UI Spec | Route / URL | Container Component | Hook / State File | API Consumed |
|---------|---------|-------------|---------------------|-------------------|--------------|
| JobQueue| JobQueue.md | `/ws/:id/jobs` | `pages/Jobs.tsx`| `useJobs.ts` | `GET /api/v1/jobs` |
```

**Every cell must be filled.** An empty cell means something is missing. Elements without a certain layer (e.g., local only state with no API consumed) should have "N/A" with rationale.

For entities with tests, add a test coverage column:

```markdown
| Entity/Feature | Unit Tests | Integration Tests | E2E Tests |
|----------------|:----------:|:-----------------:|:---------:|
| User / JobQueue| ✅ 8 tests | ✅ 5 tests        | 🔲 0 tests|
```

---

## Step 4: Update Project-Wide Artifacts

### Testing Matrix

Update `docs/roadmap/phase3/TESTING_MATRIX.md` (if it exists):
- Add any new entities from this sub-phase.
- Update test counts and coverage status.

### Archived Research Index

Update `docs/roadmap/phase3/ARCHIVED_RESEARCH_INDEX.md`:
- Add any research docs consumed during this sub-phase.
- Mark their carry-forward recommendation (Promote / Archive / Superseded).

### Test Strategy

Update `docs/roadmap/phase3/TEST_STRATEGY.md` only if new testing patterns were established
(e.g., "we discovered integration tests need `--test-threads=1`").

---

## Step 5: Final Gate Check

Before declaring the sub-phase complete, verify all gates pass:

- [ ] **Implementation Matrix:** All targeted cells show ✅ (or explicitly deferred with rationale)
- [ ] **Spec Audit:** All findings resolved or explicitly accepted as tech debt
- [ ] **Traceability Matrix:** No empty cells — every entity traces end-to-end
- [ ] **Session Journal:** All sessions documented with commit SHAs
- [ ] **Specs updated:** All affected specs show correct status and source-of-truth paths

---

## Step 6: Mark Complete

1. Update the Implementation Matrix header:

```markdown
> **Status:** ✅ Complete — YYYY-MM-DD
```

2. Add a final Session Journal entry:

```markdown
## Close-Out — YYYY-MM-DD

### Summary
- Spec Audit: {N} findings, all resolved
- Traceability Matrix: {N} entities, all traced end-to-end
- Commits: {list final audit/fix commits}
```

3. Commit all tracking doc updates:

```
git add docs/roadmap/phase3/
git commit -m "docs: close out Phase 3{X} — all gates passed"
```

---

## Checklist (Quick Version)

1. [ ] Create `PHASE3{X}_SPEC_AUDIT.md` — audit all entities across 5 dimensions
2. [ ] Fix all High/Medium findings — code commits separate from doc commits
3. [ ] Update audit with resolution status + commit SHAs
4. [ ] Create `PHASE3{X}_TRACEABILITY_MATRIX.md` — every entity traced end-to-end
5. [ ] Update Testing Matrix, Archived Research Index
6. [ ] Pass all 5 gate checks
7. [ ] Mark Implementation Matrix as complete
8. [ ] Final close-out commit
