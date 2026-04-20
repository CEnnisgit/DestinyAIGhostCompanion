# ADR 0022: Building Bookmarks (Saved Buildings)

**Date**: 2026-03-26  
**Status**: Accepted  
**Context**: Design discussion during Phase 1.5 Tenant Foundation. Follows [ADR-0021 (Client-Centric Portfolio)](0021-client-centric-portfolio.md).

## Problem

ADR-0021 established that the tenant portfolio is client-centric. A firm's "portfolio" is their client list. Buildings are referenced through jobs and optionally linked to clients.

But there's a gap: **what if a firm finds a building in the Explorer that they want to save, before they have a client or a job for it?**

Example: A firm's office staff browses the Explorer, sees a building on the LL152 roster (cycle B, coming up next year), and thinks "we should remember this one — maybe reach out to the owner." There's no client yet. There's no job. They just don't want to lose the building.

Without a mechanism for this, the firm would have to:
- Create a placeholder client with no real name (clutters client list)
- Create a draft job (misrepresents intent — no work has been agreed to)
- Write it down somewhere else (defeats the purpose of the software)

## Decision: Building Bookmarks

A firm can **bookmark** a global building. A bookmark is a lightweight, client-independent save that says "I'm interested in this building."

### What a bookmark is:
- A link between a `company_id` and a `building_id`
- Minimal: no required metadata beyond the link itself
- A staging area — a bookmarked building can later be linked to a client or have a job created for it

### What a bookmark is NOT:
- Not a claim of ownership or relationship
- Not a CRM pipeline stage
- Not a substitute for the Client entity
- Not required before creating a job (jobs can be created directly)

### How bookmarks relate to clients:

```
bookmark (no client yet)     →  can be promoted to a client-building link
client-building link         →  "this client manages this building"
job                          →  auto-creates client-building link
```

A bookmark is the **earliest, lightest** form of interest. It can evolve into a client relationship, or be removed if the firm decides they're not interested.

## Rationale

1. **Low friction:** A single click from the Explorer saves a building. No forms, no client creation, no job creation.
2. **Foundation for future features:** Bookmarks can evolve into prospect tracking, notifications ("this bookmarked building just entered LL152 cycle B"), or outreach workflows — without redesigning the data model.
3. **Doesn't interfere with Client model:** Bookmarks are orthogonal to clients. A building can be bookmarked AND linked to a client, or just one, or neither.
4. **Alpha-appropriate:** Simple enough for Phase 1.5 — just a junction table.

## Schema

```sql
CREATE TABLE saved_buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    building_id UUID NOT NULL REFERENCES buildings(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(company_id, building_id)
);

CREATE INDEX idx_saved_buildings_company ON saved_buildings(company_id);
```

No additional fields for alpha. If needed later, columns like `note` or `source` ("where did I find this?") can be trivially added.

## Consequences

**Positive:**
- Explorer has a clear action: "Save this building" — without forcing premature client/job creation.
- Establishes a building-level interest signal that can feed future features.
- Ultra-simple — one table, one constraint, minimal API surface.

**Negative:**
- Another entity to maintain alongside clients and jobs.
- Risk of bookmarks accumulating without action (stale saves). Mitigated by keeping the UI light and non-critical.

## Impact on Domain Model

- **Explorer UI:** Gets a "Save" / "Bookmark" button per building.
- **Client Aggregate:** No change — clients don't know about bookmarks.
- **Job Aggregate:** No change — jobs don't require bookmarks.
- **New API routes:** `POST /api/saved-buildings`, `DELETE /api/saved-buildings/:id`, `GET /api/saved-buildings`.

## References

- [ADR-0021: Client-Centric Portfolio](0021-client-centric-portfolio.md)
- [Tenant Portfolio Research](../2-during-implementation/DDD/ModuleDesign/CRM/Operations/Research/TENANT_PORTFOLIO_RESEARCH.md)
