## Directory and File Structure (Backend + Frontend)

I will assume a **monorepo** with a **modular monolith backend** and separate web/mobile clients. The structure is language-agnostic but I will illustrate with a typical TypeScript/Node + React stack for clarity.

### D.1 Monorepo Layout

```text
plumbers-compliance-dispatch/
├─ apps/
│  ├─ backend/                 # API + domain services
│  ├─ web-owner-portal/        # Public site + owner booking
│  ├─ web-company-dashboard/   # Company admin/dispatcher interface
│  └─ mobile-technician/       # Technician app
├─ packages/
│  ├─ shared-types/            # Shared TypeScript types / DTOs
│  ├─ shared-ui/               # Shared UI components (if web apps share)
│  └─ shared-config/           # Config utilities, env handling
└─ infra/
   ├─ docker/                  # Dockerfiles, compose
   ├─ k8s/                     # Kubernetes manifests (future)
   └─ terraform/               # Infra-as-code (optional)
```

---

### D.2 Backend Structure (Modular Monolith with Domains)

```text
apps/backend/
├─ src/
│  ├─ app/                     # App bootstrap, HTTP server, middleware
│  │  ├─ http/
│  │  │  ├─ routes/            # Route definitions, controllers
│  │  │  └─ middleware/
│  │  └─ config/
│  ├─ domain/
│  │  ├─ auth/                 # Auth & identity
│  │  ├─ company/              # Plumbing company, technicians
│  │  ├─ marketplace/          # ServiceRequest, matching logic
│  │  ├─ compliance/           # Building, InspectionJob, InspectionForm
│  │  ├─ reporting/            # InspectionReport generation
│  │  └─ notification/         # Email/SMS orchestration
│  ├─ infrastructure/
│  │  ├─ db/                   # ORM models, migrations
│  │  ├─ messaging/            # Queue/event bus adapters (if used)
│  │  ├─ storage/              # Object storage clients
│  │  └─ external/             # Email/SMS/Maps clients
│  └─ shared/
│     ├─ errors/
│     ├─ utils/
│     └─ types/
└─ test/
   ├─ unit/
   └─ integration/
```

For each domain module (e.g., `compliance/`), use a structure like:

```text
domain/compliance/
├─ entities/           # Domain models: Building, InspectionJob, ...
├─ repositories/       # Interfaces for persistence (implemented in infra)
├─ services/           # Business logic: createJob, submitForm, ...
└─ dtos/               # Request/response shapes
```

---

### D.3 Frontend – Web Owner Portal

Assuming React/Next.js:

```text
apps/web-owner-portal/
├─ src/
│  ├─ pages/                   # Next.js pages (landing, LL152 info, booking)
│  ├─ components/
│  │  ├─ layout/
│  │  ├─ forms/
│  │  ├─ directory/
│  │  └─ shared/
│  ├─ features/
│  │  ├─ booking/
│  │  └─ auth/                 # if owners can log in to see history
│  ├─ api/                     # Client-side API hooks (React Query, etc.)
│  ├─ lib/                     # Utilities
│  └─ styles/
└─ public/
```

---

### D.4 Frontend – Web Company Dashboard

Very similar to owner portal but with different features:

```text
apps/web-company-dashboard/
├─ src/
│  ├─ pages/
│  ├─ components/
│  │  ├─ navigation/
│  │  ├─ jobs/
│  │  ├─ technicians/
│  │  ├─ buildings/
│  │  └─ shared/
│  ├─ features/
│  │  ├─ jobs/
│  │  ├─ technicians/
│  │  ├─ reporting/
│  │  └─ auth/
│  ├─ api/
│  ├─ lib/
│  └─ styles/
```

---

### D.5 Frontend – Technician Mobile App (React Native Example)

```text
apps/mobile-technician/
├─ src/
│  ├─ screens/
│  │  ├─ LoginScreen.tsx
│  │  ├─ JobsListScreen.tsx
│  │  ├─ JobDetailScreen.tsx
│  │  └─ InspectionFormScreen.tsx
│  ├─ components/
│  │  ├─ forms/
│  │  ├─ photos/
│  │  └─ shared/
│  ├─ navigation/
│  ├─ api/
│  ├─ hooks/
│  ├─ lib/
│  └─ styles/
└─ android/
└─ ios/
```

Notice that each client app is organized **by feature**, reflecting the same domain boundaries used on the backend.

---
