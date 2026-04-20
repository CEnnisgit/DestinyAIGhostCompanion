# Form Payload Handling

> JSONB storage and partial update strategy for inspection forms

## Why JSONB?

LL152 forms have complex, nested data. JSONB provides:
- Flexible schema (easy to add fields)
- Partial updates without fetching full document
- Native JSON querying in PostgreSQL

---

## Schema

```typescript
// inspectionForms.ts
formPayload: jsonb('form_payload').notNull().default({}),
```

The `formPayload` field stores the entire LL152 form data.

---

## Partial Merge Behavior

When technician updates form, we **merge** payloads:

```typescript
// FormService.ts
async updateFormPayload(formId: string, update: { formPayload: object }) {
  const existing = await this.formRepo.findById(formId);
  
  // Merge: new values override, existing values preserved
  const merged = {
    ...existing.formPayload,
    ...update.formPayload,
  };
  
  return this.formRepo.updatePayload(formId, merged);
}
```

**Example:**
```typescript
// Existing payload
{ inspectorName: "John", photos: ["url1"] }

// Update request
{ photos: ["url1", "url2"], notes: "Checked basement" }

// Result (merged)
{ inspectorName: "John", photos: ["url1", "url2"], notes: "Checked basement" }
```

---

## TypeScript Typing

```typescript
// Form entity from DB
interface InspectionForm {
  formPayload: Record<string, unknown>;  // Loose typing from DB
}

// Validated payload for submission
type LL152FormPayload = z.infer<typeof LL152FormPayloadSchema>;
```

> [!NOTE]
> `formPayload` is loosely typed until validation. Only on submission do we parse with Zod to get strongly-typed `LL152FormPayload`.

---

## Validation Timing

| Action | Validation |
|--------|------------|
| Create form | None (empty payload OK) |
| Update payload | None (partial data OK) |
| Validate endpoint | Full Zod + business rules |
| Submit form | Full validation required |

---

## Code Location

| File | Responsibility |
|------|----------------|
| [@pcd/compliance-forms-core](file:///c:/github/pcd/packages/features/compliance-forms/core/src/schema.ts) | Zod schema (source of truth) |
| [modules/compliance/application/forms/](file:///c:/github/pcd/apps/backend/src/modules/compliance/application/forms/) | Merge logic in UseCases |
| [DrizzleFormRepository.ts](file:///c:/github/pcd/apps/backend/src/modules/compliance/adapters/drizzle/DrizzleFormRepository.ts) | DB persistence |

> **Note**: After the feature-centric refactor, form payload types are shared via `@pcd/compliance-forms-core`.
