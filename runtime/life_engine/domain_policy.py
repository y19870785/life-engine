"""Declarative host capabilities and pure bridge eligibility; no bridge service or data access."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .domain import DomainError, DomainId, IdKind, Principal, Revision, WorldScope, aware, check_id, require


class Capability(Enum):
    STABLE_PRINCIPAL = 'stable_principal'
    STABLE_SESSION = 'stable_session'
    ISOLATED_CONTEXT_LANE = 'isolated_context_lane'
    MESSAGE_PROVENANCE = 'message_provenance'
    RELOAD_SUPPORT = 'reload_support'
    DELIVERY_ACK = 'delivery_ack'
    HISTORY_ISOLATION = 'history_isolation'


class Support(Enum):
    SUPPORTED = 'supported'
    LIMITED = 'limited'
    UNSUPPORTED = 'unsupported'

    def __bool__(self):
        raise DomainError('Compare support explicitly; LIMITED is not SUPPORTED')


@dataclass(frozen=True)
class HostCapabilities:
    entries: tuple[tuple[Capability, Support], ...] = ()

    def __post_init__(self):
        require(self.entries, tuple)
        seen = set()
        for pair in self.entries:
            if type(pair) is not tuple or len(pair) != 2:
                raise DomainError('Invalid capability entry')
            capability, support = pair
            require(capability, Capability)
            require(support, Support)
            if capability in seen:
                raise DomainError('Duplicate capability')
            seen.add(capability)

    def status(self, capability):
        require(capability, Capability)
        return dict(self.entries).get(capability, Support.UNSUPPORTED)

    def require_supported(self, *capabilities):
        for capability in capabilities:
            if self.status(capability) is not Support.SUPPORTED:
                raise DomainError(f'Capability unavailable: {capability.value}')

    def require_private_context_isolation(self):
        self.require_supported(Capability.STABLE_PRINCIPAL, Capability.STABLE_SESSION,
                               Capability.MESSAGE_PROVENANCE, Capability.ISOLATED_CONTEXT_LANE,
                               Capability.HISTORY_ISOLATION)


def labels(values):
    require(values, frozenset)
    if not values or any(type(v) is not str or not v.strip() or '*' in v for v in values):
        raise DomainError('Explicit nonempty labels required; wildcards are not grants')


@dataclass(frozen=True)
class BridgeRequest:
    principal: Principal
    source: WorldScope
    target: WorldScope
    fields: frozenset[str]
    data_class: str
    purpose: str
    audience: frozenset[str]

    def __post_init__(self):
        require(self.principal, Principal)
        require(self.source, WorldScope)
        require(self.target, WorldScope)
        labels(self.fields)
        labels(self.audience)
        require(self.data_class, str)
        require(self.purpose, str)
        labels(frozenset((self.data_class, self.purpose)))
        if self.source.world_id == self.target.world_id:
            raise DomainError('Bridge requires distinct worlds')
        if self.source.owner_id != self.principal.owner_id or self.target.owner_id != self.principal.owner_id:
            raise DomainError('Cross-owner sharing is not supported by this contract')


@dataclass(frozen=True)
class BridgePolicy:
    grant_id: DomainId
    principal: Principal
    source: WorldScope
    target: WorldScope
    allowed_fields: frozenset[str]
    data_class: str
    purpose: str
    audience: frozenset[str]
    expires_at: datetime
    grant_revision: Revision
    revoked: bool = False

    def __post_init__(self):
        check_id(self.grant_id, IdKind.GRANT)
        BridgeRequest(self.principal, self.source, self.target, self.allowed_fields,
                      self.data_class, self.purpose, self.audience)
        aware(self.expires_at)
        require(self.grant_revision, Revision)
        require(self.revoked, bool)


class BridgeDecision(Enum):
    DENY = 'deny'
    ALLOW = 'allow'

    def __bool__(self):
        raise DomainError('Compare decision explicitly; DENY is not truthy permission')


def evaluate_bridge(policy, request, *, current_grant_revision, now):
    """Eligibility only. Caller must supply current trusted grant; no data is moved/promoted."""
    require(request, BridgeRequest)
    aware(now)
    if policy is None:
        return BridgeDecision.DENY
    require(policy, BridgePolicy)
    require(current_grant_revision, Revision)
    if policy.revoked or policy.expires_at <= now or policy.grant_revision != current_grant_revision:
        return BridgeDecision.DENY
    if (policy.principal, policy.source, policy.target, policy.data_class, policy.purpose) != (
            request.principal, request.source, request.target, request.data_class, request.purpose):
        return BridgeDecision.DENY
    if not request.fields <= policy.allowed_fields or not request.audience <= policy.audience:
        return BridgeDecision.DENY
    return BridgeDecision.ALLOW
