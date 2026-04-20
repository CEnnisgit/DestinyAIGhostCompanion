# Repository — Walkthrough

The repository layer implements the hexagonal port/adapter pattern: a trait (port) in `pcd-domain` and an adapter (implementation) in `pcd-db`.

## Port: `JobRepository` Trait

**File:** `crates/pcd-domain/src/jobs/repository.rs` (27 lines)

```rust
#[async_trait]
pub trait JobRepository: Send + Sync {
    async fn save(&self, job: &mut Job) -> anyhow::Result<()>;
    async fn find_by_id(&self, job_id: Uuid) -> anyhow::Result<Option<Job>>;
    async fn find_by_job_number(&self, company_id: Uuid, job_number: &str) -> anyhow::Result<Option<Job>>;
    async fn next_job_number(&self, company_id: Uuid) -> anyhow::Result<String>;
    async fn list_all(&self, limit: i64) -> anyhow::Result<Vec<Job>>;
}
```

| Method | Purpose |
| :--- | :--- |
| `save` | Upsert job + insert uncommitted events in a single transaction |
| `find_by_id` | Lookup by aggregate UUID |
| `find_by_job_number` | Company-scoped lookup by human-facing number |
| `next_job_number` | Generate next sequential number (counter-based: `JOB-00001`) |
| `list_all` | Most-recent-first listing with limit |

The trait requires `Send + Sync` for use with Axum's async handlers and `Arc` sharing.

---

## Adapter: `SqlxJobRepository`

**File:** `crates/pcd-db/src/jobs/mod.rs`

### Construction

```rust
pub struct SqlxJobRepository { pool: PgPool }

impl SqlxJobRepository {
    pub fn new(pool: PgPool) -> Self { Self { pool } }
}
```

### Wiring

```rust
// main.rs — construction as Arc<dyn JobRepository>
let job_repo: Arc<dyn JobRepository> = Arc::new(SqlxJobRepository::new(pool));

// routes/jobs.rs — handlers receive the abstract type
pub type AppState = Arc<dyn JobRepository>;
```

### `save()` — Transactional Persistence

The save method runs in a single database transaction:

1. **UPSERT** the job row (22 columns, `ON CONFLICT (id) DO UPDATE`)
2. **INSERT** each uncommitted domain event into `job_events`
3. **COMMIT** the transaction
4. Call `job.clear_uncommitted_events()` after commit

This guarantees the job state and its events are always consistent.

### Row Mapping: `JobRow` → `Job`

A private `JobRow` struct with `#[derive(sqlx::FromRow)]` maps database columns to Rust fields. The `row_to_job()` function calls `Job::reconstitute()` to rebuild the aggregate with validated VOs.

---

## Persistence Shape

### `jobs` table (22 columns)

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID | Primary key |
| `job_number` | VARCHAR | Company-scoped sequential |
| `company_id` | UUID | Tenant scoping |
| `job_type` | VARCHAR | E.g., `LL152_INSPECTION` |
| `building_id` | UUID | Required reference |
| `client_id` | UUID | Optional reference |
| `compliance_obligation_id` | UUID | Optional link |
| `requester_contact_id` | UUID | Optional reference |
| `title` | VARCHAR | Auto-generated or custom |
| `summary` | TEXT | Optional description |
| `source_kind` | VARCHAR | How the job was initiated |
| `priority` | VARCHAR | NORMAL / HIGH / URGENT |
| `site_notes` | TEXT | Field-level notes |
| `assigned_to` | UUID | Dispatched technician |
| `created_by_user_id` | UUID | Who created the job |
| `job_status` | VARCHAR | OPEN / IN_PROGRESS / COMPLETED / CANCELED |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `started_at` | TIMESTAMPTZ | When work began |
| `completed_at` | TIMESTAMPTZ | When work finished |
| `canceled_at` | TIMESTAMPTZ | When canceled |
| `cancellation_reason` | TEXT | Why canceled |
| `updated_at` | TIMESTAMPTZ | Last modification |

### `job_events` table (6 columns)

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID | Primary key |
| `job_id` | UUID | FK → jobs |
| `event_type` | VARCHAR | E.g., `JOB_STARTED` |
| `payload` | JSONB | Event-specific data |
| `actor_user_id` | UUID | Who triggered the event |
| `created_at` | TIMESTAMPTZ | When the event occurred |
