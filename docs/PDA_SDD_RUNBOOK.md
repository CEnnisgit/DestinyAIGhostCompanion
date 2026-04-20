# PDA-SDD Agent Playbook: PRD Integration Runbook

This is an operational workflow you (as an agent) can follow when a human drops in a PRD and asks you to convert it into PDA-SDD’s phase-based documentation spine (Pre → During → After). PDA-SDD is explicitly designed to keep docs “living” and synchronized with modern iterative development, supporting versioning and centralized storage.

---

## 1. Inputs and Setup

### Inputs You Request (Minimum)
* **PRD** (source of truth for intent)
* Any existing: API docs, architecture notes, UX mockups, compliance constraints, roadmap

### First Actions (Day 0)
1. **Create a centralized, versioned doc workspace** (repo/folder) because PDA-SDD relies on **versioning + centralized storage** to ensure consistency/completeness and prevent duplication.
2. **PRD extraction pass** → produce a *Requirements Inventory* (not the SRSD yet):
   * Goals, scope boundaries, main user flows
   * Functional requirements (features/behaviors)
   * Non-functional requirements (performance/security/usability/etc.)
   * Integrations, data entities, constraints, acceptance criteria
3. **Gap scan** (fast): flag missing targets/ambiguity (common PRD gaps: response-time target, data retention, auth model, integration protocols).

**Output of Day 0:** "PRD→SRSD mapping notes" + "Open Questions / Blockers" list.

---

## 2. Pre-Implementation (PRD → SRSD + RLD)

PDA-SDD’s three phases are: **Pre-implementation, During-implementation, After-implementation**, aligned with typical lifecycle stages.
Pre focuses on foundational docs like **detailed requirements** (and an initial architectural vision).

### 2.1 Build the SRSD (The Requirements Baseline)

SRSD is the “cornerstone” that underpins subsequent documentation; contracts can be based on it and other documents are derived from it.

#### SRSD Writing Order (Recommended)

**A) SGI (System General Info)**
* SGI-S Scope
* SGI-OJ Objectives
* SGI-MF Main Functions

**B) Code Every Requirement Using the SRSD Coding System**
The SRSD coding system assigns a unique code per requirement, categorizes into **functional (SFR)** and **non-functional (SNFR)**, and supports granular sub-requirements for clear identification and reference across design/docs.
It’s expected to remove ambiguity, support modifications, and link requirements to subsequent documentation.

**Practical ID Rule (Implementation Detail):**
* Turn each coded requirement into a unique ID like:
  `SFR-IODE-01`, `SFR-SRAN-03`, `SNFR-PRT-02`, etc.
  (Your agent can enforce uniqueness and maintain a master index.)

#### SRSD Requirement Entry Template (Agent-Friendly)
For each requirement ID:
* **ID:** `SFR-…-NN`
* **Statement:** "The system shall…"
* **Rationale:** (1–2 lines from PRD)
* **Acceptance Criteria:** measurable checks
* **Priority:** Must/Should/Could
* **Dependencies:** integrations/assumptions
* **Notes/TBD:** anything unresolved (these become blockers)

### 2.2 Build the RLD (Resource Reality Check)

Pre-implementation mandates SRSD + RLD (contracts optional). RLD exists to let PMs/stakeholders assess capability and establish a solid foundation for the pre-stage.

RLD includes:
* **Human resources:** summary (job titles + counts) and per-member details (name, title, experience, qualifications, hourly cost).
* **Equipment:** hardware + software tooling categories (e.g., dev environment, VCS, DBMS, testing tools, deployment tools, documentation tools, etc.).

---

### 2.3 Pre-Implementation Exit Gates (Blockers Before During)

You don’t move to During until:

1. **SRSD baseline is stable**
   * All major PRD features are expressed as coded requirements (SFR/SNFR) with unique IDs.
   * "Main Functions" (SGI-MF) are agreed—because they become organizing anchors later (notably in CLD).

2. **Critical ambiguities resolved or explicitly accepted**
   Typical blockers:
   * Missing NFR targets (response time / throughput / availability)
   * Undefined auth model / permissioning
   * Undefined integration contracts or data ownership
   * Unclear scope boundaries (what’s out)

3. **RLD is complete enough for planning**
   * Team roles and key tooling are identified.

4. **Versioning + centralized storage are in place**
   Because PDA-SDD explicitly depends on them for integrity and completeness.

---

## 3. Transition: Pre → During (The Operational Handoff)

During emphasizes design decisions, technical specs, test plans, and code-level documentation.
The key handoff action is: **start the DDD and begin with the traceability matrix**.

The paper is explicit: the *initial section* of the DDD is a **traceability matrix** linking DDD modules to SRSD requirements.

**First During Action (Non-negotiable):**
* Create **DDD → Traceability Matrix** with SRSD requirement IDs as rows (or references).

---

## 4. During-Implementation (DDD + CLD + Project Plan)

During stage essential docs are: **DDD**, **CLD**, and a comprehensive **project plan** (Gantt recommended; WBS optional).

### 4.1 Build the DDD from SRSD

DDD structure includes:
* Traceability Matrix (first)
* System Architecture (diagram + tech stack)
* Data Design (ERD, data structures, schema)
* Interface Design (UI + API specs)
* Module Design (per module: responsibilities, structure, interactions, algorithms, chosen data structures)

**DDD Traceability Matrix (Template Columns)**
* SRSD Requirement ID
* Requirement summary
* DDD Module(s)
* Implementation status (Planned / In dev / Done)
* Test status (Not started / Passing / Failing)
* Notes

### 4.2 Run the CLD Continuously (Changes Become First-Class)

CLD’s primary function is to chronicle project evolution—mods/additions across SRSD, DDD, and source code.
It is organized by SRSD main functions starting with SGI-MF, meaning CLD sections mirror SRSD’s main functions.

**CLD Log Fields (Template)**
* Significance (major/minor; requirement/design/code domain)
* Results (success/fail; approved modifications)
* Date/time
* Changes Summary
* Detailed Changes
* References (link to relevant SRSD requirements)
* Issue Tracking System (ticket # if used)
* Author

---

### 4.3 During-Implementation Exit Gates (Blockers Before After)

Do not move to After until:

1. **Traceability is intact**
   * Every implemented (or committed-to-ship) requirement is mapped in the DDD traceability matrix.

2. **CLD is current**
   * Major requirement/design/code changes are logged with references (and tickets if applicable).

3. **DDD reflects reality**
   * Architecture/interfaces/module design match what was actually built (not a stale plan).

---

## 5. Transition: During → After (From Building to Packaging)

After phase encompasses deployment guides, user manuals, and maintenance logs.
PDA-SDD’s After-delivery essentials include:
* User Documentation: SUMD
* Technical Documentation: updated SRSD, updated DDD, source code
* Legal Documentation: EULA

**First After Action (Recommended):**
* "Freeze shipped scope" → update SRSD + DDD to match as-built → start SUMD + EULA.

---

## 6. After-Implementation (Delivery Set)

### 6.1 SUMD (Software User Manual Document)
SUMD is a user-facing resource covering functionality, terminology, operation, basic + advanced usage, and troubleshooting.
It follows a structured framework (intro → install → basic → advanced → troubleshooting → glossary → appendix).

### 6.2 EULA (End-User License Agreement)
PDA-SDD proposes a standardized nine-section EULA framework: Grant of License, Ownership, Restrictions, Disclaimer of Warranty, Indemnity, Termination, Governing Law and Jurisdiction, Entire Agreement, Severability.

### 6.3 Package Technical Deliverables
* Updated SRSD
* Updated DDD
* Source Code

Optional: quick guide, updated CLD, certificates.

---

## 7. "Agent Behavior Rules" (The Simple Operating Policy)

1. **SRSD is the baseline**: everything references it.
2. **No requirement without an ID**: every feature/NFR must be coded for traceability.
3. **No module without traceability**: DDD starts with a matrix mapping modules to SRSD requirements.
4. **No change without a CLD entry**: CLD chronicles changes across requirements/design/code with references.
5. **Docs evolve like code**: versioning + centralized storage are mandatory foundations.
