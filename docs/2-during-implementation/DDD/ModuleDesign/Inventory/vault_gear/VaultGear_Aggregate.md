# Aggregate Root: VaultGearSaga

**Bounded Context:** Inventory
**Feature Slice:** `vault_gear`

## 1. Description
The `VaultGearSaga` is the orchestrator responsible for safely extracting an item from a character and depositing it into the global Vault.

## 2. Core Invariants (Rules)
The Saga enforces the following strict Domain Rules:
1. **Vault Capacity constraint:** The global vault must have at least 1 free slot (out of 600 or 700 max). If full, the saga aborts.
2. **Active Equip constraint:** An item cannot be vaulted if the player is currently holding/wearing it. The saga must identify the active status and, if true, equip an arbitrary fallback item from the character's bucket to "free" the target item before transferring.

## 3. Hexagonal Ports
- **Driver Port (`VaultCommandPort`)**: Receives the intent from the Bounded Context interface.
- **Driven Port (`BungieTransferAdapter`)**: The interface for executing `TransferItem` over HTTP with `transferToVault = true`.

## 4. Required Datatypes to be Modeled
Based on the invariants above, we will need to model the following in subsequent VO/Entity/Event files:
- **VOs**: VaultCapacity, ItemHash.
- **Entities**: VaultManifest.
- **Events**: VaultSucceeded.
