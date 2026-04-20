# SRSD: Software Requirements Specification Document

> **Status:** Baseline / Pre-Implementation
> **Project:** Plumber's Compliance Dispatch (PCD)

## 1. Introduction
The SRSD defines the functional and non-functional requirements originally extracted for the LL152 workflow. While the product scope has broadened to a plumbing company operations platform (see [ALPHA_PERSONAS_AND_SCOPE.md](../../ALPHA_PERSONAS_AND_SCOPE.md)), the LL152-specific requirements documented here remain valid and applicable to the LL152 workflow module.

### Sub-Sections
- [**SGI** (General Info)](./SGI/) - Scope, Objectives, Main Functions
- [**SFR** (Functional)](./SFR/) - Behaviors, Inputs, Outputs
- [**SNFR** (Non-Functional)](./SNFR/) - Performance, Security, Usability

---

## 2. Traceability Matrix

### Functional Requirements (SFR)

#### SFR-IO: Input/Output
- `SFR-IODE-01`, `SFR-IODE-02`, `SFR-IODE-03`, `SFR-IODE-04`
- `SFR-IODE-10`, `SFR-IODE-11`, `SFR-IODE-12`
- `SFR-IODO-01`, `SFR-IODO-02`, `SFR-IODO-03`
- `SFR-IODO-10`, `SFR-IODO-11`, `SFR-IODO-12`, `SFR-IODO-13`
- `SFR-IOR-01`, `SFR-IOR-02`, `SFR-IOR-03`, `SFR-IOR-04`

#### SFR-PR: Processing
- `SFR-PRC-01`, `SFR-PRC-02`, `SFR-PRC-03`, `SFR-PRC-04`, `SFR-PRC-05`
- `SFR-PRDM-01`, `SFR-PRDM-02`
- `SFR-PRDM-10`, `SFR-PRDM-11`, `SFR-PRDM-12`
- `SFR-PRDP-01`, `SFR-PRDP-02`, `SFR-PRDP-03`
- `SFR-PRDP-10`

#### SFR-BR: Business Rules
- `SFR-BRC-01`, `SFR-BRC-02`, `SFR-BRC-03`, `SFR-BRC-04`
- `SFR-BRC-10`, `SFR-BRC-11`
- `SFR-BRV-01`, `SFR-BRV-02`, `SFR-BRV-03`
- `SFR-BRV-10`, `SFR-BRV-11`
- `SFR-BRW-01`, `SFR-BRW-02`, `SFR-BRW-03`, `SFR-BRW-04`, `SFR-BRW-05`, `SFR-BRW-06`
- `SFR-BRW-10`, `SFR-BRW-11`, `SFR-BRW-12`, `SFR-BRW-13`

#### SFR-SR: Security
- `SFR-SRAN-01`, `SFR-SRAN-02`, `SFR-SRAN-03`, `SFR-SRAN-04`
- `SFR-SRAZ-01`, `SFR-SRAZ-02`, `SFR-SRAZ-03`, `SFR-SRAZ-04`, `SFR-SRAZ-05`, `SFR-SRAZ-06`, `SFR-SRAZ-07`
- `SFR-SRAC-01`, `SFR-SRAC-02`, `SFR-SRAC-03`
- `SFR-SRAC-10`

#### SFR-IR: Integration
- `SFR-IRI-01`, `SFR-IRI-02`, `SFR-IRI-03`
- `SFR-IRI-10`, `SFR-IRI-11`
- `SFR-IRDX-01`, `SFR-IRDX-02`, `SFR-IRDX-03`
- `SFR-IRDX-10`
- `SFR-IRIN-01`, `SFR-IRIN-02`
- `SFR-IRIN-10`

### Non-Functional Requirements (SNFR)

#### SNFR-P: Performance
- `SNFR-PRT-01`, `SNFR-PRT-02`, `SNFR-PRT-03`
- `SNFR-PRT-10`, `SNFR-PRT-11`
- `SNFR-PT-01`, `SNFR-PT-02`, `SNFR-PT-03`

#### SNFR-SC: Scalability
- `SNFR-SCS-01`, `SNFR-SCS-02`
- `SNFR-SCI-10`, `SNFR-SCI-11`

#### SNFR-U: Usability
- `SNFR-UEU-01`, `SNFR-UEU-02`, `SNFR-UEU-03`, `SNFR-UEU-04`
- `SNFR-UEU-10`, `SNFR-UEU-11`
- `SNFR-UE-01`, `SNFR-UE-02`
- `SNFR-UE-10`, `SNFR-UE-11`
- `SNFR-UA-01`, `SNFR-UA-02`, `SNFR-UA-03`
- `SNFR-UA-10`, `SNFR-UA-11`

#### SNFR-R: Reliability
- `SNFR-RAV-01`, `SNFR-RAV-02`
- `SNFR-RAV-10`, `SNFR-RAV-11`
- `SNFR-RAC-01`, `SNFR-RAC-02`
- `SNFR-RAC-10`, `SNFR-RAC-11`
- `SNFR-RR-01`, `SNFR-RR-02`
- `SNFR-RR-10`, `SNFR-RR-11`

#### SNFR-S: Security
- `SNFR-SC-01`, `SNFR-SC-02`, `SNFR-SC-03`
- `SNFR-SC-10`, `SNFR-SC-11`, `SNFR-SC-12`
- `SNFR-SI-01`, `SNFR-SI-02`
- `SNFR-SI-10`, `SNFR-SI-11`
- `SNFR-SA-01`, `SNFR-SA-02`, `SNFR-SA-03`

#### SNFR-M: Maintainability
- `SNFR-MM-01`, `SNFR-MM-02`
- `SNFR-MM-10`, `SNFR-MM-11`, `SNFR-MM-12`
- `SNFR-MT-01`, `SNFR-MT-02`
- `SNFR-MT-10`, `SNFR-MT-11`, `SNFR-MT-12`
- `SNFR-MP-01`, `SNFR-MP-02`
- `SNFR-MP-10`, `SNFR-MP-11`
