# ADR 007: Universal OpenAI LLM Adapter

## Status
Accepted

## Context
In the legacy Python architecture, the `ghost/` directory contained discrete files for each LLM provider (`grok.py`, `ollama.py`). This led to massive code duplication, as both files had to individually manage HTTP sessions, parsing algorithms, and system prompt injections. As external LLM APIs evolve, managing distinct adapters for every provider (OpenAI, Anthropic, Grok, local Ollama) becomes an unsustainable technical debt.

## Decision
We will deprecate all provider-specific HTTP adapters. The Rust `crates/domain/src/voice_ai/ports.rs` will define a standard `GenerativeAiPort`.
We will implement a **single, universal adapter** (`OpenAIApiAdapter`) that strictly adheres to the standard `POST /v1/chat/completions` REST specification. Because almost all modern providers (including Grok and Ollama) are OpenAI-compatible, the application will hot-swap providers simply by altering the `base_url` parameter in the environment configuration, requiring zero code changes.

## Consequences
- **Positive:** Massive reduction in boilerplate code. Trivial to add support for new LLM providers in the future.
- **Negative:** If a specific provider rolls out a proprietary feature that diverges from the OpenAI specification (e.g., Anthropic's unique prompt caching syntax), the universal adapter will not be able to immediately utilize it natively.
