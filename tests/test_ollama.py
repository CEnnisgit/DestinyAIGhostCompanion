from tests.stubs import requests, responses
import pytest

from ghost.ollama import OllamaClient, OllamaError


@responses.activate
def test_generate_success(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://example")
    monkeypatch.setenv("OLLAMA_MODEL", "m1")
    responses.add(
        responses.POST,
        "http://example/api/generate",
        json={"response": "hi"},
    )
    client = OllamaClient()
    assert client.generate("hello") == "hi"


@responses.activate
def test_generate_http_error(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://example")
    monkeypatch.setenv("OLLAMA_MODEL", "m1")
    responses.add(
        responses.POST,
        "http://example/api/generate",
        json={"response": "bad"},
        status=500,
    )
    client = OllamaClient()
    with pytest.raises(OllamaError):
        client.generate("hello")


@responses.activate
def test_generate_connection_error(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://example")
    monkeypatch.setenv("OLLAMA_MODEL", "m1")
    responses.add(
        responses.POST,
        "http://example/api/generate",
        body=requests.RequestException("boom"),
    )
    client = OllamaClient()
    with pytest.raises(OllamaError):
        client.generate("hello")
