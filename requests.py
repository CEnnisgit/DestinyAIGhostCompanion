"""Lightweight stand-in for the real :mod:`requests` library.

Only the minimal ``Session`` API used by the tests is implemented.
The ``get`` method intentionally raises :class:`NotImplementedError` because
network access is not available in the execution environment.
"""


class Session:
    """Minimal stub of :class:`requests.Session` for tests."""

    def __init__(self) -> None:
        self.headers = {}

    def get(self, *args, **kwargs):
        raise NotImplementedError("Network access is not available in tests")
