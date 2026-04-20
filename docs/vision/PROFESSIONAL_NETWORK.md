# Vision: Professional Network for Plumbers

> **Status:** Concept — not yet implemented  
> **ADR:** [ADR-0026](../adr/0026-professional-network-connections.md)  
> **Roadmap:** Phase 3E (after identity + auth foundation)

---

## The Idea

PCD isn't just a tool one plumber uses alone. Plumbing work is inherently collaborative: plumbers know other plumbers, they share work, they cover for each other, and they operate under each other's licenses.

The Professional Network is a lightweight social layer that lets plumbers **connect** with other professionals in the trade and **collaborate** across company boundaries.

---

## The Story That Inspired This

Marcus's father:

- Owns his own LLC and does plumbing work independently
- Works as a QI (Qualified Individual) under his friend Danny's LMP license for LL152 inspections
- Also works with a larger plumbing company on bigger projects

He's **one person** who operates across **three companies**. His work life isn't contained within a single company — it's a web of professional relationships.

On any given day:
- He might plan 4 jobs but only get to 3 — he wants to **send that last job** to his buddy who's nearby
- He might work a difficult job alongside another plumber — they both need that job **on their portfolio**
- His LMP friend needs to see what LL152 inspections are happening under his license — he needs to **track his QIs**
- When he does an LL152, he needs to attach the LMP's license info — the LMP should be able to **share his credential card** directly

---

## What Users Can Do

### 1. Connect with Other Professionals

Find another PCD user by email or name and send a connection request. Once accepted, you can interact.

**Connection types:**

| Type | Relationship | Example |
|------|-------------|---------|
| **Colleague** | We work together sometimes | Two plumbers who cover for each other |
| **Supervises** | I'm the LMP, they're my QI | Danny (LMP) → Father (QI) |
| **Subcontracts** | I send them overflow work | Father → his buddy on long-distance jobs |

### 2. Share/Transfer Jobs

A plumber who can't make a scheduled job can **send it** to a connected professional:

- Select a job from your portfolio
- Choose a connected user to transfer it to
- The job appears in their portfolio (with transfer history)

The job's ownership (which company it belongs to) can either stay the same (if the other plumber is also in the same company) or transfer (if it's cross-company work).

### 3. Collaborate on Jobs

Two plumbers working the same job together:

- The job owner **attaches** a connected user as a participant
- The job appears in both users' portfolios
- Both can submit findings and evidence
- The job history shows who did what

### 4. LMP Oversight Dashboard

An LMP with `SUPERVISES` connections can:

- See a list of all their QIs
- See what jobs each QI is currently working on
- Track which of their LMP credentials are being used on which jobs
- Get notified when a QI submits an inspection for review

### 5. Credential Sharing

An LMP creates their license credential card once:

- License number, name, expiration, contact info
- **Shares it** with connected QIs
- QIs can attach the shared card to LL152 jobs — no manual data entry
- If the LMP updates their card (e.g., license renewal), all connected QIs see the update

---

## What This Is NOT

- **Not a social network.** No posts, no feeds, no likes. This is strictly professional — connections exist to enable work collaboration.
- **Not a marketplace.** You can't browse available plumbers. You connect with people you already know.
- **Not multi-tenancy bypass.** Your company data stays private. Connections create specific, explicit sharing — not open access.

---

## How It Could Grow

### Near-term (Alpha+)
- Connection requests + acceptance
- Job transfer between connected users
- LMP credential sharing

### Medium-term (Beta)
- Job collaboration (multi-participant)
- LMP oversight dashboard
- Connection activity feed ("Danny assigned you a job")

### Long-term (V1+)
- Company-level visibility (see which companies your team is connected to)
- Referral tracking (who referred this client?)
- Availability signaling ("I'm free today if anyone needs help")
- Insurance/license verification via connections

---

## Design Principles

1. **People first, companies second.** The network is between humans, not legal entities.
2. **Opt-in only.** No data is visible across companies until both parties explicitly connect.
3. **Additive, not disruptive.** This layer sits ON TOP of existing tenant isolation — it doesn't replace it.
4. **Start simple.** Connection + job transfer first. Collaboration and oversight come later.
