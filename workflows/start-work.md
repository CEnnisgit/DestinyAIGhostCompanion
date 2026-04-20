---
description: Initialize a work session with git status check and branching decision
---

# Start Work Workflow

Run at the beginning of any work session to set up proper context.

> [!CAUTION]
> **NEVER branch off `main`. The default working branch is `dev`.**
> All feature branches MUST be created from `dev`.
> Before creating any branch, ALWAYS run `git branch --show-current` to verify.

## 1. Check Git Status

// turbo
```bash
git status
```

// turbo
```bash
git branch --show-current
```

**Review:**
- Any uncommitted changes?
- Which branch are you on?
- Is there work in progress to continue?
- **Are you on `dev`?** If not, switch to `dev` before creating new branches.

## 2. Sync with Remote

// turbo
```bash
git fetch origin
```

Check if you're behind:
```bash
git log HEAD..origin/dev --oneline
```

If behind, consider:
```bash
git pull origin dev
```

## 3. Decide: Branch or Direct?

### Quick decision tree:

| Work type | Time estimate | Risk | Action |
|-----------|---------------|------|--------|
| Typo fix, doc tweak | < 15 min | Low | Direct to dev OK |
| Small config change | < 30 min | Low | Direct to dev OK |
| New feature | > 30 min | Any | Create feature branch |
| Bug fix (non-trivial) | Any | Medium+ | Create feature branch |
| Refactoring | Any | Medium+ | Create feature branch |
| Anything you'd want to revert | Any | Any | Create feature branch |

**Rule of thumb:** If in doubt, branch. It's cheap.

## 4. Create Branch (if needed)

**CRITICAL: Always branch from `dev`:**
```bash
git checkout dev
git pull origin dev
git checkout -b <type>/<short-description>
```

### Branch naming:
```
type/short-description
```

Examples:
```bash
git checkout -b feat/job-actions
git checkout -b fix/auth-token-refresh
git checkout -b refactor/module-separation
git checkout -b chore/update-deps
git checkout -b phase<N>/<feature-name>
git checkout -b prototype/<name>
```

### Push and set upstream:
```bash
git push -u origin feat/your-branch-name
```

## 5. Set Context

If starting a new feature:
- Consider running `/plan-feature` first
- Check `docs/roadmap/README.md` for current priorities

If continuing work:
- Review any open PRs
- Check CI status

## 6. Merge Back to Dev

When work is complete, squash merge back to `dev`:
```bash
git checkout dev
git merge --squash <branch-name>
git commit -m "feat: <description of all changes>"
git push origin dev
```

## 7. Work Session Outputs

At end of session, you should have:

| Scenario | Expected state |
|----------|----------------|
| Small direct work | Committed to dev, pushed |
| Feature work | Commits on feature branch, PR draft open |
| Ready to release | Run `/release-staging` |

## Quick Start Commands

```bash
# Check status
git status && git branch --show-current

# Start new feature (ALWAYS from dev)
git checkout dev && git pull && git checkout -b feat/my-feature

# Continue existing feature
git checkout feat/my-feature && git pull origin feat/my-feature
```
