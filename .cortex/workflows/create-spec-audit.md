---
description: Create a spec-vs-code audit for a completed sub-phase
---

# Create Spec Audit

Use this workflow to create a `PHASE3{X}_SPEC_AUDIT.md` after implementation is complete.
The audit proves field-level compliance between DDD specs and actual code.

> **When:** Post-implementation — all entities in the implementation matrix show ✅.
> This is a verification artifact, not a planning artifact.

---

## Step 1: Gather Inputs

For each entity in the sub-phase, you need:

1. **DDD spec:** `docs/2-during-implementation/DDD/ModuleDesign/{Module}/{Entity}_Aggregate.md`
2. **Domain code:** `crates/pcd-domain/src/{module}/{entity}/mod.rs`
3. **Repository trait:** `crates/pcd-domain/src/{module}/{entity}/repository.rs`
4. **Repository impl:** `crates/pcd-db/src/{module}/{entity}.rs`
5. **Bootstrap SQL:** `crates/pcd-db/src/bootstrap.rs` (or module-level bootstrap)
6. **API routes:** `crates/pcd-api/src/routes/{entity}.rs`

Read each spec and its corresponding code files side-by-side.

## Step 2: Create the File

File: `docs/roadmap/phase3/PHASE3{X}_SPEC_AUDIT.md`

### 2.1 Header

```markdown
# Phase 3{X} Spec-vs-Code Deep Audit

> **Date:** {date} | **Scope:** All {N} Phase 3{X} entities
> **Method:** Line-by-line spec ↔ code comparison across 5 dimensions
> **Status:** 🔨 IN PROGRESS
```

### 2.2 Legend

```markdown
## Audit Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Perfect match — code aligns with spec |
| ⚠️ | Drift — spec and code disagree (needs fix) |
| 📋 | Spec gap — code does something the spec doesn't mention |
| 🔲 | Missing — spec states something that doesn't exist in code |
```

### 2.3 Per-Entity Audit

For each entity, audit across these dimensions. Not every entity type uses
every dimension — use what applies.

#### Dimension 1: Fields/Types

Compare every field in the spec to the code struct:

```markdown
### {N}.1 Fields/Types

| Spec Field | Spec Type | Code Field | Code Type | Match |
|------------|-----------|------------|-----------|:-----:|
| `id` | UUID | `id` | `Uuid` | ✅ |
| `name` | DisplayName (VO) | `name` | `DisplayName` | ✅ |
```

Every spec field must appear in code. Every code field should appear in spec.
Extra code fields get `📋`. Missing code fields get `🔲`.

#### Dimension 2: Invariants

Compare spec-stated rules to code enforcement AND database constraints:

```markdown
### {N}.2 Invariants

| # | Invariant | Spec Says | Code Enforces | Match |
|---|-----------|-----------|---------------|:-----:|
| 1 | name must be valid | Domain (VO) + DB (CHECK) | `DisplayName::new()` + CHECK | ✅ |
```

Check both layers — invariants should be enforced in domain code AND
echoed as CHECK constraints in bootstrap SQL where applicable.

#### Dimension 3: Aggregate Behavior

Compare spec method signatures to actual code:

```markdown
### {N}.3 Aggregate Behavior

| Spec Method | Spec Signature | Code Signature | Match |
|-------------|---------------|----------------|:-----:|
| Creation | `Entity::new(a, b) → Self` | `Entity::new(a, b) → Self` | ✅ |
```

For Value Objects, this may be just `new()` + normalization rules.

#### Dimension 4: Errors

Compare spec error variants to code error enum:

```markdown
### {N}.4 Errors

| Spec Error | Code Error | Match |
|------------|------------|:-----:|
| `AlreadyActive` | `EntityError::AlreadyActive` | ✅ |
```

#### Dimension 5: Repository Contract

Compare spec-defined queries to repo trait methods:

```markdown
### {N}.5 Repository Contract

| Spec Query | Repo Trait Method | Match |
|------------|-------------------|:-----:|
| Find by ID | `find_by_id(Uuid)` | ✅ |
```

If the spec doesn't define a repository contract section, mark all methods
as `📋` with a note that the spec has a gap (code is correct, spec is incomplete).

#### Dimension 6: Persistence

Compare spec SQL to actual bootstrap SQL:

```markdown
### {N}.6 Persistence (Bootstrap SQL vs Spec SQL)

| Spec SQL Element | Bootstrap SQL | Match |
|------------------|---------------|:-----:|
| `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` | ✅ Present | ✅ |
| `chk_entity_name_not_empty` | ✅ Present | ✅ |
```

Check: columns, types, defaults, constraints, indexes, foreign keys.

#### Entity Verdict

End each entity section with a clear verdict:

```markdown
**{Entity} Verdict: ✅ PASS**
```

Or if issues remain:

```markdown
**{Entity} Verdict: ⚠️ {N} findings — see resolution summary**
```

#### Supplementary Dimensions (Entity-Dependent)

Not every entity needs the same dimensions. Adapt:

- **Value Objects:** Fields/Types + Invariants + Normalization + Errors + Serialization
- **Aggregates:** All 6 dimensions
- **Junction Entities:** Fields/Types + Persistence + code extras
- **Services:** Behavior + Dependencies + Error handling

Use what makes sense. The 3A audit used different table shapes for
User (full aggregate) vs Email (VO) vs CompanyMembership (junction).

### 2.4 Resolution Summary

After all entities are audited, create two summary sections:

```markdown
## Resolution Summary

All {N} findings from the initial audit have been resolved:

| # | Entity | Finding | Resolution | Commit |
|---|--------|---------|------------|--------|
| 1 | {Entity} | {what was wrong} | ✅ {how it was fixed} | `{sha}` |
| 2 | {Entity} | {spec gap} | 📋 Deferred — {rationale} | — |
```

Track every finding, even deferred ones. Deferred items should have a rationale.

```markdown
### Final Scorecard

| Entity | Verdict |
|--------|---------|
| {Entity 1} | ✅ PASS |
| {Entity 2} | ✅ PASS |

**Phase 3{X} Deep Audit: ✅ COMPLETE — All entities fully compliant.**
```

## Step 3: Fix Findings

The audit will almost certainly find issues. The fix process:

1. **Code fixes** — commit with `fix(domain):` or `fix(db):` prefix
2. **Spec fixes** — commit with `docs(spec):` prefix
3. **Code and spec changes get separate commits**
4. After each fix, update the audit: change `⚠️` → `✅` and fill in the commit SHA

## Step 4: Finalize

When all findings are resolved (or explicitly deferred with rationale):

1. Update the header status: `🔨 IN PROGRESS` → `✅ ALL FINDINGS RESOLVED`
2. Complete the Final Scorecard
3. Commit the finalized audit

---

## Common Findings

Based on Phase 3A, these are the most frequent finding types:

| Type | Example | Typical Resolution |
|------|---------|--------------------|
| Factory signature drift | Spec shows old params, code has new ones | Update spec to match code |
| Spec status stale | Spec says "Draft", code is implemented | Update spec status |
| Missing CHECK constraints | Spec mentions constraint, bootstrap doesn't have it | Add constraint to bootstrap |
| Stale module references | Spec references old module name (e.g., "CRM") | Update spec |
| Undocumented code extras | Code has typed enums, spec says TEXT | Deferred or update spec |
| Missing repo contract | Spec doesn't define repository section | Deferred — note the gap |
