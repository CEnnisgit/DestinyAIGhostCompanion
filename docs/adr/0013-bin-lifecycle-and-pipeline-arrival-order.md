# ADR-0013: BIN Lifecycle and Pipeline Arrival Order

**Status:** Accepted  
**Date:** 2026-03-12  
**Deciders:** Development Team

## Context

NYC DOB periodically **supersedes Building Identification Numbers (BINs)**. When a building receives a new canonical BIN, the old BIN is retired and marked *"OBSOLETE BIN RETAINED FOR HISTORICAL PURPOSE ONLY"* in DOB systems. The new BIN becomes the active identity for all current compliance tracking.

This was discovered empirically during development:

- BIN `4623977` appeared on the **LL152 compliance roster** before PAD 25A had any record of it.
- BIN `4056950` shared the same physical address but was marked obsolete on DOB NOW.
- PAD **25A** still referenced the old BIN — `4623977` had no address data after that ingestion.
- PAD **25B** caught up: `4623977` gained its address, and a `PAD_UPDATE_25A` event appeared in its history.

This reveals that **LL152 can reference BINs that PAD has not yet onboarded**, due to the asynchronous release cadence of DOB's data exports. The DOB compliance roster (LL152) tracks active obligations using the *current* canonical BIN, while PAD's address data may still lag by one or more release cycles.

## Decision

**The system shall allow LL152 (and other compliance pipelines) to stub-create buildings for BINs unknown to PAD, and treat those stubs as valid first-class records that PAD will retroactively enrich.**

Concretely:

1. During `flush_compliance_payloads`, the LL152 pipeline performs `INSERT INTO buildings ... ON CONFLICT (bin) DO NOTHING`. If the BIN does not exist, a minimal stub is created with `created_from_source = 'DOB_LL152'`.
2. The stub has no address, borough, or BBL data — only a BIN and its compliance obligations.
3. When PAD subsequently ingests the same BIN, it enriches the record in place. A `PAD_UPDATE_*` building event is recorded.
4. The UI distinguishes stub buildings via the `createdFromSource` field (e.g., the "PAD VERIFIED" badge only appears when PAD has touched a record).
5. No attempt is made to resolve BIN supersession automatically. The old BIN (`4056950`) and new BIN (`4623977`) remain as separate database records. The relationship between them, if it needs to be tracked, is a future concern (Pipeline C / Geoclient verification).

## Consequences

### Positive

- Compliance obligations are captured immediately when the LL152 roster is ingested, regardless of whether PAD has acknowledged the BIN yet.
- The system remains resilient to the reality that DOB data sources are asynchronous and do not share a release cadence.
- The unified event timeline in the Building Detail Panel makes the enrichment lifecycle visible — users can see `OBLIGATION_CREATED` events before any `PAD_UPDATE_*` events appear.
- The `createdFromSource` field provides a reliable signal in the UI: a building with `DOB_LL152` as its source and no address is a stub awaiting PAD enrichment.

### Negative

- Stub buildings appear in the Building Explorer with incomplete data, which can be confusing without clear UI signposting.
- Superseded BINs (e.g., `4056950`) and their replacement (e.g., `4623977`) are **not linked** in the database. If a firm had tracked custom data against the old BIN, that data is not automatically associated with the new one.
- The system has no mechanism to detect or alert on BIN supersession events — this is a known gap until Pipeline C (Geoclient verification) is implemented.

## Alternatives Considered

### Reject LL152 rows with unknown BINs

**Rejected because:** It would cause compliance obligations for real, active buildings to be silently dropped whenever LL152 is ahead of PAD. This is unacceptable — compliance tracking cannot depend on PAD's release cadence.

### Queue unknown BINs for deferred processing

Hold LL152 rows with unknown BINs in a staging table and reprocess them after PAD runs.

**Rejected because:** It introduces significant complexity (a deferred job queue, failure modes, re-processing logic) for a problem that the stub-creation approach already solves adequately and idiomatically.

### Resolve BIN supersession at ingestion time via DOB API lookup

Call the Geoclient or DOB BIS API during ingestion to check whether a BIN is a supersession and link old → new.

**Rejected because:** This requires real-time API calls inside a batch pipeline, introduces latency and failure modes, and is the explicit responsibility of Pipeline C (Geoclient Verification). The ingestion pipelines are intentionally kept offline/batch.
