# Bounded Context: Inventory

> **Core Responsibility:** Managing the physical state of the Bungie.net API Inventory rules.

This module houses the vertical features associated with manipulating Player gear.

## Defined Feature Slices
1. **[equip_gear](./equip_gear/)**: Transfers and equips items onto an active character's loadout.
2. **[vault_gear](./vault_gear/)**: Unequips and transfers items safely back into the global Player Vault.
