# Company Sub-Module (IAM)

> **Parent:** [IAM Module](../README.md)
> **ADR:** [ADR-0027](../../../../adr/0027-user-first-registration-rls-isolation.md)

## Responsibilities
**Tenancy Container**: The organization that scopes operational data.
- **Company Profile**: Name, contact info (phone, address, email). [Spec](./Company_Aggregate.md)
- **Data Isolation**: Providing the `company_id` boundary for multi-tenancy (RLS in Phase 3C).

## Data Structures
- `companies` table — tenant identity (name, company_type, contact fields).

## Key Design Decisions
- Minimal for alpha — contact fields only. Registration fields (LLC number, insurance, DOB license) deferred to Phase 3D.
- Alpha companies are seeded, not registered. Company registration flow is a future paid-tier feature.
- Users relate to companies through `company_memberships` junction table, not a direct FK on users.
