# Saga Root: VoiceCommandSaga

**Module Path:** `crates/domain/src/voice_ai/saga.rs`

## Description
The state machine orchestrating the transcription to JSON intent pipeline.

## Core Process Flow
The Saga uniquely guarantees High-Availability via **ADR 008 (Automatic LLM Failover)**.
1. The Saga initializes with both a Primary Port (Grok) and Secondary Port (Local Ollama).
2. It attempts to resolve Intent via the Primary Port.
3. If the primary port returns an `Err` (e.g. Rate Limit, API Outage), the Saga intercepts the failure and flawlessly reroutes the exact same payload to the Offline Local port.
4. Returns the successful `VoiceIntent` back to the driver.
