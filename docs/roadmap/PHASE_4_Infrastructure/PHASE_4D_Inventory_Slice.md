# Phase 4D: Inventory Slice

> **Status:** 🔲 Not Started
> **Objective:** Implement the Bungie API HTTP client so the Ghost can physically move, equip, and vault weapons and armor in Destiny 2.
> **Crates:** `crates/api`, `crates/db`
> **Depends On:** Phase 4B (authenticated user with stored token)

---

## Context for the Agent

The Domain layer contains:
1. **`EquipItemSaga`** at `crates/domain/src/inventory/saga.rs` — The physics engine for inventory transactions. It enforces **strict serial execution** (ADR 010) and **graceful conversational error yielding** (ADR 011).
2. **`BungieInventoryPort`** at `crates/domain/src/inventory/ports.rs` — The trait your adapter must implement:
   - `locate_item(&self, membership_id, hash) -> Result<ItemLocation>`
   - `transfer_item(&self, membership_id, hash, to_vault, character_id) -> Result<()>`
   - `equip_item(&self, membership_id, hash, character_id) -> Result<()>`
   - `pull_postmaster(&self, membership_id, hash, character_id) -> Result<()>`
3. **`ManifestDatabasePort`** at `crates/domain/src/inventory/ports.rs` — For fuzzy-matching item names to hashes:
   - `resolve_item_hash(&self, transcribed_name) -> Result<DestinyItemHash>`

Your job is to implement the HTTP wrappers that talk to Bungie's REST API.

## Deliverables

### 1. `crates/api/src/bungie_inventory_client.rs`
Implement `BungieInventoryPort` using `reqwest`. All requests require:
- Header: `Authorization: Bearer {access_token}`
- Header: `X-API-Key: {BUNGIE_API_KEY}`

#### `locate_item`
- `GET https://www.bungie.net/Platform/Destiny2/{membershipType}/Profile/{membershipId}/?components=102,201,205,300`
  - Component 102 = ProfileInventories (vault)
  - Component 201 = CharacterInventories
  - Component 205 = CharacterEquipment
  - Component 300 = ItemInstances
- Search through the response to find the item by hash. Return the `ItemLocation` enum:
  - `EquippedOnCharacter(character_id)`
  - `InventoryOnCharacter(character_id)`
  - `Vault`
  - `Postmaster`

#### `transfer_item`
- `POST https://www.bungie.net/Platform/Destiny2/Actions/Items/TransferItem/`
  - Body: `{ "itemReferenceHash": hash, "stackSize": 1, "transferToVault": to_vault, "itemId": instance_id, "characterId": character_id, "membershipType": type }`

#### `equip_item`
- `POST https://www.bungie.net/Platform/Destiny2/Actions/Items/EquipItem/`
  - Body: `{ "itemId": instance_id, "characterId": character_id, "membershipType": type }`

#### `pull_postmaster`
- `POST https://www.bungie.net/Platform/Destiny2/Actions/Items/PullFromPostmaster/`
  - Body: `{ "itemReferenceHash": hash, "stackSize": 1, "itemId": instance_id, "characterId": character_id, "membershipType": type }`

> [!IMPORTANT]
> **ADR 010: Strict Serial Execution.** The `EquipItemSaga` already enforces serial `.await` chains. Your adapter MUST NOT add any parallel `tokio::join!` or `futures::join!` calls. Each HTTP request must complete fully before the next one begins. Bungie's rate limit is 25 req/sec and concurrent mutations on the same item will cause 500 errors.

### 2. `crates/db/src/manifest_item_resolver.rs` (Temporary)
Implement a simple `ManifestDatabasePort` that does basic fuzzy matching:
- For now, query the Postgres `destiny_items` table (which will be fully populated in Phase 4E).
- Use `ILIKE '%{name}%'` for basic fuzzy matching until the full RAG pipeline is ready.
- If the table doesn't exist yet, create a migration `003_create_destiny_items.sql`:
  ```sql
  CREATE TABLE IF NOT EXISTS destiny_items (
      hash          BIGINT PRIMARY KEY,
      name          TEXT NOT NULL,
      item_type     TEXT,
      tier_type     TEXT,
      icon_path     TEXT
  );
  CREATE INDEX idx_destiny_items_name ON destiny_items USING GIN (to_tsvector('english', name));
  ```

### 3. Wire into `main.rs`
```rust
let bungie_client = Arc::new(BungieInventoryClient::new(reqwest_client, api_key));
let manifest_resolver = Arc::new(ManifestItemResolver::new(pool.clone()));
let equip_saga = EquipItemSaga::new(bungie_client, manifest_resolver);
```

### 4. Add WebSocket Intent Routing
In the WebSocket handler (from Phase 4C), connect `VoiceIntent::EquipItem` to the real saga:
```rust
VoiceIntent::EquipItem { name, character } => {
    equip_saga.process_equip(&membership_id, &name, &character).await
}
```

## Verification
- [ ] Authenticate via Phase 4B login flow.
- [ ] Send via WebSocket: `{ "text": "equip my Sunshot on my Titan" }`
- [ ] Verify the Ghost responds: `"Successfully equipped Sunshot."` (requires the item to exist in Destiny 2 account).
- [ ] Verify the item physically moved in-game (check DIM or the Destiny Companion App).

## ADR References
- **ADR 010**: Strict Serial Inventory Mutations — no concurrent Bungie API calls for the same item.
- **ADR 011**: Inventory Saga State Rollbacks — graceful conversational error messages at every failure point.

## Next Phase
Once verified, proceed to → [Phase 4E: Lore RAG Slice](./PHASE_4E_Lore_RAG_Slice.md)
