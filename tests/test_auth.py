import pytest
from unittest.mock import patch, Mock

import ghost.auth as auth
from ghost.bungie import BungieClient


def make_response(data):
    resp = Mock()
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


def test_get_authorization_url():
    url = auth.get_authorization_url("123", state="abc", scopes=["ReadBasicUserProfile"])
    assert (
        url
        == "https://www.bungie.net/en/OAuth/Authorize?client_id=123&response_type=code&state=abc&scope=ReadBasicUserProfile"
    )


def test_exchange_code_for_token():
    tokens = {"access_token": "atk", "refresh_token": "rtk"}
    with patch("ghost.auth.requests.post") as mock_post:
        mock_post.return_value = make_response(tokens)
        result = auth.exchange_code_for_token("id", "secret", "code")
        assert result == tokens
        mock_post.assert_called_once_with(
            auth.TOKEN_URL,
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
        result = auth.refresh_token("id", "secret", "rtk")
        assert result == tokens
        mock_post.assert_called_once_with(
            auth.TOKEN_URL,
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


def test_token_storage(tmp_path, monkeypatch):
    token_file = tmp_path / "tokens.dat"
    monkeypatch.setenv("GHOST_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("GHOST_TOKEN_KEY", "secret")

    import importlib

    auth_module = importlib.reload(auth)
    auth_module.save_tokens({"access_token": "atk", "refresh_token": "rtk"})

    data = token_file.read_bytes()
    assert b"atk" not in data and b"rtk" not in data

    tokens = auth_module.load_tokens()
    assert tokens["access_token"] == "atk"
    assert tokens["refresh_token"] == "rtk"

    auth_module = importlib.reload(auth)
    assert auth_module.STORED_TOKENS["access_token"] == "atk"
