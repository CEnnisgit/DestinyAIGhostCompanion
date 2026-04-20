---
description: Onboard agent on the project's architectural decision landscape
---

# ADR Onboard

Run this workflow when a fresh agent conversation needs to understand the architectural
decisions that shaped PCD. This is a **read-only context recovery** workflow.

## When to Use

- Fresh conversation where the agent needs architectural context
- Agent is making design suggestions that contradict existing ADRs
- Before starting work on a new module or bounded context
- Pairs with `/pda-onboard` (documentation framework) — run both for full context

---

## Step 1: Read the Evolution

Read `docs/adr/EVOLUTION.md` first. This gives you the *story* — how thinking evolved
across 5 arcs (company model, tenancy, user role, technology, job engine).

**Key takeaways to internalize:**
- The **person** is the anchor entity, not the company (Arc 1)
- Data isolation uses **workspaces** with derived access, not schema-per-tenant (Arc 2)
- Users are **independent professionals** — companies add collaboration, not capabilities (Arc 3)
- The codebase is **Rust** (Axum + SQLx), not TypeScript (Arc 4)
- Jobs use an **engine + pluggable workflow** pattern (Arc 5)

## Step 2: Read the Index

Read `docs/adr/README.md` for the full inventory. Focus on:
- The **module index** to understand which ADRs affect the module you're working on
- The **superseded** section to know which decisions are historical

## Step 3: Read Module-Relevant ADRs

Based on the current task, read the ADRs for the relevant module:

| Working on... | Read these ADRs |
|---------------|----------------|
| IAM (users, companies, memberships) | 0027, 0028, 0029, 0030, 0031, 0032, 0033, 0034 |
| Operations (clients, buildings, jobs) | 0018, 0021, 0022, 0023 |
| Workflows (job engine, LL152) | 0007, 0016, 0025, 0035 |
| Directory (buildings, BIN, PAD) | 0012, 0013, 0014, 0015 |
| API / frontend | 0019, 0024 |
| Cross-cutting (architecture, naming) | 0001, 0005, 0008, 0036 |

Only read the ones relevant to the task — don't read all 35.

## Step 4: Verify Understanding

After reading, you should be able to answer:

1. What is the isolation unit for tenant data? → Workspace (`workspace_id`)
2. Does a user need a company to create jobs? → No, jobs are personal capabilities
3. How is workspace access determined? → Derived from domain relationships, not stored
4. What is the relationship between Job and LL152? → Engine + workflow plugin pattern
5. What naming convention do Rust modules use? → Singular (e.g., `client.rs`, not `clients.rs`)

If you got all 5, you have sufficient context. Proceed with your task.

---

## Related Workflows

| Workflow | Purpose |
|----------|---------|
| `/pda-onboard` | Documentation framework context (where docs go) |
| `/adr-check` | Mine for missing ADR candidates |
| `/adr-capture` | Draft a new ADR (includes README + EVOLUTION updates) |
