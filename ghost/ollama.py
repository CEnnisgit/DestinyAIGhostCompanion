"""Client for interacting with a locally hosted Ollama API."""

from __future__ import annotations

import os
from typing import Any

import requests


class OllamaError(Exception):
    """Raised when the Ollama API cannot be reached or returns an error."""


class OllamaClient:
    """Minimal client for the Ollama API.

    Uses ``/api/generate`` with non-streaming responses.
    """

    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "")
        if not self.model:
            raise OllamaError("Ollama model is not set")

    def generate(self, prompt: str) -> str:
        """Send ``prompt`` to the Ollama ``/api/generate`` endpoint.

        Parameters
        ----------
        prompt:
            The text prompt to feed into the model.

        Returns
        -------
        str
            The model's textual response.
        """
        url = f"{self.host}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        try:
            resp = requests.post(url, json=payload, timeout=60)
        except Exception as exc:  # pragma: no cover - defensive
            raise OllamaError("Failed to connect to Ollama") from exc

        if resp.status_code != 200:
            raise OllamaError(f"Ollama API returned {resp.status_code}: {resp.text}")

        try:
            data: dict[str, Any] = resp.json()
        except Exception as exc:  # pragma: no cover - defensive
            raise OllamaError(f"Invalid response from Ollama: {resp.text}") from exc

        return str(data.get("response", ""))

    def generate_with_system(self, system_prompt: str, user_prompt: str) -> str:
        """Use a combined prompt to simulate a system + user message.

        Parameters
        ----------
        system_prompt:
            The system message to set context.
        user_prompt:
            The user message.

        Returns
        -------
        str
            The model's textual response.
        """
        combined = f"System: {system_prompt}\nUser: {user_prompt}\nAssistant:"
        return self.generate(combined)
