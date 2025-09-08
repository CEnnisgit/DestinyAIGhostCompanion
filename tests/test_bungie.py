import os
from unittest.mock import patch, Mock

import pytest

from ghost.bungie import BungieClient, BungieAPIError


def make_response(
    json_data, headers=None, status_code=200, json_exc: Exception | None = None
):
    """Construct a mock response object for testing."""

    resp = Mock()
    if json_exc is not None:
        resp.json.side_effect = json_exc
    else:
        resp.json.return_value = json_data
    resp.headers = headers or {}
    resp.status_code = status_code
    return resp


def test_get_raises_on_error_code():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({"ErrorCode": 2, "Message": "Bad"})
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._get("/foo")


def test_get_raises_on_rate_limit():
    headers = {"X-RateLimit-Remaining": "0"}
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({"ErrorCode": 1}, headers)
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._get("/foo")


def test_get_sleeps_when_retry_after():
    headers = {"Retry-After": "5"}
    with patch("ghost.bungie.requests.Session.get") as mock_get, patch("ghost.bungie.time.sleep") as mock_sleep:
        mock_get.return_value = make_response({"ErrorCode": 1}, headers)
        client = BungieClient("key")
        result = client._get("/foo")
        mock_sleep.assert_called_once_with(5)
        assert result["ErrorCode"] == 1


def test_user_agent_header(monkeypatch):
    monkeypatch.setenv("BUNGIE_APP_NAME", "TestApp")
    monkeypatch.setenv("BUNGIE_APP_VERSION", "1.2")
    monkeypatch.setenv("BUNGIE_APP_URL", "https://example.test")
    client = BungieClient("key")
    assert (
        client.session.headers["User-Agent"]
        == "TestApp/1.2 (+https://example.test)"
    )


def test_get_raises_on_http_error():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({}, status_code=503)
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._get("/foo")


def test_get_raises_on_invalid_json():
    with patch("ghost.bungie.requests.Session.get") as mock_get:
        mock_get.return_value = make_response({}, json_exc=ValueError("boom"))
        client = BungieClient("key")
        with pytest.raises(BungieAPIError):
            client._get("/foo")
