# LL152 Inspection Workflow Specification

**Version:** 0.1.0  
**Status:** Draft  
**Module:** Job Workflows — LL152  
**Parent Aggregate:** `Job`  
**Engine Spec:** `Job_Aggregate.md`  
**JobType:** `LL152_INSPECTION`

---

## Objective

This is the **centerpiece specification** for the LL152 Inspection Workflow — the first pluggable workflow in the Job engine.

It synthesizes the research sub-specs into a single implementation-ready reference, analogous to how `Job_Aggregate.md` serves the Job engine.

A coding agent should be able to implement the LL152 workflow module from this document without inventing domain rules.

---

## 1. What the LL152 Workflow Is

The LL152 workflow governs how a gas piping periodic inspection job proceeds from creation through completion.

It is responsible for:
- determining which compliance branch applies;
- capturing inspection data (GPS1);
- recording findings and stop conditions;
- managing review and revision;
- producing certification outcomes (GPS2);
- and tracking workflow-level progress distinct from engine lifecycle.

It is **not** responsible for:
- the Job engine lifecycle (`JobStatus`);
- compliance obligation scheduling (belongs to `LL152Program` / `ComplianceObligation`);
- building identity (belongs to `Building` aggregate);
- or report delivery mechanics (separate concern).

---

## 2. Branch Topology

LL152 is **one workflow family** under one `JobType` (`LL152_INSPECTION`) with **three workflow-owned sub-branches**.

These are not minor variations. They are materially different compliance paths that share program identity but not capture requirements.

### Branch A — Standard Inspection

**Entry condition:** Building contains gas piping AND is currently supplied with gas.

This is the canonical LL152 workflow — the capture-heavy inspection path.

- Primary artifact: `GPS1` (inspection report)
- Certification artifact: `GPS2` (certification/filing)
- Produces: structured findings, correction outcomes, signed report
- This branch drives the majority of the workflow design

### Branch B — No Gas Piping

**Entry condition:** Building contains no gas piping system.

This is a certification-only path. No inspection is performed.

- Primary artifact: `GPS2` (no-gas-piping certification)
- GPS1 does **not** apply
- Must **not** be modeled as "Branch A with empty fields"

### Branch C — Gas Piping Present but Not Supplied

**Entry condition:** Building contains gas piping AND is not currently supplied with gas AND no gas utilization equipment is connected.

This is a statement-collection path, distinct from both A and B.

- Primary artifacts: utility statement, owner statement
- GPS1 does **not** apply as the governing artifact
- Must **not** be collapsed into Branch B

### Branch Discriminator

The workflow module owns an explicit discriminator:

```text
JobType = LL152_INSPECTION
  └── LL152 workflow module
        ├── branch_discriminator: STANDARD_INSPECTION | NO_GAS_PIPING | GAS_PIPING_NOT_SUPPLIED
        ├── Branch A path (capture-heavy, GPS1, findings, review, GPS2)
        ├── Branch B path (no-gas-piping certification)
        └── Branch C path (statement-collection / filing path)
```

The engine sees one `LL152_INSPECTION` job. The workflow owns branch determination.

> **Detail:** [ll_152_branch_topology.md](research/ll_152_branch_topology.md)

---

## 3. Branch Entry and Discrimination Rules

### When is branch determined?

Branch classification may happen at:
- **Intake** — if the building's gas piping status is already known;
- **Field execution** — if the inspector discovers the actual condition differs from intake assumptions.

### Who sets the branch?

The workflow module sets the branch discriminator. The Job engine does not participate.

### Can branch change?

Yes. If a job enters as `STANDARD_INSPECTION` but the building turns out to have no gas supply, the workflow should support reclassification to `GAS_PIPING_NOT_SUPPLIED` — because `JobType` is immutable, but the branch discriminator is workflow-owned and mutable.

### When does branch become fixed?

Branch should become fixed when the workflow reaches a certification-outcome state. Once the job is in `CERTIFICATION_*` or `FINALIZED`, branch reclassification should be blocked.

---

## 4. GPS1 — Inspection Report Artifact

`GPS1` is the **Gas Piping System Periodic Inspection Report**. It belongs exclusively to **Branch A**.

### Official section structure

1. Location Information
2. Licensed Master Plumber (LMP) Information
3. Individual Performing Inspection (Qualified Individual) Information
4. Certification of Inspection Results
5. Additional Comments
6. Certification of Licensed Master Plumber
7. Certification of Individual Performing Inspection

### Architectural role

GPS1 is a **workflow-owned structured report artifact**. It is not the Job engine payload, not a generic attachment, and not the full LL152 workflow model.

### Key design rules

- GPS1 section structure should drive the internal workflow data grouping
- The form captures both content (findings, comments) and attestation (LMP sign-off, inspector sign-off)
- Freeform comments complement structured findings; they do not replace them
- Location data should be pulled from `Building` at render time, not copied at capture time (see `OPEN_DESIGN_QUESTIONS.md`)

> **Detail:** [gps_1_form_spec.md](research/gps_1_form_spec.md)

---

## 5. GPS2 — Certification / Filing Artifact

`GPS2` is the **Gas Piping System Periodic Inspection Certification**. It is the cross-branch certification/filing surface.

### GPS1 vs GPS2

| | GPS1 | GPS2 |
|---|---|---|
| Type | Inspection report | Certification / filing |
| Branch scope | Branch A only | All branches |
| Content | Findings, comments, attestation | Certification outcomes |
| Audience | Owner-facing report | DOB submission |

### Certification outcome categories (from official GPS2 form)

1. **No gas piping system** (Branch B)
2. **No conditions requiring correction** (Branch A)
3. **Conditions requiring correction were identified** (Branch A)
4. **Correction of one or more conditions will take additional time** (Branch A)
5. **All identified conditions have been corrected** (Branch A)

### Branch-specific GPS2 role

- **Branch A:** certification counterpart to GPS1 inspection work
- **Branch B:** primary compliance artifact (no-gas-piping certification)
- **Branch C:** relationship still unresolved — may be statement/filing path with separate evidence

> **Detail:** [gps_2_certification_and_filing_branches.md](research/gps_2_certification_and_filing_branches.md)

---

## 6. Findings Model

A **finding** is a workflow-owned record of an inspection-result category evaluated during a Branch A inspection.

### Official findings categories (from GPS1)

1. `IMPROPER_USE_OF_FLEX_HOSE`
2. `ILLEGAL_CONNECTION_OR_NON_CODE_COMPLIANT_INSTALLATION`
3. `GAS_LEAK_0_1_PERCENT_OR_MORE_IN_AIR`
4. `WORN_PART_AFFECTING_SAFE_AND_RELIABLE_OPERATION`
5. `OTHER_UNSAFE_CONDITION`

These are a closed initial vocabulary, not freeform user-defined types.

### Finding shape

Each finding supports:

- `finding_id`
- `job_id`
- `category` (one of the five above)
- `observation_result` (`OBSERVED` / `NOT_OBSERVED`)
- `narrative_detail` (required if observed)
- `requires_correction` (boolean)
- `requires_immediate_reporting` (boolean)
- `recorded_at`
- `recorded_by`

### Full category evaluation

The model should represent all five categories per inspection — not just the ones with issues. This proves the inspection was thorough.

### Three severity tiers

1. **Observed condition** — something was found in a named category
2. **Correction-required condition** — affects certification outcome, requires follow-up
3. **Stop-the-line / immediate-report condition** — requires immediate escalation from the field

Stop conditions include at minimum: `GAS_LEAK` and `ILLEGAL_CONNECTION`.

Stop conditions are **guards and consequences** on workflow transitions, not standalone workflow states.

### Findings → GPS2 certification mapping

| Findings outcome | GPS2 certification path |
|---|---|
| All categories `NOT_OBSERVED` | `CERTIFICATION_NO_CORRECTION` |
| Any `OBSERVED` + `requires_correction` | `CERTIFICATION_CORRECTION_REQUIRED` |
| Correction in progress | `CERTIFICATION_CORRECTION_PENDING` |
| All corrections resolved | `FINALIZED` |

> **Detail:** [ll_152_findings_and_stop_conditions_spec.md](research/ll_152_findings_and_stop_conditions_spec.md)

---

## 7. Workflow State Model

The LL152 workflow owns its **own branch-aware state model**, separate from engine `JobStatus`.

### Engine / workflow split

- `JobStatus` answers: **is this work open, active, finished, or dead?**
- LL152 workflow state answers: **where is this job inside the LL152 process for its branch?**

### Branch A states

| State | Meaning |
|---|---|
| `DRAFT` | Workflow instance exists, capture not begun |
| `CAPTURING` | Inspection data actively being captured |
| `READY_FOR_REVIEW` | Capture complete enough for reviewer |
| `UNDER_REVIEW` | LMP/reviewer actively reviewing |
| `RETURNED` | Review rejected, sent back for revision |
| `CERTIFICATION_NO_CORRECTION` | No correction required |
| `CERTIFICATION_CORRECTION_REQUIRED` | Corrections identified |
| `CERTIFICATION_CORRECTION_PENDING` | Corrections in progress |
| `FINALIZED` | Workflow complete for this branch |

### Branch B states

`DRAFT` → `CERTIFICATION_READY` → `FINALIZED`

### Branch C states

`DRAFT` → `STATEMENTS_PENDING` → `STATEMENTS_READY` → `FINALIZED`

### Branch A transition table

| From | To | Trigger |
|---|---|---|
| `DRAFT` | `CAPTURING` | Capture begins |
| `CAPTURING` | `READY_FOR_REVIEW` | Package complete |
| `READY_FOR_REVIEW` | `UNDER_REVIEW` | Reviewer begins |
| `UNDER_REVIEW` | `RETURNED` | Review rejects |
| `RETURNED` | `CAPTURING` | Revision resumes |
| `UNDER_REVIEW` | `CERTIFICATION_NO_CORRECTION` | No correction needed |
| `UNDER_REVIEW` | `CERTIFICATION_CORRECTION_REQUIRED` | Correction needed |
| `CERTIFICATION_CORRECTION_REQUIRED` | `CERTIFICATION_CORRECTION_PENDING` | Additional time needed |
| `CERTIFICATION_CORRECTION_REQUIRED` | `FINALIZED` | Correction complete |
| `CERTIFICATION_CORRECTION_PENDING` | `FINALIZED` | Correction complete |
| `CERTIFICATION_NO_CORRECTION` | `FINALIZED` | Certification path complete |

### Mapping to engine `JobStatus`

| Workflow state | Engine `JobStatus` |
|---|---|
| `DRAFT` | `OPEN` |
| All active states | `IN_PROGRESS` |
| `FINALIZED` | `COMPLETED` |
| Any canceled path | `CANCELED` |

### What is NOT a workflow state

Delivery tracking (`DELIVERED`, `EMAIL_PENDING`, `SENT`), filing events (`FILED`), and operational conditions (`OVERDUE`, `URGENT`) are derived labels or separate concerns — not core workflow states.

> **Detail:** [ll_152_workflow_state_spec.md](research/ll_152_workflow_state_spec.md)

---

## 8. Data Extension Model

The Job engine stores coarse data. The LL152 workflow stores branch-specific detail in extension tables.

### `ll152_job_details`

One-to-one with `jobs`. Contains:
- `branch_discriminator` (`STANDARD_INSPECTION` | `NO_GAS_PIPING` | `GAS_PIPING_NOT_SUPPLIED`)
- `workflow_state` (branch-aware state value)
- branch-specific payload (shape varies by branch)

### Findings storage

Findings should be stored as **structured workflow records** — not a single JSONB blob and not freeform text. Whether they are normalized rows or embedded JSONB records is an implementation decision, but the conceptual model is: one record per category per inspection.

### Photos / evidence

Photo evidence attachment design is deferred to implementation. The open question is whether photos attach to individual findings or to the job broadly.

---

## 9. Relationship to Job Engine

The Job engine remains unchanged. Per Phase 1:

- `JobType = LL152_INSPECTION` identifies the workflow
- `JobStatus` remains `OPEN → IN_PROGRESS → COMPLETED / CANCELED`
- The engine does not know about branches, findings, GPS1/GPS2, or certification outcomes

### Engine invariants preserved

- `JobType` is immutable — branch classification is workflow-layer, not a `JobType` change
- `JobStatus` is not expanded — workflow-specific progress stays in the workflow module
- The engine/workflow seam defined in `JobType_VO_Spec.md` is honored

---

## 10. Relationship to ComplianceObligation / LL152Program

The LL152 workflow lives **below** the compliance program layer.

- `LL152Program` owns: program identity, cycle schedule, timing rules, applicability
- `ComplianceObligation` owns: per-building obligation, window dates, compliance status
- `LL152 workflow` owns: how a concrete job proceeds once work begins

Deadline truth is program/policy truth first. The workflow consumes timing; it does not set compliance deadlines.

---

## 11. Invariants

### Branch invariants
1. Every LL152 workflow instance must resolve to exactly one branch.
2. Branch A is the only branch that uses the GPS1 inspection-capture flow.
3. Branch B must not be modeled as a partially completed Branch A.
4. Branch C must not be collapsed into Branch B.
5. Branch classification may change before certification; it is fixed at certification.

### Findings invariants
6. Every Branch A inspection must evaluate all five official findings categories.
7. Findings support observed / not-observed outcomes.
8. Stop conditions are a severity subset of findings, not separate concepts.
9. Freeform comments do not replace structured findings.

### State invariants
10. Workflow state is always branch-aware.
11. Workflow state is never persisted as `job_status`.
12. `FINALIZED` is the only state that maps to engine `COMPLETED`.
13. Stop conditions influence transitions but are not standalone states.

### Artifact invariants
14. GPS1 belongs only to Branch A.
15. GPS2 is the cross-branch certification/filing artifact.
16. GPS1 and GPS2 are complementary, not duplicates.

---

## 12. Open Questions

1. ~~At what moment is branch determined — intake, field execution, or review?~~ **RESOLVED:** Branch is set at intake. For alpha, every LL152 job defaults to `STANDARD_INSPECTION` automatically — no UI choice needed. The `branch_discriminator` field is stored from day one. Reclassification during field execution is architecturally supported (before certification), but is a post-alpha feature. Branch must be known before/during capture because it determines what data to collect.
2. ~~Should branch reclassification (A → C) produce an audit trail or event?~~ **RESOLVED:** Yes. Reclassification must emit a `BRANCH_RECLASSIFIED` domain event with `{from, to, reason, actor, timestamp}`. Job events are critical for compliance audit trails. Post-alpha feature — no reclassification mechanism in v1, but the decision is recorded for when B/C are added.
3. ~~Does Branch C produce a GPS2 directly, or is it a distinct statement/filing path?~~ **DEFERRED:** Branch C is post-alpha (per Q4). Insufficient operational evidence to design its artifact surface now. Will resolve when Branch C is designed, informed by field observation of gas-piping-not-supplied scenarios.
4. ~~Should v1 support all three branches, or Branch A first with B/C as deferred-but-known?~~ **RESOLVED:** Branch A first. B/C are deferred-but-known paths — the architecture accounts for them (branch discriminator enum, lighter state families), but no code or UI for B/C in alpha. If a building has no gas piping, the plumber handles it manually outside the app.
5. ~~Should `READY_FOR_REVIEW` and `UNDER_REVIEW` remain distinct, or is one a derived label?~~ **RESOLVED:** Keep both distinct. They represent a real handoff between two different people (QI → LMP). `READY_FOR_REVIEW` = QI has finished capture, package is ready to send. `UNDER_REVIEW` = LMP has opened/started reviewing. Alpha state machine stops at `READY_FOR_REVIEW` (the alpha endpoint). `UNDER_REVIEW` and all certification states are post-alpha — the LMP is not an alpha tester.
6. ~~Should findings be persisted as child entities or an embedded structured payload?~~ **RESOLVED:** Child entities in a separate `inspection_findings` table. One row per GPS1 category per job. Findings are the core product data — they deserve proper relational modeling with typed columns, NOT NULL constraints, and their own IDs. Key reason: corrections must be surgical (QI fixes one finding's photo or notes without touching others). JSONB blobs make corrections clumsy. **Related discovery:** Field observation revealed the QI often completes multiple inspections per day (one job per building), then reviews at home. The state machine must support a **recall transition** (`READY_FOR_REVIEW → CAPTURING`) so the QI can pull back and fix a submission before the LMP opens it. This avoids the pain of locked submissions that require phone calls to middle management to correct.
7. ~~Should photos attach to individual findings or to the job broadly?~~ **RESOLVED:** Both. Finding-level photos are required evidence per GPS1 category (the QI must photograph specific conditions). Job-level photos are general building/visit evidence (exterior, meter room, access points). Schema: `inspection_photos` table with a nullable `finding_id` FK — set means finding evidence, null means job-level photo. Both levels are alpha requirements. In-app camera capture recommended over camera-roll selection to prevent misattribution (field observation: QI doing 5 inspections/day accidentally attached wrong building's photo from camera roll).

---

## 13. Supporting Sub-Specs

These documents contain the detailed research and reasoning behind this synthesis:

| Sub-Spec | Purpose |
|---|---|
| [ll_152_branch_topology.md](research/ll_152_branch_topology.md) | Branch identification, entry conditions, architectural consequences |
| [gps_1_form_spec.md](research/gps_1_form_spec.md) | GPS1 section structure, data groupings, field ownership categories |
| [gps_2_certification_and_filing_branches.md](research/gps_2_certification_and_filing_branches.md) | GPS2 role across branches, certification outcome categories |
| [ll_152_findings_and_stop_conditions_spec.md](research/ll_152_findings_and_stop_conditions_spec.md) | Findings model, severity tiers, stop condition behavior |
| [ll_152_workflow_state_spec.md](research/ll_152_workflow_state_spec.md) | Branch-aware state sets, transition model, engine mapping |
| [OPEN_DESIGN_QUESTIONS.md](OPEN_DESIGN_QUESTIONS.md) | Parking lot for deferred design questions |
