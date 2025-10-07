"""FastAPI server exposing a chat endpoint orchestrated by ``GhostAssistant``."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from ghost.assistant import GhostAssistant
from ghost.ollama import OllamaError
from ghost.bungie import BungieAPIError
from ghost import auth

def get_repo_root() -> Path:
    """Resolve the directory that holds the application files."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent

REPO_ROOT = get_repo_root()
FRONTEND_BUILD_DIR = REPO_ROOT / "frontend"

app = FastAPI()
assistant = GhostAssistant()

# Serve static files only in the bundled executable
if getattr(sys, "frozen", False):
    app.mount("/", StaticFiles(directory=str(FRONTEND_BUILD_DIR), html=True), name="static")


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root() -> dict[str, str]:
    """Provide basic usage information."""
    return {"detail": "Send POST /chat with {'message': ...}"}


@app.post("/chat")
def chat(req: ChatRequest) -> dict[str, str]:
    try:
        reply = assistant.chat(req.message)
    except (OllamaError, BungieAPIError) as exc:  # pragma: no cover - simple wrapper
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"reply": reply}


@app.get("/oauth/authorize")
def oauth_authorize() -> dict[str, str]:
    """Return the Bungie authorization URL."""
    client_id = os.environ["BUNGIE_CLIENT_ID"]
    redirect_uri = os.environ["BUNGIE_REDIRECT_URI"]
    url = auth.get_authorization_url(client_id, redirect_uri=redirect_uri)
    return {"authorization_url": url}


@app.get("/oauth/callback")
def oauth_callback(code: str) -> dict:
    """Exchange ``code`` for tokens and persist them."""
    client_id = os.environ["BUNGIE_CLIENT_ID"]
    client_secret = os.environ["BUNGIE_CLIENT_SECRET"]
    tokens = auth.exchange_code_for_token(client_id, client_secret, code)
    auth.save_tokens(tokens)
    assistant.bungie.authenticate_user(tokens)
    return tokens
