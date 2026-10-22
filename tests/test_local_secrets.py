import asyncio
from types import SimpleNamespace
import httpx
import pytest
from ghost import local_secrets


@pytest.fixture
def local(monkeypatch):
    import server
    monkeypatch.setenv('GHOST_MODE', 'desktop')
    values = {}
    fake = SimpleNamespace(get_keyring=lambda: SimpleNamespace(priority=1),
        get_password=lambda service, name: values.get((service, name)),
        set_password=lambda service, name, value: values.__setitem__((service, name), value),
        delete_password=lambda service, name: values.pop((service, name)))
    monkeypatch.setattr(local_secrets, 'keyring', fake)
    def call(method, path, host='127.0.0.1', **kwargs):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app, client=(host, 50000)), base_url='http://127.0.0.1:8000') as c:
                return await c.request(method, path, **kwargs)
        return asyncio.run(run())
    return call, values


def test_keyring_roundtrip(local):
    call, values = local
    assert call('GET', '/config').json() == {'mode': 'desktop', 'keyring_available': True}
    assert call('PUT', '/local/secrets', json={'key':'fake-ai','bungieKey':'fake-bungie'}).status_code == 200
    assert values[('ghost-companion', 'key')] == 'fake-ai'
    r = call('GET', '/local/secrets')
    assert r.json() == {'key':'fake-ai','bungieKey':'fake-bungie'}
    assert r.headers['cache-control'] == 'no-store'
    assert call('DELETE', '/local/secrets').status_code == 200
    assert call('GET', '/local/secrets').json() == {'key':'','bungieKey':''}


def test_keyring_boundaries(local, monkeypatch):
    call, _ = local
    assert call('GET', '/local/secrets', host='192.0.2.2').status_code == 403
    assert call('PUT', '/local/secrets', headers={'Origin':'https://evil.example'}, json={'key':'fake'}).status_code == 403
    assert call('GET', '/local/secrets', headers={'Host':'evil.example'}).status_code == 403
    monkeypatch.setenv('GHOST_MODE', 'hosted')
    assert call('GET', '/local/secrets').status_code == 403
    assert call('GET', '/config').json()['keyring_available'] is False


def test_missing_keyring(local, monkeypatch):
    call, _ = local
    monkeypatch.setattr(local_secrets, 'keyring', None)
    assert call('GET', '/config').json()['keyring_available'] is False
    assert call('GET', '/local/secrets').status_code == 503


def test_keyring_failures_do_not_disclose_keys(local, monkeypatch, caplog):
    call, _ = local
    def fail(*args):
        raise RuntimeError('fake-secret-must-not-appear')
    monkeypatch.setattr(local_secrets.keyring, 'set_password', fail)
    r = call('PUT', '/local/secrets', json={'key': 'fake-secret-must-not-appear'})
    assert r.status_code == 503
    assert 'fake-secret-must-not-appear' not in r.text
    assert 'fake-secret-must-not-appear' not in caplog.text
