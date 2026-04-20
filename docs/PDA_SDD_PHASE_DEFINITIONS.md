# PDA-SDD Phase Definitions

PDA-SDD organizes software documentation into **three primary phases**—**Pre-implementation**, **During-implementation**, and **After-implementation**—chosen to mirror the "natural and intuitive progression" of typical software lifecycle stages so documentation stays **synchronized and intrinsically linked** with development work.

---

## Pre-Implementation

### Pre-Implementation Purpose

**Pre-implementation** exists to establish the project's *foundation* before building: define **detailed requirements** and an **initial architectural vision** so the rest of the lifecycle has a stable baseline to design and implement against.

### Pre-Implementation Outputs

* **SRSD (Software Requirements Specifications Document)** *(essential)*
* **RLD (Resources List Document)** *(essential)*
* **Contracts** *(optional)*

---

## During-Implementation

### During-Implementation Purpose

**During-implementation** exists to keep documentation "alive" while the system is actively built: capture **design decisions**, **technical specifications**, **test plans**, and **code-level documentation** as development evolves.

### During-Implementation Outputs

* **DDD (Detailed Design Document)** *(essential)*
* **CLD (Change Log Document)** *(essential)*
* **Project Plan (Gantt Chart)** *(essential; recommended for planning)*
* **WBS** *(optional)*

---

## After-Implementation

### After-Implementation Purpose

**After-implementation** exists to transition the system into real-world use and long-term ownership: provide **deployment guides**, **user manuals**, and **maintenance logs** so the delivered software can be operated and sustained.

### After-Implementation Outputs

* **User Documentation** *(essential: SUMD — Software User Manual Document)*
* **Technical Documentation** *(essential: updated SRSD, updated DDD, source code)*
* **Legal Documentation** *(essential: EULA)*
* Optional: **Quick Guide**, **updated CLD**, **certifications**

---

## Phase Handoff Rule

Each phase handoff is defined by *promoting the phase's essential artifacts into the next phase's working inputs*, maintaining continuity across time:

* **Pre → During:** requirements + baseline intent (**SRSD/RLD**) become the reference point for capturing implementation-time design and change.
* **During → After:** implementation-time documentation (design + change history + plan) becomes the basis for delivery documentation and maintenance-ready technical truth.

This works because the phases are explicitly intended to keep documentation "synchronized and intrinsically linked with development activities."

---

## Cross-Phase Infrastructure

PDA-SDD relies on two operational pillars across all phases:

* **Versioning** to ensure consistency/completeness over time
* **Centralized storage** to prevent duplication and preserve integrity
