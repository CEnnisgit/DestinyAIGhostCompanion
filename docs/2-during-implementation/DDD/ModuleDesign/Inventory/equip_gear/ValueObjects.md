# Value Objects & Entities: Equip Gear

Based on the invariants enforced by the `EquipGearSaga`, the Domain mandates the following immutable and mutable data structures.

## Value Objects (VO)
Value objects have no conceptual identity; they describe characteristics.
- **`ItemHash` (u32)**: The static Bungie identifier defining a piece of gear. Used exclusively to cross-reference the Manifest cache.
- **`ItemInstanceId` (i64)**: A guaranteed unique identifier mapping to a player's physical gear drop. Required for all transfer API payloads.
- **`CharacterId` (i64)**: The distinct identifier mapping to the User's Titan, Hunter, or Warlock.
- **`BucketHash` (u32)**: Discriminates whether gear goes to Kinetic, Energy, Power, Helmet, etc.

## Entities
Entities hold an ongoing identity across time and are manipulated by the Saga.
- **`MasterInventory`**: The full tree of all items across the Vault and all 3 characters. The Saga parses this entity to discover if the `ItemInstanceId` requires moving.
- **`CharacterLoadout`**: The specific bucket array of equipped items on a character. Required to validate if a slot has space or needs an unequip.
