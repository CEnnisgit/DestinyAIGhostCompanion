"""Helpers for Bungie.net OAuth authentication."""

from __future__ import annotations

from urllib.parse import urlencode

import requests

AUTH_URL = "https://www.bungie.net/en/OAuth/Authorize"
TOKEN_URL = "https://www.bungie.net/Platform/App/OAuth/token/"


def get_authorization_url(client_id: str, state: str | None = None, scopes: list[str] | None = None) -> str:
    """Return the user authorization URL.

    Parameters
    ----------
    client_id:
        The application's client identifier.
    state:
        Optional state parameter to include in the authorization request.
    scopes:
        Optional list of OAuth scopes to request.
    """

    params: dict[str, str] = {"client_id": client_id, "response_type": "code"}
    if state is not None:
        params["state"] = state
    if scopes:
        params["scope"] = " ".join(scopes)
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(client_id: str, client_secret: str, code: str) -> dict:
    """Exchange an authorization ``code`` for OAuth tokens."""

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    resp = requests.post(TOKEN_URL, data=payload)
    resp.raise_for_status()
    return resp.json()


def refresh_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    """Refresh an access token using ``refresh_token``."""

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    resp = requests.post(TOKEN_URL, data=payload)
    resp.raise_for_status()
    return resp.json()
