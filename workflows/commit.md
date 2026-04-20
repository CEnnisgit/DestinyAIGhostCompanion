---
description: Create well-formed commits following project conventions
---

# Commit Workflow

Use when making commits to ensure consistency and quality.

## Quick Reference

```
type(scope): short imperative summary
```

Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `ci`

Full guidelines: [COMMITS.md](../../docs/development/COMMITS.md)

---

## 1. Stage Changes Atomically

Review what you're committing:

```bash
git diff --stat
git add -p  # for partial staging
```

**Rule:** One logical change per commit.

## 2. Write Commit Message

### For intermediate commits (during development)

Informal is OK — these get squashed:
```bash
git commit -m "wip: job service refactor"
git commit -m "add tests"
```

### For direct-to-dev commits

Must follow conventional format:
```bash
git commit -m "fix(auth): handle expired refresh tokens"
```

## 3. PR Title (Most Important)

Since you squash-merge, **the PR title becomes the commit on main**.

Format:
```
type(scope): imperative description
```

Examples:
- `feat(compliance): add job schedule and complete actions`
- `fix(auth): unify invalid-credentials responses`
- `refactor(container): centralize module wiring`

## 4. Pre-Push Checks

Before pushing, verify:

// turbo
```bash
pnpm --filter @pcd/backend run lint
```

// turbo
```bash
pnpm --filter @pcd/backend run build
```

## 5. Commit Quality Checklist

Before finalizing a commit or PR:

- [ ] One logical change only
- [ ] Build/lint passes
- [ ] Commit message follows convention
- [ ] Scope is accurate
- [ ] Description is imperative ("add" not "added")

## Breaking Changes

If your change breaks backward compatibility:

```
type(scope)!: description

BREAKING CHANGE: explanation of what breaks and migration path
```

## Quick Commit Commands

```bash
# Feature commit
git commit -m "feat(scope): add feature description"

# Bug fix
git commit -m "fix(scope): correct issue description"

# Refactor
git commit -m "refactor(scope): restructure description"

# Docs
git commit -m "docs(scope): update documentation"

# Chore
git commit -m "chore(scope): maintenance task"
```
