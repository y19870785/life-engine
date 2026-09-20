"""角色世界应用操作；从事务仓储取可信快照，不接入宿主或生产存储。"""
from dataclasses import dataclass, replace
from datetime import datetime
from functools import wraps

from .domain import (BindingStatus, CharacterDefinition, CharacterInstance, DefinitionRef,
                     DomainError, DomainId, IdKind, Principal, Provenance, RealityStatus,
                     CanonStatus, Revision, Soul, SourceType, Values, WorldKind, WorldScope,
                     WorldStatus, WorldTimeline, WriterEpoch, check_id, require)
from .domain_lifecycle import (WorldCommand, bind_session, close_session, create_world,
                               transition_world, validate_write)
from .world_repository import (FailureCode as Code, WorldRepository, WorldRuntimeError,
                               WorldSnapshot, fail)

_NO_EPOCH = object()
_NO_TIMELINE = object()

def checked(operation):
    """把基础值对象校验失败转换为固定代码，保留明确的业务失败分类。"""
    @wraps(operation)
    def call(*args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except WorldRuntimeError:
            raise
        except DomainError:
            raise WorldRuntimeError(Code.INVALID_ARGUMENT) from None
    return call


@dataclass(frozen=True)
class SwitchResult:
    """同一次提交得到的源、目标世界快照。"""
    source: WorldSnapshot
    target: WorldSnapshot


class WorldRuntime:
    """每个世界最多一个开放会话；主体认证由可信调用方负责。"""
    def __init__(self, repository: WorldRepository):
        self.repository = repository

    @staticmethod
    def _owner(actor, owner_id):
        require(actor, Principal)
        if actor.owner_id != owner_id:
            fail(Code.OWNER_MISMATCH)

    def _world(self, tx, actor, world_id, timeline_id=_NO_TIMELINE):
        snapshot = tx.get_world(world_id)
        self._owner(actor, snapshot.world.owner_id)
        if timeline_id is not _NO_TIMELINE:
            check_id(timeline_id, IdKind.TIMELINE)
            if snapshot.timeline.scope.timeline_id != timeline_id:
                fail(Code.TIMELINE_MISMATCH)
        return snapshot

    @staticmethod
    def _fence(snapshot, expected_revision, writer_epoch=_NO_EPOCH):
        require(expected_revision, Revision)
        if writer_epoch is not _NO_EPOCH:
            require(writer_epoch, WriterEpoch)
            if snapshot.world.writer_epoch != writer_epoch:
                fail(Code.STALE_WRITER_EPOCH)
        if snapshot.world.revision != expected_revision:
            fail(Code.REVISION_CONFLICT)

    @staticmethod
    def _provenance(actor, source_id, at):
        return Provenance(SourceType.OWNER_COMMAND, str(source_id), at, actor,
                          RealityStatus.FICTIONAL, CanonStatus.UNREVIEWED)

    def _character(self, tx, snapshot, character_id):
        character = tx.get_character(character_id)
        if character.scope.owner_id != snapshot.world.owner_id:
            fail(Code.OWNER_MISMATCH)
        if character.scope.world_id != snapshot.world.world_id:
            fail(Code.WORLD_MISMATCH)
        if character.scope.timeline_id != snapshot.timeline.scope.timeline_id:
            fail(Code.TIMELINE_MISMATCH)
        if character.scope != snapshot.timeline.scope:
            fail(Code.WORLD_MISMATCH)
        return character

    def _binding(self, tx, actor, snapshot, session_id):
        binding = tx.get_session(session_id)
        self._owner(actor, binding.principal.owner_id)
        if binding.scope.world_id != snapshot.world.world_id:
            fail(Code.WORLD_MISMATCH)
        if binding.scope.timeline_id != snapshot.timeline.scope.timeline_id:
            fail(Code.TIMELINE_MISMATCH)
        if binding.principal != actor:
            fail(Code.SESSION_BINDING_CONFLICT)
        return binding

    @checked
    def register_soul(self, actor: Principal, soul: Soul):
        require(soul, Soul)
        self._owner(actor, soul.owner_id)
        with self.repository.transaction() as tx:
            tx.add_soul(soul)

    @checked
    def register_definition(self, actor: Principal, definition: CharacterDefinition):
        require(definition, CharacterDefinition)
        self._owner(actor, definition.owner_id)
        with self.repository.transaction() as tx:
            tx.add_definition(definition)

    @checked
    def snapshot(self, actor: Principal, world_id: DomainId):
        with self.repository.transaction() as tx:
            return self._world(tx, actor, world_id)

    @checked
    def create_roleplay_world(self, actor: Principal, soul_id: DomainId, at: datetime,
                              *, world_id=None, timeline_id=None):
        with self.repository.transaction() as tx:
            soul = tx.get_soul(soul_id)
            self._owner(actor, soul.owner_id)
            world_id = world_id if world_id is not None else DomainId.new(IdKind.WORLD)
            timeline_id = timeline_id if timeline_id is not None else DomainId.new(IdKind.TIMELINE)
            provenance = self._provenance(actor, world_id, at)
            world = create_world(soul, actor, world_id, WorldKind.ROLEPLAY, provenance).world
            scope = WorldScope(soul.owner_id, soul.soul_id, world_id, timeline_id)
            result = WorldSnapshot(world, WorldTimeline(scope, provenance))
            tx.add_world(result)
            return result

    @checked
    def instantiate(self, actor, world_id, timeline_id, definition_ref: DefinitionRef,
                    expected_revision: Revision, at: datetime, *, character_id=None,
                    state=Values(), relationships=Values()):
        with self.repository.transaction() as tx:
            current = self._world(tx, actor, world_id, timeline_id)
            self._fence(current, expected_revision)
            if current.world.kind is not WorldKind.ROLEPLAY or current.world.status not in (
                    WorldStatus.CREATED, WorldStatus.SUSPENDED):
                fail(Code.INVALID_LIFECYCLE_TRANSITION)
            definition = tx.get_definition(definition_ref)
            self._owner(actor, definition.owner_id)
            cid = character_id if character_id is not None else DomainId.new(IdKind.CHARACTER)
            character = CharacterInstance(cid, current.timeline.scope, definition.reference,
                self._provenance(actor, cid, at), state, relationships)
            result = replace(current, world=replace(current.world, revision=current.world.revision.next()),
                             characters=current.characters + (character,))
            tx.save_world(result, expected_revision)
            return result

    def _open(self, tx, actor, world_id, timeline_id, character_id, expected_revision,
              writer_epoch, command, session_id):
        current = self._world(tx, actor, world_id, timeline_id)
        self._fence(current, expected_revision, writer_epoch)
        if any(s.status is BindingStatus.OPEN for s in current.sessions):
            fail(Code.SESSION_BINDING_CONFLICT)
        if (command is WorldCommand.RESUME and current.sessions
                and current.sessions[-1].character_instance_id != character_id):
            fail(Code.SESSION_BINDING_CONFLICT)
        if current.world.kind is WorldKind.ROLEPLAY:
            character = self._character(tx, current, character_id)
        else:
            if character_id is not None:
                fail(Code.SESSION_BINDING_CONFLICT)
            character = None
        # Soul 世界关闭会话后仍 ACTIVE；再次绑定只推进围栏，不挂起世界。
        if current.world.kind is WorldKind.SOUL and current.world.status is WorldStatus.ACTIVE and command is WorldCommand.ENTER:
            world = replace(current.world, revision=current.world.revision.next(),
                            writer_epoch=current.world.writer_epoch.next())
        else:
            expected_status = WorldStatus.CREATED if command is WorldCommand.ENTER else WorldStatus.SUSPENDED
            if current.world.status is not expected_status:
                fail(Code.INVALID_LIFECYCLE_TRANSITION)
            world = transition_world(current.world, command, actor, expected_revision, writer_epoch).world
        sid = session_id if session_id is not None else DomainId.new(IdKind.SESSION)
        binding = bind_session(world, current.timeline, actor, sid, character)
        result = replace(current, world=world, sessions=current.sessions + (binding,))
        tx.save_world(result, expected_revision)
        return result

    @checked
    def enter(self, actor, world_id, timeline_id, character_id, expected_revision, writer_epoch, *, session_id=None):
        with self.repository.transaction() as tx:
            return self._open(tx, actor, world_id, timeline_id, character_id, expected_revision,
                              writer_epoch, WorldCommand.ENTER, session_id)

    @checked
    def resume(self, actor, world_id, timeline_id, character_id, expected_revision, writer_epoch, *, session_id=None):
        with self.repository.transaction() as tx:
            return self._open(tx, actor, world_id, timeline_id, character_id, expected_revision,
                              writer_epoch, WorldCommand.RESUME, session_id)

    def _close(self, tx, actor, world_id, timeline_id, session_id, expected_revision, writer_epoch, suspend=False):
        current = self._world(tx, actor, world_id, timeline_id)
        binding = self._binding(tx, actor, current, session_id)
        if binding.status is BindingStatus.CLOSED:
            fail(Code.SESSION_ALREADY_CLOSED)
        self._fence(current, expected_revision, writer_epoch)
        if binding.writer_epoch != writer_epoch:
            fail(Code.STALE_WRITER_EPOCH)
        if current.world.status is not WorldStatus.ACTIVE:
            fail(Code.INVALID_LIFECYCLE_TRANSITION)
        if suspend:
            if current.world.kind is not WorldKind.ROLEPLAY:
                fail(Code.INVALID_LIFECYCLE_TRANSITION)
            world = transition_world(current.world, WorldCommand.SUSPEND, actor, expected_revision, writer_epoch).world
            closed = replace(binding, status=BindingStatus.CLOSED)
        else:
            world, closed = close_session(current.world, binding, actor, expected_revision)
        result = replace(current, world=world,
                         sessions=tuple(closed if s.session_id == session_id else s for s in current.sessions))
        tx.save_world(result, expected_revision)
        return result

    @checked
    def exit(self, actor, world_id, timeline_id, session_id, expected_revision, writer_epoch):
        with self.repository.transaction() as tx:
            return self._close(tx, actor, world_id, timeline_id, session_id, expected_revision, writer_epoch)

    @checked
    def suspend(self, actor, world_id, timeline_id, session_id, expected_revision, writer_epoch):
        with self.repository.transaction() as tx:
            return self._close(tx, actor, world_id, timeline_id, session_id, expected_revision, writer_epoch, True)

    @checked
    def switch_world(self, actor, source_world_id, source_timeline_id, source_session_id,
                     source_revision, source_epoch, target_world_id, target_timeline_id,
                     target_character_id, target_revision, target_epoch, *, session_id=None):
        if source_world_id == target_world_id:
            fail(Code.SESSION_BINDING_CONFLICT)
        with self.repository.transaction() as tx:
            source = self._close(tx, actor, source_world_id, source_timeline_id, source_session_id,
                                 source_revision, source_epoch)
            target = self._world(tx, actor, target_world_id, target_timeline_id)
            command = WorldCommand.RESUME if target.world.status is WorldStatus.SUSPENDED else WorldCommand.ENTER
            target = self._open(tx, actor, target_world_id, target_timeline_id, target_character_id,
                                target_revision, target_epoch, command, session_id)
            return SwitchResult(source, target)

    @checked
    def update_character(self, actor, world_id, timeline_id, session_id, character_id,
                         expected_revision, writer_epoch, at: datetime, *, state: Values, relationships: Values):
        """替换最小状态值以验证隔离和围栏，不求值关系、记忆或故事。"""
        with self.repository.transaction() as tx:
            current = self._world(tx, actor, world_id, timeline_id)
            binding = self._binding(tx, actor, current, session_id)
            self._fence(current, expected_revision, writer_epoch)
            if binding.writer_epoch != writer_epoch:
                fail(Code.STALE_WRITER_EPOCH)
            if binding.status is BindingStatus.CLOSED:
                fail(Code.SESSION_ALREADY_CLOSED)
            character = self._character(tx, current, character_id)
            if binding.character_instance_id != character_id:
                fail(Code.SESSION_BINDING_CONFLICT)
            validate_write(current.world, binding, actor, character, expected_revision)
            updated = replace(character, state=state, relationships=relationships,
                              provenance=self._provenance(actor, session_id, at))
            result = replace(current, world=replace(current.world, revision=current.world.revision.next()),
                characters=tuple(updated if c.character_instance_id == character_id else c for c in current.characters))
            tx.save_world(result, expected_revision)
            return result
