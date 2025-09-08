"""FastAPI server exposing a simple chat endpoint backed by Ollama."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ghost.ollama import OllamaClient, OllamaError

app = FastAPI()
client = OllamaClient()


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(req: ChatRequest) -> dict[str, str]:
    try:
        reply = client.generate(req.message)
    except OllamaError as exc:  # pragma: no cover - simple wrapper
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"reply": reply}
