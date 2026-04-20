# ADR-0002: Drizzle ORM for Database Layer

**Status:** Accepted  
**Date:** December 2024  
**Deciders:** Development Team

## Context

The backend needs a TypeScript-native database layer for PostgreSQL. Key requirements:

1. **Type safety** - Full TypeScript integration
2. **Migration support** - Schema versioning and deployment
3. **Performance** - Efficient queries, connection pooling
4. **Developer experience** - Good tooling, readable queries

## Decision

We use **Drizzle ORM** as the database layer.

### Schema Definition

```typescript
// infrastructure/db/schema/inspectionJobs.ts
export const inspectionJobs = pgTable('inspection_jobs', {
    jobId: uuid('job_id').primaryKey().defaultRandom(),
    companyId: uuid('company_id').notNull(),
    buildingId: uuid('building_id').notNull(),
    status: text('status').notNull().default('PENDING_ASSIGNMENT'),
    // ...
});
```

### Query Pattern

```typescript
// infrastructure/db/repositories/DrizzleJobRepository.ts
export class DrizzleJobRepository implements JobRepository {
    async findById(jobId: string): Promise<InspectionJob | undefined> {
        const results = await db.select()
            .from(inspectionJobs)
            .where(sql`${inspectionJobs.jobId} = ${jobId}`)
            .limit(1);
        return results[0];
    }
}
```

> [!NOTE]
> We use `sql` tagged templates instead of Drizzle's `eq()` helper due to a version mismatch issue. See [REPOSITORY_PATTERN.md](../architecture/REPOSITORY_PATTERN.md#sql-template-workaround).

## Consequences

### Positive

- **Full type inference** - Schema types flow through to services
- **Lightweight** - No heavy ORM abstraction, close to SQL
- **Good migration story** - `drizzle-kit push` for development, migration files for production
- **Modern tooling** - Active development, good community

### Negative

- **Schema type leakage** - Domain interfaces currently import infrastructure types
- **Version sensitivity** - Encountered type mismatches between drizzle-orm versions
- **Less mature than Prisma** - Some rough edges in tooling

### Workarounds in Place

| Issue | Workaround |
|-------|------------|
| `eq()` type mismatch | Use `sql` tagged templates |
| In-memory filtering | Some filters applied post-query (MVP trade-off) |

## Alternatives Considered

### Prisma

**Pros:** More mature, excellent DX  
**Cons:** Heavier runtime, generated client, less control over queries  
**Rejected because:** Drizzle's lightweight approach better fits our layered architecture

### TypeORM

**Rejected because:** Decorator-based approach, heavier abstraction

### Raw SQL with pg

**Rejected because:** Manual type definitions, no migration tooling

### Kysely

**Considered but:** Drizzle offered similar benefits with slightly better migration story

## Future Considerations

- **Pure domain entities** - Create domain types separate from Drizzle schema types
- **Query optimization** - Replace in-memory filtering with proper SQL composition
- **Connection pooling** - Evaluate pg-pool configuration for production scale
