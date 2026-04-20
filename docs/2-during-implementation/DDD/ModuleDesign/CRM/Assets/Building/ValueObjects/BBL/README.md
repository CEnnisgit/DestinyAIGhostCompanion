# BBL Value Object Component

**Module:** CRM
**Parent:** Building Aggregate

This folder defines the **Borough-Block-Lot (BBL)**, the fundamental identifier for NYC real estate. Because "Tax Lots" are complex, the domain logic is split into three distinct specifications:

## 1. Core Identity (`BBL_VO_Spec.md`)
> *Start here.*

Defines the **BBL Value Object** itself.
*   **Role:** Immutable Identifier (no business logic).
*   **Shape:** `boroughCode` (1-5), `block` (int), `lot` (int).
*   **Invariants:** Valid ranges (e.g. block > 0), integer enforcement.
*   **Canonical String:** `"1-00123-0045"`

## 2. Input Normalization (`BBL_Source_Adapters.md`)
> *How to safely create a BBL from messy external data.*

Defines the **Adapters** that sit between raw sources (LL152, PAD, Geoclient) and the clean BBL VO.
*   **Role:** Sanitization & Validation.
*   **Sentinel Handling:** Converts explicit sentinels (e.g., `0000000000` from Geoclient/Geosupport) into anomalies, preventing invalid VOs from being created.
*   **Parsing:** String parsing rules (handling padding, delimiters).

## 3. Semantic Meaning (`TaxLotClassification.md`)
> *What "Kind" of lot is this?*

Defines the **Derived Classification** logic.
*   **Role:** Interpretation.
*   **Why split?** A BBL is just an ID. Whether that ID represents a *Condo Billing Lot*, a *Subterranean Lot*, or an *Air Rights Lot* is semantic meaning derived from the lot number ranges.
*   **Logic:** E.g. "Lot 7501-7599 implies Condo Billing context."
