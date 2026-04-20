# Phase 5E: Inventory UI

> **Status:** 🔲 Not Started
> **Objective:** Build a visual gear management interface that lets users browse, equip, vault, and transfer weapons and armor.
> **Location:** `apps/desktop/src/`
> **Depends On:** Phase 5C (authenticated session), Phase 4D (Bungie inventory API)

---

## Context for the Agent

The Rust backend (Phase 4D) exposes inventory operations via the WebSocket:
- `VoiceIntent::EquipItem { name, character }` → equips an item.
- The `BungieInventoryPort` can locate, transfer, equip, and pull from postmaster.

However, the Inventory UI is not only voice-driven — users should also be able to **visually browse** their gear and click to equip or vault items.

## Deliverables

### 1. `apps/desktop/src/hooks/useInventory.ts`
A custom React hook that fetches the user's full inventory:
```typescript
interface UseInventoryReturn {
  characters: Character[];
  vaultItems: InventoryItem[];
  isLoading: boolean;
  refresh: () => void;
  equipItem: (itemHash: number, characterId: string) => Promise<string>;
  vaultItem: (itemHash: number, characterId: string) => Promise<string>;
}
```
- Fetch inventory from the backend REST API: `GET /api/inventory/{membershipId}`
- The backend proxies this to Bungie's profile endpoint (components 102, 201, 205).

### 2. `apps/desktop/src/components/inventory/CharacterCard.tsx`
Display a Destiny character (Titan, Hunter, Warlock):
- Show emblem background image, class icon, power level.
- Equipped weapons (Kinetic, Energy, Power) displayed as item tiles.
- Equipped armor (Helmet, Arms, Chest, Legs, Class Item) displayed below.

### 3. `apps/desktop/src/components/inventory/ItemTile.tsx`
A single inventory item:
```typescript
interface ItemTileProps {
  item: InventoryItem;
  onEquip?: () => void;
  onVault?: () => void;
  onInspect?: () => void;
}
```
- Display the item icon (fetched from `https://www.bungie.net{icon_path}`).
- Tier color border: Exotic = gold (`--gold`), Legendary = purple, Rare = blue.
- Hover state: Show item name tooltip and action buttons (Equip, Vault).
- Click: Open an item detail popover.

### 4. `apps/desktop/src/components/inventory/VaultGrid.tsx`
A scrollable grid displaying all items in the vault:
- Filter tabs: All, Weapons, Armor, Other.
- Search bar for item name filtering.
- Drag-and-drop support (optional, stretch goal).

### 5. `apps/desktop/src/components/inventory/ItemDetailPopover.tsx`
When an item is clicked, show a popover with:
- Full item name and flavor text.
- Tier type (Exotic, Legendary, etc.).
- Current location (which character, vault, postmaster).
- Action buttons: "Equip on [Character Name]", "Send to Vault", "Pull from Postmaster".
- Each action calls the corresponding WebSocket command.

### 6. `apps/desktop/src/pages/InventoryPage.tsx`
The full inventory management page:
- Horizontal character selector at the top (up to 3 characters).
- Selected character's equipped gear displayed prominently.
- Vault grid below.
- Real-time updates: when an equip/transfer completes, the UI refreshes automatically.

### 7. Backend REST Endpoint (if not already created)
The backend may need a new REST endpoint for fetching the full inventory snapshot:
- `GET /api/inventory/:membership_id` → returns structured JSON of characters + vault items.
- This is a read-only proxy to Bungie's profile endpoint.

## Design Constraints
- Item icons must use Bungie's CDN: `https://www.bungie.net{icon_path}`.
- Exotic items should have a subtle gold shimmer animation on hover.
- The grid should match Destiny's in-game UI aesthetic (dark panels, thin borders, high-contrast icons).
- All equip/transfer actions must show a loading spinner on the specific item tile while the operation is in progress.

## Verification
- [ ] The inventory page loads and displays all 3 characters with their equipped gear.
- [ ] Item icons render correctly from Bungie's CDN.
- [ ] Clicking "Equip" on a vault item moves it to the character and updates the UI.
- [ ] Clicking "Vault" on an equipped item moves it to the vault and updates the UI.
- [ ] Error states display gracefully (e.g., "Inventory full" when the character has no space).

## ADR References
- **ADR 010**: Strict Serial Inventory Mutations — the UI must show a loading state and prevent duplicate clicks.
- **ADR 011**: Inventory Saga State Rollbacks — error messages from the backend should be displayed verbatim in the UI.

## Next Phase
Once verified, proceed to → [Phase 5F: Lore Chat](./PHASE_5F_Lore_Chat.md)
