"""本地可信边界的不透明凭据；不序列化到模型、日志或 transcript。"""
from dataclasses import dataclass, field
import hashlib
import hmac
import secrets

from .living_domain import canonical, fail


@dataclass(frozen=True, repr=False)
class Capability:
    _handle: str = field(repr=False)

    def __repr__(self):
        return '<Capability redacted>'


@dataclass(frozen=True, repr=False)
class ExecutionPermit:
    _handle: str = field(repr=False)

    def __repr__(self):
        return '<ExecutionPermit redacted>'


class CredentialVault:
    """调用者须持 authority mutex；消费与 lifecycle transition 在同一锁下。"""
    def __init__(self, key):
        self._key = key
        self._entries = {}

    def issue(self, kind, claims):
        nonce = secrets.token_hex(32)
        stamp = hmac.new(self._key, canonical([kind.__name__, nonce, claims]).encode('utf-8'),
                         hashlib.sha256).hexdigest()
        token = kind(nonce + '.' + stamp)
        self._entries[token._handle] = (kind, claims)
        return token

    def consume(self, token, kind, expected, now):
        if type(token) is not kind:
            fail('CAPABILITY_DENIED')
        entry = self._entries.get(token._handle)
        if entry is None or entry[0] is not kind:
            fail('CAPABILITY_STALE')
        claims = entry[1]
        nonce, stamp = token._handle.split('.')
        correct = hmac.new(self._key, canonical([kind.__name__, nonce, claims]).encode('utf-8'),
                           hashlib.sha256).hexdigest()
        if not hmac.compare_digest(stamp, correct):
            fail('CAPABILITY_DENIED')
        if now >= claims['expiry']:
            del self._entries[token._handle]
            fail('CAPABILITY_EXPIRED')
        for name, value in expected.items():
            if claims.get(name) != value:
                fail('GENERATION_STALE' if name == 'generation' else 'CAPABILITY_DENIED')
        del self._entries[token._handle]
        return claims

    def revoke(self):
        self._entries.clear()
