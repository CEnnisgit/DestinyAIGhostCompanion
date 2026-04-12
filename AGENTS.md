# Agent Notes

## Bungie API First
- The Bungie API is the foundation of this app.
- At the start of every session that touches auth, profile data, inventory, equips, transfers, vaulting, postmaster, manifest, or item definitions, verify behavior against Bungie API docs before changing code.
- Primary references:
  - https://destinydevs.github.io/BungieNetPlatform/docs/Endpoints
  - https://github.com/Bungie-net/api
  - https://bungie-net.github.io/multi/index.html
- Prefer Bungie OpenAPI/docs/repo over memory when endpoint shapes or payload requirements are unclear.

## Inventory Rules
- Treat weapons and armor as the MVP gear-management scope.
- Preserve Bungie flow constraints:
  - vault moves use character-to-vault transfer
  - vault pulls use vault-to-character transfer
  - postmaster items must be pulled before equip/vault workflows complete
  - equipped items on another character cannot be moved until unequipped
- Reuse one normalized inventory/action contract across chat commands and UI actions.

## Voice Mode
- Voice mode should stay functional even when no server-side STT/TTS provider is configured.
- Browser speech capture and browser speech synthesis are the baseline fallback.
