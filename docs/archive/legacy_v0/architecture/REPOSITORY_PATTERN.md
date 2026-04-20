# Repository Pattern

> Data access layer with dependency injection

## Pattern Overview

```
┌──────────────────────┐
│   Service Layer      │  ← Business logic
│   (JobService, etc)  │
└──────────┬───────────┘
           │ uses interface
           ▼
┌──────────────────────┐
│   Repository         │  ← Abstract interface
│   Interface          │
└──────────┬───────────┘
           │ implements
           ▼
┌──────────────────────┐
│   DrizzleRepository  │  ← Concrete implementation
│   (DrizzleJobRepo)   │
└──────────┬───────────┘
           │ uses
           ▼
┌──────────────────────┐
│   Database           │
└──────────────────────┘
```

---

## Why This Pattern?

1. **Testability** - Mock repositories in unit tests
2. **Flexibility** - Swap database without changing services
3. **Clean boundaries** - Services don't know about Drizzle

---

## Interface Example

```typescript
// domain/compliance/repositories/JobRepository.ts
export interface JobRepository {
  findById(jobId: string): Promise<InspectionJob | undefined>;
  findByCompanyId(companyId: string): Promise<InspectionJob[]>;
  create(data: NewInspectionJob): Promise<InspectionJob>;
  update(jobId: string, data: Partial<InspectionJob>): Promise<InspectionJob>;
}
```

---

## Drizzle Implementation

```typescript
// infrastructure/db/repositories/DrizzleJobRepository.ts
export class DrizzleJobRepository implements JobRepository {
  async findById(jobId: string): Promise<InspectionJob | undefined> {
    const results = await db.select()
      .from(inspectionJobs)
      .where(sql`${inspectionJobs.jobId} = ${jobId}`)
      .limit(1);
    return results[0] ?? undefined;
  }
}
```

---

## SQL Template Workaround

> [!IMPORTANT]
> We use `sql` tagged templates instead of Drizzle's `eq()` helper due to a version mismatch issue.

```typescript
// ❌ This causes type errors
.where(eq(inspectionJobs.jobId, jobId))

// ✅ Use this instead
.where(sql`${inspectionJobs.jobId} = ${jobId}`)
```

---

## Adding a New Repository

1. **Create interface** in `domain/[domain]/repositories/`:
   ```typescript
   export interface MyRepository {
     findById(id: string): Promise<MyEntity | undefined>;
     // ...
   }
   ```

2. **Create implementation** in `infrastructure/db/repositories/`:
   ```typescript
   export class DrizzleMyRepository implements MyRepository {
     // ...
   }
   ```

3. **Inject into service**:
   ```typescript
   export class MyService {
     constructor(private myRepo: MyRepository) {}
   }
   ```

4. **Wire in routes**:
   ```typescript
   const myRepo = new DrizzleMyRepository();
   const myService = new MyService(myRepo);
   ```

---

## Code Location

| Layer | Location |
|-------|----------|
| Interfaces | `src/domain/*/repositories/` |
| Implementations | `src/infrastructure/db/repositories/` |
| Wiring | Route files (constructor injection) |
