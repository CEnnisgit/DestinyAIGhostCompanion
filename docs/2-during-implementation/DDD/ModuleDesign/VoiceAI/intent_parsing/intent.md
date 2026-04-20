# Value Object: VoiceIntent

**Module Path:** `crates/domain/src/voice_ai/intent.rs`

## Description
Due to **ADR 009 (Structured JSON Intents)**, the Voice AI domain strictly processes deterministic JSON payloads instead of regex matches. The `VoiceIntent` enum natively represents these actions.

## Defined Intents Phase 1
- `Equip`: Equip an item on a specific character.
- `Transfer`: Move an item to the vault.
- `PullPostmaster`: Extract engrams/items caught in the postbox.
- `QueryInventory`: Simple read-operations for the user.
- `Lore`: Lore queries.
- `Unknown`: Fallback state when the AI cannot map the speech.
