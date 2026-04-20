# ADR-0024: Frontend Technology Stack

**Status:** Accepted  
**Date:** 2026-03-26  
**Deciders:** Marcus, AI Pair Programming  

## Context

The PCD platform has multiple frontend surfaces serving different users:

1. **Company Dashboard** — office staff managing jobs, buildings, compliance, and clients
2. **Dev Dashboard** — internal developer tool for data exploration during development
3. **Mobile Technician** — field technicians performing LL152 inspections
4. **Owner Portal** — building owners checking compliance status (Phase 2+)

The current codebase has prototypes in varying states: a Vite+React SPA (`web-dashboard`), a Next.js dev tool (`dev-dashboard`), a bare React Native app (`mobile-technician`), and deployment infrastructure on GCP Cloud Run.

We need a coherent, justified technology decision for each surface.

## Decision

| Surface | Stack | Framework |
|---|---|---|
| **Company Dashboard** | Vite + React 19 + TypeScript | SPA, react-router-dom, CSS Modules |
| **Dev Dashboard** | Vite + React 19 + TypeScript | Same as production (migrate from Next.js) |
| **Mobile Technician** | Expo (React Native) | Expo Router, expo-camera/location/sqlite |
| **Owner Portal** | Astro or Next.js (deferred) | SSR justified for public-facing content |

### Company Dashboard — Vite + React SPA

- **Auth-gated, no SEO** — every route requires authentication. Server-side rendering adds latency and complexity for zero benefit.
- **Single backend** — the Rust API (`pcd-api`) is the real backend. A Vite SPA talks directly to it. Next.js would introduce a second server layer (Node.js SSR → Rust API → Postgres), adding an unnecessary network hop.
- **Prototype-validated** — the `web-dashboard` prototype already has 9 routes, a 3-column shell, Solo/Firm mode toggle, and contextual drawers, all working in Vite+React.
- **Data fetching** — TanStack Query (react-query) for caching, refetching, and optimistic updates.

### Dev Dashboard — Same Stack

- Currently Next.js 15, but will migrate to Vite+React to match the production stack.
- Eliminates maintaining two different frontend architectures.
- Not urgent — functional as-is.

### Mobile Technician — Expo

- **Native access required** — camera for inspection photos, signature canvas, GPS for location verification, offline inspection storage.
- **Bare React Native is painful** — the old app required Xcode + Android Studio, manual signing, Gradle plugins. Expo handles native compilation via EAS Build in the cloud.
- **OTA updates** — `expo-updates` enables pushing JS updates without app store resubmission. Critical for a field app.
- **Offline-first** — `expo-sqlite` for local inspection storage, background sync when back online.
- **Ecosystem sharing** — both web and mobile are React + TypeScript. Shared types, API client, and domain logic via a `packages/` workspace.

### Owner Portal — Deferred

- Public-facing, so SSR is justified (SEO, social sharing, performance).
- Requirements not fully defined yet.
- Candidate stacks: Astro (mostly static) or Next.js (more interactivity needed).

## Consequences

- All frontend surfaces share TypeScript + React, enabling cross-app code sharing.
- The Rust API remains the single backend — no Node.js server layer in between.
- Deployment is simpler: Vite SPAs build to static files (CDN-friendly), Expo handles mobile builds.
- The `mobile-technician` directory will be deleted and rebuilt from scratch with Expo.
- The `web-dashboard-v1` directory remains archived (frozen snapshot).
