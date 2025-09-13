from unittest.mock import patch
import importlib
from urllib.parse import unquote


def test_oauth_authorize(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "dummy")
    monkeypatch.setenv("BUNGIE_CLIENT_ID", "123")
    redirect = "https://example.com/callback"
    monkeypatch.setenv("BUNGIE_REDIRECT_URI", redirect)
    import server

    importlib.reload(server)
    from ghost import auth

    expected = auth.get_authorization_url("123", redirect_uri=redirect)
    result = server.oauth_authorize()
    assert result == {"authorization_url": expected}
    assert redirect in unquote(result["authorization_url"])


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
