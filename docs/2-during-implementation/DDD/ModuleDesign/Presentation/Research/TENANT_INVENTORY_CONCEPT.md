# ⚠️ SUPERSEDED — Historical Reference Only

> **This document is outdated.** The TenantAsset model it discusses has been replaced by:
> - [ADR-0021: Client-Centric Portfolio](../../../../adr/0021-client-centric-portfolio.md) — clients, not buildings
> - [ADR-0022: Building Bookmarks](../../../../adr/0022-building-bookmarks.md) — lightweight building saves
> - The "Portfolio" rail concept discussed below was adopted (Option 3), holding both Clients and Saved Buildings.
>
> Kept for historical context on the design exploration process.

---

# Tenant Inventory — Concept Exploration (SUPERSEDED)

## Existing Reference (Draft)

The [TenantAsset Aggregate](file:///c:/github/pcd/docs/2-during-implementation/DDD/ModuleDesign/CRM/Operations/TenantAsset_Aggregate.md) in `CRM/Operations` captures the core concept: a firm's relationship with a global building, keyed by `(FirmID, BIN)`.

> [!WARNING]
> TenantAsset is a **draft placeholder** from an earlier planning phase. Its field list (nickname, internalStatus, tags, notes, bucketId) is directional but not ground truth. Treat it as a starting point to evolve, not a spec to implement literally.

---

## Confirmed Decisions

| Question | Decision |
|---|---|
| Explorer vs. My Buildings | **Separate views** — not tabs within one rail |
| Auto-adoption on job creation | **Yes** — creating a job for a building auto-creates the TenantAsset |
| TenantAsset fields | **Draft only** — field list will be refined when this gets built |
| Contact ownership | TenantAsset was a placeholder — contacts will be designed properly in a future phase |
| Prospect workflow | **TBD** — user wants notifications/alerts for inventory buildings for sure |
| Profile merging | **TBD** — needs pros/cons analysis (see below) |

---

## Open: Where Does "My Buildings" Live?

Buildings Explorer gets its own rail ✅. But "My Buildings" (the tenant inventory) needs a home. Four options:

### Option 1: Dashboard Rail

```
Dashboard
├── Solo "My Day" — next stop, queue, paperwork, deadlines
├── Firm "Ops Console" — stat strip, team, dispatch, filing
└── [NEW] My Buildings section — compact list of active buildings
```

**For:**
- Dashboard is already "what matters to me today"
- Buildings with upcoming deadlines naturally surface here
- No new rail — keeps navigation simple
- Solo plumber with 10 buildings sees them alongside today's queue

**Against:**
- Dashboard is action-oriented (today's work), not reference-oriented (my portfolio)
- Firm with 200 buildings can't show them all — needs its own search/filter
- Mixing operational dashboard with inventory management muddies the purpose

### Option 2: Jobs Rail (as context)

```
Jobs
├── Job List (Table / Schedule)
├── Job Detail
└── [NEW] Building context — "My Buildings" as a filter/grouping dimension
```

**For:**
- Jobs are always *about* a building — natural pairing
- "Show me all jobs for this building" is already a need
- building-grouped job view could serve both purposes

**Against:**
- Jobs rail is about *the work*, not *the asset*
- "Add a building to my inventory" doesn't feel like a Jobs action
- Overloads an already feature-dense rail

### Option 3: New "Portfolio" or "Inventory" Rail

```
Icon Rail: 🏠 Dashboard | 📋 Jobs | 🏢 Explorer | 📂 Portfolio | ⚙ Settings
```

**For:**
- Clean separation of concerns
- Portfolio = "my buildings + my contacts + my prospect pipeline"
- Could grow into a full CRM view (outreach, client management)
- Dedicating a rail signals that building inventory management is a first-class concept

**Against:**
- 5th rail — more navigation, more cognitive load
- For a solo plumber with 15 buildings, a whole rail might feel like overkill
- Risk of the Portfolio rail becoming a "junk drawer" for everything CRM-related

### Option 4: Buildings Rail with Scope Toggle (Explorer ↔ My Buildings)

```
Buildings Rail
├── Scope: [Explorer] [My Buildings]  ← top-level toggle, not tabs
├── Explorer: PAD-backed search (~1M)
└── My Buildings: Tenant inventory (~10-200)
```

**For:**
- One rail for all building-related work
- Conceptually clear: "Buildings" means buildings regardless of scope
- Explorer is where you *find* buildings, My Buildings is where you *work* them
- Toggle at the top, not tabs — feels like a filter/scope, not two different pages

**Against:**
- The user said "separate, not tabs" — this is close to tabs
- Two very different data sources and scales behind one rail
- Drawer filters would need to change dramatically between modes

---

### Recommendation

**Option 3 (New Rail)** or **Option 4 (Scope Toggle)** are the strongest.

The key question: Does the tenant inventory *deserve its own rail*, or is it a *scoped view of buildings*?

If the inventory grows to include contacts, outreach tracking, prospect pipeline, and bucket organization — it's a **CRM rail** (Option 3). That's where the `CRM/Operations` sub-module points.

If the inventory stays focused on "which buildings am I working" with lightweight overlay — it's a **scoped buildings view** (Option 4), and the scope toggle is different from tabs because it changes the underlying data source, not just the display format.

---

## Open: Building Profile Merging — Pros/Cons

When a user clicks on a building, should the detail page be the same component regardless of adoption status?

### Option A: Same Component, Adaptive Content

| Aspect | Pro | Con |
|---|---|---|
| **Development** | One component to maintain | Conditional logic gets complex |
| **UX continuity** | User clicks "88 Greenwich" and always lands on the same page, whether from Explorer or Inventory | Might confuse user about what's editable vs. read-only |
| **Adoption CTA** | Pre-adoption: shows global data + "Add to My Buildings" button. Post-adoption: shows global + overlay | Need clear visual distinction between "viewing" and "managing" |
| **Data density** | Gracefully grows from sparse (explorer) to rich (inventory) | Risk of the explorer view looking "empty" before adoption |

### Option B: Separate Pages

| Aspect | Pro | Con |
|---|---|---|
| **Clarity** | Explorer has a "Building Card" (read-only snapshot). Inventory has a "Building Profile" (full management) | Two components to build and maintain |
| **Permission model** | Explorer page has no edit affordances — zero confusion | Navigating from Explorer → Profile after adoption means a URL/route change |
| **Feature growth** | Inventory profile can grow without polluting the explorer's simpler view | Duplicated header/identity section across both |
| **URL structure** | `/explorer/:bin` vs `/portfolio/:bin` — clean routing | User might not understand why the "same" building has two different pages |

### Option C: Shared Shell, Pluggable Sections

```
BuildingPage (shared)
├── Header: BIN, Address, Borough (always)
├── Identity Card: BBL, CD, Condo (always)
├── [IF adopted] Tenant Overlay: Status, Tags, Notes, Contacts
├── [IF adopted] Job History
├── Compliance Obligations (always, from global)
├── [IF NOT adopted] "Add to My Buildings" CTA
```

| Aspect | Pro | Con |
|---|---|---|
| **Best of both** | One route, one shell, sections appear/disappear based on adoption | Most complex to implement |
| **Progressive disclosure** | Explorer users see what they need. Inventory users see the full picture | Still need clear visual signal of "this is YOUR data vs. global data" |
| **Natural adoption flow** | Click "Add to My Buildings" → tenant sections appear in-place | Testing is harder — need to verify both states |
