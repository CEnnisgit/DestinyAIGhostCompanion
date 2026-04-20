# Vision: Registration, Tenancy, and the Business Model

> **Status:** Concept  
> **ADR:** [ADR-0027](../adr/0027-user-first-registration-rls-isolation.md), [ADR-0030](../adr/0030-workspace-isolation-abstraction.md)  
> **Related:** [Professional Network Vision](./PROFESSIONAL_NETWORK.md)

---

## The Core Idea

PCD is a professional tool for plumbers — individuals first, companies second. A plumber isn't just a company employee. They're a person who does their own work, may work across multiple companies, and maintains a professional identity that transcends any single employer.

The registration and tenancy model reflects this reality:

1. **You join as a person**, not as a company
2. **You can work immediately** — create jobs, manage clients, from day one
3. **Your company is something you create or join**, not a prerequisite for doing work
4. **Your data is isolated by workspace** — personal, company, and team contexts are all protected
5. **Your identity persists** even if you leave a company

---

## The Registration Journey

### Path A: Individual Account

A plumber downloads PCD and creates a personal account:

- Name, email, password
- That's it. They're in.
- They get a **personal workspace** automatically — their own private space for jobs, clients, and work.

### Path B: Company Registration

A plumber (or business owner) registers a company:

- Requires a **paid Company subscription** from day one
- Requires **verification** (license validation, business registration)
- Not something anyone can casually create — it represents a real, licensed business
- The registrant becomes the company's ADMIN
- They can invite employees (who join as ADMIN or TECHNICIAN)
- The company gets its own **company workspace** — a separate isolated space for company-scoped data

> A plumber can do both: have a personal account AND register/join companies. These are independent.

---

## Personal Subscription Tiers

Every user has their own personal subscription, independent of any company:

| Tier | What You Get |
|------|-------------|
| **Free** | Basic portfolio — create/track own jobs, manage own clients, hand-off jobs to connections |
| **Pro** | Buildings Explorer (PAD data, compliance obligations) + Team coordination (Beta) |
| **Premium** | AI features (future — see [AI Vision](./AI_FEATURES.md) when written) |

> [!IMPORTANT]
> **Free users CAN create jobs and manage clients.** The app is a tool for plumbers — a plumber who signs up should be able to start tracking their work immediately. Jobs and clients are not company-gated features.

---

## Company Subscription

A company has its own subscription, separate from any user's personal tier:

- **Company-scoped data** — jobs, clients, buildings that belong to the business entity
- **Employee management** — formal roles (ADMIN, TECHNICIAN), invitation flow
- **Advanced team operations** — company-level dispatching, full worker tracking (activity, location, arrivals, completions)
- **Reporting and oversight** — company-wide dashboards, team workload visibility
- **Verification status** — validated against NYC DOB / business registries

> A company subscription does NOT upgrade a user's personal tier. A personal subscription does NOT grant company features. They are independent.

---

## How a User Sees Their World

A user's portfolio is a unified view across all their contexts:

### User A (Marcus's Father)
- Has his own LLC → registered as a **Company** (ADMIN)
- Also a member of **Company B** (Danny's firm, as TECHNICIAN/QI)
- Also a member of **Company C** (larger firm, subcontract)

**His portfolio shows:**
1. His **personal jobs** (created by him, in his personal workspace)
2. **Company A jobs** (his LLC — he's ADMIN, sees all company jobs)
3. **Company B jobs** (Danny's firm — sees jobs assigned to him)
4. **Company C jobs** (larger firm — sees jobs assigned to him)

### User B (Second Alpha Tester)
- Does **NOT** own a company
- Has an individual account (Pro personal tier)
- Creates and manages his own jobs
- Coordinates with other individual users (connections) to share work

**His portfolio shows:**
1. His **personal jobs**
2. Jobs shared or coordinated via connections

---

## Three Kinds of Work Coordination

### 1. Hand-Off (Free — via Connections)
- "I can't make this job, I'm handing it to my buddy"
- Once handed off, the original user does not actively track the other user
- The job moves to the other person's workspace
- Peer-to-peer; no hierarchy, no oversight

### 2. Team Coordination (Pro — via Teams, Beta)
- "I own this job but I'm sending one of my guys"
- Teams are lightweight groups of individual users — no business validation, no LLC
- The team admin tracks workers, but with lighter oversight than company dispatch
- Teams are a coordination layer — they don't own client data (clients belong to the admin)
- **Deferred to Beta**

### 3. Company Dispatch (Company Subscription)
- "I'm assigning this job to my technician"
- ADMIN dispatches, TECHNICIAN executes
- Full employer/employee oversight: activity status, location, job site arrival, completion tracking
- Requires a registered, verified Company

---

## Data Isolation: The Workspace Model

### The Problem

PCD handles compliance-sensitive data: inspection findings, photos of plumbing violations, client contact information, license numbers. One user's data must never be visible to another — whether they're in different companies or just different individuals.

### The Solution: Workspaces + Row-Level Security (RLS)

Every piece of tenant-scoped data belongs to a **workspace**. A workspace is the universal isolation boundary.

- **Every user** gets a personal workspace on signup
- **Every company** gets a company workspace on registration
- **Every team** (Beta) gets a team workspace on creation
- All tenant-scoped tables (jobs, clients, saved buildings, findings, photos) use `workspace_id`
- PostgreSQL RLS enforces isolation: `workspace_id = current_setting('app.workspace_id')::uuid`

### How It Works

```text
User logs in
    │
    ▼
JWT issued (contains user_id)
    │
    ▼
User selects context (personal / Company A / Company B)
    │
    ▼
API middleware: SET app.workspace_id = '<workspace_uuid>'
    │
    ▼
All queries automatically filtered by RLS
    │
    ▼
Only the active workspace's data is returned
```

### Portfolio Query (All Contexts)

When showing the full portfolio, the API queries across all workspaces the user has access to:

```text
User's workspaces:
    Personal workspace  →  my own jobs
    Company A workspace →  Company A jobs (I'm ADMIN)
    Company B workspace →  Company B jobs (assigned to me)

Portfolio = UNION of all accessible workspace data
```

### What About Cross-Workspace Features?

Phase 3E Connections create controlled exceptions:

- If User A hands off a job to User B, the job moves from one workspace to another
- RLS policies can include exceptions for connected users on shared items
- The default is always isolation — sharing is opt-in and explicit

See [ADR-0030](../adr/0030-workspace-isolation-abstraction.md) for the full technical specification.

---

## Company Verification (Future)

For a compliance tool, fake companies are a liability. Future verification options:

1. **License number validation** — Cross-reference against NYC DOB master plumber license database
2. **Business registration** — Verify LLC/Corp registration with NY Department of State
3. **Manual review** — Admin approval for new company registrations
4. **Peer verification** — Existing verified companies can vouch for new ones

For alpha: verification is manual (Marcus seeds the accounts). For beta: invite-only growth. For V1: automated verification.

---

## How This All Fits Together

```text
                    ┌──────────────────┐
                    │     Person       │
                    │  (Free Account)  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼────┐  ┌──────▼─────┐  ┌────▼─────────┐
    │   Personal   │  │ Company A  │  │ Company B    │
    │  Workspace   │  │ Workspace  │  │ Workspace    │
    │  (auto)      │  │ (ADMIN)    │  │ (TECHNICIAN) │
    └──────┬───────┘  └──────┬─────┘  └──────┬───────┘
           │                 │               │
      ┌────┴────┐      ┌────┴────┐     ┌────┴────┐
      │ My Jobs │      │ Co. A   │     │ Co. B   │
      │ My      │      │ Jobs    │     │ Jobs    │
      │ Clients │      │ Clients │     │ (mine)  │
      └─────────┘      └─────────┘     └─────────┘

     ← Each workspace isolated by RLS →
     ← Connections create controlled bridges →
```

---

## Pricing Model (Future Decision)

Options to explore:

**Personal tiers:**
- Free / Pro / Premium (as defined above)

**Company subscription:**
- Per-company flat rate
- Per-seat (per active user in the company)
- Per-job (usage-based)
- Tiered (Small: 1-5 users, Medium: 6-20, Enterprise: 20+)

> [!NOTE]
> Pricing is a business decision, not an architectural one. The system should be flexible enough to support any of these models.

---

## Design Principles

1. **Person first, company second.** The user's identity and work outlive any single company.
2. **Free gets you working.** A plumber who signs up can create jobs and manage clients immediately.
3. **Company unlocks collaboration, not basic work.** Dispatching, team management, and oversight are company features — but creating and tracking your own work is not.
4. **Isolation by default.** RLS on workspaces ensures data privacy even when application code has bugs.
5. **Growth through the network.** Invite-only beats open registration for trust and quality.
6. **Verify before you trust.** Company registration should be gated, not open.
