# Ports & Adapters: Vault Gear

Following strict Hexagonal Architecture, the core Rust business logic in the `VaultGearSaga` never knows *how* external data is moved. It only communicates through defined Ports.

## 1. Primary Driver Port
How the outside triggers a Vault action.
**`trait VaultCommandHandler`**
- **Method**: `execute(intent: VaultIntent) -> Result<Success, DomainError>`
- **Real Adapter**: The Axum router inside `crates/api`.

## 2. Secondary Driven Ports
How the Core commands the outside to do things.
**`trait DestinyTransferClient`**
- **Method**: `transfer_item(item_id: i64, target_character: i64, to_vault: bool)`
- **Real Adapter**: A specialized `reqwest` module executing the HTTPS payload. 

**Note**: To push an item to the vault, `transfer_item` is called with `to_vault = true` and `target_character` explicitly mapped to the character currently holding the item.
