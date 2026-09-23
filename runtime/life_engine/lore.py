"""Lore 的不可变领域值；正文和来源始终是低信任数据。"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

from .domain import (CanonStatus, DomainError, DomainId, IdKind, Principal,
                     Revision, WorldScope, WriterEpoch, aware, check_id, require)
from .import_ir import JsonValue
from .memory import (AudienceKind, MemoryAudience, MemoryLifecycle, MemoryQueryResult,
                     SessionMemoryContext)

MAX_ENABLED_BOOKS = 32
MAX_SCOPE_BINDINGS = 32
MAX_ENTRIES_PER_BOOK = 10_000
MAX_SCOPE_SCAN_ENTRIES = 10_000
MAX_SCOPE_TRIGGERS = 10_000
MAX_TRIGGER_BYTES = 256
MAX_ENTRY_TEXT_BYTES = 65_536
MAX_INITIAL_CORPUS_BYTES = 262_144
MAX_RECURSIVE_CORPUS_BYTES = 262_144
MAX_ACTIVATION_ROUNDS = 16
MAX_ACTIVATED_ENTRIES = 128
MAX_OUTPUT_TEXT_BYTES = 524_288
MAX_SCAN_WORK_BYTES = 16 * 1024 * 1024
MAX_METADATA_BYTES = 4096
MAX_IDENTITY_BYTES = 512
MAX_SLOT_BYTES = 128
MAX_INT = 2 ** 31 - 1


def byte_size(value):
    """严格计算 UTF-8 字节数，拒绝不可编码文本。"""
    if type(value) is not str:
        raise DomainError('Lore 文本类型错误')
    try:
        return len(value.encode('utf-8'))
    except UnicodeError:
        raise DomainError('Lore 文本 Unicode 错误') from None


def metadata(value):
    require(value, JsonValue)
    if byte_size(value.text) > MAX_METADATA_BYTES:
        raise DomainError('Lore 来源元数据越界')


def bounded_int(value, *, minimum=0, maximum=MAX_INT):
    if type(value) is not int or not minimum <= value <= maximum:
        raise DomainError('Lore 整数越界')


@dataclass(frozen=True, order=True)
class LoreBookVersion:
    value: int

    def __post_init__(self):
        bounded_int(self.value, minimum=1)

    def next(self):
        return LoreBookVersion(self.value + 1)


@dataclass(frozen=True)
class LoreBindingRevision(Revision):
    """每个 WorldScope 独立的绑定修订。"""

    def next(self):
        return LoreBindingRevision(self.value + 1)


class LoreDiagnostic(str, Enum):
    UNSUPPORTED_REGEX = 'UNSUPPORTED_REGEX'
    UNSUPPORTED_EXTENSION = 'UNSUPPORTED_EXTENSION'
    INVALID_TRIGGER_FIELD = 'INVALID_TRIGGER_FIELD'
    CONFLICTING_ENABLE_FLAGS = 'CONFLICTING_ENABLE_FLAGS'
    EMPTY_TRIGGER = 'EMPTY_TRIGGER'
    SELECTIVE_WITHOUT_SECONDARY = 'SELECTIVE_WITHOUT_SECONDARY'
    INVALID_PRIORITY_ORDER = 'INVALID_PRIORITY_ORDER'
    ACTIVATION_ROUND_LIMIT = 'ACTIVATION_ROUND_LIMIT'
    ACTIVATION_ENTRY_LIMIT = 'ACTIVATION_ENTRY_LIMIT'
    ACTIVATION_BYTE_LIMIT = 'ACTIVATION_BYTE_LIMIT'
    ACTIVATION_SCAN_LIMIT = 'ACTIVATION_SCAN_LIMIT'


class LoreActivationReason(str, Enum):
    CONSTANT = 'CONSTANT'
    PRIMARY_TRIGGER = 'PRIMARY_TRIGGER'
    SELECTIVE_TRIGGER = 'SELECTIVE_TRIGGER'
    RECURSIVE_TRIGGER = 'RECURSIVE_TRIGGER'


@dataclass(frozen=True)
class LoreBookDefinition:
    book_id: DomainId
    owner_id: DomainId
    display_name: str
    current_version: LoreBookVersion
    source_type: str
    source_metadata: JsonValue
    created_at: datetime
    created_by: DomainId

    def __post_init__(self):
        check_id(self.book_id, IdKind.LORE_BOOK)
        check_id(self.owner_id, IdKind.OWNER)
        check_id(self.created_by, IdKind.PRINCIPAL)
        require(self.current_version, LoreBookVersion)
        if not self.display_name.strip() or byte_size(self.display_name) > 512:
            raise DomainError('Lore 书名越界')
        if not self.source_type or byte_size(self.source_type) > 64:
            raise DomainError('Lore 来源类型越界')
        metadata(self.source_metadata)
        aware(self.created_at)


@dataclass(frozen=True)
class LoreBookVersionRecord:
    book_id: DomainId
    version: LoreBookVersion
    source_type: str
    source_fingerprint: str
    payload_fingerprint: str | None
    source_metadata: JsonValue
    registration_fingerprint: str
    entry_count: int
    runtime_compatible: bool
    created_at: datetime
    created_by: DomainId

    def __post_init__(self):
        check_id(self.book_id, IdKind.LORE_BOOK)
        require(self.version, LoreBookVersion)
        check_id(self.created_by, IdKind.PRINCIPAL)
        if not self.source_type or byte_size(self.source_type) > 64:
            raise DomainError('Lore 来源类型越界')
        for value in (self.source_fingerprint, self.registration_fingerprint):
            if type(value) is not str or not re.fullmatch('[0-9a-f]{64}', value):
                raise DomainError('Lore 指纹格式错误')
        if self.payload_fingerprint is not None and (type(self.payload_fingerprint) is not str or
                not re.fullmatch('[0-9a-f]{64}', self.payload_fingerprint)):
            raise DomainError('Lore payload 指纹格式错误')
        metadata(self.source_metadata)
        bounded_int(self.entry_count, maximum=MAX_ENTRIES_PER_BOOK)
        require(self.runtime_compatible, bool)
        aware(self.created_at)


@dataclass(frozen=True)
class LoreEntryDefinition:
    entry_id: DomainId
    book_id: DomainId
    book_version: LoreBookVersion
    enabled: bool
    constant: bool
    selective: bool
    case_sensitive: bool
    runtime_priority: int
    runtime_order: int
    text: str
    primary_triggers: tuple[str, ...]
    secondary_triggers: tuple[str, ...]
    runtime_disabled_reason: LoreDiagnostic | None
    source_metadata: JsonValue
    diagnostics: tuple[LoreDiagnostic, ...] = ()

    def __post_init__(self):
        check_id(self.entry_id, IdKind.LORE_ENTRY)
        check_id(self.book_id, IdKind.LORE_BOOK)
        require(self.book_version, LoreBookVersion)
        for field in (self.enabled, self.constant, self.selective, self.case_sensitive):
            require(field, bool)
        bounded_int(self.runtime_priority, minimum=-MAX_INT)
        bounded_int(self.runtime_order)
        if byte_size(self.text) > MAX_ENTRY_TEXT_BYTES:
            raise DomainError('Lore 正文越界')
        for triggers in (self.primary_triggers, self.secondary_triggers):
            require(triggers, tuple)
            if len(triggers) > 32 or len(set(triggers)) != len(triggers):
                raise DomainError('Lore 触发词数量或重复错误')
            for trigger in triggers:
                if not trigger or byte_size(trigger) > MAX_TRIGGER_BYTES:
                    raise DomainError('Lore 触发词越界')
        if self.runtime_disabled_reason is not None:
            require(self.runtime_disabled_reason, LoreDiagnostic)
        metadata(self.source_metadata)
        require(self.diagnostics, tuple)
        for diagnostic in self.diagnostics:
            require(diagnostic, LoreDiagnostic)


@dataclass(frozen=True)
class LoreBinding:
    scope: WorldScope
    book_id: DomainId
    book_version: LoreBookVersion
    enabled: bool
    binding_order: int
    source: str

    def __post_init__(self):
        require(self.scope, WorldScope)
        check_id(self.book_id, IdKind.LORE_BOOK)
        require(self.book_version, LoreBookVersion)
        require(self.enabled, bool)
        bounded_int(self.binding_order)
        if not self.source or byte_size(self.source) > MAX_IDENTITY_BYTES:
            raise DomainError('Lore 绑定来源越界')


@dataclass(frozen=True)
class LoreBudget:
    max_rounds: int = MAX_ACTIVATION_ROUNDS
    max_entries: int = MAX_ACTIVATED_ENTRIES
    max_output_bytes: int = MAX_OUTPUT_TEXT_BYTES
    max_scan_work_bytes: int = MAX_SCAN_WORK_BYTES

    def __post_init__(self):
        for value, maximum in ((self.max_rounds, MAX_ACTIVATION_ROUNDS),
                               (self.max_entries, MAX_ACTIVATED_ENTRIES),
                               (self.max_output_bytes, MAX_OUTPUT_TEXT_BYTES),
                               (self.max_scan_work_bytes, MAX_SCAN_WORK_BYTES)):
            bounded_int(value, minimum=1, maximum=maximum)


@dataclass(frozen=True)
class LoreRegistrationIdentity:
    source: str
    slot: str

    def __post_init__(self):
        if not self.source or byte_size(self.source) > MAX_IDENTITY_BYTES:
            raise DomainError('Lore 登记来源越界')
        if not self.slot or byte_size(self.slot) > MAX_SLOT_BYTES:
            raise DomainError('Lore 登记槽位越界')


@dataclass(frozen=True)
class OwnerLoreContext:
    """由受信适配器提供的管理断言，不是登录凭据。"""
    principal: Principal
    scope: WorldScope | None = None

    def __post_init__(self):
        require(self.principal, Principal)
        if self.scope is not None:
            require(self.scope, WorldScope)
            if self.scope.owner_id != self.principal.owner_id:
                raise DomainError('Lore 管理 Scope 与 Owner 不符')


@dataclass(frozen=True)
class SessionLoreContext:
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
        if type(self.runtime_id) is not str or not self.runtime_id:
            raise DomainError('Lore 运行代次错误')
        require(self.viewer, MemoryAudience)
        if self.viewer.kind not in (AudienceKind.CHARACTER_INSTANCE, AudienceKind.SOUL):
            raise DomainError('Lore 会话观看身份错误')


@dataclass(frozen=True)
class LoreMemoryProjection:
    """只允许当前会话已授权 Memory 结果转为触发文本。"""
    scope: WorldScope
    viewer: MemoryAudience
    version: str
    texts: tuple[str, ...]
    _authorized: bool = field(default=False, init=False, repr=False, compare=False)

    def __post_init__(self):
        require(self.scope, WorldScope)
        require(self.viewer, MemoryAudience)
        if type(self.version) is not str or not self.version or type(self.texts) is not tuple:
            raise DomainError('Memory 投影格式错误')
        for text in self.texts:
            byte_size(text)

    @classmethod
    def from_session_result(cls, context, result):
        require(context, SessionMemoryContext)
        require(result, MemoryQueryResult)
        if not result.version:
            raise DomainError('Memory 查询版本缺失')
        texts = []
        for record in result.records:
            if (record.scope != context.scope or record.lifecycle is not MemoryLifecycle.LIVE
                    or record.provenance.canon_status is not CanonStatus.ACCEPTED
                    or not any(a.kind is AudienceKind.WORLD or a == context.viewer for a in record.audience)):
                raise DomainError('Memory 投影越权')
            texts.append(record.content)
        if sum(byte_size(text) for text in texts) > MAX_INITIAL_CORPUS_BYTES:
            raise DomainError('Memory 投影越界')
        projection = cls(context.scope, context.viewer, result.version, tuple(texts))
        object.__setattr__(projection, '_authorized', True)
        return projection


@dataclass(frozen=True)
class LoreActivationRequest:
    context: SessionLoreContext
    conversation_projection: tuple[str, ...]
    expected_revision: LoreBindingRevision
    budget: LoreBudget = LoreBudget()
    memory_projection: LoreMemoryProjection | None = None

    def __post_init__(self):
        require(self.context, SessionLoreContext)
        require(self.conversation_projection, tuple)
        for text in self.conversation_projection:
            byte_size(text)
        require(self.expected_revision, LoreBindingRevision)
        require(self.budget, LoreBudget)
        if self.memory_projection is not None:
            require(self.memory_projection, LoreMemoryProjection)
            if (not self.memory_projection._authorized or
                    self.memory_projection.scope != self.context.scope or
                    self.memory_projection.viewer != self.context.viewer):
                raise DomainError('Memory 投影 Scope 或 viewer 不符')
        size = sum(byte_size(text) for text in self.conversation_projection)
        if self.memory_projection:
            size += sum(byte_size(text) for text in self.memory_projection.texts)
        if size > MAX_INITIAL_CORPUS_BYTES:
            raise DomainError('Lore 初始语料越界')


@dataclass(frozen=True)
class ActivatedLoreEntry:
    book_id: DomainId
    book_version: LoreBookVersion
    entry_id: DomainId
    text: str
    reason: LoreActivationReason
    round: int
    matched_primary: tuple[str, ...]
    matched_secondary: tuple[str, ...]
    runtime_priority: int
    binding_order: int
    runtime_order: int


@dataclass(frozen=True)
class LoreActivationResult:
    scope: WorldScope
    viewer: MemoryAudience
    session_id: DomainId
    writer_epoch: WriterEpoch
    runtime_id: str
    world_revision: Revision
    lore_binding_revision: LoreBindingRevision
    book_versions: tuple[tuple[DomainId, LoreBookVersion], ...]
    entries: tuple[ActivatedLoreEntry, ...]
    diagnostics: tuple[LoreDiagnostic, ...]
    budget_used: tuple[int, int, int]
    budget_exhausted: bool
    version: str


@dataclass(frozen=True)
class LoreReceipt:
    book_id: DomainId
    book_version: LoreBookVersion
    revision: LoreBindingRevision | None = None
