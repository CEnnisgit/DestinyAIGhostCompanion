# ADR 0016: Job Engine with Pluggable Workflow Types

**Date**: 2026-03-16  
**Status**: Accepted  
**Context**: Realigning domain terminology and aggregate boundaries before beginning Phase 1 (Inspection Job) design work.

## Application Context

The existing `InspectionsModule` was originally scaffolded as a monolithic module containing three sub-modules (Dispatch, Capture, Compliance). During domain analysis, we identified two problems:

1. **The "Job" concept was hidden.** The PRD consistently uses "Job" as the core unit of work (Job Intake, Dispatched, Job Status States), but our module structure absorbed it under the name "Inspections" — conflating the *work container* with the *type of work*.
2. **"Inspection" was doing double duty.** It referred to both the lifecycle of a work assignment (scheduling, dispatch, status tracking) and the specific LL152 data capture workflow (GPS1 form, findings, photos).

## Decision: Separate Job (Engine) from Inspection (Workflow)

We adopt the same **Engine + Program** architecture proven in the Compliance module (see [ADR-0012](./0012-compliance-engine-extensions-and-roster-status.md)):

### The Job Aggregate (Engine)

A generic work container that manages the lifecycle of any field assignment:

- **Identity & assignment:** who is doing the work, where, when
- **Building reference:** links to `CRM/Assets`
- **Obligation reference:** links to `CRM/Compliance` (optional — not all jobs are obligation-driven)
- **State machine:** Intake → Dispatched → In Progress → Submitted → Reviewed → Finalized → Delivered
- **Job type:** a discriminator field (e.g., `LL152_INSPECTION`) that activates the appropriate workflow

The Job aggregate owns the lifecycle but is agnostic to the specific type of work.

### Workflow Types (Programs)

Type-specific behavior that plugs into the Job engine:

- **Form schema:** what data the technician captures (GPS1 for LL152)
- **Validation rules:** required fields, stop conditions
- **Review rules:** what the LMP checks during approval
- **Output:** deliverables produced (GPS1/GPS2 packet for LL152)
- **Deadline computation:** type-specific deadline rules (30/60/120/180-day for LL152)

Each workflow type may have its own extension table (e.g., `ll152_job_details`) following the 1:1 extension pattern from ADR-0012.

## Architectural Parallel

| Layer | Compliance Pattern | Job Pattern |
|-------|-------------------|-------------|
| **Engine** | `ComplianceObligation` aggregate | `Job` aggregate |
| **Program/Type** | `Programs/LL152/LL152_Program_Spec.md` | `Workflows/LL152/LL152_Inspection_Spec.md` |
| **Extension table** | `ll152_obligation_details` | `ll152_job_details` |
| **Core question** | *"What is owed?"* | *"What work is being done?"* |

## Rationale

1. **Domain clarity:** "Job" matches the PRD language and how practitioners (plumbers, LMPs) think about their work. "Inspection" describes the *type*, not the *thing* being managed.
2. **Extensibility:** The same Job engine can support repair jobs, estimate visits, follow-up inspections, or any future work type by adding a new workflow definition — without modifying the core Job aggregate.
3. **Consistency:** This mirrors the proven Compliance Engine + Extensions pattern already in production (ADR-0012), giving the codebase a unified architectural vocabulary.
4. **Spec clarity:** When writing aggregate specs, the separation makes boundaries obvious — the Job spec defines the lifecycle; the LL152 Inspection spec defines the payload and rules.

## Consequences

**Positive:**
- Clean aggregate boundaries: Job lifecycle is separated from inspection-specific logic.
- Future-proof: new work types don't require restructuring the core Job module.
- Consistent architecture across the two core engines (Obligations and Jobs).
- Module naming aligns with PRD vocabulary.

**Negative:**
- The existing `InspectionsModule` directory structure and README references will need to be refactored/renamed.
- Join complexity: queries needing both Job state and LL152-specific details require joining across `jobs` and `ll152_job_details`.

## Impact on Module Structure

The `InspectionsModule` will be **renamed to `JobsModule`** with the following internal restructure:

```
Before:                          After:
InspectionsModule/               JobsModule/
├── Dispatch/                    ├── Engine/        (Job aggregate, state machine, dispatch)
├── Capture/                     └── Workflows/
└── Compliance/                      └── LL152/     (GPS1 form, validation, review rules, output)
```

The old `Inspections/Compliance` sub-module (validation rules engine) becomes part of the LL152 workflow definition, since validation rules are type-specific.
