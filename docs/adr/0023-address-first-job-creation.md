# ADR 0023: Address-First Job Creation with Graceful Degradation

**Date**: 2026-03-26
**Status**: Accepted
**Context**: UX design discussion for the job creation flow during Phase 1.5.

## Problem

The current Job aggregate requires `building_id` (UUID, NOT NULL). This means a building must be identified and resolved before a job can be created.

But real-world plumber workflows don't start with a building ID. They start with a phone call: *"I have a leak at 88 Greenwich St."* The plumber needs to create the job **immediately** — while on the phone, while driving, while busy. They can't stop to search a database for the correct BIN.

If the system blocks job creation because it can't match the address to a building, the plumber falls back to pen and paper. The app fails the **notebook test**: if it's harder than writing in a notebook, plumbers won't use it.

## Evidence

From direct observation of an LMP's workflow (Danny Vega, Staten Island):

> Danny received a spontaneous emergency call. He accepted the job on the spot and asked only for: the address and a phone number. He wrote it in his notebook and kept driving.

The notebook captured: **what** (emergency leak), **where** (address), **who** (name + phone). No BIN, no building lookup, no system interaction.

## Decision: Address-First, Building-Optional

### 1. Job creation takes an address, not a building_id

The user types a street address. The system performs fuzzy search against the PAD buildings database to suggest matches. The user picks a match — or doesn't.

### 2. `building_id` becomes nullable on the Job aggregate

```sql
ALTER TABLE jobs ALTER COLUMN building_id DROP NOT NULL;
```

A job can exist without a matched building. The address is always stored as free text.

### 3. Unresolved jobs are flagged, not blocked

If no building match is found (or the user skips selection), the job is created with:
- `building_id = NULL`
- `address = "88 Greenwich St"` (raw user input, new field)
- An internal flag or derived status: **building_unresolved**

The system surfaces unresolved jobs for later correction — when the plumber is free, or when the office staff reviews the day's work. This can also be auto-resolved by future pipeline runs (Geoclient, PAD updates).

### 4. Client creation is inline

The same form captures client info (name, phone). The system autocompletes against existing clients. If no match, a new Client is auto-created. This matches the "one form, one action" principle from the notebook test.

## The Notebook Test

> If the app is harder to use than writing in a notebook, plumbers won't use it.

The job creation form has **4 fields**:
1. **Address** — where (fuzzy search with optional building match)
2. **Client** — who (autocomplete, inline creation)
3. **Phone** — contact info (pre-fills for existing clients)
4. **Job Type** — what (dropdown: Emergency, LL152, General Repair)

Everything else (summary, site notes, priority, compliance obligation) is optional and can be added later from the Job Detail view.

## Consequences

**Positive:**
- Plumber can create a job in seconds — matches notebook speed
- No friction from address resolution failures
- Data quality improves over time (auto-resolution from pipelines)
- Client records build up naturally through job creation

**Negative:**
- `building_id` is no longer guaranteed on Job — queries and views must handle NULL
- Need a "building resolution" workflow (manual or automated) for unresolved jobs
- New `address` text field needed on the Job (currently only has `building_id`)

## Impact on Domain Model

- **Job Aggregate**: `building_id` becomes `Option<Uuid>`. New `address: Option<String>` field.
- **Job Aggregate Spec**: Must be updated to reflect nullable building_id.
- **Job creation API**: New field `address` in CreateJobRequest. `building_id` becomes optional.
- **Dev Dashboard**: Job creation form redesigned around address input.
- **Building search API**: Fuzzy address search endpoint (may already exist in CRM routes).

## Post-Creation Behavior

After a job is created, the user is taken to the **Job Detail View** with a **"Create Another"** shortcut for batch entry scenarios (e.g., planning tomorrow's LL152 day).

## References

- [ADR-0021: Client-Centric Portfolio](0021-client-centric-portfolio.md)
- [ADR-0018: Client Account vs Requester Contact](0018-client-account-vs-requester-contact.md)
- [Tenant Portfolio Research](../2-during-implementation/DDD/ModuleDesign/CRM/Operations/Research/TENANT_PORTFOLIO_RESEARCH.md)
