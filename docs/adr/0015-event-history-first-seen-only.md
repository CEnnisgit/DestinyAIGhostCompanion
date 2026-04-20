# ADR-0015: Event History Shows First Seen Only, Not Version Membership

**Status:** Accepted  
**Date:** 2026-03-15  
**Deciders:** Development Team  
**Relates to:** [ADR-0014](0014-version-membership-junction-table.md)

## Context

After replacing `PAD_UPDATE_*` events with the `building_pad_versions` junction table (ADR-0014), the BuildingCard Event History was updated to display version membership entries from the junction table. However, this created noise: a building present unchanged across all 4 versions (25A–25D) displayed 4 `PAD_VERSION_*` entries, implying something happened in each version when nothing actually changed.

This conflated two distinct concepts:

1. **Version membership** — "this building exists in this PAD version" (a fact, not an event)
2. **Event history** — "something happened to this building" (a state change)

## Decision

**The Event History only shows the building's first version membership — when it was first seen in PAD — not subsequent unchanged memberships.**

Concretely:

- The `getUnifiedTimeline` query fetches only `LIMIT 1` from `building_pad_versions` ordered by `first_seen_at ASC`, producing a single "First seen in PAD 25A" entry.
- All 4 version rows remain in the junction table for the Identity Lifecycle Filter, future timeline slider, and any analytics queries.
- `PAD_SUPERSEDED` events remain in `building_events` and continue to appear in the Event History as before — they represent a real state change.

The Event History now displays only **meaningful state transitions**:

| Source | What it represents | Shows in Event History? |
|:--|:--|:--|
| `building_pad_versions` (first row) | Building first confirmed by PAD | ✅ Yes — "First seen in PAD 25A" |
| `building_pad_versions` (subsequent rows) | Building still present (no change) | ❌ No — not an event |
| `building_events` (`PAD_SUPERSEDED`) | Building dropped from latest PAD | ✅ Yes — real state change |
| `obligation_events` | Compliance status changes | ✅ Yes — real state change |
| `import_anomalies` | Data quality issues | ✅ Yes — diagnostic event |

## Consequences

### Positive

- Event History is clean and meaningful — only shows things that happened.
- Building detail panel loads faster with fewer entries to render.
- Clear separation: junction table = membership data, events table = change data.

### Negative

- Users cannot see the full version history of a building from the Event History alone. This information is still queryable from `building_pad_versions` and will be surfaced via a future timeline slider feature.
