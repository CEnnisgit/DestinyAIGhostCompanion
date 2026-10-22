from unittest.mock import patch
import importlib
from urllib.parse import parse_qs, urlparse

from tests.http_client import request


def test_oauth_authorize(monkeypatch):
    monkeypatch.setenv("BUNGIE_CLIENT_ID", "123")
    import server

    importlib.reload(server)
    response = request(server.app, "GET", "/oauth/authorize")
    assert response.status_code == 200
    result = response.json()
    query = parse_qs(urlparse(result["authorization_url"]).query)
    assert query == {
        "client_id": ["123"],
        "response_type": ["code"],
        "redirect_uri": ["http://testserver/oauth/callback"],
    }
    assert result["redirect_uri"] == "http://testserver/oauth/callback"


def test_oauth_callback(monkeypatch):
    monkeypatch.setenv("BUNGIE_CLIENT_ID", "id")
    monkeypatch.setenv("BUNGIE_CLIENT_SECRET", "secret")
    monkeypatch.delenv("BUNGIE_API_KEY", raising=False)
    import server

    importlib.reload(server)
    tokens = {"access_token": "atk", "refresh_token": "rtk"}
    landing = request(server.app, "GET", "/oauth/callback", params={"code": "abc"})
    assert landing.status_code == 200
    assert '"code":"abc"' in landing.text
    assert "fetch('/oauth/callback'" in landing.text
    with patch("server.exchange_code_for_token", return_value=tokens) as exchange, \
        patch("server.get_user_by_email", return_value={"id": 7}), \
        patch("server.upsert_bungie_tokens") as save, \
        patch("server.create_jwt", return_value="session-token") as jwt:
        result = request(server.app, "POST", "/oauth/callback", json={"code": "abc"})
        assert result.status_code == 200
        assert result.json() == {"ok": True, "token": "session-token", "bungie_linked": True}
        exchange.assert_called_once_with("id", "secret", "abc")
        save.assert_called_once()
        uid, stored = save.call_args.args
        assert uid == 7
        assert stored["access_token"] == "atk"
        assert stored["refresh_token"] == "rtk"
        jwt.assert_called_once_with(7, "desktop@local")
