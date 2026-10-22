import asyncio
import importlib

import pytest
from tests.http_client import request


@pytest.fixture
def server(monkeypatch, tmp_path):
    import server as module
    import server_db
    monkeypatch.setenv('GHOST_MODE', 'hosted')
    monkeypatch.setenv('JWT_SECRET', 'unit-test-only-signing-key-with-32-characters')
    monkeypatch.setenv('GHOST_UI_ORIGINS', 'https://ghost.example')
    monkeypatch.setattr(server_db, 'DB_PATH', tmp_path / 'test.db')
    server_db.init_db()
    importlib.reload(module)
    yield module
    monkeypatch.setenv('GHOST_MODE', 'desktop')
    importlib.reload(module)


def test_headers_cors_and_paths(server):
    r = request(server.app, 'GET', '/health', headers={'Origin': 'https://ghost.example'})
    assert 'log' not in r.json()
    assert r.headers['access-control-allow-origin'] == 'https://ghost.example'
    assert r.headers['strict-transport-security'].startswith('max-age=')
    assert r.headers['x-frame-options'] == 'DENY'
    assert r.headers['x-content-type-options'] == 'nosniff'
    assert r.headers['referrer-policy'] == 'strict-origin-when-cross-origin'
    assert "frame-ancestors 'none'" in r.headers['content-security-policy']
    r = request(server.app, 'OPTIONS', '/chat', headers={'Origin': 'https://evil.example', 'Access-Control-Request-Method': 'POST'})
    assert r.status_code == 400
    assert 'access-control-allow-origin' not in r.headers
    assert r.headers['x-frame-options'] == 'DENY'
    r = request(server.app, 'OPTIONS', '/chat', headers={'Origin': 'https://ghost.example', 'Access-Control-Request-Method': 'POST'})
    assert r.status_code == 200


def test_wildcard_cors_rejected(server, monkeypatch):
    monkeypatch.setenv('GHOST_UI_ORIGINS', '*')
    with pytest.raises(RuntimeError, match='explicit origins'):
        importlib.reload(server)
    monkeypatch.setenv('GHOST_UI_ORIGINS', 'https://ghost.example')
    importlib.reload(server)


def test_size_limit_including_chunked(server, monkeypatch):
    monkeypatch.setenv('GHOST_MAX_BODY_BYTES', '32')
    r = request(server.app, 'POST', '/oauth/callback', content=b'x' * 33, headers={'Origin':'https://ghost.example'})
    assert r.status_code == 413
    assert r.headers['access-control-allow-origin'] == 'https://ghost.example'
    async def body():
        yield b'x' * 20
        yield b'x' * 20
    assert request(server.app, 'POST', '/oauth/callback', content=body()).status_code == 413


def test_rate_limit(server, monkeypatch):
    monkeypatch.setenv('GHOST_RATE_CAPACITY', '1')
    monkeypatch.setenv('GHOST_RATE_REFILL_PER_SECOND', '.001')
    assert request(server.app, 'GET', '/personas').status_code == 200
    assert request(server.app, 'GET', '/personas').status_code == 429
    assert request(server.app, 'GET', '/health').status_code == 200


def test_rate_limit_per_authenticated_user(server, monkeypatch):
    import server_db
    from server_auth import create_jwt
    monkeypatch.setenv('GHOST_RATE_CAPACITY', '1')
    monkeypatch.setenv('GHOST_RATE_REFILL_PER_SECOND', '.001')
    for name in ('one', 'two'):
        uid = server_db.create_user(name, 'unused')
        headers = {'Authorization': 'Bearer ' + create_jwt(uid, name)}
        assert request(server.app, 'GET', '/personas', headers=headers).status_code == 200
        assert request(server.app, 'GET', '/personas', headers=headers).status_code == 429


@pytest.mark.parametrize('method,path', [('POST','/stt'), ('POST','/stt/local'), ('GET','/stt/health'), ('GET','/diagnostics/audio'), ('POST','/finetune'), ('GET','/local/secrets'), ('GET','/models'), ('GET','/voices'), ('POST','/ai/test')])
def test_local_features_gated(server, method, path):
    assert request(server.app, method, path).status_code == 403


def test_provider_urls_and_tokens(server, monkeypatch):
    from ghost import auth
    from ghost.assistant import GhostAssistant
    from ghost.providers import Provider, ProviderError
    monkeypatch.setattr(auth, 'STORED_TOKENS', {'access_token': 'other-user'})
    assert GhostAssistant()._current_tokens is None
    assert auth.load_tokens() == {}
    with pytest.raises(RuntimeError):
        auth.save_tokens({'access_token': 'no-file'})
    for name, url in [('ollama', ''), ('openai', 'http://127.0.0.1:8000'), ('openai', 'https://evil.example')]:
        with pytest.raises(ProviderError):
            Provider(name, 'fake', base_url=url)


def test_conversation_ownership_and_tokens(server):
    import server_db as db
    from server_auth import create_jwt
    one = db.create_user('one', 'unused')
    two = db.create_user('two', 'unused')
    db.ensure_conversation('shared-id', one, 'private', 'openai')
    db.append_message('shared-id', 'm1', 'user', 'private message')
    db.upsert_bungie_tokens(one, {'access_token': 'one-token'})
    assert db.get_bungie_tokens(two) is None
    with pytest.raises(PermissionError):
        db.ensure_conversation('shared-id', two, 'intruder', 'openai')
    h = {'Authorization': 'Bearer ' + create_jwt(two, 'two'), 'X-AI-Provider': 'openai'}
    assert request(server.app, 'GET', '/conversations/shared-id', headers=h).json()['messages'] == []
    assert request(server.app, 'GET', '/chat/stream', headers=h, params={'message': 'inject', 'session_id': 'shared-id'}).status_code == 403
    assert len(db.get_conversation_messages('shared-id', one)) == 1


def test_oauth_users_are_distinct(server, monkeypatch):
    import server_db as db
    monkeypatch.setattr(server, '_consume_oauth', lambda *a: ('verifier','cid','redirect',0,'origin'))
    for member in ('one', 'two'):
        monkeypatch.setattr(server, 'public_exchange', lambda *a, m=member: {'membership_id': m, 'access_token': m})
        r = request(server.app, 'POST', '/oauth/callback', json={})
        assert r.status_code == 200
    one, two = db.get_user_by_email('bungie:one'), db.get_user_by_email('bungie:two')
    assert one['id'] != two['id']
    assert db.get_bungie_tokens(one['id'])['access_token'] == 'one'
    assert db.get_bungie_tokens(two['id'])['access_token'] == 'two'


def test_lifespan(server, monkeypatch):
    calls = []
    monkeypatch.setattr(server, 'init_db', lambda: calls.append('db'))
    monkeypatch.setattr(server, '_ensure_ollama_on_startup', lambda: calls.append('ollama'))
    async def run():
        async with server.app.router.lifespan_context(server.app):
            assert calls == ['db']
        monkeypatch.setenv('GHOST_MODE', 'desktop')
        async with server.app.router.lifespan_context(server.app):
            assert calls == ['db', 'db', 'ollama']
        monkeypatch.setenv('GHOST_MODE', 'hosted')
        monkeypatch.delenv('JWT_SECRET')
        with pytest.raises(RuntimeError, match='JWT_SECRET'):
            async with server.app.router.lifespan_context(server.app):
                pass
    asyncio.run(run())


def test_request_assistants_are_isolated(server, monkeypatch):
    from ghost.assistant import GhostAssistant
    clients = []
    class FakeProvider:
        def generate(self, prompt):
            return 'OK'
        def generate_with_system(self, system, prompt):
            return 'OK'
    class ObservedAssistant(GhostAssistant):
        def chat(self, message, provider=None, tokens=None, **kwargs):
            clients.append((self, self._clients['request'], tokens))
            self._bucket_loc_cache[1] = message
            return message
    monkeypatch.setattr(server, 'GhostAssistant', ObservedAssistant)
    monkeypatch.setattr(server, 'from_headers', lambda _: FakeProvider())
    monkeypatch.setattr(server, '_require_user', lambda auth: {'id': int(auth)})
    monkeypatch.setattr(server, 'get_bungie_tokens', lambda uid: {'access_token': f'token-{uid}'})
    for uid in (1, 2):
        r = request(server.app, 'POST', '/chat', headers={'Authorization': str(uid), 'X-AI-Provider':'openai'}, json={'message': str(uid)})
        assert r.json() == {'reply': str(uid)}
    assert clients[0][0] is not clients[1][0]
    assert clients[0][1] is not clients[1][1]
    assert clients[0][2] != clients[1][2]
    assert clients[0][0]._bucket_loc_cache == {1: '1'}
    assert clients[1][0]._bucket_loc_cache == {1: '2'}


def test_hosted_does_not_load_local_caches(server, monkeypatch, tmp_path):
    from ghost.bungie import BungieClient
    from ghost import lore
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(lore, '_DOCS', [('private-path', 'private text')])
    assert lore.search('private') == []
    first = BungieClient('fake')
    second = BungieClient('fake')
    first._profile_cache['private'] = 'private'
    assert second._profile_cache == {}
    assert not (tmp_path / 'cache').exists()
