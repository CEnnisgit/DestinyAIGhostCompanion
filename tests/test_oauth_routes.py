from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
import hashlib
import base64
from tests.http_client import request


def authorize(monkeypatch):
    import server
    monkeypatch.setenv('BUNGIE_CLIENT_ID', '123')
    r = request(server.app, 'GET', '/oauth/authorize')
    q = parse_qs(urlparse(r.json()['authorization_url']).query)
    state = q['state'][0]
    return server, state, {'cookie': 'ghost_oauth_state=' + state}, q


def test_oauth_authorize(monkeypatch):
    server, state, headers, q = authorize(monkeypatch)
    verifier = server._oauth_attempts[state][0]
    assert q['code_challenge_method'] == ['S256']
    assert q['code_challenge'] == [base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')]
    assert 43 <= len(verifier) <= 128


def test_oauth_callback(monkeypatch):
    server, state, headers, q = authorize(monkeypatch)
    monkeypatch.delenv('GHOST_BUNGIE_TOKEN_PROXY', raising=False)
    with patch('server.public_exchange', return_value={'access_token': 'atk'}) as exchange, patch('server.get_user_by_email', return_value={'id': 7}), patch('server.upsert_bungie_tokens'), patch('server.create_jwt', return_value='jwt'):
        r = request(server.app, 'POST', '/oauth/callback', headers=headers, json={'code': 'abc', 'state': state})
        assert r.status_code == 200
        assert exchange.call_args.args[-1] is None
        assert request(server.app, 'POST', '/oauth/callback', headers=headers, json={'code': 'abc', 'state': state}).status_code == 400


def test_state_mismatch(monkeypatch):
    server, state, headers, _ = authorize(monkeypatch)
    assert request(server.app, 'POST', '/oauth/callback', headers=headers, json={'code': 'abc', 'state': 'wrong'}).status_code == 400


def test_proxy(monkeypatch):
    server, state, headers, _ = authorize(monkeypatch)
    monkeypatch.delenv('GHOST_BUNGIE_TOKEN_PROXY', raising=False)
    assert request(server.app, 'POST', '/oauth/token', json={}).status_code == 404
    assert request(server.app, 'POST', '/oauth/refresh', json={}).status_code == 404
    monkeypatch.setenv('GHOST_BUNGIE_TOKEN_PROXY', '1')
    monkeypatch.setenv('BUNGIE_CLIENT_SECRET', 'private-secret')
    with patch('ghost.auth.requests.post') as post:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {'access_token': 'atk', 'client_secret': 'private-secret'}
        r = request(server.app, 'POST', '/oauth/token', headers=headers, json={'code': 'abc', 'state': state})
        assert r.status_code == 200
        assert post.call_args.kwargs['data']['client_secret'] == 'private-secret'
        assert 'private-secret' not in r.text
        r = request(server.app, 'POST', '/oauth/refresh', json={'refresh_token': 'rt'})
        assert r.status_code == 200
        assert post.call_args.kwargs['data']['client_secret'] == 'private-secret'


def test_native_redirect_and_session_binding(monkeypatch):
    import server
    monkeypatch.setenv('BUNGIE_CLIENT_ID', '123')
    monkeypatch.setattr(server, 'UI_ORIGINS', ['capacitor://localhost'])
    headers = {'origin': 'capacitor://localhost'}
    response = request(server.app, 'GET', '/oauth/authorize?redirect_uri=ghostcompanion://oauth/callback', headers=headers)
    assert response.status_code == 200
    data = response.json()
    query = parse_qs(urlparse(data['authorization_url']).query)
    assert query['redirect_uri'] == ['ghostcompanion://oauth/callback']
    assert query['code_challenge_method'] == ['S256']
    payload = {'code': 'abc', 'state': query['state'][0], 'native_session': data['native_session']}
    assert request(server.app, 'POST', '/oauth/callback', headers=headers, json={**payload, 'native_session': 'wrong'}).status_code == 400
    assert request(server.app, 'POST', '/oauth/callback', json=payload).status_code == 400
    verifier = server._oauth_attempts[payload['state']][0]
    assert server._oauth_attempts[payload['state']][2] == 'ghostcompanion://oauth/callback'
    with patch('server.public_exchange', return_value={'access_token': 'atk'}) as exchange, patch('server.get_user_by_email', return_value={'id': 7}), patch('server.upsert_bungie_tokens'), patch('server.create_jwt', return_value='jwt'):
        monkeypatch.delenv('GHOST_BUNGIE_TOKEN_PROXY', raising=False)
        assert request(server.app, 'POST', '/oauth/callback', headers=headers, json=payload).status_code == 200
        assert exchange.call_args.args[2] == verifier
        assert exchange.call_args.args[-1] is None
        assert request(server.app, 'POST', '/oauth/callback', headers=headers, json=payload).status_code == 400


def test_native_redirect_rejects_other_targets(monkeypatch):
    import server
    monkeypatch.setenv('BUNGIE_CLIENT_ID', '123')
    assert request(server.app, 'GET', '/oauth/authorize?redirect_uri=evil://callback').status_code == 400
    monkeypatch.setattr(server, 'UI_ORIGINS', [])
    assert request(server.app, 'GET', '/oauth/authorize?redirect_uri=ghostcompanion://oauth/callback', headers={'origin': 'capacitor://localhost'}).status_code == 400
