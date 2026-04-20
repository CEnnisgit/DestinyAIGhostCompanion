import importlib


def test_root_endpoint(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "dummy")
    import server

    importlib.reload(server)
    assert server.root() == {"detail": "Send POST /chat with {'message': ...}"}

