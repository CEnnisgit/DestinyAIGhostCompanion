"""FastAPI server exposing a chat endpoint for the desktop/web UI.

Minimal, robust server used by the desktop app. It serves the React build when
requested and provides basic health/auth routes so the UI can render. Expand as
needed by re‑adding richer endpoints.
"""

from __future__ import annotations

import os
import sys
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Any

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, StreamingResponse
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
from ghost.bungie import BungieClient  # type: ignore
from ghost import personalities as _personas  # type: ignore
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


def build_assistant() -> GhostAssistant:
    api_key = os.getenv("BUNGIE_API_KEY", "").strip() or "_unset_"
    return GhostAssistant(bungie_client=BungieClient(api_key))


# Single assistant instance (lazy model clients inside)
assistant = build_assistant()


@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


# Decide whether to serve the built UI (mounted at end)
SERVE_UI = FRONTEND_BUILD_DIR.exists()


class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    session_id: Optional[str] = None


class CommandParseRequest(BaseModel):
    text: str


class CommandResolveRequest(BaseModel):
    text: str | None = None
    intent: str | None = None
    item_query: str | None = None
    target: str | None = None


class CommandExecuteRequest(BaseModel):
    confirmation_token: str


class InventoryActionPreviewRequest(BaseModel):
    action: str
    item_instance_id: str
    target_character_id: str | None = None


class VoiceSessionRequest(BaseModel):
    mode: str | None = None


class VoiceTurnRequest(BaseModel):
    text: str
    session_id: str | None = None


_COMMAND_CONFIRMATIONS: dict[str, dict[str, Any]] = {}
_ACTION_AUDIT: dict[str, dict[str, Any]] = {}
_VOICE_STATE: dict[str, dict[str, Any]] = {}
_COMMAND_CONFIRM_TTL_SECONDS = 180


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "status": "ok",
        "ui": bool(SERVE_UI),
        "log": str(log_file),
        "ts": datetime.now(timezone.utc).isoformat(),
        "ollama_host": os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3"),
    }


@app.get("/app", include_in_schema=False)
def app_shell():
    if (FRONTEND_BUILD_DIR / "index.html").exists():
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")
    fallback = REPO_ROOT / "webapp" / "index.html"
    if fallback.exists():
        return FileResponse(fallback)
    raise HTTPException(status_code=404, detail="UI assets are missing")


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
    global assistant
    assistant = build_assistant()
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
    configured_redirect = (os.getenv("BUNGIE_REDIRECT_URI") or "").strip()
    if configured_redirect:
        return configured_redirect

    public_app_url = (os.getenv("PUBLIC_APP_URL") or "").strip().rstrip("/")
    if public_app_url:
        return f"{public_app_url}/oauth/callback"

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


def _mobile_callback_url(request: Request) -> str:
    public_app_url = (os.getenv("PUBLIC_APP_URL") or "").strip().rstrip("/")
    if public_app_url:
        return f"{public_app_url}/oauth/mobile/callback"
    try:
        return str(request.url_for("oauth_mobile_callback"))
    except Exception:
        host = request.headers.get("host", "127.0.0.1:8000")
        return f"http://{host}/oauth/mobile/callback"


def _mobile_callback_scheme(raw_scheme: str | None) -> str:
    scheme = (raw_scheme or "").strip()
    if not scheme:
        return "ghostcompanion"
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]{1,63}", scheme):
        return scheme
    return "ghostcompanion"


def _finish_oauth_exchange(code: str) -> dict[str, Any]:
    email = "desktop@local"
    row = get_user_by_email(email)
    if not row:
        try:
            create_user(email, "local")
            row = get_user_by_email(email)
        except Exception:
            row = get_user_by_email(email)
    uid = int(row["id"]) if row else 1

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
        try:
            api_key = os.getenv("BUNGIE_API_KEY", "")
            if api_key and access:
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


@app.get("/oauth/mobile/authorize")
def oauth_mobile_authorize(request: Request, callback_scheme: str | None = None) -> RedirectResponse:
    client_id = os.getenv("BUNGIE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=404, detail="OAuth not configured")
    redirect_uri = _mobile_callback_url(request)
    scheme = _mobile_callback_scheme(callback_scheme)
    base = "https://www.bungie.net/en/OAuth/Authorize"
    url = f"{base}?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&state=mobile:{scheme}"
    return RedirectResponse(url=url, status_code=307)


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


@app.get("/oauth/mobile/callback")
def oauth_mobile_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
) -> RedirectResponse:
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    scheme = "ghostcompanion"
    if state and state.startswith("mobile:"):
        scheme = _mobile_callback_scheme(state.split(":", 1)[1])
    result = _finish_oauth_exchange(code)
    token = str(result.get("token") or "")
    linked = "1" if result.get("bungie_linked") else "0"
    redirect_target = f"{scheme}://auth?token={token}&bungie_linked={linked}"
    logger.info(
        "Completed mobile OAuth callback for host=%s scheme=%s linked=%s",
        request.headers.get("host", ""),
        scheme,
        linked,
    )
    return RedirectResponse(url=redirect_target, status_code=307)


# Legacy alias
@app.get("/user/oauth/callback")
def user_oauth_callback(code: str | None = None, state: str | None = None) -> HTMLResponse:
    return oauth_callback(code, state)


@app.get("/")
def root():
    if SERVE_UI:
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")
    fallback = REPO_ROOT / "webapp" / "index.html"
    if fallback.exists():
        return FileResponse(fallback)
    return {"detail": "Send GET /chat/stream or open /app for the UI."}


# Mount static last so API routes like /auth/* remain reachable
## (static mount moved to end of file so API routes remain reachable)


# --------- helpers ---------
def json_dumps(obj) -> str:
    import json as _json
    return _json.dumps(obj, separators=(",", ":"))


# -------------------- Command API helpers --------------------
def _cleanup_expired_confirmations() -> None:
    now = _time.time()
    stale = [k for k, v in _COMMAND_CONFIRMATIONS.items() if float(v.get("expires_at", 0)) < now]
    for k in stale:
        _COMMAND_CONFIRMATIONS.pop(k, None)
    stale_voice = [
        k for k, v in _VOICE_STATE.items()
        if float(v.get("expires_at", 0) or 0) and float(v.get("expires_at", 0)) < now
    ]
    for k in stale_voice:
        _VOICE_STATE.pop(k, None)


def _voice_state_key(uid: int, session_id: str | None) -> str:
    return f"{uid}:{(session_id or 'default').strip() or 'default'}"


def _ensure_voice_state(uid: int, session_id: str | None) -> dict[str, Any]:
    key = _voice_state_key(uid, session_id)
    state = _VOICE_STATE.setdefault(
        key,
        {
            "uid": uid,
            "session_id": session_id or "default",
            "active_character_id": None,
            "pending_confirmation_token": None,
            "pending_candidates": [],
            "pending_intent": None,
            "pending_target": None,
            "last_candidate": None,
            "last_intent": None,
            "expires_at": _time.time() + 1800,
        },
    )
    state["expires_at"] = _time.time() + 1800
    return state


def _class_target_to_type(target: str | None) -> int | None:
    cmap = {"titan": 0, "hunter": 1, "warlock": 2}
    if not target:
        return None
    return cmap.get(target.lower())


def _canonical_target(target: str | None) -> str | None:
    if not target:
        return None
    text = re.sub(r"\s+", " ", str(target).strip().lower())
    aliases = {
        "current": "me",
        "active": "me",
        "current character": "me",
        "active character": "me",
        "guardian": "me",
        "my guardian": "me",
    }
    return aliases.get(text, text)


def _parse_command_text(text: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {"intent": "unknown", "item_query": None, "target": None, "mode": "command"}
    lower = raw.lower().strip()

    if lower in {"yes", "yeah", "yep", "confirm", "do it", "go ahead", "run it"}:
        return {"intent": "confirm", "item_query": None, "target": None, "mode": "control"}
    if lower in {"no", "nope", "cancel", "never mind", "stop"}:
        return {"intent": "cancel", "item_query": None, "target": None, "mode": "control"}

    if state and state.get("pending_candidates"):
        ordinal_map = {
            "first": 0,
            "1": 0,
            "one": 0,
            "second": 1,
            "2": 1,
            "two": 1,
            "third": 2,
            "3": 2,
            "three": 2,
        }
        if lower in ordinal_map:
            return {"intent": "select_candidate", "selection": {"index": ordinal_map[lower]}, "mode": "control"}
        if "vault" in lower:
            return {"intent": "select_candidate", "selection": {"source": "vault"}, "mode": "control"}
        if "postmaster" in lower:
            return {"intent": "select_candidate", "selection": {"source": "postmaster"}, "mode": "control"}
        if "inventory" in lower:
            return {"intent": "select_candidate", "selection": {"source": "inventory"}, "mode": "control"}
        if "equipped" in lower:
            return {"intent": "select_candidate", "selection": {"source": "equipped"}, "mode": "control"}
        for klass in ("hunter", "warlock", "titan"):
            if klass in lower:
                return {"intent": "select_candidate", "selection": {"class_name": klass.title()}, "mode": "control"}

    m = re.search(r"\b(?:where\s+is|find|locate)\s+(?:my\s+|the\s+)?(.+)$", raw, re.IGNORECASE)
    if m:
        return {
            "intent": "find_item",
            "item_query": m.group(1).strip(),
            "target": None,
            "mode": "read",
        }

    if re.search(r"\b(?:what(?:'s| is)?\s+equipped|show|list)\b.*\bequipped\b", raw, re.IGNORECASE):
        target_match = re.search(r"\b(?:on|for)\s+(?:my\s+)?(hunter|warlock|titan|me)\b", raw, re.IGNORECASE)
        return {
            "intent": "list_equipped",
            "item_query": None,
            "target": _canonical_target((target_match.group(1) if target_match else "me")),
            "mode": "read",
        }

    if re.search(r"\b(?:show|list|what(?:'s| is) in)\b.*\bpost[-\s]?master\b", raw, re.IGNORECASE):
        target_match = re.search(r"\b(?:for|on)\s+(?:my\s+)?(hunter|warlock|titan|me)\b", raw, re.IGNORECASE)
        return {
            "intent": "list_postmaster",
            "item_query": None,
            "target": _canonical_target((target_match.group(1) if target_match else "me")),
            "mode": "read",
        }

    if re.search(r"\b(?:show|list)\b.*\b(?:inventory|gear|vault)\b", raw, re.IGNORECASE):
        section = "inventory"
        if re.search(r"\bvault\b", raw, re.IGNORECASE):
            section = "vault"
        target_match = re.search(r"\b(?:for|on)\s+(?:my\s+)?(hunter|warlock|titan|me)\b", raw, re.IGNORECASE)
        return {
            "intent": "list_inventory",
            "item_query": None,
            "target": _canonical_target((target_match.group(1) if target_match else "me")),
            "section": section,
            "mode": "read",
        }

    m = re.search(
        r"\b(?:can\s+you\s+)?(?:equip|put\s+on|use)\s+(?:my\s+)?(.+?)(?:\s+(?:on|to)\s+(?:my\s+)?(hunter|warlock|titan|me)s?)?$",
        raw,
        re.IGNORECASE,
    )
    if m:
        return {
            "intent": "equip",
            "item_query": m.group(1).strip(),
            "target": _canonical_target(m.group(2) or "me"),
            "mode": "command",
        }

    m = re.search(r"\bvault\s+(?:my\s+|the\s+)?(.+)$", raw, re.IGNORECASE)
    if m:
        return {"intent": "vault", "item_query": m.group(1).strip(), "target": None, "mode": "command"}

    m = re.search(
        r"\b(?:pull|get|transfer|move)\s+(?:my\s+)?(.+?)\s+from\s+my\s+post[-\s]?master\b",
        raw,
        re.IGNORECASE,
    )
    if m:
        return {"intent": "pull_postmaster", "item_query": m.group(1).strip(), "target": "me", "mode": "command"}

    m = re.search(r"\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+from\s+my\s+vault\b", raw, re.IGNORECASE)
    if m:
        return {"intent": "transfer_from_vault", "item_query": m.group(1).strip(), "target": "me", "mode": "command"}

    m = re.search(
        r"\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+(?:to\s+)?(?:my\s+)?(hunter|warlock|titan|me)\b",
        raw,
        re.IGNORECASE,
    )
    if m:
        return {
            "intent": "transfer_to_character",
            "item_query": m.group(1).strip(),
            "target": _canonical_target(m.group(2)),
            "mode": "command",
        }

    m = re.search(r"\b(?:transfer|move)\s+(?:my\s+)?(.+?)\s+(?:to\s+)?(?:my\s+)?vault\b", raw, re.IGNORECASE)
    if m:
        return {"intent": "vault", "item_query": m.group(1).strip(), "target": None, "mode": "command"}

    return {"intent": "unknown", "item_query": None, "target": None, "mode": "chat"}


def _allowed_sources_for_intent(intent: str) -> set[str]:
    if intent == "equip":
        return {"inventory", "equipped", "vault", "postmaster"}
    if intent == "vault":
        return {"inventory", "equipped", "vault", "postmaster"}
    if intent == "pull_postmaster":
        return {"postmaster"}
    if intent == "transfer_from_vault":
        return {"vault"}
    if intent == "transfer_to_character":
        return {"inventory", "equipped", "vault", "postmaster"}
    return {"inventory", "equipped", "vault", "postmaster"}


def _resolve_target_character_id(profile: dict, target: str | None) -> str | None:
    chars = profile.get("Response", {}).get("characters", {}).get("data", {}) or {}
    if not chars:
        return None
    if target and str(target) in chars:
        return str(target)
    if not target or target == "me":
        cid = assistant._active_character_id(profile)
        if cid:
            return str(cid)
        return str(next(iter(chars.keys())))
    want = _class_target_to_type(target)
    if want is None:
        return str(next(iter(chars.keys())))
    for cid, cdata in chars.items():
        if cdata.get("classType") == want:
            return str(cid)
    return None


def _resolve_target_from_inventory(inventory: dict[str, Any], target: str | None) -> str | None:
    target = _canonical_target(target)
    chars = inventory.get("characters", []) or []
    if not chars:
        return None
    if target and any(str(target) == str(item.get("character_id")) for item in chars):
        return str(target)
    if not target or target == "me":
        return str(inventory.get("active_character_id") or chars[0].get("character_id"))
    for item in chars:
        if str(item.get("class_name") or "").lower() == target:
            return str(item.get("character_id"))
    return str(inventory.get("active_character_id") or chars[0].get("character_id"))


def _arm_assistant_tokens_for_user(uid: int) -> dict[str, Any] | None:
    tokens = get_bungie_tokens(uid) or None
    assistant._current_tokens = tokens
    if tokens:
        try:
            assistant.bungie.authenticate_user(tokens)
        except Exception:
            pass
    return tokens


def _resolve_item_for_user(uid: int, parsed: dict[str, Any]) -> dict[str, Any]:
    _arm_assistant_tokens_for_user(uid)
    dm = assistant._get_destiny_membership()
    if not dm:
        raise HTTPException(status_code=400, detail="Bungie account not linked")
    mid, mtype = dm
    profile = assistant.bungie.get_profile(mtype, mid, [102, 200, 201, 205])
    target = parsed.get("target")
    target_cid = _resolve_target_character_id(profile, target)
    target_class_type = None
    chars = profile.get("Response", {}).get("characters", {}).get("data", {}) or {}
    if target_cid and target_cid in chars:
        target_class_type = chars[target_cid].get("classType")

    res = assistant._resolve_dynamic_item(
        profile,
        parsed.get("item_query") or "",
        allowed_sources=_allowed_sources_for_intent(parsed.get("intent") or "unknown"),
        target_class_type=target_class_type,
    )
    return {
        "membership_id": mid,
        "membership_type": int(mtype),
        "profile": profile,
        "target_character_id": target_cid,
        "resolution": res,
    }


def _confirmation_payload(
    *,
    uid: int,
    intent: str,
    item_query: str | None,
    target: str | None,
    candidate: dict[str, Any],
    membership_id: str,
    membership_type: int,
) -> dict[str, Any]:
    _cleanup_expired_confirmations()
    token = f"cmd_{uuid.uuid4().hex}"
    payload = {
        "uid": uid,
        "intent": intent,
        "item_query": item_query or candidate.get("name"),
        "target": target,
        "candidate": {
            "instance_id": candidate.get("instance_id"),
            "item_hash": candidate.get("item_hash"),
            "name": candidate.get("name"),
            "source": candidate.get("source"),
            "character_id": candidate.get("character_id"),
            "class_type": candidate.get("class_type"),
        },
        "membership_id": membership_id,
        "membership_type": membership_type,
        "created_at": _time.time(),
        "expires_at": _time.time() + _COMMAND_CONFIRM_TTL_SECONDS,
    }
    _COMMAND_CONFIRMATIONS[token] = payload
    return {"token": token, "payload": payload}


def _character_name(characters: list[dict[str, Any]], character_id: str | None) -> str:
    if not character_id:
        return "active character"
    target = next((item for item in characters if str(item.get("character_id")) == str(character_id)), None)
    return str((target or {}).get("class_name") or character_id)


def _planned_steps_for_action(action: str, candidate: dict[str, Any], target_character_id: str | None) -> list[str]:
    name = candidate.get("name") or "item"
    source = candidate.get("source") or "inventory"
    steps: list[str] = []
    if source == "postmaster" and action in {"equip", "move_to_character", "vault", "pull_from_postmaster"}:
        steps.append(f"Claim {name} from postmaster")
    if source == "vault" and action in {"equip", "pull_from_vault", "move_to_character"}:
        steps.append(f"Pull {name} from vault")
    if source in {"inventory", "equipped"} and action in {"equip", "move_to_character"}:
        src_cid = candidate.get("character_id")
        if src_cid and target_character_id and str(src_cid) != str(target_character_id):
            steps.append(f"Move {name} to vault")
            steps.append(f"Move {name} to target character")
    if action == "vault":
        steps.append(f"Send {name} to vault")
    elif action == "equip":
        steps.append(f"Equip {name}")
    elif action == "move_to_character":
        steps.append(f"Move {name} to target character")
    elif action == "pull_from_postmaster":
        steps.append(f"Keep {name} on character inventory")
    elif action == "pull_from_vault":
        steps.append(f"Place {name} on character inventory")
    return steps


def _candidate_summary(candidate: dict[str, Any], inventory: dict[str, Any]) -> dict[str, Any]:
    character_id = candidate.get("character_id")
    return {
        "instance_id": candidate.get("instance_id"),
        "name": candidate.get("name"),
        "source": candidate.get("source"),
        "character_id": character_id,
        "character_name": _character_name(inventory.get("characters", []), str(character_id) if character_id else None),
        "power": candidate.get("power"),
        "tier": candidate.get("tier"),
        "class_name": candidate.get("class_name"),
    }


def _select_candidate_from_state(state: dict[str, Any], inventory: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any] | None:
    candidates = state.get("pending_candidates") or []
    if not candidates:
        return None
    idx = selection.get("index")
    if idx is not None and 0 <= int(idx) < len(candidates):
        return _find_normalized_item(inventory.get("items", []), str(candidates[int(idx)].get("instance_id") or ""))
    source = selection.get("source")
    if source:
        for candidate in candidates:
            if str(candidate.get("source")) == str(source):
                return _find_normalized_item(inventory.get("items", []), str(candidate.get("instance_id") or ""))
    class_name = selection.get("class_name")
    if class_name:
        for candidate in candidates:
            if str(candidate.get("character_name") or "").lower() == str(class_name).lower():
                return _find_normalized_item(inventory.get("items", []), str(candidate.get("instance_id") or ""))
    return None


def _execute_resolved_command(payload: dict[str, Any]) -> dict[str, Any]:
    intent = str(payload.get("intent") or "")
    cand = payload.get("candidate") or {}
    mid = payload.get("membership_id")
    mtype = int(payload.get("membership_type"))
    target = payload.get("target")
    item_name = cand.get("name") or payload.get("item_query") or "item"
    src = cand.get("source")
    src_cid = cand.get("character_id")
    iid = str(cand.get("instance_id"))
    ih = cand.get("item_hash")

    profile = assistant.bungie.get_profile(mtype, mid, [102, 200, 201, 205])
    target_cid = _resolve_target_character_id(profile, target)
    if intent in {"equip", "transfer_to_character", "transfer_from_vault", "pull_postmaster"} and not target_cid:
        raise HTTPException(status_code=400, detail="No target character available")

    if intent == "vault":
        if src == "vault":
            return {"ok": True, "message": f"{item_name} is already in your vault."}
        if src == "equipped":
            raise HTTPException(status_code=400, detail=f"{item_name} is equipped. Unequip it first.")
        if src == "postmaster":
            if not src_cid:
                raise HTTPException(status_code=400, detail="Postmaster item source character not found")
            pr = assistant.bungie.pull_from_postmaster(int(ih), 1, iid, str(src_cid), int(mtype))
            if pr.get("ErrorCode") != 1:
                raise HTTPException(status_code=400, detail=f"Failed to pull {item_name} from postmaster")
        if not src_cid:
            raise HTTPException(status_code=400, detail="Item source character not found")
        tr = assistant.bungie.transfer_item(
            membership_type=mtype,
            character_id=str(src_cid),
            item_id=iid,
            item_reference_hash=ih,
            stack_size=1,
            transfer_to_vault=True,
        )
        if tr.get("ErrorCode") != 1:
            raise HTTPException(status_code=400, detail=f"Failed to vault {item_name}")
        return {"ok": True, "message": f"Vaulted {item_name}."}

    if intent == "pull_postmaster":
        if src != "postmaster":
            return {"ok": True, "message": f"{item_name} is not in postmaster."}
        pull_to = src_cid or target_cid
        pr = assistant.bungie.pull_from_postmaster(int(ih), 1, iid, str(pull_to), int(mtype))
        if pr.get("ErrorCode") != 1:
            raise HTTPException(status_code=400, detail=f"Failed to pull {item_name} from postmaster")
        return {"ok": True, "message": f"Pulled {item_name} from postmaster."}

    if intent == "transfer_from_vault":
        if src != "vault":
            return {"ok": True, "message": f"{item_name} is not in your vault."}
        tr = assistant.bungie.transfer_item(
            membership_type=mtype,
            character_id=str(target_cid),
            item_id=iid,
            item_reference_hash=ih,
            stack_size=1,
            transfer_to_vault=False,
        )
        if tr.get("ErrorCode") != 1:
            raise HTTPException(status_code=400, detail=f"Failed to transfer {item_name} from vault")
        return {"ok": True, "message": f"Moved {item_name} from vault."}

    if intent in {"transfer_to_character", "equip"}:
        if src == "postmaster":
            pull_to = src_cid or target_cid
            pr = assistant.bungie.pull_from_postmaster(int(ih), 1, iid, str(pull_to), int(mtype))
            if pr.get("ErrorCode") != 1:
                raise HTTPException(status_code=400, detail=f"Failed to pull {item_name} from postmaster")
            src = "inventory"
            src_cid = str(pull_to)

        if src == "equipped" and src_cid and str(src_cid) != str(target_cid):
            raise HTTPException(status_code=400, detail=f"{item_name} is equipped on another character")

        if src == "vault":
            tr = assistant.bungie.transfer_item(
                membership_type=mtype,
                character_id=str(target_cid),
                item_id=iid,
                item_reference_hash=ih,
                stack_size=1,
                transfer_to_vault=False,
            )
            if tr.get("ErrorCode") != 1:
                raise HTTPException(status_code=400, detail=f"Failed to move {item_name} from vault")
            src = "inventory"
            src_cid = str(target_cid)

        if src in {"inventory", "equipped"} and src_cid and str(src_cid) != str(target_cid):
            to_vault = assistant.bungie.transfer_item(
                membership_type=mtype,
                character_id=str(src_cid),
                item_id=iid,
                item_reference_hash=ih,
                stack_size=1,
                transfer_to_vault=True,
            )
            if to_vault.get("ErrorCode") != 1:
                raise HTTPException(status_code=400, detail=f"Failed to move {item_name} to vault")
            to_target = assistant.bungie.transfer_item(
                membership_type=mtype,
                character_id=str(target_cid),
                item_id=iid,
                item_reference_hash=ih,
                stack_size=1,
                transfer_to_vault=False,
            )
            if to_target.get("ErrorCode") != 1:
                raise HTTPException(status_code=400, detail=f"Failed to move {item_name} to target character")

        if intent == "equip":
            eq = assistant.bungie.equip_item(membership_type=mtype, character_id=str(target_cid), item_id=iid)
            if eq.get("ErrorCode") != 1:
                raise HTTPException(status_code=400, detail=f"Failed to equip {item_name}")
            return {"ok": True, "message": f"Equipped {item_name}."}
        return {"ok": True, "message": f"Moved {item_name} to target character."}

    raise HTTPException(status_code=400, detail=f"Unsupported intent: {intent}")


def _class_name(class_type: int | None) -> str:
    names = {0: "Titan", 1: "Hunter", 2: "Warlock", 3: "Any"}
    return names.get(class_type, "Unknown")


def _item_kind(definition: dict[str, Any]) -> str:
    resp = definition.get("Response", {}) if isinstance(definition, dict) else {}
    item_type = resp.get("itemType")
    if item_type == 2:
        return "armor"
    if item_type == 3:
        return "weapon"
    return "other"


def _item_icon_path(definition: dict[str, Any]) -> str | None:
    resp = definition.get("Response", {}) if isinstance(definition, dict) else {}
    icon = resp.get("displayProperties", {}).get("icon")
    if isinstance(icon, str) and icon:
        if icon.startswith("http://") or icon.startswith("https://"):
            return icon
        return f"https://www.bungie.net{icon}"
    return None


def _character_summary_map(profile: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    chars = profile.get("Response", {}).get("characters", {}).get("data", {}) or {}
    active_id = assistant._active_character_id(profile)
    items: list[dict[str, Any]] = []
    for cid, cdata in chars.items():
        items.append(
            {
                "character_id": str(cid),
                "class_type": cdata.get("classType"),
                "class_name": _class_name(cdata.get("classType")),
                "light": cdata.get("light"),
                "date_last_played": cdata.get("dateLastPlayed"),
                "is_active": str(cid) == str(active_id),
            }
        )
    items.sort(key=lambda item: (not item["is_active"], item["class_name"]))
    return items, (str(active_id) if active_id else None)


def _allowed_actions_for_item(
    source: str,
    character_id: str | None,
    active_character_id: str | None,
    kind: str,
    class_type: int | None,
) -> list[str]:
    if kind not in {"weapon", "armor"}:
        return []
    actions: list[str] = []
    if source == "vault":
        actions.append("pull_from_vault")
        actions.append("equip")
        actions.append("move_to_character")
    elif source == "postmaster":
        actions.append("pull_from_postmaster")
        actions.append("equip")
        actions.append("move_to_character")
        actions.append("vault")
    elif source == "inventory":
        actions.append("vault")
        actions.append("equip")
        if not active_character_id or str(character_id) != str(active_character_id):
            actions.append("move_to_character")
    elif source == "equipped":
        if active_character_id and str(character_id) == str(active_character_id):
            actions.append("equip")
    return actions


def _load_profile_for_user(uid: int) -> tuple[str, int, dict[str, Any]]:
    _arm_assistant_tokens_for_user(uid)
    dm = assistant._get_destiny_membership()
    if not dm:
        raise HTTPException(status_code=400, detail="Bungie account not linked")
    mid, mtype = dm
    profile = assistant.bungie.get_profile(mtype, mid, [102, 200, 201, 205, 300, 302, 304, 305])
    return str(mid), int(mtype), profile


def _normalized_inventory_payload(uid: int) -> dict[str, Any]:
    membership_id, membership_type, profile = _load_profile_for_user(uid)
    characters, active_character_id = _character_summary_map(profile)
    normalized_items: list[dict[str, Any]] = []
    sections = {
        "equipped": [],
        "inventory": [],
        "vault": [],
        "postmaster": [],
    }

    for ref in assistant._collect_owned_items(profile):
        item = ref.get("item", {}) or {}
        item_hash = item.get("itemHash")
        instance_id = item.get("itemInstanceId")
        if item_hash is None or not instance_id:
            continue
        try:
            definition = assistant.bungie.get_inventory_item_definition(item_hash)
        except Exception:
            definition = {"Response": {}}
        source = str(ref.get("source") or "inventory")
        character_id = ref.get("character_id")
        kind = _item_kind(definition)
        class_type = assistant._item_class_type(item_hash)
        normalized = {
            "instance_id": str(instance_id),
            "item_hash": item_hash,
            "name": assistant._get_item_name(item_hash) or "Unknown Item",
            "icon": _item_icon_path(definition),
            "bucket": kind.title(),
            "bucket_hash": item.get("bucketHash"),
            "source": source,
            "character_id": str(character_id) if character_id is not None else None,
            "equipped": source == "equipped",
            "item_type": definition.get("Response", {}).get("itemType"),
            "item_type_name": kind,
            "tier": definition.get("Response", {}).get("inventory", {}).get("tierTypeName"),
            "power": item.get("primaryStat", {}).get("value"),
            "class_type": class_type,
            "class_name": _class_name(class_type),
            "transfer_status": item.get("transferStatus"),
            "transferable": item.get("transferStatus", 0) == 0,
            "actions": _allowed_actions_for_item(source, str(character_id) if character_id is not None else None, active_character_id, kind, class_type),
        }
        normalized_items.append(normalized)
        if source in sections:
            sections[source].append(normalized)

    def _sort_key(entry: dict[str, Any]) -> tuple[Any, ...]:
        return (
            entry.get("item_type_name") != "weapon",
            entry.get("item_type_name") != "armor",
            -(entry.get("power") or 0),
            str(entry.get("name") or "").lower(),
        )

    for bucket in sections.values():
        bucket.sort(key=_sort_key)

    return {
        "membership_id": membership_id,
        "membership_type": membership_type,
        "active_character_id": active_character_id,
        "characters": characters,
        "sections": sections,
        "items": normalized_items,
    }


def _find_normalized_item(items: list[dict[str, Any]], instance_id: str) -> dict[str, Any] | None:
    for item in items:
        if str(item.get("instance_id")) == str(instance_id):
            return item
    return None


def _intent_for_action(action: str) -> str:
    mapping = {
        "equip": "equip",
        "vault": "vault",
        "pull_from_vault": "transfer_from_vault",
        "pull_from_postmaster": "pull_postmaster",
        "move_to_character": "transfer_to_character",
    }
    intent = mapping.get((action or "").strip().lower())
    if not intent:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")
    return intent


def _action_for_intent(intent: str) -> str:
    mapping = {
        "equip": "equip",
        "vault": "vault",
        "transfer_from_vault": "pull_from_vault",
        "pull_postmaster": "pull_from_postmaster",
        "transfer_to_character": "move_to_character",
    }
    action = mapping.get((intent or "").strip().lower())
    if not action:
        raise HTTPException(status_code=400, detail=f"Unsupported intent: {intent}")
    return action


def _preview_message(action: str, candidate: dict[str, Any], target_character_id: str | None, characters: list[dict[str, Any]]) -> str:
    name = candidate.get("name") or "item"
    source = candidate.get("source") or "inventory"
    if action == "vault":
        return f"Vault {name} from {source}?"
    if action == "pull_from_vault":
        target = next((c for c in characters if str(c.get("character_id")) == str(target_character_id)), None)
        target_name = (target or {}).get("class_name") or "active character"
        return f"Move {name} from vault to your {target_name}?"
    if action == "pull_from_postmaster":
        return f"Pull {name} from postmaster?"
    if action == "equip":
        target = next((c for c in characters if str(c.get("character_id")) == str(target_character_id)), None)
        target_name = (target or {}).get("class_name") or "active character"
        return f"Equip {name} on your {target_name}?"
    if action == "move_to_character":
        target = next((c for c in characters if str(c.get("character_id")) == str(target_character_id)), None)
        target_name = (target or {}).get("class_name") or "target character"
        return f"Move {name} to your {target_name}?"
    return f"Run {action} for {name}?"


def _prepare_action_confirmation(
    *,
    uid: int,
    inventory: dict[str, Any],
    candidate: dict[str, Any],
    action: str,
    target_character_id: str | None,
    item_query: str | None = None,
) -> dict[str, Any]:
    if action not in set(candidate.get("actions") or []):
        raise HTTPException(status_code=400, detail=f"Action '{action}' is not available for this item")
    if action in {"equip", "pull_from_vault", "move_to_character"} and not target_character_id:
        raise HTTPException(status_code=400, detail="A target character is required for this action")
    class_type = candidate.get("class_type")
    target_character = next(
        (item for item in inventory.get("characters", []) if str(item.get("character_id")) == str(target_character_id)),
        None,
    )
    if (
        action in {"equip", "move_to_character", "pull_from_vault"}
        and class_type in {0, 1, 2}
        and target_character
        and target_character.get("class_type") != class_type
    ):
        raise HTTPException(
            status_code=400,
            detail=f"{candidate.get('name')} is {_class_name(class_type)}-only and cannot go to {target_character.get('class_name')}",
        )
    intent = _intent_for_action(action)
    stored = _confirmation_payload(
        uid=uid,
        intent=intent,
        item_query=item_query or candidate.get("name"),
        target=str(target_character_id) if target_character_id else None,
        candidate=candidate,
        membership_id=str(inventory.get("membership_id") or ""),
        membership_type=int(inventory.get("membership_type") or 0),
    )
    return {
        "action": action,
        "intent": intent,
        "candidate": candidate,
        "target_character_id": str(target_character_id) if target_character_id else None,
        "target_character_name": target_character.get("class_name") if target_character else None,
        "preview": _preview_message(action, candidate, str(target_character_id) if target_character_id else None, inventory.get("characters", [])),
        "confirmation_token": stored["token"],
        "confirmation_expires_in": _COMMAND_CONFIRM_TTL_SECONDS,
        "planned_steps": _planned_steps_for_action(action, candidate, str(target_character_id) if target_character_id else None),
    }


def _read_inventory_reply(inventory: dict[str, Any], parsed: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    intent = parsed.get("intent")
    target_character_id = _resolve_target_from_inventory(inventory, parsed.get("target"))
    items = inventory.get("items", [])
    characters = inventory.get("characters", [])
    if intent == "list_equipped":
        equipped = [
            item for item in items
            if item.get("source") == "equipped" and str(item.get("character_id")) == str(target_character_id)
        ]
        char_name = _character_name(characters, target_character_id)
        if not equipped:
            return (f"Your {char_name} has no equipped gear I can read right now.", [])
        names = ", ".join(item.get("name") or "Unknown Item" for item in equipped[:6])
        return (f"Your {char_name} has {names} equipped.", equipped[:6])
    if intent == "list_postmaster":
        postmaster = [
            item for item in items
            if item.get("source") == "postmaster" and str(item.get("character_id")) == str(target_character_id)
        ]
        char_name = _character_name(characters, target_character_id)
        if not postmaster:
            return (f"Your {char_name} postmaster is clear.", [])
        names = ", ".join(item.get("name") or "Unknown Item" for item in postmaster[:5])
        return (f"Your {char_name} postmaster has {names}.", postmaster[:5])
    if intent == "list_inventory":
        section_name = str(parsed.get("section") or "inventory")
        scoped = inventory.get("sections", {}).get(section_name, []) or []
        if section_name == "inventory" and target_character_id:
            scoped = [item for item in scoped if str(item.get("character_id")) == str(target_character_id)]
        if not scoped:
            return (f"I don't see anything in your {section_name}.", [])
        names = ", ".join(item.get("name") or "Unknown Item" for item in scoped[:6])
        return (f"Your {section_name} includes {names}.", scoped[:6])
    if intent == "find_item":
        query = str(parsed.get("item_query") or "").lower()
        matches = [item for item in items if query and query in str(item.get("name") or "").lower()]
        if not matches:
            return (f"I couldn't find {parsed.get('item_query')}.", [])
        if len(matches) == 1:
            match = matches[0]
            source = match.get("source")
            owner = _character_name(characters, match.get("character_id"))
            return (f"{match.get('name')} is in {source} on your {owner}.", [match])
        summaries = [
            f"{item.get('name')} in {item.get('source')} on {_character_name(characters, item.get('character_id'))}"
            for item in matches[:4]
        ]
        return ("I found multiple matches: " + "; ".join(summaries) + ".", matches[:4])
    return ("I can help with inventory, equipped gear, vault, and postmaster actions.", [])


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
    message: str,
    provider: str | None = None,
    session_id: str | None = None,
    model: str | None = None,
    persona: str | None = None,
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

    headers = {"X-Conversation-Id": conv_id}
    return StreamingResponse(_gen(), media_type="text/plain", headers=headers)


def _execute_confirmation_token(uid: int, token: str) -> dict[str, Any]:
    _cleanup_expired_confirmations()
    pending = _COMMAND_CONFIRMATIONS.get(token)
    if not pending:
        raise HTTPException(status_code=400, detail="Invalid or expired confirmation token")
    if int(pending.get("uid") or -1) != uid:
        raise HTTPException(status_code=403, detail="Confirmation token does not belong to this user")

    try:
        current_inventory = _normalized_inventory_payload(uid)
        current_item = _find_normalized_item(
            current_inventory.get("items", []),
            str((pending.get("candidate") or {}).get("instance_id") or ""),
        )
        if not current_item:
            raise HTTPException(status_code=409, detail="That item is no longer available in the expected location")
        expected_action = _action_for_intent(str(pending.get("intent") or ""))
        if expected_action not in set(current_item.get("actions") or []):
            raise HTTPException(status_code=409, detail="That action is no longer valid for the current item state")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to validate pending command state before execution")

    _arm_assistant_tokens_for_user(uid)
    outcome = _execute_resolved_command(pending)
    action_id = f"act_{uuid.uuid4().hex}"
    audit = {
        "action_id": action_id,
        "uid": uid,
        "intent": pending.get("intent"),
        "item_query": pending.get("item_query"),
        "target": pending.get("target"),
        "candidate": pending.get("candidate"),
        "result": outcome,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _ACTION_AUDIT[action_id] = audit
    _COMMAND_CONFIRMATIONS.pop(token, None)
    return {
        "status": "ok",
        "action_id": action_id,
        "result": outcome,
    }


def _voice_catalog_payload() -> dict[str, Any]:
    return {
        "examples": [
            "Equip Forerunner on my Hunter",
            "Move Hawkmoon to my Warlock",
            "Pull my Matador from the vault",
            "Grab my postmaster shotgun",
            "Where is Conditional Finality",
            "Show equipped gear on my Titan",
        ],
        "read_intents": ["list_equipped", "list_inventory", "list_postmaster", "find_item"],
        "action_intents": ["equip", "vault", "transfer_from_vault", "transfer_to_character", "pull_postmaster"],
        "confirmation_required_for": ["equip", "vault", "transfer_from_vault", "transfer_to_character", "pull_postmaster"],
    }


def _voice_turn_response(
    *,
    uid: int,
    session_id: str | None,
    text: str,
    inventory: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    parsed = _parse_command_text(text, state)
    intent = str(parsed.get("intent") or "unknown")
    response: dict[str, Any] = {
        "session_id": session_id or "default",
        "transcript_text": text,
        "intent": intent,
        "reply_text": "",
        "resolution_state": "unknown",
        "confirmation_required": False,
        "confirmation_token": None,
        "planned_steps": [],
        "candidates": [],
        "result": None,
        "target": parsed.get("target"),
        "item_query": parsed.get("item_query"),
    }

    if intent == "cancel":
        state["pending_confirmation_token"] = None
        state["pending_candidates"] = []
        state["pending_intent"] = None
        state["pending_target"] = None
        response["reply_text"] = "Canceled. Ready for the next order."
        response["resolution_state"] = "cancelled"
        return response

    if intent == "confirm":
        token = state.get("pending_confirmation_token")
        if not token:
            response["reply_text"] = "There is no pending action to confirm."
            response["resolution_state"] = "unresolved"
            return response
        executed = _execute_confirmation_token(uid, str(token))
        state["pending_confirmation_token"] = None
        state["pending_candidates"] = []
        state["pending_intent"] = None
        state["pending_target"] = None
        response["reply_text"] = str((executed.get("result") or {}).get("message") or "Action completed.")
        response["resolution_state"] = "executed"
        response["result"] = executed.get("result")
        response["action_id"] = executed.get("action_id")
        return response

    if intent == "select_candidate":
        candidate = _select_candidate_from_state(state, inventory, parsed.get("selection") or {})
        if not candidate:
            response["reply_text"] = "I still need you to choose one of the matching items."
            response["resolution_state"] = "ambiguous"
            response["candidates"] = state.get("pending_candidates") or []
            return response
        action = _action_for_intent(str(state.get("pending_intent") or ""))
        target_character_id = _resolve_target_from_inventory(inventory, state.get("pending_target"))
        preview = _prepare_action_confirmation(
            uid=uid,
            inventory=inventory,
            candidate=candidate,
            action=action,
            target_character_id=target_character_id,
        )
        state["pending_confirmation_token"] = preview["confirmation_token"]
        state["pending_candidates"] = []
        state["last_candidate"] = _candidate_summary(candidate, inventory)
        response["reply_text"] = preview["preview"]
        response["resolution_state"] = "confirmation_required"
        response["confirmation_required"] = True
        response["confirmation_token"] = preview["confirmation_token"]
        response["planned_steps"] = preview["planned_steps"]
        response["result"] = preview
        return response

    if parsed.get("mode") == "read":
        reply_text, matches = _read_inventory_reply(inventory, parsed)
        response["reply_text"] = reply_text
        response["resolution_state"] = "resolved" if matches else "unresolved"
        response["candidates"] = [_candidate_summary(item, inventory) for item in matches]
        return response

    if intent == "unknown":
        response["reply_text"] = "I can handle inventory voice commands like equip, move, vault, postmaster, and gear lookups."
        response["resolution_state"] = "unknown"
        return response

    resolved = _resolve_item_for_user(uid, parsed)
    res = resolved["resolution"]
    resolution_state = str(res.get("state") or "unresolved")
    if resolution_state == "unresolved":
        response["reply_text"] = f"I couldn't find {parsed.get('item_query')}."
        response["resolution_state"] = "unresolved"
        return response
    if resolution_state == "ambiguous":
        candidates = [
            _candidate_summary(candidate, inventory)
            for candidate in (res.get("candidates") or [])
        ]
        state["pending_candidates"] = candidates
        state["pending_intent"] = parsed.get("intent")
        state["pending_target"] = parsed.get("target")
        response["reply_text"] = "I found multiple matches. Say the vault one, the equipped one, or first, second, or third."
        response["resolution_state"] = "ambiguous"
        response["candidates"] = candidates
        return response

    candidate = res.get("candidate")
    if not candidate:
        response["reply_text"] = "I couldn't resolve that item."
        response["resolution_state"] = "unresolved"
        return response

    target_character_id = resolved.get("target_character_id") or _resolve_target_from_inventory(inventory, parsed.get("target"))
    action = _action_for_intent(intent)
    preview = _prepare_action_confirmation(
        uid=uid,
        inventory=inventory,
        candidate=candidate,
        action=action,
        target_character_id=str(target_character_id) if target_character_id else None,
        item_query=str(parsed.get("item_query") or candidate.get("name") or ""),
    )
    state["pending_confirmation_token"] = preview["confirmation_token"]
    state["pending_candidates"] = []
    state["pending_intent"] = parsed.get("intent")
    state["pending_target"] = parsed.get("target")
    state["last_candidate"] = _candidate_summary(candidate, inventory)
    state["last_intent"] = parsed.get("intent")
    response["reply_text"] = preview["preview"]
    response["resolution_state"] = "confirmation_required"
    response["confirmation_required"] = True
    response["confirmation_token"] = preview["confirmation_token"]
    response["planned_steps"] = preview["planned_steps"]
    response["result"] = preview
    return response


@app.post("/api/v1/commands/parse")
def api_parse_command(payload: CommandParseRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    _require_user(authorization)
    parsed = _parse_command_text(payload.text or "")
    intent = parsed.get("intent")
    if intent in {"unknown", "confirm", "cancel", "select_candidate"} or parsed.get("mode") == "read":
        return {
            "intent": "unknown",
            "item_query": None,
            "target": None,
            "needs_confirmation": False,
            "message": "No executable inventory command detected.",
        }
    return {
        "intent": intent,
        "item_query": parsed.get("item_query"),
        "target": parsed.get("target"),
        "needs_confirmation": True,
    }


@app.post("/api/v1/items/resolve")
def api_resolve_item(payload: CommandResolveRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    user = _require_user(authorization)
    uid = int(user["id"])
    parsed = {
        "intent": payload.intent,
        "item_query": payload.item_query,
        "target": payload.target,
    }
    if not parsed["intent"] and payload.text:
        parsed = _parse_command_text(payload.text)
    if not parsed.get("intent") or parsed.get("intent") == "unknown" or not parsed.get("item_query"):
        raise HTTPException(status_code=400, detail="Could not parse a supported command intent")

    resolved = _resolve_item_for_user(uid, parsed)
    res = resolved["resolution"]
    state = res.get("state")
    if state == "unresolved":
        return {"resolution_state": "unresolved", "candidates": [], "intent": parsed["intent"], "target": parsed.get("target")}
    if state == "ambiguous":
        return {
            "resolution_state": "ambiguous",
            "candidates": res.get("candidates", []),
            "intent": parsed["intent"],
            "target": parsed.get("target"),
        }

    candidate = res.get("candidate")
    if not candidate:
        return {"resolution_state": "unresolved", "candidates": [], "intent": parsed["intent"], "target": parsed.get("target")}

    stored = _confirmation_payload(
        uid=uid,
        intent=str(parsed["intent"]),
        item_query=str(parsed["item_query"]),
        target=parsed.get("target"),
        candidate=candidate,
        membership_id=str(resolved["membership_id"]),
        membership_type=int(resolved["membership_type"]),
    )
    return {
        "resolution_state": "resolved",
        "candidate": candidate,
        "intent": parsed["intent"],
        "target": parsed.get("target"),
        "confirmation_token": stored["token"],
        "confirmation_expires_in": _COMMAND_CONFIRM_TTL_SECONDS,
    }


@app.get("/api/v1/voice/catalog")
def api_voice_catalog(authorization: str | None = Header(None)) -> dict[str, Any]:
    _require_user(authorization)
    return _voice_catalog_payload()


@app.post("/api/v1/voice/turn")
def api_voice_turn(payload: VoiceTurnRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    user = _require_user(authorization)
    uid = int(user["id"])
    conv_id = (payload.session_id or "").strip() or f"conv-{uuid.uuid4().hex}"
    ensure_conversation(conv_id, uid, name="Voice", provider="voice")
    append_message(conv_id, f"msg-{uuid.uuid4().hex}", "user", payload.text or "")
    inventory = _normalized_inventory_payload(uid)
    state = _ensure_voice_state(uid, conv_id)
    state["active_character_id"] = inventory.get("active_character_id")
    result = _voice_turn_response(
        uid=uid,
        session_id=conv_id,
        text=payload.text or "",
        inventory=inventory,
        state=state,
    )
    try:
        append_message(conv_id, f"msg-{uuid.uuid4().hex}", "assistant", str(result.get("reply_text") or ""))
    except Exception:
        pass
    return result


@app.get("/api/v1/inventory")
def api_inventory(authorization: str | None = Header(None)) -> dict[str, Any]:
    user = _require_user(authorization)
    return _normalized_inventory_payload(int(user["id"]))


@app.get("/api/v1/inventory/characters")
def api_inventory_characters(authorization: str | None = Header(None)) -> dict[str, Any]:
    user = _require_user(authorization)
    payload = _normalized_inventory_payload(int(user["id"]))
    return {
        "active_character_id": payload.get("active_character_id"),
        "characters": payload.get("characters", []),
    }


@app.post("/api/v1/items/actions/preview")
def api_preview_inventory_action(
    payload: InventoryActionPreviewRequest,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    user = _require_user(authorization)
    uid = int(user["id"])
    inventory = _normalized_inventory_payload(uid)
    candidate = _find_normalized_item(inventory.get("items", []), payload.item_instance_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Item instance not found")

    action = (payload.action or "").strip().lower()
    target_character_id = payload.target_character_id or inventory.get("active_character_id")
    return _prepare_action_confirmation(
        uid=uid,
        inventory=inventory,
        candidate=candidate,
        action=action,
        target_character_id=str(target_character_id) if target_character_id else None,
    )


@app.post("/api/v1/items/actions/execute")
def api_execute_inventory_action(
    payload: CommandExecuteRequest,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    return api_execute_command(payload, authorization)


@app.post("/api/v1/commands/execute")
def api_execute_command(payload: CommandExecuteRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    user = _require_user(authorization)
    uid = int(user["id"])
    token = (payload.confirmation_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="Missing confirmation token")
    return _execute_confirmation_token(uid, token)


@app.get("/api/v1/actions/{action_id}")
def api_get_action(action_id: str, authorization: str | None = Header(None)) -> dict[str, Any]:
    user = _require_user(authorization)
    uid = int(user["id"])
    item = _ACTION_AUDIT.get(action_id)
    if not item or int(item.get("uid") or -1) != uid:
        raise HTTPException(status_code=404, detail="Action not found")
    return item


@app.get("/models")
def list_models() -> dict[str, object]:
    """Return available model options for providers.

    Currently supports:
    - Ollama: queries ``/api/tags`` and returns tag names.
    """
    result: dict[str, object] = {"ollama": [], "providers": [], "default_provider": None}
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

    providers: list[str] = []
    if os.getenv("XAI_API_KEY"):
        providers.append("grok")
    if result["ollama"] or os.getenv("OLLAMA_MODEL"):
        providers.append("ollama")
    if os.getenv("GHOST_ENABLE_FINETUNE", "").strip().lower() in {"1", "true", "yes", "on"}:
        providers.append("finetune")
    if not providers:
        providers = ["ollama", "grok"]

    default_provider = "grok" if "grok" in providers else providers[0]
    if "ollama" in providers:
        try:
            default_provider = assistant._default_provider()
        except Exception:
            default_provider = "grok" if "grok" in providers else providers[0]

    result["providers"] = providers
    result["default_provider"] = default_provider
    return result


@app.get("/api/v1/app-config")
def api_app_config(authorization: str | None = Header(None)) -> dict[str, Any]:
    auth = auth_status(authorization)
    models = list_models()
    personas = list_personas()
    voices = list_voices()
    return {
        "auth": auth,
        "models": models,
        "personas": personas.get("personas", []),
        "voices": voices.get("voices", []),
        "voice_capabilities": voices.get("capabilities", {}),
        "voice_catalog": _voice_catalog_payload(),
        "api_base": "/",
        "mobile_oauth_path": "/oauth/mobile/authorize",
    }


@app.get("/personas")
def list_personas() -> dict[str, object]:
    try:
        return {"personas": _personas.list_personalities()}
    except Exception:
        return {"personas": ["destiny_ghost"]}


def _voice_capabilities() -> dict[str, Any]:
    realtime_enabled = bool((os.getenv("GHOST_REALTIME_VOICE") or "").strip())
    return {
        "mode": "realtime" if realtime_enabled else "browser-native",
        "continuous": True,
        "interruptible": True,
        "stt": {
            "browser": True,
            "server_upload": False,
            "server_live": False,
        },
        "tts": {
            "browser": True,
            "server_audio": False,
        },
        "fallback": "browser-native",
    }


@app.get("/voices")
def list_voices() -> dict[str, object]:
    capabilities = _voice_capabilities()
    return {
        "voices": [
            {
                "key": "system",
                "name": "System",
                "provider": "browser",
                "mode": capabilities["mode"],
                "personas": ["destiny_ghost"],
            },
            {
                "key": "ghost",
                "name": "Ghost Companion",
                "provider": "browser",
                "mode": capabilities["mode"],
                "personas": ["destiny_ghost"],
            },
        ],
        "capabilities": capabilities,
    }


@app.post("/api/v1/voice/session")
def create_voice_session(
    payload: VoiceSessionRequest | None = None,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    user = _require_user(authorization)
    requested_mode = (payload.mode if payload else None) or "auto"
    capabilities = _voice_capabilities()
    return {
        "session_id": f"voice_{uuid.uuid4().hex}",
        "requested_mode": requested_mode,
        "capabilities": capabilities,
        "recommended_voice": "ghost",
        "status": "ready",
        "user_id": int(user["id"]),
    }


@app.post("/api/v1/voice/cancel")
def cancel_voice_session(authorization: str | None = Header(None)) -> dict[str, Any]:
    _require_user(authorization)
    return {"ok": True, "status": "cancelled"}


@app.post("/stt")
async def stt_upload(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type.lower():
        raise HTTPException(status_code=400, detail="Expected multipart audio upload")
    raise HTTPException(
        status_code=501,
        detail="Server STT is not configured in this build. Use browser speech mode from the UI.",
    )


@app.post("/stt/local")
def stt_local(_: dict[str, Any] | None = None) -> dict[str, Any]:
    raise HTTPException(
        status_code=501,
        detail="Desktop capture STT is not configured in this build. Use browser speech mode from the UI.",
    )


@app.get("/diagnostics/audio")
def audio_diagnostics() -> dict[str, object]:
    return {
        "devices": [],
        "ok": True,
        "note": "Browser-side microphones only in this build.",
        "voice": _voice_capabilities(),
    }


# Mount static last so API routes like /auth/* remain reachable
if SERVE_UI:
    app.mount("/", StaticFiles(directory=str(FRONTEND_BUILD_DIR), html=True), name="static")
