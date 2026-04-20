# ADR 008: Automatic LLM Failover Circuit

## Status
Accepted

## Context
The Ghost Companion is completely reliant on Voice AI for its core functionality. If the external LLM provider goes down (e.g., API outage, rate limiting, connection failure), the companion immediately becomes useless, ruining the user's in-game experience. Cloud-native AI applications often suffer from unpredictable degraded performance.

## Decision
We will implement an **Automatic Failover Circuit** within the `voice_ai` domain orchestrator. 
The system will be configured with a Primary Provider (e.g., cloud-hosted Grok) and a Secondary Fallback Provider (e.g., desktop-hosted local Ollama). If the `GenerativeAiPort` yields an HTTP 500, a connection timeout, or an HTTP 429 (Too Many Requests), the domain saga will catch the error, suppress it from the user, and immediately retry the identical request against the Fallback Provider.

## Consequences
- **Positive:** Extremely high availability. If the user's internet lags or the cloud provider crashes in the middle of a raid, the app falls back to local processing without interrupting their gameplay.
- **Negative:** Increased complexity in the Saga orchestrator to manage state rollbacks and tracking which provider is currently active.
