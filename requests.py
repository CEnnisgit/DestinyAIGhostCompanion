"""Lightweight stand-in for the real :mod:`requests` library.

Only a sliver of the ``requests`` interface is required for the unit tests in
this kata.  The functions provided here intentionally raise
``NotImplementedError`` to prevent accidental network access, while still being
patchable by tests.
"""


class RequestException(Exception):
    """Base exception matching ``requests``'s API."""


class Session:
    """Minimal stub of :class:`requests.Session` for tests."""

    def __init__(self) -> None:
        self.headers = {}

    def get(self, *args, **kwargs):  # pragma: no cover - exercised via mocks
        raise NotImplementedError("Network access is not available in tests")

    def post(self, *args, **kwargs):  # pragma: no cover - exercised via mocks
        raise NotImplementedError("Network access is not available in tests")


def post(*args, **kwargs):  # pragma: no cover - exercised via mocks
    """Module level convenience function mirroring :func:`requests.post`."""
    raise NotImplementedError("Network access is not available in tests")


class Response:  # pragma: no cover - convenience for mocks
    """Very small Response object used by tests when mocking requests."""

    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json
