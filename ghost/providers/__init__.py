"""Request-scoped AI transports. Never cache these clients."""
from contextvars import ContextVar
request_secrets = ContextVar("request_secrets", default=())

import logging
import os
import re
from urllib.parse import urlsplit
import requests


def redact(value, secrets=()):
    text = str(value)
    for secret in secrets:
        if secret:
            text = text.replace(secret, '[REDACTED]')
    return re.sub(r'(?i)(bearer\s+|(?:x-ai-key|api[_-]?key|client_secret)[\s\"\x27:=]+)[^\s,\"\x27}]+', r'\1[REDACTED]', text)


class RedactionFilter(logging.Filter):
    def filter(self, record):
        # Exception tracebacks may contain request objects/credentials.
        record.msg = redact(record.getMessage(), request_secrets.get())
        record.args = ()
        if record.stack_info:
            record.stack_info = redact(record.stack_info, request_secrets.get())
        if record.exc_info:
            record.msg += ' [exception details suppressed]'
            record.exc_info = None
            record.exc_text = None
        return True


class ProviderError(ValueError):
    pass


def validate_base_url(url):
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise ProviderError('Base URL must be an http/https URL without credentials, query or fragment')
    return url.rstrip('/')


class Provider:
    def __init__(self, name, key='', model='', base_url=''):
        self.name = {'grok': 'xai', 'local': 'ollama'}.get(name, name)
        defaults = {'xai': ('https://api.x.ai/v1', 'grok-3'), 'openai': ('https://api.openai.com/v1', 'gpt-4o-mini'), 'anthropic': ('https://api.anthropic.com/v1', 'claude-sonnet-4-5'), 'ollama': ('http://127.0.0.1:11434', 'llama3.2'), 'openai_compatible': ('', '')}
        if self.name not in defaults:
            raise ProviderError('Unknown AI provider')
        base, default_model = defaults[self.name]
        self.base_url = validate_base_url(base_url or base)
        self.model = model or default_model
        if not self.model:
            raise ProviderError('AI model is required')
        if not key and self.name != 'ollama':
            raise ProviderError('AI key is required')
        self._key = key

    def chat(self, messages, model=None, max_tokens=1024, **options):
        headers = {'Content-Type': 'application/json'}
        body = dict(messages=messages, model=model or self.model, stream=False)
        if self.name == 'anthropic':
            headers.update({'x-api-key': self._key, 'anthropic-version': '2023-06-01'})
            body['system'] = '\n'.join(m['content'] for m in messages if m['role'] == 'system')
            body['messages'] = [m for m in messages if m['role'] != 'system']
            body['max_tokens'] = max_tokens
            path = '/messages'
        elif self.name == 'ollama':
            path = '/api/chat'
        else:
            headers['Authorization'] = 'Bearer ' + self._key
            body['max_tokens'] = max_tokens
            path = '/chat/completions'
        try:
            response = requests.post(self.base_url + path, headers=headers, json=body, timeout=60, allow_redirects=False)
            if response.status_code != 200:
                raise ProviderError('AI provider returned HTTP ' + str(response.status_code))
            data = response.json()
            if self.name == 'anthropic':
                return redact(''.join(b.get('text', '') for b in data['content']), (self._key,))
            if self.name == 'ollama':
                return redact(data['message']['content'], (self._key,))
            return redact(data['choices'][0]['message']['content'], (self._key,))
        except Exception:
            pass
        # Raise outside the except block so raw transport exceptions (which may
        # contain credentials) are not retained as __context__.
        raise ProviderError('AI request failed; check provider, model and credentials')

    def generate(self, prompt):
        return self.chat([{'role': 'user', 'content': prompt}])

    def generate_with_system(self, system, prompt):
        return self.chat([{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}])


def from_headers(headers):
    name = headers.get('x-ai-provider') or 'ollama'
    key = headers.get('x-ai-key', '')
    if not key and name in ('xai', 'grok') and os.getenv('GHOST_ALLOW_ENV_AI_KEY') == '1':
        key = os.getenv('XAI_API_KEY', '')
    return Provider(name, key, headers.get('x-ai-model', ''), headers.get('x-ai-base-url', ''))
