"""世界聚合的事务仓储合同与内存实现；不定义数据库结构。"""
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import ContextManager, Protocol

from .domain import (BindingStatus, CharacterDefinition, CharacterInstance, DefinitionRef,
                     DomainError, DomainId, IdKind, Revision, SessionBinding, Soul, World,
                     WorldKind, WorldStatus, WorldTimeline, check_id, require)


class FailureCode(str, Enum):
    WORLD_NOT_FOUND = 'WorldNotFound'
    SOUL_NOT_FOUND = 'SoulNotFound'
    DEFINITION_NOT_FOUND = 'DefinitionNotFound'
    CHARACTER_INSTANCE_NOT_FOUND = 'CharacterInstanceNotFound'
    SESSION_NOT_FOUND = 'SessionNotFound'
    OWNER_MISMATCH = 'OwnerMismatch'
    WORLD_MISMATCH = 'WorldMismatch'
    TIMELINE_MISMATCH = 'TimelineMismatch'
    INVALID_LIFECYCLE_TRANSITION = 'InvalidLifecycleTransition'
    REVISION_CONFLICT = 'RevisionConflict'
    STALE_WRITER_EPOCH = 'StaleWriterEpoch'
    SESSION_ALREADY_CLOSED = 'SessionAlreadyClosed'
    SESSION_BINDING_CONFLICT = 'SessionBindingConflict'
    IDENTITY_CONFLICT = 'IdentityConflict'
    DEFINITION_VERSION_CONFLICT = 'DefinitionVersionConflict'
    INVALID_ARGUMENT = 'InvalidArgument'
    TRANSACTION_CLOSED = 'TransactionClosed'
    NESTED_TRANSACTION = 'NestedTransaction'


class WorldRuntimeError(DomainError):
    """用固定代码区分运行失败，不携带用户内容。"""
    def __init__(self, code: FailureCode):
        self.code = code
        super().__init__(code.value)


def fail(code):
    raise WorldRuntimeError(code)


@dataclass(frozen=True)
class WorldSnapshot:
    """单时间线世界聚合；会话历史和角色实例均为不可变值。"""
    world: World
    timeline: WorldTimeline
    characters: tuple[CharacterInstance, ...] = ()
    sessions: tuple[SessionBinding, ...] = ()

    def __post_init__(self):
        require(self.world, World)
        require(self.timeline, WorldTimeline)
        require(self.characters, tuple)
        require(self.sessions, tuple)
        self.timeline.scope.validate_world(self.world)
        ids = set()
        for character in self.characters:
            require(character, CharacterInstance)
            if self.world.kind is not WorldKind.ROLEPLAY or character.scope != self.timeline.scope:
                fail(FailureCode.WORLD_MISMATCH)
            if character.character_instance_id in ids:
                fail(FailureCode.IDENTITY_CONFLICT)
            ids.add(character.character_instance_id)
        sessions, opened = set(), 0
        for binding in self.sessions:
            require(binding, SessionBinding)
            if binding.scope != self.timeline.scope:
                fail(FailureCode.WORLD_MISMATCH)
            if binding.session_id in sessions:
                fail(FailureCode.SESSION_BINDING_CONFLICT)
            sessions.add(binding.session_id)
            if (self.world.kind is WorldKind.ROLEPLAY and binding.character_instance_id not in ids
                    or self.world.kind is WorldKind.SOUL and binding.character_instance_id is not None):
                fail(FailureCode.CHARACTER_INSTANCE_NOT_FOUND)
            if binding.status is BindingStatus.OPEN:
                opened += 1
                if self.world.status is not WorldStatus.ACTIVE or binding.writer_epoch != self.world.writer_epoch:
                    fail(FailureCode.SESSION_BINDING_CONFLICT)
        if opened > 1 or (self.world.kind is WorldKind.ROLEPLAY
                          and self.world.status is WorldStatus.ACTIVE and opened != 1):
            fail(FailureCode.SESSION_BINDING_CONFLICT)


class WorldTransaction(Protocol):
    """事务内读取最新值；所有写入须一起提交或全部回滚。"""
    def get_soul(self, soul_id: DomainId) -> Soul: ...
    def get_definition(self, reference: DefinitionRef) -> CharacterDefinition: ...
    def get_world(self, world_id: DomainId) -> WorldSnapshot: ...
    def get_character(self, character_id: DomainId) -> CharacterInstance: ...
    def get_session(self, session_id: DomainId) -> SessionBinding: ...
    def add_soul(self, soul: Soul) -> None: ...
    def add_definition(self, definition: CharacterDefinition) -> None: ...
    def add_world(self, snapshot: WorldSnapshot) -> None: ...
    def save_world(self, snapshot: WorldSnapshot, expected_revision: Revision) -> None: ...


class WorldRepository(Protocol):
    """未来存储须提供串行化事务及修订号比较写入，不能分开保存聚合。"""
    def transaction(self) -> ContextManager[WorldTransaction]: ...


class _MemoryTransaction:
    """仅在持锁事务中使用的写时复制视图。"""
    def __init__(self, souls, definitions, worlds):
        self._souls, self._definitions, self._worlds = dict(souls), dict(definitions), dict(worlds)
        self._open = True

    def _check(self):
        if not self._open:
            fail(FailureCode.TRANSACTION_CLOSED)

    def get_soul(self, soul_id):
        self._check()
        check_id(soul_id, IdKind.SOUL)
        if soul_id not in self._souls:
            fail(FailureCode.SOUL_NOT_FOUND)
        return self._souls[soul_id]

    def get_definition(self, reference):
        self._check()
        require(reference, DefinitionRef)
        if reference not in self._definitions:
            fail(FailureCode.DEFINITION_NOT_FOUND)
        return self._definitions[reference]

    def get_world(self, world_id):
        self._check()
        check_id(world_id, IdKind.WORLD)
        if world_id not in self._worlds:
            fail(FailureCode.WORLD_NOT_FOUND)
        return self._worlds[world_id]

    def get_character(self, character_id):
        self._check()
        check_id(character_id, IdKind.CHARACTER)
        for snapshot in self._worlds.values():
            for character in snapshot.characters:
                if character.character_instance_id == character_id:
                    return character
        fail(FailureCode.CHARACTER_INSTANCE_NOT_FOUND)

    def get_session(self, session_id):
        self._check()
        check_id(session_id, IdKind.SESSION)
        for snapshot in self._worlds.values():
            for binding in snapshot.sessions:
                if binding.session_id == session_id:
                    return binding
        fail(FailureCode.SESSION_NOT_FOUND)

    def add_soul(self, soul):
        self._check()
        require(soul, Soul)
        if soul.soul_id in self._souls or any(s.soul_world_id == soul.soul_world_id for s in self._souls.values()):
            fail(FailureCode.IDENTITY_CONFLICT)
        if soul.soul_world_id in self._worlds:
            fail(FailureCode.IDENTITY_CONFLICT)
        self._souls[soul.soul_id] = soul

    def add_definition(self, definition):
        self._check()
        require(definition, CharacterDefinition)
        if definition.reference in self._definitions:
            fail(FailureCode.DEFINITION_VERSION_CONFLICT)
        for ref, stored in self._definitions.items():
            if ref.definition_id == definition.reference.definition_id and stored.owner_id != definition.owner_id:
                fail(FailureCode.OWNER_MISMATCH)
        self._definitions[definition.reference] = definition

    def _validate(self, snapshot):
        require(snapshot, WorldSnapshot)
        soul = self.get_soul(snapshot.world.soul_id)
        if soul.owner_id != snapshot.world.owner_id:
            fail(FailureCode.OWNER_MISMATCH)
        if (snapshot.world.kind is WorldKind.SOUL) != (snapshot.world.world_id == soul.soul_world_id):
            fail(FailureCode.WORLD_MISMATCH)
        for other_soul in self._souls.values():
            if other_soul.soul_id != soul.soul_id and other_soul.soul_world_id == snapshot.world.world_id:
                fail(FailureCode.IDENTITY_CONFLICT)
        for character in snapshot.characters:
            character.validate_definition(self.get_definition(character.definition))
        for wid, other in self._worlds.items():
            if wid == snapshot.world.world_id:
                continue
            if other.timeline.scope.timeline_id == snapshot.timeline.scope.timeline_id:
                fail(FailureCode.IDENTITY_CONFLICT)
            if {x.character_instance_id for x in other.characters} & {x.character_instance_id for x in snapshot.characters}:
                fail(FailureCode.IDENTITY_CONFLICT)
            if {x.session_id for x in other.sessions} & {x.session_id for x in snapshot.sessions}:
                fail(FailureCode.SESSION_BINDING_CONFLICT)

    def add_world(self, snapshot):
        self._check()
        require(snapshot, WorldSnapshot)
        if snapshot.world.world_id in self._worlds:
            fail(FailureCode.IDENTITY_CONFLICT)
        self._validate(snapshot)
        self._worlds[snapshot.world.world_id] = snapshot

    def save_world(self, snapshot, expected_revision):
        self._check()
        require(snapshot, WorldSnapshot)
        require(expected_revision, Revision)
        current = self.get_world(snapshot.world.world_id)
        if current.world.revision != expected_revision or snapshot.world.revision != expected_revision.next():
            fail(FailureCode.REVISION_CONFLICT)
        if (snapshot.timeline != current.timeline or snapshot.world.owner_id != current.world.owner_id
                or snapshot.world.soul_id != current.world.soul_id or snapshot.world.kind != current.world.kind):
            fail(FailureCode.WORLD_MISMATCH)
        characters = {c.character_instance_id: c for c in snapshot.characters}
        for previous in current.characters:
            updated = characters.get(previous.character_instance_id)
            if updated is None or updated.definition != previous.definition or updated.scope != previous.scope:
                fail(FailureCode.DEFINITION_VERSION_CONFLICT)
        sessions = {s.session_id: s for s in snapshot.sessions}
        for previous in current.sessions:
            updated = sessions.get(previous.session_id)
            if (updated is None or updated.principal != previous.principal or updated.scope != previous.scope
                    or updated.character_instance_id != previous.character_instance_id
                    or updated.writer_epoch != previous.writer_epoch
                    or previous.status is BindingStatus.CLOSED and updated.status is not BindingStatus.CLOSED):
                fail(FailureCode.SESSION_BINDING_CONFLICT)
        if snapshot.world.writer_epoch.value not in (current.world.writer_epoch.value,
                                                     current.world.writer_epoch.value + 1):
            fail(FailureCode.STALE_WRITER_EPOCH)
        self._validate(snapshot)
        self._worlds[snapshot.world.world_id] = snapshot


class InMemoryWorldRepository:
    """进程内串行化事务；异常不发布副本，不代表数据库或跨进程锁。"""
    def __init__(self):
        self._souls, self._definitions, self._worlds = {}, {}, {}
        self._lock = RLock()
        self._in_transaction = False

    @contextmanager
    def transaction(self):
        with self._lock:
            if self._in_transaction:
                fail(FailureCode.NESTED_TRANSACTION)
            self._in_transaction = True
            tx = _MemoryTransaction(self._souls, self._definitions, self._worlds)
            try:
                yield tx
                self._souls, self._definitions, self._worlds = tx._souls, tx._definitions, tx._worlds
            finally:
                tx._open = False
                self._in_transaction = False
