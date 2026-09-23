"""Story 的不可变身份、类型化事件载荷与投影值。"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .domain import (DomainError, DomainId, IdKind, Principal, Provenance, Revision,
                     WorldScope, WriterEpoch, aware, check_id, require)
from .memory import MemoryAudience, AudienceKind
from .world_codec import dumps

PROJECTION_VERSION = 'SP-004C-story-projection-v1'
MAX_EVENT_PAYLOAD_BYTES = 65_536
MAX_NARRATIVE_TEXT_BYTES = 16_384
MAX_STORY_STATE_BYTES = 1_048_576
MAX_SOURCE_REFERENCES = 32
MAX_FACT_KEY_BYTES = 256
MAX_FACT_VALUE_BYTES = 4096
MAX_THREAD_TITLE_BYTES = 512
MAX_THREAD_SUMMARY_BYTES = 8192
MAX_RELATIONSHIP_KEY_BYTES = 256
MAX_RELATIONSHIP_VALUE_BYTES = 4096
MAX_SOURCE_ID_BYTES = 512


def bounded(value, maximum, *, allow_empty=False):
    if type(value) is not str or (not value and not allow_empty) or len(value.encode('utf-8')) > maximum:
        raise DomainError('Story 文本无效或超出预算')
    return value


@dataclass(frozen=True)
class StoryRevision(Revision):
    """每 WorldScope 的独立 Story CAS 修订。"""


@dataclass(frozen=True)
class StoryClock:
    logical_tick: int = 0

    def __post_init__(self):
        if type(self.logical_tick) is not int or self.logical_tick < 0:
            raise DomainError('Story 逻辑刻度无效')

    def next(self):
        return StoryClock(self.logical_tick + 1)


class StoryEventKind(str, Enum):
    WORLD_FACT_SET = 'world_fact_set'
    WORLD_FACT_REMOVED = 'world_fact_removed'
    CHARACTER_STATE_SET = 'character_state_set'
    CHARACTER_STATE_REMOVED = 'character_state_removed'
    RELATIONSHIP_SET = 'relationship_set'
    RELATIONSHIP_REMOVED = 'relationship_removed'
    THREAD_OPENED = 'thread_opened'
    THREAD_UPDATED = 'thread_updated'
    THREAD_RESOLVED = 'thread_resolved'
    THREAD_CANCELLED = 'thread_cancelled'
    NARRATIVE_EVENT = 'narrative_event'


class StoryThreadStatus(str, Enum):
    OPEN = 'open'
    RESOLVED = 'resolved'
    CANCELLED = 'cancelled'


class SourceReferenceKind(str, Enum):
    STORY_EVENT = 'story_event'
    MEMORY = 'memory'
    LORE_ENTRY = 'lore_entry'
    EXTERNAL_MESSAGE = 'external_message'


@dataclass(frozen=True)
class StoryEventSourceReference:
    kind: SourceReferenceKind
    identity: str

    def __post_init__(self):
        require(self.kind, SourceReferenceKind)
        bounded(self.identity, MAX_SOURCE_ID_BYTES)
        if self.kind in (SourceReferenceKind.STORY_EVENT, SourceReferenceKind.MEMORY):
            check_id(DomainId.parse(self.identity), IdKind.EVENT if self.kind is SourceReferenceKind.STORY_EVENT else IdKind.MEMORY)
        elif self.kind is SourceReferenceKind.LORE_ENTRY:
            parts = self.identity.split('|')
            if len(parts) != 3 or not parts[1].isdigit() or str(int(parts[1])) != parts[1] or int(parts[1]) < 1:
                raise DomainError('Lore 来源身份无效')
            check_id(DomainId.parse(parts[0]), IdKind.LORE_BOOK)
            check_id(DomainId.parse(parts[2]), IdKind.LORE_ENTRY)


@dataclass(frozen=True)
class FactPayload:
    namespace: str
    key: str
    value: str | None = None

    def __post_init__(self):
        bounded(self.namespace, MAX_FACT_KEY_BYTES)
        bounded(self.key, MAX_FACT_KEY_BYTES)
        if self.value is not None:
            bounded(self.value, MAX_FACT_VALUE_BYTES, allow_empty=True)


@dataclass(frozen=True)
class CharacterPayload:
    character_id: DomainId
    key: str
    value: str | None = None

    def __post_init__(self):
        check_id(self.character_id, IdKind.CHARACTER)
        bounded(self.key, MAX_FACT_KEY_BYTES)
        if self.value is not None:
            bounded(self.value, MAX_FACT_VALUE_BYTES, allow_empty=True)


@dataclass(frozen=True)
class RelationshipPayload:
    source_id: DomainId
    target_id: DomainId
    key: str
    value: str | None = None

    def __post_init__(self):
        check_id(self.source_id, IdKind.CHARACTER)
        check_id(self.target_id, IdKind.CHARACTER)
        if self.source_id == self.target_id:
            raise DomainError('Story 关系不支持自身指向')
        bounded(self.key, MAX_RELATIONSHIP_KEY_BYTES)
        if self.value is not None:
            bounded(self.value, MAX_RELATIONSHIP_VALUE_BYTES, allow_empty=True)


@dataclass(frozen=True)
class ThreadPayload:
    thread_id: DomainId
    title: str | None = None
    summary: str | None = None

    def __post_init__(self):
        check_id(self.thread_id, IdKind.STORY_THREAD)
        if self.title is not None:
            bounded(self.title, MAX_THREAD_TITLE_BYTES)
        if self.summary is not None:
            bounded(self.summary, MAX_THREAD_SUMMARY_BYTES, allow_empty=True)


@dataclass(frozen=True)
class NarrativePayload:
    text: str

    def __post_init__(self):
        bounded(self.text, MAX_NARRATIVE_TEXT_BYTES)


_PAYLOAD_TYPES = {
    StoryEventKind.WORLD_FACT_SET: FactPayload,
    StoryEventKind.WORLD_FACT_REMOVED: FactPayload,
    StoryEventKind.CHARACTER_STATE_SET: CharacterPayload,
    StoryEventKind.CHARACTER_STATE_REMOVED: CharacterPayload,
    StoryEventKind.RELATIONSHIP_SET: RelationshipPayload,
    StoryEventKind.RELATIONSHIP_REMOVED: RelationshipPayload,
    StoryEventKind.THREAD_OPENED: ThreadPayload,
    StoryEventKind.THREAD_UPDATED: ThreadPayload,
    StoryEventKind.THREAD_RESOLVED: ThreadPayload,
    StoryEventKind.THREAD_CANCELLED: ThreadPayload,
    StoryEventKind.NARRATIVE_EVENT: NarrativePayload,
}


def payload_data(kind, payload):
    require(kind, StoryEventKind)
    if type(payload) is not _PAYLOAD_TYPES[kind]:
        raise DomainError('Story 事件载荷类型不匹配')
    if isinstance(payload, FactPayload):
        value = {'namespace': payload.namespace, 'key': payload.key, 'value': payload.value}
    elif isinstance(payload, CharacterPayload):
        value = {'character_id': str(payload.character_id), 'key': payload.key, 'value': payload.value}
    elif isinstance(payload, RelationshipPayload):
        value = {'source_id': str(payload.source_id), 'target_id': str(payload.target_id),
                 'key': payload.key, 'value': payload.value}
    elif isinstance(payload, ThreadPayload):
        value = {'thread_id': str(payload.thread_id), 'title': payload.title, 'summary': payload.summary}
    else:
        value = {'text': payload.text}
    wants_value = kind in (StoryEventKind.WORLD_FACT_SET, StoryEventKind.CHARACTER_STATE_SET,
                           StoryEventKind.RELATIONSHIP_SET)
    if isinstance(payload, (FactPayload, CharacterPayload, RelationshipPayload)) and (payload.value is not None) != wants_value:
        raise DomainError('Story SET/REMOVE 载荷不匹配')
    if isinstance(payload, ThreadPayload):
        if kind is StoryEventKind.THREAD_OPENED and (payload.title is None or payload.summary is None):
            raise DomainError('新线索需要标题与摘要')
        if kind is StoryEventKind.THREAD_UPDATED and (payload.title is not None or payload.summary is None):
            raise DomainError('线索更新只接受摘要')
        if kind in (StoryEventKind.THREAD_RESOLVED, StoryEventKind.THREAD_CANCELLED) and (payload.title is not None or payload.summary is not None):
            raise DomainError('线索结案不接受内容字段')
    if len(dumps(value).encode('utf-8')) > MAX_EVENT_PAYLOAD_BYTES:
        raise DomainError('Story 事件载荷超出预算')
    return value


def payload_load(kind, value):
    require(kind, StoryEventKind)
    if type(value) is not dict:
        raise DomainError('Story 载荷格式无效')
    if kind in (StoryEventKind.WORLD_FACT_SET, StoryEventKind.WORLD_FACT_REMOVED):
        if set(value) != {'namespace', 'key', 'value'}:
            raise DomainError('Story 事实字段无效')
        payload = FactPayload(**value)
    elif kind in (StoryEventKind.CHARACTER_STATE_SET, StoryEventKind.CHARACTER_STATE_REMOVED):
        if set(value) != {'character_id', 'key', 'value'}:
            raise DomainError('Story 角色字段无效')
        payload = CharacterPayload(DomainId.parse(value['character_id']), value['key'], value['value'])
    elif kind in (StoryEventKind.RELATIONSHIP_SET, StoryEventKind.RELATIONSHIP_REMOVED):
        if set(value) != {'source_id', 'target_id', 'key', 'value'}:
            raise DomainError('Story 关系字段无效')
        payload = RelationshipPayload(DomainId.parse(value['source_id']), DomainId.parse(value['target_id']), value['key'], value['value'])
    elif kind in (StoryEventKind.THREAD_OPENED, StoryEventKind.THREAD_UPDATED,
                  StoryEventKind.THREAD_RESOLVED, StoryEventKind.THREAD_CANCELLED):
        if set(value) != {'thread_id', 'title', 'summary'}:
            raise DomainError('Story 线索字段无效')
        payload = ThreadPayload(DomainId.parse(value['thread_id']), value['title'], value['summary'])
    else:
        if set(value) != {'text'}:
            raise DomainError('Story 叙事字段无效')
        payload = NarrativePayload(value['text'])
    payload_data(kind, payload)
    return payload


@dataclass(frozen=True)
class StoryIdempotencyIdentity:
    source: str
    slot: str

    def __post_init__(self):
        bounded(self.source, 512)
        bounded(self.slot, 128)


@dataclass(frozen=True)
class OwnerStoryContext:
    principal: Principal
    scope: WorldScope

    def __post_init__(self):
        require(self.principal, Principal)
        require(self.scope, WorldScope)
        if self.principal.owner_id != self.scope.owner_id:
            raise DomainError('Story 管理主体与 Scope 不符')


@dataclass(frozen=True)
class SessionStoryContext:
    principal: Principal
    scope: WorldScope
    session_id: DomainId
    writer_epoch: WriterEpoch
    runtime_id: str
    viewer: MemoryAudience

    def __post_init__(self):
        require(self.principal, Principal)
        require(self.scope, WorldScope)
        check_id(self.session_id, IdKind.SESSION)
        require(self.writer_epoch, WriterEpoch)
        bounded(self.runtime_id, 128)
        require(self.viewer, MemoryAudience)
        if self.principal.owner_id != self.scope.owner_id or self.viewer.kind not in (AudienceKind.SOUL, AudienceKind.CHARACTER_INSTANCE):
            raise DomainError('Story 会话主体或观看身份错误')


@dataclass(frozen=True)
class StoryEventProposal:
    kind: StoryEventKind
    payload: object
    provenance: Provenance
    source_refs: tuple[StoryEventSourceReference, ...] = ()
    character_actor_id: DomainId | None = None
    supersedes_event_id: DomainId | None = None
    payload_version: int = 1

    def __post_init__(self):
        payload_data(self.kind, self.payload)
        require(self.provenance, Provenance)
        if type(self.payload_version) is not int or self.payload_version != 1:
            raise DomainError('Story 载荷版本无效')
        if type(self.source_refs) is not tuple or len(self.source_refs) > MAX_SOURCE_REFERENCES:
            raise DomainError('Story 来源数量越界')
        for item in self.source_refs:
            require(item, StoryEventSourceReference)
        if self.character_actor_id is not None:
            check_id(self.character_actor_id, IdKind.CHARACTER)
        if self.supersedes_event_id is not None:
            check_id(self.supersedes_event_id, IdKind.EVENT)


@dataclass(frozen=True)
class StoryEvent:
    event_id: DomainId
    scope: WorldScope
    sequence: int
    revision: StoryRevision
    clock: StoryClock
    proposal: StoryEventProposal
    accepted_by: DomainId
    accepted_at: datetime

    def __post_init__(self):
        check_id(self.event_id, IdKind.EVENT)
        require(self.scope, WorldScope)
        require(self.revision, StoryRevision)
        require(self.clock, StoryClock)
        require(self.proposal, StoryEventProposal)
        check_id(self.accepted_by, IdKind.PRINCIPAL)
        aware(self.accepted_at)
        if type(self.sequence) is not int or self.sequence < 1 or self.sequence != self.revision.value or self.sequence != self.clock.logical_tick:
            raise DomainError('Story 事件顺序或时钟无效')
        if self.proposal.provenance.actor.owner_id != self.scope.owner_id:
            raise DomainError('Story 来源 Owner 不匹配')


@dataclass(frozen=True)
class StoryThread:
    thread_id: DomainId
    title: str
    summary: str
    status: StoryThreadStatus
    opened_by_event: DomainId
    last_updated_event: DomainId
    resolved_by_event: DomainId | None = None

    def __post_init__(self):
        check_id(self.thread_id, IdKind.STORY_THREAD)
        bounded(self.title, MAX_THREAD_TITLE_BYTES)
        bounded(self.summary, MAX_THREAD_SUMMARY_BYTES, allow_empty=True)
        require(self.status, StoryThreadStatus)
        check_id(self.opened_by_event, IdKind.EVENT)
        check_id(self.last_updated_event, IdKind.EVENT)
        if self.resolved_by_event is not None:
            check_id(self.resolved_by_event, IdKind.EVENT)
        if (self.status is StoryThreadStatus.OPEN) != (self.resolved_by_event is None):
            raise DomainError('Story 线索结案事件不一致')


@dataclass(frozen=True)
class StoryState:
    scope: WorldScope
    revision: StoryRevision = StoryRevision()
    clock: StoryClock = StoryClock()
    last_event_sequence: int = 0
    projection_version: str = PROJECTION_VERSION
    world_facts: tuple[tuple[str, str, str], ...] = ()
    character_states: tuple[tuple[DomainId, str, str], ...] = ()
    relationships: tuple[tuple[DomainId, DomainId, str, str], ...] = ()
    threads: tuple[StoryThread, ...] = ()

    def __post_init__(self):
        require(self.scope, WorldScope)
        require(self.revision, StoryRevision)
        require(self.clock, StoryClock)
        if type(self.last_event_sequence) is not int or self.last_event_sequence < 0 or not (self.last_event_sequence == self.revision.value == self.clock.logical_tick):
            raise DomainError('Story 投影修订与时钟不一致')
        if self.projection_version != PROJECTION_VERSION:
            raise DomainError('Story 投影版本无效')
        for name in ('world_facts', 'character_states', 'relationships', 'threads'):
            if type(getattr(self, name)) is not tuple:
                raise DomainError('Story 投影集合必须不可变')


@dataclass(frozen=True)
class StoryReceipt:
    event_id: DomainId
    revision: StoryRevision
    clock: StoryClock


@dataclass(frozen=True)
class StoryProjection:
    scope: WorldScope
    viewer: MemoryAudience
    revision: StoryRevision
    clock: StoryClock
    projection_version: str
    world_facts: tuple[tuple[str, str, str], ...]
    character_state: tuple[tuple[str, str], ...]
    relationships: tuple[tuple[DomainId, DomainId, str, str], ...]
    open_threads: tuple[StoryThread, ...]
    snapshot_token: str
