# ADR-0004: Rate Limiting Strategy

**Status:** Accepted  
**Date:** December 2024  
**Deciders:** Development Team

## Context

The backend needed protection against brute-force attacks and DDoS. Auth endpoints are particularly sensitive - password guessing attacks and credential stuffing are common.

We needed to decide:
1. Which rate limiting library to use
2. Global vs per-endpoint limits
3. How to handle rate limiting behind a reverse proxy
4. In-memory vs shared store for horizontal scaling

## Decision

We adopt `@fastify/rate-limit` with **tiered per-endpoint limits** and **explicit proxy handling**.

### Rate Limits

| Endpoint | Limit | Rationale |
|----------|-------|-----------|
| POST /register | 5/min | Prevent mass account creation |
| POST /login | 10/min | Balance security vs UX |
| POST /forgot-password | 3/min | Prevent email bombing |
| POST /health | Exempt | Noisy health checks |
| All others | 100/min | General protection |

### Proxy Configuration

```typescript
const app = Fastify({
    trustProxy: true, // GCP Cloud Run always adds x-forwarded-for
});

await app.register(fastifyRateLimit, {
    keyGenerator: (req) => req.ip, // Correct IP with trustProxy
});
```

### MVP Trade-off: In-Memory Store

We accept the **in-memory store** limitation for MVP:
- Single Cloud Run instance = consistent enforcement
- Rate limits are per-instance when scaled
- Redis store can be added when horizontal scaling is needed

## Consequences

### Positive

- **Immediate brute-force protection** for auth endpoints
- **Correct IP handling** behind GCP load balancer
- **Minimal latency** with in-memory store
- **Custom 429 response** consistent with API format

### Negative

- **Per-instance limits** if horizontally scaled
- **Permissive trustProxy** (acceptable for GCP but not all deployments)

## Alternatives Considered

### No Rate Limiting

**Rejected because:** Security baseline for production.

### Redis-Based Store from Day One

**Rejected because:**
- Adds operational complexity
- Single instance for MVP
- Can upgrade later when scaling

### WAF/Cloudflare Rate Limiting

**Rejected because:**
- Not yet configured
- Per-endpoint granularity harder to achieve
- Can layer on top later

## Future Considerations

1. Add Redis store when scaling to multiple instances
2. Consider stricter limits for failed login attempts specifically
3. Layer with WAF for IP-level blocking
