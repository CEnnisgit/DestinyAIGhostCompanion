# Value Objects & Entities: Vault Gear

Based on the invariants enforced by the `VaultGearSaga`, the Domain mandates the following data structures.

## Value Objects (VO)
- **`ItemInstanceId` (i64)**: Identifies the exact item needing vaulting.
- **`VaultCapacityStatus` (u16)**: Tracks the `current_count` vs `max_capacity` (600 or 700).

## Entities
- **`PlayerVault`**: The entity representing the global storage node. The Saga interacts with this entity strictly to enforce capacity limits before firing API calls.
