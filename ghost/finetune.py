"""Wrapper client for the local fine-tuned LLaMA pipeline.

This client defers heavy imports until used and falls back internally to
Ollama via ``inference_with_api.generate_response``.
"""

from __future__ import annotations

from typing import Optional


class FineTuneClient:
    """Thin wrapper around ``inference_with_api.generate_response``."""

    def __init__(self) -> None:
        # No heavy initialization here; inference module handles lazy load
        pass

    def generate(self, prompt: str) -> str:
        from inference_with_api import generate_response

        resp = generate_response(prompt)
        return resp if isinstance(resp, str) else str(resp)

    def generate_with_system(self, system_prompt: str, user_prompt: str) -> str:
        # Compose a chat-style prompt that ``generate_response`` can split
        prompt = f"System: {system_prompt}\nUser: {user_prompt}\nGhost:"
        return self.generate(prompt)

