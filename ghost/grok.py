"""Client for interacting with xAI's Grok API."""

from __future__ import annotations

import os
from typing import Any

import requests


class GrokError(Exception):
    """Raised when the Grok API cannot be reached or returns an error."""


class GrokClient:
    """Client for xAI's Grok API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("XAI_API_KEY", "")
        if not self.api_key:
            raise GrokError("xAI API key is not set")
        self.base_url = "https://api.x.ai/v1"

    def generate(self, prompt: str) -> str:
        """Send ``prompt`` to the Grok API as a single message.

        Parameters
        ----------
        prompt:
            The text prompt to feed into the model.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": os.getenv("GROK_MODEL", "grok-3"),
            "stream": False,
            "temperature": 0.7
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise GrokError(f"Grok API error: {response.status_code} - {response.text}")

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def generate_with_system(self, system_prompt: str, user_prompt: str) -> str:
        """Send system and user prompts to the Grok API.

        Parameters
        ----------
        system_prompt:
            The system prompt to set context.
        user_prompt:
            The user prompt.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "model": os.getenv("GROK_MODEL", "grok-3"),
            "stream": False,
            "temperature": 0.7
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise GrokError(f"Grok API error: {response.status_code} - {response.text}")

        result = response.json()
        return result["choices"][0]["message"]["content"]
