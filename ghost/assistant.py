"""High level assistant orchestrating Bungie and Ollama clients."""

from __future__ import annotations

import os
import re
from typing import Any

from .bungie import BungieClient
from .ollama import OllamaClient


class GhostAssistant:
    """Orchestrates requests between Bungie and Ollama.

    The assistant performs a very small amount of intent detection. If the
    incoming message asks for Destiny player information (``player <name>``)
    the Bungie API is queried and the results are fed into the language
    model. Otherwise the message is passed directly to the model.
    """

    def __init__(
        self,
        bungie_client: BungieClient | None = None,
        ollama_client: OllamaClient | None = None,
        api_key: str | None = None,
    ) -> None:
        """Create a new assistant instance.

        Parameters
        ----------
        bungie_client:
            Optional preconfigured :class:`BungieClient` instance.
        ollama_client:
            Optional client used for language model interactions.
        api_key:
            If ``None``, the key is read from the ``BUNGIE_API_KEY`` environment
            variable.
        """
        if bungie_client is None:
            key = api_key or os.getenv("BUNGIE_API_KEY", "")
            bungie_client = BungieClient(key)
        self.bungie = bungie_client
        self.ollama = ollama_client or OllamaClient()

    # ------------------------------------------------------------------
    def chat(self, message: str) -> str:
        """Return a reply for ``message``.

        When the message matches ``player <name>`` the Bungie ``search_destiny_player``
        endpoint is invoked and the resulting payload is included in the prompt
        sent to the language model.
        """

        match = re.search(r"player\s+(\w+)", message, flags=re.IGNORECASE)
        if match:
            name = match.group(1)
            data: Any = self.bungie.search_destiny_player(0, name)
            prompt = f"Information about player {name}: {data}"
            return self.ollama.generate(prompt)
        return self.ollama.generate(message)
