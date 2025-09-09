"""Minimal client for interacting with the Bungie API.

This module exposes :class:`BungieClient` which wraps a ``requests.Session``
configured according to Bungie's guidelines. Requests automatically include the
required API key and a descriptive ``User-Agent`` header, and responses are
checked for throttling and error codes.
"""

from __future__ import annotations

import os
import time
import threading
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
        *,
        manifest_ttl: int = 3600,
        profile_ttl: int = 60,
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
        # Throttling -------------------------------------------------------
        # ``_next_request`` tracks when the next request may be made according
        # to ``Retry-After`` headers. A simple ``Lock`` is used to queue
        # concurrent calls so only one request is in flight at a time.
        self._throttle_lock = threading.Lock()
        self._next_request: float = 0.0

        # Caching ----------------------------------------------------------
        self.manifest_ttl = manifest_ttl
        self.profile_ttl = profile_ttl
        # ``_manifest_cache`` stores (data, expiry)
        self._manifest_cache: tuple[Dict[str, Any], float] | None = None
        # ``_profile_cache`` maps request parameters to (data, expiry)
        self._profile_cache: Dict[tuple[str, str, str], tuple[Dict[str, Any], float]] = {}
        # ``_entity_cache`` keeps a mapping of entity type -> hash -> response
        # for ``get_entity`` lookups.
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

        A simple throttle controller ensures that requests respecting
        ``Retry-After`` headers are spaced out and that concurrent calls are
        queued. Rate limit headers still result in :class:`BungieAPIError`.
        """

        with self._throttle_lock:
            now = time.time()
            wait = self._next_request - now
            if wait > 0:
                time.sleep(wait)

            resp = self.session.get(f"{BASE_URL}{path}", params=params)

            retry_after = resp.headers.get("Retry-After")
            delay = 0
            if retry_after:
                try:
                    delay = int(retry_after)
                except ValueError:
                    delay = 0
            self._next_request = max(self._next_request, time.time() + delay)

        if resp.status_code != 200:
            raise BungieAPIError(f"HTTP error {resp.status_code}")

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

        with self._throttle_lock:
            now = time.time()
            wait = self._next_request - now
            if wait > 0:
                time.sleep(wait)

            resp = self.session.post(
                f"{BASE_URL}{path}", json=payload, headers=headers
            )

            retry_after = resp.headers.get("Retry-After")
            delay = 0
            if retry_after:
                try:
                    delay = int(retry_after)
                except ValueError:
                    delay = 0
            self._next_request = max(self._next_request, time.time() + delay)

        if resp.status_code != 200:
            raise BungieAPIError(f"HTTP error {resp.status_code}")

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

        Results are cached in-memory for ``profile_ttl`` seconds to minimise
        duplicate network requests during short polling intervals.
        ``components`` is a comma separated list of component codes as strings
        defined by Bungie's API. It is passed directly to the underlying
        request.
        """

        path = f"/Destiny2/{membership_type}/Profile/{destiny_membership_id}/"
        params = {"components": components}
        key = (str(membership_type), str(destiny_membership_id), components)
        cached = self._profile_cache.get(key)
        now = time.time()
        if cached and cached[1] > now:
            return cached[0]

        result = self._get(path, params)
        self._profile_cache[key] = (result, time.time() + self.profile_ttl)
        return result

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

    # Item and loadout actions -----------------------------------------
    def transfer_item(
        self,
        membership_type: int | str,
        character_id: str,
        item_id: str,
        item_reference_hash: int | str,
        stack_size: int = 1,
        transfer_to_vault: bool = False,
    ) -> Dict[str, Any]:
        """Transfer an item to a character or the vault."""

        path = "/Destiny2/Actions/Items/TransferItem/"
        payload = {
            "membershipType": membership_type,
            "characterId": character_id,
            "itemId": item_id,
            "itemReferenceHash": item_reference_hash,
            "stackSize": stack_size,
            "transferToVault": transfer_to_vault,
        }
        return self._post(path, payload)

    def pull_from_postmaster(
        self,
        membership_type: int | str,
        character_id: str,
        item_id: str,
        item_reference_hash: int | str,
        stack_size: int = 1,
    ) -> Dict[str, Any]:
        """Pull an item from the postmaster to a character."""

        path = "/Destiny2/Actions/Items/PullFromPostmaster/"
        payload = {
            "membershipType": membership_type,
            "characterId": character_id,
            "itemId": item_id,
            "itemReferenceHash": item_reference_hash,
            "stackSize": stack_size,
        }
        return self._post(path, payload)

    def equip_item(
        self,
        membership_type: int | str,
        character_id: str,
        item_id: str,
    ) -> Dict[str, Any]:
        """Equip a single item on a character."""

        path = "/Destiny2/Actions/Items/EquipItem/"
        payload = {
            "membershipType": membership_type,
            "characterId": character_id,
            "itemId": item_id,
        }
        return self._post(path, payload)

    def equip_items(
        self,
        membership_type: int | str,
        character_id: str,
        item_ids: list[str | int],
    ) -> Dict[str, Any]:
        """Equip multiple items on a character."""

        path = "/Destiny2/Actions/Items/EquipItems/"
        payload = {
            "membershipType": membership_type,
            "characterId": character_id,
            "itemIds": item_ids,
        }
        return self._post(path, payload)

    def equip_loadout(
        self,
        membership_type: int | str,
        character_id: str,
        loadout_index: int,
    ) -> Dict[str, Any]:
        """Equip a loadout by index."""

        path = "/Destiny2/Actions/Loadouts/EquipLoadout/"
        payload = {
            "membershipType": membership_type,
            "characterId": character_id,
            "loadoutIndex": loadout_index,
        }
        return self._post(path, payload)

    def snapshot_loadout(
        self,
        membership_type: int | str,
        character_id: str,
        loadout_index: int,
        name_hash: int | None = None,
        icon_hash: int | None = None,
        color_hash: int | None = None,
    ) -> Dict[str, Any]:
        """Snapshot a loadout with the currently equipped items."""

        path = "/Destiny2/Actions/Loadouts/SnapshotLoadout/"
        payload: Dict[str, Any] = {
            "membershipType": membership_type,
            "characterId": character_id,
            "loadoutIndex": loadout_index,
        }
        if name_hash is not None:
            payload["nameHash"] = name_hash
        if icon_hash is not None:
            payload["iconHash"] = icon_hash
        if color_hash is not None:
            payload["colorHash"] = color_hash
        return self._post(path, payload)

    def set_lock_state(
        self,
        membership_type: int | str,
        character_id: str,
        item_id: str,
        state: bool,
    ) -> Dict[str, Any]:
        """Set the lock state for an item instance."""

        path = "/Destiny2/Actions/Items/SetLockState/"
        payload = {
            "membershipType": membership_type,
            "characterId": character_id,
            "itemId": item_id,
            "state": state,
        }
        return self._post(path, payload)

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

        The result is cached on the client instance for ``manifest_ttl``
        seconds so repeated calls within the TTL do not trigger additional
        network requests.
        """
        now = time.time()
        if self._manifest_cache and self._manifest_cache[1] > now:
            return self._manifest_cache[0]

        data = self._get("/Destiny2/Manifest/")
        self._manifest_cache = (data, time.time() + self.manifest_ttl)
        return data

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

    # GroupV2 endpoints --------------------------------------------------
    def group_search(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Search for groups or clans using the provided ``query`` payload."""

        path = "/GroupV2/Search/"
        return self._post(path, query)


    def get_clan_members(
        self,
        group_id: int | str,
        *,
        member_type: int | None = None,
        name_search: str | None = None,
        current_page: int | None = None,
    ) -> Dict[str, Any]:
        """Retrieve the members of a clan."""

        path = f"/GroupV2/{group_id}/Members/"
        params: Dict[str, Any] = {}
        if member_type is not None:
            params["memberType"] = member_type
        if name_search is not None:
            params["nameSearch"] = name_search
        if current_page is not None:
            params["currentPage"] = current_page
        return self._get(path, params or None)


    def set_membership_type(
        self,
        group_id: int | str,
        membership_type: int | str,
        membership_id: int | str,
        member_type: int | str,
    ) -> Dict[str, Any]:
        """Change the membership type of a clan member."""

        path = (
            f"/GroupV2/{group_id}/Members/{membership_type}/{membership_id}/"
            f"SetMembershipType/{member_type}/"
        )
        return self._post(path, {})


    def kick_member(
        self,
        group_id: int | str,
        membership_type: int | str,
        membership_id: int | str,
    ) -> Dict[str, Any]:
        """Kick a member from the clan."""

        path = (
            f"/GroupV2/{group_id}/Members/{membership_type}/{membership_id}/Kick/"
        )
        return self._post(path, {})


    def ban_member(
        self,
        group_id: int | str,
        membership_type: int | str,
        membership_id: int | str,
        *,
        comment: str | None = None,
        length: int | None = None,
    ) -> Dict[str, Any]:
        """Ban a member from the clan."""

        path = (
            f"/GroupV2/{group_id}/Members/{membership_type}/{membership_id}/Ban/"
        )
        payload: Dict[str, Any] = {}
        if comment is not None:
            payload["comment"] = comment
        if length is not None:
            payload["length"] = length
        return self._post(path, payload)


    # Fireteam endpoints -------------------------------------------------
    def fireteam_search(
        self,
        platform: int | str,
        activity_type: int | str,
        date_range: int | str,
        slot_filter: int | str,
        page: int | str,
        *,
        exclude_immediate: bool | None = None,
        lang_filter: str | None = None,
    ) -> Dict[str, Any]:
        """Search for public fireteams."""

        path = (
            f"/Fireteam/Search/Available/{platform}/{activity_type}/"
            f"{date_range}/{slot_filter}/{page}/"
        )
        params: Dict[str, Any] = {}
        if exclude_immediate is not None:
            params["excludeImmediate"] = exclude_immediate
        if lang_filter is not None:
            params["langFilter"] = lang_filter
        return self._get(path, params or None)

    def list_clan_fireteams(
        self,
        group_id: int | str,
        platform: int | str,
        activity_type: int | str,
        date_range: int | str,
        slot_filter: int | str,
        public_only: int | str,
        page: int | str,
        *,
        exclude_immediate: bool | None = None,
        lang_filter: str | None = None,
    ) -> Dict[str, Any]:
        """List fireteams for a specific clan."""

        path = (
            f"/Fireteam/Clan/{group_id}/Available/{platform}/{activity_type}/"
            f"{date_range}/{slot_filter}/{public_only}/{page}/"
        )
        params: Dict[str, Any] = {}
        if exclude_immediate is not None:
            params["excludeImmediate"] = exclude_immediate
        if lang_filter is not None:
            params["langFilter"] = lang_filter
        return self._get(path, params or None)

    def fireteam_summary(
        self, group_id: int | str, fireteam_id: int | str
    ) -> Dict[str, Any]:
        """Get summary information about a clan fireteam."""

        path = f"/Fireteam/Clan/{group_id}/Summary/{fireteam_id}/"
        return self._get(path)
