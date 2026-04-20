# Phase 3P: Payments

> **Status:** 🔲 Not Started
> **Objective:** Integrate billing infrastructure — how money is collected for person and company subscriptions.
> **Depends On:** Phase 3N (entitlements define what is being purchased)
> **ADRs:** [ADR-0029](../adr/0029-phase3-decomposition-membership-entitlements.md), [ADR-0031](../adr/0031-person-first-entitlement-gating.md) (person-first gating)
> **Branch:** `phase3p/payments`

---

## Why This Sub-Phase Exists

[Phase 3N (Entitlements)](./PHASE_3N_Entitlements.md) defines what features each tier includes. This phase handles **how users pay to unlock those tiers** — the billing rails.

> [!IMPORTANT]
> **Payments ≠ Entitlements.** Entitlements can run with manual flags (admin sets tier = PRO). Payments adds self-service: users subscribe, cards are charged, webhooks update tiers, downgrades happen automatically on payment failure.

---

## Scope (High-Level — Detailed Design Pending)

### 1. Payment Provider Integration

- **Stripe** is the most likely choice (standard for SaaS)
- Stripe Checkout for subscription creation
- Stripe Billing for recurring charges
- Stripe Webhooks for tier sync

### 2. Subscription Management

| Flow | Description |
|------|-------------|
| **Subscribe** | User selects tier → Stripe Checkout → webhook confirms → tier updated |
| **Upgrade** | User selects higher tier → prorated billing → immediate access |
| **Downgrade** | User selects lower tier → takes effect at period end |
| **Cancel** | User cancels → access continues until period end → tier reverts to FREE |
| **Payment failure** | Stripe retries → after grace period → tier downgraded |

### 3. Two Billing Subjects

| Subject | Who pays | What they get |
|---------|----------|---------------|
| **Person subscription** | The individual user | Personal tier features (Pro profile, analytics) |
| **Company subscription** | The company owner (ADMIN) | Company tier features (jobs, dispatch, reports) |

These are two separate Stripe subscriptions. A user can have a personal Pro subscription without their company having a Professional tier, and vice versa.

### 4. Billing Portal

- Stripe Customer Portal for managing payment methods, viewing invoices, canceling
- Or custom billing UI if Stripe Portal doesn't meet UX needs

---

## Research Questions (to resolve before implementation)

- [ ] Stripe or alternative? (Stripe is assumed but not confirmed)
- [ ] Per-seat pricing for companies? Or flat rate per company?
- [ ] Who pays for the company subscription? The ADMIN? What if there are multiple ADMINs?
- [ ] Grace period on payment failure? (7 days? 14 days?)
- [ ] Should free-tier users see ads, or is free truly free?
- [ ] Tax handling? (Stripe Tax, or manual?)
- [ ] Refund policy?
- [ ] Do we need a trial period? How long?

---

## Implementation Plan (draft — pending provider selection and pricing model)

### Dependencies (Cargo.toml)

```toml
stripe-rust = "latest"  # or equivalent Stripe SDK
```

### Schema

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    entity_type TEXT NOT NULL, -- 'USER' or 'COMPANY'
    entity_id UUID NOT NULL,
    stripe_subscription_id TEXT NOT NULL,
    stripe_customer_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    status TEXT NOT NULL, -- 'ACTIVE', 'PAST_DUE', 'CANCELED', 'TRIALING'
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### API Layer

| Endpoint | Method | Guard | Description |
|----------|--------|-------|-------------|
| `POST /api/billing/checkout` | POST | Auth | Create Stripe Checkout session |
| `POST /api/billing/portal` | POST | Auth | Create Stripe Customer Portal session |
| `POST /api/webhooks/stripe` | POST | None (Stripe signature verification) | Handle Stripe events |
| `GET /api/billing/status` | GET | Auth | Current subscription status |

### Webhook Events to Handle

| Stripe Event | Action |
|---|---|
| `checkout.session.completed` | Create subscription record, update tier |
| `invoice.payment_succeeded` | Update subscription period |
| `invoice.payment_failed` | Mark as past_due, start grace period |
| `customer.subscription.updated` | Sync tier changes (upgrade/downgrade) |
| `customer.subscription.deleted` | Revert to FREE tier |

---

## Exit Criteria

- [ ] Users can subscribe to person tiers via Stripe Checkout
- [ ] Company ADMINs can subscribe to company tiers via Stripe Checkout
- [ ] Stripe webhooks sync tier changes to entitlement model
- [ ] Payment failure triggers grace period then downgrade
- [ ] Billing portal accessible for payment management
- [ ] Subscription status visible in user/company profile
- [ ] Integration tests with Stripe test mode

---

## Why This Is Last in the Chain

```text
3A (identity) → 3B (auth) → 3C.1 (RBAC) → 3M (membership) → 3N (entitlements) → 3C.2 (full authz) → 3P (payments)
```

Payments are last because:
1. You can't charge for tiers that don't exist yet (need 3N)
2. You can't gate features without authorization (need 3C)
3. You can't manage company subscriptions without membership (need 3M)
4. Alpha doesn't need billing — everyone gets everything for free during testing
