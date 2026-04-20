---
description: Full context recovery for a fresh agent conversation
---

# Agent Onboard

The master onboarding workflow. Run this at the start of any fresh conversation
where the agent has zero context about PCD. After completing this workflow, the
agent should be able to work productively on any part of the codebase.

**Time:** ~2 minutes of reading. No commands, no artifacts — read-only.

---

## Step 1: What Is PCD?

PCD (Plumber Compliance Dashboard) is a SaaS platform for NYC plumbing compliance.
It helps plumbers and plumbing companies manage Local Law 152 gas inspections,
track buildings, manage clients, and handle compliance obligations.

**Key identity insight:** The *person* (plumber) is the anchor entity, not the
company. A plumber signs up as an individual, can work independently or join
companies, and their credentials/work history belong to *them*.

## Step 2: Codebase Structure

Read the workspace root to understand the Rust crate layout:

```
crates/
├── pcd-domain/   # Domain layer — aggregates, VOs, repository traits
│   └── src/
│       ├── iam/         # Identity: User, Company, LmpCredential, Membership
│       ├── operations/  # Client, SavedBuilding, Job
│       ├── workflows/   # LL152 workflow-specific logic
│       ├── directory/   # Buildings, addresses, BIN pipeline
│       └── shared/      # Cross-cutting (Email, PhoneNumber VOs)
├── pcd-db/       # Database layer — SQLx repos, migrations, bootstrap
└── pcd-api/      # API layer — Axum routes, middleware, server
```

Quickly scan:
1. `crates/pcd-domain/src/lib.rs` — module declarations
2. `crates/pcd-api/src/routes/` — available API endpoints

## Step 3: Documentation Framework

Run `/pda-onboard` mentally or by reading `docs/` structure:

| Directory | Purpose |
|-----------|---------|
| `docs/1-pre-implementation/` | Requirements (SRSD) and resources (RLD) |
| `docs/2-during-implementation/DDD/` | Design specs — **source of truth during active dev** |
| `docs/2-during-implementation/CLD/` | Feature completion logs |
| `docs/3-after-implementation/` | Post-ship walkthroughs and manuals |
| `docs/roadmap/` | Phase plans, sub-phase tracking artifacts |
| `docs/adr/` | Architecture Decision Records |
| `docs/pda-sdd-paper/` | The research paper the framework is based on |

**Key rule:** DDD specs in `ModuleDesign/` are the source of truth. When in doubt
about how an entity works, read its spec before reading code.

If deeper understanding is needed, read `.agent/workflows/pda-onboard.md` in full.

## Step 4: Architectural Decisions

Read `docs/adr/EVOLUTION.md` — this gives the *story* of how architectural thinking
evolved across 5 arcs:

1. **Company:** tenant container → optional membership
2. **Tenancy:** company_id → workspace abstraction + derived access
3. **User Role:** employee → independent professional
4. **Technology:** TypeScript hexagonal → Rust DDD crates
5. **Job Engine:** monolithic CRUD → pluggable workflows

If working on a specific module, read the module-relevant ADRs listed in
`docs/adr/README.md` under the module index.

If deeper understanding is needed, read `.agent/workflows/adr-onboard.md` in full.

## Step 5: Locate Roadmap Position

This is the most important step. The goal is to know exactly where work left off
and what the next task is.

### 5.1 Git state

// turbo
```bash
git branch --show-current
git log --oneline -10
git status --short
```

Note the branch name — it encodes the active phase (e.g., `phase3a/data-foundation`).

### 5.2 Find the active phase roadmap

Read the roadmap for the current phase:

```
docs/roadmap/phase3/          ← Phase tracking directory
docs/roadmap/phase3/README.md ← Phase overview and sub-phase breakdown
```

Scan the README to understand:
- What sub-phases exist (3A, 3B, 3C, etc.)
- What each sub-phase covers
- Which ones are marked complete vs in-progress vs planned

### 5.3 Find the active sub-phase artifacts

Look for the 4 tracking artifacts in `docs/roadmap/phase3/`:

| Artifact | What it tells you |
|----------|-------------------|
| `*_implementation_matrix.md` | **What's built (✅) vs pending (⬜).** This is the resume point. |
| `*_session_journal.md` | **What happened recently.** Last few entries = last session's work. |
| `*_spec_audit.md` | Whether specs match code. If this exists and is complete, the sub-phase may be closing. |
| `*_traceability_matrix.md` | End-to-end wiring proof. If complete, sub-phase is ready to close. |

Read the implementation matrix first — it tells you exactly which entities/features
are done and which are next.

### 5.4 Read the relevant DDD specs

Based on what the matrix says is next, read the DDD spec for the next entity:

```
docs/2-during-implementation/DDD/ModuleDesign/{Module}/{Entity}_Aggregate.md
```

This is the blueprint for the next piece of work.

### 5.5 Produce a resume summary

After steps 5.1–5.4, summarize for the user:

```markdown
## Resume Point

**Phase:** [e.g., Phase 3 — IAM & Access Control]
**Sub-phase:** [e.g., 3A — Data Foundation]
**Branch:** [e.g., phase3a/data-foundation]
**Last commit:** [commit message and date]

### Completed
- [list of ✅ items from the matrix]

### Next Up
- [first ⬜ item from the matrix]
- [relevant spec: link to DDD spec]

### Open Items (if any)
- [deferred tasks, spec drift, or pending decisions noted in journal]
```

Present this summary to the user and confirm before starting work.

## Step 6: Working Rules

These are non-negotiable constraints:

| Rule | Detail |
|------|--------|
| **Commit policy** | Code changes and documentation updates are committed separately |
| **Build policy** | **NEVER** run `cargo build -p pcd-api` automatically — always ask first |
| **Test execution** | Always use `--test-threads=1` for database integration tests |
| **Diagnostics** | Prefer raw SQL and methodical investigation over speculative fixes |
| **Naming** | Singular module names (`client.rs`, not `clients.rs`) — see ADR-0036 |
| **Package manager** | `pnpm`, never `npm` (for any JS/TS tooling) |
| **File editing** | Use `write_to_file` instead of `replace_file_content` (user rule) |

## Step 7: Verify Readiness

After completing steps 1–6, you should be able to answer:

1. What language/framework is the backend? → Rust, Axum, SQLx
2. What are the 4 domain modules? → iam, operations, workflows, directory
3. Where do entity design specs live? → `docs/2-during-implementation/DDD/ModuleDesign/`
4. What is the data isolation unit? → Workspace (`workspace_id`)
5. Can a user create jobs without a company? → Yes, jobs are personal capabilities
6. What phase/sub-phase are we in? → (from step 5)
7. What was the last thing completed? → (from implementation matrix)
8. What is the next task to pick up? → (from implementation matrix)

**If you can answer all 8, present the resume summary from step 5.5 and wait for
user confirmation before starting any work.**

---

## Related Workflows

After onboarding, these are the most common next steps:

| Situation | Workflow |
|-----------|----------|
| Starting a work session | `/start-work` |
| Need deeper doc framework context | `/pda-onboard` |
| Need deeper architectural context | `/adr-onboard` |
| Starting a new sub-phase | `/start-subphase` |
| Continuing an active sub-phase | `/maintain-subphase` |
| Don't know which workflow to use | `/workflow-guide` |

