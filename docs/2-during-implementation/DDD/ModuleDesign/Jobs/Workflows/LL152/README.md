# LL152 Inspection Workflow (Jobs)

> **Parent:** [JobsModule](../../README.md)
> **ADR:** [ADR-0016](../../../../../adr/0016-job-engine-pluggable-workflows.md)

## Primary Specification

**[LL152_Inspection_Workflow.md](LL152_Inspection_Workflow.md)** — the single implementation-ready reference for the LL152 workflow module.

This is the Phase 2 centerpiece, analogous to `Job_Aggregate.md` for the Phase 1 engine.

---

## Responsibilities

**LL152-Specific Behavior**: Defines how an LL152 Inspection job works — what is captured, how it's validated, and what is produced.

### Branch Topology
- Three compliance branches: Standard Inspection (A), No Gas Piping (B), Gas Piping Not Supplied (C)
- Branch A is the capture-heavy inspection path; B and C are certification/statement paths
- Branch discriminator is workflow-owned, not a `JobType` distinction

### Capture (Branch A)
- **GPS1 Report**: Structured inspection report with seven official sections
- **Findings**: Five official categories with observed/not-observed outcomes
- **Stop Conditions**: Immediate-report escalation for gas leaks and illegal connections

### Certification / Filing (All Branches)
- **GPS2 Certification**: Cross-branch certification/filing artifact
- Branch-specific certification outcomes

### Output
- GPS1/GPS2 packet generation
- Owner delivery packet

---

## Supporting Sub-Specs

These contain the detailed research and reasoning behind the synthesis doc:

| Sub-Spec | Purpose |
|---|---|
| [ll_152_branch_topology.md](research/ll_152_branch_topology.md) | Branch identification and architectural consequences |
| [gps_1_form_spec.md](research/gps_1_form_spec.md) | GPS1 section structure and data groupings |
| [gps_2_certification_and_filing_branches.md](research/gps_2_certification_and_filing_branches.md) | GPS2 role across branches |
| [ll_152_findings_and_stop_conditions_spec.md](research/ll_152_findings_and_stop_conditions_spec.md) | Findings model and stop condition behavior |
| [ll_152_workflow_state_spec.md](research/ll_152_workflow_state_spec.md) | Branch-aware state sets and transition model |
| [OPEN_DESIGN_QUESTIONS.md](OPEN_DESIGN_QUESTIONS.md) | Parking lot for deferred design questions |

---

## Data Structures
- `ll152_job_details` extension table (1:1 with `jobs`)
- Findings storage (structured records, one per category per inspection)
- Photo/evidence attachment (design deferred to implementation)

## Status
✅ **Phase 2 spec work complete** — synthesis doc and supporting sub-specs are finalized.
