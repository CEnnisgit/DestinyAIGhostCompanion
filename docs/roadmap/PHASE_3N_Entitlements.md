# Phase 3N: Entitlements

> **Status:** 🔲 Not Started
> **Objective:** Define what features users and companies are allowed to use. Person-level and company-level tiers with feature resolution rules.
> **Depends On:** Phase 3M (membership model clarifies who belongs where)
> **ADRs:** [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md), [ADR-0031](../adr/0031-person-first-entitlement-gating.md) (person-first gating)
> **Branch:** `phase3n/entitlements`

---

## Why This Sub-Phase Exists

Until this phase, every user and company has access to everything. This sub-phase introduces **feature gating** — the ability to say "this user/company can use feature X" based on their tier.

> [!IMPORTANT]
> **Entitlements ≠ Payments.** This phase defines the _model_ (what tiers exist, what features they include, how resolution works). [Phase 3P (Payments)](./PHASE_3P_Payments.md) handles _billing_ (Stripe, checkout, webhooks). Entitlements can be implemented with manual flags and no billing integration.

---

## Two-Level Tier Model

Entitlements exist at **both** the person level and the company level. These are independent.

### Person Tier

| Tier | Cost | Features |
|------|------|----------|
| **Free** | $0 | Browse buildings, view compliance obligations, basic professional profile |
| **Pro** (future) | TBD | Premium profile features, advanced search, analytics, portfolio exports |

### Company Tier

| Tier | Cost | Features |
|------|------|----------|
| **Starter** (future) | TBD | Job management, client portfolio, basic dispatching |
| **Professional** (future) | TBD | GPS reports, team management, LMP credential sharing |
| **Enterprise** (future) | TBD | Multi-team, advanced analytics, API access |

> [!NOTE]
> Specific tiers and pricing are **not finalized**. The entitlement model should be flexible enough to add/modify tiers without schema changes. The tier names above are examples for design purposes.

---

## Feature Resolution

When checking "can user X do action Y?", the system evaluates:

1. **Person tier** — does the user's personal tier include this feature?
2. **Company tier** — does the active company's tier include this feature?
3. **Role permission** — does the user's membership role allow this action? (from 3C.1)

### Resolution rule (to be decided during research)

| Question | Options |
|----------|---------|
| How do person + company tiers combine? | Union (either tier grants access)? Company wins? Most restrictive? |
| What if user has no company context? | Person tier only (free-tier features) |
| What if company tier doesn't include a feature? | Deny even if person tier includes it? Or person tier overrides for personal features? |

The most likely answer: **person tier controls personal features** (profile, search, analytics), **company tier controls company features** (jobs, dispatch, reports). They don't overlap much.

---

## Domain Concepts to Design

### 1. Entitlement Model

How tiers and features are stored:

| Option | Tradeoffs |
|--------|-----------|
| **Enum tiers** (e.g., `FREE`, `PRO`) | Simple, rigid. Adding a tier requires code change. |
| **Feature flags** (`user_features` table) | Flexible, granular. More complex queries. |
| **Tier + feature override** | Tier sets defaults, individual features can be overridden. Best of both. |

### 2. Where Tier Lives

| Level | Storage |
|-------|---------|
| Person tier | `users.tier` or `user_entitlements` table |
| Company tier | `companies.tier` or `company_entitlements` table |

### 3. Feature Catalog

A list of features that can be gated:

| Feature Key | Description | Level | Alpha Default |
|---|---|---|---|
| `buildings.browse` | Search and view buildings | Person | ✅ All |
| `compliance.view` | View compliance obligations | Person | ✅ All |
| `jobs.create` | Create jobs (also requires ADMIN role) | Company | ✅ All |
| `jobs.dispatch` | Assign jobs to technicians | Company | ✅ All |
| `reports.generate` | Generate GPS1/GPS2 PDFs | Company | ✅ All |
| `profile.enhanced` | Extended profile fields | Person | ✅ All (for alpha) |

---

## Research Questions (to resolve before implementation)

- [ ] What is the pricing model? (per-seat, flat rate, per-job, tiered?)
- [ ] Which features are person-level vs. company-level?
- [ ] Should free-tier users see "upgrade" prompts, or just get 403s?
- [ ] How do trials work? (time-limited full access? limited feature set?)
- [ ] Can an ADMIN buy Pro for their technicians, or do technicians buy their own?
- [ ] When a company downgrades, what happens to data created with higher-tier features?

---

## Implementation Plan (draft — pending business decisions)

### Schema

```sql
-- Option: simple tier column approach
ALTER TABLE users ADD COLUMN tier TEXT NOT NULL DEFAULT 'FREE';
ALTER TABLE companies ADD COLUMN tier TEXT NOT NULL DEFAULT 'STARTER';

-- Option: feature table approach
CREATE TABLE feature_entitlements (
    id UUID PRIMARY KEY,
    entity_type TEXT NOT NULL, -- 'USER' or 'COMPANY'
    entity_id UUID NOT NULL,
    feature_key TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    UNIQUE (entity_type, entity_id, feature_key)
);
```

### Domain Layer

| File | Action |
|------|--------|
| `src/entitlements/mod.rs` | New — tier model, feature resolution |
| `src/entitlements/feature.rs` | New — feature catalog |

### Integration with 3C.2

After this phase, [Phase 3C.2](./PHASE_3C_Authorization.md) extends authorization checks to include entitlement queries:

```rust
// 3C.1 check (exists today)
guard.require_admin(auth_context)?;

// 3C.2 check (added after 3N)
guard.require_admin(auth_context)?;
guard.require_feature("reports.generate", auth_context)?;
```

---

## Exit Criteria

- [ ] Tier model defined for both person and company levels
- [ ] Feature catalog enumerated
- [ ] Feature resolution rules documented and implemented
- [ ] "Can user do X?" check works with tier + role combined
- [ ] Alpha default: all features enabled (no gating until tiers are marketed)
- [ ] Entitlement spec written in DDD docs
