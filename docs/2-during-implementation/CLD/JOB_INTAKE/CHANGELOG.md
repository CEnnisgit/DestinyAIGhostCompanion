# Change Log: Job Intake

> **Function:** Job Intake (SGI-MF)
> **Description:** LMP creates new LL152 job with address and access details

---

## Log Template

When adding a log entry, use this format:

```markdown
### Log XXX: <Title>
- **Significance:** [Major/Minor] | [Requirements/Design/Code]
- **Results:** Success | Failure | Approved Modification
- **Date:** YYYY-MM-DD HH:mm
- **Change Summary:** <one-line summary>
- **Detailed Changes:**
  - <bullet point>
  - <bullet point>
- **References:** SFR-IODE-10, etc.
- **Issue Tracking:** #123 (if applicable)
- **Author:** <name>
```

---

## Logs

### Log 001: Address-First Job Schema

- **Significance:** Major | Design
- **Results:** Success
- **Date:** 2026-03-26 18:00
- **Change Summary:** Made `building_id` nullable and added `address` text field to Job aggregate, enabling address-first creation per ADR-0023.
- **Detailed Changes:**
  - `building_id` changed from required to optional on Job aggregate
  - Added `address: String` field (required) — freeform text from the caller
  - Added `building_unresolved: bool` flag for lazy resolution
  - Job title auto-generation now uses address when building is unresolved
  - `OpenJobParams` updated with new fields
  - Migration adds `address` column and makes `building_id` nullable
- **References:** ADR-0023 (address-first job creation)
- **Issue Tracking:** N/A
- **Author:** Marcus (via Antigravity)

### Log 002: Job Creation Form (4-Field Notebook)

- **Significance:** Major | Code
- **Results:** Success
- **Date:** 2026-03-26 20:00
- **Change Summary:** Implemented CreateJobModal with address search, client autocomplete, and auto-create — the "notebook test" form.
- **Detailed Changes:**
  - New `CreateJobModal.tsx` component with 4 fields: address, client, phone, job type
  - Address field searches PAD buildings via `GET /api/buildings/search`
  - Client field filters existing clients with inline autocomplete
  - `+ New` badge appears for unrecognized client names
  - On submit: auto-creates client via `POST /api/clients` if new, then `POST /api/jobs`
  - Client phone auto-fills when existing client selected
  - Debounced search (300ms) for address input
- **References:** ADR-0023 (address-first job creation)
- **Issue Tracking:** N/A
- **Author:** Marcus (via Antigravity)

### Log 003: Client Auto-Creation in Job Flow

- **Significance:** Major | Code
- **Results:** Success
- **Date:** 2026-03-27 13:00
- **Change Summary:** Idempotent client creation via POST /api/clients returns 200/201 and inline AddClientForm in Portfolio.
- **Detailed Changes:**
  - `POST /api/clients` returns 200 for existing client (dedup by name+company), 201 for new
  - `AddClientForm.tsx` — inline 3-field form (name, phone, address) in Portfolio Clients tab
  - Dashed `+ Add Client` toggle button in ClientsTab
  - `GET /api/clients/:id/summary` endpoint returns job_count, buildings[], last_job_at
  - Client detail panel shows derived stats in summary bar
- **References:** Client_Aggregate.md §7 (dual creation paths), §9 (derived views)
- **Issue Tracking:** N/A
- **Author:** Marcus (via Antigravity)

### Log 004: Emergency and Repair Job Types

- **Significance:** Major | Design + Code
- **Results:** Success
- **Date:** 2026-03-27 14:30
- **Change Summary:** Added Emergency and Repair variants to JobType enum, expanding from 1 to 3 registered job types.
- **Detailed Changes:**
  - `JobType` enum: added `Emergency`, `Repair` variants
  - Updated `from_str`, `display_name`, `as_str` for each variant
  - Added `JobType::all()` method for UI enumeration
  - 6 new domain tests (from_str, display_name, all() coverage)
  - Frontend job type selector updated from `<select>` to combobox with 3 options
  - Total domain tests: 69/69 passing
- **References:** JobType_VO_Spec.md §4 (future candidate values → known v1 values)
- **Issue Tracking:** N/A
- **Author:** Marcus (via Antigravity)

### Log 005: Bidirectional Client-Address Intelligence

- **Significance:** Major | Code
- **Results:** Success
- **Date:** 2026-03-27 14:45
- **Change Summary:** Modal redesign with bidirectional Client↔Address intelligence — selecting a client shows their known buildings in address dropdown.
- **Detailed Changes:**
  - 3-section modal layout: Location, Client, Job Type (subtle dividers)
  - Selecting client fetches `/api/clients/:id/summary` for known buildings
  - Client's buildings appear as pinned dropdown section in address field
  - Auto-fills address if client has exactly 1 known building
  - Each resolved field has independent ✕ clear button (no cascading side effects)
  - Enter key submits form, ↵ hint on Create button
- **References:** ADR-0023 (notebook test), Client_Aggregate.md §9 (derived views)
- **Issue Tracking:** N/A
- **Author:** Marcus (via Antigravity)
