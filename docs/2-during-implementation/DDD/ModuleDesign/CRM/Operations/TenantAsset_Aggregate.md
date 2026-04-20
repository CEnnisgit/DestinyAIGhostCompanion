# ⚠️ SUPERSEDED — Do Not Implement

> **This spec is retired.** Per [ADR-0021: Client-Centric Portfolio](../../../../adr/0021-client-centric-portfolio.md), the tenant portfolio centers on **Clients**, not buildings. The `TenantAsset(FirmID, BIN)` model was the wrong abstraction.
>
> **Replaced by:** [Client Aggregate Spec](../Clients/Client_Aggregate.md) + [Building Bookmarks (ADR-0022)](../../../../adr/0022-building-bookmarks.md)
>
> This file is kept for historical reference only.

---

# TenantAsset Aggregate Specification (RETIRED)

**Module:** `CRM`
**Sub-Module:** `Operations`
**Source of Truth:** Not yet implemented in Rust — future CRM Operations sub-module

## 1. Core Decision: The Firm's Link to Reality
This Aggregate represents **a Firm's relationship with a Building**. It allows multiple firms to "claim" or "track" the same physical building without colliding. It stores all private data (notes, statuses, tags) that belongs to the firm.

*   **Primary Identity:** Composite Key `(FirmID, BIN)`.
*   **Foreign Keys:**
    *   `FirmID` -> Auth/Tenant Module.
    *   `BIN` -> `CRM/Assets/Building` (Global Identity).

## 2. Attributes

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Internal PK. |
| `firmId` | `UUID` | The Tenant. |
| `bin` | `BIN` (VO) | Strategies to the Global Building. |
| `nickname` | `string?` | Optional internal name (e.g. "The Smith Building"). |
| `internalStatus` | `string` | e.g. "Prospect", "Active Client", "Do Not Contact". |
| `tags` | `string[]` | e.g. ["urgent", "violation_risk"]. |
| `notes` | `text` | Free-text notes. |
| `bucketId?` | `UUID` | Optional link to a Bucket/List. |

## 3. Aggregate Behavior

### Factory
`TenantAsset.track({ firmId, bin })`
*   Creates the link.
*   Default status: "tracked".

### Methods
*   `updateStatus(newStatus: string)`
*   `addTag(tag: string)`
*   `moveToBucket(bucketId: UUID)`

## 4. Persistence

```sql
CREATE TABLE tenant_assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  firm_id UUID NOT NULL,
  bin VARCHAR(7) NOT NULL REFERENCES buildings(bin), -- FK to Global
  
  -- Firm Private Data
  nickname TEXT,
  internal_status TEXT NOT NULL DEFAULT 'tracked',
  tags TEXT[],
  bucket_id UUID, -- FK to Buckets (if exists)
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(firm_id, bin) -- One asset record per firm per building
);

CREATE INDEX idx_tenant_assets_firm ON tenant_assets(firm_id);
```
