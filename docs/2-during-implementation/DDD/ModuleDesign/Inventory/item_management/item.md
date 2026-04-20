# Value Objects: Item Logic

**Module Path:** `crates/domain/src/inventory/item.rs`

## Description
This module explicitly defines the mathematical parameters of an item.

1. **`DestinyItemHash`**: An integer representing the Bungie Manifest ID. It physically cannot be instantiated with a `0`, protecting the APIs from null-hash lookups.
2. **`ItemLocation`**: An Enum isolating exactly where a physical item sits in the Bungie databases (Vault, Postmaster, Equipped, Inventory).
