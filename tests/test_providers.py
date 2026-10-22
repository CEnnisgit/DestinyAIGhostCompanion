import logging
from unittest.mock import patch
import pytest
from ghost.providers import Provider, ProviderError, from_headers, redact, RedactionFilter
from ghost.auth import public_exchange
from tests.http_client import request


@pytest.mark.parametrize('name', ['xai', 'openai', 'anthropic', 'openai_compatible', 'ollama', 'local'])
def test_shapes(name):
    p = Provider(name, 'test-key', 'test-model', 'http://localhost:1234/v1')
    with patch('ghost.providers.requests.post') as post:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {'choices': [{'message': {'content': 'ok'}}], 'content': [{'text': 'ok'}], 'message': {'content': 'ok'}}
        assert p.chat([{'role': 'system', 'content': 'sys'}, {'role': 'user', 'content': 'hi'}]) == 'ok'
        args = post.call_args.kwargs
        assert args['json']['model'] == 'test-model'
        assert args['allow_redirects'] is False
        if name == 'anthropic':
            assert post.call_args.args[0].endswith('/messages')
            assert args['json']['system'] == 'sys'
            assert args['headers']['x-api-key'] == 'test-key'
        elif name in ('ollama', 'local'):
            assert post.call_args.args[0].endswith('/api/chat')
        else:
            assert args['headers']['Authorization'] == 'Bearer test-key'


def test_redaction_and_no_persistence(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('XAI_API_KEY', 'env-key')
    monkeypatch.delenv('GHOST_ALLOW_ENV_AI_KEY', raising=False)
    with pytest.raises(ProviderError):
        from_headers({'x-ai-provider': 'xai'})
    p = from_headers({'x-ai-provider': 'openai', 'x-ai-key': 'private-key'})
    with patch('ghost.providers.requests.post', side_effect=RuntimeError('private-key')):
        with pytest.raises(ProviderError) as e:
            p.generate('hi')
        assert 'private-key' not in str(e.value)
        assert e.value.__cause__ is None
        assert e.value.__context__ is None
    assert list(tmp_path.iterdir()) == []
    assert redact('private-key', ['private-key']) == '[REDACTED]'
    record = logging.LogRecord('test', 40, '', 1, 'Authorization: Bearer private-key', (), None)
    RedactionFilter().filter(record)
    assert 'private-key' not in record.getMessage()
    monkeypatch.setenv('GHOST_ALLOW_ENV_AI_KEY', '1')
    assert from_headers({'x-ai-provider': 'xai'})._key == 'env-key'


@pytest.mark.parametrize('url', ['file:///tmp/a', 'ftp://host', 'https://user:password@host', 'https://host?key=abc'])
def test_bad_base_urls(url):
    with pytest.raises(ProviderError):
        Provider('openai', 'key', base_url=url)


def test_public_exchange():
    with patch('ghost.auth.requests.post') as post:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {'access_token': 'atk'}
        public_exchange('id', 'code', 'verifier')
        assert post.call_args.kwargs['data'] == dict(grant_type='authorization_code', client_id='id', code='code', code_verifier='verifier')
        assert 'auth' not in post.call_args.kwargs


def test_ai_test():
    import server
    with patch('ghost.providers.requests.post') as post:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {'choices': [{'message': {'content': 'ok'}}]}
        assert request(server.app, 'POST', '/ai/test', headers={'X-AI-Provider': 'openai', 'X-AI-Key': 'test-key'}).json() == {'ok': True}
    r = request(server.app, 'POST', '/ai/test', headers={'X-AI-Provider': 'openai'})
    assert r.json()['ok'] is False


def test_bungie_header(monkeypatch):
    import server
    monkeypatch.delenv('BUNGIE_API_KEY', raising=False)
    monkeypatch.setattr(server, '_require_user', lambda _: {'id': 1})
    monkeypatch.setattr(server, 'get_bungie_tokens', lambda _: None)
    with patch('server.GhostAssistant') as assistant:
        assistant.return_value.chat.return_value = 'ok'
        assert request(server.app, 'POST', '/chat', headers={'X-Bungie-API-Key': 'device-key'}, json={'message': 'hi'}).status_code == 200
        assistant.assert_called_once_with(api_key='device-key')


def test_request_log_filter_redacts_raw_key():
    from ghost.providers import request_secrets
    marker = request_secrets.set(('raw-private-key',))
    try:
        record = logging.LogRecord('test', 40, '', 1, 'upstream failed: %s', ('raw-private-key',), None)
        RedactionFilter().filter(record)
        assert 'raw-private-key' not in record.getMessage()
    finally:
        request_secrets.reset(marker)


def test_chat_key_never_reaches_shared_assistant_or_storage(monkeypatch):
    import server
    monkeypatch.setattr(server, '_require_user', lambda _: {'id': 1})
    monkeypatch.setattr(server, 'get_bungie_tokens', lambda _: None)
    with patch('ghost.providers.requests.post') as post, patch('server.append_message') as save:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {'choices': [{'message': {'content': 'hi'}}]}
        r = request(server.app, 'POST', '/chat', headers={'X-AI-Provider': 'openai', 'X-AI-Key': 'request-only-key'}, json={'message': 'hello'})
        assert r.status_code == 200
        assert 'request-only-key' not in r.text
        save.assert_not_called()
        assert not hasattr(server, 'assistant')


def test_stream_uses_request_credentials(monkeypatch):
    import server
    monkeypatch.setattr(server, '_require_user', lambda _: {'id': 1})
    monkeypatch.setattr(server, 'get_bungie_tokens', lambda _: None)
    with patch('ghost.providers.requests.post') as post, patch('server.append_message') as save, patch('server.ensure_conversation'):
        post.return_value.status_code = 200
        post.return_value.json.return_value = {'choices': [{'message': {'content': 'echo stream-private-key'}}]}
        r = request(server.app, 'GET', '/chat/stream', params={'message': 'hello'}, headers={'X-AI-Provider': 'openai', 'X-AI-Model': 'chosen-model', 'X-AI-Key': 'stream-private-key'})
        assert r.status_code == 200
        assert r.text == 'echo [REDACTED]'
        assert post.call_args.kwargs['json']['model'] == 'chosen-model'
        assert 'stream-private-key' not in repr(save.call_args_list)
        assert not hasattr(server, 'assistant')
