# Ports & Adapters: Intent Parsing

## Secondary Driven Ports

**`trait LocalLlmClient`**
- **Method**: `generate_intent(context: ConversationContext, transcript: Transcript) -> Result<DestinyIntent, LlmError>`
- **Real Adapter**: A `reqwest` wrapper mapping to the Ollama JSON API.

**`trait FallbackLlmClient`**
- **Real Adapter**: A wrapper mapping to the External Grok/OpenAI interface if local computation hardware is insufficient.
