# Prototype V1 Specification

> **Tag:** `prototype-v1` · **Branch:** `prototype/web-dashboard`
> **Stack:** Vite 8 + React 19 + TypeScript + CSS Modules
> **Data:** All hardcoded mock data — no backend

## Purpose

Validate UX patterns for LL152 compliance dashboard before production implementation. Answers the question: *"Does the information architecture work for both solo plumbers and LMP firms?"*

---

## Rail Specifications

### Dashboard

| View | Solo | Firm |
|---|---|---|
| Hero | Next-stop card (address, time, contact) | Stat strip (active, unassigned, completed) |
| Queue | Today's jobs sorted by time | Team status cards (on-site, in-transit, available) |
| Paperwork | Filing due (GPS1/GPS2 pending) | Dispatch queue (unassigned jobs) |
| Deadlines | Due soon (≤14 days) | Deadline alerts + filing status |

**Drawer:** Solo shows schedule + action items; Firm shows team status + ops snapshots.

---

### Jobs

**List Views:**
- **Table** — Columns: Job #, Type, Building, Status, Priority, Scheduled, Filing. Color-coded deadlines.
- **Schedule/Agenda** — Groups: Today, Tomorrow, This Week, Later, Unscheduled (dispatch holding area)

**Detail Page (section-based):**
1. Site & Contact (building, owner, super)
2. Schedule & Assignment
3. Compliance Chain Tracker: `Inspected → GPS1 → GPS2 → Closed`
4. Notes (placeholder)
5. Timeline (actual dates)

**Quick-Create Modal:** Building select, date/time, priority, notes, assign-to (firm only).

**Drawer:** Status, priority, assignment, filing status filters.

---

### Buildings

**List Views:**
- **Table** — Columns: Address, BIN, Gas, Obligation, Next Due (color-coded), Last Inspected, Jobs, Filings. Prospect rows dimmed.
- **Cards** — Gas indicator, obligation badge, prospect badge, due date.

**Building Profile (`/buildings/:bin`):**
1. Header (address, BIN, badges, "+ New Job")
2. Contact & Ownership (owner, super with phones)
3. Compliance Status (cycle, next due countdown, last inspected, prior filings, filing chain tracker)
4. Job History table (clickable rows → Job Detail)
5. Notes (placeholder)

**Drawer:** Search, borough, obligation status, gas status, due window (overdue/30d/90d), client type (active/prospect).

---

### Settings

**4-tab admin area:**

| Tab | Contents |
|---|---|
| Organization | Company profile + compliance config (signatory, seal, GPS templates, filing borough) |
| Team & Permissions | Role table with permission tags (firm); indie message (solo) |
| Notifications | 7 categories × 3 channels (Email/SMS/In-App) toggle grid |
| Data & Integrations | Import center, data quality cards, integration status, filing defaults |

**Solo/Firm toggle** demoted to bottom as "⚡ Prototype Control" with explanatory text.

---

## Mock Data Model

```
MockJob (7 records)
├── identity: id, jobNumber, jobType, sourceKind
├── assignment: buildingBin, assignedTo, status, priority
├── schedule: scheduledFor, scheduledTime, deadline
└── filing: inspectionCompletedAt, gps1SentToOwnerAt, gps2FiledWithDobAt, correctionRequired

MockBuilding (9 records, 2 prospects)
├── identity: bin, address, borough, communityDistrict
├── obligation: obligationStatus, cycleKey, subcycle, gasStatus
├── contacts: ownerName/Phone, superName/Phone
└── compliance: lastInspectionDate, nextDueDate, priorFilingsCount, isProspect

MockTechnician (3 records)
└── id, name, role, status

MockActivity (7 records)
└── id, type, description, timestamp, jobNumber
```

**Derived helpers:** 10 functions for filtering, grouping, and cross-referencing.

---

## File Architecture

```
apps/web-dashboard/src/
├── App.tsx                     # 7 routes
├── lib/
│   ├── context.tsx             # AppProvider (mode, theme)
│   └── mock-data.ts            # Types, data, helpers
├── components/
│   ├── layout/                 # AppShell, ContextDrawer, IconRail
│   ├── drawer/                 # 4 route-specific panels
│   ├── ui/                     # StatusBadge, MetricCard
│   └── QuickCreateJob.tsx      # Modal
└── pages/
    ├── CommandCenter.tsx        # Dashboard
    ├── JobsList.tsx + JobDetail.tsx
    ├── Buildings.tsx + BuildingProfile.tsx
    └── Settings.tsx
```

---

## What V2 Should Address

Based on research findings not yet prototyped:

1. **Calendar view** on Jobs rail (week/month schedule)
2. **Map view** on Buildings rail (geographic clustering)
3. **GPS1/GPS2 form workflow** (field capture → review → file)
4. **Client/contact management** (beyond building-level contacts)
5. **Notification badges/indicators** in icon rail
6. **Responsive sidebar** (collapse drawer on narrow viewports)
7. **Data table sorting/pagination** (currently static)
