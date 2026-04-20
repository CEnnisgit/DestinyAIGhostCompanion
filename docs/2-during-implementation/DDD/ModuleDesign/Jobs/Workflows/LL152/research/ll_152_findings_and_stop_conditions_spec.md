# LL152 Findings and Stop Conditions Specification

**Version:** 0.1.0  
**Status:** Draft  
**Module:** Job Workflows — LL152  
**Branch:** `STANDARD_INSPECTION` (Branch A only)  
**Parent Aggregate:** `Job`  
**Related Specs:** `ll_152_branch_topology.md`, `gps_1_form_spec.md`, `gps_2_certification_and_filing_branches.md`

---

## Objective

This spec defines the first public-evidence-first model for **findings** and **stop conditions** in the LL152 Standard Inspection workflow.

It exists to answer these questions:

1. What is a finding in the LL152 workflow?
2. How should the official GPS1 findings categories be represented in the domain?
3. What is the difference between an observed condition, a correction-required condition, and a stop-the-line condition?
4. Which conditions require immediate escalation or reporting?
5. What data should the workflow store for each finding?
6. How do findings influence later certification/filing outcomes in `GPS2`?

This spec is intentionally scoped to the **Standard Inspection Branch**.

---

## 1. Core Decision

A **finding** is a workflow-owned record of an inspection-result category evaluated during a Branch A LL152 gas piping inspection.

The initial findings model should be anchored in the five official GPS1 categories, not in arbitrary freeform notes.

### Architectural meaning

The LL152 workflow should begin with a **structured findings model** that supports:
- category identity;
- observed vs not observed outcome;
- narrative detail;
- severity / escalation classification;
- and downstream certification consequences.

### Core distinction

A finding is not automatically a stop condition.

The workflow must distinguish between:
- **Observed condition**
- **Correction-required condition**
- **Immediate-report / stop-the-line condition**

These are related but not identical concepts.

---

## 2. What This Spec Is

This spec defines:

- the first findings model for Branch A;
- the official category set from GPS1;
- the first pass distinction between ordinary findings and immediate-report conditions;
- the role of findings in correction and certification logic;
- and the workflow consequences of observed unsafe conditions.

---

## 3. What This Spec Is Not

This spec does **not** define:

- every field on the GPS1 form;
- the full workflow-state machine;
- the complete review / return loop;
- the photo evidence model in detail;
- the deliverable packet;
- or the full filing implementation contract.

It also does **not** define utility / DOB integration mechanics beyond the workflow obligation to recognize immediate-report conditions.

---

## 4. Branch Applicability

This spec applies only to:
- `STANDARD_INSPECTION`

It does **not** govern:
- `NO_GAS_PIPING`
- `GAS_PIPING_NOT_SUPPLIED`

### Invariant

Branch B and Branch C must not be modeled as though they produce the same findings structure as Branch A.

---

## 5. Findings Definition

A finding is the workflow-owned representation of one inspection-result category evaluated during a Branch A LL152 inspection.

### Minimum meaning of a finding

Each finding answers:
- **which category was evaluated**;
- **whether a condition was observed**;
- **what was observed, if anything**;
- and **whether the observation carries correction or immediate-report consequences**.

### First design rule

The workflow should create findings from a **known category set**, not from freeform user-defined types.

---

## 6. Official Findings Categories

The initial findings category set is the official GPS1 category set:

1. `IMPROPER_USE_OF_FLEX_HOSE`
2. `ILLEGAL_CONNECTION_OR_NON_CODE_COMPLIANT_INSTALLATION`
3. `GAS_LEAK_0_1_PERCENT_OR_MORE_IN_AIR`
4. `WORN_PART_AFFECTING_SAFE_AND_RELIABLE_OPERATION`
5. `OTHER_UNSAFE_CONDITION`

### Consequence

These categories should be represented as a closed initial vocabulary in the workflow model.

### Future flexibility

If later field research reveals recurrent sub-types inside these categories, those should be modeled as:
- subtype values,
- classification tags,
- or structured detail fields,

rather than by discarding the official category spine.

---

## 7. Observed / Not Observed Structure

Each official findings category should support a binary result:

- `NOT_OBSERVED`
- `OBSERVED`

### Rule

If a finding is `NOT_OBSERVED`, narrative detail should be optional or absent.

If a finding is `OBSERVED`, narrative detail should be expected.

### Consequence

The findings model should not begin as a simple list of only the conditions that were found.

It should be able to represent the full category evaluation set.

---

## 8. First-Pass Finding Shape

Each finding should likely support, at minimum:

- `finding_id`
- `job_id`
- `category`
- `observation_result` (`OBSERVED` / `NOT_OBSERVED`)
- `narrative_detail`
- `requires_correction` (boolean)
- `requires_immediate_reporting` (boolean)
- `recorded_at`
- `recorded_by`

### Design note

This does not yet decide whether findings are persisted as:
- child entities,
- embedded workflow records,
- or a normalized findings table.

But the conceptual model should behave like a first-class workflow structure, not like a single comments blob.

---

## 9. Difference Between Findings, Corrections, and Stop Conditions

### 9.1 Observed condition

An observed condition means the inspection identified something in a named findings category.

This is the broadest class.

---

### 9.2 Correction-required condition

A correction-required condition is an observed condition that affects certification outcomes and requires follow-up correction behavior.

This is narrower than “observed condition.”

Not every finding must be modeled as a stop-the-line condition.

---

### 9.3 Stop condition / immediate-report condition

A stop condition is a finding whose presence requires **immediate workflow escalation** because DOB/public guidance treats it as requiring immediate reporting from the field.

This is narrower than both:
- observed condition; and
- correction-required condition.

### Core meaning

Stop conditions are workflow-disrupting findings, not just ordinary report content.

---

## 10. Public-Evidence Stop Conditions

At the public-evidence stage, the workflow should recognize at least these conditions as potential immediate-report / stop-the-line conditions:

1. `GAS_LEAK_0_1_PERCENT_OR_MORE_IN_AIR`
2. `ILLEGAL_CONNECTION_OR_NON_CODE_COMPLIANT_INSTALLATION`
3. other unsafe / hazardous conditions that meet the public DOB rule/guidance threshold for immediate reporting

### Design rule

The workflow should not wait for the later certification/filing path to recognize these conditions.

They must be visible as field-time escalation conditions.

---

## 11. Stop Condition Workflow Consequences

When a stop condition is present, the workflow should support consequences such as:

- explicit escalation marker on the job/workflow;
- requirement to record narrative detail;
- requirement to preserve time/actor context;
- recognition that the finding affects certification logic;
- and support for later reporting/audit evidence.

### Important boundary

This spec does not yet define the exact state transition model caused by a stop condition.

That belongs in `LL152_Workflow_State_Spec.md`.

But this spec does establish that stop conditions are not just passive findings.

---

## 12. Relationship to GPS1

`GPS1` is the public artifact that exposes the official findings categories and observed/not-observed structure.

### Consequence

The internal findings model should begin from the shape implied by `GPS1`, while still allowing the workflow to preserve richer internal metadata than the rendered form.

### Invariant

Freeform comments must not replace the structured findings model.

---

## 13. Relationship to GPS2

`GPS2` expresses certification/filing outcomes that depend, in part, on what findings were observed.

### Consequence

The findings model must support at least these downstream interpretations:
- no correction required;
- correction required;
- correction pending / additional time;
- corrected-all state.

### Important distinction

Findings themselves are not GPS2 states.

They are workflow evidence that influences GPS2 certification outcomes.

---

## 14. Relationship to Job Engine

The Job engine remains unchanged.

The engine should not know:
- which findings categories exist;
- which findings were observed;
- whether a stop condition exists;
- or whether corrections are required.

Those belong to the LL152 workflow layer.

### Invariant

Findings and stop conditions must not be encoded into `JobStatus`.

---

## 15. Relationship to Review / Return Behavior

This spec does not yet define the LMP review loop.

But findings are likely one of the main inputs into:
- return-for-fixes behavior;
- correction-required certification decisions;
- and final approval/certification preparation.

### Consequence

The findings model must be durable enough to survive:
- draft capture;
- review;
- possible return/revision;
- and later certification output.

---

## 16. First-Pass Domain Invariants

1. Every Branch A LL152 inspection must evaluate the official findings category set.
2. Each category must support an observed/not-observed outcome.
3. Observed findings should support narrative detail.
4. Stop conditions are a special subset of findings, not a separate unrelated concept.
5. Findings influence certification outcomes but are not themselves certification states.
6. Freeform comments must not replace category-structured findings.

---

## 17. Open Questions

1. Should findings be persisted as first-class child entities or as a structured workflow payload block?
2. Which findings categories always imply `requires_correction = true` versus conditionally imply it?
3. Should `requires_immediate_reporting` be inferred from category, user-selected, or both?
4. What additional sub-classification is needed inside `OTHER_UNSAFE_CONDITION`?
5. What photo or evidence attachments should be linked directly to findings versus to the job broadly?
6. Should the workflow require completion of all five categories before the inspection can be treated as fully captured?

---

## 18. Follow-On Work

This sub-spec has been converged into:

**[LL152_Inspection_Workflow.md](LL152_Inspection_Workflow.md)** — the Phase 2 synthesis document.

Findings → GPS2 mapping is addressed in §6 of the synthesis doc.

---

## 19. Current Recommendation

Treat findings as a **first-class structured workflow model** anchored in the five official GPS1 categories.

Treat stop conditions as a **special severity/escalation subset of findings** that carry immediate workflow consequences.

This gives the LL152 workflow a clean center between:
- report structure (`GPS1`),
- certification/filing outcomes (`GPS2`),
- and future review/state behavior.

