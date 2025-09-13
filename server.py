"""FastAPI server exposing a chat endpoint orchestrated by ``GhostAssistant``."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from ghost.assistant import GhostAssistant
from ghost.ollama import OllamaError
from ghost.bungie import BungieAPIError

app = FastAPI()
assistant = GhostAssistant()


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
