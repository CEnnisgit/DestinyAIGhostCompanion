Teaching Notes: Code Basics Used Here

Python Essentials
- Modules and imports: Files like `server.py` and `ghost/bungie.py` are modules. `from x import y` pulls in names from modules.
- Types: Hints like `def f(x: int) -> str:` document intent and improve tooling. They don’t change runtime by themselves.
- Dataclasses: `@dataclass` creates lightweight containers with auto-generated `__init__` and friends.
- Virtual environments: Keep dependencies isolated; install via `pip install -r requirements.txt`.

FastAPI Basics
- Endpoints: Decorators `@app.get("/path")` and `@app.post("/path")` make handlers. Use Pydantic models for validation.
- Responses: `JSONResponse` returns JSON; `StreamingResponse` yields chunks for token-by-token updates.
- Middleware: Functions that wrap every request (e.g., logging).

HTTP and Auth
- JWT: A signed JSON payload with claims like `sub` (subject) and `exp` (expiry). The client includes it as `Authorization: Bearer <token>`.
- OAuth (Bungie): User authorizes the app; the server exchanges an authorization `code` for tokens and stores them (access/refresh).

Requests/Caching/Throttling
- `requests.Session` keeps headers and connection pooling. Use a single session per client.
- Bungie throttling: Honor `Retry-After` header and check `X-RateLimit-Remaining`. Back off and retry POSTs on transient errors.
- Caching: Keep manifest and profile responses in memory briefly to reduce load.

React Essentials
- State: `useState` holds UI state; `useEffect` runs side effects; `useCallback` memoizes functions.
- Props: Data flows down from `App` to components like `ChatWindow` and `Sidebar`.
- Streaming: Read a `ReadableStream` from `fetch()` and incrementally update state to render partial assistant output.

Frontend/Auth Pattern
- Popup OAuth: Open `/oauth/authorize`; upon redirect to `/oauth/callback`, the server responds with a small script that posts back the token and closes the popup.
- Storage: Save the token in `localStorage` so refresh persists log-in.

LLM Provider Routing
- Ollama: Local host and model name from env or UI (e.g., `ollama:llama3`).
- Grok: Cloud API with `XAI_API_KEY`.
- Persona: A “system prompt” shaping the assistant style, chosen in the UI.

Inventory Command Basics
- Regex matching: The assistant looks for verbs like transfer/equip and item/location phrases.
- Resolution: Uses Bungie membership + profile to find character/vault/postmaster and the item instance; then calls the corresponding action.

