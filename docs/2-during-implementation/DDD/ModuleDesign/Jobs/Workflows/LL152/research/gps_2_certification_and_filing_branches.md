# GPS2 Certification and Filing Branches Specification

**Version:** 0.1.0  
**Status:** Draft  
**Module:** Job Workflows — LL152  
**Branches:** All (`STANDARD_INSPECTION`, `NO_GAS_PIPING`, `GAS_PIPING_NOT_SUPPLIED`)  
**Parent Aggregate:** `Job`  
**Related Engine Spec:** `Job_Aggregate.md`  
**Related Topology:** `ll_152_branch_topology.md`

---

## Objective

This spec defines the role of the official `GPS2` artifact across the LL152 workflow family.

It exists to answer these questions:

1. What is `GPS2` in the LL152 domain?
2. How does `GPS2` differ from `GPS1`?
3. Which branches use `GPS2`, and in what way?
4. What filing/certification outcomes does `GPS2` express?
5. What should the product model as branch-specific certification behavior versus generic workflow behavior?
6. What architectural boundary should exist between `GPS2`, the Job engine, and the obligation/program layer?

---

## 1. Core Decision

`GPS2` is the **certification / filing artifact** of the LL152 workflow family.

It is not the same kind of artifact as `GPS1`.

### Summary distinction

- `GPS1` = inspection report artifact for the **Standard Inspection Branch**
- `GPS2` = certification / filing artifact that spans multiple LL152 compliance branches

### Architectural meaning

`GPS2` should be treated as:
- a workflow-owned certification artifact;
- the primary cross-branch filing surface in the LL152 family;
- and a branch-sensitive artifact whose meaning changes depending on the compliance path.

It should **not** be modeled as:
- a second inspection-capture form;
- a generic Job-engine concept;
- or a universal substitute for branch-specific workflow meaning.

---

## 2. What This Spec Is

This spec defines:

- the role of `GPS2` in the LL152 workflow family;
- the branch-specific ways in which `GPS2` is used;
- the major certification outcomes visible on the official form;
- the first public-evidence interpretation of filing branches;
- and the architectural consequences for later workflow specs.

---

## 3. What This Spec Is Not

This spec does **not** define:

- every visual field on the official `GPS2` form;
- the full review-state machine;
- the entire portal submission experience;
- all downstream owner-delivery behavior;
- or the complete filing implementation contract.

It also does **not** replace:
- `LL152_Branch_Topology.md`;
- `GPS1_Form_Spec.md`;
- or future findings / review / deliverable specs.

---

## 4. Artifact Role in the Workflow Family

### 4.1 What GPS2 is

`GPS2` is the official **Gas Piping System Periodic Inspection Certification** artifact.

Within the product model, it should be treated as the branch-sensitive certification/filing surface that expresses compliance outcomes to DOB.

### Product meaning

`GPS2` is where the LL152 workflow family reaches a formal certification state.

It is closer to:
- certification,
- filing,
- and compliance outcome expression,

than to field capture.

---

### 4.2 What GPS2 is not

`GPS2` is not:
- the full inspection narrative;
- the primary findings container;
- the generic Job payload;
- or the Job engine’s completion model.

---

### 4.3 Relationship to GPS1

`GPS1` and `GPS2` are related but non-identical artifacts.

### `GPS1`
- inspection-report oriented
- Branch A only
- findings-centered
- owner-facing report artifact

### `GPS2`
- certification/f filing oriented
- cross-branch relevance
- branch-outcome centered
- DOB submission artifact

### Invariant

`GPS2` must not be modeled as a richer duplicate of `GPS1`.

---

## 5. Branch Applicability

### 5.1 Branch A — Standard Inspection Branch

### Role of GPS2

In Branch A, `GPS2` expresses the certification outcome of the standard inspection path.

This includes at least these visible public-form branches:
- no conditions requiring correction were identified;
- conditions requiring correction were identified;
- correction of one or more conditions will take additional time;
- all identified conditions have been corrected.

### Meaning

In Branch A, `GPS2` should be treated as the certification/filing counterpart to the inspection work represented by `GPS1`.

### Product consequence

Branch A likely needs:
- a relationship between inspection findings/report state and certification state;
- filing readiness rules;
- and branch-specific certification transitions.

---

### 5.2 Branch B — No Gas Piping Branch

### Role of GPS2

In Branch B, `GPS2` is the primary certification artifact for the “no gas piping system” compliance path.

### Meaning

This branch is not a simplified Branch A inspection.

Instead, `GPS2` itself becomes the central public compliance artifact.

### Product consequence

Branch B likely requires:
- minimal workflow payload;
- branch-specific certification state;
- and no standard findings/report model comparable to Branch A.

### Invariant

Branch B must not be modeled as Branch A with empty findings.

---

### 5.3 Branch C — Gas Piping Present but Not Supplied Branch

### Role of GPS2

Branch C is the least settled of the three branches at the workflow level.

Public evidence indicates that this branch is handled through required statements rather than the standard inspection path.

### Current interpretation

At the public-evidence stage, Branch C should be treated as:
- a statement-centered compliance path;
- distinct from Branch A;
- and distinct from the “no gas piping” certification path of Branch B.

### GPS2 relationship

It remains unresolved whether `GPS2` is always directly used in Branch C in the same operational manner as Branch B, or whether Branch C is better modeled as a statement/filing path that intersects with certification logic differently.

### Product consequence

Branch C should remain explicitly branch-aware and should not be collapsed into either:
- Branch A’s standard inspection/certification pair; or
- Branch B’s no-gas-piping certification path.

---

## 6. Public Form Outcome Categories

The official `GPS2` form visibly expresses at least these certification outcomes:

1. **No gas piping system**
2. **No conditions requiring correction were identified**
3. **Conditions requiring correction were identified**
4. **Correction of one or more conditions will take additional time**
5. **All conditions identified have been corrected**

### Architectural meaning

These are not merely checkbox renderings.

They are the first public evidence of the certification/filing branches that the workflow must support.

### 6.1 Detailed Field Inventory (From GPS2 PDF)

The official form requires the following specific fields per section:

**1. LOCATION INFORMATION (required for all certifications)**
*   House No(s), Street Name, Owner Name
*   Borough, Block, Lot, BIN, Community Board No.
*(Note: GPS2 omits the 'Number of Stories' and 'Number of Meters' fields found on GPS1)*

**2. LICENSED MASTER PLUMBER INFORMATION**
*   Name: Last Name, First Name, Middle Initial
*   Business Name, Business Phone, Business Fax
*   Business Address, City, State, Zip
*   Mobile Phone, Email, License Number

**3. INDIVIDUAL PERFORMING INSPECTION (QUALIFIED INDIVIDUAL)**
*   Name: Last Name, First Name, Middle Initial
*   Business Name, Business Phone, Business Fax
*   Business Address, City, State, Zip
*   Mobile Phone, Email, Employer Name

**4. CERTIFICATION OF NO GAS PIPING SYSTEM**
*   Checkbox: "I certify that the above building contains no gas piping system. (proceed to Section 6 if box is checked)"

**5. CERTIFICATION OF INSPECTION (to be completed by LMP)**
*   Checkbox: Personally performed inspection
*   Checkbox: Exercised direct and continuing supervision over individual in Section 3
*   Text input: "Date of initial inspection (MM/DD/YYYY):"
*   Checkboxes for Outcomes:
    *   No conditions requiring correction were identified
    *   Conditions requiring correction were identified
    *   Correction of conditions will take additional time (180 days)
    *   All identified conditions have been corrected

**6. STATEMENTS AND SIGNATURES (required for all certifications)**
*   Name (printed), Date
*   Affix seal and signature

---

## 7. First-Pass Filing Branch Model

At the current evidence level, the LL152 workflow family should likely recognize these certification/filing outcomes:

### A. No-gas-piping certification path
- tied to Branch B
- minimal compliance-certification path

### B. Standard inspection, no-correction outcome
- tied to Branch A
- inspection completed;
- certification states that no correction is required

### C. Standard inspection, correction-required outcome
- tied to Branch A
- certification states that conditions requiring correction were found

### D. Standard inspection, correction-pending / additional-time outcome
- tied to Branch A
- certification states that one or more conditions will take additional time to correct

### E. Standard inspection, correction-completed outcome
- tied to Branch A
- certification states that all identified conditions have been corrected

### F. Statement-centered non-supplied-gas path
- tied to Branch C
- public branch known;
- exact GPS2 interaction still requires further clarification

---

## 8. Workflow Meaning vs Program / Obligation Meaning

### 8.1 What belongs to program / obligation truth

The following remain primarily policy/compliance-layer truth:
- official timing windows;
- filing deadlines;
- cycle/subcycle schedule;
- obligation due windows;
- legal applicability of LL152.

### 8.2 What belongs to workflow meaning

The following belong to the workflow layer:
- which branch the job is in;
- whether the job has produced the certification inputs needed for `GPS2`;
- which certification outcome path applies;
- whether correction-related certification states have been reached;
- and whether the workflow has enough information to render/prepare the certification artifact.

### Invariant

`GPS2` certification logic should consume compliance timing truth, but should not become the root authority for deadline policy.

---

## 9. Relationship to Job Engine

The Job engine remains unchanged.

The engine should not know:
- which `GPS2` outcome applies;
- whether corrections were required;
- whether additional time is needed;
- whether the branch is no-gas-piping versus statement-centered;
- or whether filing has occurred.

### Engine scope

The engine only knows:
- a Job of type `LL152_INSPECTION` exists;
- it remains in a coarse engine lifecycle;
- and the LL152 workflow layer carries the certification/filing meaning.

### Invariant

Certification/filing outcomes must not be added to `JobStatus`.

---

## 10. Relationship to Branch Topology

This spec depends directly on `LL152_Branch_Topology.md`.

### Important consequence

If branch topology is ignored, `GPS2` will be overgeneralized in one of two bad ways:
- treated as if it only belongs to Branch A; or
- treated as if all branches use it identically.

Both are incorrect.

---

## 11. Relationship to Future Specs

This spec should feed directly into:

1. `LL152_Findings_and_Stop_Conditions_Spec.md`
2. `LL152_Workflow_State_Spec.md`
3. `LL152_Deliverable_Packet_Spec.md`
4. future filing / submission implementation notes

### Dependency effect

Workflow-state design should be informed by the certification/filing branches identified here, not just by the field-capture/report path of `GPS1`.

---

## 12. Invariants

1. `GPS2` is a certification/filing artifact, not a second inspection form.
2. `GPS2` has cross-branch relevance within the LL152 workflow family.
3. Branch B uses `GPS2` differently from Branch A.
4. Branch C must remain explicitly distinct from both Branch A and Branch B.
5. Certification/filing outcomes must remain workflow-layer meaning, not Job-engine lifecycle meaning.
6. `GPS2` consumes compliance truth; it does not replace program/obligation authority.

---

## 13. Open Questions

1. What exact section/field inventory should be modeled from the official `GPS2` form?
2. Which certification outcomes should be represented as explicit internal workflow states versus render-time outcomes?
3. Does Branch C produce a first-class `GPS2` artifact in all cases, or should it be modeled primarily as a statement/filing path with separate evidence structures?
4. Which dates associated with `GPS2` need first-class domain modeling?
5. Should correction-related certification outcomes be represented as a dedicated workflow sub-state family inside Branch A?
6. What data must already exist before the system can generate or prepare `GPS2` for filing?

---

## 14. Follow-On Work

This sub-spec has been converged into:

**[LL152_Inspection_Workflow.md](LL152_Inspection_Workflow.md)** — the Phase 2 synthesis document.

Field inventory expansion will occur during implementation.

---

## 15. Current Recommendation

Treat `GPS2` as the **cross-branch certification/filing artifact** of the LL152 workflow family.

Use it to model:
- branch-sensitive certification outcomes,
- correction/no-correction filing paths,
- and the distinction between inspection reporting (`GPS1`) and compliance certification/filing (`GPS2`).

