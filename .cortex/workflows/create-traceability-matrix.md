---
description: Create an end-to-end traceability matrix for a completed sub-phase
---

# Create Traceability Matrix

Use this workflow to create a `PHASE3{X}_TRACEABILITY_MATRIX.md` after implementation.
The matrix proves every entity has complete vertical wiring from spec to API.

> **When:** Post-implementation, alongside or after the spec audit.
> If the spec audit finds gaps, fix them before finalizing the traceability matrix.

---

## Step 1: Gather Inputs

For each entity, you need to locate the file at every layer:

| Layer | Where to look |
|-------|--------------|
| Spec | `docs/2-during-implementation/DDD/ModuleDesign/{Module}/` |
| Domain Struct | `crates/pcd-domain/src/{module}/{entity}/mod.rs` |
| Error Type | Same file or `errors.rs` |
| Params Struct | Same file (e.g., `UpdateEntityProfile`) |
| Unit Tests | Inline `#[cfg(test)]` or `tests.rs` in same directory |
| Repo Trait | `crates/pcd-domain/src/{module}/{entity}/repository.rs` |
| SQLx Impl | `crates/pcd-db/src/{module}/{entity}.rs` |
| DB Tests | `crates/pcd-db/tests/{entity}_repo.rs` |
| DB Table | Bootstrap SQL in `crates/pcd-db/src/{module}/mod.rs` or `bootstrap.rs` |
| API Route | `crates/pcd-api/src/routes/{entity}.rs` |

## Step 2: Create the File

File: `docs/roadmap/phase3/PHASE3{X}_TRACEABILITY_MATRIX.md`

### 2.1 Header

```markdown
# Phase 3{X} End-to-End Traceability Matrix

> Shows the full vertical slice for every entity: **Spec → Domain → Repo Trait → SQLx Impl → DB Table → API Route**
>
> **Status:** 🔨 In Progress — {date}
```

### 2.2 Per-Entity Trace Table

For each entity, create a layer-by-layer table.
The rows vary by entity type — use what applies.

#### Full Aggregate (e.g., User, Company, LmpCredential)

```markdown
### {Entity}

| Layer | File | Status |
|-------|------|--------|
| **Spec** | `docs/.../{Entity}_Aggregate.md` | ✅ |
| **Domain Struct** | `pcd-domain/src/{module}/{entity}/mod.rs` → `{Entity}` | ✅ |
| **Error Type** | `pcd-domain/src/{module}/{entity}/mod.rs` → `{Entity}Error` | ✅ |
| **Params Struct** | `pcd-domain/src/{module}/{entity}/mod.rs` → `Update{Entity}` | ✅ |
| **Unit Tests** | `pcd-domain/src/{module}/{entity}/tests.rs` | ✅ {N} tests |
| **Repo Trait** | `pcd-domain/src/{module}/{entity}/repository.rs` → `{Entity}Repository` | ✅ |
| **SQLx Impl** | `pcd-db/src/{module}/{entity}.rs` → `Sqlx{Entity}Repository` | ✅ |
| **DB Tests** | `pcd-db/tests/{entity}_repo.rs` | ✅ {N} tests |
| **DB Table** | `pcd-db/src/{module}/mod.rs` → `CREATE TABLE {entities}` | ✅ |
| **API Route** | `pcd-api/src/routes/{entity}.rs` | ✅ |
```

Follow this with the API route listing:

````markdown
```
API: GET   /api/{entities}          → list_all()
     GET   /api/{entities}/:id      → find_by_id()
     PATCH /api/{entities}/:id      → update()
```
````

#### Value Object (e.g., Email, DisplayName)

VOs don't have their own tables or routes — they're embedded:

```markdown
### {VO} (Value Object)

| Layer | File | Status |
|-------|------|--------|
| **Spec** | `docs/.../{VO}_Spec.md` | ✅ |
| **Domain Struct** | `pcd-domain/src/{module}/{parent}/{vo}.rs` → `{VO}` | ✅ |
| **Unit Tests** | `pcd-domain/src/{module}/{parent}/{vo}.rs` → inline | ✅ {N} tests |
| **Repo Trait** | — | — (VO, no persistence of its own) |
| **SQLx** | — | — (serialized as TEXT column on `{parent}` table) |
| **DB Column** | `{parent_table}.{column} TEXT NOT NULL` + CHECK constraints | ✅ |
| **API** | — | — (embedded in {Parent} responses) |
```

Use `—` with an explanation for layers that don't apply.

#### Junction / Infrastructure Entity (e.g., CompanyMembership)

May have no API routes if it's consumed internally:

```markdown
### {Entity}

| Layer | File | Status |
|-------|------|--------|
| **Spec** | `docs/.../{Entity}.md` | ✅ |
| **Domain Struct** | `pcd-domain/src/...` → `{Entity}` | ✅ |
| **Enum** | `pcd-domain/src/...` → `{Role}` | ✅ |
| **Unit Tests** | inline | ✅ {N} tests |
| **Repo Trait** | `pcd-domain/src/...` → `{Entity}Repository` | ✅ |
| **SQLx Impl** | `pcd-db/src/...` → `Sqlx{Entity}Repository` | ✅ |
| **DB Tests** | `pcd-db/tests/...` | ✅ {N} tests |
| **DB Table** | bootstrap SQL | ✅ |
| **API Route** | — | — ({reason why no API}) |

> **Note:** {explain the entity's role, e.g., consumed by middleware not CRUD}
```

### 2.3 Pre-Existing Entities (if migrated during this sub-phase)

If this sub-phase touched entities from earlier phases, include them in a
separate section:

```markdown
## {N}. {Module} Entities (Pre-3{X}, verified during 3{X} migration)

These entities had full end-to-end wiring before Phase 3{X}.
During 3{X}, their schema was migrated from {old} to {new}.
```

Use a condensed trace table for these (no need for the full treatment).

### 2.4 Test Coverage Summary

Aggregate all test counts across all entities:

```markdown
## Test Coverage Summary

| Entity | Domain Tests | DB Tests | API Tests |
|--------|:-----------:|:--------:|:---------:|
| {Entity 1} | ✅ {N} | ✅ {N} | — |
| {Entity 2} | ✅ {N} | — | — |
| **Total** | **{N}** | **{N}** | **{N}** |

> **Note:** {explain any missing test columns — e.g., API tests deferred}
```

Run the actual test commands to get accurate counts:
- Domain: `cargo test -p pcd-domain -- --test-threads=1 2>&1 | Select-String "test result"`
- DB: `cargo test -p pcd-db -- --test-threads=1 2>&1 | Select-String "test result"`

### 2.5 Data Flow Traces

Pick 1–2 representative operations and trace the full request path
through the architecture. This proves the wiring actually works, not just
that files exist:

````markdown
## Data Flow Trace (Example: {Operation Name})

```
Frontend
  ↓  {HTTP Method} /api/{path}  { field: "value" }
  
pcd-api/routes/{entity}.rs
  ↓  Extract Path(id), Json({Request})
  ↓  state.{repo}.find_by_id(id)  ← calls repo trait
  
pcd-db/{module}/{entity}.rs (Sqlx{Entity}Repository)
  ↓  SELECT * FROM {table} WHERE id = $1
  ↓  Returns {Row} → {Entity}::reconstitute()
  
pcd-api/routes/{entity}.rs
  ↓  entity.{method}({params})  ← domain logic
  ↓  state.{repo}.update(&entity)  ← calls repo trait
  
pcd-db/{module}/{entity}.rs
  ↓  UPDATE {table} SET ... WHERE id=$1
  
pcd-api/routes/{entity}.rs
  ↓  Json({Response}::from(entity))  → {status code}
  
Frontend
```
````

Choose operations that exercise the full stack: create (POST), read-modify-write
(PATCH), and any domain-heavy flows (e.g., state transitions).

## Step 3: Verify Completeness

Every entity should have a layer table. Check for gaps:

- **Empty cells** mean something is missing — either the wiring doesn't exist
  (bug) or the layer doesn't apply (use `—` with explanation)
- **Missing entities** mean the matrix doesn't cover all sub-phase scope
- **Missing data flow traces** mean the wiring is asserted but not demonstrated

## Step 4: Finalize

When all entities are traced:

1. Update header status to `✅ Complete — {date}`
2. Verify test counts match reality (run the tests)
3. Commit the finalized matrix
