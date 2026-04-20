---
description: Audit a crate's internal structure and conventions (ADR-0040 Rule 3, ADR-0041)
---

# Audit Crate

Run this when you've added new files, new aggregates, or finished a refactor inside `pcd-domain` or `pcd-db`. Checks internal conventions — not cross-crate boundaries (that's `/audit-hexagonal`).

The user specifies which crate: `pcd-domain`, `pcd-db`, or both.

---

## If auditing `pcd-domain`

### Step 1 — Run Tests

// turbo
```
cargo test -p pcd-domain
```

All tests must pass before auditing structure.

### Step 2 — File Inventory

List all files with sizes. Flag any file over 400 lines for review (ADR-0041 says split by concern count, not line count — but 400+ is a smell worth investigating).

```powershell
Get-ChildItem crates\pcd-domain\src -Recurse -File | ForEach-Object { "$($_.FullName) ($(Get-Content $_.FullName | Measure-Object -Line | Select-Object -Expand Lines) lines)" }
```

Present as a table sorted by line count descending.

### Step 3 — Test Organization (ADR-0041)

Check that value object files have inline `#[cfg(test)]` blocks, and aggregate directories have sibling `tests.rs`.

```powershell
# Find VO files WITHOUT inline tests — potential violation
# (VOs are files that are NOT mod.rs, tests.rs, repository, or the aggregate root)
Get-ChildItem crates\pcd-domain\src -Recurse -Include "*.rs" | ForEach-Object {
    $name = $_.Name
    if ($name -notmatch "mod\.rs|tests\.rs|repository|lib\.rs") {
        $hasTests = Select-String -Path $_.FullName -Pattern "#\[cfg\(test\)\]" -Quiet
        if (-not $hasTests) {
            "⚠ No inline tests: $($_.FullName)"
        }
    }
}
```

```powershell
# Find aggregate directories WITHOUT tests.rs — potential violation
Get-ChildItem crates\pcd-domain\src -Recurse -Directory | ForEach-Object {
    $modFile = Join-Path $_.FullName "mod.rs"
    $testFile = Join-Path $_.FullName "tests.rs"
    if ((Test-Path $modFile) -and -not (Test-Path $testFile)) {
        "⚠ No tests.rs: $($_.FullName)"
    }
}
```

For each flagged file, determine:
- Is it a value object with behavior? → Should have inline tests
- Is it a pure struct with no methods? → No tests needed (e.g., search_params.rs)
- Is it an aggregate directory? → Should have tests.rs

### Step 4 — Module Structure

Check that aggregate directories follow the convention:

```
<aggregate>/
├── mod.rs          — re-exports, entity/aggregate root
├── tests.rs        — aggregate-level integration tests
├── <vo>.rs         — value objects with inline tests
├── <repository>.rs — port trait (optional, may be in mod.rs)
└── events.rs       — domain events (optional)
```

Flag any directory that has:
- More than 10 files (might be too granular)
- Only 1 file besides mod.rs (might not need a directory)
- A folder inside a folder (micro-file anti-pattern from ADR-0041)

### Step 5 — Domain Purity Check

Domain crate should not contain infrastructure logic:

```powershell
# Should find zero matches (excluding derives and trait definitions)
Select-String -Path crates\pcd-domain\src\*.rs -Pattern "sqlx::query" -Recurse
Select-String -Path crates\pcd-domain\src\*.rs -Pattern "PgPool" -Recurse
Select-String -Path crates\pcd-domain\src\*.rs -Pattern "use pcd_db" -Recurse
```

Exception: `sqlx::FromRow` derives are allowed (ADR-0040 Rule 3).

---

## If auditing `pcd-db`

### Step 1 — Build Check

// turbo
```
cargo build -p pcd-db
```

### Step 2 — File Inventory

Same as domain — list all files with sizes, flag 400+ line files.

```powershell
Get-ChildItem crates\pcd-db\src -Recurse -File | ForEach-Object { "$($_.FullName) ($(Get-Content $_.FullName | Measure-Object -Line | Select-Object -Expand Lines) lines)" }
```

### Step 3 — Duplicate Type Check (ADR-0040 Rule 3)

Find all `sqlx::FromRow` structs and check for potential domain duplicates:

```powershell
Select-String -Path crates\pcd-db\src\*.rs -Pattern "derive.*sqlx::FromRow" -Recurse
```

For each `FromRow` struct, check:

1. Does a struct with the same or similar name exist in `pcd-domain`?
2. If the struct has a field-by-field mapping function (not a `reconstitute()` call) → likely duplicate
3. If the mapping converts String → enum/VO → legitimate row type

Present results in a table:

| DB Row Type | Domain Equivalent? | Mapping Type | Verdict |
|-------------|:--:|-------------|---------|
| JobRow | Job | reconstitute + enum conversion | ✅ Legitimate |
| ... | ... | ... | ... |

### Step 4 — Trait Coverage

Check that every domain repository trait has an implementation in pcd-db:

```powershell
# List all domain traits
Select-String -Path crates\pcd-domain\src\*.rs -Pattern "pub trait \w+Repository" -Recurse

# List all trait impls in pcd-db
Select-String -Path crates\pcd-db\src\*.rs -Pattern "impl \w+Repository for" -Recurse
```

Every domain trait should have exactly one implementation. Flag any gaps.

### Step 5 — File Organization

Check that the pcd-db module structure mirrors pcd-domain:

```
pcd-domain/src/operations/job/    →  pcd-db/src/operations/job.rs (or job/)
pcd-domain/src/workflows/ll152/   →  pcd-db/src/workflows/ll152/
pcd-domain/src/iam/               →  pcd-db/src/iam/
pcd-domain/src/directory/          →  pcd-db/src/directory/
```

Flag any DB module that doesn't have a corresponding domain module, or vice versa.

---

## Summary Report

```
Crate Audit: {crate_name}
============================
Tests:              ✅ PASS / ❌ FAIL
File sizes:         ✅ All under 400 / 🟡 N files over threshold
Test organization:  ✅ ADR-0041 compliant / 🟡 N files missing tests
Domain purity:      ✅ No leaks / ❌ N violations
Duplicate types:    ✅ None / ❌ N duplicates (pcd-db only)
Trait coverage:     ✅ Complete / ❌ N gaps (pcd-db only)

Issues:
- [list any]

Recommendations:
- [list any]
```
