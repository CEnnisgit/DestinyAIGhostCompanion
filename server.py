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
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
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
from ghost.assistant import GhostAssistant  # type: ignore
from ghost import personalities as _personas  # type: ignore
from ghost.voice import make_tts_provider, voice_id_for_persona  # type: ignore
from ghost.voice import make_stt_provider  # type: ignore
from ghost.voice import Pyttsx3TTS  # type: ignore
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
    REPO_ROOT / "frontend",
]
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

app = FastAPI()

# Logging
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / "server.log"
_file_handler = RotatingFileHandler(str(log_file), maxBytes=1_000_000, backupCount=3)
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, logging.StreamHandler()])
logger = logging.getLogger("ghost")
logger.info("Server started; logging to %s", log_file)

# Ensure DB exists for token-backed sessions
try:
    init_db()
except Exception:
    logger.exception("DB init failed")

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


@app.on_event("startup")
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


# Single assistant instance (lazy model clients inside)
assistant = GhostAssistant()


@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


# Decide whether to serve the built UI (mounted at end)
SERVE_UI = bool(getattr(sys, "frozen", False) or os.getenv("SERVE_FRONTEND") == "1") and FRONTEND_BUILD_DIR.exists()


class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    session_id: Optional[str] = None


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "ui": bool(SERVE_UI),
        "log": str(log_file),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/auth/status")
def auth_status(authorization: str | None = Header(None)) -> dict[str, object]:
    user = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            user = get_user_from_token(token)
        except Exception:
            user = None
    api_key = os.getenv("BUNGIE_API_KEY", "")
    masked = (api_key[:4] + "*" * max(0, len(api_key) - 8) + api_key[-4:]) if api_key else ""
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
def set_api_key(payload: KeyPayload) -> dict[str, object]:
    key = (payload.api_key or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="Missing api_key")
    os.environ["BUNGIE_API_KEY"] = key
    # Best-effort update of .env if present
    try:
        env_path = REPO_ROOT / ".env"
        if env_path.exists():
            # naive replacement or append
            text = env_path.read_text(encoding="utf-8")
            lines = []
            found = False
            for line in text.splitlines():
                if line.startswith("BUNGIE_API_KEY="):
                    lines.append(f"BUNGIE_API_KEY={key}")
                    found = True
                else:
                    lines.append(line)
            if not found:
                lines.append(f"BUNGIE_API_KEY={key}")
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        pass
    return {"ok": True}


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


@app.get("/oauth/authorize")
def oauth_authorize(request: Request) -> dict[str, str]:
    client_id = os.getenv("BUNGIE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=404, detail="OAuth not configured")
    # Coerce to http unless local TLS is configured via env
    redirect_uri = _callback_url(request, force_http=None)
    base = "https://www.bungie.net/en/OAuth/Authorize"
    url = f"{base}?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}"
    return {"authorization_url": url, "redirect_uri": redirect_uri}


# Aliases for legacy paths used by the web UI
@app.get("/user/oauth/authorize")
def user_oauth_authorize(request: Request) -> dict[str, str]:
    return oauth_authorize(request)


@app.get("/oauth/callback")
def oauth_callback(code: str | None = None, state: str | None = None) -> HTMLResponse:
    """OAuth redirect landing page.

    - If opened as a popup (window.opener exists): postMessage the code and close.
    - If opened in the main window (no opener): directly exchange the code for a
      token via POST /oauth/callback, store it in localStorage, and redirect to '/'.
    """
    payload = {
        "type": "bungie_oauth",
        "ok": bool(code),
        "code": code or "",
        "state": state or "",
    }
    script = (
        "<!doctype html><html><head><meta charset=\"utf-8\"><title>Auth</title></head><body>"
        "<script>\n"
        "(function(){\n"
        "  var p = %s;\n"
        "  function closeSoon(){ try{ window.close(); }catch(_){} setTimeout(function(){ try{ window.close(); }catch(_){} }, 300); }\n"
        "  if (window.opener) {\n"
        "    try { window.opener.postMessage(p, '*'); } catch(e){}\n"
        "    if (p && p.code) {\n"
        "      try {\n"
        "        fetch('/oauth/callback', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({code: p.code})})\n"
        "          .then(function(r){ return r.json(); })\n"
        "          .then(function(data){ if (data && data.token) { try { localStorage.setItem('ghost-companion-token', JSON.stringify(data.token)); } catch(_){} } try { window.opener.postMessage({type:'oauth_complete'}, '*'); } catch(_){} closeSoon(); });\n"
        "      } catch (e) { closeSoon(); }\n"
        "      return;\n"
        "    }\n"
        "    closeSoon();\n"
        "    return;\n"
        "  }\n"
        "  // Fallback when this page took over the main window.\n"
        "  if (p && p.code) {\n"
        "    try {\n"
        "      fetch('/oauth/callback', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({code: p.code})})\n"
        "        .then(function(r){ return r.json(); })\n"
        "        .then(function(data){\n"
        "          if (data && data.token) {\n"
        "            try { localStorage.setItem('ghost-companion-token', JSON.stringify(data.token)); } catch(_){}\n"
        "            location.replace('/');\n"
        "          } else { document.body.innerHTML = '<p>Authentication failed. Please close this window.</p>'; }\n"
        "        })\n"
        "        .catch(function(){ document.body.innerHTML = '<p>Authentication failed. Please close this window.</p>'; });\n"
        "    } catch (e) { document.body.innerHTML = '<p>Authentication failed. Please close this window.</p>'; }\n"
        "  } else {\n"
        "    document.body.innerHTML = '<p>Missing authorization code. You can close this window.</p>';\n"
        "  }\n"
        "})();\n"
        "</script>"
        "<p>You can close this window.</p>"
        "</body></html>"
    ) % (json_dumps(payload))
    return HTMLResponse(content=script, status_code=200)


@app.post("/oauth/callback")
def oauth_callback_post(payload: dict | None = None):
    # Extract code
    code = ""
    try:
        if isinstance(payload, dict):
            code = str(payload.get("code") or "")
    except Exception:
        code = ""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Ensure a local app user exists
    email = "desktop@local"
    row = get_user_by_email(email)
    if not row:
        try:
            _uid = create_user(email, "local")
            row = get_user_by_email(email)
        except Exception:
            row = get_user_by_email(email)
    uid = int(row["id"]) if row else 1

    # Exchange the code for Bungie tokens
    cid = os.getenv("BUNGIE_CLIENT_ID")
    csecret = os.getenv("BUNGIE_CLIENT_SECRET")
    if not cid or not csecret:
        logger.warning("Bungie OAuth creds missing; issuing local token only")
        token = create_jwt(uid, email)
        return {"ok": True, "token": token, "bungie_linked": False}

    try:
        tok = exchange_code_for_token(cid, csecret, code)
    except Exception as e:
        logger.exception("OAuth token exchange failed: %s", e)
        raise HTTPException(status_code=400, detail="Token exchange failed")

    # Persist tokens
    try:
        access = str(tok.get("access_token") or "")
        refresh = str(tok.get("refresh_token") or "")
        membership_id = str(tok.get("membership_id") or "")
        expires_in = int(tok.get("expires_in") or 0)
        access_exp = __import__('time').time() + max(0, expires_in)
        upsert_bungie_tokens(
            uid,
            {
                "access_token": access,
                "refresh_token": refresh,
                "membership_id": membership_id,
                "membership_type": None,
                "access_token_expires": access_exp,
            },
        )
        # Optionally resolve membership type
        try:
            api_key = os.getenv("BUNGIE_API_KEY", "")
            if api_key and access:
                from ghost.bungie import BungieClient  # type: ignore

                bc = BungieClient(api_key, access_token=access)
                mresp = bc.get_memberships_for_current_user()
                dms = (mresp or {}).get("Response", {}).get("destinyMemberships", []) or []
                if dms:
                    m = dms[0]
                    upsert_bungie_tokens(
                        uid,
                        {
                            "access_token": access,
                            "refresh_token": refresh,
                            "membership_id": m.get("membershipId"),
                            "membership_type": m.get("membershipType"),
                            "access_token_expires": access_exp,
                        },
                    )
        except Exception:
            pass
    except Exception:
        logger.exception("Failed to persist Bungie tokens")

    token = create_jwt(uid, email)
    return {"ok": True, "token": token, "bungie_linked": True}


# Legacy alias
@app.get("/user/oauth/callback")
def user_oauth_callback(code: str | None = None, state: str | None = None) -> HTMLResponse:
    return oauth_callback(code, state)


if not SERVE_UI:
    @app.get("/")
    def root_fallback() -> dict[str, str]:
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
    user = _require_user(authorization)
    uid = int(user["id"])  # type: ignore[index]
    conv_id = session_id or f"conv-{__import__('uuid').uuid4().hex}"
    # If provider is Ollama and a model is provided, persist as "ollama:<model>"
    provider_key = (provider or "").lower()
    if provider_key == "ollama" and model:
        provider_key = f"ollama:{model}"
    ensure_conversation(conv_id, uid, name="Chat", provider=provider_key or provider)

    # Persist user message
    append_message(conv_id, f"msg-{__import__('uuid').uuid4().hex}", "user", message)

    def _gen():
        # Try real assistant; if model not configured, fall back to a simple reply.
        try:
            tokens = get_bungie_tokens(uid) or None
            reply = assistant.chat(message, provider=provider_key or provider, tokens=tokens, persona=persona)
        except Exception as e:  # model missing, etc.
            logger.exception("Assistant failure; replying with fallback: %s", e)
            reply = (
                "Hi Guardian. The model provider isn't configured (e.g., OLLAMA_MODEL). "
                "I can still chat lightly."
            )
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


@app.get("/voices")
def list_voices() -> dict[str, object]:
    items: list[dict[str, str]] = []
    items.append({"key": "system", "name": "System (device TTS)", "provider": "pyttsx3"})
    env_map = {
        "Vergil": os.getenv("ELEVEN_VOICE_ID_VERGIL", ""),
        "Ghost": os.getenv("ELEVEN_VOICE_ID_GHOST", ""),
        "Cortana": os.getenv("ELEVEN_VOICE_ID_CORTANA", ""),
    }
    for label, vid in env_map.items():
        if vid:
            items.append({"key": f"eleven:{vid}", "name": f"{label} (ElevenLabs)", "provider": "elevenlabs"})
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
                            items.append({"key": f"eleven:{vid}", "name": f"{name} (ElevenLabs)", "provider": "elevenlabs"})
            except Exception:
                pass
    seen = set()
    out: list[dict[str, str]] = []
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


# Mount static last so API routes like /auth/* remain reachable
if SERVE_UI:
    app.mount("/", StaticFiles(directory=str(FRONTEND_BUILD_DIR), html=True), name="static")
