"""不可变的 World Memory 值对象；内容分类不授予权限。"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .domain import (DomainError, DomainId, IdKind, Principal, Provenance, Revision,
                     WorldScope, WriterEpoch, aware, check_id, require)

MAX_CONTENT_BYTES = 65536
MAX_QUERY_BYTES = 1024
MAX_AUDIENCES = 32
MAX_SUBJECTS = 32
MAX_LINEAGE = 32
MAX_LIMIT = 100


def bounded_text(value, maximum, *, empty=False):
    require(value, str)
    if (not empty and not value.strip()) or len(value.encode('utf-8')) > maximum:
        raise DomainError('文本为空或超过长度限制')


class MemoryKind(Enum):
    EPISODIC = 'episodic'
    SEMANTIC = 'semantic'
    SUMMARY = 'summary'
    OBSERVATION = 'observation'
    PREFERENCE = 'preference'
    RELATIONSHIP_EXPERIENCE = 'relationship_experience'
    SHARED_EXPERIENCE = 'shared_experience'


class MemoryLifecycle(Enum):
    LIVE = 'live'
    HIDDEN = 'hidden'
    SUPERSEDED = 'superseded'
    TOMBSTONED = 'tombstoned'


@dataclass(frozen=True)
class MemoryCollectionRevision(Revision):
    """完整 Scope 的内容修订，与 World 修订和写入代次相互独立。"""


class AudienceKind(Enum):
    WORLD = 'world'
    CHARACTER_INSTANCE = 'character_instance'
    USER = 'user'
    SOUL = 'soul'
    PRINCIPAL = 'principal'


@dataclass(frozen=True)
class MemoryAudience:
    kind: AudienceKind
    target: DomainId | None = None

    def __post_init__(self):
        require(self.kind, AudienceKind)
        if self.kind is AudienceKind.WORLD:
            if self.target is not None:
                raise DomainError('WORLD 受众不能携带目标')
        else:
            check_id(self.target, {AudienceKind.CHARACTER_INSTANCE: IdKind.CHARACTER,
                     AudienceKind.USER: IdKind.OWNER, AudienceKind.SOUL: IdKind.SOUL,
                     AudienceKind.PRINCIPAL: IdKind.PRINCIPAL}[self.kind])


def audiences(value):
    require(value, tuple)
    if not 1 <= len(value) <= MAX_AUDIENCES:
        raise DomainError('受众数量越界')
    for item in value:
        require(item, MemoryAudience)
    ordered = tuple(sorted(set(value), key=lambda a: (a.kind.value, str(a.target))))
    if len(ordered) != len(value):
        raise DomainError('受众重复')
    if any(a.kind is AudienceKind.WORLD for a in value) and len(value) != 1:
        raise DomainError('WORLD 不能与私有受众混合')
    return ordered


class SubjectKind(Enum):
    WORLD = 'world'
    CHARACTER_INSTANCE = 'character_instance'
    SOUL = 'soul'
    TEXT = 'text'


@dataclass(frozen=True)
class MemorySubject:
    kind: SubjectKind
    target: DomainId | None = None
    text: str = ''

    def __post_init__(self):
        require(self.kind, SubjectKind)
        if self.kind is SubjectKind.TEXT:
            bounded_text(self.text, 512)
            if self.target is not None:
                raise DomainError('文本主题不是实体引用')
        else:
            check_id(self.target, {SubjectKind.WORLD: IdKind.WORLD,
                     SubjectKind.CHARACTER_INSTANCE: IdKind.CHARACTER,
                     SubjectKind.SOUL: IdKind.SOUL}[self.kind])
            if self.text != '':
                raise DomainError('实体主题不能附带文本键')


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: DomainId
    scope: WorldScope
    kind: MemoryKind
    content: str
    content_version: int
    provenance: Provenance
    audience: tuple[MemoryAudience, ...]
    subjects: tuple[MemorySubject, ...]
    lifecycle: MemoryLifecycle
    created_at: datetime
    predecessor: DomainId | None = None
    superseded_by: DomainId | None = None
    lineage: tuple[DomainId, ...] = ()

    def __post_init__(self):
        check_id(self.memory_id, IdKind.MEMORY)
        require(self.scope, WorldScope)
        require(self.kind, MemoryKind)
        bounded_text(self.content, MAX_CONTENT_BYTES)
        if type(self.content_version) is not int or self.content_version < 1:
            raise DomainError('正文版本必须为正整数')
        require(self.provenance, Provenance)
        if self.provenance.actor.owner_id != self.scope.owner_id:
            raise DomainError('来源主体不属于记录 Owner')
        object.__setattr__(self, 'audience', audiences(self.audience))
        require(self.subjects, tuple)
        if len(self.subjects) > MAX_SUBJECTS or len(set(self.subjects)) != len(self.subjects):
            raise DomainError('主题数量越界或重复')
        for subject in self.subjects:
            require(subject, MemorySubject)
        require(self.lifecycle, MemoryLifecycle)
        aware(self.created_at)
        for ref in (self.predecessor, self.superseded_by):
            if ref is not None:
                check_id(ref, IdKind.MEMORY)
                if ref == self.memory_id:
                    raise DomainError('记录不能引用自身作为前驱或后继')
        require(self.lineage, tuple)
        if len(self.lineage) > MAX_LINEAGE or len(set(self.lineage)) != len(self.lineage):
            raise DomainError('来源数量越界或重复')
        for ref in self.lineage:
            check_id(ref, IdKind.MEMORY)
            if ref == self.memory_id:
                raise DomainError('记录不能派生自自身')


@dataclass(frozen=True)
class IdempotencyIdentity:
    source: str
    slot: str

    def __post_init__(self):
        bounded_text(self.source, 512)
        bounded_text(self.slot, 128)


@dataclass(frozen=True)
class OwnerMemoryContext:
    """可信适配器的显式管理断言，不是凭据，禁止暴露给模型构造。"""
    principal: Principal
    scope: WorldScope

    def __post_init__(self):
        require(self.principal, Principal)
        require(self.scope, WorldScope)
        if self.principal.owner_id != self.scope.owner_id:
            raise DomainError('管理主体与 Scope 不符')


@dataclass(frozen=True)
class SessionMemoryContext:
    """读取身份由当前绑定决定；不能联合多个角色或升级为管理视图。"""
    principal: Principal
    scope: WorldScope
    session_id: DomainId
    writer_epoch: WriterEpoch
    viewer: MemoryAudience

    def __post_init__(self):
        require(self.principal, Principal)
        require(self.scope, WorldScope)
        check_id(self.session_id, IdKind.SESSION)
        require(self.writer_epoch, WriterEpoch)
        require(self.viewer, MemoryAudience)
        if self.viewer.kind not in (AudienceKind.CHARACTER_INSTANCE, AudienceKind.SOUL):
            raise DomainError('会话必须使用单一角色或 Soul 身份')


@dataclass(frozen=True)
class MemoryReceipt:
    memory_id: DomainId
    revision: MemoryCollectionRevision


@dataclass(frozen=True)
class MemoryQueryResult:
    """只包含授权记录；角色结果不暴露全集合修订计数。"""
    records: tuple[MemoryRecord, ...]
    version: str
