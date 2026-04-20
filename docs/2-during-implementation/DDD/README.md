# Detailed Design Document (DDD)

> **Status:** Live Document
> **Phase:** During-Implementation (PDA-SDD)

This document serves as the central hub for the system's technical design.

## Sections

| Section | Description | Link |
|---------|-------------|------|
| **1. Traceability Matrix** | Maps SRSD requirements → Modules | [Traceability/](./Traceability/) |
| **2. System Architecture** | High-level diagram + Tech stack | [SystemArchitecture/](./SystemArchitecture/) |
| **3. Data Design** | ERD, Data Structures, DB Schema | [DataDesign/](./DataDesign/) |
| **4. Interface Design** | UI Specs + API Specs | [InterfaceDesign/](./InterfaceDesign/) |
| **5. Module Design** | Per-module responsibilities & interactions | [ModuleDesign/](./ModuleDesign/) |

## TODO

- [ ] **SRSD Scaling Decision** — As the product grows, SRSD files (organized by requirement type) will get longer. Decide between: (A) adding a `Module` column to SRSD tables so splitting is mechanical later, or (B) letting DDD Traceability files be the sole source for module↔requirement mapping. Either way, prepare for eventual splitting of large SRSD files into per-module sub-files. See discussion in conversation 4054bca5.

