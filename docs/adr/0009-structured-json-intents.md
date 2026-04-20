# ADR 009: Structured JSON Intents vs Regex Parsing

## Status
Accepted

## Context
The legacy Python application (`ghost/assistant.py`) relied on prompting an LLM to generate raw text, and then applying thousands of lines of Regex chains to deduce what the LLM wanted to do (e.g., looking for the word "equip" followed by a noun). This was brittle, highly prone to hallucinations, and caused catastrophic failures when the LLM decided to use a synonym or format the text differently.

## Decision
We will strictly forbid the use of raw text regex for command execution. We will utilize **Structured JSON Outputs**.
The `voice_ai` domain will prompt the `GenerativeAiPort` to return a strict JSON payload adhering to a predefined schema. 

For example:
```json
{
  "action": "EQUIP",
  "target_item_name": "Sunshot",
  "character_class": "Warlock"
}
```
The Rust domain will use `serde` to deserialize this JSON payload directly into a strongly-typed `VoiceIntent` enum. If deserialization fails, the adapter will reject the response and force the LLM to fix its formatting.

## Consequences
- **Positive:** Mathematical certainty in intent parsing. Eliminates 99% of "hallucination-induced" application crashes. Vastly reduces the mental overhead of maintaining regex patterns.
- **Negative:** Slightly increased latency, as structured JSON generation can occasionally be marginally slower for smaller, less capable LLMs (like an 8B param local model) to compute.
