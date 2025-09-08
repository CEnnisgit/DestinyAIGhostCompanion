"""Minimal client for interacting with the Bungie API.

This module exposes :class:`BungieClient` which wraps a ``requests.Session``
configured according to Bungie's guidelines. Requests automatically include the
required API key and a descriptive ``User-Agent`` header, and responses are
checked for throttling and error codes.
"""

from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any

import requests

BASE_URL = "https://www.bungie.net/Platform"


class BungieAPIError(Exception):
    """Raised when the Bungie API returns an error."""


class BungieClient:
    """Client for performing requests against the Bungie API.

    Parameters
    ----------
    api_key:
        A valid Bungie API key obtained from Bungie.net.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize a client with authentication and headers.

        The ``User-Agent`` header follows Bungie's recommended format
        ``AppName/Version (+URL)`` and is sourced from environment variables:

        ``BUNGIE_APP_NAME`` (default ``"Ghost-Companion"``),
        ``BUNGIE_APP_VERSION`` (default ``"0"``) and
        ``BUNGIE_APP_URL`` (default ``"https://example.com"``).
        """

        self.session = requests.Session()
        self.session.headers["X-API-Key"] = api_key

        app_name = os.getenv("BUNGIE_APP_NAME", "Ghost-Companion")
        version = os.getenv("BUNGIE_APP_VERSION", "0")
        url = os.getenv("BUNGIE_APP_URL", "https://example.com")
        self.session.headers["User-Agent"] = f"{app_name}/{version} (+{url})"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform a GET request to ``path`` and return the JSON payload.

        This helper enforces Bungie's throttling recommendations, raising
        :class:`BungieAPIError` when rate limits are exceeded or when the API
        returns a non-success ``ErrorCode``.
        """

        resp = self.session.get(f"{BASE_URL}{path}", params=params)

        if resp.status_code != 200:
            raise BungieAPIError(f"HTTP error {resp.status_code}")

        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                time.sleep(int(retry_after))
            except ValueError:
                pass

        if resp.headers.get("X-RateLimit-Remaining") == "0":
            raise BungieAPIError(
                "Bungie API rate limit exceeded. Please slow down your requests."
            )

        try:
            data = resp.json()
        except ValueError as exc:  # pragma: no cover - defensive
            raise BungieAPIError("Invalid JSON response from Bungie API") from exc

        if data.get("ErrorCode") != 1:
            message = data.get("Message", "Bungie API error")
            raise BungieAPIError(message)
        return data

    # Public API methods -------------------------------------------------

    def search_destiny_player(
        self, membership_type: int | str, display_name: str
    ) -> Dict[str, Any]:
        """Search for a Destiny player by membership type and display name."""

        path = f"/Destiny2/SearchDestinyPlayer/{membership_type}/{display_name}/"
        return self._get(path)

    def get_profile(
        self,
        membership_type: int | str,
        destiny_membership_id: str,
        components: str,
    ) -> Dict[str, Any]:
        """Retrieve a Destiny profile for ``destiny_membership_id``.

        ``components`` is a comma separated list of component codes as strings
        defined by Bungie's API. It is passed directly to the underlying
        request.
        """

        path = f"/Destiny2/{membership_type}/Profile/{destiny_membership_id}/"
        params = {"components": components}
        return self._get(path, params)

    def get_character(
        self,
        membership_type: int | str,
        destiny_membership_id: str,
        character_id: str,
        components: str,
    ) -> Dict[str, Any]:
        """Retrieve a character for a Destiny profile."""

        path = (
            f"/Destiny2/{membership_type}/Profile/{destiny_membership_id}/"
            f"Character/{character_id}/"
        )
        params = {"components": components}
        return self._get(path, params)
