# Assets Sub-Module (CRM)

> **Parent:** [CRMModule](../README.md)

## Responsibilities
**Asset Registry**: Manages the physical buildings.
- **Building Profile**: `SFR-IODE-11` Address, BIN, Block, Lot.
- **Cycle Determination**: Storing `community_district` to drive compliance logic.

## Key Algorithms
- **Address Normalization**: Ensuring "123 Main St" and "123 Main Street" resolve identically.

## Data Structures
- `buildings` table.
