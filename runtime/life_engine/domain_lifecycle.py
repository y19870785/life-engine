"""Pure lifecycle transitions and fencing checks; caller owns storage and authentication."""
from dataclasses import dataclass, replace
from enum import Enum

from .domain import (BindingStatus, CharacterInstance, DomainError, IdKind, Principal, Provenance,
                     Revision, SessionBinding, Soul, World, WorldKind, WorldScope,
                     WorldState, WorldStatus, WorldTimeline, WriterEpoch, check_id, require)


class WorldCommand(Enum):
    CREATE = 'create'
    ENTER = 'enter'
    SUSPEND = 'suspend'
    RESUME = 'resume'
    EXIT = 'exit'
    ARCHIVE = 'archive'
    UNARCHIVE = 'unarchive'
    DELETE = 'delete'


class WorldEvent(Enum):
    CREATED = 'world_created'
    ENTERED = 'world_entered'
    SUSPENDED = 'world_suspended'
    RESUMED = 'world_resumed'
    EXITED = 'world_exited'
    ARCHIVED = 'world_archived'
    UNARCHIVED = 'world_unarchived'
    TOMBSTONED = 'world_tombstoned'


@dataclass(frozen=True)
class Transition:
    world: World
    event: WorldEvent


def create_world(soul, principal, world_id, kind, provenance):
    """Explicit CREATE evaluation, returning objects only; never registers a live world."""
    require(soul, Soul)
    require(principal, Principal)
    require(kind, WorldKind)
    require(provenance, Provenance)
    check_id(world_id, IdKind.WORLD)
    if principal.owner_id != soul.owner_id or provenance.actor != principal:
        raise DomainError('Creation owner/actor mismatch')
    if (kind is WorldKind.SOUL) != (world_id == soul.soul_world_id):
        raise DomainError('Soul World must match the reserved default world ID')
    return Transition(World(world_id, soul.owner_id, soul.soul_id, kind, provenance), WorldEvent.CREATED)


def validate_fence(world, principal, expected_revision, writer_epoch):
    require(world, World)
    require(principal, Principal)
    require(expected_revision, Revision)
    require(writer_epoch, WriterEpoch)
    if principal.owner_id != world.owner_id:
        raise DomainError('Wrong owner')
    if expected_revision != world.revision:
        raise DomainError('Stale revision')
    if writer_epoch != world.writer_epoch:
        raise DomainError('Stale writer epoch')


_TRANSITIONS = {
    WorldCommand.ENTER: ((WorldStatus.CREATED,), WorldStatus.ACTIVE, WorldEvent.ENTERED),
    WorldCommand.SUSPEND: ((WorldStatus.ACTIVE,), WorldStatus.SUSPENDED, WorldEvent.SUSPENDED),
    WorldCommand.RESUME: ((WorldStatus.SUSPENDED,), WorldStatus.ACTIVE, WorldEvent.RESUMED),
    WorldCommand.EXIT: ((WorldStatus.ACTIVE,), WorldStatus.SUSPENDED, WorldEvent.EXITED),
    WorldCommand.ARCHIVE: ((WorldStatus.CREATED, WorldStatus.SUSPENDED), WorldStatus.ARCHIVED, WorldEvent.ARCHIVED),
    WorldCommand.UNARCHIVE: ((WorldStatus.ARCHIVED,), WorldStatus.SUSPENDED, WorldEvent.UNARCHIVED),
    WorldCommand.DELETE: ((WorldStatus.ARCHIVED,), WorldStatus.TOMBSTONED, WorldEvent.TOMBSTONED),
}


def transition_world(world, command, principal, expected_revision, writer_epoch):
    require(command, WorldCommand)
    validate_fence(world, principal, expected_revision, writer_epoch)
    if command not in _TRANSITIONS:
        raise DomainError('CREATE requires create_world, not an existing world')
    allowed, target, event = _TRANSITIONS[command]
    if world.status not in allowed:
        raise DomainError('Illegal lifecycle transition')
    if world.kind is WorldKind.SOUL and command in (
            WorldCommand.SUSPEND, WorldCommand.EXIT, WorldCommand.ARCHIVE,
            WorldCommand.UNARCHIVE, WorldCommand.DELETE):
        raise DomainError('Soul World uses default-life policy; roleplay lifecycle command denied')
    return Transition(replace(world, status=target, revision=world.revision.next(),
                              writer_epoch=world.writer_epoch.next()), event)


def bind_session(world, timeline, principal, session_id, character=None):
    require(world, World)
    require(timeline, WorldTimeline)
    require(principal, Principal)
    timeline.scope.validate_world(world)
    if world.status is not WorldStatus.ACTIVE or principal.owner_id != world.owner_id:
        raise DomainError('Binding requires active world and matching owner')
    if world.kind is WorldKind.ROLEPLAY:
        require(character, CharacterInstance)
        if character.scope != timeline.scope:
            raise DomainError('Character belongs to another world/timeline')
    elif character is not None:
        raise DomainError('Soul binding does not impersonate a CharacterInstance')
    return SessionBinding(session_id, principal, timeline.scope,
                          character.character_instance_id if character else None, world.writer_epoch)


def _validate_binding(world, binding, principal):
    require(binding, SessionBinding)
    require(principal, Principal)
    if binding.status is not BindingStatus.OPEN or binding.principal != principal:
        raise DomainError('Closed session or different principal')
    binding.scope.validate_world(world)
    if (world.kind is WorldKind.ROLEPLAY) != (binding.character_instance_id is not None):
        raise DomainError('Binding character does not match world kind')


def validate_write(world, binding, principal, reference, expected_revision):
    """Validate against the current authoritative world snapshot, never a cached old world."""
    _validate_binding(world, binding, principal)
    if world.status is not WorldStatus.ACTIVE:
        raise DomainError('World is not writable')
    validate_fence(world, principal, expected_revision, binding.writer_epoch)
    if type(reference) not in (WorldState, CharacterInstance):
        raise DomainError('Expected scoped state or character reference')
    if reference.scope != binding.scope:
        raise DomainError('Cross-world/timeline reference')
    if isinstance(reference, CharacterInstance) and reference.character_instance_id != binding.character_instance_id:
        raise DomainError('Different character instance')


class CloseReason(Enum):
    EXIT = 'exit'
    SWITCH = 'switch'


def close_session(world, binding, principal, expected_revision, reason=CloseReason.EXIT):
    """Single-writer/last-participant contract. SWITCH only closes source, never opens target."""
    require(reason, CloseReason)
    _validate_binding(world, binding, principal)
    validate_fence(world, principal, expected_revision, binding.writer_epoch)
    if world.kind is WorldKind.SOUL:
        # Closing a host conversation does not stop the default world's life clock.
        if world.status is not WorldStatus.ACTIVE:
            raise DomainError('World is not active')
        updated = replace(world, revision=world.revision.next(), writer_epoch=world.writer_epoch.next())
    else:
        updated = transition_world(world, WorldCommand.EXIT, principal,
                                   expected_revision, binding.writer_epoch).world
    return updated, replace(binding, status=BindingStatus.CLOSED)
