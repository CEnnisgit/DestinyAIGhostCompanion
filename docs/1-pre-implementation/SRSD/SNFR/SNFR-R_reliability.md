# Non-Functional Requirements: Reliability (SNFR-R)

## Availability (SNFR-RAV)
- **`SNFR-RAV-01` (Bungie Graceful Degradation)**: The Destiny 2 API goes down frequently for server maintenance. The companion must detect HTTP 500s or "API Maintenance" flags and respond with an in-universe spoken explanation rather than a generic stack trace.

## Fallback Modes (SNFR-RF)
- **`SNFR-RF-01` (LLM Fallback)**: If the `localhost:11434` Ollama instance crashes or the host PC lacks sufficient hardware, the system should smoothly failover to a configured cloud API (such as Grok) automatically.
- **`SNFR-RF-02` (STT/TTS Fallback)**: If backend audio pipelines fail, the client interfaces MUST default to using the native browser `SpeechRecognition` and `speechSynthesis` APIs to ensure the app continues to function seamlessly.
