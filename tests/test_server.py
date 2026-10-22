import importlib


def test_root_endpoint(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "dummy")
    import server

    importlib.reload(server)
    from tests.http_client import request
    response = request(server.app, "GET", "/")
    assert response.status_code == 200
    if server.SERVE_UI:
        assert "text/html" in response.headers["content-type"]
    else:
        assert response.json() == {"detail": "Send POST /chat with {'message': ...}"}


def test_health_without_bungie_key(monkeypatch):
    from tests.http_client import request
    import server

    monkeypatch.delenv("BUNGIE_API_KEY", raising=False)
    importlib.reload(server)
    assert not hasattr(server, "assistant")
    response = request(server.app, "GET", "/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert not hasattr(server, "assistant")


def test_bungie_chat_without_key_returns_503(monkeypatch):
    from tests.http_client import request
    import server

    monkeypatch.delenv("BUNGIE_API_KEY", raising=False)
    importlib.reload(server)
    monkeypatch.setattr(server, "_require_user", lambda _: {"id": 7})
    monkeypatch.setattr(server, "ensure_conversation", lambda *a, **k: None)
    monkeypatch.setattr(server, "append_message", lambda *a, **k: None)
    monkeypatch.setattr(server, "get_bungie_tokens", lambda _: None)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    for message in ("tell me about player foo", "bungie get_manifest"):
        response = request(server.app, "GET", "/chat/stream", params={"message": message, "provider": "ollama"})
        assert response.status_code == 503
        assert response.json() == {
            "detail": "Bungie API key not configured (set BUNGIE_API_KEY)"
        }
