# Tenant Repository — Code Walkthrough

> **Trait crate:** `pcd-domain/src/tenant/repository.rs`
> **Impl crate:** `pcd-db/src/tenant/`

## Repository Traits (Ports)

### ClientRepository

```rust
#[async_trait]
pub trait ClientRepository: Send + Sync {
    async fn save(&self, client: &Client) -> anyhow::Result<()>;
    async fn update(&self, client: &Client) -> anyhow::Result<()>;
    async fn find_by_id(&self, client_id: Uuid) -> anyhow::Result<Option<Client>>;
    async fn list_by_company(&self, company_id: Uuid) -> anyhow::Result<Vec<Client>>;
    async fn find_by_name_and_phone(
        &self, company_id: Uuid, name: &str, phone: Option<&str>,
    ) -> anyhow::Result<Option<Client>>;
}
```

### SavedBuildingRepository

```rust
#[async_trait]
pub trait SavedBuildingRepository: Send + Sync {
    async fn save(&self, saved: &SavedBuilding) -> anyhow::Result<()>;
    async fn remove(&self, company_id: Uuid, building_id: Uuid) -> anyhow::Result<()>;
    async fn remove_by_id(&self, id: Uuid) -> anyhow::Result<()>;
    async fn list_by_company(&self, company_id: Uuid) -> anyhow::Result<Vec<SavedBuilding>>;
    async fn is_saved(&self, company_id: Uuid, building_id: Uuid) -> anyhow::Result<bool>;
}
```

## Sqlx Implementations

### SqlxClientRepository (`pcd-db/src/tenant/clients.rs`)

- `save` — `INSERT INTO clients`
- `update` — `UPDATE clients SET name, phone, address, is_blocked, blocked_reason, updated_at`
- `find_by_id` — `SELECT * FROM clients WHERE id = $1`
- `list_by_company` — `SELECT * FROM clients WHERE company_id = $1 ORDER BY name`
- `find_by_name_and_phone` — dedup query using `LOWER(name) = LOWER($2)` and optional phone match

### SqlxSavedBuildingRepository (`pcd-db/src/tenant/saved_buildings.rs`)

- `save` — `INSERT INTO saved_buildings` with `ON CONFLICT DO NOTHING` (UNIQUE constraint)
- `remove` — `DELETE FROM saved_buildings WHERE company_id = $1 AND building_id = $2`
- `remove_by_id` — `DELETE FROM saved_buildings WHERE id = $1`
- `list_by_company` — `SELECT * FROM saved_buildings WHERE company_id = $1`
- `is_saved` — `SELECT EXISTS(...)` check
- `list_by_company_with_bin` — custom query JOINing `buildings` table for BIN display

### Design Decision: Read-Side Projections

The `client_summary` endpoint bypasses both repository traits and queries `PgPool` directly. This was a deliberate choice to avoid adding cross-aggregate read methods to domain-layer repository traits. The summary is a read-side projection, not a domain operation.

## Database Schema

### companies (stub)

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    company_type TEXT NOT NULL DEFAULT 'independent',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### clients

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    is_blocked BOOLEAN NOT NULL DEFAULT false,
    blocked_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_blocked_reason CHECK (
        (is_blocked = true AND blocked_reason IS NOT NULL) OR
        (is_blocked = false AND blocked_reason IS NULL)
    )
);
```

### saved_buildings

```sql
CREATE TABLE saved_buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    building_id UUID NOT NULL REFERENCES buildings(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(company_id, building_id)
);
```
