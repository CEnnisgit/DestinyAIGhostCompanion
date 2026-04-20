# Data Retention Policy

> Source: Previously in `packages/shared-config/src/DataRetentionPolicy.ts` (deleted during Drizzle layer removal).
> Reference: SNFR-SC-12

## Retention Periods

| Data Type | Retention | Rationale |
|-----------|----------|-----------|
| Inspection records & reports | **7 years** | NYC LL152 requires 3-year minimum; we retain 7 for safety |
| Photo evidence | **7 years** | Aligned with inspection records |
| Audit logs | **3 years** | Standard compliance audit trail |
| Password reset tokens | **24 hours** | Security best practice |
| Deleted user data (grace period) | **30 days** | Before hard delete |
