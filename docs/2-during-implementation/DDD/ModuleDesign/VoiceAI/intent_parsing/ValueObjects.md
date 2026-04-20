# Value Objects & Entities: Intent Parsing

Based on the invariants enforced by the `IntentParser`, the Domain mandates the following data structures.

## Value Objects (VO)
- **`Transcript` (String)**: The raw text generated from speech.
- **`ConfidenceScore` (f32)**: Confidence of the LLM parsed intent.
- **`DestinyIntent` (Enum)**: A strict Rust Enum modeling valid actions: `Equip { item_hash, ... }`, `Vault { item_hash, ... }`, `Converse { text }`.

## Entities
- **`ConversationContext`**: A sliding window of the last 10 intents and responses, allowing the LLM to remember context (e.g. "Equip the hand cannon" -> "Now vault it").
