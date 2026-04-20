# Interface Design: UI Specifications

> **Source of Truth:** `apps/dev-dashboard/` (implemented) | Other apps are future work
> **Scope:** [Pilot Core (LL152)](file:///c:/github/pcd/docs/PILOT_SCOPE_CONTEXT.md)

## Overview

User Interface specifications. Only the **Dev Dashboard** is currently implemented. The Mobile App and Web Company Dashboard are planned for future phases.

---

## 1. Dev Dashboard (Implemented)

**Source:** `apps/dev-dashboard/src/`
**Framework:** Next.js 15 (React)
**Purpose:** Development-time exploration and testing of CRM data. Not a production UI.

| Page | Route | Responsibility |
| :--- | :--- | :--- |
| **Building Explorer** | `/buildings` | Search, filter, and inspect buildings. Identity Timeline filter. Building detail panel with addresses, obligations, event history, and lineage. |
| **Event Log** | `/events` | Paginated import run history with anomaly severity counts. |
| **Developer Tools** | `/dev-tools` | Database wipe/seed utilities. |

### Building Explorer Features
- **Search**: BIN exact match, address ILIKE, borough filter
- **Filters**: padVerified, introducedIn, hasObligations, Identity Timeline (state × verb × timing)
- **Detail Panel**: Building profile, addresses, compliance obligations, unified event history (building events + obligation events + anomalies + PAD version membership), BIN lineage

---

## 2. Mobile App — Technician *(future)*

**Source:** `apps/mobile-technician/` *(not yet started)*

| Screen | Responsibility |
| :--- | :--- |
| **Login** | Auth entry point |
| **Jobs List** | Lists assigned jobs for the technician |
| **Job Detail** | Job context (address, access notes) + action buttons |
| **Inspection Form** | GPS1 data capture flow |

---

## 3. Web Company Dashboard — LMP/Admin *(future)*

**Source:** `apps/web-dashboard/` *(not yet started)*

| Page | Responsibility |
| :--- | :--- |
| **Login** | Auth entry point |
| **Command Center** | KPI overview, "at a glance" status |
| **Job Management** | List, dispatch, and review jobs |
| **Buildings** | Manage buildings and customer relationships |
| **Technicians** | Manage technician profiles and invites |
| **Settings** | Company profile and configuration |

---

## User Flows *(future — production apps)*

### Dispatch Flow

1. **LMP** logs into **Web Dashboard**.
2. Navigates to **Job Management**.
3. Creates Job -> Assigns **Technician**.
4. **Technician** sees job in **Mobile App** > **Jobs List**.

### Capture Flow

1. **Technician** selects job in **Jobs List**.
2. Reviews details in **Job Detail**.
3. Taps "Start Inspection" -> Opens **Inspection Form**.
4. Completes all required sections -> Submits.
5. Job Status updates to `COMPLETED`.

### Review Flow

1. **LMP** sees "Needs Review" in **Command Center**.
2. Opens **Job Management** -> Review Panel.
3. Approves results -> Generates **Inspection Report** (PDF).
