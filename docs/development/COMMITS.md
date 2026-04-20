# Commit Guidelines

> Optimized for: clean history + agent speed via squash-merge PRs

## Branch Naming

```
feat/inventory-cross-character-transfer
fix/auth-token-refresh-loop
chore/ci-commitlint
```

## Commit Message Format

**Conventional Commits:**

```
type(scope): short imperative summary

optional body: why + what changed
optional footer: BREAKING CHANGE / refs
```

### Types

| Type | Use For |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change (no behavior change) |
| `perf` | Performance improvement |
| `test` | Adding/fixing tests |
| `docs` | Documentation only |
| `chore` | Build, deps, config |
| `ci` | CI/CD changes |

### Scopes

| Scope | Area |
|-------|------|
| `auth`, `voice_ai`, `inventory`, `lore` | Domain modules (`crates/domain`) |
| `api`, `db`, `domain` | Technical layers (`crates/`) |
| `ci`, `docs` | Supporting |

### Examples

```
fix(auth): handle expired Bungie refresh tokens gracefully
feat(inventory): add cross-character vault transfer saga
refactor(voice_ai): simplify intent JSON schema
docs(adr): log decision 015 for RAG lore architecture
```

## Merge Strategy

**Squash and merge** — PR title becomes the commit on main.

| Rule | Scope |
|------|-------|
| PR title | Must be conventional commit format |
| Intermediate commits | Light guidance (can be informal) |
| Branch | Delete after merge |

## Agent Rule

When working with an agent:
- Intermediate commits can be working notes
- PR title must be compliant
- Clean main branch is the goal

## What Makes a Good Commit

1. **Atomic** — One logical change
2. **Buildable** — Tests/lint pass
3. **Explains intent** — What and why
4. **Easy to revert** — No bundled unrelated changes
5. **Correct scope/type** — Helps grep and changelogs
