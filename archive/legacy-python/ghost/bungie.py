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
import json
from pathlib import Path

import requests

BASE_URL = "https://www.bungie.net/Platform"


class BungieAPIError(Exception):
    """Raised when the Bungie API returns an error."""


class BungieClient:
    """Client for performing requests against the Bungie API.

    The constructor requires an API key. When used through
    :class:`GhostAssistant`, the key is automatically read from the
    ``BUNGIE_API_KEY`` environment variable unless a client is provided
    explicitly.

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

        if not api_key:
            raise RuntimeError("BUNGIE_API_KEY environment variable not set or empty")

        self.session = requests.Session()
        self.session.headers["X-API-Key"] = api_key

        # Separate session for unauthenticated requests (like manifest)
        self.unauth_session = requests.Session()
        self.unauth_session.headers["X-API-Key"] = api_key

        app_name = os.getenv("BUNGIE_APP_NAME", "Ghost-Companion")
        version = os.getenv("BUNGIE_APP_VERSION", "0")
        url = os.getenv("BUNGIE_APP_URL", "https://example.com")
        self.session.headers["User-Agent"] = f"{app_name}/{version} (+{url})"
        self.unauth_session.headers["User-Agent"] = f"{app_name}/{version} (+{url})"

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
        # Caching (beginner-friendly summary):
        # - We remember some responses for a short time so repeated calls
        #   don’t re-download the same JSON over and over.
        # - For the manifest (slow, rarely changes), we keep it for
        #   `manifest_ttl` seconds. For profiles (queried a lot), we keep each
        #   unique request for `profile_ttl` seconds.
        # - Each cache entry stores `(data, expiry_timestamp)`.
        # - After the time passes, we fetch again and refresh the cache.
        # ``_manifest_cache`` stores (data, expiry)
        self._manifest_cache: tuple[Dict[str, Any], float] | None = None
        # ``_profile_cache`` maps request parameters to (data, expiry)
        self._profile_cache: Dict[tuple[str, str, str], tuple[Dict[str, Any], float]] = {}
        # ``_entity_cache`` keeps a mapping of entity type -> hash -> response
        # for ``get_entity`` lookups.
        self._entity_cache: Dict[str, Dict[str, Any]] = {}
        if access_token is not None:
            self.set_access_token(access_token)

        # Disk cache for definitions
        try:
            cache_dir = Path(os.getcwd()) / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self._defs_cache_path = cache_dir / "item_defs.json"
            self._defs_disk: Dict[str, Any] = {}
            if self._defs_cache_path.exists():
                try:
                    with self._defs_cache_path.open("r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        if isinstance(data, dict):
                            self._defs_disk = dict(data.get("defs", {}))
                except Exception:
                    self._defs_disk = {}
        except Exception:
            self._defs_disk = {}

    # Lightweight definition cache -------------------------------------
    def get_inventory_item_definition(self, item_hash: int | str) -> Dict[str, Any]:
        """Return DestinyInventoryItemDefinition for a given hash with caching.

        This avoids repeated network calls across requests for the same item.
        """
        bucket = self._entity_cache.setdefault("DestinyInventoryItemDefinition", {})
        key = str(item_hash)
        # Check memory cache
        cached = bucket.get(key)
        if cached is not None:
            return cached
        # Check disk cache
        disk = getattr(self, "_defs_disk", {})
        if key in disk:
            bucket[key] = disk[key]
            return disk[key]
        data = self._get(
            f"/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/",
            authenticated=False,
        )
        bucket[key] = data
        # Persist to disk cache
        try:
            disk[key] = data
            with self._defs_cache_path.open("w", encoding="utf-8") as fh:
                json.dump({"defs": disk}, fh)
        except Exception:
            pass
        return data

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

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, authenticated: bool = True) -> Dict[str, Any]:
        """Perform a GET request to ``path`` and return the JSON payload.

        A simple throttle controller ensures that requests respecting
        ``Retry-After`` headers are spaced out and that concurrent calls are
        queued. Rate limit headers still result in :class:`BungieAPIError`.
        """

        session = self.session if authenticated else self.unauth_session

        with self._throttle_lock:
            now = time.time()
            wait = self._next_request - now
            if wait > 0:
                time.sleep(wait)

            resp = session.get(f"{BASE_URL}{path}", params=params)

            retry_after = resp.headers.get("Retry-After")
            delay = 0
            if retry_after:
                try:
                    delay = int(retry_after)
                except ValueError:
                    delay = 0
            self._next_request = max(self._next_request, time.time() + delay)

        if resp.status_code != 200:
            try:
                body = resp.text[:500]
            except Exception:
                body = "<no body>"
            raise BungieAPIError(f"HTTP error {resp.status_code}: {body}")

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
        """Perform a POST request to ``path`` and return the JSON payload.

        Retries a few times on transient server/network errors (5xx, 429).
        """

        attempts = 3
        backoff = 0.5
        last_exc: Exception | None = None
        for attempt in range(attempts):
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

            # Non-200s
            if resp.status_code != 200:
                # Gather body for diagnostics
                try:
                    body = resp.text[:500]
                except Exception:
                    body = "<no body>"
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                    time.sleep(backoff * (attempt + 1))
                    continue
                raise BungieAPIError(f"HTTP error {resp.status_code}: {body}")

            if resp.headers.get("X-RateLimit-Remaining") == "0":
                raise BungieAPIError(
                    "Bungie API rate limit exceeded. Please slow down your requests."
                )

            try:
                data = resp.json()
            except ValueError as exc:  # pragma: no cover - defensive
                last_exc = exc
                if attempt < attempts - 1:
                    time.sleep(backoff * (attempt + 1))
                    continue
                raise BungieAPIError("Invalid JSON response from Bungie API") from exc

            if data.get("ErrorCode") != 1:
                message = data.get("Message", "Bungie API error")
                # Not transient if application-level failure
                raise BungieAPIError(f"{message} (ErrorCode: {data.get('ErrorCode')})")
            return data

        # Should not get here
        if last_exc:
            raise BungieAPIError(str(last_exc))
        raise BungieAPIError("Bungie POST failed after retries")

    # Public API methods -------------------------------------------------

    def get_memberships_by_id(
        self, membership_id: str, membership_type: int | str
    ) -> Dict[str, Any]:
        """Get memberships for a Bungie.net user."""

        path = f"/User/GetMembershipsById/{membership_id}/{membership_type}/"
        return self._get(path)

    def get_memberships_for_current_user(self) -> Dict[str, Any]:
        """Get memberships for the current authenticated user."""

        path = "/User/GetMembershipsForCurrentUser/"
        return self._get(path)

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

    def _get_profile_cached(
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

    def _get_character(
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

    def dismantle_item(
        self,
        membership_type: int | str,
        character_id: str,
        item_id: str,
    ) -> Dict[str, Any]:
        """Dismantle an item instance on a character."""

        path = "/Destiny2/Actions/Items/DismantleItem/"
        payload = {
            "membershipType": membership_type,
            "characterId": character_id,
            "itemId": item_id,
        }
        return self._post(path, payload)

    def _get_item(
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

    def _get_character_vendors(
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

    def _get_vendor(
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

    def _get_collectibles(
        self,
        membership_type: int | str,
        destiny_membership_id: str,
        character_id: str,
        collectible_presentation_node_hash: str,
        components: str,
    ) -> Dict[str, Any]:
        """Retrieve collectible status for a character presentation node.

        Parameters
        ----------
        collectible_presentation_node_hash:
            Hash identifier for the presentation node whose collectibles should
            be returned.
        """

        path = (
            f"/Destiny2/{membership_type}/Profile/{destiny_membership_id}/"
            f"Character/{character_id}/Collectibles/{collectible_presentation_node_hash}/"
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

    def get_milestones(self) -> Dict[str, Any]:
        """Get information about current milestones."""
        return self._get("/Destiny2/Milestones/")

    def get_trending_categories(self) -> Dict[str, Any]:
        """Get trending categories."""
        return self._get("/Trending/Categories/")

    def get_trending_category(self, category_id: str, page: int = 0) -> Dict[str, Any]:
        """Get specific trending category."""
        return self._get(f"/Trending/Categories/{category_id}/{page}")

    def get_global_alerts(self) -> Dict[str, Any]:
        """Get global alerts and announcements."""
        return self._get("/GlobalAlerts/")

    # Destiny 2 specific endpoints ---------------------------------------

    def search_destiny_player_by_bungie_name(
        self, membership_type: int, display_name: str, display_name_code: int = 0
    ) -> Dict[str, Any]:
        """Search for Destiny 2 player by Bungie name."""
        path = f"/Destiny2/SearchDestinyPlayerByBungieName/{membership_type}/"
        payload = {
            "displayName": display_name,
            "displayNameCode": display_name_code
        }
        return self._post(path, payload)

    def get_profile(
        self,
        membership_type: int,
        destiny_membership_id: str,
        components: list[int] | None = None
    ) -> Dict[str, Any]:
        """Get Destiny 2 profile information (cached briefly).

        Accepts a list of component codes; converts to the API's comma-separated
        string, then delegates to the cached implementation to respect
        `profile_ttl`.
        """
        if components is None:
            components = [100, 200, 201, 205, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 400, 401, 402, 500, 600, 700, 800, 900, 1000, 1100]
        components_str = ",".join(str(c) for c in components)
        return self._get_profile_cached(membership_type, destiny_membership_id, components_str)

    def get_character(
        self,
        membership_type: int,
        destiny_membership_id: str,
        character_id: str,
        components: list[int] | None = None
    ) -> Dict[str, Any]:
        """Get Destiny 2 character information.

        Accepts components as list of ints and delegates to the canonical
        implementation after formatting.
        """
        if components is None:
            components = [100, 200, 201, 205, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 400, 401, 402]
        components_str = ",".join(str(c) for c in components)
        return self._get_character(membership_type, destiny_membership_id, character_id, components_str)

    def transfer_item(self, *args, **kwargs) -> Dict[str, Any]:
        """Transfer an item between vault and character inventory.

        Supports both calling styles used across the codebase:
        - transfer_item(membership_type, character_id, item_id, item_reference_hash, stack_size=1, transfer_to_vault=False)
        - transfer_item(item_reference_hash, stack_size, transfer_to_vault, item_id, character_id, membership_type)
        - transfer_item(membership_type=.., character_id=.., item_id=.., item_reference_hash=.., stack_size=1, transfer_to_vault=False)
        """
        # Defaults
        membership_type = kwargs.get("membership_type")
        character_id = kwargs.get("character_id")
        item_id = kwargs.get("item_id")
        item_reference_hash = kwargs.get("item_reference_hash")
        stack_size = kwargs.get("stack_size", 1)
        transfer_to_vault = kwargs.get("transfer_to_vault", False)

        # If positional in legacy order: (membership_type, character_id, item_id, item_reference_hash, stack_size?, transfer_to_vault?)
        if membership_type is None and len(args) >= 3:
            membership_type = args[0]
            character_id = args[1]
            item_id = args[2]
            if len(args) >= 4:
                item_reference_hash = args[3]
            if len(args) >= 5:
                stack_size = args[4]
            if len(args) >= 6:
                transfer_to_vault = args[5]

        # If positional in alternate order from this file's earlier definition:
        # (item_reference_hash, stack_size, transfer_to_vault, item_id, character_id, membership_type)
        if item_id is None and len(args) >= 6 and membership_type is None:
            item_reference_hash = args[0]
            stack_size = args[1]
            transfer_to_vault = args[2]
            item_id = args[3]
            character_id = args[4]
            membership_type = args[5]

        # Validate
        if item_reference_hash is None:
            raise BungieAPIError("item_reference_hash is required for transfer_item")
        if membership_type is None or character_id is None or item_id is None:
            raise BungieAPIError("membership_type, character_id, and item_id are required for transfer_item")

        path = "/Destiny2/Actions/Items/TransferItem/"
        payload = {
            "itemReferenceHash": int(item_reference_hash),
            "stackSize": int(stack_size),
            "transferToVault": bool(transfer_to_vault),
            "itemId": str(item_id),
            "characterId": str(character_id),
            "membershipType": int(membership_type),
        }
        return self._post(path, payload)

    def equip_item(
        self,
        item_id: str,
        character_id: str,
        membership_type: int
    ) -> Dict[str, Any]:
        """Equip an item on a character."""
        path = "/Destiny2/Actions/Items/EquipItem/"
        payload = {
            "itemId": item_id,
            "characterId": character_id,
            "membershipType": membership_type
        }
        return self._post(path, payload)

    def pull_from_postmaster(
        self,
        item_reference_hash: int,
        stack_size: int,
        item_id: str,
        character_id: str,
        membership_type: int
    ) -> Dict[str, Any]:
        """Pull an item from the postmaster."""
        path = "/Destiny2/Actions/Items/PullFromPostmaster/"
        payload = {
            "itemReferenceHash": item_reference_hash,
            "stackSize": stack_size,
            "itemId": item_id,
            "characterId": character_id,
            "membershipType": membership_type
        }
        return self._post(path, payload)

    def get_vendors(
        self,
        membership_type: int,
        destiny_membership_id: str,
        character_id: str,
        components: list[int] | None = None
    ) -> Dict[str, Any]:
        """Get vendor information for a character (wrapper).

        Converts component list and calls the canonical implementation.
        """
        if components is None:
            components = [100, 101, 102, 103, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320]
        components_str = ",".join(str(c) for c in components)
        return self._get_character_vendors(membership_type, destiny_membership_id, character_id, components_str)

    def get_vendor(
        self,
        membership_type: int,
        destiny_membership_id: str,
        character_id: str,
        vendor_hash: int,
        components: list[int] | None = None
    ) -> Dict[str, Any]:
        """Get specific vendor information (wrapper)."""
        if components is None:
            components = [100, 101, 102, 103, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320]
        components_str = ",".join(str(c) for c in components)
        return self._get_vendor(membership_type, destiny_membership_id, character_id, str(vendor_hash), components_str)

    def get_historical_stats_for_account(
        self,
        membership_type: int,
        destiny_membership_id: str,
        groups: list[int] | None = None,
        modes: list[int] | None = None,
        period_type: int = 2,
        month_start: int | None = None,
        month_end: int | None = None,
        day_start: int | None = None,
        day_end: int | None = None
    ) -> Dict[str, Any]:
        """Get historical stats for a Destiny account."""
        path = f"/Destiny2/{membership_type}/Account/{destiny_membership_id}/Stats/"
        params = {"periodType": period_type}
        if groups:
            params["groups"] = ",".join(str(g) for g in groups)
        if modes:
            params["modes"] = ",".join(str(m) for m in modes)
        if month_start is not None:
            params["monthstart"] = month_start
        if month_end is not None:
            params["monthend"] = month_end
        if day_start is not None:
            params["daystart"] = day_start
        if day_end is not None:
            params["dayend"] = day_end
        return self._get(path, params)

    def get_historical_stats(
        self,
        membership_type: int,
        destiny_membership_id: str,
        character_id: str,
        groups: list[int] | None = None,
        modes: list[int] | None = None,
        period_type: int = 2,
        month_start: int | None = None,
        month_end: int | None = None,
        day_start: int | None = None,
        day_end: int | None = None
    ) -> Dict[str, Any]:
        """Get historical stats for a Destiny character."""
        path = f"/Destiny2/{membership_type}/Account/{destiny_membership_id}/Character/{character_id}/Stats/"
        params = {"periodType": period_type}
        if groups:
            params["groups"] = ",".join(str(g) for g in groups)
        if modes:
            params["modes"] = ",".join(str(m) for m in modes)
        if month_start is not None:
            params["monthstart"] = month_start
        if month_end is not None:
            params["monthend"] = month_end
        if day_start is not None:
            params["daystart"] = day_start
        if day_end is not None:
            params["dayend"] = day_end
        return self._get(path, params)

    def get_leaderboards_for_character(
        self,
        membership_type: int,
        destiny_membership_id: str,
        character_id: str,
        modes: str | None = None,
        statid: str | None = None,
        period_type: int = 2
    ) -> Dict[str, Any]:
        """Get leaderboards for a character."""
        path = f"/Destiny2/Stats/Leaderboards/{membership_type}/{destiny_membership_id}/{character_id}/"
        params = {"periodType": period_type}
        if modes:
            params["modes"] = modes
        if statid:
            params["statid"] = statid
        return self._get(path, params)

    def get_clan_weekly_reward_state(self, group_id: int) -> Dict[str, Any]:
        """Get clan weekly reward state."""
        path = f"/Destiny2/Clan/{group_id}/WeeklyRewardState/"
        return self._get(path)

    def get_item(
        self,
        membership_type: int,
        destiny_membership_id: str,
        item_instance_id: str,
        components: list[int] | None = None
    ) -> Dict[str, Any]:
        """Get detailed information about a specific item (wrapper)."""
        if components is None:
            # Use a broad default, but allow callers to be explicit when they know
            # exactly which components they need.
            components = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320]
        components_str = ",".join(str(c) for c in components)
        return self._get_item(membership_type, destiny_membership_id, item_instance_id, components_str)

    def get_public_milestone_content(self, milestone_hash: int) -> Dict[str, Any]:
        """Get public milestone content."""
        path = f"/Destiny2/Milestones/{milestone_hash}/Content/"
        return self._get(path)

    def get_collectibles(
        self,
        membership_type: int,
        destiny_membership_id: str,
        character_id: str,
        collectible_presentation_node_hash: int
    ) -> Dict[str, Any]:
        """Get collectibles for a character (wrapper)."""
        # The earlier canonical implementation expects components as a string; for
        # this variant, the default in earlier method is already embedded, so we
        # call it with an empty components string to preserve behavior.
        return self._get_collectibles(membership_type, destiny_membership_id, character_id, str(collectible_presentation_node_hash), "")

    def get_post_game_carnage_report(self, activity_id: str) -> Dict[str, Any]:
        """Get post-game carnage report for an activity."""
        path = f"/Destiny2/Stats/PostGameCarnageReport/{activity_id}/"
        return self._get(path)

    def get_activity_history(
        self,
        membership_type: int,
        destiny_membership_id: str,
        character_id: str,
        mode: int | None = None,
        count: int = 25,
        page: int = 0
    ) -> Dict[str, Any]:
        """Get activity history for a character."""
        path = f"/Destiny2/{membership_type}/Account/{destiny_membership_id}/Character/{character_id}/Stats/Activities/"
        params = {"count": count, "page": page}
        if mode is not None:
            params["mode"] = mode
        return self._get(path, params)

    def get_unique_weapon_history(
        self,
        membership_type: int,
        destiny_membership_id: str,
        character_id: str
    ) -> Dict[str, Any]:
        """Get unique weapon history for a character."""
        path = f"/Destiny2/{membership_type}/Account/{destiny_membership_id}/Character/{character_id}/Stats/UniqueWeapons/"
        return self._get(path)

    def get_aggregate_activity_stats(
        self,
        membership_type: int,
        destiny_membership_id: str,
        character_id: str
    ) -> Dict[str, Any]:
        """Get aggregate activity stats for a character."""
        path = f"/Destiny2/{membership_type}/Account/{destiny_membership_id}/Character/{character_id}/Stats/AggregateActivityStats/"
        return self._get(path)
