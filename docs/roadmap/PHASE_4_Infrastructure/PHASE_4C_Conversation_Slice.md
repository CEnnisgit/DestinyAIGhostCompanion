# Phase 4C: Conversation Slice

> **Status:** 🟢 Route-verified — `/ws/voice` is mounted and, with no LLM key configured, correctly returns 503 to an upgrade request (graceful-disable path works). ⛔ Remaining: a live voice turn (real WebSocket client + an `LLM_API_KEY`/`OPENAI_API_KEY`) to exercise `VoiceCommandSaga` → intent → response.
> **Objective:** Build the communication bridge so the Electron/Web frontend can stream voice commands to the Ghost and receive AI-generated responses.
> **Crates:** `crates/api`
> **Depends On:** Phase 4B (user must be authenticated)
>
> **Delivered:** `crates/api/src/openai_client.rs` (`OpenAiClient` → `GenerativeAiPort`,
> configurable `LLM_BASE_URL`/`LLM_MODEL` per ADR-007, JSON-object response coerced into
> `VoiceIntent` with an adapter-side schema hint); `crates/api/src/websocket_handler.rs`
> (`/ws/voice`, parses `{text}`, runs `VoiceCommandSaga`, returns `{response,intent}`, dev-token
> auth seam + `describe_intent` test); wired into `build_router` and the `apps/server`
> composition root (personality via `GHOST_PERSONALITY`, server boots even without an LLM key).
>
> **Note:** the spec referenced a `Greeting` intent; the real `VoiceIntent` enum has no such
> variant, so greetings fall through to `Unknown`. Gear/lore execution is acknowledged only —
> it lands in Phases 4D/4E.

---

## Context for the Agent

The Domain layer contains:
1. **`VoiceCommandSaga`** at `crates/domain/src/voice_ai/saga.rs` — Orchestrates intent parsing with automatic failover between a primary and fallback AI port.
2. **`GenerativeAiPort`** at `crates/domain/src/voice_ai/ports.rs` — The trait your adapter must implement:
   - `interpret_command(&self, system_prompt: &str, user_input: &str) -> Result<VoiceIntent>`
3. **`VoiceIntent`** at `crates/domain/src/voice_ai/intent.rs` — A strongly-typed enum representing parsed user intentions (equip, vault, lore query, etc.).

Your job is to:
- Implement the AI client that talks to OpenAI (or any OpenAI-compatible API per ADR 007).
- Build the WebSocket server that the frontend connects to for real-time voice streaming.

## Deliverables

### 1. `crates/api/src/openai_client.rs`
Implement `GenerativeAiPort` using `reqwest`:
- Hit `POST https://api.openai.com/v1/chat/completions`
  - Model: `gpt-4o-mini` (or configurable via env var `LLM_MODEL`).
  - Messages: `[{role: "system", content: system_prompt}, {role: "user", content: user_input}]`
  - Set `response_format: { type: "json_object" }` to guarantee structured output.
- Parse the response JSON into a `VoiceIntent` using `serde_json::from_str`.
- Per **ADR 007**, this adapter MUST work with any OpenAI-compatible API (Ollama, Grok, etc.) — the base URL should be configurable via env var `LLM_BASE_URL` (default: `https://api.openai.com/v1`).

### 2. `crates/api/src/websocket_handler.rs`
Implement an `axum` WebSocket endpoint:
- **Route:** `GET /ws/voice` (upgrades to WebSocket)
- **Authentication:** Validate the user's session token from the WebSocket handshake headers or query params. Reject unauthenticated connections.
- **Inbound Messages:** The frontend sends JSON: `{ "text": "equip my Sunshot" }`
- **Processing Pipeline:**
  1. Pass `text` through `VoiceCommandSaga::process(system_prompt, user_input)`.
  2. The saga returns a `VoiceIntent`.
  3. Route the intent:
     - `VoiceIntent::EquipItem { name, character }` → call `EquipItemSaga::process_equip()`
     - `VoiceIntent::LoreQuery { topic }` → call `LoreSaga::process(topic)`
     - `VoiceIntent::Greeting` / `VoiceIntent::Unknown` → generate a conversational response.
- **Outbound Messages:** Return JSON: `{ "response": "Done! Sunshot equipped.", "intent": "equip_item" }`

### 3. Wire into `main.rs`
Add the WebSocket route and OpenAI client to the existing `axum` Router:
```rust
let openai = Arc::new(OpenAiClient::new(base_url, api_key, model));
let voice_saga = VoiceCommandSaga::new(openai.clone(), openai.clone()); // primary + fallback

let app = Router::new()
    .route("/auth/login", get(auth_login))
    .route("/auth/callback", get(auth_callback))
    .route("/ws/voice", get(websocket_handler));
```

## Verification
- [ ] Connect to `ws://localhost:8080/ws/voice` using a WebSocket client (e.g., `websocat` or browser dev tools).
- [ ] Send `{ "text": "hello Ghost" }` → receive a JSON response with `intent: "greeting"`.
- [ ] Send `{ "text": "equip Sunshot" }` → receive a JSON response with `intent: "equip_item"` (will fail gracefully because Inventory adapters aren't built yet — that's Phase 4D).

## ADR References
- **ADR 007**: Universal OpenAI-Compatible LLM Adapter — configurable base URL.
- **ADR 008**: Voice AI Failover Circuit — the `VoiceCommandSaga` automatically falls back to the secondary port if the primary fails.

## Next Phase
Once verified, proceed to → [Phase 4D: Inventory Slice](./PHASE_4D_Inventory_Slice.md)
