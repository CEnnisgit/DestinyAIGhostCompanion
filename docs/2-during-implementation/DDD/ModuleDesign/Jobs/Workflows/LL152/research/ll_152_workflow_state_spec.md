# LL152 Workflow State Specification

**Version:** 0.1.0  
**Status:** Draft  
**Module:** Job Workflows — LL152  
**Branches:** All (branch-aware state families)  
**Parent Aggregate:** `Job`  
**Related Specs:** `ll_152_branch_topology.md`, `gps_1_form_spec.md`, `gps_2_certification_and_filing_branches.md`, `ll_152_findings_and_stop_conditions_spec.md`

---

## Objective

This spec defines the **workflow-layer state model** for the LL152 workflow family.

It exists to answer these questions:

1. What states exist inside the LL152 workflow layer?
2. How do those states differ from engine `JobStatus`?
3. How should state vary by LL152 branch?
4. How do findings, review, correction, and certification outcomes influence state progression?
5. Which states are true domain states versus derived operational labels?
6. How should workflow state map back to the coarse Job engine lifecycle?

---

## 1. Core Decision

The LL152 workflow owns its **own branch-aware state model**.

This state model is richer than engine `JobStatus`, but it does **not** replace the engine lifecycle.

### Engine / workflow split

- `JobStatus` remains the engine-level answer to: **is this work open, active, finished, or dead?**
- LL152 workflow state answers: **where is this job inside the LL152 process for its branch?**

### Consequence

Branch-specific progress such as:
- capture in progress,
- under review,
- returned for revision,
- correction pending,
- certification ready,
- finalized,

belongs in the LL152 workflow layer, not in `JobStatus`.

---

## 2. What This Spec Is

This spec defines:

- the first-pass workflow state families for the LL152 workflow;
- the difference between Branch A, Branch B, and Branch C progression;
- the mapping from workflow state to engine `JobStatus`;
- and the rules for which state concepts should remain outside the core state machine.

---

## 3. What This Spec Is Not

This spec does **not** define:

- every form field;
- every filing implementation detail;
- email/report delivery tracking;
- the owner-facing delivery queue;
- or all authorization policy.

This spec also does **not** redefine `JobStatus`.

---

## 4. Relationship to Job Engine

Per Phase 1, engine `JobStatus` is closed and generic:
- `OPEN`
- `IN_PROGRESS`
- `COMPLETED`
- `CANCELED`

The LL152 workflow must map into those states without expanding them.

### Invariant

Workflow state must not be persisted as `job_status`.

### Invariant

Workflow state may be richer than engine state, but engine state remains the only generic lifecycle state the Job aggregate exposes.

---

## 5. Relationship to Branch Topology

The LL152 workflow family contains three sub-branches:
- `STANDARD_INSPECTION`
- `NO_GAS_PIPING`
- `GAS_PIPING_NOT_SUPPLIED`

These branches do not share the same capture complexity.

### Consequence

The workflow state model should be **branch-aware**, not branch-blind.

### Design rule

Branch A gets the richest workflow state path.

Branches B and C should have lighter state families unless later evidence shows they require more complexity.

---

## 6. State Modeling Principles

### 6.1 True states vs derived labels

A workflow state should exist only when it represents a real domain checkpoint with behavioral consequences.

Examples of true workflow states:
- data capture is in progress;
- the package is under LMP review;
- the work was returned for revision;
- correction certification is still pending;
- the workflow is fully finalized.

Examples of likely derived labels, not core states:
- email pending;
- ready to send;
- overdue filing;
- waiting on owner;
- urgent.

These should usually be modeled as derived operational views, not workflow-state values.

### 6.2 Branch-specific workflow states are allowed

A branch may support state values that are not meaningful in another branch.

### 6.3 Workflow state is owned by the workflow module

The engine should not care whether a job is:
- under review,
- correction pending,
- or in a statement collection path.

That is workflow-owned meaning.

---

## 7. Branch A — Standard Inspection State Family

Branch A is the canonical and most detailed LL152 workflow path.

### 7.1 First-pass state set

The first-pass Branch A workflow state set should be:

1. `DRAFT`
2. `CAPTURING`
3. `READY_FOR_REVIEW`
4. `UNDER_REVIEW`
5. `RETURNED`
6. `CERTIFICATION_NO_CORRECTION`
7. `CERTIFICATION_CORRECTION_REQUIRED`
8. `CERTIFICATION_CORRECTION_PENDING`
9. `FINALIZED`

### 7.2 Meaning of each state

#### `DRAFT`
A workflow instance exists, but structured LL152 capture has not materially begun.

#### `CAPTURING`
Inspection/report data is actively being captured or edited.

#### `READY_FOR_REVIEW`
Capture is considered complete enough to hand to the LMP/reviewer.

#### `UNDER_REVIEW`
The LMP or authorized reviewer is actively reviewing the Branch A packet.

#### `RETURNED`
The review found issues or missing data and sent the work back for revision.

#### `CERTIFICATION_NO_CORRECTION`
Review is complete and the certification outcome is that no correction is required.

#### `CERTIFICATION_CORRECTION_REQUIRED`
Review/certification has concluded that conditions requiring correction were identified.

#### `CERTIFICATION_CORRECTION_PENDING`
A correction-required path exists and one or more conditions remain unresolved or require additional time.

#### `FINALIZED`
The workflow-side LL152 package is complete from the branch’s perspective.

### 7.3 Why this shape

This state family reflects the separation already established by the Phase 2 specs:
- GPS1 owns report/capture structure;
- findings own observed/correction/immediate-report meaning;
- GPS2 owns certification/filing outcomes.

### 7.4 What is intentionally excluded

Branch A workflow state does **not** include:
- `DELIVERED`
- `EMAIL_PENDING`
- `FILED`
- `OVERDUE`

Those are either:
- report-delivery concerns,
- filing event facts,
- or derived operational conditions.

---

## 8. Branch B — No Gas Piping State Family

Branch B is a certification-oriented path, not a capture-heavy inspection path.

### 8.1 First-pass state set

The first-pass Branch B workflow state set should be:

1. `DRAFT`
2. `CERTIFICATION_READY`
3. `FINALIZED`

### 8.2 Meaning

#### `DRAFT`
The branch has been identified, but certification data is not yet ready.

#### `CERTIFICATION_READY`
The no-gas-piping certification path has enough data to prepare/submit the relevant certification artifact.

#### `FINALIZED`
The branch workflow is complete from the workflow’s perspective.

### 8.3 Important note

Branch B should remain intentionally light unless later evidence shows that it requires a richer review loop.

---

## 9. Branch C — Gas Piping Present but Not Supplied State Family

Branch C is a statement-centered path and remains the least settled.

### 9.1 First-pass state set

The first-pass Branch C workflow state set should be:

1. `DRAFT`
2. `STATEMENTS_PENDING`
3. `STATEMENTS_READY`
4. `FINALIZED`

### 9.2 Meaning

#### `DRAFT`
The branch has been identified, but required statement inputs are not yet assembled.

#### `STATEMENTS_PENDING`
One or more required statements or statement-linked workflow facts are still outstanding.

#### `STATEMENTS_READY`
The branch has enough statement evidence to prepare the required filing path.

#### `FINALIZED`
The branch workflow is complete from the workflow’s perspective.

### 9.3 Important note

This branch remains more provisional than Branch A and should be revisited once more operational evidence exists.

---

## 10. Branch A Transition Model

### 10.1 Valid first-pass transitions

| From | To | Meaning |
|---|---|---|
| `DRAFT` | `CAPTURING` | Actual workflow capture begins |
| `CAPTURING` | `READY_FOR_REVIEW` | Capture package is complete enough for review |
| `READY_FOR_REVIEW` | `UNDER_REVIEW` | Reviewer begins review |
| `UNDER_REVIEW` | `RETURNED` | Review rejects current package and sends back for revision |
| `RETURNED` | `CAPTURING` | Revision work resumes |
| `UNDER_REVIEW` | `CERTIFICATION_NO_CORRECTION` | Review concludes no correction is required |
| `UNDER_REVIEW` | `CERTIFICATION_CORRECTION_REQUIRED` | Review concludes correction is required |
| `CERTIFICATION_CORRECTION_REQUIRED` | `CERTIFICATION_CORRECTION_PENDING` | Additional time / unresolved correction path is active |
| `CERTIFICATION_CORRECTION_REQUIRED` | `FINALIZED` | Correction-related certification is complete without pending state |
| `CERTIFICATION_CORRECTION_PENDING` | `FINALIZED` | Correction path is complete |
| `CERTIFICATION_NO_CORRECTION` | `FINALIZED` | No-correction certification path is complete |

### 10.2 Notable exclusions

This first-pass model does **not** introduce:
- a separate `SUBMITTED` state distinct from `READY_FOR_REVIEW`;
- a separate `APPROVED` state distinct from certification outcomes;
- or a `DELIVERED` state.

These may still appear later as derived labels or separate report-side concepts, but they are not necessary in the first branch-aware workflow-state model.

---

## 11. Stop Condition Interaction

A stop condition is not itself a workflow state.

It is a finding-level severity/escalation fact that can influence state transitions.

### Consequence

Stop conditions may:
- force review attention;
- block certain workflow completions;
- require explicit narrative detail;
- and affect whether the workflow can progress to certification-ready outcomes.

### Design rule

Model stop conditions as **guards and workflow consequences**, not as standalone state values.

---

## 12. Mapping to Engine `JobStatus`

The first-pass workflow-to-engine mapping should be:

| Workflow state | Engine `JobStatus` |
|---|---|
| `DRAFT` | `OPEN` |
| `CAPTURING` | `IN_PROGRESS` |
| `READY_FOR_REVIEW` | `IN_PROGRESS` |
| `UNDER_REVIEW` | `IN_PROGRESS` |
| `RETURNED` | `IN_PROGRESS` |
| `CERTIFICATION_READY` | `IN_PROGRESS` |
| `CERTIFICATION_NO_CORRECTION` | `IN_PROGRESS` |
| `CERTIFICATION_CORRECTION_REQUIRED` | `IN_PROGRESS` |
| `CERTIFICATION_CORRECTION_PENDING` | `IN_PROGRESS` |
| `STATEMENTS_PENDING` | `IN_PROGRESS` |
| `STATEMENTS_READY` | `IN_PROGRESS` |
| `FINALIZED` | `COMPLETED` |
| any canceled branch path | `CANCELED` |

### Consequence

The workflow may reach many meaningful internal milestones while the engine still simply sees `IN_PROGRESS`.

---

## 13. Relationship to Delivery Tracking

Report delivery is not part of the core LL152 workflow-state machine.

### Consequence

States such as:
- `DELIVERED`
- `EMAIL_PENDING`
- `SENT`

should not be added to the LL152 core workflow state family merely to track downstream report distribution.

Those belong in a report/delivery model or as derived operational views.

---

## 14. Relationship to GPS2

The certification-oriented states in this spec are intentionally derived from the branch-sensitive GPS2 outcomes:
- no correction required;
- correction required;
- correction pending / additional time;
- correction complete / finalized.

### Invariant

Workflow certification states must remain richer than engine completion state, but they must not become a second engine lifecycle.

---

## 15. Relationship to Findings

Findings are workflow evidence, not states.

### Consequence

Findings influence:
- review outcomes;
- whether correction is required;
- whether stop conditions exist;
- and whether the workflow can move into a certification outcome state.

But the workflow state machine should not be replaced by findings categories.

---

## 16. First-Pass Workflow Invariants

1. Workflow state is always interpreted in the context of exactly one branch.
2. Branch A may have a richer state family than Branch B or Branch C.
3. Workflow state must not be persisted as `job_status`.
4. `FINALIZED` is the only workflow-side completion state that maps to engine `COMPLETED`.
5. Delivery/report-sending concepts are outside the core LL152 workflow-state family.
6. Stop conditions influence transitions but are not standalone workflow states.
7. Branch B and Branch C should remain lighter unless future evidence proves otherwise.

---

## 17. Open Questions

1. Should `READY_FOR_REVIEW` and `UNDER_REVIEW` remain distinct states, or is one of them only an operational queue label?
2. Should `CERTIFICATION_CORRECTION_REQUIRED` and `CERTIFICATION_CORRECTION_PENDING` both exist, or can one be derived from structured correction data?
3. Does Branch B require a distinct review state in practice, or is `CERTIFICATION_READY` enough?
4. Does Branch C require more explicit intermediate states once statement collection is better understood?
5. At what exact moment should the engine transition from `OPEN` to `IN_PROGRESS` — first capture activity, explicit start action, or branch activation?
6. Is `FINALIZED` always the correct workflow-side completion moment, or should some branches distinguish between finalized and filed?

---

## 18. Follow-On Work

This sub-spec has been converged into:

**[LL152_Inspection_Workflow.md](LL152_Inspection_Workflow.md)** — the Phase 2 synthesis document.

Implementation decisions (enum storage, guard sets, command lists) will be resolved during coding.

---

## 19. Current Recommendation

Model LL152 workflow state as a **branch-aware workflow-layer state machine** that remains separate from engine `JobStatus`.

Use:
- a rich Branch A state family,
- lighter Branch B and Branch C families,
- `FINALIZED` as the workflow-side completion point,
- and keep delivery/report-sending outside the core state machine.

