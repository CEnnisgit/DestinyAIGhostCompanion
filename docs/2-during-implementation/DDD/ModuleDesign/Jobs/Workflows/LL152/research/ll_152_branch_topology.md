# LL152 Branch Topology Specification

**Version:** 0.1.0  
**Status:** Draft  
**Module:** Job Workflows — LL152  
**Parent Aggregate:** `Job`  
**Related Engine Spec:** `Job_Aggregate.md`

---

## Objective

This spec exists to settle the **topology of the LL152 workflow** before designing form schemas, findings models, or workflow states.

It is intended to answer one foundational question:

> Is LL152 a single workflow with minor branches, or multiple materially different compliance paths that share the same program identity?

This matters because the answer determines:

1. whether `GPS1_Form_Spec.md` applies to the whole LL152 domain or only to one branch;
2. whether `ll152_job_details` should represent one generic workflow payload or branch-specific shapes;
3. how workflow state should be modeled;
4. what data is required at intake; and
5. whether certain LL152 jobs should exist at all in the Job engine.

---

## 1. Core Decision

LL152 is **not** one single linear inspection workflow.

It is best modeled as **one workflow family under one `JobType` (`LL152_INSPECTION`) with three workflow-owned sub-branches**:

1. **Standard Inspection Branch**
   - building contains gas piping;
   - building is currently supplied with gas;
   - standard inspection is performed.

2. **No Gas Piping Branch**
   - building contains **no gas piping system**;
   - compliance is satisfied through certification of no gas piping.

3. **Gas Piping Present but Not Supplied Branch**
   - building contains gas piping;
   - building is **not currently supplied with gas**;
   - no gas utilization equipment is connected;
   - compliance is handled through required statements rather than the standard inspection path.

### Architectural meaning

These are **not just small flags on one form flow**.

They are three materially different compliance paths that share:

- the same legal/program identity (`LL152`),
- the same building/program obligation context,
- the same Job-engine surface (`JobType = LL152_INSPECTION`),
- and some overlapping filing concepts,

but they do **not** share the same capture requirements.

### Resolution

These branches should be modeled as **sub-branches inside one LL152 workflow module**, **not** as separate top-level workflow implementations and **not** as separate `JobType` values.

Why:
- DOB treats them as one LL152 compliance universe.
- A single `ComplianceObligation` should still map cleanly to a single LL152 job family.
- `JobType` is immutable, while branch classification may be learned or corrected later.
- Branches B and C are materially different from Branch A, but not weighty enough to justify separate engine/workflow implementations.

---

## 2. What This Spec Is

This spec defines:

- the three public LL152 branches;
- the criteria that place a building/job into each branch;
- which official artifacts are relevant in each branch;
- which branch is the true home of the GPS1 workflow;
- and the architectural consequences for Phase 2 specs.

---

## 3. What This Spec Is Not

This spec does **not** define:

- every GPS1 field;
- every GPS2 field;
- findings storage design;
- photo evidence rules;
- review workflow details;
- deliverable packet composition;
- or the complete LL152 workflow state machine.

Those follow after the branch topology is settled.

---

## 4. Authorities

Every branch rule in this spec must trace back to DOB-published materials.

### Primary authorities

- `1 RCNY §103-10`
- DOB LL152 Gas Piping Inspections guidance page
- DOB LL152 FAQ page
- official DOB `GPS1` form
- official DOB `GPS2` form

### Interpretation rule

If future field observation conflicts with DOB-published rules, the system must distinguish:
- **public compliance truth**;
- **common office practice**;
- and **company-specific shortcut behavior**.

This topology spec is grounded in **public compliance truth**.

---

## 5. Branch Definitions

### 5.1 Branch A — Standard Inspection Branch

### Entry condition

Use this branch when:
- the building contains gas piping; and
- the building is currently supplied with gas.

### Core meaning

This is the **main LL152 inspection workflow**.

It is the branch where:
- a qualified inspection is actually performed;
- the inspection report is produced;
- inspection findings are recorded;
- correction/no-correction outcomes matter;
- and the standard report/certification timing windows apply.

### Primary artifacts

- `GPS1` inspection report
- `GPS2` certification
- findings / comments
- possible correction follow-up

### Product consequence

This is the branch that should drive:
- `GPS1_Form_Spec.md`
- `Findings_Evidence_Spec.md`
- `Stop_Conditions_Spec.md`
- and the first true `LL152_Workflow_State_Spec.md`

### Design classification

This is the **canonical LL152 workflow branch** for Phase 2 workflow design.

---

### 5.2 Branch B — No Gas Piping Branch

### Entry condition

Use this branch when:
- the building contains **no gas piping system**.

### Core meaning

This is **not** the standard inspection path.

The building is still within the LL152 compliance universe, but compliance is satisfied by certifying that the building has no gas piping system.

### Primary artifact

- `GPS2` no-gas-piping certification path

### GPS1 relationship

`GPS1` is **not** the primary artifact of this branch.

This branch should not be modeled as “standard inspection with most fields blank.”

### Product consequence

This branch likely requires:
- a much smaller workflow payload;
- certification-oriented handling;
- and separate branch logic from the standard inspection flow.

### Design classification

This is a **certification branch**, not a capture-heavy inspection branch.

---

### 5.3 Branch C — Gas Piping Present but Not Supplied Branch

### Entry condition

Use this branch when:
- the building contains gas piping;
- the building is **not currently supplied with gas**; and
- no gas utilization equipment is connected to that piping.

### Core meaning

This is also **not** the standard inspection path.

Compliance is handled through required statements rather than the standard inspection/report flow.

### Primary artifacts

- utility statement
- owner statement
- DOB portal submission behavior

### GPS1 relationship

`GPS1` is **not** the governing artifact of this branch.

### GPS2 relationship

This branch is not the same as the no-gas-piping branch.

It should not be collapsed into Branch B, because:
- gas piping still exists;
- the compliance fact pattern is different;
- and the required evidence is different.

### Product consequence

This branch likely requires:
- a separate branch payload;
- a separate filing-state path;
- and workflow logic centered on statement collection rather than field inspection findings.

### Design classification

This is a **non-supplied gas-piping branch**, distinct from both standard inspection and no-gas-piping certification.

---

## 6. Branch Comparison Table

| Aspect | Branch A — Standard Inspection | Branch B — No Gas Piping | Branch C — Gas Piping Present, Not Supplied |
|---|---|---|---|
| Gas piping exists? | Yes | No | Yes |
| Gas currently supplied? | Yes | No | No |
| Standard inspection performed? | Yes | No | No |
| GPS1 relevant? | Yes — core artifact | No — not the primary path | No — not the primary path |
| GPS2 relevant? | Yes | Yes | Possibly as part of compliance path, but not the same as Branch B |
| Findings model needed? | Yes | No or minimal | No standard findings model |
| Statement-based path? | No | No-gas certification | Yes |
| Main product shape | Inspection workflow | Certification workflow | Statement / filing workflow |

---

## 7. Primary Architectural Consequences

### 7.1 GPS1 applies to Branch A, not the whole LL152 domain

`GPS1_Form_Spec.md` should be written as the form spec for the **Standard Inspection Branch**.

It should not be treated as the universal form schema for all LL152 compliance cases.

---

### 7.2 Phase 2 must split capture-heavy vs certification-heavy paths

The first LL152 workflow work should focus on the branch that actually produces inspection findings.

That means:
- Branch A first;
- Branch B and Branch C as separate branch specs or sub-specs.

---

### 7.3 Branch topology comes before workflow state design

Workflow-state design cannot be correct until branch topology is settled.

Why:
- Branch A includes true inspection progress and review behavior.
- Branch B is largely certification-oriented.
- Branch C is statement-oriented.

A single state machine covering all three without prior topology work would likely be muddy and assumption-heavy.

---

### 7.4 `ll152_job_details` must not assume one payload shape for all branches

If a Job of type `LL152_INSPECTION` can enter multiple branches, then the extension model must account for branch differences.

At minimum, the workflow layer likely needs an explicit branch discriminator such as:
- `STANDARD_INSPECTION`
- `NO_GAS_PIPING`
- `GAS_PIPING_NOT_SUPPLIED`

This is a workflow-layer discriminator, not a `JobType` change.

### Recommended shape

```text
JobType = LL152_INSPECTION
  └── LL152 workflow module
        ├── branch_discriminator
        ├── Branch A path (capture-heavy, GPS1, findings, review, GPS2)
        ├── Branch B path (no-gas-piping certification)
        └── Branch C path (statement-collection / filing path)
```

The engine sees one `LL152_INSPECTION` job family.
The workflow owns branch determination, branch-specific payload shape, and branch-specific progress logic.

---

### 7.5 Deadline truth remains program/policy truth first

The three-branch topology does not change the architectural principle that LL152 deadline truth is fundamentally program/policy truth.

The workflow consumes branch-relevant timing and filing requirements, but should not become the root authority for the LL152 compliance schedule.

---

## 8. Relationship to Job Engine

The Job engine remains unchanged.

Per Phase 1 design:
- `JobType = LL152_INSPECTION` still identifies the governing workflow family;
- `JobStatus` remains generic (`OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELED`);
- branch-specific progress belongs in the LL152 workflow layer.

### Engine implication

The Job engine should not encode:
- `NO_GAS_PIPING`
- `NOT_SUPPLIED`
- `UNDER_REVIEW`
- `CORRECTION_PENDING`
- `DELIVERED`

Those belong to branch-specific LL152 workflow behavior.

---

## 9. Relationship to ComplianceObligation / LL152Program

The topology in this spec lives **below** the compliance program layer.

### `LL152Program` owns
- program identity;
- cycle/subcycle schedule;
- public compliance timing rules;
- policy-level applicability model.

### `ComplianceObligation` owns
- per-building obligation instance;
- window dates and compliance facts;
- obligation status derived from evidence + schedule.

### `LL152 workflow branch topology` owns
- how a concrete LL152 job proceeds once work is being done for a particular branch path.

This means:
- branch topology is **not** a replacement for obligation status;
- and not every obligation necessarily implies the same capture workflow.

---

## 10. Invariants

1. Every LL152 workflow instance must resolve to exactly one branch.
2. Branch A is the only branch that owns the standard GPS1 inspection-capture flow.
3. Branch B must not be modeled as a partially completed Branch A workflow.
4. Branch C must not be collapsed into Branch B merely because gas is not currently supplied.
5. Branch topology is workflow-layer meaning, not Job-engine lifecycle meaning.
6. A change in branch meaning changes workflow behavior, not `JobType`.

---

## 11. Follow-on Specs

All five sub-specs have been completed and converged into:

**[LL152_Inspection_Workflow.md](LL152_Inspection_Workflow.md)** — the Phase 2 synthesis document.

Branch entry/discrimination rules are addressed in §3 of the synthesis doc.

---

## 12. Open Questions

1. ~~At what moment is branch determined?~~ **RESOLVED (2026-03-27):** Set at intake, defaulting to `STANDARD_INSPECTION`. Reclassification during field execution is architecturally supported (before certification) but is post-alpha. Review-time determination is ruled out — branch must be known before/during capture.

2. ~~Can a Branch A job later resolve into Branch C if supply assumptions were wrong, or should the workflow support branch reclassification inside the same job?~~ **RESOLVED (2026-03-27):** Yes, reclassification is supported architecturally (before certification). Must emit a `BRANCH_RECLASSIFIED` domain event for audit trail. Post-alpha feature — alpha is Branch A only.

3. ~~Does Branch C ever produce a GPS2 artifact directly in the same way as Branch B, or should it be modeled as a statement-only path with separate filing evidence?~~ **DEFERRED (2026-03-27):** Branch C is post-alpha. Insufficient real-world evidence to decide. Will resolve during Branch C design phase.

4. ~~Should the initial product support all three branches in v1, or support Branch A first and explicitly mark Branch B/C as deferred-but-known paths?~~ **RESOLVED (2026-03-27):** Branch A first. B/C are deferred-but-known. Architecture supports future extension via branch discriminator enum. Alpha users handle B/C buildings manually outside the app.

---

## 13. Current Recommendation

For Phase 2 progression:

- keep **one `JobType`**: `LL152_INSPECTION`;
- model **three workflow-owned sub-branches** inside the LL152 workflow module;
- treat **Branch A** as the first fully designed workflow branch;
- treat **Branch B** and **Branch C** as known distinct branches that must not be collapsed into Branch A;
- and design all later LL152 specs with explicit branch awareness.

This preserves correctness without fragmenting LL152 into multiple top-level workflow implementations.

