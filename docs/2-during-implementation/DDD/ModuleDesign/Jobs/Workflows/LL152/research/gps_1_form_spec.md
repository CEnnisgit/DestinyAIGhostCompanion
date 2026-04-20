# GPS1 Form Specification

**Version:** 0.1.0  
**Status:** Draft  
**Module:** Job Workflows — LL152  
**Branch:** `STANDARD_INSPECTION` (Branch A only)  
**Parent Aggregate:** `Job`  
**Related Engine Spec:** `Job_Aggregate.md`  
**Related Topology:** `ll_152_branch_topology.md`

---

## Objective

This spec defines the **public-evidence-first model** of the official `GPS1` artifact used in the LL152 Standard Inspection Branch.

It exists to answer these questions:

1. What is `GPS1` in the LL152 workflow?
2. Which workflow branch owns it?
3. What major sections does it contain?
4. What categories of data does it require?
5. What does the form imply about the first findings model?
6. What fields are clearly public/form-defined versus still unresolved operationally?

This spec is intentionally limited to the **official form layer**.

---

## 1. Core Decision

`GPS1` is the **inspection report artifact** for the **Standard Inspection Branch** of the LL152 workflow.

It is **not** the universal form for all LL152 compliance paths.

It applies only when:
- the building contains gas piping; and
- the building is currently supplied with gas; and
- a standard periodic gas piping inspection is actually performed.

### Architectural meaning

`GPS1` belongs to:
- the `LL152_INSPECTION` workflow family;
- specifically the `STANDARD_INSPECTION` sub-branch;
- and should not be imposed on the `NO_GAS_PIPING` or `GAS_PIPING_NOT_SUPPLIED` branches.

---

## 2. What This Spec Is

This spec defines:

- the role of `GPS1` in the LL152 workflow;
- the official section structure of the form;
- the first-pass field grouping model;
- the findings categories explicitly named on the form;
- and what should be deferred to later specs.

---

## 3. What This Spec Is Not

This spec does **not** define:

- the full `GPS2` certification behavior;
- branch B / branch C paths;
- full review-state logic;
- photo evidence rules;
- the final deliverable packet;
- internal app UX;
- offline sync behavior;
- or complete validation logic for every field.

Those are separate specs.

---

## 4. Artifact Role in the Workflow

### 4.1 What GPS1 is

`GPS1` is the **Gas Piping System Periodic Inspection Report**.

Within the workflow, it should be treated as:
- the primary inspection-report artifact for Branch A;
- the form that captures the official inspection-result categories;
- the form that records observed unsafe conditions/comments;
- and the report provided by the inspecting LMP to the owner.

### 4.2 What GPS1 is not

`GPS1` is not:
- the generic Job payload;
- the engine-level state model;
- the DOB certification submission artifact;
- or the sole representation of all LL152 workflow data.

### 4.3 Product implication

The application should treat `GPS1` as a **workflow-owned structured report artifact**, not as a generic attachment and not as the entire LL152 workflow model.

---

## 5. Branch Applicability

`GPS1` applies only to the **Standard Inspection Branch**.

### Applies to
- `STANDARD_INSPECTION`

### Does not apply as the governing form to
- `NO_GAS_PIPING`
- `GAS_PIPING_NOT_SUPPLIED`

### Invariant

A workflow instance in Branch B or Branch C must not be modeled as a partially completed `GPS1` path.

---

## 6. Official Section Inventory

The official form contains the following major sections:

1. **Location Information**
2. **Licensed Master Plumber Information**
3. **Individual Performing Inspection (Qualified Individual) Information**
4. **Certification of Inspection Results**
5. **Additional Comments**
6. **Certification of Licensed Master Plumber**
7. **Certification of Individual Performing Inspection**

### 6.1 Detailed Field Inventory (From GPS1 PDF)

The official form requires the following specific fields per section:

**1. Location Information (required for all reports)**
*   House No(s), Street Name, Owner Name
*   Borough, Block, Lot, BIN, Community Board No.
*   Number of Stories, Total Number of Meters, Total Number of Active Meters

**2. Licensed Master Plumber Information (required for all reports)**
*   Name: Last Name, First Name, Middle Initial
*   Business Name, Business Telephone, Business Fax
*   Business Address, City, State, Zip
*   Mobile Telephone, Email, License Number

**3. Individual Performing Inspection (Qualified Individual) Information**
*(required where a qualified individual performed inspection under LMP supervision)*
*   Name: Last Name, First Name, Middle Initial
*   Business Name, Business Telephone, Business Fax
*   Business Address, City, State, Zip
*   Mobile Telephone, Email, Employer Name

**4. Certification of Inspection Results (required for all reports)**
For each of the 5 categories, the form captures:
*   Checkbox: "No Condition(s) Observed" OR "Condition(s) Observed"
*   Text area: "Conditions observed (e.g., floor number & location...)"

**5. Additional Comments**
*   Freeform text area for supplemental notes

**6. Certification of Licensed Master Plumber (required for all reports)**
*   Name (printed), Signature, Date, LMP Seal

**7. Certification of Individual Performing Inspection**
*(required where a Non-LMP performed inspection under LMP supervision)*
*   Name (printed), Signature, Date

### Consequence

These sections should become the first top-level grouping structure for the internal workflow model.

---

## 7. First-Pass Data Groupings

### 7.1 Location Information

This section should be treated as the form’s **inspection-site identification block**.

### Likely data category
- building/site identification
- address/location text
- identifying context sufficient for the owner/report

### Architectural note

This data is not the same as canonical Building truth.

The workflow may consume data from `Building`, but the form still represents a report-layer location block that should be rendered explicitly.

---

### 7.2 Licensed Master Plumber Information

This section should be treated as the **responsible LMP block**.

### Likely data category
- LMP identity
- license/business information
- contact / identifying details required on the form

### Architectural note

This is workflow/report identity, not generic Job identity.

---

### 7.3 Individual Performing Inspection Information

This section should be treated as the **field inspector / qualified individual block**.

### Likely data category
- individual identity
- qualification/supervision context
- relationship to the responsible LMP

### Architectural note

This section reinforces that the workflow needs to represent both:
- the responsible LMP; and
- the individual who actually performed the inspection, when different.

---

### 7.4 Certification of Inspection Results

This is the **core findings section** of `GPS1`.

It is the most important section for Phase 2 design because it already defines named inspection-result categories.

### Consequence

The internal findings model should begin from this section rather than from freeform notes.

---

### 7.5 Additional Comments

This section should be treated as the **freeform narrative / supplemental notes block**.

### Architectural note

This section is not a substitute for the structured findings model. It is a complement to it.

---

### 7.6 LMP Certification

This section should be treated as the **responsible LMP attestation block**.

### Consequence

The workflow likely needs a distinction between:
- inspection content; and
- sign-off / attestation state.

---

### 7.7 Inspector Certification

This section should be treated as the **individual performer attestation block**.

### Consequence

The workflow likely needs to preserve the difference between:
- performer acknowledgment; and
- responsible LMP certification.

---

## 8. Built-In Findings Categories

The official form defines five named inspection-result categories:

1. **Improper Use of Flex Hose**
2. **Evidence of Illegal Connections / Non-Code Compliant Installations**
3. **Gas Leak (0.1% gas or more in air)**
4. **Worn Part(s) Affecting Safe and Reliable Operation**
5. **Other Unsafe Condition(s)**

### Core meaning

These categories are not optional product inventions.

They are official parts of the public artifact and therefore should be the first source of truth for the initial findings structure.

---

## 9. Observed / Not Observed Structure

For each named findings category, the form implies a binary branch:

- **No Condition(s) Observed**
- **Condition(s) Observed**

And, where conditions are observed, the form expects a narrative description.

### First model implication

Each findings category should likely support:
- category identity;
- observed/not-observed outcome;
- optional narrative detail.

### Open design question

Whether these should be modeled as:
- a fixed embedded structure inside `ll152_job_details`,
- or first-class workflow child entities,

should be decided in `LL152_Findings_and_Stop_Conditions_Spec.md`.

---

## 10. Field Ownership Categories

At the current public-evidence stage, the form data should be classified into these buckets:

### A. Pulled or derived from existing system context
Examples:
- building/location identity
- known LMP business identity
- known job reference context

### B. Captured during workflow execution
Examples:
- inspection findings
- comments
- performer identity when not implicit

### C. Certification / attestation layer
Examples:
- LMP sign-off
- inspector sign-off
- dates associated with report completion/certification

### D. Still unresolved operationally
Examples:
- exactly which fields should be prefilled versus editable;
- whether comments are single-block or section-specific internally;
- whether the application stores raw form fidelity or normalized domain fields first.

---

## 11. Relationship to Job Engine

The Job engine remains unchanged.

The engine should not own:
- `GPS1` sections;
- findings categories;
- attestation logic;
- or report rendering concerns.

The engine only knows:
- the Job exists;
- it is of type `LL152_INSPECTION`;
- it is in a coarse engine lifecycle state.

### Invariant

`GPS1` must remain workflow-owned payload and report logic, not Job-engine core state.

---

## 12. Relationship to LL152 Branch Topology

This spec depends on `LL152_Branch_Topology.md`.

### Important consequence

If branch discrimination is not respected, `GPS1` will be overgeneralized and the workflow model will become incorrect.

This spec must therefore be interpreted as:
- **Branch A only**;
- not a cross-branch LL152 universal form schema.

---

## 13. Relationship to Future Specs

This spec should feed directly into:

1. `LL152_Findings_and_Stop_Conditions_Spec.md`
2. `GPS2_Certification_and_Filing_Branches.md`
3. `LL152_Workflow_State_Spec.md`
4. `LL152_Deliverable_Packet_Spec.md`

### Dependency order

- `GPS1_Form_Spec.md` should precede findings/state design.
- Findings/state design should precede final workflow synthesis.

---

## 14. Invariants

1. `GPS1` belongs only to the `STANDARD_INSPECTION` branch.
2. The official section structure must be preserved in some form in the workflow model.
3. The five named findings categories must be treated as first-class public-artifact categories.
4. The findings section must support observed vs not-observed outcomes.
5. Narrative comments complement structured findings; they do not replace them.
6. LMP certification and inspector certification are distinct attestation concepts.

---

## 15. Open Questions

1. What exact field list belongs to each official section?
2. Which fields are best modeled as normalized workflow fields versus report-rendering fields?
3. Which fields should be editable after initial capture versus locked at certification time?
4. Should the findings categories be embedded or entity-like?
5. Should comments be global only, or should the internal model also support category-specific notes?
6. What report dates need explicit first-class modeling?

---

## 16. Follow-On Work

This sub-spec has been converged into:

**[LL152_Inspection_Workflow.md](LL152_Inspection_Workflow.md)** — the Phase 2 synthesis document.

Field inventory expansion will occur during implementation.

---

## 17. Current Recommendation

Treat `GPS1` as the **official structured inspection-report artifact for Branch A**.

Use its section structure and built-in findings categories as the first stable public skeleton for the LL152 Standard Inspection workflow.

