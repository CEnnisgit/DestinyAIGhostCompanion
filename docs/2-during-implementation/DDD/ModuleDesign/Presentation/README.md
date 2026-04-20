# Presentation Module (The Dashboard)

> **Source of Truth:** `apps/web-dashboard/` (prototype) — no production code yet
> **Scope:** Pilot Core (LL152) — **Prototype v1** (tagged `prototype-v1`)
> **ADR:** [ADR-0017: Solo/Firm Modal Split](../../../../adr/0017-solo-firm-modal-split.md) *(if exists)*

## Traceability

> **Research:** [UX Research Notes](./Research/UX_RESEARCH_NOTES.md)
> **Prototype:** [Prototype v1 Spec](./Prototype/V1_SPEC.md)

This module handles the user-facing web dashboard — the primary interface for plumbers and LMP firms to manage LL152 compliance operations.

## Sub-Modules

### 1. [Dashboard Rail](./Dashboard/README.md) *(prototype)*
**Responsibility:** Morning operations console.
* Solo "My Day" — next stop, today's queue, paperwork due, deadlines
* Firm "Ops Console" — stat strip, team status, dispatch queue, filing

### 2. [Jobs Rail](./Jobs/README.md) *(prototype)*
**Responsibility:** Job lifecycle management UI.
* Dual-view list (Table / Schedule-Agenda)
* Section-based job detail with compliance chain tracker
* Quick-create modal with building select

### 3. [Buildings Rail](./Buildings/README.md) *(prototype)*
**Responsibility:** Building-centric compliance management UI.
* Dual-view list (Table / Cards)
* Building Profile — canonical compliance record
* Prospect mode for DOB roster imports

### 4. [Settings Rail](./Settings/README.md) *(prototype)*
**Responsibility:** Admin configuration UI.
* Organization + compliance config
* Team & permissions
* Notification preferences
* Data & integrations

## Module Interactions

- **Consumes**: `CRMModule` (Buildings, ComplianceObligations), `JobsModule` (jobs, workflows), `UsersModule` (team, roles)
- **Produces**: User commands → API calls → domain commands

## Architecture Decisions

| Decision | Rationale |
|---|---|
| **Solo / Firm split** | NYC LL152 market has both independent plumbers and LMP firms — every rail adapts |
| **Buildings as first-class** | Unlike generic FSM tools, LL152 compliance is building-centric |
| **Compliance chain tracker** | LL152 filing sequence (Inspection → GPS1 → GPS2) must be visualized to reduce errors |
| **Contextual drawer** | Each rail needs different filters/context; drawer adapts per route |
| **Prospect mode** | DOB rosters import thousands of buildings; must distinguish prospects from clients |
| **Desktop-only** | Office/admin dashboard; field-tech UX is a separate concern |

## Current Implementation

| Component | Location | Status |
|---|---|---|
| Vite SPA scaffold | `apps/web-dashboard/` | ✅ Prototype v1 |
| 3-column layout (Icon Rail → Drawer → Workspace) | `src/components/layout/` | ✅ Prototype v1 |
| Dashboard rail (Solo + Firm) | `src/pages/CommandCenter.tsx` | ✅ Prototype v1 |
| Jobs rail (list + detail + quick-create) | `src/pages/Jobs*.tsx` | ✅ Prototype v1 |
| Buildings rail (list + profile) | `src/pages/Building*.tsx` | ✅ Prototype v1 |
| Settings rail (4-tab admin) | `src/pages/Settings.tsx` | ✅ Prototype v1 |
| Context-aware drawer panels | `src/components/drawer/` | ✅ Prototype v1 |
| API integration | — | ⏳ Future |
| Real-time updates | — | ⏳ Future |
| Auth / route guards | — | ⏳ Future |
| GPS1/GPS2 form workflows | — | ⏳ Future |
