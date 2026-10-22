"""FastAPI server exposing a chat endpoint for the desktop/web UI.

Minimal, robust server used by the desktop app. It serves the React build when
requested and provides basic health/auth routes so the UI can render. Expand as
needed by re‑adding richer endpoints.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests as _requests
import shutil as _shutil
import subprocess as _subprocess
import threading as _threading
import time as _time
from dotenv import load_dotenv
from server_db import (
    init_db,
    create_user,
    get_user_by_email,
    list_conversations,
    create_conversation,
    rename_conversation,
    update_conversation_provider,
    delete_conversation,
    get_conversation_messages,
    append_message,
    ensure_conversation,
    get_bungie_tokens,
    upsert_bungie_tokens,
)
from server_auth import create_jwt, get_user_from_token
from ghost.auth import exchange_code_for_token  # type: ignore
from ghost.assistant import BungieConfigError, GhostAssistant  # type: ignore
from ghost import personalities as _personas  # type: ignore
from ghost.voice import make_tts_provider, voice_id_for_persona  # type: ignore
from ghost.voice import make_stt_provider  # type: ignore
from ghost.voice import Pyttsx3TTS, diagnose_audio, pcm16le_to_wav_bytes, Recorder  # type: ignore
from ghost.voice import HAVE_SD  # type: ignore
try:
    from ghost.voice import ElevenLabsTTS  # type: ignore
except Exception:  # optional dependency may be missing
    ElevenLabsTTS = None  # type: ignore


def get_repo_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


REPO_ROOT = get_repo_root()
load_dotenv(REPO_ROOT / ".env")

# Determine the frontend directory to serve. In development this is
# `frontend/build`. In packaged bundles, the build may be collected into
# `frontend/` directly. Support both to avoid mismatches.
_FE_CANDIDATES = [
    REPO_ROOT / "frontend" / "build",
]
if getattr(sys, "frozen", False):
    _FE_CANDIDATES.append(REPO_ROOT / "frontend")
FRONTEND_BUILD_DIR = None
for _cand in _FE_CANDIDATES:
    try:
        if (_cand / "index.html").exists():
            FRONTEND_BUILD_DIR = _cand
            break
    except Exception:
        pass
if FRONTEND_BUILD_DIR is None:
    # Fall back to the default dev path; mount is gated by SERVE_UI below
    FRONTEND_BUILD_DIR = REPO_ROOT / "frontend" / "build"

from ghost.providers import from_headers, ProviderError, RedactionFilter, request_secrets
from ghost.auth import generate_pkce, public_exchange, _safe_token_request
import secrets
from urllib.parse import urlencode

from contextlib import asynccontextmanager
from ghost.security import hosted, loopback, SecurityMiddleware

@asynccontextmanager
async def lifespan(app):
    if hosted() and (not os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET") == "dev-secret-change-me"):
        raise RuntimeError("Hosted mode requires a strong JWT_SECRET")
    init_db()
    if not hosted():
        _ensure_ollama_on_startup()
    try:
        yield
    finally:
        _oauth_attempts.clear()

app = FastAPI(lifespan=lifespan)
from ghost.local_secrets import router as local_router
app.include_router(local_router)
from fastapi.middleware.cors import CORSMiddleware
UI_ORIGINS = [v.strip() for v in (os.getenv("GHOST_UI_ORIGINS") or ("" if hosted() else "http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:5173,http://localhost:5173")).split(",") if v.strip()]
if hosted() and any("*" in origin for origin in UI_ORIGINS):
    raise RuntimeError("Hosted CORS requires explicit origins")
app.add_middleware(CORSMiddleware, allow_origins=UI_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Conversation-Id"])


@app.exception_handler(ProviderError)
async def provider_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})



@app.exception_handler(BungieConfigError)
async def bungie_config_error_handler(request: Request, exc: BungieConfigError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


# Logging
LOG_DIR = (Path.home() / ".ghost-companion" if getattr(sys, "frozen", False) else REPO_ROOT) / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / "server.log"
_file_handler = RotatingFileHandler(str(log_file), maxBytes=1_000_000, backupCount=3)
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, logging.StreamHandler()])
for handler in logging.getLogger().handlers:
    handler.addFilter(RedactionFilter())
logger = logging.getLogger("ghost")
logger.info("Server started; logging to %s", log_file)

# -------------------- Ollama auto-start helpers --------------------

def _ollama_host() -> str:
    return (os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")


def _ollama_up() -> bool:
    try:
        r = _requests.get(f"{_ollama_host()}/api/tags", timeout=1.5)
        return r.status_code < 500
    except Exception:
        return False


def _start_ollama_background() -> None:
    if _shutil.which("ollama") is None:
        logger.info("Ollama CLI not found; skipping auto-start")
        return
    try:
        logger.info("Starting 'ollama serve' in background...")
        # Start detached to avoid tying lifecycle to this process
        creationflags = 0
        if os.name == "nt":
            creationflags = 0x00000008  # CREATE_NEW_PROCESS_GROUP
        _subprocess.Popen(
            ["ollama", "serve"],
            stdout=_subprocess.DEVNULL,
            stderr=_subprocess.DEVNULL,
            stdin=_subprocess.DEVNULL,
            creationflags=creationflags,
            shell=True,
        )
    except Exception:
        logger.exception("Failed to start ollama serve")


def _maybe_pull_model_async(model: str) -> None:
    if not model:
        return
    if _shutil.which("ollama") is None:
        return
    def _worker():
        try:
            logger.info("Ensuring Ollama model '%s' is available (pulling if needed)...", model)
            _subprocess.run(["ollama", "pull", model], check=False, shell=True)
        except Exception:
            logger.exception("Ollama pull failed")
    t = _threading.Thread(target=_worker, daemon=True)
    t.start()


def _ensure_ollama_on_startup() -> None:
    # If Ollama is configured via env but not responding, try to start it
    if os.getenv("OLLAMA_MODEL") and not _ollama_up():
        _start_ollama_background()
        # Give it a brief moment to come up
        for _ in range(10):
            if _ollama_up():
                break
            _time.sleep(0.5)
        # Opportunistic pull of the configured model in background
        _maybe_pull_model_async(os.getenv("OLLAMA_MODEL", ""))


@app.middleware("http")
async def log_requests(request, call_next):
    marker = request_secrets.set(tuple(v for v in (request.headers.get("x-ai-key"), request.headers.get("x-bungie-api-key"), os.getenv("BUNGIE_CLIENT_SECRET")) if v))
    try:
        logger.info("Request: %s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info("Response: %s", response.status_code)
        return response
    finally:
        request_secrets.reset(marker)



# Decide whether to serve the built UI (mounted at end)
SERVE_UI = (FRONTEND_BUILD_DIR / "index.html").exists()


class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    session_id: Optional[str] = None


class LocalSttRequest(BaseModel):
    duration: float | None = 6.0
    device_index: int | None = None


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "ui": bool(SERVE_UI),
        **({} if hosted() else {"log": str(log_file)}),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/auth/status")
def auth_status(authorization: str | None = Header(None), x_bungie_api_key: str | None = Header(None)) -> dict[str, object]:
    user = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            user = get_user_from_token(token)
        except Exception:
            user = None
    api_key = os.getenv("BUNGIE_API_KEY") or x_bungie_api_key or ""
    masked = "configured" if api_key else ""
    linked = False
    if user:
        try:
            toks = get_bungie_tokens(int(user["id"]))
            if toks and toks.get("access_token"):
                # Consider linked if we have at least an access token and it's not obviously expired
                exp = float(toks.get("access_token_expires") or 0)
                linked = (exp == 0) or (exp > __import__('time').time() - 30)
        except Exception:
            linked = False
    return {
        "authenticated": bool(user),
        "bungie_linked": bool(linked),
        "api_key_ok": bool(api_key),
        "api_key_masked": masked,
    }


class KeyPayload(BaseModel):
    api_key: str


@app.post("/auth/key")
def set_api_key(payload: KeyPayload):
    raise HTTPException(410, "Use device Settings and X-Bungie-API-Key instead")


def _callback_url(request: Request, force_http: bool | None = None) -> str:
    try:
        url = str(request.url_for("oauth_callback"))
    except Exception:
        # Fallback: build from host header
        host = request.headers.get("host", "127.0.0.1:8765")
        url = f"http://{host}/oauth/callback"
    # Decide forcing http: if caller passed flag, use it; otherwise infer from SSL env
    if force_http is None:
        force_http = not (os.getenv("SSL_CERTFILE") and os.getenv("SSL_KEYFILE"))
    if force_http:
        # Ensure scheme is http for loopback (Qt WebEngine can block self-signed TLS)
        try:
            from urllib.parse import urlparse, urlunparse
            p = urlparse(url)
            if p.scheme != "http":
                url = urlunparse(p._replace(scheme="http"))
        except Exception:
            pass
    return url


# Short-lived, one-use OAuth attempts contain no API keys.
_oauth_attempts = {}

@app.get("/oauth/authorize")
@app.get("/user/oauth/authorize")
def oauth_authorize(request: Request):
    cid = os.getenv("BUNGIE_CLIENT_ID") or request.headers.get("x-bungie-client-id")
    if not cid:
        raise HTTPException(404, "OAuth client ID not configured")
    verifier, challenge = generate_pkce()
    state = secrets.token_urlsafe(32)
    now = _time.time()
    for old, attempt in list(_oauth_attempts.items()):
        if attempt[3] < now:
            _oauth_attempts.pop(old, None)
    if len(_oauth_attempts) >= 10000:
        raise HTTPException(429, "Too many pending OAuth attempts")
    native = request.query_params.get("redirect_uri") == "ghostcompanion://oauth/callback"
    if request.query_params.get("redirect_uri") and not native:
        raise HTTPException(400, "Unrecognized OAuth redirect")
    redirect = "ghostcompanion://oauth/callback" if native else (os.getenv("BUNGIE_REDIRECT_URI") or str(request.url_for("oauth_callback")))
    origin = request.headers.get("origin") or str(request.base_url).rstrip("/")
    if origin not in UI_ORIGINS and origin != str(request.base_url).rstrip("/"):
        raise HTTPException(400, "Unrecognized UI origin")
    if native and (origin != "capacitor://localhost" or origin not in UI_ORIGINS):
        raise HTTPException(400, "Native OAuth requires configured Capacitor origin")
    native_session = secrets.token_urlsafe(32) if native else None
    _oauth_attempts[state] = (verifier, cid, redirect, now + 600, origin, native_session)
    url = "https://www.bungie.net/en/OAuth/Authorize?" + urlencode(dict(client_id=cid, response_type="code", redirect_uri=redirect, state=state, code_challenge=challenge, code_challenge_method="S256"))
    response = JSONResponse({"authorization_url": url, "redirect_uri": redirect, **({"native_session": native_session} if native else {})})
    response.set_cookie("ghost_oauth_state", state, httponly=True, secure=request.url.scheme == "https", samesite="lax", max_age=600)
    return response

@app.get("/oauth/callback")
def oauth_callback(code: str | None = None, state: str | None = None):
    # Values are escaped as JSON, including '<' to prevent script injection.
    payload = json_dumps(dict(type="bungie_oauth", code=code or "", state=state or "")).replace("<", "\\u003c")
    attempt = _oauth_attempts.get(state)
    origin = json_dumps(attempt[4] if attempt else "")
    html = "<!doctype html><title>Ghost Companion</title><script>const p=" + payload + ";if(window.opener){window.opener.postMessage(p," + origin + ");window.addEventListener('message',function(e){if(e.source===window.opener && e.origin===" + origin + " && e.data.type==='oauth_complete'){window.close();}});}else{document.body.textContent='Return to Ghost Companion and try signing in again.'}</script>"
    import hashlib, base64
    script = html.split('<script>', 1)[1].split('</script>', 1)[0]
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    return HTMLResponse(html, headers={"Content-Security-Policy": f"default-src 'self'; script-src 'sha256-{digest}'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"})

def _consume_oauth(request, payload):
    state = str(payload.get("state") or "")
    cookie = request.cookies.get("ghost_oauth_state", "")
    attempt = _oauth_attempts.get(state)
    native_session = attempt[5] if attempt and len(attempt) > 5 else None
    if native_session:
        valid = request.headers.get("origin") == attempt[4] and secrets.compare_digest(native_session, str(payload.get("native_session") or ""))
    else:
        valid = bool(state) and secrets.compare_digest(state, cookie)
    if not valid:
        raise HTTPException(400, "OAuth state mismatch")
    attempt = _oauth_attempts.pop(state, None)
    if not attempt or attempt[3] < _time.time():
        raise HTTPException(400, "OAuth state expired or already used")
    attempt = attempt[:5]
    return attempt

def _proxy_secret():
    secret = os.getenv("BUNGIE_CLIENT_SECRET")
    if os.getenv("GHOST_BUNGIE_TOKEN_PROXY") != "1" or not secret:
        raise HTTPException(404, "Token proxy disabled")
    return secret

@app.post("/oauth/callback")
def oauth_callback_post(request: Request, payload: dict):
    verifier, cid, redirect, expiry, _ = _consume_oauth(request, payload)
    secret = _proxy_secret() if os.getenv("GHOST_BUNGIE_TOKEN_PROXY") == "1" else None
    try:
        tok = public_exchange(cid, str(payload.get("code") or ""), verifier, secret)
    except ValueError:
        raise HTTPException(400, "Bungie token exchange failed") from None
    if hosted():
        membership = tok.get("membership_id")
        if not membership:
            raise HTTPException(400, "Bungie membership ID missing")
        email = f"bungie:{membership}"
    else:
        email = "desktop@local"
    row = get_user_by_email(email)
    if not row:
        create_user(email, "local")
        row = get_user_by_email(email)
    uid = int(row["id"])
    upsert_bungie_tokens(uid, {"access_token": tok.get("access_token", ""), "refresh_token": tok.get("refresh_token", ""), "membership_id": tok.get("membership_id"), "membership_type": None, "access_token_expires": _time.time() + int(tok.get("expires_in", 0))})
    return {"ok": True, "token": create_jwt(uid, email), "bungie_linked": True}

@app.post("/oauth/token")
def oauth_token(request: Request, payload: dict):
    secret = _proxy_secret()
    verifier, cid, _, _, _ = _consume_oauth(request, payload)
    try:
        return public_exchange(cid, str(payload.get("code") or ""), verifier, secret)
    except ValueError:
        raise HTTPException(400, "Bungie token exchange failed") from None

@app.post("/oauth/refresh")
def oauth_refresh(payload: dict):
    secret = _proxy_secret()
    cid = os.getenv("BUNGIE_CLIENT_ID")
    if not cid:
        raise HTTPException(503, "OAuth client ID not configured")
    try:
        return _safe_token_request(dict(grant_type="refresh_token", client_id=cid, client_secret=secret, refresh_token=str(payload.get("refresh_token") or "")))
    except ValueError:
        raise HTTPException(400, "Bungie token exchange failed") from None


# Legacy alias
@app.get("/user/oauth/callback")
def user_oauth_callback(code: str | None = None, state: str | None = None) -> HTMLResponse:
    return oauth_callback(code, state)


if not SERVE_UI:
    @app.get("/")
    def root() -> dict[str, str]:
        return {"detail": "Send POST /chat with {'message': ...}"}


# Mount static last so API routes like /auth/* remain reachable
## (static mount moved to end of file so API routes remain reachable)


# --------- helpers ---------
def json_dumps(obj) -> str:
    import json as _json
    return _json.dumps(obj, separators=(",", ":"))


# -------------------- Conversations + Chat API --------------------
def _require_user(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


class ConversationCreate(BaseModel):
    name: str
    provider: str | None = None


@app.get("/conversations")
def api_list_conversations(authorization: str | None = Header(None)) -> dict[str, object]:
    user = _require_user(authorization)
    items = list_conversations(int(user["id"]))
    return {"conversations": items}


@app.post("/conversations")
def api_create_conversation(payload: ConversationCreate, authorization: str | None = Header(None)) -> dict[str, str]:
    user = _require_user(authorization)
    cid = create_conversation(int(user["id"]), payload.name or "New Chat", payload.provider)
    return {"id": cid}


class ConversationPatch(BaseModel):
    name: str | None = None
    provider: str | None = None


@app.patch("/conversations/{conversation_id}")
def api_patch_conversation(conversation_id: str, payload: ConversationPatch, authorization: str | None = Header(None)) -> dict[str, object]:
    user = _require_user(authorization)
    if payload.name:
        rename_conversation(conversation_id, int(user["id"]), payload.name)
    if payload.provider is not None:
        update_conversation_provider(conversation_id, int(user["id"]), payload.provider)
    return {"ok": True}


@app.delete("/conversations/{conversation_id}")
def api_delete_conversation(conversation_id: str, authorization: str | None = Header(None)) -> dict[str, object]:
    user = _require_user(authorization)
    delete_conversation(conversation_id, int(user["id"]))
    return {"ok": True}


@app.get("/conversations/{conversation_id}")
def api_get_conversation(conversation_id: str, authorization: str | None = Header(None)) -> dict[str, object]:
    user = _require_user(authorization)
    msgs = get_conversation_messages(conversation_id, int(user["id"]))
    return {"messages": msgs}


@app.get("/chat/stream")
def api_chat_stream(
    request: Request,
    message: str,
    provider: str | None = None,
    session_id: str | None = None,
    model: str | None = None,
    persona: str | None = None,
    speak: bool | None = False,
    voice: str | None = None,
    authorization: str | None = Header(None),
):
    if hosted() and speak:
        raise HTTPException(403, "Server audio is disabled in hosted mode")
    user = _require_user(authorization)
    uid = int(user["id"])  # type: ignore[index]
    conv_id = session_id or f"conv-{__import__('uuid').uuid4().hex}"
    # If provider is Ollama and a model is provided, persist as "ollama:<model>"
    provider_key = request.headers.get("x-ai-provider", "ollama").lower()
    model = request.headers.get("x-ai-model") or model
    if provider_key == "ollama" and model:
        provider_key = f"ollama:{model}"
    try:
        ensure_conversation(conv_id, uid, name="Chat", provider=provider_key or provider)
    except PermissionError:
        raise HTTPException(403, "Conversation belongs to another user") from None

    # Persist user message
    append_message(conv_id, f"msg-{__import__('uuid').uuid4().hex}", "user", message)

    # Resolve before sending headers so configuration errors become HTTP errors.
    try:
        tokens = get_bungie_tokens(uid) or None
        local_assistant = GhostAssistant(api_key=os.getenv("BUNGIE_API_KEY") or request.headers.get("x-bungie-api-key"))
        client = from_headers(request.headers)
        local_assistant._clients["request"] = client
        reply = local_assistant.chat(message, provider="request", tokens=tokens, persona=persona)
    except (BungieConfigError, ProviderError):
        raise
    except Exception as e:
        logger.exception("Assistant failure; replying with fallback: %s", e)
        reply = (
            "Hi Guardian. The model provider isn't configured (e.g., OLLAMA_MODEL). "
            "I can still chat lightly."
        )

    def _gen():
        # Stream in chunks
        chunk = 200
        sent = 0
        while sent < len(reply):
            yield reply[sent : sent + chunk]
            sent += chunk
        # Save assistant message after streaming out
        try:
            append_message(conv_id, f"msg-{__import__('uuid').uuid4().hex}", "assistant", reply)
        except Exception:
            pass
        # Optional: speak the reply using TTS on the backend (desktop)
        try:
            if speak:
                tts = None
                vid_override = None
                if voice:
                    if voice == "system":
                        tts = Pyttsx3TTS()
                    elif voice.startswith("eleven:") and ElevenLabsTTS is not None:
                        vid_override = voice.split(":", 1)[1]
                        tts = ElevenLabsTTS()
                if tts is None:
                    tts = make_tts_provider()
                vid = vid_override or voice_id_for_persona(persona)
                tts.speak(reply, voice_id=vid)
        except Exception:
            # Non-fatal if TTS is not configured
            pass

    headers = {"X-Conversation-Id": conv_id}
    return StreamingResponse(_gen(), media_type="text/plain", headers=headers)


@app.post("/ai/test")
def ai_test(request: Request):
    try:
        from_headers(request.headers).chat([{"role": "user", "content": "Reply OK"}], max_tokens=8)
        return {"ok": True}
    except ProviderError as exc:
        return {"ok": False, "error": str(exc)}

@app.post("/chat")
def api_chat(payload: ChatRequest, request: Request, authorization: str | None = Header(None)):
    user = _require_user(authorization)
    local = GhostAssistant(api_key=os.getenv("BUNGIE_API_KEY") or request.headers.get("x-bungie-api-key"))
    local._clients["request"] = from_headers(request.headers)
    reply = local.chat(payload.message, provider="request", tokens=get_bungie_tokens(int(user["id"])))
    return {"reply": reply}


@app.get("/models")
def list_models() -> dict[str, object]:
    """Return available model options for providers.

    Currently supports:
    - Ollama: queries ``/api/tags`` and returns tag names.
    """
    result: dict[str, object] = {"ollama": []}
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    try:
        r = _requests.get(f"{host}/api/tags", timeout=2)
        if r.status_code == 200:
            data = r.json() or {}
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            result["ollama"] = models
    except Exception:
        # Leave empty if not reachable
        pass
    return result


@app.get("/personas")
def list_personas() -> dict[str, object]:
    try:
        return {"personas": _personas.list_personalities()}
    except Exception:
        return {"personas": ["destiny_ghost"]}


def _persona_voice_map() -> dict[str, list[str]]:
    """Return mapping of Eleven voice keys to personas that prefer them."""
    personas: list[str]
    try:
        personas = _personas.list_personalities()
    except Exception:
        personas = []
    mapping: dict[str, list[str]] = {}
    for persona in personas:
        try:
            vid = voice_id_for_persona(persona)
        except Exception:
            vid = None
        if vid:
            key = f"eleven:{vid}"
            mapping.setdefault(key, []).append(persona)
    return mapping


@app.get("/voices")
def list_voices() -> dict[str, object]:
    persona_voice_map = _persona_voice_map()
    items: list[dict[str, object]] = []
    items.append({"key": "system", "name": "System (device TTS)", "provider": "pyttsx3"})
    env_map = {
        "Vergil": os.getenv("ELEVEN_VOICE_ID_VERGIL", ""),
        "Ghost": os.getenv("ELEVEN_VOICE_ID_GHOST", ""),
        "Cortana": os.getenv("ELEVEN_VOICE_ID_CORTANA", ""),
    }
    for label, vid in env_map.items():
        if not vid:
            continue
        key = f"eleven:{vid}"
        item: dict[str, object] = {"key": key, "name": f"{label} (ElevenLabs)", "provider": "elevenlabs"}
        personas = persona_voice_map.get(key)
        if personas:
            item["personas"] = personas
        items.append(item)
    # Only include curated voices by default to avoid clutter.
    # Set ELEVEN_LIST_ALL=1 to include all ElevenLabs voices from the account.
    if os.getenv("ELEVEN_LIST_ALL", "").lower() in {"1", "true", "yes"}:
        api_key = os.getenv("ELEVEN_API_KEY", "")
        if api_key:
            try:
                r = _requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": api_key}, timeout=5)
                if r.status_code == 200:
                    data = r.json() or {}
                    for v in data.get("voices", []) or []:
                        vid = v.get("voice_id")
                        name = v.get("name")
                        if vid and name:
                            key = f"eleven:{vid}"
                            item = {"key": key, "name": f"{name} (ElevenLabs)", "provider": "elevenlabs"}
                            personas = persona_voice_map.get(key)
                            if personas:
                                item["personas"] = personas
                            items.append(item)
            except Exception:
                pass
    seen = set()
    out: list[dict[str, object]] = []
    for it in items:
        if it["key"] in seen:
            continue
        seen.add(it["key"])
        out.append(it)
    return {"voices": out}


@app.post("/stt")
async def stt_endpoint(request: Request):
    """Accept an uploaded WAV file and return transcription.

    Frontend sends multipart/form-data with field 'file'.
    """
    form = await request.form()
    file = form.get("file")
    if not file:
        raise HTTPException(status_code=400, detail="Missing file")
    try:
        content = await file.read()  # type: ignore[attr-defined]
    except Exception:
        # Some Starlette uploads expose .file instead
        f = getattr(file, "file", None)
        if f is None:
            raise HTTPException(status_code=400, detail="Invalid upload")
        content = f.read()
    try:
        stt = make_stt_provider()
        text = stt.transcribe(content)
        return JSONResponse({"text": text})
    except Exception as e:
        logger.exception("STT failed: %s", e)
        # Provide a more descriptive error to the caller for diagnostics
        hint = "Transcription failed"
        if not os.getenv("OPENAI_API_KEY"):
            hint += "; missing OPENAI_API_KEY or local faster-whisper"
        raise HTTPException(status_code=500, detail=hint)


@app.get("/stt/health")
def stt_health() -> dict[str, object]:
    """Report STT configuration and likely issues to aid debugging."""
    info: dict[str, object] = {
        "openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "provider": None,
        "ok": False,
        "error": None,
    }
    try:
        prov = make_stt_provider()
        info["provider"] = type(prov).__name__
        # Simple sanity: transcribe an empty wav to ensure call path is usable
        import wave, io
        bio = io.BytesIO()
        with wave.open(bio, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"")
        _ = prov.transcribe(bio.getvalue())
        info["ok"] = True
    except Exception as e:
        info["error"] = str(e)
    return info


def _normalize_sd_device(device: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in device.items():
        if isinstance(value, (int, float, str)) or value is None:
            normalized[key] = value
            continue
        try:
            normalized[key] = float(value)  # numpy scalars, etc.
        except Exception:
            normalized[key] = str(value)
    return normalized


@app.get("/diagnostics/audio")
def audio_diagnostics() -> dict[str, object]:
    """Return structured audio diagnostics for mic/STT troubleshooting."""
    payload: dict[str, object] = {
        "report": diagnose_audio().splitlines(),
        "openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "stt_provider": os.getenv("STT_PROVIDER", "auto"),
        "secure_context_hint": bool(os.getenv("SSL_CERTFILE") and os.getenv("SSL_KEYFILE")),
    }
    if HAVE_SD:
        try:
            import sounddevice as _sd  # type: ignore

            devices = _sd.query_devices()
            payload["devices"] = [_normalize_sd_device(dev) for dev in devices]
            try:
                default_in = getattr(_sd.default, "device", [None, None])[0]
            except Exception:
                default_in = None
            payload["default_input_device"] = default_in
        except Exception as exc:
            payload["devices_error"] = str(exc)
    else:
        payload["devices_error"] = "sounddevice module not available"
    return payload


@app.post("/stt/local")
def stt_local(payload: LocalSttRequest) -> dict[str, object]:
    """Record audio via the desktop host (PortAudio) and transcribe server-side."""
    if not HAVE_SD:
        raise HTTPException(status_code=500, detail="Local microphone capture unavailable on this host.")
    duration = payload.duration or 6.0
    duration = max(1.0, min(duration, 30.0))
    try:
        recorder = Recorder(sample_rate=16000, channels=1)
        chunk = recorder.record_blocking(duration, device=payload.device_index)
        wav_bytes = pcm16le_to_wav_bytes(chunk)
    except Exception as exc:
        logger.exception("Local recording failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Local recording failed: {exc}")
    try:
        stt = make_stt_provider()
        text = stt.transcribe(wav_bytes)
        return {"text": text}
    except Exception as exc:
        logger.exception("Local STT failed: %s", exc)
        raise HTTPException(status_code=500, detail="Transcription failed for local recording")


# Mount static last so API routes like /auth/* remain reachable
if SERVE_UI:
    if (FRONTEND_BUILD_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_BUILD_DIR / "assets")), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str):
        candidate = (FRONTEND_BUILD_DIR / path).resolve()
        if candidate.is_relative_to(FRONTEND_BUILD_DIR.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        if path.startswith(("local/", "api/", "oauth/", "auth/")):
            raise HTTPException(404)
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")

# Wrap CORS and all routes so preflight and rejected requests also receive headers.
app.add_middleware(SecurityMiddleware, allowed_origins=UI_ORIGINS)
