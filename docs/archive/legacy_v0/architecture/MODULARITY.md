# Feature-Centric Architecture: The "Split & Seal" Pattern

This document explains our architecture for managing complexity in the monorepo.

## The Problem
In a traditional Monolith, code is organized by **Technical Layer** (Controllers, Services, Models).
*   **Problem**: Adding a feature requires jumping between 5 different folders.
*   **Problem**: Logic leaks. "Controllers" do business logic. "Services" do SQL queries.
*   **Problem**: The Mobile App and Backend duplicate logic (e.g., Form Validation), leading to bugs.

## The Solution: Feature-Centric Packages
We organize code by **Domain Feature** (Vertical Slices), located in `packages/features/`.

### The Rule: "The Split"
Every feature MUST be split into three sub-packages to enforce boundaries:

```mermaid
graph TD
    App[Apps (Mobile / Backend)] --> |Import| BackendPkg
    App --> |Import| MobilePkg
    
    subgraph "Feature Package: compliance-forms"
        BackendPkg[backend] --> |Depends On| CorePkg[core]
        MobilePkg[mobile] --> |Depends On| CorePkg[core]
        CorePkg --> |Imports| None[Nothing (Pure Logic)]
    end
```

### 1. Core (`packages/features/<name>/core`)
**The Hexagon**. Pure business logic.
*   **Contains**: Zod Schemas (`schema.ts`), TypeScript Interfaces, Pure Validator functions.
*   **Banned**: No React, No Fastify, No Database, No Node.js APIs.
*   **Goal**: Run anywhere (Browser, Mobile, Backend, Lambda).

### 2. Backend Adapter (`packages/features/<name>/backend`)
**The Translator**.
*   **Contains**: API Validation helpers, DTO mappers.
*   **Dependencies**: Depends on `core`. Can import specific backend utilities.

### 3. Mobile Adapter (`packages/features/<name>/mobile`)
**The Hook**.
*   **Contains**: React Hooks (`useFormState`), React Native specific helpers.
*   **Dependencies**: Depends on `core`. Can import React.

## Apps are "Thin Shells"
The `apps/` directory should contain minimal logic. Apps are just **Shells** that wire things together.

*   **Backend App**: Wires Routing + Database + Feature Packages.
*   **Mobile App**: Wires Navigation + UI Screens + Feature Packages.

## How to Add a New Feature
1.  Create `packages/features/<name>`.
2.  Create `core`, `backend`, `mobile` folders with `package.json` in each.
3.  Define the **Schema** in `core`.
4.  Implement logic.
5.  Import the package in `apps/backend/package.json` and `apps/mobile-technician/package.json`.
