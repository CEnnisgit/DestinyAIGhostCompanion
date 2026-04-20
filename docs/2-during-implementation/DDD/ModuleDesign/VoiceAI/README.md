# Bounded Context: Voice AI

> **Core Responsibility:** Capturing human intent and translating it into strongly typed JSON payloads.

This module houses the vertical features associated with local LLM integration and parsing.

## Defined Feature Slices
1. **[intent_parsing](./intent_parsing/)**: Evaluates Speech-To-Text transcripts via Ollama to determine Actions (Equip, Vault, Lore).
