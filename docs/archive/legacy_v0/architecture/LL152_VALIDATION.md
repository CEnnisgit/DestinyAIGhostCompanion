# LL152 Validation

> NYC DOB compliance rules for gas piping inspections

## Background

**Local Law 152** requires periodic inspections of gas piping systems in NYC buildings. Our validation ensures inspection forms meet DOB submission requirements.

---

## Two-Layer Validation

### Layer 1: Schema Validation (Zod)

Validates data types and required fields:

```typescript
const LL152FormPayloadSchema = z.object({
  inspectorName: z.string().min(1),
  inspectorLicense: z.string().min(1),
  inspectionDate: z.string(),  // ISO date
  gasPipingCondition: z.enum(['GOOD', 'FAIR', 'POOR']),
  defects: z.array(DefectSchema),
  overallResult: z.enum(['PASS', 'FAIL']),
  notes: z.string().optional(),
  photos: z.array(z.string()).min(2),  // URLs
  clientSignature: z.string().min(1),  // Base64
});
```

### Layer 2: Business Rules

Validates DOB compliance logic:

| Rule | Description | Severity |
|------|-------------|----------|
| Critical defects → FAIL | If any `CRITICAL` defect, result must be `FAIL` | **Error** |
| FAIL needs defects | `FAIL` result should have documented defects | Warning |
| Notes recommended | Empty notes generate a warning | Warning |

---

## Error vs Warning

| Type | Effect | Example |
|------|--------|---------|
| **Error** | Blocks submission | "CRITICAL defect found but result is PASS" |
| **Warning** | Allows submission, logged | "No notes provided" |

---

## Code Location

| File | Responsibility |
|------|----------------|
| [@pcd/compliance-forms-core](file:///c:/github/pcd/packages/features/compliance-forms/core/src/schema.ts) | Zod schema (source of truth) |
| [modules/compliance/application/forms/](file:///c:/github/pcd/apps/backend/src/modules/compliance/application/forms/) | UseCase handlers |
| [forms/routes.ts](file:///c:/github/pcd/apps/backend/src/app/http/routes/forms/routes.ts) | HTTP endpoints |

> **Note**: After the feature-centric refactor, the Zod schema moved to `@pcd/compliance-forms-core`. Both mobile and backend import from this single source of truth.

---

## Adding New Rules

1. **Open** `LL152ValidationService.ts`

2. **Add rule** in `validateBusinessRules()`:
   ```typescript
   private validateBusinessRules(data: LL152FormPayload, result: ValidationResult): void {
     // Existing rules...
     
     // Your new rule
     if (data.someCondition) {
       result.errors.push('Your error message');
       result.isValid = false;
     }
   }
   ```

3. **Add tests** in `LL152ValidationService.test.ts`

---

## DOB Compliance Notes

> [!IMPORTANT]
> These rules are based on NYC DOB requirements as of 2024. When regulations change, update both the Zod schema AND business rules.

**Key DOB Requirements:**
- Licensed plumber must sign
- Inspection date must be within valid period
- Photos must document gas piping condition
- Critical defects require remediation before PASS
