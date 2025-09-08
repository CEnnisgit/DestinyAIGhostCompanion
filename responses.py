"""Minimal stub of the :mod:`responses` library used in tests.

This implementation is intentionally tiny and only provides the features
required for the unit tests in this kata.  It allows registering expected
``POST`` calls and will patch :func:`requests.post` to return mocked responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Tuple

import requests

POST = "POST"


@dataclass
class _Entry:
    method: str
    url: str
    json: Any = None
    status: int = 200
    body: Any | None = None


class _Responses:
    def __init__(self) -> None:
        self._entries: List[_Entry] = []
        self.calls: List[Tuple[str, str]] = []

    def add(self, method: str, url: str, *, json: Any | None = None, status: int = 200, body: Any | None = None) -> None:
        self._entries.append(_Entry(method, url, json=json, status=status, body=body))

    def __enter__(self) -> "_Responses":
        self._orig = requests.post

        def _mock_post(url: str, *, json: Any | None = None, **kwargs: Any) -> Any:
            for entry in self._entries:
                if entry.method == POST and entry.url == url:
                    self.calls.append((entry.method, url))
                    if isinstance(entry.body, Exception):
                        raise entry.body
                    return SimpleNamespace(status_code=entry.status, json=lambda: entry.json)
            raise requests.RequestException(f"No response mocked for {url}")

        requests.post = _mock_post
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        requests.post = self._orig

_ACTIVE: _Responses | None = None


def activate(func: Callable) -> Callable:
    """Decorator emulating :func:`responses.activate`."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        global _ACTIVE
        with _Responses() as rsps:
            _ACTIVE = rsps
            try:
                return func(*args, **kwargs)
            finally:
                _ACTIVE = None

    return wrapper


def add(method: str, url: str, *, json: Any | None = None, status: int = 200, body: Any | None = None) -> None:
    if _ACTIVE is None:
        raise RuntimeError("responses.add called outside activate context")
    _ACTIVE.add(method, url, json=json, status=status, body=body)
