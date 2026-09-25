"""一次性、非持久的会话 Prompt 投影值；正文永远不是权限。"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from .domain import (CharacterDefinition, CharacterInstance, DefinitionRef, DomainId,
                     IdKind, Principal, Revision, WorldScope, WriterEpoch, check_id, require)
from .domain_policy import Capability
from .lore import LoreActivationRequest, LoreActivationResult, LoreBindingRevision
from .memory import (AudienceKind, MemoryAudience, MemoryQueryResult, MemoryRecord,
                     SessionMemoryContext)
from .story import SessionStoryContext, StoryProjection, StoryRevision
from .bridge import BridgeProjection, BridgeRuntimeError

TEMPLATE_VERSION = 'SP-004K-prompt-v1'
MAX_PROMPT_BYTES = 1_048_576
MAX_SECTION_BYTES = 524_288
MAX_ITEM_BYTES = 65_536
MAX_PROMPT_ITEMS = 2048
MAX_CONVERSATION_TURNS = 256
MAX_CONVERSATION_TURN_BYTES = 65_536
_TRUSTED = object()  # 只标识由本进程受信适配器取得的结果，不是认证凭据。


class PromptPurpose(str, Enum):
    ROLEPLAY_RESPONSE = 'roleplay_response'
    SOUL_RESPONSE = 'soul_response'


class PromptAuthority(str, Enum):
    RUNTIME_CONTROL = 'runtime_control'
    TRUSTED_STRUCTURED_STATE = 'trusted_structured_state'
    UNTRUSTED_CONTENT_DATA = 'untrusted_content_data'


class PromptSectionKind(str, Enum):
    RUNTIME_CONTROL = 'runtime_control'
    CHARACTER_IDENTITY = 'character_identity'
    CHARACTER_BEHAVIOR = 'character_behavior'
    CHARACTER_EXAMPLES = 'character_examples'
    STORY_CONTEXT = 'story_context'
    LORE_CONTEXT = 'lore_context'
    MEMORY_CONTEXT = 'memory_context'
    CONVERSATION_CONTEXT = 'conversation_context'
    BRIDGE_CONTEXT = 'bridge_context'


class TruncationPolicy(str, Enum):
    NONE = 'none'
    PREFIX = 'prefix'
    SUFFIX = 'suffix'


class PromptDiagnostic(str, Enum):
    TOKEN_ESTIMATE_UNAVAILABLE = 'token_estimate_unavailable'
    LORE_TRUNCATED = 'lore_truncated'
    MEMORY_TRUNCATED = 'memory_truncated'
    BRIDGE_TRUNCATED = 'bridge_truncated'
    CONVERSATION_TRUNCATED = 'conversation_truncated'
    CHARACTER_EXAMPLES_TRUNCATED = 'character_examples_truncated'
    OPTIONAL_SECTION_DROPPED = 'optional_section_dropped'


class PromptFailure(str, Enum):
    INVALID_ARGUMENT = 'invalid_argument'
    AUTHORIZATION_DENIED = 'authorization_denied'
    SCOPE_MISMATCH = 'scope_mismatch'
    VIEWER_MISMATCH = 'viewer_mismatch'
    SESSION_STALE = 'session_stale'
    WORLD_STALE = 'world_stale'
    MEMORY_STALE = 'memory_stale'
    LORE_STALE = 'lore_stale'
    STORY_STALE = 'story_stale'
    BRIDGE_STALE = 'bridge_stale'
    DEFINITION_STALE = 'definition_stale'
    BUDGET_REQUIRED = 'budget_required'
    BUDGET_INPUT = 'budget_input'
    UNSUPPORTED_PURPOSE = 'unsupported_purpose'
    UNSUPPORTED_CAPABILITY = 'unsupported_capability'


class PromptRuntimeError(ValueError):
    def __init__(self, code: PromptFailure):
        self.code = code
        super().__init__(code.value)


def fail(code):
    raise PromptRuntimeError(code)


def _text(value, maximum, *, empty=False):
    if type(value) is not str or (not empty and not value):
        fail(PromptFailure.INVALID_ARGUMENT)
    try:
        length = len(value.encode('utf-8'))
    except UnicodeError:
        fail(PromptFailure.INVALID_ARGUMENT)
    if length > maximum:
        fail(PromptFailure.BUDGET_INPUT)
    return length


@dataclass(frozen=True)
class PromptItem:
    source_kind: str
    source_id: str
    content: str
    byte_size: int = field(init=False)

    def __post_init__(self):
        _text(self.source_kind, 64)
        _text(self.source_id, 512)
        _text(self.content, MAX_ITEM_BYTES, empty=True)
        from .prompt_codec import item_bytes
        size = item_bytes(self)
        if size > MAX_ITEM_BYTES:
            fail(PromptFailure.BUDGET_INPUT)
        object.__setattr__(self, 'byte_size', size)


@dataclass(frozen=True)
class PromptSection:
    kind: PromptSectionKind
    authority: PromptAuthority
    source: str
    items: tuple[PromptItem, ...]
    priority: int
    required: bool
    truncation_policy: TruncationPolicy
    byte_size: int = field(init=False)
    _bridge_seal: object = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        require(self.kind, PromptSectionKind)
        require(self.authority, PromptAuthority)
        require(self.truncation_policy, TruncationPolicy)
        _text(self.source, 64)
        if type(self.items) is not tuple or any(type(x) is not PromptItem for x in self.items):
            fail(PromptFailure.INVALID_ARGUMENT)
        if type(self.priority) is not int or self.priority < 0 or type(self.required) is not bool:
            fail(PromptFailure.INVALID_ARGUMENT)
        if self.kind is PromptSectionKind.BRIDGE_CONTEXT and self._bridge_seal is not _TRUSTED:
            fail(PromptFailure.UNSUPPORTED_CAPABILITY)
        if self.kind is PromptSectionKind.BRIDGE_CONTEXT and self.authority is not PromptAuthority.UNTRUSTED_CONTENT_DATA:
            fail(PromptFailure.AUTHORIZATION_DENIED)
        if (self.kind is PromptSectionKind.RUNTIME_CONTROL) != (self.authority is PromptAuthority.RUNTIME_CONTROL):
            fail(PromptFailure.AUTHORIZATION_DENIED)
        from .prompt_codec import section_bytes
        object.__setattr__(self, 'byte_size', section_bytes(self))


@dataclass(frozen=True)
class PromptBudget:
    max_total_bytes: int = MAX_PROMPT_BYTES
    runtime_control_bytes: int = 32_768
    character_identity_bytes: int = 65_536
    character_behavior_bytes: int = 131_072
    character_examples_bytes: int = 131_072
    story_bytes: int = 131_072
    lore_bytes: int = 262_144
    memory_bytes: int = 262_144
    bridge_bytes: int = 262_144
    conversation_bytes: int = 262_144
    max_total_tokens: int | None = None

    def __post_init__(self):
        if type(self.max_total_bytes) is not int or not 1 <= self.max_total_bytes <= MAX_PROMPT_BYTES:
            fail(PromptFailure.BUDGET_INPUT)
        for name in ('runtime_control_bytes', 'character_identity_bytes', 'character_behavior_bytes',
                     'character_examples_bytes', 'story_bytes', 'lore_bytes', 'memory_bytes',
                     'bridge_bytes', 'conversation_bytes'):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= MAX_SECTION_BYTES:
                fail(PromptFailure.BUDGET_INPUT)
        if self.max_total_tokens is not None and (type(self.max_total_tokens) is not int or self.max_total_tokens < 1):
            fail(PromptFailure.BUDGET_INPUT)

    def limit(self, kind):
        name = kind.value.removesuffix('_context') + '_bytes'
        return getattr(self, name)


class PromptTokenEstimator(Protocol):
    def estimate(self, text: str) -> int: ...


class ConversationVersionValidator(Protocol):
    def current_version(self, scope: WorldScope, viewer: MemoryAudience,
                        session_id: DomainId, lane_id: str) -> str: ...


@dataclass(frozen=True)
class ConversationTurn:
    category: str
    text: str
    source_ref: str

    def __post_init__(self):
        if self.category not in ('user', 'assistant') or type(self.category) is not str:
            fail(PromptFailure.INVALID_ARGUMENT)
        _text(self.text, MAX_CONVERSATION_TURN_BYTES, empty=True)
        _text(self.source_ref, 512)


@dataclass(frozen=True)
class ConversationProjection:
    scope: WorldScope
    viewer: MemoryAudience
    session_id: DomainId
    lane_id: str
    version: str
    turns: tuple[ConversationTurn, ...]
    _seal: object = field(default=None, init=False, repr=False, compare=False)
    _validator: object = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        require(self.scope, WorldScope)
        require(self.viewer, MemoryAudience)
        check_id(self.session_id, IdKind.SESSION)
        _text(self.lane_id, 256)
        _text(self.version, 256)
        if type(self.turns) is not tuple or len(self.turns) > MAX_CONVERSATION_TURNS or any(type(x) is not ConversationTurn for x in self.turns):
            fail(PromptFailure.BUDGET_INPUT)

    @classmethod
    def from_trusted_adapter(cls, scope, viewer, session_id, lane_id, version, turns, validator):
        if validator is None or not callable(getattr(validator, 'current_version', None)):
            fail(PromptFailure.UNSUPPORTED_CAPABILITY)
        value = cls(scope, viewer, session_id, lane_id, version, turns)
        if validator.current_version(scope, viewer, session_id, lane_id) != version:
            fail(PromptFailure.SESSION_STALE)
        object.__setattr__(value, '_validator', validator)
        object.__setattr__(value, '_seal', _TRUSTED)
        return value


@dataclass(frozen=True)
class PromptMemoryProjection:
    context: SessionMemoryContext
    runtime_id: str
    generation: str
    query: str
    limit: int
    history: bool
    memory_id: DomainId | None
    result: MemoryQueryResult
    _seal: object = field(default=None, init=False, repr=False, compare=False)
    _runtime: object = field(default=None, init=False, repr=False, compare=False)

    @classmethod
    def from_session_query(cls, runtime, context, *, query='', limit=20, history=False, memory_id=None):
        if type(context) is not SessionMemoryContext or history is not False:
            fail(PromptFailure.AUTHORIZATION_DENIED)
        if not callable(getattr(runtime, 'query', None)):
            fail(PromptFailure.INVALID_ARGUMENT)
        try:
            result = runtime.query(context, query=query, limit=limit, history=False, memory_id=memory_id)
        except Exception:
            fail(PromptFailure.AUTHORIZATION_DENIED)
        cls.validate_records(context, result)
        value = cls(context, runtime.repository.runtime_id, runtime.repository.generation,
                    query, limit, False, memory_id, result)
        object.__setattr__(value, '_seal', _TRUSTED)
        object.__setattr__(value, '_runtime', runtime)
        return value

    @staticmethod
    def validate_records(context, result):
        if type(result) is not MemoryQueryResult or type(result.version) is not str or not result.version:
            fail(PromptFailure.AUTHORIZATION_DENIED)
        for record in result.records:
            if type(record) is not MemoryRecord or record.scope != context.scope:
                fail(PromptFailure.SCOPE_MISMATCH)
            from .domain import CanonStatus
            from .memory import MemoryLifecycle
            if (record.lifecycle is not MemoryLifecycle.LIVE or
                    record.provenance.canon_status is not CanonStatus.ACCEPTED or
                    not any(a.kind is AudienceKind.WORLD or a == context.viewer for a in record.audience)):
                fail(PromptFailure.AUTHORIZATION_DENIED)


@dataclass(frozen=True)
class PromptStoryProjection:
    context: SessionStoryContext
    runtime_id: str
    generation: str
    result: StoryProjection
    _seal: object = field(default=None, init=False, repr=False, compare=False)
    _runtime: object = field(default=None, init=False, repr=False, compare=False)

    @classmethod
    def from_session_projection(cls, runtime, context):
        if type(context) is not SessionStoryContext or not callable(getattr(runtime, 'get_story_projection', None)):
            fail(PromptFailure.AUTHORIZATION_DENIED)
        try:
            result = runtime.get_story_projection(context)
        except Exception:
            fail(PromptFailure.SESSION_STALE)
        if result.scope != context.scope or result.viewer != context.viewer:
            fail(PromptFailure.AUTHORIZATION_DENIED)
        value = cls(context, runtime.repository.runtime_id, runtime.repository.generation, result)
        object.__setattr__(value, '_seal', _TRUSTED)
        object.__setattr__(value, '_runtime', runtime)
        return value


@dataclass(frozen=True)
class PromptLoreProjection:
    request: LoreActivationRequest
    runtime_id: str
    generation: str
    result: LoreActivationResult
    _seal: object = field(default=None, init=False, repr=False, compare=False)
    _runtime: object = field(default=None, init=False, repr=False, compare=False)

    @classmethod
    def from_activation(cls, runtime, request):
        if type(request) is not LoreActivationRequest or not callable(getattr(runtime, 'activate', None)):
            fail(PromptFailure.AUTHORIZATION_DENIED)
        try:
            result = runtime.activate(request)
        except Exception:
            fail(PromptFailure.LORE_STALE)
        if (result.scope != request.context.scope or result.viewer != request.context.viewer or
                result.session_id != request.context.session_id or result.writer_epoch != request.context.writer_epoch or
                result.runtime_id != request.context.runtime_id):
            fail(PromptFailure.AUTHORIZATION_DENIED)
        value = cls(request, runtime.repository.runtime_id, runtime.repository.generation, result)
        object.__setattr__(value, '_seal', _TRUSTED)
        object.__setattr__(value, '_runtime', runtime)
        return value


@dataclass(frozen=True)
class PromptBridgeProjection:
    """只由 Bridge Runtime 当前投影生成；token 本身不提供授权。"""
    result: BridgeProjection
    _runtime: object = field(default=None, init=False, repr=False, compare=False)
    _seal: object = field(default=None, init=False, repr=False, compare=False)

    @classmethod
    def from_bridge_projection(cls, runtime, projection):
        from .bridge_runtime import BridgeRuntime
        if type(projection) is not BridgeProjection or type(runtime) is not BridgeRuntime:
            fail(PromptFailure.AUTHORIZATION_DENIED)
        try:
            runtime.revalidate_projection(projection)
        except BridgeRuntimeError:
            fail(PromptFailure.BRIDGE_STALE)
        value = cls(projection)
        object.__setattr__(value, '_runtime', runtime)
        object.__setattr__(value, '_seal', _TRUSTED)
        return value


@dataclass(frozen=True)
class PromptSessionContext:
    principal: Principal
    scope: WorldScope
    session_id: DomainId
    writer_epoch: WriterEpoch
    runtime_id: str
    generation: str
    viewer: MemoryAudience
    world_revision: Revision
    purpose: PromptPurpose

    def __post_init__(self):
        require(self.principal, Principal)
        require(self.scope, WorldScope)
        check_id(self.session_id, IdKind.SESSION)
        require(self.writer_epoch, WriterEpoch)
        _text(self.runtime_id, 128)
        _text(self.generation, 256)
        require(self.viewer, MemoryAudience)
        require(self.world_revision, Revision)
        if type(self.purpose) is not PromptPurpose:
            fail(PromptFailure.UNSUPPORTED_PURPOSE)


@dataclass(frozen=True)
class PromptAssemblyRequest:
    session: PromptSessionContext
    definition: CharacterDefinition | None
    character: CharacterInstance | None
    memory: PromptMemoryProjection
    lore: PromptLoreProjection
    story: PromptStoryProjection
    conversation: ConversationProjection
    budget: PromptBudget
    bridges: tuple[PromptBridgeProjection, ...] = ()


@dataclass(frozen=True)
class PromptRequirements:
    capabilities: tuple[Capability, ...] = (
        Capability.STABLE_PRINCIPAL, Capability.STABLE_SESSION, Capability.MESSAGE_PROVENANCE,
        Capability.ISOLATED_CONTEXT_LANE, Capability.HISTORY_ISOLATION)


@dataclass(frozen=True)
class PromptSnapshot:
    scope: WorldScope
    principal: Principal
    viewer: MemoryAudience
    purpose: PromptPurpose
    session_id: DomainId
    writer_epoch: WriterEpoch
    runtime_id: str
    generation: str
    definition_ref: DefinitionRef | None
    character_instance_id: DomainId | None
    world_revision: Revision
    memory_version: str
    memory_query_spec: tuple
    lore_binding_revision: LoreBindingRevision
    lore_version: str
    lore_book_versions: tuple
    story_revision: StoryRevision
    story_projection_version: str
    story_snapshot_token: str
    conversation_lane_id: str
    conversation_version: str
    template_version: str
    sections: tuple[PromptSection, ...]
    budget: PromptBudget
    budget_used: int
    token_used: int | None
    token_safe: bool
    diagnostics: tuple[PromptDiagnostic, ...]
    budget_exhausted: bool
    requirements: PromptRequirements
    bridge_snapshots: tuple
    fingerprint: str
    snapshot_token: str
    _request: PromptAssemblyRequest = field(repr=False, compare=False)
