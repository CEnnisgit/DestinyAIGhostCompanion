# Job Creation UX — Design Research

> **Status:** 📋 Design decisions captured — pending UI implementation
> **Phase:** 1.5 (dev dashboard), informs future web/mobile
> **ADR:** [ADR-0023: Address-First Job Creation](../../../../adr/0023-address-first-job-creation.md)

---

## The Notebook Test

> If the app is harder to use than writing in a notebook, plumbers won't use it.

Based on direct observation: Danny accepted a spontaneous emergency call, asked for the address and phone number, and wrote it in his notebook. The app must match that speed and simplicity.

---

## Creation Form: 4 Fields

| Field | Input | System behavior |
|---|---|---|
| **Address** | Free text ("88 Greenwich St") | Fuzzy search PAD buildings. Suggest matches. Allow "no match." |
| **Client** | Free text with autocomplete | Search existing clients by name. If no match → creates new Client. |
| **Phone** | Free text | Pre-fills if existing client selected. Becomes part of new Client if created. |
| **Job Type** | Dropdown | Emergency, LL152 Inspection, General Repair, etc. |

Everything else (summary, site notes, priority, compliance obligation) is **optional** and added later from the Job Detail view.

---

## Behind the Scenes

### Address → Building Resolution

1. User types address → fuzzy search fires
2. **Match found**: show suggestions, user picks one → `building_id` set
3. **No match**: job created with `building_id = NULL`, `address` stored as raw text
4. Unresolved jobs are flagged for later correction (manual or via pipeline)

### Client → Client ID Resolution

1. User starts typing client name → autocomplete fires against existing clients
2. **Match found**: user selects → `client_id` set, phone pre-fills
3. **No match**: user finishes typing → new Client auto-created (name + phone + address)

### Post-Creation

- Navigate to **Job Detail View** (confirms creation, allows adding notes)
- Show **"Create Another"** shortcut (for batch entry during planning)

---

## What This Changes on the Job Aggregate

| Field | Before | After |
|---|---|---|
| `building_id` | `UUID NOT NULL` | `UUID` (nullable) |
| `address` | Not in schema | `TEXT` (new field, user's raw input) |

The `address` field is always stored regardless of whether `building_id` is resolved. It's the user's original input and serves as the fallback when building resolution fails.

---

## Deferred from This Discussion

- **LL152 scheduled flow** — handled separately in Phase 2 (different creation path with known buildings)
- **Where the "Create Job" button lives** — depends on final web/mobile design, not dev dashboard
- **Building resolution workflow** — how unresolved jobs get matched later (manual? pipeline? notification?)
