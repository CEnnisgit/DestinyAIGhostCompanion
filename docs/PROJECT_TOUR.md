Project Tour: Ghost Companion

Overview
- Purpose: A chat assistant for Destiny 2 that combines Bungie.net API data with an LLM (Ollama local model or xAI Grok) and optional voice (STT/TTS).
- Stack: FastAPI backend (Python) + React frontend (JS) + SQLite for simple server-side sessions and conversations.
- Key flows: OAuth to link Bungie account; chat streaming to/from the model; inventory actions via Bungie endpoints; optional speech.

Core Components
- Backend API (`server.py`)
  - Auth & OAuth: `/auth/status`, `/auth/key`, `/oauth/authorize`, `/oauth/callback`.
  - Chat: `/chat/stream` streams assistant tokens; stores conversations/messages if authenticated.
  - Data: `/models`, `/personas`, `/voices`; conversation CRUD routes; health check.
  - Startup: Boots logging, DB, and optionally starts/pulls Ollama models.
  - Uses `GhostAssistant` to route a user’s message to the chosen model provider and optionally to Bungie API.

- Assistant Orchestration (`ghost/assistant.py`)
  - Parses user intent (regex) for inventory/vault/postmaster actions and list queries.
  - Resolves model provider on each request (Ollama/Grok/finetune) and injects a system prompt (persona) before calling the model.
  - Holds a `BungieClient` instance; forwards OAuth tokens when provided; uses cached membership info.
  - Tracks last referenced item/location for follow-up commands (e.g., "move it to vault").

- Bungie API Client (`ghost/bungie.py`)
  - Thin wrapper around Bungie REST endpoints.
  - Handles auth headers, throttling via Retry-After, light caching for manifest/profile, and retries for POSTs.
  - Exposes item transfer/equip, loadouts, vendors, stats, and helper manifest lookups.

- Model Clients
  - `ghost/ollama.py`: Local model via `OLLAMA_HOST` and `OLLAMA_MODEL`, `/api/generate` non-streaming.
  - `ghost/grok.py`: xAI’s Grok via `XAI_API_KEY` and `chat/completions`.
  - `ghost/finetune.py`: Local wrapper stub for a fine-tuned model (used as fallback).

- Voice (`ghost/voice.py`)
  - STT providers: OpenAI Whisper API or local faster-whisper.
  - TTS providers: ElevenLabs or offline `pyttsx3`.
  - Small helpers for recording and WAV encoding; persona-to-voice mapping.

- Server DB/Auth
  - `server_db.py`: SQLite tables for users, Bungie tokens, conversations, and messages. Simple helpers for CRUD.
  - `server_auth.py`: JWT helpers, password hashing (bcrypt), and token decode/lookup.

- Frontend (`frontend/`)
  - React SPA.
  - `App.js` wires UI together: state for messages, auth/token, provider/persona/voices; handlers for OAuth popup, chat streaming, and conversation operations.
  - Components under `src/components` handle chat window, input box, sidebar, etc.

Typical Request Flow
1) User clicks "Sign in with Bungie":
   - Frontend calls `/oauth/authorize`, opens returned URL in a popup.
   - Bungie redirects to `/oauth/callback?code=...`; server exchanges `code` for tokens, returns a JWT, and frontend stores it.
2) User sends a chat message:
   - Frontend calls `/chat/stream?message=...&provider=...&persona=...` with `Authorization: Bearer <jwt>`.
   - Backend resolves model provider and persona, optionally queries Bungie for inventory/membership, and streams the model’s response while logging/storing conversation messages.
3) Inventory actions:
   - If the message matches a transfer/equip/list regex, `GhostAssistant` calls `BungieClient` endpoints and returns a concise result; otherwise it queries the LLM.

Environment & Keys
- `.env` is loaded by `server.py` on startup. Important variables:
  - Bungie: `BUNGIE_API_KEY`, `BUNGIE_CLIENT_ID`, `BUNGIE_CLIENT_SECRET`.
  - Ollama: `OLLAMA_HOST`, `OLLAMA_MODEL`.
  - Grok: `XAI_API_KEY`.
  - STT/TTS: `OPENAI_API_KEY`, `ELEVEN_API_KEY`, `ELEVEN_VOICE_ID`.
  - Server: `JWT_SECRET`, `SERVE_FRONTEND=1` to serve the build.

Local Dev & Packaging
- Start: `python launch.py` to orchestrate backend and frontend.
- Backend dev: `uvicorn server:app --reload`.
- Frontend dev: `(cd frontend && npm start)`; use `REACT_APP_API_URL` when API is not on the same origin.
- Build EXE: `build_exe.bat` and Inno Setup installer under `installer/`.

Reading the Code
- Start with `server.py` to see routes and streaming.
- Jump to `ghost/assistant.py` to understand how messages are interpreted.
- Reference `ghost/bungie.py` for concrete API calls.
- Skim `frontend/src/App.js` to see the UI state machine (auth, chat, conversations).

Glossary & Basics
- FastAPI Router: Decorators like `@app.get('/path')` define endpoints; Pydantic models validate request bodies.
- StreamingResponse: Sends partial content as it’s generated; the frontend reads with a `ReadableStream` reader.
- JWT: Signed tokens with claims (subject, email, expiration) used for auth.
- SQLite: File-based DB; `server_db.py` centralizes schema and queries.
- React state: useState/useEffect/useCallback manage UI state and side effects.

