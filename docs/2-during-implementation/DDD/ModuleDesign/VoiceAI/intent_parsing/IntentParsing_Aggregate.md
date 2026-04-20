# Aggregate Root: IntentParser

**Bounded Context:** Voice AI
**Feature Slice:** `intent_parsing`

## 1. Description
The `IntentParser` acts as a firewall between the unpredictable physics of natural language from Ollama and the strict requirements of the Cargo workspace.

## 2. Core Invariants (Rules)
1. **Fallback Confidence**: If the LLM generates a JSON payload that does not match the strong schemas, the Parser rejects it and triggers a fallback response ("I didn't quite catch that, Guardian").
2. **Prohibited Action Firewall**: If the LLM hallucinates an intent to "Delete", "Infuse", or "Spend Glimmer", the Parser forcefully catches it and aborts the flow, enforcing `SFR-BRC-01`.
3. **Fuzzy Item Hashing**: The LLM output might just be "Sunshot". The Parser must immediately evaluate this string against the `ManifestCache` to resolve it to `u32: 2907129557` before sending it to the `Inventory` domain.

## 3. Hexagonal Ports
- **Driver Port**: Listens for HTTP POSTs with Raw Audio/Text from the Presentation layer.
- **Driven Port (`LlmInferenceAdapter`)**: The interface for executing HTTP requests against `localhost:11434` (Ollama) or the Grok fallback.
