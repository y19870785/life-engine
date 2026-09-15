"""SP-004A immutable domain contracts. No storage, host SDK, or runtime activation."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class DomainError(ValueError):
    """Invalid domain value or incompatible reference."""


def require(value, cls):
    if type(value) is not cls:
        raise DomainError(f'Expected {cls.__name__}')


class IdKind(Enum):
    OWNER = 'owner'
    PRINCIPAL = 'principal'
    SOUL = 'soul'
    WORLD = 'world'
    TIMELINE = 'timeline'
    DEFINITION = 'character_definition'
    CHARACTER = 'character_instance'
    SESSION = 'session'
    EVENT = 'event'
    GRANT = 'grant'


@dataclass(frozen=True)
class DomainId:
    kind: IdKind
    value: UUID

    def __post_init__(self):
        require(self.kind, IdKind)
        require(self.value, UUID)
        if self.value.version != 4:
            raise DomainError('Domain IDs require random UUID4 values')

    @classmethod
    def new(cls, kind):
        return cls(kind, uuid4())

    def __str__(self):
        return f'{self.kind.value}:{self.value}'

    @classmethod
    def parse(cls, text):
        try:
            kind, value = text.split(':', 1)
            result = cls(IdKind(kind), UUID(value))
            if str(result) != text:
                raise ValueError('Noncanonical ID')
            return result
        except (AttributeError, ValueError) as exc:
            raise DomainError('Invalid canonical domain ID') from exc


def check_id(value, kind):
    require(value, DomainId)
    if value.kind is not kind:
        raise DomainError(f'Expected {kind.value} ID')


@dataclass(frozen=True)
class Revision:
    value: int = 0

    def __post_init__(self):
        if type(self.value) is not int or self.value < 0:
            raise DomainError('Counter must be a nonnegative integer')

    def next(self):
        return type(self)(self.value + 1)


@dataclass(frozen=True)
class WriterEpoch(Revision):
    """Fencing generation, distinct from a state revision."""


@dataclass(frozen=True)
class DefinitionVersion(Revision):
    def __post_init__(self):
        super().__post_init__()
        if self.value < 1:
            raise DomainError('Definition version starts at 1')


class WorldKind(Enum):
    SOUL = 'soul'
    ROLEPLAY = 'roleplay'


class WorldStatus(Enum):
    CREATED = 'created'
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    ARCHIVED = 'archived'
    TOMBSTONED = 'tombstoned'


class RealityStatus(Enum):
    OBSERVED_REAL_WORLD_FACT = 'observed_real_world_fact'
    USER_CLAIMED = 'user_claimed_fact'
    AGENT_INFERRED = 'agent_inferred_fact'
    SIMULATED_LIFE_STATE = 'simulated_life_state'
    FICTIONAL = 'fictional'
    FICTIONAL_SHARED_EXPERIENCE = 'fictional_shared_experience'
    UNKNOWN = 'unknown'
    LEGACY_UNREVIEWED = 'legacy_unreviewed'


class CanonStatus(Enum):
    CANDIDATE = 'candidate'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    UNREVIEWED = 'unreviewed'


class SourceType(Enum):
    OBSERVATION = 'observation'
    USER_REPORT = 'user_report'
    MODEL = 'model'
    SIMULATION = 'simulation'
    IMPORT = 'import'
    BRIDGE = 'bridge'
    LEGACY = 'legacy'
    OWNER_COMMAND = 'owner_command'


@dataclass(frozen=True)
class Owner:
    owner_id: DomainId

    def __post_init__(self):
        check_id(self.owner_id, IdKind.OWNER)


@dataclass(frozen=True)
class Principal:
    """Authenticated caller assertion supplied by a future trusted adapter, not a credential."""
    principal_id: DomainId
    owner_id: DomainId

    def __post_init__(self):
        check_id(self.principal_id, IdKind.PRINCIPAL)
        check_id(self.owner_id, IdKind.OWNER)


def aware(value):
    require(value, datetime)
    if value.utcoffset() is None:
        raise DomainError('Timestamp must include timezone')


@dataclass(frozen=True)
class Provenance:
    source_type: SourceType
    source_id: str
    created_at: datetime
    actor: Principal
    reality_status: RealityStatus
    canon_status: CanonStatus = CanonStatus.CANDIDATE
    source_world_id: DomainId | None = None
    source_timeline_id: DomainId | None = None
    source_session_id: DomainId | None = None
    source_event_id: DomainId | None = None

    def __post_init__(self):
        require(self.source_type, SourceType)
        require(self.actor, Principal)
        require(self.reality_status, RealityStatus)
        require(self.canon_status, CanonStatus)
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise DomainError('Source reference required')
        aware(self.created_at)
        for value, kind in ((self.source_world_id, IdKind.WORLD),
                            (self.source_timeline_id, IdKind.TIMELINE),
                            (self.source_session_id, IdKind.SESSION), (self.source_event_id, IdKind.EVENT)):
            if value is not None:
                check_id(value, kind)
        if self.source_timeline_id and not self.source_world_id:
            raise DomainError('Source timeline requires source world')
        if (self.source_session_id or self.source_event_id) and not self.source_timeline_id:
            raise DomainError('Source session/event requires world and timeline')
        if self.reality_status is RealityStatus.OBSERVED_REAL_WORLD_FACT and self.source_type not in (
                SourceType.OBSERVATION, SourceType.BRIDGE):
            raise DomainError('Claims/inferences cannot declare observed facts')


@dataclass(frozen=True)
class Soul:
    soul_id: DomainId
    owner_id: DomainId
    soul_world_id: DomainId

    def __post_init__(self):
        check_id(self.soul_id, IdKind.SOUL)
        check_id(self.owner_id, IdKind.OWNER)
        check_id(self.soul_world_id, IdKind.WORLD)


@dataclass(frozen=True)
class World:
    world_id: DomainId
    owner_id: DomainId
    soul_id: DomainId
    kind: WorldKind
    provenance: Provenance
    status: WorldStatus = WorldStatus.CREATED
    revision: Revision = Revision()
    writer_epoch: WriterEpoch = WriterEpoch()

    def __post_init__(self):
        check_id(self.world_id, IdKind.WORLD)
        check_id(self.owner_id, IdKind.OWNER)
        check_id(self.soul_id, IdKind.SOUL)
        require(self.kind, WorldKind)
        require(self.status, WorldStatus)
        require(self.revision, Revision)
        require(self.writer_epoch, WriterEpoch)
        require(self.provenance, Provenance)
        if self.provenance.actor.owner_id != self.owner_id:
            raise DomainError('World provenance belongs to another owner')
        if self.kind is WorldKind.SOUL and self.status in (WorldStatus.ARCHIVED, WorldStatus.TOMBSTONED):
            raise DomainError('Default Soul World cannot be archived/deleted by world lifecycle')


@dataclass(frozen=True)
class WorldScope:
    owner_id: DomainId
    soul_id: DomainId
    world_id: DomainId
    timeline_id: DomainId

    def __post_init__(self):
        for value, kind in ((self.owner_id, IdKind.OWNER), (self.soul_id, IdKind.SOUL),
                            (self.world_id, IdKind.WORLD), (self.timeline_id, IdKind.TIMELINE)):
            check_id(value, kind)

    def validate_world(self, world):
        require(world, World)
        if (self.owner_id, self.soul_id, self.world_id) != (world.owner_id, world.soul_id, world.world_id):
            raise DomainError('World scope mismatch')


@dataclass(frozen=True)
class WorldTimeline:
    scope: WorldScope
    provenance: Provenance
    revision: Revision = Revision()
    logical_tick: int = 0

    def __post_init__(self):
        require(self.scope, WorldScope)
        require(self.provenance, Provenance)
        if self.provenance.actor.owner_id != self.scope.owner_id:
            raise DomainError('Timeline provenance owner mismatch')
        require(self.revision, Revision)
        if type(self.logical_tick) is not int or self.logical_tick < 0:
            raise DomainError('Invalid logical tick')


@dataclass(frozen=True)
class Values:
    """Minimal immutable string properties, not a final Story/Relationship schema."""
    items: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        require(self.items, tuple)
        keys = set()
        for pair in self.items:
            if type(pair) is not tuple or len(pair) != 2 or any(type(v) is not str for v in pair):
                raise DomainError('Properties must be immutable string pairs')
            if not pair[0] or pair[0] in keys:
                raise DomainError('Property keys must be nonempty and unique')
            keys.add(pair[0])


@dataclass(frozen=True)
class WorldState:
    scope: WorldScope
    revision: Revision
    provenance: Provenance
    values: Values = Values()

    def __post_init__(self):
        require(self.scope, WorldScope)
        require(self.revision, Revision)
        require(self.provenance, Provenance)
        require(self.values, Values)
        if self.provenance.actor.owner_id != self.scope.owner_id:
            raise DomainError('State provenance owner mismatch')


@dataclass(frozen=True)
class DefinitionRef:
    definition_id: DomainId
    version: DefinitionVersion

    def __post_init__(self):
        check_id(self.definition_id, IdKind.DEFINITION)
        require(self.version, DefinitionVersion)


@dataclass(frozen=True)
class CharacterDefinition:
    reference: DefinitionRef
    owner_id: DomainId
    name: str
    traits: Values
    provenance: Provenance

    def __post_init__(self):
        require(self.reference, DefinitionRef)
        check_id(self.owner_id, IdKind.OWNER)
        require(self.traits, Values)
        require(self.provenance, Provenance)
        if type(self.name) is not str or not self.name.strip():
            raise DomainError('Definition display name required')
        if self.provenance.actor.owner_id != self.owner_id:
            raise DomainError('Definition owner mismatch')


@dataclass(frozen=True)
class CharacterInstance:
    character_instance_id: DomainId
    scope: WorldScope
    definition: DefinitionRef
    provenance: Provenance
    state: Values = Values()
    relationships: Values = Values()

    def __post_init__(self):
        check_id(self.character_instance_id, IdKind.CHARACTER)
        require(self.scope, WorldScope)
        require(self.definition, DefinitionRef)
        require(self.provenance, Provenance)
        if self.provenance.actor.owner_id != self.scope.owner_id:
            raise DomainError('Instance provenance owner mismatch')
        require(self.state, Values)
        require(self.relationships, Values)

    def validate_definition(self, definition):
        require(definition, CharacterDefinition)
        if definition.reference != self.definition or definition.owner_id != self.scope.owner_id:
            raise DomainError('Definition owner/version mismatch')


class BindingStatus(Enum):
    OPEN = 'open'
    CLOSED = 'closed'


@dataclass(frozen=True)
class SessionBinding:
    session_id: DomainId
    principal: Principal
    scope: WorldScope
    character_instance_id: DomainId | None
    writer_epoch: WriterEpoch
    status: BindingStatus = BindingStatus.OPEN

    def __post_init__(self):
        check_id(self.session_id, IdKind.SESSION)
        require(self.principal, Principal)
        require(self.scope, WorldScope)
        require(self.writer_epoch, WriterEpoch)
        require(self.status, BindingStatus)
        if self.character_instance_id is not None:
            check_id(self.character_instance_id, IdKind.CHARACTER)
        if self.principal.owner_id != self.scope.owner_id:
            raise DomainError('Session owner mismatch')
