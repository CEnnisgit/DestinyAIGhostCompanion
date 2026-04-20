---
description: Onboard agent context on the PDA-SDD documentation framework and how PCD uses it
---

# PDA-SDD Context Onboarding

Run this workflow when the agent has lost context on the project's documentation philosophy
and starts making mistakes like: putting specs in wrong directories, creating docs without
following the phase structure, or confusing what belongs where.

This is a **read-only context recovery** workflow — it produces no artifacts, only understanding.

---

## Step 1: Read the Model

Read the PDA-SDD paper overview to understand the three-phase concept:

1. Read `docs/pda-sdd-paper/README.md` — paper section map and how PCD adapts it.
2. Read `docs/pda-sdd-paper/03_model_overview.md` — the core 3-phase model.

**Key takeaway:** All software documentation belongs to one of three lifecycle phases:
Pre-Implementation, During-Implementation, or After-Implementation. Each phase has
specific document types. Documents are "living" — they evolve with the code.

---

## Step 2: Understand the PCD Development Cycle

PCD follows a research-first iterative cycle that maps directly to PDA-SDD.
This is the actual workflow used for Phases 1–3:

```
Roadmap (= PRD)
  │  "Phase 3 covers Identity, Auth, RLS, Profile"
  ↓
Research → SRSD requirements
  │  No assumptions. Research the domain, audit the codebase,
  │  identify entities and boundaries. Sub-phases emerge here.
  ↕
DDD Spec Design (co-evolves with research)
  │  Write entity specs (aggregates, VOs, repos).
  │  Research may reshape the roadmap — that's expected.
  ↓
Roadmap Refinement
  │  Update the roadmap if research changed the plan.
  │  Sub-phase boundaries crystallize.
  ↓
Sub-Phase Implementation (per sub-phase)
  │  /start-subphase → /maintain-subphase → /finish-subphase
  │  Build each entity: Domain → DB → API → Tests
  ↓
CLD Feature Logs
  │  Record what was built after each feature ships.
  ↓
Revision (if needed)
    Rare. Feeds back into DDD specs or sub-phase plan.
```

**Critical insight:** The roadmap and DDD specs **co-evolve** during the research phase.
It is NOT "finish roadmap → write specs." It is "rough roadmap → research challenges it →
specs take shape → roadmap adjusts → sub-phases crystallize." The roadmap is not fixed
until the specs are done.

---

## Step 3: Understand the Three Phases

### Pre-Implementation (`docs/1-pre-implementation/`)

**When:** Before writing code. Captures WHAT to build.

| PDA-SDD Doc | PCD Implementation | Purpose |
|-------------|-------------------|---------|
| **SRSD** (Software Requirements Specification Document) | `1-pre-implementation/SRSD/` | Coded functional + non-functional requirements (SFR/SNFR) |
| **RLD** (Resources List Document) | `1-pre-implementation/RLD.md` | Team, tools, tech stack |

Also contains:
- `Architecture/` — Early architectural decisions (ADR-influenced)
- `PRD_EXTRACTION_NOTES.md` — Raw notes from the Product Requirements Document

### During-Implementation (`docs/2-during-implementation/`)

**When:** While writing code. Captures HOW it's built. This is the most active directory.

| PDA-SDD Doc | PCD Implementation | Purpose |
|-------------|-------------------|---------|
| **DDD** (Detailed Design Document) | `2-during-implementation/DDD/` | Technical design — architecture, data, interfaces, modules |
| **CLD** (Change Log Document) | `2-during-implementation/CLD/` | Feature completion logs organized by workflow phase |

The DDD has five sub-sections:
- `DDD/Traceability/` — Maps SRSD requirements to modules
- `DDD/SystemArchitecture/` — High-level diagrams and tech stack
- `DDD/DataDesign/` — ERD, schemas, database design
- `DDD/InterfaceDesign/` — UI specs and API specs
- `DDD/ModuleDesign/` — **Per-module DDD specs** (this is where entity specs live)

**ModuleDesign is the most critical directory.** It contains bounded-context-level specs:
- `ModuleDesign/IAM/` — Identity entities (User, Company, LmpCredential, etc.)
- `ModuleDesign/Auth/` — Authentication (Phase 3B+)
- `ModuleDesign/Operations/` — Jobs, Clients, SavedBuildings
- Each entity has a spec file (e.g., `User_Aggregate.md`, `Company_Aggregate.md`)

**Important:** DDD specs are "living documents" — they are drafted BEFORE coding starts
(during the research phase) and refined as implementation reveals drift. They are NOT
written after the fact.

### After-Implementation (`docs/3-after-implementation/`)

**When:** After code is shipped. Captures the final state for users and maintainers.

| PDA-SDD Doc | PCD Implementation | Purpose |
|-------------|-------------------|---------|
| **SUMD** (Software User Manual Document) | `3-after-implementation/Modules/` | Per-module walkthrough of what was built |
| **EULA** (End User License Agreement) | `3-after-implementation/` | Legal/licensing (deferred for PCD) |

Also contains:
- `Architecture_Overview.md` — Post-implementation architecture snapshot
- `future-feats/` — Deferred feature ideas captured during implementation

---

## Step 4: Understand the Roadmap's Role

**The roadmap IS the PRD.** It is not separate from PDA-SDD — it is the input that drives it.

| Location | Role in PDA-SDD |
|----------|----------------|
| `docs/roadmap/` | **PRD** — defines what each phase covers |
| `docs/roadmap/phase3/` | **Phase tracking** — sub-phase artifacts (matrices, journals, audits) |

Phase tracking artifacts live alongside the roadmap because they are project management
tools that verify the PDA-SDD deliverables (specs, code, tests) are correct:

| Artifact | Purpose | Relationship to PDA-SDD |
|----------|---------|------------------------|
| Implementation Matrix | Tracks what's built | Rows = DDD entities to implement |
| Session Journal | Logs commits | Records when DDD→code work happened |
| Spec Audit | Verifies code matches spec | Directly reads DDD specs |
| Traceability Matrix | Proves end-to-end wiring | Traces DDD spec → domain → db → api |

---

## Step 5: Know the Handoff Points

These are the moments where work crosses between roadmap, DDD, and CLD:

### Roadmap → DDD (before you write code)
The roadmap names WHAT to build. You go to DDD/ModuleDesign/ to design the spec.
This happens during the research phase, before sub-phases are even defined.

### DDD → Code (while you write code)
The DDD spec is the blueprint. You implement the domain struct to match it exactly.
The roadmap (Session Journal) logs that this happened.

### Code → Roadmap (after you write code)
Mark the entity ✅ in the Implementation Matrix. Log the commit in the Session Journal.
No DDD changes here — just tracking.

### Roadmap ↔ DDD (during the spec audit)
The Spec Audit (roadmap artifact) reads DDD specs, compares them to code, and produces
fix-actions that flow back into DDD specs. This is the only overlap point.

### Code → CLD (after features ship)
Feature completion logs go to CLD after code is committed and verified.
CLD is organized by workflow phase (Job Intake, Field Capture, etc.), not by date.

---

## Step 6: Know the Rules

### Rule 1: Phase determines directory
- Requirement? → `1-pre-implementation/SRSD/`
- Design spec for an entity? → `2-during-implementation/DDD/ModuleDesign/{Module}/`
- Feature completion log? → `2-during-implementation/CLD/{Feature}/`
- Walkthrough of what was built? → `3-after-implementation/Modules/`
- ADR? → `docs/adr/` (complements PDA-SDD)
- Phase plan / tracking? → `docs/roadmap/`

### Rule 2: DDD specs are the source of truth during active development
- When in doubt about how an entity works, read its DDD spec first.
- Each spec has a `Source of Truth` line pointing to the Rust implementation file.
- Specs and code must stay in sync — drift is a bug.

### Rule 3: Living documents, not deliverables
- The SRSD, DDD, and CLD are continuously updated as the system evolves.
- Version numbers in specs track significant changes.
- Status fields track implementation progress (Draft → Implemented).

### Rule 4: CLD entries are written AFTER a feature is complete
- Never log a feature to `2-during-implementation/CLD/` until the code is committed.
- Each CLD entry records: what changed, why, and which files were affected.

### Rule 5: Specs are designed BEFORE code, not after
- DDD specs are drafted during the research phase, before implementation starts.
- The research phase may reshape the roadmap — that's expected and correct.
- Sub-phase boundaries emerge from research, not from upfront guessing.

---

## Step 7: Verify Understanding

After reading the above, you should be able to answer:

1. What is the relationship between the roadmap and PDA-SDD? → The roadmap is the PRD — the input that drives the framework.
2. When are DDD specs written? → During the research phase, BEFORE coding. They co-evolve with the roadmap.
3. Where does a new entity's aggregate spec go? → `docs/2-during-implementation/DDD/ModuleDesign/{Module}/`
4. Where does a requirement go? → `docs/1-pre-implementation/SRSD/`
5. Where do phase tracking artifacts go? → `docs/roadmap/phase3/`
6. Where does a feature completion log go? → `docs/2-during-implementation/CLD/{Workflow}/`
7. When does the CLD get written? → After code is committed and verified, never before.
8. What is the only point where roadmap and DDD directly interact? → The Spec Audit.

If you got all 8 right, context is restored. Proceed with your task.

---

## Related Workflows

| Workflow | Purpose |
|----------|---------|
| `/pda-pre-implementation` | Generate SRSD + RLD from a PRD |
| `/pda-during-implementation` | Populate DDD + CLD during coding |
| `/pda-after-implementation` | Generate SUMD + EULA after shipping |
| `/pda-sync-feature` | Update DDD for a single feature cyclically |
| `/start-subphase` | Scaffold sub-phase tracking artifacts |
| `/maintain-subphase` | Session-level journal + matrix tracking |
| `/finish-subphase` | Spec audit + traceability proof + gate checks |
