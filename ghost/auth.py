"""Helpers for Bungie.net OAuth authentication."""

from __future__ import annotations

from urllib.parse import urlencode

import base64
import itertools
import json
import os
from pathlib import Path
from typing import Dict

import requests

AUTH_URL = "https://www.bungie.net/en/OAuth/Authorize"
TOKEN_URL = "https://www.bungie.net/Platform/App/OAuth/token/"

# ---------------------------------------------------------------------------
# Token storage

TOKEN_FILE = Path(os.getenv("GHOST_TOKEN_FILE", Path.home() / ".ghost_tokens"))


def _get_key() -> bytes:
    """Return the encryption key derived from ``GHOST_TOKEN_KEY``."""

    key = os.getenv("GHOST_TOKEN_KEY")
    if not key:
        raise RuntimeError("GHOST_TOKEN_KEY environment variable not set")
    # Use SHA256 to produce a 32-byte key for XOR operations
    import hashlib

    return hashlib.sha256(key.encode()).digest()


def _xor(data: bytes, key: bytes) -> bytes:
    """Return ``data`` XOR'ed with ``key`` repeated as necessary."""

    return bytes(a ^ b for a, b in zip(data, itertools.cycle(key)))


def save_tokens(tokens: Dict[str, str]) -> None:
    """Persist tokens to an encrypted file.

    Parameters
    ----------
    tokens:
        Mapping containing ``access_token`` and ``refresh_token``.
    """

    key = _get_key()
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    plaintext = json.dumps(tokens).encode()
    ciphertext = base64.b64encode(_xor(plaintext, key))
    TOKEN_FILE.write_bytes(ciphertext)
    try:  # pragma: no cover - platform dependent
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:  # pragma: no cover - best effort
        pass


def load_tokens() -> Dict[str, str]:
    """Load tokens from the encrypted file if present."""

    if not TOKEN_FILE.exists():
        return {}
    try:
        key = _get_key()
    except RuntimeError:
        return {}
    data = TOKEN_FILE.read_bytes()
    plaintext = _xor(base64.b64decode(data), key)
    return json.loads(plaintext.decode())


# Load tokens at import time so callers can access ``STORED_TOKENS`` directly.
STORED_TOKENS: Dict[str, str] = load_tokens()


def get_authorization_url(
    client_id: str,
    state: str | None = None,
    scopes: list[str] | None = None,
    redirect_uri: str | None = None,
) -> str:
    """Return the user authorization URL.

    Parameters
    ----------
    client_id:
        The application's client identifier.
    state:
        Optional state parameter to include in the authorization request.
    scopes:
        Optional list of OAuth scopes to request.
    redirect_uri:
        Optional redirect URI for the authorization response.
    """

    params: dict[str, str] = {"client_id": client_id, "response_type": "code"}
    if state is not None:
        params["state"] = state
    if scopes:
        params["scope"] = " ".join(scopes)
    if redirect_uri is not None:
        params["redirect_uri"] = redirect_uri
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
