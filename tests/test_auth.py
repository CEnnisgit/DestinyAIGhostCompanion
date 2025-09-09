import pytest
from unittest.mock import patch, Mock

from ghost.auth import TOKEN_URL, get_authorization_url, exchange_code_for_token, refresh_token
from ghost.bungie import BungieClient


def make_response(data):
    resp = Mock()
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


def test_get_authorization_url():
    url = get_authorization_url("123", state="abc", scopes=["ReadBasicUserProfile"])
    assert (
        url
        == "https://www.bungie.net/en/OAuth/Authorize?client_id=123&response_type=code&state=abc&scope=ReadBasicUserProfile"
    )


def test_exchange_code_for_token():
    tokens = {"access_token": "atk", "refresh_token": "rtk"}
    with patch("ghost.auth.requests.post") as mock_post:
        mock_post.return_value = make_response(tokens)
        result = exchange_code_for_token("id", "secret", "code")
        assert result == tokens
        mock_post.assert_called_once_with(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": "code",
                "client_id": "id",
                "client_secret": "secret",
            },
        )


def test_refresh_token():
    tokens = {"access_token": "new_atk", "refresh_token": "new_rtk"}
    with patch("ghost.auth.requests.post") as mock_post:
        mock_post.return_value = make_response(tokens)
        result = refresh_token("id", "secret", "rtk")
        assert result == tokens
        mock_post.assert_called_once_with(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": "rtk",
                "client_id": "id",
                "client_secret": "secret",
            },
        )


def test_bungie_client_authenticate_user():
    client = BungieClient("key")
    client.authenticate_user({"access_token": "atk", "refresh_token": "rtk"})
    assert client.access_token == "atk"
    assert client.refresh_token == "rtk"
    assert client.session.headers["Authorization"] == "Bearer atk"
