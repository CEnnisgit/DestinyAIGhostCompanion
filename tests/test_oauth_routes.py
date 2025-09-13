from unittest.mock import patch
import importlib


def test_oauth_authorize(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "dummy")
    monkeypatch.setenv("BUNGIE_CLIENT_ID", "123")
    import server

    importlib.reload(server)
    from ghost import auth

    expected = auth.get_authorization_url("123")
    assert server.oauth_authorize() == {"authorization_url": expected}


def test_oauth_callback(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "dummy")
    monkeypatch.setenv("BUNGIE_CLIENT_ID", "id")
    monkeypatch.setenv("BUNGIE_CLIENT_SECRET", "secret")
    import server

    importlib.reload(server)
    tokens = {"access_token": "atk", "refresh_token": "rtk"}
    with patch("server.auth.exchange_code_for_token") as mock_exchange, patch(
        "server.auth.save_tokens"
    ) as mock_save:
        mock_exchange.return_value = tokens
        result = server.oauth_callback(code="abc")
        assert result == tokens
        mock_exchange.assert_called_once_with("id", "secret", "abc")
        mock_save.assert_called_once_with(tokens)
