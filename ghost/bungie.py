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
    access_token:
        Optional OAuth access token to be included in requests. If provided,
        an ``Authorization`` header will be added using the ``Bearer`` scheme.
    refresh_token:
        Optional OAuth refresh token. When supplied, it is stored for future
        token refresh operations.
    """

    def __init__(
        self,
        api_key: str,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
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

        self.access_token: str | None = None
        self.refresh_token: str | None = refresh_token
        # Manifest caching -------------------------------------------------
        # ``_manifest`` stores the result of ``get_manifest`` so subsequent
        # calls do not hit the network again. ``_entity_cache`` keeps a mapping
        # of entity type -> hash -> response for ``get_entity`` lookups.
        self._manifest: Dict[str, Any] | None = None
        self._entity_cache: Dict[str, Dict[str, Any]] = {}
        if access_token is not None:
            self.set_access_token(access_token)

    def authenticate_user(self, tokens: Dict[str, Any]) -> None:
        """Store OAuth tokens for subsequent requests.

        Parameters
        ----------
        tokens:
            Mapping containing at least an ``access_token`` and optionally a
            ``refresh_token`` from the OAuth token exchange.
        """

        access = tokens.get("access_token")
        if access:
            self.set_access_token(access)
        self.refresh_token = tokens.get("refresh_token", self.refresh_token)

    # ------------------------------------------------------------------
    # Token handling ---------------------------------------------------
    def set_access_token(self, access_token: str) -> None:
        """Set or update the OAuth access token for authenticated requests."""

        self.access_token = access_token
        self.session.headers["Authorization"] = f"Bearer {access_token}"

    def refresh_access_token(self, access_token: str) -> None:
        """Refresh the OAuth access token.

        This is a convenience wrapper around :meth:`set_access_token` to make
        the intent explicit for callers when rotating tokens.
        """

        self.set_access_token(access_token)

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

        error_code = data.get("ErrorCode")
        if error_code != 1:
            message = data.get("Message", "Bungie API error")
            raise BungieAPIError(f"{message} (ErrorCode: {error_code})")
        return data

    def _post(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Perform a POST request to ``path`` and return the JSON payload."""

        resp = self.session.post(
            f"{BASE_URL}{path}", json=payload, headers=headers
        )

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

    def search_player_by_name(
        self, membership_type: int | str, display_name: str, display_code: int
    ) -> Dict[str, Any]:
        """Search for a player by Bungie name and code."""

        path = f"/Destiny2/SearchDestinyPlayerByBungieName/{membership_type}/"
        payload = {"displayName": display_name, "displayNameCode": display_code}
        return self._post(path, payload)

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

    def get_linked_profiles(
        self,
        membership_type: int | str,
        destiny_membership_id: str,
        get_all_memberships: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve linked profiles for the given membership."""

        path = (
            f"/Destiny2/{membership_type}/Profile/{destiny_membership_id}/LinkedProfiles/"
        )
        params = {"getAllMemberships": get_all_memberships}
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

    def get_item(
        self,
        membership_type: int | str,
        destiny_membership_id: str,
        item_instance_id: str,
        components: str,
    ) -> Dict[str, Any]:
        """Retrieve a Destiny item instance."""

        path = (
            f"/Destiny2/{membership_type}/Profile/{destiny_membership_id}/"
            f"Item/{item_instance_id}/"
        )
        params = {"components": components}
        return self._get(path, params)

    def get_character_vendors(
        self,
        membership_type: int | str,
        destiny_membership_id: str,
        character_id: str,
        components: str,
    ) -> Dict[str, Any]:
        """Retrieve vendor data for a character."""

        path = (
            f"/Destiny2/{membership_type}/Profile/{destiny_membership_id}/"
            f"Character/{character_id}/Vendors/"
        )
        params = {"components": components}
        return self._get(path, params)

    def get_vendor(
        self,
        membership_type: int | str,
        destiny_membership_id: str,
        character_id: str,
        vendor_hash: str,
        components: str,
    ) -> Dict[str, Any]:
        """Retrieve a specific vendor for a character."""

        path = (
            f"/Destiny2/{membership_type}/Profile/{destiny_membership_id}/"
            f"Character/{character_id}/Vendors/{vendor_hash}/"
        )
        params = {"components": components}
        return self._get(path, params)

    def get_collectibles(
        self,
        membership_type: int | str,
        destiny_membership_id: str,
        character_id: str,
        components: str,
    ) -> Dict[str, Any]:
        """Retrieve collectible status for a character."""

        path = (
            f"/Destiny2/{membership_type}/Profile/{destiny_membership_id}/"
            f"Character/{character_id}/Collectibles/"
        )
        params = {"components": components}
        return self._get(path, params)

    # Manifest endpoints -------------------------------------------------
    def get_manifest(self) -> Dict[str, Any]:
        """Retrieve the Destiny manifest.

        The result is cached on the client instance so repeated calls do not
        trigger additional network requests.
        """

        if self._manifest is None:
            self._manifest = self._get("/Destiny2/Manifest/")
        return self._manifest

    def get_entity(self, entity_type: str, hash_id: int | str) -> Dict[str, Any]:
        """Retrieve a single entity definition from the manifest.

        Parameters
        ----------
        entity_type:
            The manifest component type, e.g. ``"DestinyInventoryItemDefinition"``.
        hash_id:
            Hash identifier of the desired entity.

        Results are cached per entity type and hash to avoid redundant network
        calls.
        """

        cache = self._entity_cache.setdefault(entity_type, {})
        key = str(hash_id)
        if key not in cache:
            cache[key] = self._get(
                f"/Destiny2/Manifest/{entity_type}/{key}/"
            )
        return cache[key]
