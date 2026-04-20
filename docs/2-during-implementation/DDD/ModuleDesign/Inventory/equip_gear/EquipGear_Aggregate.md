# Aggregate Root: EquipGearSaga

**Bounded Context:** Inventory
**Feature Slice:** `equip_gear`

## 1. Description
Because this is a stateless proxy application, the Aggregate Root is not an Entity like `Weapon`. The Aggregate Root is the **`EquipGearSaga`**: the orchestrator state-machine that ensures the Bungie API constraints are respected when moving a weapon or armor piece.

## 2. Core Invariants (Rules)
The Saga enforces the following strict Domain Rules:
1. **Ownership Constraint:** The requested item must exist within the authenticated user's master profile.
2. **Target Validation:** The character class receiving the item must match the class restrictions of the item (e.g. Hunters cannot equip Warlock bonds).
3. **Space Availability (Transitive Transfer):** An item cannot be pulled from the Vault to Character B if Character B's bucket (e.g. Kinetic slot) is fully maxed at 10/10 slots.
4. **Unequip Safety:** An item actively equipped on Character A cannot be transferred. The Saga *must* swap it with a fallback item on Character A before moving it to the Vault.

## 3. Hexagonal Ports
- **Driver Port (`EquipCommandPort`)**: Receives the fully parsed intent (`EquipWeapon`) from the `VoiceAI` Bounded Context.
- **Driven Port (`BungieTransferAdapter`)**: The interface for executing `TransferItem` and `EquipItem` over HTTP.

## 4. Required Datatypes to be Modeled
Based on the invariants above, we will need to model the following in subsequent VO/Entity/Event files:
- **VOs**: Identifier hashes, Capacity counters.
- **Entities**: ItemInstance.
- **Events**: EquipSucceeded, EquipFailedCapacity.
