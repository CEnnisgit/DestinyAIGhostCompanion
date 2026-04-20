# Ports & Adapters: Equip Gear

Following strict Hexagonal Architecture, the core Rust business logic in the `EquipGearSaga` never knows *how* external data is moved. It only communicates through defined Ports.

## 1. Primary Driver Port
How the outside triggers an Equip.
**`trait EquipCommandHandler`**
- **Method**: `execute(intent: EquipIntent) -> Result<Success, DomainError>`
- **Real Adapter**: The Axum router inside `crates/api` which parses the incoming JSON request from the Electron Desktop client and calls this interface.

## 2. Secondary Driven Ports
How the Core commands the outside to do things.
**`trait DestinyTransferClient`**
- **Method**: `transfer_item(item_id: i64, target_character: i64, to_vault: bool)`
- **Method**: `equip_item(item_id: i64, target_character: i64)`
- **Real Adapter**: A specialized `reqwest` module that builds the exact HTTPS POST payload expected by `bungie.net/Platform/Destiny2/Actions/Items/TransferItem/`, attaching the decrypted OAuth Bearer token.

**`trait ManifestCacheReader`**
- **Method**: `get_item_definition(hash: u32) -> Result<ItemDef, RepoError>`
- **Real Adapter**: The `sqlx` module inside `crates/db` that opens a fast SQLite socket to read the local Bungie Manifest disk file.
