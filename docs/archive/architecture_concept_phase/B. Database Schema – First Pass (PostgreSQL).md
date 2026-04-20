## B. Database Schema – First Pass (PostgreSQL)

Below is a first-pass relational schema aligned with our ontology and diagrams.

Assumptions:

* PostgreSQL as the relational database.
* UUIDs as primary keys.
* Timestamps in UTC.
* Basic indexing; you can refine later.

### B.1 Users & Identity

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    user_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email          CITEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    role           VARCHAR(32) NOT NULL, -- PLATFORM_ADMIN, COMPANY_ADMIN, TECHNICIAN, OWNER
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Optional: a `user_sessions` or `refresh_tokens` table later.

---

### B.2 Company Context

```sql
CREATE TABLE plumbing_companies (
    company_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name           TEXT NOT NULL,
    license_number TEXT NOT NULL,
    service_areas  TEXT[],                 -- e.g. ['Queens', 'Brooklyn']
    phone          TEXT,
    email          CITEXT,
    website_url    TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE technicians (
    technician_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    company_id     UUID NOT NULL REFERENCES plumbing_companies(company_id) ON DELETE CASCADE,
    display_name   TEXT NOT NULL,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- If you want explicit link between company and its admin users:
CREATE TABLE company_admins (
    company_admin_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    company_id       UUID NOT NULL REFERENCES plumbing_companies(company_id) ON DELETE CASCADE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### B.3 Owner Context

```sql
CREATE TABLE owners (
    owner_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    organization_name TEXT,
    phone           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### B.4 Compliance Context – Buildings & Inspections

```sql
CREATE TABLE buildings (
    building_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id      UUID NOT NULL REFERENCES owners(owner_id) ON DELETE CASCADE,
    address_line1 TEXT NOT NULL,
    address_line2 TEXT,
    borough       TEXT NOT NULL,
    zipcode       TEXT NOT NULL,
    lat           DOUBLE PRECISION,
    lng           DOUBLE PRECISION,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_buildings_owner ON buildings(owner_id);
CREATE INDEX idx_buildings_location ON buildings(borough, zipcode);
```

#### Inspection Jobs

```sql
CREATE TYPE job_status AS ENUM (
    'PENDING_ASSIGNMENT',
    'SCHEDULED',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED'
);

CREATE TABLE inspection_jobs (
    job_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id        UUID NOT NULL REFERENCES plumbing_companies(company_id) ON DELETE CASCADE,
    technician_id     UUID REFERENCES technicians(technician_id) ON DELETE SET NULL,
    building_id       UUID NOT NULL REFERENCES buildings(building_id) ON DELETE CASCADE,
    service_request_id UUID REFERENCES service_requests(request_id) ON DELETE SET NULL,
    law_type          TEXT NOT NULL DEFAULT 'LL152', -- future-proofing
    scheduled_at      TIMESTAMPTZ,
    status            job_status NOT NULL DEFAULT 'PENDING_ASSIGNMENT',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_inspection_jobs_company ON inspection_jobs(company_id);
CREATE INDEX idx_inspection_jobs_technician ON inspection_jobs(technician_id);
CREATE INDEX idx_inspection_jobs_building ON inspection_jobs(building_id);
```

#### Inspection Forms

```sql
CREATE TYPE form_status AS ENUM ('IN_PROGRESS', 'COMPLETED');

CREATE TABLE inspection_forms (
    form_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id         UUID NOT NULL UNIQUE REFERENCES inspection_jobs(job_id) ON DELETE CASCADE,
    status         form_status NOT NULL DEFAULT 'IN_PROGRESS',
    form_payload   JSONB NOT NULL, -- structured LL152 data
    submitted_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### Inspection Reports

```sql
CREATE TABLE inspection_reports (
    report_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    form_id        UUID NOT NULL REFERENCES inspection_forms(form_id) ON DELETE CASCADE,
    storage_url    TEXT NOT NULL,
    version        INTEGER NOT NULL DEFAULT 1,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_inspection_reports_form ON inspection_reports(form_id);
```

#### Photos (optional explicit table)

```sql
CREATE TABLE inspection_photos (
    photo_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    form_id       UUID NOT NULL REFERENCES inspection_forms(form_id) ON DELETE CASCADE,
    storage_url   TEXT NOT NULL,
    taken_at      TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_photos_form ON inspection_photos(form_id);
```

---

### B.5 Marketplace Context – Service Requests

```sql
CREATE TYPE request_status AS ENUM ('RECEIVED', 'MATCHED', 'CANCELLED');

CREATE TABLE service_requests (
    request_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id         UUID NOT NULL REFERENCES buildings(building_id) ON DELETE CASCADE,
    owner_id            UUID NOT NULL REFERENCES owners(owner_id) ON DELETE CASCADE,
    requested_start     TIMESTAMPTZ,
    requested_end       TIMESTAMPTZ,
    status              request_status NOT NULL DEFAULT 'RECEIVED',
    matched_company_id  UUID REFERENCES plumbing_companies(company_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_service_requests_owner ON service_requests(owner_id);
CREATE INDEX idx_service_requests_building ON service_requests(building_id);
CREATE INDEX idx_service_requests_status ON service_requests(status);
```

Note: `inspection_jobs` references `service_requests`, so create `service_requests` before `inspection_jobs` in actual migration order.

---

