from unittest.mock import Mock

from ghost.assistant import GhostAssistant


def test_chat_calls_bungie_for_player_request():
    bungie = Mock()
    bungie.search_destiny_player.return_value = {"Response": {}}
    ollama = Mock()
    ollama.generate.return_value = "ok"
    assistant = GhostAssistant(bungie_client=bungie, ollama_client=ollama)

    result = assistant.chat("tell me about player foo")
    assert result == "ok"
    bungie.search_destiny_player.assert_called_once_with(0, "foo")
    assert ollama.generate.called


def test_chat_without_player_uses_ollama_only():
    bungie = Mock()
    ollama = Mock()
    ollama.generate.return_value = "hi"
    assistant = GhostAssistant(bungie_client=bungie, ollama_client=ollama)

    result = assistant.chat("hello")
    assert result == "hi"
    bungie.search_destiny_player.assert_not_called()
    ollama.generate.assert_called_once_with("hello")


def test_tokens_applied_when_present(monkeypatch):
    tokens = {"access_token": "abc"}
    monkeypatch.setattr("ghost.auth.STORED_TOKENS", tokens)
    bungie = Mock()
    ollama = Mock()
    GhostAssistant(bungie_client=bungie, ollama_client=ollama)
    bungie.authenticate_user.assert_called_once_with(tokens)


def test_bungie_is_lazy_and_retries_after_configuration(monkeypatch):
    import pytest
    from ghost.assistant import BungieConfigError
    from unittest.mock import patch

    monkeypatch.delenv("BUNGIE_API_KEY", raising=False)
    tokens = {"access_token": "test-token"}
    monkeypatch.setattr("ghost.auth.STORED_TOKENS", tokens)
    with patch("ghost.assistant.BungieClient") as factory:
        assistant = GhostAssistant()
        factory.assert_not_called()
        with pytest.raises(BungieConfigError, match="Bungie API key not configured"):
            _ = assistant.bungie
        factory.assert_not_called()
        monkeypatch.setenv("BUNGIE_API_KEY", "test-key")
        assert assistant.bungie is factory.return_value
        assert assistant.bungie is factory.return_value
        factory.assert_called_once_with("test-key")
        factory.return_value.authenticate_user.assert_called_once_with(tokens)
