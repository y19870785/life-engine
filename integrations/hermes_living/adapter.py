"""Hermes 0.21.3 platform seam for Life Engine REAL_CONTACT.

The factory registration grants no delivery authority. Without a trusted local
binding and an injected exact transport, this adapter cannot connect or send.
The only generic Hermes outbound method returns a non-retryable denial.
"""

from dataclasses import dataclass
import re
import threading
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


class _ExactPort:
    """Private fixed dependency owned by the RealDeliveryConsumer."""
    def __init__(self, adapter):
        self.adapter = adapter

    def preflight(self, authority, target, payload):
        adapter = self.adapter
        with adapter._lifecycle_lock:
            if (not adapter._connected or adapter._authority is not authority
                    or adapter._consumer is None or adapter._transport is None
                    or adapter._bound_epoch != authority.binding_runtime_epoch
                    or adapter._bound_plugin_epoch != authority.plugin_epoch
                    or adapter._instance_epoch != adapter._bound_instance_epoch
                    or type(target) is not TrustedDeliveryTarget
                    or target != adapter._target
                    or target.platform != PLATFORM_NAME or target.provider != 'discord'
                    or target.profile != adapter._identity.profile
                    or target.agent != adapter._identity.agent
                    or target.binding != authority.host_identity):
                fail('ADAPTER_LIFECYCLE_STALE')
            validation_text(payload)

    async def invoke_exact(self, target, payload):
        # This is the sole post-consume transport call. No target lookup, queue,
        # formatting, chunking, retry, fallback, or generic ledger exists here.
        return await self.adapter._transport.invoke_exact(target.channel, payload)


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
        self._target = None
        self._authority = None
        self._consumer = None
        self._transport = transport  # Default factory installs no transport.
        self._connected = False

    def bind_trusted_host(self, authority, target, identity):
        """Trusted local deployment wiring; never registered as a Hermes tool."""
        with self._lifecycle_lock:
            if (self._consumer is not None or self._transport is None
                    or type(identity) is not AdapterIdentity
                    or type(target) is not TrustedDeliveryTarget
                    or authority.execution_mode is not BindingMode.REAL_DELIVERY
                    or authority._real_target != target
                    or target.platform != PLATFORM_NAME or target.provider != 'discord'
                    or target.profile != identity.profile or target.agent != identity.agent
                    or target.binding != authority.host_identity):
                fail('REAL_POLICY_DENIED')
            self._authority = authority
            self._target = target
            self._identity = identity
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
