# Hexagonal Ports

**Module Path:** `crates/domain/src/voice_ai/ports.rs`

## 1. GenerativeAiPort (Secondary/Driven)
As defined in **ADR 007**, this single trait universally replaces `grok.py` and `ollama.py`. 
It accepts a System Prompt and User Audio string, and promises to return a cleanly formatted `Result<VoiceIntent>`. Implementations of this port (living in `crates/api` or `crates/db`) are expected to adhere to the generic OpenAI REST API standard structure.
