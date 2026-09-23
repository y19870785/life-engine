"""受信 Owner/Session 显式接受与限域 Story 投影服务。"""
from datetime import datetime, timezone
from functools import wraps
import hashlib
import hmac
import secrets

from .domain import (BindingStatus, DomainError, DomainId, IdKind, WorldKind,
                     WorldStatus, check_id, require)
from .memory import AudienceKind, MemoryAudience
from .story import (MAX_STORY_STATE_BYTES, OwnerStoryContext, SessionStoryContext,
                    StoryClock, StoryEvent, StoryEventProposal, StoryIdempotencyIdentity,
                    StoryProjection, StoryReceipt, StoryRevision)
from .story_codec import payload_data, scope_values, state_dump
from .story_reducer import reduce_story, replay_story
from .story_repository import StoryFailure as SC, StoryRuntimeError, fail
from .world_codec import dumps, provenance_dump
from .world_repository import FailureCode as WC, WorldRuntimeError


def checked(method):
    @wraps(method)
    def call(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except StoryRuntimeError:
            raise
        except WorldRuntimeError as exc:
            if exc.code in (WC.STORAGE_CORRUPT,WC.SCHEMA_MISMATCH,WC.STORAGE_BUSY,WC.RECOVERY_REQUIRED):
                fail({WC.STORAGE_CORRUPT:SC.STORAGE_CORRUPT,WC.SCHEMA_MISMATCH:SC.SCHEMA_MISMATCH,
                      WC.STORAGE_BUSY:SC.STORAGE_BUSY,WC.RECOVERY_REQUIRED:SC.RECOVERY_REQUIRED}[exc.code])
            fail(SC.NOT_AVAILABLE)
        except (DomainError, TypeError, ValueError, KeyError, AttributeError):
            fail(SC.INVALID_ARGUMENT)
    return call


def _owner(context):
    require(context,OwnerStoryContext)


def _world(tx, context, *, write=False):
    snap = tx.world.get_world(context.scope.world_id)
    if (snap.timeline.scope != context.scope or snap.world.owner_id != context.principal.owner_id):
        fail(SC.NOT_AVAILABLE)
    if write and snap.world.status not in (WorldStatus.CREATED,WorldStatus.ACTIVE,WorldStatus.SUSPENDED):
        fail(SC.NOT_AVAILABLE)
    return snap


def _session(tx, context):
    require(context,SessionStoryContext)
    snap = _world(tx,context)
    if context.runtime_id is None:
        fail(SC.SESSION_STALE)
    try:
        binding = tx.world.get_session(context.session_id)
    except WorldRuntimeError as exc:
        if exc.code is WC.SESSION_NOT_FOUND:
            fail(SC.SESSION_STALE)
        raise
    if (snap.world.status is not WorldStatus.ACTIVE or binding.scope != context.scope or
            binding.principal != context.principal or binding.status is not BindingStatus.OPEN or
            binding.writer_epoch != context.writer_epoch or snap.world.writer_epoch != context.writer_epoch):
        fail(SC.SESSION_STALE)
    viewer = (MemoryAudience(AudienceKind.SOUL,context.scope.soul_id)
        if snap.world.kind is WorldKind.SOUL else
        MemoryAudience(AudienceKind.CHARACTER_INSTANCE,binding.character_instance_id))
    if context.viewer != viewer:
        fail(SC.SESSION_STALE)
    return snap,binding


def _fingerprint(scope, expected, proposal):
    p = proposal
    value = [scope_values(scope),expected.value,p.kind.value,p.payload_version,
        payload_data(p.kind,p.payload),provenance_dump(p.provenance),
        [[ref.kind.value,ref.identity] for ref in p.source_refs],
        str(p.character_actor_id) if p.character_actor_id else None,
        str(p.supersedes_event_id) if p.supersedes_event_id else None]
    return hashlib.sha256(dumps(value).encode('utf-8')).hexdigest()


class StoryRuntime:
    """业务层不执行 SQL，也不读取 Memory、Lore、宿主或外部资源。"""
    def __init__(self, repository):
        self.repository = repository
        self._token_key = secrets.token_bytes(32)

    @checked
    def accept_story_event(self, context, expected_revision, proposal, identity):
        if type(context) not in (OwnerStoryContext,SessionStoryContext):
            fail(SC.AUTHORIZATION_DENIED)
        require(expected_revision,StoryRevision)
        require(proposal,StoryEventProposal)
        require(identity,StoryIdempotencyIdentity)
        if proposal.provenance.actor.owner_id != context.scope.owner_id:
            fail(SC.AUTHORIZATION_DENIED)
        if type(context) is SessionStoryContext and context.runtime_id != self.repository.runtime_id:
            fail(SC.SESSION_STALE)
        stamp = _fingerprint(context.scope,expected_revision,proposal)
        with self.repository.transaction() as tx:
            snap = _world(tx,context,write=True) if type(context) is OwnerStoryContext else _session(tx,context)[0]
            replay = tx.replay(identity,context.principal.principal_id,stamp)
            if replay:
                return replay
            current = tx.state(context.scope)
            tx.cas(context.scope,expected_revision)
            if current.revision != expected_revision:
                fail(SC.REVISION_CONFLICT)
            if proposal.supersedes_event_id is not None:
                target = tx.event(context.scope,proposal.supersedes_event_id)
                if target is None or target.sequence > current.last_event_sequence:
                    fail(SC.EVENT_CONFLICT)
            characters = {item.character_instance_id for item in snap.characters}
            p = proposal.payload
            needed = tuple(x for x in (proposal.character_actor_id,
                getattr(p,'character_id',None),getattr(p,'source_id',None),getattr(p,'target_id',None)) if x is not None)
            if any(item not in characters for item in needed):
                fail(SC.EVENT_CONFLICT)
            next_revision = current.revision.next()
            next_clock = current.clock.next()
            event = StoryEvent(DomainId.new(IdKind.EVENT),context.scope,current.last_event_sequence+1,
                next_revision,next_clock,proposal,context.principal.principal_id,datetime.now(timezone.utc))
            try:
                projected = reduce_story(current,event)
            except DomainError:
                fail(SC.EVENT_CONFLICT)
            if len(state_dump(projected).encode('utf-8')) > MAX_STORY_STATE_BYTES:
                fail(SC.BUDGET_INPUT)
            tx.insert(event,projected,identity,stamp)
            return StoryReceipt(event.event_id,next_revision,next_clock)

    @checked
    def get_story_state(self, context):
        _owner(context)
        with self.repository.transaction() as tx:
            _world(tx,context)
            return tx.state(context.scope)

    @checked
    def story_revision(self, context):
        return self.get_story_state(context).revision

    @checked
    def list_story_events(self, context, *, after=0, limit=100):
        _owner(context)
        if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 100:
            fail(SC.INVALID_ARGUMENT)
        with self.repository.transaction() as tx:
            _world(tx,context)
            return tx.events(context.scope,after=after,limit=limit)

    @checked
    def get_story_event(self, context, event_id):
        _owner(context)
        check_id(event_id,IdKind.EVENT)
        with self.repository.transaction() as tx:
            _world(tx,context)
            result = tx.event(context.scope,event_id)
            if result is None:
                fail(SC.NOT_AVAILABLE)
            return result

    @checked
    def replay_verify(self, context):
        _owner(context)
        with self.repository.transaction() as tx:
            _world(tx,context)
            current = tx.state(context.scope)
            events = []
            after = 0
            while True:
                page = tx.events(context.scope,after=after,limit=100)
                if not page:
                    break
                events.extend(page)
                after = page[-1].sequence
            if replay_story(context.scope,events) != current:
                fail(SC.STORAGE_CORRUPT)
            return current

    @checked
    def get_story_projection(self, context):
        require(context,SessionStoryContext)
        if context.runtime_id != self.repository.runtime_id:
            fail(SC.SESSION_STALE)
        with self.repository.transaction() as tx:
            _,binding = _session(tx,context)
            state = tx.state(context.scope)
            character = binding.character_instance_id
            own = tuple((key,value) for ident,key,value in state.character_states if ident == character)
            relations = tuple(row for row in state.relationships if character is not None and character in row[:2])
            opened = tuple(thread for thread in state.threads if thread.status.value == 'open')
            token_data = dumps([self.repository.generation,self.repository.runtime_id,
                scope_values(context.scope),str(context.principal.principal_id),
                str(context.session_id),context.writer_epoch.value,context.viewer.kind.value,
                str(context.viewer.target),state_dump(state)])
            token = hmac.new(self._token_key,token_data.encode('utf-8'),hashlib.sha256).hexdigest()
            return StoryProjection(context.scope,context.viewer,state.revision,state.clock,
                state.projection_version,state.world_facts,own,relations,opened,token)
