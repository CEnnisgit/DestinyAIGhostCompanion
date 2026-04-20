---
description: Generate a learning-focused design worksheet for a new module
---

# Design Module Worksheet

This workflow generates a tailored learning worksheet for a new module, covering domain-specific concepts, trade-offs, and critical decisions.

## When to Use
- Before starting implementation of a new module
- When entering an unfamiliar domain (auth, payments, scheduling, etc.)
- When you want to research and understand before coding

## Workflow Steps

### 1. Identify the Module Domain

Ask the user:
- What is the module name?
- What problem domain does it cover? (e.g., authentication, job scheduling, compliance forms)
- What's the pilot/MVP scope? (what's in vs out for now)

### 2. Research Domain Concepts

Before generating the worksheet, research:
- Common patterns in this domain
- Standard terminology
- Typical trade-offs and decision points
- Security or compliance considerations specific to this domain

### 3. Generate the Worksheet

Create a markdown file at: `docs/design-worksheets/{module-name}.md`

The worksheet should follow this structure:

```markdown
# {Module Name} Design Worksheet

> A guided learning journey for designing {module description}.
> Use this as a reference while researching. Capture your decisions as you learn.

---

## Concept 1: {Core Concept}

{Explanation of what this concept is and why it matters}

| Option | Trade-offs |
|--------|------------|
| ... | ... |

> **Research prompt:** "{search terms for learning more}"

### Your Decision
{Space for user to capture their choice and rationale}

---

## Concept N: {Another Concept}

{Repeat pattern...}

---

## Summary: Critical Decisions Checklist

Before coding, you should have answers for:
- [ ] {Decision 1}
- [ ] {Decision 2}
- [ ] ...

---

## Research Queue

Topics to look up:
- [ ] _____________
```

### 4. Present to User

After generating, let the user know:
- Where the worksheet is saved
- A summary of concepts covered
- That they should take time to research and fill it in

## Example Domains and Concepts

| Domain | Example Concepts to Cover |
|--------|--------------------------|
| **Auth** | Passwords, sessions, tokens, OAuth, MFA, rate limiting |
| **Payments** | Idempotency, webhooks, refunds, fraud, PCI compliance |
| **Job Scheduling** | State machines, async processing, retries, dead letters |
| **File Storage** | Upload strategies, CDNs, signed URLs, virus scanning |
| **Notifications** | Channels (email/SMS/push), templates, delivery tracking |
| **Search** | Indexing, full-text, facets, relevance, pagination |
| **Reporting** | Aggregations, time series, exports, caching |

## Output

- A learning-focused worksheet tailored to the module's domain
- Saved in `docs/design-worksheets/` for reference
