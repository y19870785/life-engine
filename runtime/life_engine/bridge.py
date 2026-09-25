"""受控跨 World Prompt 投影的强类型值；Grant ID 与 token 均不是凭据。"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .domain import (CanonStatus, DomainError, DomainId, IdKind, Principal, RealityStatus,
                     Revision, WorldScope, WriterEpoch, aware, check_id, require)
from .memory import AudienceKind, MemoryAudience
from .memory import MemoryLifecycle, MemoryQueryResult, SessionMemoryContext
from .story import SessionStoryContext, StoryProjection

MAX_BRIDGE_ITEMS = 128
MAX_BRIDGE_ITEM_BYTES = 65_536
MAX_BRIDGE_TOTAL_BYTES = 262_144
FIELD_REGISTRY = {
    'memory': frozenset(('content', 'kind', 'subjects', 'reality_status',
                         'canon_status', 'source_reference')),
    'story_projection': frozenset(('character_state', 'viewer_relationships')),
}


class BridgeFailure(str, Enum):
    INVALID_ARGUMENT = 'invalid_argument'
    AUTHORIZATION_DENIED = 'authorization_denied'
    SOURCE_SCOPE_MISMATCH = 'source_scope_mismatch'
    TARGET_SCOPE_MISMATCH = 'target_scope_mismatch'
    AUDIENCE_DENIED = 'audience_denied'
    UNSUPPORTED_DIRECTION = 'unsupported_direction'
    UNSUPPORTED_DATA_CLASS = 'unsupported_data_class'
    UNSUPPORTED_PURPOSE = 'unsupported_purpose'
    GRANT_NOT_FOUND = 'grant_not_found'
    GRANT_REVOKED = 'grant_revoked'
    GRANT_EXPIRED = 'grant_expired'
    GRANT_REVISION_CONFLICT = 'grant_revision_conflict'
    FIELD_DENIED = 'field_denied'
    SOURCE_STALE = 'source_stale'
    TARGET_STALE = 'target_stale'
    PREVIEW_STALE = 'preview_stale'
    PROJECTION_STALE = 'projection_stale'
    IDEMPOTENCY_CONFLICT = 'idempotency_conflict'
    BUDGET_INPUT = 'budget_input'
    CONTROL_REQUIRED = 'control_required'
    STORAGE_CORRUPT = 'storage_corrupt'
    STORAGE_BUSY = 'storage_busy'
    SCHEMA_MISMATCH = 'schema_mismatch'
    RECOVERY_REQUIRED = 'recovery_required'


class BridgeRuntimeError(ValueError):
    def __init__(self, code: BridgeFailure):
        self.code = code
        super().__init__(code.value)


def deny(code):
    raise BridgeRuntimeError(code)


def bounded(value, limit=512):
    if type(value) is not str or not value or len(value.encode('utf-8')) > limit:
        deny(BridgeFailure.INVALID_ARGUMENT)


class BridgeDataClass(str, Enum):
    MEMORY = 'memory'
    STORY_PROJECTION = 'story_projection'


class BridgePurpose(str, Enum):
    PROMPT_CONTEXT = 'prompt_context'
    PERSIST_TARGET_MEMORY = 'persist_target_memory'
    PERSIST_TARGET_STORY_CANDIDATE = 'persist_target_story_candidate'


class BridgeGrantStatus(str, Enum):
    ACTIVE = 'active'
    REVOKED = 'revoked'


@dataclass(frozen=True)
class BridgeGrantRevision(Revision):
    pass


def checked_fields(data_class, fields):
    require(data_class, BridgeDataClass)
    if (type(fields) is not tuple or not fields or len(fields) > 16 or
            any(type(x) is not str for x in fields) or
            tuple(sorted(set(fields))) != fields or
            not set(fields) <= FIELD_REGISTRY[data_class.value]):
        deny(BridgeFailure.FIELD_DENIED)


def checked_audience(audience):
    require(audience, MemoryAudience)
    if audience.kind not in (AudienceKind.SOUL, AudienceKind.CHARACTER_INSTANCE):
        deny(BridgeFailure.AUDIENCE_DENIED)


@dataclass(frozen=True)
class OwnerBridgeContext:
    principal: Principal
    source_scope: WorldScope
    target_scope: WorldScope

    def __post_init__(self):
        require(self.principal, Principal)
        require(self.source_scope, WorldScope)
        require(self.target_scope, WorldScope)
        if self.principal.owner_id != self.source_scope.owner_id or self.principal.owner_id != self.target_scope.owner_id:
            deny(BridgeFailure.AUTHORIZATION_DENIED)


@dataclass(frozen=True)
class SessionBridgeContext:
    principal: Principal
    target_scope: WorldScope
    session_id: DomainId
    writer_epoch: WriterEpoch
    runtime_id: str
    generation: str
    viewer: MemoryAudience

    def __post_init__(self):
        require(self.principal, Principal)
        require(self.target_scope, WorldScope)
        check_id(self.session_id, IdKind.SESSION)
        require(self.writer_epoch, WriterEpoch)
        bounded(self.runtime_id, 128)
        bounded(self.generation, 256)
        checked_audience(self.viewer)


@dataclass(frozen=True)
class BridgeGrantProposal:
    source_scope: WorldScope
    target_scope: WorldScope
    data_class: BridgeDataClass
    allowed_fields: tuple[str, ...]
    purpose: BridgePurpose
    target_audience: MemoryAudience
    expires_at: datetime

    def __post_init__(self):
        require(self.source_scope, WorldScope)
        require(self.target_scope, WorldScope)
        checked_fields(self.data_class, self.allowed_fields)
        require(self.purpose, BridgePurpose)
        checked_audience(self.target_audience)
        aware(self.expires_at)


@dataclass(frozen=True)
class BridgeGrant:
    grant_id: DomainId
    principal: Principal
    proposal: BridgeGrantProposal
    revision: BridgeGrantRevision
    status: BridgeGrantStatus
    created_at: datetime
    revoked_by: Principal | None = None
    revoked_at: datetime | None = None

    def __post_init__(self):
        check_id(self.grant_id, IdKind.GRANT)
        require(self.principal, Principal)
        require(self.proposal, BridgeGrantProposal)
        require(self.revision, BridgeGrantRevision)
        require(self.status, BridgeGrantStatus)
        aware(self.created_at)
        if self.revision.value not in (1, 2) or (self.status is BridgeGrantStatus.ACTIVE) != (self.revision.value == 1):
            deny(BridgeFailure.STORAGE_CORRUPT)
        if self.status is BridgeGrantStatus.REVOKED:
            require(self.revoked_by, Principal)
            aware(self.revoked_at)
        elif self.revoked_by is not None or self.revoked_at is not None:
            deny(BridgeFailure.STORAGE_CORRUPT)


@dataclass(frozen=True)
class BridgeIdempotencyIdentity:
    producer: str
    source: str
    slot: str

    def __post_init__(self):
        bounded(self.producer, 256)
        bounded(self.source, 512)
        bounded(self.slot, 128)


@dataclass(frozen=True)
class BridgeBudget:
    max_items: int = MAX_BRIDGE_ITEMS
    max_item_bytes: int = MAX_BRIDGE_ITEM_BYTES
    max_total_bytes: int = MAX_BRIDGE_TOTAL_BYTES

    def __post_init__(self):
        for field_name, maximum in (('max_items', MAX_BRIDGE_ITEMS),
                                    ('max_item_bytes', MAX_BRIDGE_ITEM_BYTES),
                                    ('max_total_bytes', MAX_BRIDGE_TOTAL_BYTES)):
            value = getattr(self, field_name)
            if type(value) is not int or not 1 <= value <= maximum:
                deny(BridgeFailure.BUDGET_INPUT)


@dataclass(frozen=True)
class BridgePreview:
    grant_id: DomainId
    principal: Principal
    proposal: BridgeGrantProposal
    runtime_id: str
    generation: str
    fingerprint: str
    token: str


@dataclass(frozen=True)
class BridgeReceipt:
    grant_id: DomainId
    revision: BridgeGrantRevision
    status: BridgeGrantStatus


@dataclass(frozen=True)
class BridgeLineage:
    source_scope: WorldScope
    source_subsystem: BridgeDataClass
    source_object_id: str
    source_version: str
    source_audience: tuple[MemoryAudience, ...]
    reality_status: RealityStatus
    canon_status: CanonStatus
    grant_id: DomainId
    grant_revision: BridgeGrantRevision


@dataclass(frozen=True)
class BridgeItem:
    item_id: str
    fields: tuple[tuple[str, str], ...]
    lineage: BridgeLineage
    byte_size: int


@dataclass(frozen=True)
class BridgeProjection:
    grant_id: DomainId
    grant_revision: BridgeGrantRevision
    source_scope: WorldScope
    target_scope: WorldScope
    data_class: BridgeDataClass
    purpose: BridgePurpose
    fields: tuple[str, ...]
    target_audience: MemoryAudience
    source_version: str
    source_principal: Principal
    source_viewer: MemoryAudience
    source_session_id: DomainId
    source_writer_epoch: WriterEpoch
    source_runtime_id: str
    source_generation: str
    target_session: SessionBridgeContext
    items: tuple[BridgeItem, ...]
    budget: BridgeBudget
    budget_used: int
    fingerprint: str
    projection_token: str
    _source: object = field(default=None, init=False, repr=False, compare=False)
    _runtime: object = field(default=None, init=False, repr=False, compare=False)


_SOURCE_SEAL = object()


@dataclass(frozen=True)
class BridgeMemorySource:
    context: SessionMemoryContext
    query: str
    limit: int
    memory_id: DomainId | None
    result: MemoryQueryResult
    runtime_id: str
    generation: str
    _runtime: object = field(default=None, init=False, repr=False, compare=False)
    _seal: object = field(default=None, init=False, repr=False, compare=False)

    @classmethod
    def from_session_query(cls, runtime, context, *, query='', limit=20, memory_id=None):
        if type(context) is not SessionMemoryContext or not callable(getattr(runtime, 'query', None)):
            deny(BridgeFailure.AUTHORIZATION_DENIED)
        result = runtime.query(context, query=query, limit=limit, history=False, memory_id=memory_id)
        cls.validate_records(context, result)
        if memory_id is not None and not any(record.memory_id == memory_id for record in result.records):
            deny(BridgeFailure.SOURCE_STALE)
        value = cls(context, query, limit, memory_id, result, runtime.repository.runtime_id,
                    runtime.repository.generation)
        object.__setattr__(value, '_runtime', runtime)
        object.__setattr__(value, '_seal', _SOURCE_SEAL)
        return value

    @staticmethod
    def validate_records(context, result):
        if type(result) is not MemoryQueryResult or not result.version:
            deny(BridgeFailure.SOURCE_STALE)
        for record in result.records:
            if (record.scope != context.scope or record.lifecycle is not MemoryLifecycle.LIVE or
                    record.provenance.canon_status is not CanonStatus.ACCEPTED or
                    not any(a.kind is AudienceKind.WORLD or a == context.viewer for a in record.audience)):
                deny(BridgeFailure.AUTHORIZATION_DENIED)


@dataclass(frozen=True)
class BridgeStorySource:
    context: SessionStoryContext
    result: StoryProjection
    runtime_id: str
    generation: str
    _runtime: object = field(default=None, init=False, repr=False, compare=False)
    _seal: object = field(default=None, init=False, repr=False, compare=False)

    @classmethod
    def from_session_projection(cls, runtime, context):
        if type(context) is not SessionStoryContext or not callable(getattr(runtime, 'get_story_projection', None)):
            deny(BridgeFailure.AUTHORIZATION_DENIED)
        result = runtime.get_story_projection(context)
        if result.scope != context.scope or result.viewer != context.viewer:
            deny(BridgeFailure.SOURCE_STALE)
        value = cls(context, result, runtime.repository.runtime_id, runtime.repository.generation)
        object.__setattr__(value, '_runtime', runtime)
        object.__setattr__(value, '_seal', _SOURCE_SEAL)
        return value


@dataclass(frozen=True)
class BridgeProjectionRequest:
    grant_id: DomainId
    principal: Principal
    source_scope: WorldScope
    target_scope: WorldScope
    data_class: BridgeDataClass
    fields: tuple[str, ...]
    purpose: BridgePurpose
    target_audience: MemoryAudience
    budget: BridgeBudget

    def __post_init__(self):
        check_id(self.grant_id, IdKind.GRANT)
        require(self.principal, Principal)
        require(self.source_scope, WorldScope)
        require(self.target_scope, WorldScope)
        checked_fields(self.data_class, self.fields)
        require(self.purpose, BridgePurpose)
        checked_audience(self.target_audience)
        require(self.budget, BridgeBudget)
