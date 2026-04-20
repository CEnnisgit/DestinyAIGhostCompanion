---
description: Audit a crate for ADR-0040 hexagonal compliance (run after adding files or major refactors)
---

# Audit Hexagonal Compliance

Run this workflow after adding new files, new modules, or completing a refactor on any PCD crate. It checks all three rules from [ADR-0040](../../docs/adr/0040-hexagonal-enforcement-and-cqrs-lite.md).

The user may specify a crate to focus on (`pcd-api`, `pcd-db`, `pcd-domain`), or run across all three.

## Step 1 — Run Architecture Tests (Rule 1)

These are the automated guard rails. If they pass, Rule 1 is satisfied.

```
cargo test -p pcd-api --test architecture
```

Report: Pass/Fail. If any test fails, stop — fix the hexagonal violation before continuing.

## Step 2 — Check for Import Violations (Rule 1, extended)

Grep for imports that shouldn't exist. Report any matches as violations.

```bash
# pcd-api route handlers must not import pcd_db or sqlx
grep -rn "use pcd_db" crates/pcd-api/src/routes/
grep -rn "use sqlx" crates/pcd-api/src/routes/
grep -rn "PgPool" crates/pcd-api/src/routes/

# pcd-api auth layer must not import pcd_db or sqlx
grep -rn "use pcd_db" crates/pcd-api/src/auth/
grep -rn "use sqlx" crates/pcd-api/src/auth/

# Exception: main.rs (composition root) is allowed to import anything
```

Report: List any matches. Zero matches = pass. Any match outside `main.rs` = violation.

## Step 3 — Route Module Size Check (Rule 2)

Check route file sizes to identify candidates for CQRS-lite splitting.

```bash
# List all route files with line counts
find crates/pcd-api/src/routes -name "*.rs" | xargs wc -l | sort -rn
```

Flag files that exceed the thresholds from ADR-0040:
- **> 200 lines** with both reads and writes → should be a directory module
- **> 4 endpoints** with both reads and writes → should be a directory module

Present results as a table:

| File | Lines | Endpoints | Has Queries? | Has Commands? | Action |
|------|------:|----------:|:---:|:---:|--------|
| ... | ... | ... | ... | ... | Keep / Split |

## Step 4 — Duplicate Type Audit (Rule 3)

Find all `sqlx::FromRow` structs in `pcd-db` and check for potential domain duplicates.

```bash
# List all FromRow structs in pcd-db
grep -rn "derive.*sqlx::FromRow" crates/pcd-db/src/ | grep "struct"

# List all pub structs in pcd-domain
grep -rn "pub struct" crates/pcd-domain/src/
```

For each `FromRow` struct in pcd-db, check:

1. **Does a struct with the same name exist in pcd-domain?** → Likely duplicate. Investigate.
2. **Does the DB struct have a field-by-field mapping function?** → Smell. Check if the types are identical.
3. **Does the DB struct convert String fields to domain enums/VOs?** → Legitimate. No action needed.

Present results as a table:

| DB Row Type | File | Domain Equivalent? | Has Mapping Fn? | Verdict |
|-------------|------|--------------------|:---:|---------|
| ... | ... | ... | ... | Clean / Duplicate / Investigate |

## Step 5 — Summary Report

Produce a summary:

```
ADR-0040 Hexagonal Compliance Audit
====================================
Rule 1 (Import Boundary):     ✅ PASS / ❌ FAIL (N violations)
Rule 2 (Route Organization):  ✅ PASS / 🟡 N files over threshold
Rule 3 (No Duplicate Types):  ✅ PASS / ❌ N duplicates found

Violations requiring action:
- [list any]

Recommendations (non-blocking):
- [list any]
```

## When To Run This Workflow

- After adding new route handlers or API endpoints
- After adding new repository traits or DB adapter types
- After a significant refactor touching cross-crate boundaries
- Before closing a sub-phase that touched `pcd-api` or `pcd-db`
