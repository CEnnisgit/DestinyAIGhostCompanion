# Phase 0: Foundation Data ✅ COMPLETE

> **Status:** ✅ Done
> **Objective:** Establish authoritative NYC building coverage and compliance obligation tracking before building user-facing features.

---

## Domain Concepts Designed

### Building Aggregate (CRM/Assets)

| Concept | Spec | Status |
|---------|------|--------|
| Building Aggregate | [Building_Aggregate.md](../2-during-implementation/DDD/ModuleDesign/CRM/Assets/Building/Building_Aggregate.md) | ✅ |
| Data Sources & Import Strategy | [02_data_sources_and_import_strategy_v2.md](../2-during-implementation/DDD/ModuleDesign/CRM/Assets/Building/02_data_sources_and_import_strategy_v2.md) | ✅ |
| BIN ValueObject | [BIN_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/CRM/Assets/Building/ValueObjects/BIN/BIN_VO_Spec.md) | ✅ |
| BBL ValueObject | [BBL_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/CRM/Assets/Building/ValueObjects/BBL/BBL_VO_Spec.md) | ✅ |
| Address ValueObject | [Address_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/CRM/Assets/Building/ValueObjects/Address/Address_VO_Spec.md) | ✅ |
| Community District ValueObject | [CommunityDistrict_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/CRM/Assets/Building/ValueObjects/CD/CommunityDistrict_VO_Spec.md) | ✅ |
| DOF Building Class ValueObject | [DOFBuildingClass_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/CRM/Assets/Building/ValueObjects/DOF/DOFBuildingClass_VO_Spec.md) | ✅ |
| Condo Status ValueObject | [CondoStatus_VO_Spec.md](../2-during-implementation/DDD/ModuleDesign/CRM/Assets/Building/ValueObjects/Condo/CondoStatus_VO_Spec.md) | ✅ |

### ComplianceObligation Engine (CRM/Compliance)

| Concept | Spec | Status |
|---------|------|--------|
| Compliance Obligation Aggregate | [ComplianceObligation_Aggregate.md](../2-during-implementation/DDD/ModuleDesign/CRM/Compliance/Obligations/ComplianceObligation_Aggregate.md) | ✅ |
| LL152 Program Spec | [LL152_Program_Spec.md](../2-during-implementation/DDD/ModuleDesign/CRM/Compliance/Programs/LL152/LL152_Program_Spec.md) | ✅ |
| Engine Extension Pattern | [ADR-0012](../adr/0012-compliance-engine-extensions-and-roster-status.md) | ✅ |

---

## Implementation Artifacts Produced

| Artifact | Technology | Description |
|----------|------------|-------------|
| Database Schema | SQLx (Rust) | 11 tables in `crates/pcd-db` |
| PAD Ingestion | Rust | Pipeline A — city-wide building population from PAD |
| LL152 Ingestion | Rust | Pipeline B — DOB LL152 roster import |
| Dev Dashboard | Next.js | Internal visualization tool for buildings, anomalies, events, obligations |

---

## Deferred Items

| Item | Spec | Reason for Deferral |
|------|------|---------------------|
| Pipeline D — Condo Verification | [Pipeline_D_Condo_Verification.md](../2-during-implementation/DDD/ModuleDesign/CRM/Assets/Building/Pipeline_D_Condo_Verification.md) | Not needed for alpha launch. Buildings already have `condo_status` populated from PAD data. The DOF API verification step adds precision but is not on the critical path for LL152 inspections. Revisit post-beta when condo billing accuracy matters for invoicing. |

---

## Key ADRs

- [ADR-0005](./Architecture/DecisionLog/ADR-005-Hybrid-Event-Sourcing-For-Building-Timelines.md) — Hybrid Event Sourcing for Building Timelines
- [ADR-0011](../adr/0011-pad-ingestion-rust-worker.md) — PAD Ingestion Rust Worker
- [ADR-0012](../adr/0012-compliance-engine-extensions-and-roster-status.md) — Compliance Engine Extensions and Roster Status
- [ADR-0013](../adr/0013-bin-lifecycle-and-pipeline-arrival-order.md) — BIN Lifecycle and Pipeline Arrival Order
- [ADR-0014](../adr/0014-version-membership-junction-table.md) — Version Membership Junction Table
- [ADR-0015](../adr/0015-event-history-first-seen-only.md) — Event History First Seen Only
