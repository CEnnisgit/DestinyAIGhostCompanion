# Tenant Portfolio — Domain Research

> **Status:** ✅ Research Complete — ready for aggregate spec design
> **Module:** `CRM/Operations` → reimagined as `CRM/Clients`
> **Phase:** 1.5 (pulled forward from Phase 3)
> **ADR:** [ADR-0021: Client-Centric Portfolio](../../../../adr/0021-client-centric-portfolio.md)

---

## Purpose of This Document

Before designing the Tenant Portfolio aggregate, we needed to understand the real domain from first principles. The old `TenantAsset_Aggregate.md` draft was built from assumptions. The web-dashboard prototype was a UX exercise.

This document captures domain research conducted through interviews with an active LMP's workflow.

---

## 1. Established Facts (from ADRs and Code)

| Fact | Source |
|---|---|
| Global data (buildings, obligations) is shared by all tenants. Tenant data is scoped by `company_id`. | [ADR-0020](../../../../adr/0020-multi-tenancy-database-isolation.md) |
| "Company" = any org unit — firm or solo plumber. | [ADR-0017](../../../../adr/0017-independent-plumber-tenancy.md) |
| Buildings are BIN-identified, PAD-populated, globally shared. | [Building Aggregate](../CRM/Assets/Building/Building_Aggregate.md) |
| Jobs reference `building_id` + `company_id`. Core game loop. | [Job Aggregate](../Jobs/Engine/Job_Aggregate.md) |
| `client_id` = account level. `requester_contact_id` = person level. | [ADR-0018](../../../../adr/0018-client-account-vs-requester-contact.md) |
| Auto-adoption on job creation was confirmed. | [TENANT_INVENTORY_CONCEPT.md](../Presentation/Research/TENANT_INVENTORY_CONCEPT.md) |

---

## 2. Real-World Domain Evidence

> Source: Direct experience working with Danny Vega, Licensed Master Plumber, Staten Island.

### Scenario A: Pre-Planned LL152 Day

Danny used Google Calendar with the day's LL152 inspections. His son drove him job-to-job so he could complete LL152 forms between stops.

- Jobs are planned ahead of time
- Buildings were already known — the client relationship existed before the job
- The entry point was a client requesting service

### Scenario B: Spontaneous Emergency Call

During the LL152 day, Danny got a call from a new person with an emergency leak (referred by a friend). He accepted on the spot and asked for: (1) the address, (2) a phone number.

- New building relationships start instantly — no "adoption" step
- The job IS the relationship
- Minimal info captured: address + phone

### Scenario C: Vendor List / Repeat Client (Snug Harbor)

Danny is on the vendor list for Snug Harbor Cultural Center — a campus with multiple buildings. He gets many different jobs from this one place. He calls **one person — the facilities manager** — for all questions.

- The meaningful relationship is with the **client**, not individual buildings
- Contact info belongs at the client level
- Danny thinks of Snug Harbor as a single client ("I'm doing work at Snug Harbor today")

### Key Insight

> [!IMPORTANT]
> The tenant portfolio is **client-centric**, not building-centric. The old `TenantAsset(FirmID, BIN)` was the wrong abstraction. The real entity is the **Client** — the person or organization who commissions work.
>
> Buildings are global locations. A client *references* buildings through jobs. The plumber's portfolio is their **client list**.

---

## 3. Domain Questions — All Answered

### Q1: What IS the entity?

**Answer: Client.** The person or organization who commissions work. Ranges from a one-off emergency caller to a property management company with many buildings on a vendor list.

### Q2: How does the relationship start?

**Answer: Through a job (or intent to create one).** Three observed paths:

| Path | Example | Client status before |
|---|---|---|
| Pre-planned | Building owner calls about LL152 → job scheduled days later | New or existing client |
| Spontaneous | Cold call with emergency leak → job accepted on spot | New client, created instantly |
| Repeat | Existing client (Snug Harbor) requests new job | Known client |

None start with "browsing the Explorer and adopting a building."

### Q3: How does the relationship end?

**Answer: It rarely ends formally.** Clients either:
- **Stay active** — recent or ongoing work
- **Go dormant** — haven't called in a while, could return
- **Get blocked** — explicitly dropped for **non-payment or unreliability** (rare)

No need for a "remove" action. Just a **flag** for blocked clients.

### Q4: Can a building be in multiple firms' portfolios?

**Answer: Yes.** Multiple firms can work at the same building for different clients.

### Q5: What data lives on the Client vs on the Job?

**Answer: Client retains minimal info between jobs:**
- **Name** (person or organization)
- **Phone number**
- **Address**

That's it. Job-level data (site_notes, summary, schedule) stays on the Job. Buildings are derived from job history. No tags, statuses, pipeline stages, or notes on the client entity.

### Q6: Do plumbers nickname buildings?

**Answer: No separate nickname needed.** The client name naturally serves as the location shorthand. "I'm doing work at Snug Harbor today" uses the client name. For individual homeowners, the address serves the same purpose.

### Q7: Where do building contacts (owner, super) live?

**Answer: On the client.** "The lady who manages everything at Snug Harbor" is a client contact, not a building contact. Per ADR-0018, `client_id` is the account level; `requester_contact_id` is the person-level for a specific job.

### Q8: Is this a tracker or a CRM?

**Answer: Simple tracker for Phase 1.5.** No pipeline, outreach, lead scoring, or sales features. Just a client list with contact info.

### Q9: Minimum viable Client for alpha?

**Answer:**

```
Client
├── name: TEXT          ← "Snug Harbor Cultural Center" or "Maria Rodriguez"
├── phone: TEXT         ← primary contact number
├── address: TEXT       ← primary address (may differ from job building)
├── is_blocked: BOOL   ← "don't work for this client" flag
└── [derived] buildings: from job history
└── [derived] job count: from job history
```

### Q10: Do we even need a separate entity?

**Answer: Yes.** A plumber wants to know "who are my clients?" separate from "what are my jobs?" Client info (name, phone) persists across jobs and would otherwise be duplicated on every job record.

---

## 4. Design Tensions — Resolved

### Tension A: Client Entity vs Derived From Jobs → **Separate entity**
Client needs to store contact info that persists across jobs. Deriving from jobs would mean no standalone client list.

### Tension B: Client-Level vs Building-Level Data → **Client-level only**
Buildings are global, not tenant-owned. All tenant-specific data lives on the Client or the Job.

### Tension C: One-Off vs Recurring Clients → **Same entity, no distinction**
Both are clients. The difference is naturally reflected by job count and recency. A "vendor list" relationship is just a client with many jobs over time — no special status needed.

---

## 5. Impact: Old TenantAsset Draft Is Superseded

The following from the old draft are **retired**:

| Old Concept | Why it's wrong |
|---|---|
| `TenantAsset(FirmID, BIN)` | Wrong unit — should be Client, not Building |
| `nickname` field | Client name serves this purpose |
| `internalStatus` (tracked/prospect/active_client/do_not_contact) | CRM pipeline thinking; not how plumbers work. Only need `is_blocked`. |
| `tags[]` | No real-world use case identified |
| `bucketId` | Project management scope creep |
| `notes` on portfolio link | Notes belong on Jobs, not on a portfolio link |

---

## 6. Next Steps

1. ✅ Domain questions answered
2. **Write Client aggregate spec** — following Building/Job pattern (Objective → Core Decisions → Attributes → Behavior → Persistence)
3. **Revise Phase 1.5 spec** — swap TenantAsset for Client
4. **Industry research** (optional) — validate against Jobber/ServiceTitan patterns
