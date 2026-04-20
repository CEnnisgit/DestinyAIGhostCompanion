# ADR 0021: Client-Centric Portfolio (Not Building-Centric)

**Date**: 2026-03-26  
**Status**: Accepted  
**Context**: Domain research during Phase 1.5 Tenant Foundation design. Supersedes the draft `TenantAsset_Aggregate.md`.

## Problem

The original tenant portfolio model was designed as `TenantAsset(FirmID, BIN)` — a firm's relationship with a single building. This was assumed from CRM patterns, not validated against how plumbers actually work.

Domain research (interviews with an independent LMP on Staten Island) revealed that this model is wrong. The real relationship unit is not the building — it's the **client**.

## Evidence

### Snug Harbor (Recurring Client, Many Buildings)

Danny Vega is on the vendor list for Snug Harbor Cultural Center on Staten Island — a campus with multiple buildings. He gets many different jobs from this one place. When he has questions or needs to confirm job status, he calls **one person — the facilities manager**.

**What this proves:** Danny's relationship is with the client (Snug Harbor), not with individual buildings. The buildings are just locations where jobs happen. Contact info and the vendor relationship live at the client level.

### Emergency Leak Caller (One-Off Client, One Building)

During an LL152 workday, Danny received a cold call from an unknown person with an emergency leak, referred by a friend. He accepted the job on the spot and asked only for: (1) the address, (2) a phone number.

**What this proves:** The building entered Danny's world because of a job, not because of a portfolio adoption step. The "relationship" is with the person who called (a client, even if one-time), not with the building itself.

### Pre-Planned LL152 Day (Scheduled Jobs, Known Clients)

Danny's LL152 inspections were on Google Calendar, scheduled days in advance. The buildings were already known because an earlier client interaction set up the job.

**What this proves:** Even for planned work, the entry point was a client requesting service — not the plumber browsing buildings and "adopting" them.

## Decision: Tenant Portfolio Is Client-Centric

The portfolio model should center on **clients**, not buildings.

The old model:
```
TenantAsset(FirmID, BIN) ← wrong abstraction
```

The correct model:
```
Client(company_id) → has many Buildings
Job(company_id, client_id, building_id) → work done at a building for a client
```

### Key principles:
1. A **client** is the person or entity who commissions work (building owner, property manager, facilities manager).
2. A client may control one building (individual owner) or many buildings (property management company, campus).
3. **Buildings don't need "adoption."** Buildings are global locations. A client *has* a relationship with buildings. A job *happens at* a building *for* a client.
4. **Contact info lives on the client**, not on individual buildings. "The lady at Snug Harbor" is a client contact.
5. A firm's portfolio is their **client list**, not their building list.

## What This Changes

- **`TenantAsset(FirmID, BIN)`** is retired as a concept. It was the wrong abstraction.
- The new concept is `Client(company_id)` with a relationship to buildings via jobs (and potentially a direct many-to-many for "this client manages these buildings").
- The Job aggregate's `client_id` field (currently nullable UUID, future FK) becomes more important — it's the link to the client who commissioned the work.
- The web-dashboard prototype's "Portfolio" page should show **clients**, not buildings. Buildings appear underneath a client.

## Open Questions (Not Yet Decided)

These are being researched in [TENANT_PORTFOLIO_RESEARCH.md](../2-during-implementation/DDD/ModuleDesign/CRM/Operations/Research/TENANT_PORTFOLIO_RESEARCH.md):

1. Does the plumber consider one-off callers as "clients," or only recurring ones?
2. Can one building have different clients at different times?
3. What data lives on the Client vs on the Job?
4. Is a separate Client entity necessary, or can "client" be derived from job history?
5. Minimum viable Client model for alpha (2 users)?

## Impact on Domain Model

- **Job Aggregate:** No breaking change — already has `client_id` (nullable UUID). The field becomes required or more meaningful once the Client entity exists.
- **Building Aggregate:** No change — buildings remain global, identity-only.
- **TenantAsset draft:** Superseded. Should not be implemented as designed.
- **CRM/Operations module:** Reimagined as client management, not building adoption.
- **Phase 1.5 spec:** Will be revised after research completes.

## References

- [ADR-0017: Independent Plumber Tenancy](0017-independent-plumber-tenancy.md)
- [ADR-0018: Client Account vs Requester Contact](0018-client-account-vs-requester-contact.md)
- [ADR-0020: Multi-Tenancy Database Isolation](0020-multi-tenancy-database-isolation.md)
- [Tenant Portfolio Research](../2-during-implementation/DDD/ModuleDesign/CRM/Operations/Research/TENANT_PORTFOLIO_RESEARCH.md)
