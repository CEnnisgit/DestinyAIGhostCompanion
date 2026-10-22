"""Hosted request boundaries; state contains rate counters, never credentials."""
import ipaddress
import os
import time
from collections import OrderedDict
from starlette.responses import JSONResponse


def hosted():
    return os.getenv('GHOST_MODE', 'desktop') == 'hosted'


def loopback(host):
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class SecurityMiddleware:
    def __init__(self, app, allowed_origins=()):
        self.app = app
        self.allowed_origins = allowed_origins
        self.buckets = OrderedDict()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope['headers']}
        async def secured(message):
            if message['type'] == 'http.response.start':
                values = dict(message.get('headers', []))
                values.setdefault(b'content-security-policy', b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; media-src 'self' blob:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
                values.update({b'x-content-type-options': b'nosniff', b'referrer-policy': b'strict-origin-when-cross-origin', b'x-frame-options': b'DENY'})
                if hosted():
                    values[b'strict-transport-security'] = b'max-age=31536000; includeSubDomains'
                message['headers'] = list(values.items())
            await send(message)
        async def reject(status, detail):
            response_headers = {}
            origin = headers.get('origin')
            if origin and origin in self.allowed_origins:
                response_headers.update({'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Credentials': 'true', 'Vary': 'Origin'})
            if status == 429:
                response_headers['Retry-After'] = '1'
            await JSONResponse({'detail': detail}, status_code=status, headers=response_headers)(scope, receive, secured)
        path = scope['path']
        if hosted():
            if scope['method'] != 'OPTIONS' and (path.startswith(('/local/', '/stt', '/diagnostics/', '/finetune', '/fine-tune')) or path in ('/models', '/voices')):
                return await reject(403, 'Feature available only in desktop mode')
            if scope['method'] != 'OPTIONS' and path in ('/chat', '/chat/stream', '/ai/test') and headers.get('x-ai-provider', 'ollama') in ('ollama', 'local', 'finetune', 'fine-tune'):
                return await reject(403, 'Local AI providers are disabled in hosted mode')
            if scope['query_string'] and b'speak=true' in scope['query_string'].lower():
                return await reject(403, 'Server audio is disabled in hosted mode')
            if path != '/health' and scope['method'] != 'OPTIONS':
                # Never trust forwarded addresses unless the ASGI server has a trusted proxy configured.
                host = (scope.get('client') or ('unknown', 0))[0]
                identity = 'ip:' + host
                auth = headers.get('authorization', '')
                if auth.lower().startswith('bearer '):
                    from server_auth import decode_jwt
                    claims = decode_jwt(auth.split(' ', 1)[1])
                    if claims:
                        identity = 'user:' + str(claims['sub'])
                now = time.monotonic()
                capacity = max(1, int(os.getenv('GHOST_RATE_CAPACITY', '60')))
                refill = max(.001, float(os.getenv('GHOST_RATE_REFILL_PER_SECOND', '1')))
                tokens, stamp = self.buckets.pop(identity, (capacity, now))
                tokens = min(capacity, tokens + (now - stamp) * refill)
                self.buckets[identity] = (max(0, tokens - 1), now)
                while len(self.buckets) > 10000:
                    self.buckets.popitem(last=False)
                if tokens < 1:
                    return await reject(429, 'Rate limit exceeded')
        limit = int(os.getenv('GHOST_MAX_BODY_BYTES', '1048576'))
        try:
            if int(headers.get('content-length', '0')) > limit:
                return await reject(413, 'Request body too large')
        except ValueError:
            return await reject(400, 'Invalid Content-Length')
        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            body.extend(message.get('body', b''))
            if len(body) > limit:
                return await reject(413, 'Request body too large')
            if not message.get('more_body', False):
                break
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
            return await receive()
        await self.app(scope, replay, secured)
