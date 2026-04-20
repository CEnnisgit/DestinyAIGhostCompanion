# PDA-SDD Specification

> **Source:** Computers 2024, 13, 378 (computers-14-00378-v3.pdf)
> **Purpose:** Formal specification for CI/CD linting and documentation enforcement.

---

## 1. Phases Overview (Figure 2)

### Pre-Implementation
| Document | Status | Our Implementation |
|----------|--------|-------------------|
| **SRSD** (Software Requirements Specification) | Essential | `1-pre-implementation/SRSD/` ✅ |
| **RLD** (Resources List Document) | Essential | `1-pre-implementation/RLD.md` ⚠️ <br> *Requires: Human Resources (Summary + Detail), Equipment* |
| Contracts | Optional | N/A |

### During-Implementation
| Document | Status | Our Implementation |
|----------|--------|-------------------|
| **DDD** (Detailed Design Document) | Essential | `2-during-implementation/DDD/` ✅ |
| **CLD** (Change Log Document) | Essential | `2-during-implementation/CLD/` ✅ |
| Project Plan (Gantt Chart) | Essential | External (GitHub Projects) |
| WBS | Optional | N/A |

### After-Implementation
| Document | Status | Our Implementation |
|----------|--------|-------------------|
| **SUMD** (Software User Manual) | Essential | `3-after-implementation/SUMD/` ⏳ |
| Updated SRSD | Essential | Version control |
| Updated DDD | Essential | Version control |
| Source Code | Essential | `packages/`, `apps/` |
| EULA | Essential | TBD |
| Quick Guide | Optional | N/A |

---

## 2. SRSD Coding System (Table 2 + Figure 3)

### SGI (General Info)
| Code | Component |
|------|-----------|
| `SGI-S` | Scope |
| `SGI-OJ` | Objectives |
| `SGI-MF` | Main Functions |

### SFR (Functional Requirements)
| Code | Type | Sub-Types |
|------|------|-----------|
| `SFR-IO` | Input/Output | `IODE` (Data Entry), `IODO` (Data Output), `IOR` (Reporting) |
| `SFR-PR` | Processing | `PRC` (Calculation), `PRDM` (Decision Making), `PRDP` (Data Manipulation) |
| `SFR-BR` | Business Rules | `BRC` (Constraints), `BRV` (Validation), `BRW` (Workflow) |
| `SFR-SR` | Security | `SRAN` (Authentication), `SRAZ` (Authorization), `SRAC` (Access Control) |
| `SFR-IR` | Integration | `IRI` (Interface), `IRDX` (Data Exchange), `IRIN` (Interoperability) |

### SNFR (Non-Functional Requirements)
| Code | Type | Sub-Types |
|------|------|-----------|
| `SNFR-P` | Performance | `PRT` (Response Time), `PT` (Throughput), `PS` (Scalability) |
| `SNFR-U` | Usability | `UEU` (Ease of Use), `UE` (Efficiency), `UA` (Aesthetics) |
| `SNFR-S` | Security | `SC` (Confidentiality), `SI` (Integrity), `SA` (Availability) |
| `SNFR-R` | Reliability | `RAV` (Availability), `RAC` (Accuracy), `RR` (Robustness) |
| `SNFR-M` | Maintainability | `MM` (Modifiability), `MT` (Testability), `MP` (Portability) |

---

## 3. CLD Log Format (§4.3.4)

Each log entry MUST contain these 8 fields:
1. **Significance** — Major/Minor + Domain (Requirements/Design/Code)
2. **Results** — Success/Failure/Approved Modification
3. **Date** — ISO 8601 datetime
4. **Change Summary** — One-line summary
5. **Detailed Changes** — Bullet list
6. **References** — SRSD codes (e.g., `SFR-IODE-01`)
7. **Issue Tracking** — Ticket number (if applicable)
8. **Author** — Name

---

## 2. Document Structures (Figures 4, 5, 6)

### 2.1. RLD Structure (Figure 4)
**Human Resources**
- **Summary:** Job Title, Sum (Quantity)
- **Details:** Name, Job Title, Experience, Qualification, Hourly Cost

**Equipments**
- **Hardware:** Computers, Servers, Storage Devices
- **Software:**
  - Development Environment
  - Version Control System
  - Database Management System
  - Operating System
  - Design Tools
  - Testing Tools
  - Deployment Tools
  - Project Management Tools
  - Communication Tools
  - Documentation Tools
  - Virtual Machines

### 2.2. DDD Structure (Figure 5)
1. **Traceability Matrix**
2. **System Architecture**
   - High-Level Diagram
   - Technology Stack
3. **Data Design**
   - Entity-Relationship Diagram (ERD)
   - Data Structures
   - Database Schema
4. **Interface Design**
   - User Interface (UI) Specifications
   - API Specifications
5. **Module Design** (Repeated per Feature)
   - Module Responsibilities
   - Module Structure
   - Module Interactions
   - Algorithm Descriptions
   - Data Structure Selection

### 2.3. CLD Structure (Figure 6)
**Organization:** Feature-based (Matched to SRSD SGI-MF)

**Log Entry Elements (8 Required):**
1. **Significance:** Major/Minor + Domain (Req/Design/Code)
2. **Results:** Success/Failure/Approved Modification
3. **Date:** YYYY-MM-DD HH:mm
4. **Changes Summary:** Brief description
5. **Detailed Changes:** Full details
6. **References:** Link to SRSD codes
7. **Issue Tracking System:** Ticket #
8. **Author:** Name
