# Data Design

> **Parent:** [Detailed Design Document (DDD)](../README.md)

This section covers the **Data Design**, the third component of the DDD.

## Components

Per the PDA-SDD specification (Figure 5), this section consists of:

1.  **[Entity-Relationship Diagram (ERD)](ERD.md)**
    *   Canonical entity list, relationships, and Module Ownership.

2.  **[Data Structures](DataStructures.md)**
    *   Shared / Cross-cutting domain object definitions.

3.  **[Database Schema](DatabaseSchema.md)**
    *   PostgreSQL table definitions, constraints, and indexes.

## Philosophy

> **DataDesign defines the "world of data". ModuleDesign defines each module's relationship to that world.**

- DataDesign is the **source of truth** for entity names, table schemas, and relationships.
- Module Design documents should *reference* DataDesign, not redefine it.
