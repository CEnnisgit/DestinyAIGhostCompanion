# ADR-0031: Person-First Feature Gating and Two-Dimensional Subscription Model

**Status:** Accepted  
**Date:** 2026-03-30  
**Deciders:** Marcus, AI Pair Programming  
**Related:** [ADR-0027](./0027-user-first-registration-rls-isolation.md), [ADR-0030](./0030-workspace-isolation-abstraction.md)

## Context

PCD needs a clear model for what features are available to whom. The registration model (ADR-0027) establishes that users sign up as individuals — but it doesn't specify what a free individual user can actually **do**.

Previous documentation incorrectly stated that free users "cannot create jobs" and "cannot manage clients," gating all operational features behind company membership. This was inconsistent with the product intent:

- **User A** (Marcus's father) owns an LLC but also does personal work outside his company. He needs personal jobs that aren't company-scoped.
- **User B** (second alpha tester) doesn't own a company at all. He manages his own jobs and coordinates with peers.

Both users need to create jobs and manage clients from day one — company or not.

## Decision

### 1. Jobs and Clients Are Personal Capabilities

Creating jobs and managing clients are available to **all users**, including free tier. These are not company-gated features. A plumber who signs up should be able to start tracking their work immediately.

When a user creates a job without a company context, it belongs to their **personal workspace** (see ADR-0030).

### 2. Two-Dimensional Subscription Model

Subscriptions operate on **two independent axes**:

#### Personal Tiers (per user)

| Tier | Capabilities |
|------|-------------|
| **Free** | Basic portfolio (create/track jobs, manage clients), hand-off jobs to connections |
| **Pro** | Buildings Explorer (PAD data, compliance), Team coordination (Beta) |
| **Premium** | AI-powered features (deferred) |

#### Company Subscription (per company)

| Feature | Description |
|---------|-------------|
| Company-scoped data | Jobs, clients, buildings owned by the business entity |
| Employee management | Formal roles (ADMIN, TECHNICIAN), invitation flow |
| Company dispatch | Full technician tracking (activity, location, arrivals, completion) |
| Advanced reporting | Company-wide dashboards, workload visibility |

**These are independent.** A user's personal Pro tier does not grant company features. A company subscription does not upgrade any user's personal tier. A user can have Free personal tier while working as a TECHNICIAN in a company.

### 3. Three Work Coordination Modes

Work coordination maps to different entitlement levels:

| Mode | Tier Required | Relationship | Tracking Level |
|------|--------------|-------------|---------------|
| **Hand-off** | Free (via Connections) | Peer-to-peer | None — job moves, original user disengages |
| **Team** | Pro personal (Beta) | Admin → members | Light — admin sees member status and job completion |
| **Company dispatch** | Company subscription | Employer → employee | Full — activity status, location, arrivals, completion |

## Alternatives Considered

### Company-first feature gating

All operational features (jobs, clients, dispatch) require company membership. Free users can only browse buildings and view profiles.

**Rejected.** This contradicts the core user stories. Both alpha testers need to create and manage their own jobs independently of any company. Forcing company creation to do basic work creates friction and doesn't match how plumbers actually operate — many work independently or across multiple companies.

### Flat single-tier model

All users get everything for free; monetize only through company subscriptions.

**Rejected.** The Buildings Explorer (PAD data access) and AI features have real infrastructure costs. Tiering personal features allows sustainable growth while keeping the core (portfolio management) free.

### Merge personal and company subscriptions

One subscription that covers both personal features and company features.

**Rejected.** Users who belong to companies don't pay for the company — the company subscription covers them. A technician at Company X shouldn't need a personal paid tier just because their employer has a subscription. The two dimensions must remain independent.

## Implications

### For Data Model

- `jobs` and `clients` use `workspace_id` (ADR-0030), not `company_id`
- Personal jobs exist in the user's personal workspace — no company FK needed
- Feature gating is enforced at the **API layer** (personal tier checks), not the database layer

### For API Design

- Subscription tier must be available in the auth context (from JWT or user lookup)
- Endpoints must check personal tier for features like Buildings Explorer
- Company-scoped endpoints additionally check company membership and company subscription status

### For Phase 3A (Alpha)

- Alpha users are seeded with appropriate tiers (no self-service subscription management yet)
- Subscription enforcement is deferred — all alpha users effectively get Pro tier
- The schema must support the model even if enforcement comes later

### For Future Billing Integration

- Need a `subscription_tier` field on `users` (personal tier)
- Need a `subscription_status` field on `companies` (company subscription)
- Billing provider integration (Stripe, etc.) maps to these fields
- Tier changes must be auditable

## References

- [ADR-0027: User-First Registration](./0027-user-first-registration-rls-isolation.md)
- [ADR-0030: Workspace Abstraction](./0030-workspace-isolation-abstraction.md)
- [Vision: Registration and Tenancy](../vision/REGISTRATION_AND_TENANCY.md)
- [Alpha Personas and Scope](../ALPHA_PERSONAS_AND_SCOPE.md)
