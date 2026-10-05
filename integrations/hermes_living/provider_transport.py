"""Dedicated one-shot Discord MESSAGE_CREATE boundary.

The Hermes plugin default never constructs this transport. A trusted Host
binding must first prove credential ownership and inject a session factory.
No Discord SDK or network client is imported by this module.
"""

from dataclasses import dataclass, field
from enum import Enum
import json
import re
from threading import Lock
from types import MappingProxyType

from life_engine.living_real_delivery import TrustedDeliveryTarget, validation_text

from .provider_ownership import (CredentialClaim, DiscordRestOwnership,
                                 ProviderBoundaryError)


_SNOWFLAKE = re.compile(r'[0-9]{1,20}\Z')
_ROUTE = 'POST /channels/{channel_id}/messages'


class ProviderResultClass(Enum):
    PRE_SEND_DENY = 'PRE_SEND_DENY'
    PROVIDER_CONFIRMED_SUCCESS = 'PROVIDER_CONFIRMED_SUCCESS'
    PROVIDER_CONFIRMED_REJECTION = 'PROVIDER_CONFIRMED_REJECTION'
    RATE_LIMITED_NO_RETRY = 'RATE_LIMITED_NO_RETRY'
    UNKNOWN = 'UNKNOWN'


@dataclass(frozen=True)
class ProviderInvocationResult:
    classification: ProviderResultClass
    sent_candidate: bool = False
    message_id: str | None = None


@dataclass(frozen=True)
class FrozenTextChannelCapability:
    target: TrustedDeliveryTarget
    application: str
    channel_type: str
    lifecycle: tuple
    owner: DiscordRestOwnership = field(repr=False, compare=False)

    def __post_init__(self):
        if (type(self.target) is not TrustedDeliveryTarget
                or self.target.platform != 'life_engine_discord'
                or self.target.provider != 'discord'
                or self.channel_type != 'guild_text'
                or not _SNOWFLAKE.fullmatch(self.target.server)
                or not _SNOWFLAKE.fullmatch(self.target.channel)
                or not self.application):
            raise ProviderBoundaryError('EXACT_TEXT_CHANNEL_REQUIRED')


@dataclass(frozen=True)
class ResolvedTextChannel:
    """Protected resolver result, established before permit consumption."""
    server: str
    channel: str
    application: str
    channel_type: str


@dataclass(frozen=True)
class FrozenUtf8TextJson:
    text: str = field(repr=False)
    digest: str
    body: bytes = field(repr=False)

    @classmethod
    def freeze(cls, text):
        digest = validation_text(text)
        # A1's stricter 1024-character bound is retained. No truncation/split.
        if len(text) > 1024:
            raise ProviderBoundaryError('PAYLOAD_TOO_LONG')
        body = json.dumps({'content': text, 'allowed_mentions': {'parse': []}},
                          ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        return cls(text, digest, body)


class PreparedDiscordMessageCreate:
    """Immutable target/body/session reference, with a single-use attempt bit."""

    def __init__(self, capability, payload, session, authorization, authority):
        self._capability = capability
        self._payload = payload
        self._session = session
        self._authority = authority
        self._headers = MappingProxyType({'Authorization': authorization,
                         'Content-Type': 'application/json',
                         'Content-Length': str(len(payload.body))})
        self._used = False
        self._armed = False
        self._lock = Lock()
        self.http_message_create_attempt_count = 0

    def __repr__(self):
        return '<PreparedDiscordMessageCreate redacted>'

    def arm_after_consume(self, authority, permit, attempt):
        # A direct call to the prepared provider object cannot send. Only the
        # consumer's post-consume window can arm it, and only once in memory.
        with self._lock:
            grants = tuple(authority._real_grants.values())
            if (self._armed or self._used or authority is not self._authority
                    or attempt in authority._real_issued or permit is None
                    or not any(g.state == 'SPENT' and g.attempt == attempt
                               for g in grants)):
                raise ProviderBoundaryError('PROVIDER_ADMISSION_MISSING')
            self._capability.owner.reserve_attempt_once(attempt)
            self._armed = True

    async def invoke_exact(self, channel, payload):
        if channel != self._capability.target.channel or payload != self._payload.text:
            raise ProviderBoundaryError('FROZEN_INVOCATION_MISMATCH')
        with self._lock:
            if not self._armed:
                raise ProviderBoundaryError('PROVIDER_ADMISSION_MISSING')
            if self._used:
                raise ProviderBoundaryError('SAFETY_VIOLATION_DUPLICATE_ATTEMPT')
            self._used = True
            # Linearization point immediately before the sole provider await.
            self.http_message_create_attempt_count += 1
            if self.http_message_create_attempt_count > 1:
                raise ProviderBoundaryError('SAFETY_VIOLATION_MULTIPLE_ATTEMPTS')
        try:
            response = await self._session.post_once(
                'https://discord.com/api/v10/channels/' + channel + '/messages',
                headers=self._headers, data=self._payload.body)
        except BaseException:
            # Do not expose provider exceptions, credential-bearing URL/headers,
            # or treat a post-entry exception as safe to retry.
            return ProviderInvocationResult(ProviderResultClass.UNKNOWN)
        self._capability.owner.domain.observe(_ROUTE, response.status, response.headers)
        return classify_response(response, channel)


def classify_response(response, channel):
    status = response.status
    if status == 429:
        return ProviderInvocationResult(ProviderResultClass.RATE_LIMITED_NO_RETRY)
    if status in (400, 401, 403, 404, 405, 413, 415):
        return ProviderInvocationResult(ProviderResultClass.PROVIDER_CONFIRMED_REJECTION)
    if status not in (200, 201):
        return ProviderInvocationResult(ProviderResultClass.UNKNOWN)
    try:
        data = json.loads(response.body)
        message_id, channel_id = data['id'], data['channel_id']
        if (type(message_id) is str and _SNOWFLAKE.fullmatch(message_id)
                and type(channel_id) is str and channel_id == channel):
            return ProviderInvocationResult(ProviderResultClass.PROVIDER_CONFIRMED_SUCCESS,
                                            sent_candidate=True, message_id=message_id)
    except (ValueError, TypeError, KeyError):
        pass
    return ProviderInvocationResult(ProviderResultClass.UNKNOWN)


class OneShotDiscordTransport:
    """Trusted adapter dependency; no generic send method or retry queue."""

    def __init__(self, ownership, *, application, resolver=None, source_config=None):
        if type(ownership) is not DiscordRestOwnership:
            raise ProviderBoundaryError('REST_OWNERSHIP_REQUIRED')
        self._ownership = ownership
        self._application = application
        self._resolver = resolver
        self._source_config = source_config

    def bind_lifecycle(self, projection):
        self._ownership.bind_lifecycle_once((projection.authority_epoch,
                    projection.authority.plugin_epoch, projection.generation))

    def revoke(self):
        self._ownership.revoke()

    async def close(self):
        await self._ownership.close()

    def prepare_exact(self, projection, target, payload):
        if projection.expected.application != self._application:
            raise ProviderBoundaryError('APPLICATION_IDENTITY_MISMATCH')
        if self._resolver is None:
            raise ProviderBoundaryError('PROTECTED_TARGET_RESOLVER_MISSING')
        resolved = self._resolver.resolve(target)
        if (type(resolved) is not ResolvedTextChannel
                or resolved.server != target.server
                or resolved.channel != target.channel
                or resolved.application != self._application):
            raise ProviderBoundaryError('EXACT_TEXT_CHANNEL_REQUIRED')
        lifecycle = (projection.authority_epoch,
                     projection.authority.plugin_epoch,
                     projection.generation)
        self._ownership.require_current(lifecycle)
        capability = FrozenTextChannelCapability(target, self._application,
                                                  resolved.channel_type, lifecycle,
                                                  self._ownership)
        frozen = FrozenUtf8TextJson.freeze(payload)
        self._ownership.domain.admit_now(_ROUTE)
        try:
            # Session and exact Authorization header freeze before consume.
            return PreparedDiscordMessageCreate(capability, frozen,
                        self._ownership.session, self._ownership.authorization_header,
                        projection.authority)
        except BaseException:
            self._ownership.domain.release()
            raise

    def release_admission(self):
        self._ownership.domain.release()


class TrustedProviderTransportFactory:
    """Explicit Host/plugin construction; never called by plugin discovery.

    `config` is the official PlatformConfig supplied to adapter_factory. The
    complete inventory must come from protected Host configuration management,
    not this platform's config or a generic send argument.
    """

    def create(self, config, *, profile, adapter_owner, inventory, resolver,
               session_factory, application):
        if (type(getattr(config, 'token', None)) is not str or not config.token
                or getattr(config, 'enabled', None) is not True
                or not profile or not adapter_owner or not application):
            raise ProviderBoundaryError('PROTECTED_PLATFORM_CONFIG_REQUIRED')
        claim = CredentialClaim('life_engine_discord', profile, adapter_owner,
                                config.token)
        owner = DiscordRestOwnership.create(candidate=claim, inventory=inventory,
                    session_factory=session_factory, lifecycle=None)
        return OneShotDiscordTransport(owner, application=application,
                                       resolver=resolver, source_config=config)


class AiohttpOneShotSessionFactory:
    """Opt-in production factory; never installed by the default plugin.

    aiohttp 3.14.3 is pinned because POST retry/redirect behavior is audited.
    The test suite injects a fake factory and blocks all sockets.
    """

    def create(self, token):
        try:
            import aiohttp
            if aiohttp.__version__ != '3.14.3':
                raise ProviderBoundaryError('UNVERIFIED_AIOHTTP_VERSION')
            return _AiohttpOneShotSession(aiohttp.ClientSession(trust_env=False,
                                                                 raise_for_status=False))
        except ProviderBoundaryError:
            raise
        except BaseException:
            raise ProviderBoundaryError('PROVIDER_SESSION_CREATE_DENIED') from None


@dataclass(frozen=True)
class _HttpResponse:
    status: int
    headers: dict
    body: bytes = field(repr=False)


class _AiohttpOneShotSession:
    def __init__(self, session):
        self._session = session

    async def post_once(self, url, *, headers, data):
        # No middleware, redirect follow, retry library, or SDK HTTPClient.
        async with self._session.post(url, headers=headers, data=data,
                                      allow_redirects=False) as response:
            body = await response.read()
            return _HttpResponse(response.status, dict(response.headers), body)

    async def close(self):
        await self._session.close()
