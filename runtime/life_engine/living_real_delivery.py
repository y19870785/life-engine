"""Host-neutral REAL_CONTACT admission; this module has no transport dependency."""
from dataclasses import dataclass
from enum import Enum

from .living_domain import fail, fingerprint, text


class BindingMode(Enum):
    SIMULATION = 'SIMULATION'
    REAL_DELIVERY = 'REAL_DELIVERY'


class ExecutionPurpose(Enum):
    SIMULATED_CONTACT = 'SIMULATED_CONTACT'
    REAL_CONTACT = 'REAL_CONTACT'


class PolicyDecision(Enum):
    ALLOW = 'ALLOW'
    DENY = 'DENY'


@dataclass(frozen=True)
class TrustedDeliveryTarget:
    platform: str
    provider: str
    server: str
    channel: str
    owner: str
    profile: str
    agent: str
    binding: str

    def __post_init__(self):
        for value in vars(self).values():
            text(value)
            if value != value.strip() or any(mark in value for mark in (',', '|', '*', '\n', '\r')):
                fail('TARGET_AMBIGUOUS')

    @property
    def key(self):
        return 'TRUSTED_TARGET:' + fingerprint(vars(self))


@dataclass(frozen=True)
class DeliveryContext:
    binding: str
    authority_epoch: str
    adapter_epoch: str
    generation: str
    target: TrustedDeliveryTarget
    intent: str
    attempt: str
    invocation: str
    purpose: ExecutionPurpose
    lifecycle: str
    session: object
    payload_digest: str


class RealDeliveryPolicy:
    """Trusted deployment extension point. Unknown and exceptional decisions deny."""
    def decide(self, context: DeliveryContext) -> PolicyDecision:
        return PolicyDecision.DENY


class OneShotRealDeliveryGrant:
    __slots__ = ('_authority', 'target', 'intent', 'invocation', 'payload_digest',
                 'expiry', 'generation', 'authority_epoch', 'adapter_epoch',
                 'purpose', 'state', 'attempt')

    def __init__(self, authority, target, intent, invocation, payload_digest, expiry):
        self._authority = authority
        self.target = target
        self.intent = intent
        self.invocation = invocation
        self.payload_digest = payload_digest
        self.expiry = expiry
        self.generation = authority._generation()
        self.authority_epoch = authority.binding_runtime_epoch
        self.adapter_epoch = authority.plugin_epoch
        self.purpose = ExecutionPurpose.REAL_CONTACT
        self.state = 'UNBOUND'
        self.attempt = None

    def __repr__(self):
        return '<OneShotRealDeliveryGrant redacted>'

    def __reduce__(self):
        raise TypeError('grant is memory-only')

    def revoke(self):
        self.state = 'REVOKED'

    def reserve(self, authority, context, now):
        if self.state != 'UNBOUND':
            fail('REAL_GRANT_SPENT')
        self.state = 'RESERVED'  # no refund on denial, expiry or issuance failure
        if (authority is not self._authority or now >= self.expiry
                or self.generation != authority._generation()
                or self.authority_epoch != authority.binding_runtime_epoch
                or self.adapter_epoch != authority.plugin_epoch
                or context.purpose is not self.purpose
                or context.target != self.target or context.intent != self.intent
                or context.invocation != self.invocation
                or context.payload_digest != self.payload_digest):
            self.revoke()
            fail('REAL_GRANT_DENIED')
        self.attempt = context.attempt  # Core-returned Attempt only


def validation_text(value):
    text(value, limit=1024)
    if ('\n' in value or '\r' in value or '@' in value or value.startswith(('/', '!'))
            or any(mark in value for mark in ('```', '<@', 'http://', 'https://'))):
        fail('REAL_PAYLOAD_DENIED')
    return fingerprint(value)


class SimulationConsumer:
    """Compatibility boundary for simulated permits; no real-purpose selector."""
    def __init__(self, authority):
        self.authority = authority

    def intercept(self, permit, *, target, attempt, invocation):
        with self.authority.consume_permit(permit, target=target, attempt=attempt,
                                           invocation=invocation):
            return 'LOCAL_SIMULATION_INTERCEPT'


class RealDeliveryConsumer:
    """REAL_CONTACT admission. A bound port owns the sole post-consume call.

    The original local intercept remains the default validation path. A transport
    port is installed only by trusted Host integration code, never by a caller
    choosing a transport while consuming a permit.
    """
    def __init__(self, authority, *, port=None):
        self.authority = authority
        self._port = port
        self._count = 0

    @property
    def intercept_count(self):
        return self._count

    def intercept(self, permit, *, target, intent, attempt, invocation, payload):
        with self.authority._consume_real_permit(permit, target=target, intent=intent,
                attempt=attempt, invocation=invocation, payload=payload):
            self._count += 1
            return 'LOCAL_PRE_TRANSPORT_INTERCEPT'

    async def deliver_bound(self, permit, *, target, intent, attempt, invocation, payload):
        """Admit once, then invoke the fixed Host port; never issue SENT evidence.

        ``preflight`` is synchronous and side-effect free. The only await after
        permit consumption is the single exact transport invocation. Exception
        and unknown results remain reconciliation concerns, never retries.
        """
        if self._port is None:
            fail('REAL_TRANSPORT_UNBOUND')
        self._port.preflight(self.authority, target, payload)
        with self.authority._consume_real_permit(permit, target=target, intent=intent,
                attempt=attempt, invocation=invocation, payload=payload):
            return await self._port.invoke_exact(target, payload)
