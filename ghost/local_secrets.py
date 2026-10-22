"""OS credential storage. No plaintext fallback on the server."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from ghost.security import hosted, loopback

try:
    import keyring
except ImportError:
    keyring = None

router = APIRouter()
SERVICE = 'ghost-companion'


def available():
    try:
        return keyring is not None and keyring.get_keyring().priority > 0
    except Exception:
        return False


def require_local(request):
    origin = request.headers.get('origin')
    if (hosted() or not request.client or not loopback(request.client.host)
            or not loopback(request.url.hostname or '')
            or (origin and origin != str(request.base_url).rstrip('/'))):
        raise HTTPException(403, 'Loopback desktop access required')
    if not available():
        raise HTTPException(503, 'OS keyring unavailable')


class Secrets(BaseModel):
    model_config = ConfigDict(extra='forbid')
    key: str | None = None
    bungieKey: str | None = None


@router.get('/config')
def config(request: Request):
    return {'mode': 'hosted' if hosted() else 'desktop',
            'keyring_available': not hosted() and request.client is not None and loopback(request.client.host) and available()}


@router.get('/local/secrets')
def read(request: Request):
    require_local(request)
    try:
        values = {name: keyring.get_password(SERVICE, name) or '' for name in ('key', 'bungieKey')}
        from fastapi.responses import JSONResponse
        return JSONResponse(values, headers={'Cache-Control': 'no-store'})
    except Exception:
        raise HTTPException(503, 'OS keyring read failed') from None


@router.put('/local/secrets')
def write(request: Request, payload: Secrets):
    require_local(request)
    try:
        for name, value in payload.model_dump(exclude_none=True).items():
            if value:
                keyring.set_password(SERVICE, name, value)
            elif keyring.get_password(SERVICE, name) is not None:
                keyring.delete_password(SERVICE, name)
    except Exception:
        raise HTTPException(503, 'OS keyring write failed') from None
    return {'ok': True}


@router.delete('/local/secrets')
def delete(request: Request):
    return write(request, Secrets(key='', bungieKey=''))
