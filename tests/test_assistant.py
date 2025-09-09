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
