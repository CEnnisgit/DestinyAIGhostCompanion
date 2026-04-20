from unittest.mock import Mock, patch
import pytest

from ghost.bungie import BungieClient


def make_response(json_data, headers=None, status_code=200):
    resp = Mock()
    resp.json.return_value = json_data
    resp.headers = headers or {}
    resp.status_code = status_code
    return resp


def test_retry_after_delays_next_request():
    headers = {"Retry-After": "2"}
    with patch("ghost.bungie.requests.Session.get") as mock_get, patch(
        "ghost.bungie.time.sleep"
    ) as mock_sleep:
        mock_get.side_effect = [
            make_response({"ErrorCode": 1}, headers),
            make_response({"ErrorCode": 1}, {}),
        ]
        client = BungieClient("key")
        client._get("/foo")
        client._get("/foo")
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args.args[0] == pytest.approx(2, abs=0.1)


def test_manifest_cache_ttl_expires():
    data = {"ErrorCode": 1, "Response": {}}
    times = iter([0, 0, 0, 0, 0, 10, 10, 10, 10])
    with patch("ghost.bungie.requests.Session.get") as mock_get, patch(
        "ghost.bungie.time.time", side_effect=lambda: next(times)
    ):
        mock_get.return_value = make_response(data)
        client = BungieClient("key", manifest_ttl=5)
        client.get_manifest()
        client.get_manifest()
        client.get_manifest()
        assert mock_get.call_count == 2


def test_profile_cache_ttl_expires():
    data = {"ErrorCode": 1, "Response": {}}
    times = iter([0, 0, 0, 0, 0, 10, 10, 10, 10])
    with patch("ghost.bungie.requests.Session.get") as mock_get, patch(
        "ghost.bungie.time.time", side_effect=lambda: next(times)
    ):
        mock_get.return_value = make_response(data)
        client = BungieClient("key", profile_ttl=5)
        client.get_profile(1, "123", "100")
        client.get_profile(1, "123", "100")
        client.get_profile(1, "123", "100")
        assert mock_get.call_count == 2
