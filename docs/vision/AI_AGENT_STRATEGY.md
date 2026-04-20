# AI Agent Strategy — North Star Vision

**Status:** Vision Document (not a spec)  
**Date:** 2026-03-27  
**Author:** Marcus + AI Pair Programming  
**Audience:** Future self, contributors, investors

---

## Why This Document Exists

PCD is not just a plumbing operations app. It is a **data platform** that consolidates everything a plumber touches into one structured system — and then makes that data actionable through AI.

This document captures the long-term AI vision so that every architectural decision made today can be evaluated against where the product is going. Nothing in this document needs to be built for alpha. But everything in this document should be *possible* given the foundation we're laying.

---

## The Core Thesis

### The Problem: Fragmented Work

A plumber's work today is scattered across 6+ disconnected tools:

| Tool | What It Holds | Problem |
|---|---|---|
| Paper notebooks | Job notes, site observations, phone numbers | Not searchable, easy to lose |
| LMP's proprietary app | Inspection submissions, forms | Locks submissions, can't fix mistakes, no data ownership |
| Text messages / calls | Client communication, scheduling | No record tied to jobs |
| Spreadsheets | Obligation tracking, billing, schedules | Manual, error-prone, out of date |
| DOB website | Compliance deadlines, roster status | Requires manual lookup, no alerts |
| Camera roll | Inspection photos, building evidence | Photos from different jobs mixed together |

An AI agent trying to help a plumber across these fragmented tools sees **nothing useful**. It can't connect a photo to an inspection, a building to an obligation, or a client to a job. The data is unstructured, scattered, and owned by different parties.

### The Opportunity: One Consolidated Platform

PCD brings everything into one structured system:

- **Buildings** — canonical identity, address, BIN, BBL, compliance history
- **Clients** — contact cards, job history, building portfolios
- **Obligations** — compliance deadlines, program codes, cycle windows
- **Jobs** — type-specific workflows, status tracking, domain events
- **Inspections** — structured findings, categorized observations, timestamped photos
- **Events** — full audit trail of every action, every transition, every change

An AI agent sitting on top of PCD has **complete context** about a plumber's business. It can answer questions, create jobs, review findings, flag compliance issues, and surface insights — because it can see everything, in one place, with structure.

### The Moat

> **The value of an AI agent is proportional to the quality and completeness of the data it can access.**

A competitor could build a better chatbot. But they can't give it access to a plumber's consolidated operational data unless they also build the platform. PCD is the platform. The AI is what makes the platform extraordinary.

---

## Three Layers of AI

### Layer 1: The Data Platform (Alpha)

**No AI.** This is the structured data foundation. Every domain object is well-typed, every operation goes through a clean API, every state change emits a domain event.

The platform delivers value immediately without AI:
- The QI can fix his own mistakes (recall transition)
- Photos are tied to specific findings, not floating in a camera roll
- Jobs are tracked through a clear workflow with audit trail
- Compliance obligations surface what's due and when

**Technical foundation for AI:**
- DDD with well-defined aggregates → clean tool surface for agents
- REST API with typed endpoints → agent calls the same API as humans
- Domain events → agent can consume/react to state changes
- Extension tables → AI features are additive, never invasive
- Unconstrained TEXT fields → AI has rich narrative to work with

### Layer 2: AI Review Agent (Beta — Advanced Tier)

**What it does:** Reads the QI's field notes and photos after capture, flags compliance issues the QI might have missed, and suggests `requires_correction` and `requires_immediate_reporting` flags.

**The real-world pain point it solves:**

A QI walks a building and writes quick notes in the field:

> *"found flexable hose behind stove, looked worn, gas smell present near meter"*

The notes are informal, misspelled, abbreviated. The QI is standing in a basement with a flashlight, not composing formal prose. Today, parsing these notes for compliance implications is entirely manual — the QI has to mentally connect "gas smell" to "requires immediate reporting per DOB rules."

The AI review agent does this automatically:

1. Reads `narrative_detail` from each finding
2. Consults the company's **configurable rules** (a `workflow.md` file or rules table that defines what conditions trigger immediate reporting, what requires correction, etc.)
3. Suggests flag values: `requires_immediate_reporting = true`, `requires_correction = true`
4. The QI or LMP reviews and accepts/overrides the AI's suggestions

**Company-configurable rules:**

Different companies may have different thresholds. One company might flag any mention of "smell" or "odor" as immediate reporting. Another might only flag confirmed gas leak readings. The rules file lets each company tune the AI to their workflow.

This is conceptually similar to how AI coding assistants use `rules.md` or `skills.md` to customize behavior — the same pattern applied to plumbing compliance.

**Why it's a paid feature:** It requires LLM inference, which has real cost. And it provides genuine value — catching missed safety flags before a report is filed protects the plumber's license and the building's occupants.

### Layer 3: Personal Agent (Beta/v1 — Available to All Tiers)

**What it does:** A conversational AI assistant that understands the plumber's business. It can create, query, and manage data through natural language.

**Use cases for Solo Plumber (User B):**

*Job creation from unstructured input:*
> "Hey, I just got off the phone with the super at 450 Ocean Ave. He needs a boiler repair, says the basement is flooded. Create a job."

Agent calls `OpenJob`:
- address = "450 Ocean Ave"
- job_type = REPAIR
- site_notes = "basement flooded, boiler issue"
- source_kind = CUSTOMER_REQUEST

*Batch job creation from documents:*
> "Here's an email from ABC Management with 12 buildings that need LL152 inspections this cycle." *(pastes email)*

Agent parses the email, extracts addresses, matches to buildings in the system, cross-references obligations, and batch-creates 12 LL152 jobs. The plumber reviews and confirms.

*Data querying:*
> "What inspections are due this week?"
> "How many jobs did I do for ABC Management last year?"
> "Show me all buildings on Atlantic Ave that I've inspected."
> "Which of my open jobs are overdue?"

Agent queries the structured data (obligations, jobs, buildings, clients) and returns answers with links to specific records.

*Daily briefing:*
> "What's my day look like?"

Agent checks open jobs, upcoming obligation deadlines, unsubmitted inspections, and surfaces a prioritized task list.

**Use cases for Small Team Manager (User C):**

> "How many jobs did each technician complete this month?"
> "Assign the 450 Ocean Ave job to Marcus."
> "Which inspections are still unsubmitted from last week?"

**Why it works:** The agent calls the **same API endpoints** the UI calls. `OpenJob`, `UpdateFinding`, `AttachClient`, `SubmitForReview` — these are all just tools the agent can invoke. The DDD architecture means every domain operation is already a discrete, well-defined action. The agent doesn't need special backdoors — it uses the front door.

---

## Subscription Model

### Core Principle

> **All users generate the same data. Premium users get AI that acts on it.**

The database schema is identical for Basic and Advanced users. Subscription tier is a company-level property. The API checks entitlements before calling AI services.

### Tier Structure (Draft)

| Capability | Basic | Advanced |
|---|---|---|
| **Core Platform** | | |
| Create/manage jobs, buildings, clients | ✅ | ✅ |
| LL152 workflow (findings, photos, review) | ✅ | ✅ |
| Recall submissions, fix mistakes | ✅ | ✅ |
| Compliance obligation tracking | ✅ | ✅ |
| Domain event audit trail | ✅ | ✅ |
| **Personal Agent** | | |
| Job creation from text/conversation | ✅ (limited/month) | ✅ (unlimited) |
| Data queries ("what's due this week?") | ✅ (limited) | ✅ (unlimited) |
| Batch job creation from documents | ❌ | ✅ |
| Daily briefing | ❌ | ✅ |
| **AI Review** | | |
| Auto-flag findings from field notes | ❌ | ✅ |
| Company-configurable review rules | ❌ | ✅ |
| AI confidence scores on flags | ❌ | ✅ |
| **Team Features** | | |
| Multi-user / team management | ❌ | ✅ |
| Team analytics agent queries | ❌ | ✅ |

### Metering

Basic tier gets a limited number of agent interactions per month (e.g., 50 queries/month). This lets solo plumbers experience the agent's value without paying for full AI access, creating natural upgrade pressure.

---

## Technical Architecture (Future — Not for Alpha)

### Agent ↔ API Surface

The AI agent is an **API consumer**, just like the mobile app and web dashboard. It authenticates as the user, respects the same authorization rules, and calls the same endpoints.

```
┌──────────────────────────────────────────────────────┐
│                    PCD Platform                       │
│                                                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ Mobile  │  │   Web    │  │  AI Agent         │    │
│  │  App    │  │Dashboard │  │  (MCP Client)     │    │
│  └────┬────┘  └────┬─────┘  └────────┬──────────┘    │
│       │             │                 │               │
│       └─────────────┴────────┬────────┘               │
│                              │                        │
│                     ┌────────▼────────┐               │
│                     │    PCD API      │               │
│                     │  (Rust/Actix)   │  ◄── Entitlements check │
│                     └────────┬────────┘               │
│                              │                        │
│                     ┌────────▼────────┐               │
│                     │   PostgreSQL    │               │
│                     │  (all domain    │               │
│                     │   data here)    │               │
│                     └─────────────────┘               │
└──────────────────────────────────────────────────────┘
```

The API may also expose itself as an **MCP server** — making PCD's domain operations (OpenJob, QueryObligations, SubmitForReview, etc.) available as tools that any MCP-compatible AI agent can call. This is the natural evolution of a well-structured API.

### AI Review Pipeline

```
Finding submitted by QI
        │
        ▼
  ┌─────────────────┐
  │ AI Review Agent  │
  │                  │
  │ Reads:           │
  │  - narrative     │
  │  - category      │
  │  - photos        │
  │                  │
  │ Consults:        │
  │  - company rules │
  │    (workflow.md) │
  │                  │
  │ Writes:          │
  │  - suggestions   │
  │    to ai_reviews │
  │    table         │
  └────────┬────────┘
           │
           ▼
  QI/LMP reviews AI suggestions
  Accepts or overrides
           │
           ▼
  Final values stored on
  inspection_findings row
```

### Future Tables (Beta — Not for Alpha Schema)

```sql
-- Tracks AI review results per finding
CREATE TABLE ai_finding_reviews (
    id                UUID PRIMARY KEY,
    finding_id        UUID REFERENCES inspection_findings(id),
    model_version     TEXT,
    confidence        REAL,
    recommendation    JSONB,
    accepted_by_user  BOOLEAN,
    reviewed_at       TIMESTAMPTZ
);

-- Company-configurable AI rules
CREATE TABLE company_ai_configs (
    id          UUID PRIMARY KEY,
    company_id  UUID REFERENCES companies(id),
    config_type TEXT,           -- 'FINDING_REVIEW_RULES', 'AGENT_PERSONA', etc.
    config_body TEXT,           -- markdown/YAML rules content
    version     INTEGER,
    updated_at  TIMESTAMPTZ
);

-- Agent interaction log (for metering and debugging)
CREATE TABLE agent_interactions (
    id            UUID PRIMARY KEY,
    company_id    UUID REFERENCES companies(id),
    user_id       UUID,
    interaction_type TEXT,      -- 'JOB_CREATION', 'DATA_QUERY', 'FINDING_REVIEW'
    input_summary TEXT,
    actions_taken JSONB,        -- which API calls the agent made
    created_at    TIMESTAMPTZ
);
```

---

## Why the Alpha Architecture Enables All This

Every alpha decision maps to a future AI capability:

| Alpha Decision | Future AI Enablement |
|---|---|
| DDD aggregates with clean commands | Each command = a tool the agent can invoke |
| REST API with typed endpoints | Agent calls the same API as humans |
| Domain events (`job_events`) | Agent can consume/react to state changes |
| Stored booleans (not derived) | AI can write `requires_correction = true` |
| Unconstrained `narrative_detail` TEXT | AI reads rich field notes without truncation |
| Extension tables (ADR-0025) | AI features are additive tables, not schema changes |
| Company-scoped tenancy (ADR-0017) | Subscription tier is a company property |
| `inspection_photos` with metadata | AI can analyze photos for compliance (future) |
| Address → Building resolution | Agent can match pasted addresses to known buildings |

---

## What Not to Build for Alpha

- No AI inference calls
- No agent conversation UI
- No subscription/billing system
- No `ai_finding_reviews` table
- No `company_ai_configs` table
- No `agent_interactions` table
- No MCP server exposure

All of this is additive. The alpha platform is the fertile ground. The AI is the crop planted later.

---

## Product Positioning

> **PCD: The operating system for plumbing companies — with an AI that actually understands your business.**

The pitch to a plumber:

> "You know how your work is spread across 6 different apps and none of them talk to each other? PCD puts everything in one place — your buildings, your clients, your inspections, your photos, your compliance deadlines. And then it gives you an AI assistant that actually knows your business. Tell it to create a job, ask it what's due this week, let it review your field notes for things you might have missed. It works because it can see everything, not just one slice."

The pitch to an investor:

> "Every plumbing company in NYC that handles LL152 inspections is using fragmented tools with no data integration. PCD consolidates their operations into a structured platform, then layers AI on top. The platform creates the data moat — once a company's operational data is in PCD, the AI gets smarter about their specific business. Switching costs are high because the AI's value grows with usage. Basic tier drives adoption, Advanced tier drives revenue."

---

## Open Questions (For Future Sessions)

1. **Voice input:** Should the personal agent support voice? Field workers have dirty hands and can't type easily. Voice → text → agent could be powerful for job creation.
2. **Photo analysis:** Should the AI review agent analyze inspection photos in addition to narrative text? (e.g., detecting flex hoses in images)
3. **Proactive alerts:** Should the agent push notifications? ("You have 3 unsubmitted inspections from today" or "Building 123 Main St has an LL152 deadline in 2 weeks and no job exists yet")
4. **Multi-language:** Many plumbers in NYC speak Spanish as a first language. Should the agent support bilingual interaction?
5. **Offline agent:** The personal agent requires connectivity. Should there be a simplified offline mode?
