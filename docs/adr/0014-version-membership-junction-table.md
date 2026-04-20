# ADR-0014: Replace PAD_UPDATE Events with Version Membership Table

**Status:** Accepted  
**Date:** 2026-03-15  
**Deciders:** Development Team

## Context

The PAD ingestion pipeline generated a `PAD_UPDATE_<version>` event in the `building_events` table for **every building in every run** — regardless of whether any data changed. After just 3 PAD runs (25A → 25C), this produced:

- **4.4 million rows** in `building_events`
- **884 MB** of disk (460 MB data + 424 MB indexes)
- **40 seconds per run** spent on event generation alone (52% of the Buildings phase)

Additionally, the event table had no unique constraint on `(bin, event_type)`. When the 25C pipeline was killed mid-lineage and rerun, it inserted duplicate events — 2.2M `PAD_UPDATE_25C` rows instead of 1.1M. There was no idempotency protection.

The events served two purposes:

1. **Identity Lifecycle Filter** — the "PAD Verified" state queried `PAD_UPDATE_*` events to determine which buildings appeared in a given version.
2. **BuildingCard Event History** — displayed `PAD_UPDATE_25A`, `PAD_UPDATE_25B`, etc. on the building detail timeline.

Neither use case required the full weight of an event row (UUID primary key, jsonb payload, FK to buildings). Both needed only the answer to: "was this building in this version?"

## Decision

**Replace `PAD_UPDATE_*` events with a lightweight `building_pad_versions` junction table.**

The new table uses a composite primary key on `(bin, pad_version)`:

```sql
CREATE TABLE building_pad_versions (
    bin         VARCHAR(7) NOT NULL REFERENCES buildings(bin),
    pad_version TEXT       NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (bin, pad_version)
);
```

Concretely:

1. The Rust pipeline's `flush_buildings` now inserts into `building_pad_versions` with `ON CONFLICT (bin, pad_version) DO NOTHING` instead of inserting `PAD_UPDATE_*` events.
2. Version membership is recorded in **both bootstrap and non-bootstrap modes** (the old events were skipped during bootstrap).
3. The Identity Lifecycle Filter's "PAD Verified" state queries `building_pad_versions` using `MIN(pad_version)` subqueries to correctly distinguish "became" from "remained."
4. The BuildingCard Event History displays version membership entries from the junction table alongside `PAD_SUPERSEDED` events and obligation events.
5. `PAD_SUPERSEDED` events (2,713 rows from lineage reconciliation) remain in `building_events` — they are sparse, meaningful, and used by the lineage process.

## Consequences

### Positive

- The composite primary key makes ingestion **idempotent** — rerunning the same version cannot create duplicates.
- Disk usage is dramatically reduced: ~16 MB per version vs. ~220 MB with events.
- The Identity Lifecycle Filter gains proper "became" vs. "remained" semantics via `MIN(pad_version)`, which was not possible with the old event-based approach.
- The junction table directly supports a future **timeline slider** feature (e.g., "show me all buildings as of version 25B").
- Version membership is recorded during bootstrap mode, closing a data gap where 25A buildings had no event record.

### Negative

- `PAD_UPDATE_*` events no longer appear in `building_events`. Any code that queries `building_events` for PAD update history must be updated to query `building_pad_versions` instead.
- The `building_events` table still exists and stores `PAD_SUPERSEDED` events. Care must be taken not to confuse the two data sources — version membership is in the junction table, supersession events are in the events table.
- The INSERT performance improvement was less dramatic than initially projected (~19-48s vs. ~40s, not the ~2s estimate). The composite PK index still has significant work for 1.1M rows.

## Alternatives Considered

### Keep PAD_UPDATE events but only for changed buildings

Only insert events for buildings where data actually changed between versions.

**Rejected because:** The Identity Lifecycle Filter's "Verified" state needs to know about *all* buildings present in a version, not just changed ones. Change-only events would break the "became verified in 25C" query.

### Use the `buildings.pad_version` column directly

The `pad_version` column on the buildings table already stores the last-seen version.

**Rejected because:** It only stores the *latest* version and overwrites on each run. It cannot answer "was this building in 25A AND 25C but not 25B?" — information needed for the future timeline slider and for "became verified before X" queries.

### Truncate and rebuild events per version

Delete all `PAD_UPDATE` events for the current version before re-inserting.

**Rejected because:** It doesn't solve the performance bottleneck (still writes ~1.1M rows per run) and DELETE + INSERT is actually slower than INSERT alone.
