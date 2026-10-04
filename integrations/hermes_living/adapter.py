"""Hermes 0.21.3 platform seam for Life Engine REAL_CONTACT.

The factory registration grants no delivery authority. Without a trusted local
binding and an injected exact transport, this adapter cannot connect or send.
The only generic Hermes outbound method returns a non-retryable denial.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
import re
import threading
from weakref import WeakKeyDictionary, ref
from uuid import uuid4

from gateway.config import Platform
from gateway.platform_registry import platform_registry
from gateway.platforms.base import BasePlatformAdapter, SendResult

from life_engine.living_domain import fail
from life_engine.living_real_delivery import (BindingMode, RealDeliveryConsumer,
    TrustedDeliveryTarget, validation_text)


PLATFORM_NAME = 'life_engine_discord'
GENERIC_DENIAL = 'REAL_CONTACT_AUTHORITY_REQUIRED'
_DIGEST = re.compile(r'[0-9a-f]{64}\Z')
_IDENTITY = re.compile(r'[A-Za-z0-9:_-]{1,128}\Z')
_PROJECTION_SEAL = object()
_PROJECTION_LOCK = threading.RLock()
_PROJECTIONS = WeakKeyDictionary()


@dataclass(frozen=True)
class AdapterIdentity:
    """Credential identity is a digest, never a bot token or secret value."""
    profile: str
    agent: str
    application: str
    credential_digest: str

    def __post_init__(self):
        if (not all(type(value) is str and _IDENTITY.fullmatch(value) for value in
                    (self.profile, self.agent, self.application))
                or type(self.credential_digest) is not str
                or not _DIGEST.fullmatch(self.credential_digest)):
            fail('HOST_IDENTITY_MISSING')


@dataclass(frozen=True)
class AuthorityHostProjection:
    """Pinned trusted deployment identity, separate from observed adapter state."""
    _authority_ref: object = field(repr=False)
    target: TrustedDeliveryTarget
    expected: AdapterIdentity
    authority_epoch: str
    generation: str
    _seal: object = field(repr=False, compare=False)

    def __post_init__(self):
        if self._seal is not _PROJECTION_SEAL or self._authority_ref() is None:
            fail('HOST_IDENTITY_MISSING')

    @property
    def authority(self):
        return self._authority_ref()


class ProtectedDeliveryRegistry:
    """Trusted deployment input, never populated from a send caller or metadata.

    A2 must verify this source against its protected Hermes Home configuration.
    The application identity is pinned before adapter observation or permit issue.
    """
    def __init__(self, target, expected_identity):
        if (type(target) is not TrustedDeliveryTarget
                or type(expected_identity) is not AdapterIdentity
                or target.platform != PLATFORM_NAME or target.provider != 'discord'
                or target.profile != expected_identity.profile
                or target.agent != expected_identity.agent):
            fail('HOST_IDENTITY_MISSING')
        self._target = target
        self._expected = expected_identity

    def project(self, authority):
        with authority._mutex:
            authority._data()
            if (authority.execution_mode is not BindingMode.REAL_DELIVERY
                    or authority._real_target != self._target
                    or authority.host_identity != self._target.binding):
                fail('REAL_POLICY_DENIED')
            with _PROJECTION_LOCK:
                existing = _PROJECTIONS.get(authority)
                if existing is not None:
                    if existing.target != self._target or existing.expected != self._expected:
                        fail('HOST_IDENTITY_MISMATCH')
                    return existing
                projection = AuthorityHostProjection(ref(authority), self._target,
                    self._expected, authority.binding_runtime_epoch,
                    authority._generation(), _PROJECTION_SEAL)
                _PROJECTIONS[authority] = projection
                return projection


class _ExactPort:
    """Private fixed dependency owned by the RealDeliveryConsumer."""
    def __init__(self, adapter):
        self.adapter = adapter

    @contextmanager
    def execution_window(self, authority, target, payload):
        adapter = self.adapter
        # Lock order: adapter lifecycle -> BindingAuthority -> Core management.
        # Every adapter-owned transition takes the same lifecycle lock. A direct
        # authority transition takes only the later authority lock.
        with adapter._lifecycle_lock:
            projection = adapter._projection
            transport = adapter._transport  # frozen before permit consumption
            if (not adapter._connected or adapter._authority is not authority
                    or adapter._consumer is None or transport is None
                    or type(projection) is not AuthorityHostProjection
                    or _PROJECTIONS.get(authority) is not projection
                    or projection.authority is not authority
                    or projection.authority_epoch != authority.binding_runtime_epoch
                    or projection.generation != authority._generation()
                    or adapter._bound_epoch != authority.binding_runtime_epoch
                    or adapter._bound_plugin_epoch != authority.plugin_epoch
                    or adapter._instance_epoch != adapter._bound_instance_epoch
                    or type(target) is not TrustedDeliveryTarget
                    or target != projection.target or target != adapter._target
                    or target.platform != PLATFORM_NAME or target.provider != 'discord'
                    or target.profile != adapter._identity.profile
                    or target.agent != adapter._identity.agent
                    or adapter._identity != projection.expected
                    or target.binding != authority.host_identity):
                fail('ADAPTER_LIFECYCLE_STALE')
            validation_text(payload)
            yield transport


class LifeEngineDiscordAdapter(BasePlatformAdapter):
    """An independent BasePlatformAdapter, not a DiscordAdapter subclass."""
    name = PLATFORM_NAME
    splits_long_messages = False
    supports_async_delivery = False
    MAX_MESSAGE_LENGTH = 1024

    def __init__(self, config, *, transport=None):
        super().__init__(config, Platform(PLATFORM_NAME))
        self._lifecycle_lock = threading.RLock()
        self._instance_epoch = uuid4().hex
        self._bound_instance_epoch = None
        self._bound_epoch = None
        self._bound_plugin_epoch = None
        self._identity = None
        self._projection = None
        self._target = None
        self._authority = None
        self._consumer = None
        self._transport = transport  # Default factory installs no transport.
        self._connected = False

    def bind_trusted_host(self, projection, identity):
        """Trusted local deployment wiring; never registered as a Hermes tool."""
        with self._lifecycle_lock:
            if type(projection) is not AuthorityHostProjection:
                fail('HOST_IDENTITY_MISSING')
            authority, target = projection.authority, projection.target
            if (self._consumer is not None or self._transport is None
                    or type(identity) is not AdapterIdentity
                    or type(target) is not TrustedDeliveryTarget
                    or _PROJECTIONS.get(authority) is not projection
                    or identity != projection.expected
                    or projection.authority_epoch != authority.binding_runtime_epoch
                    or projection.generation != authority._generation()
                    or authority.execution_mode is not BindingMode.REAL_DELIVERY
                    or authority._real_target != target
                    or target.platform != PLATFORM_NAME or target.provider != 'discord'
                    or target.profile != identity.profile or target.agent != identity.agent
                    or target.binding != authority.host_identity):
                fail('REAL_POLICY_DENIED')
            # Claiming a fresh adapter instance revokes any earlier adapter's
            # grant/permit under the existing BindingAuthority lifecycle epoch.
            authority.reload_plugin()
            self._authority = authority
            self._target = target
            self._identity = identity
            self._projection = projection
            self._bound_epoch = authority.binding_runtime_epoch
            self._bound_plugin_epoch = authority.plugin_epoch
            self._bound_instance_epoch = self._instance_epoch
            self._consumer = RealDeliveryConsumer(authority, port=_ExactPort(self))

    async def connect(self, *, is_reconnect=False):
        # A1 has no provider connector. A local inert transport may be connected
        # for contract tests; the plugin's default factory fails closed.
        with self._lifecycle_lock:
            self._connected = self._consumer is not None and self._transport is not None
            return self._connected

    async def disconnect(self):
        with self._lifecycle_lock:
            self._connected = False
            if self._authority is not None:
                self._authority.reload_plugin()

    def credential_identity_changed(self, credential_digest):
        """Trusted Host lifecycle projection; raw credentials never enter here."""
        if type(credential_digest) is not str or not _DIGEST.fullmatch(credential_digest):
            fail('HOST_IDENTITY_MISSING')
        with self._lifecycle_lock:
            if self._identity is None:
                fail('HOST_IDENTITY_MISSING')
            if credential_digest != self._identity.credential_digest:
                self._connected = False
                self._identity = AdapterIdentity(self._identity.profile,
                    self._identity.agent, self._identity.application,
                    credential_digest)
                if self._authority is not None:
                    self._authority.reload_plugin()

    def application_identity_changed(self, application):
        if type(application) is not str or not _IDENTITY.fullmatch(application):
            fail('HOST_IDENTITY_MISSING')
        with self._lifecycle_lock:
            if self._identity is None:
                fail('HOST_IDENTITY_MISSING')
            if application != self._identity.application:
                self._connected = False
                self._identity = AdapterIdentity(self._identity.profile,
                    self._identity.agent, application,
                    self._identity.credential_digest)
                if self._authority is not None:
                    self._authority.reload_plugin()

    async def deliver_authorized_real_contact(self, permit, *, target, intent,
                                              attempt, invocation, payload):
        """Private Host binding entry; no generic route registers this method."""
        consumer = self._consumer
        if consumer is None:
            fail('REAL_TRANSPORT_UNBOUND')
        return await consumer.deliver_bound(permit, target=target, intent=intent,
                                            attempt=attempt, invocation=invocation,
                                            payload=payload)

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_final_ledgered(self, *args, **kwargs):
        # Refuse before the inherited generic ledger bracket can write an obligation.
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False), self

    async def _send_with_retry(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_draft(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_multiple_images(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_image(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_animation(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_voice(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_video(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_document(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_image_file(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_private_notice(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_exec_approval(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_slash_confirm(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_clarify(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def send_typing(self, *args, **kwargs):
        fail(GENERIC_DENIAL)

    async def edit_message(self, *args, **kwargs):
        return SendResult(success=False, error=GENERIC_DENIAL, retryable=False)

    async def delete_message(self, *args, **kwargs):
        fail(GENERIC_DENIAL)

    async def create_handoff_thread(self, *args, **kwargs):
        fail(GENERIC_DENIAL)


def register(ctx):
    """Official PluginContext seam; never register tools or sender callbacks."""
    if platform_registry.get(PLATFORM_NAME) is not None:
        fail('PLATFORM_NAME_CONFLICT')
    handle = ctx.register_platform(name=PLATFORM_NAME, label='Life Engine Discord',
        adapter_factory=LifeEngineDiscordAdapter, check_fn=lambda: True,
        max_message_length=LifeEngineDiscordAdapter.MAX_MESSAGE_LENGTH,
        cron_deliver_env_var='', send_message_handler=None,
        standalone_sender_fn=None, parse_target_ref_fn=None,
        validate_target_ref_fn=None)
    if handle is None:
        fail('PLATFORM_REGISTRATION_FAILED')
    return handle
