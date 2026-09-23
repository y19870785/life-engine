"""附着既有运行代次的 Story SQLite 仓储与只读数据验证。"""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import re
import sqlite3

from .domain import DomainError, DomainId, IdKind, check_id
from .story import (MAX_STORY_STATE_BYTES, StoryClock, StoryEvent, StoryEventKind, StoryEventProposal,
                    StoryEventSourceReference, StoryReceipt, StoryRevision, SourceReferenceKind)
from .story_codec import (payload_decode, payload_dump, scope_load, scope_values, state_dump,
                          state_load)
from .story_reducer import replay_story
from .story_repository import StoryFailure as SC, StoryRuntimeError, fail
from .world_codec import provenance_dump, provenance_load
from .world_repository import FailureCode as WC, WorldRuntimeError
from .world_schema import validate_schema
from .world_sqlite_repository import _SQLiteTransaction

SCOPE_SQL = 'owner_id=? AND soul_id=? AND world_id=? AND timeline_id=?'


def _id(value, kind):
    result = DomainId.parse(value)
    check_id(result, kind)
    return result


def decoded(function):
    """持久数据解码失败固定映射为损坏，不暴露正文。"""
    def call(*args):
        try:
            return function(*args)
        except StoryRuntimeError:
            raise
        except (DomainError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError):
            fail(SC.STORAGE_CORRUPT)
    return call


@decoded
def _state(row):
    if type(row['projection']) is not str or len(row['projection'].encode('utf-8')) > MAX_STORY_STATE_BYTES:
        fail(SC.STORAGE_CORRUPT)
    return state_load(scope_load(row), row['revision'], row['logical_tick'],
                      row['last_event_sequence'], row['projection_version'], row['projection'])


@decoded
def _event(db, row):
    sources = db.execute('SELECT position,source_kind,source_identity FROM story_event_sources '
        'WHERE event_id=? ORDER BY position', (row['event_id'],)).fetchall()
    if [item['position'] for item in sources] != list(range(len(sources))):
        fail(SC.STORAGE_CORRUPT)
    refs = tuple(StoryEventSourceReference(SourceReferenceKind(item['source_kind']),item['source_identity'])
                 for item in sources)
    kind = StoryEventKind(row['event_kind'])
    provenance = provenance_load(row['provenance'])
    proposal = StoryEventProposal(kind, payload_decode(kind,row['payload']), provenance, refs,
        _id(row['character_actor_id'],IdKind.CHARACTER) if row['character_actor_id'] else None,
        _id(row['supersedes_event_id'],IdKind.EVENT) if row['supersedes_event_id'] else None,
        row['payload_version'])
    event = StoryEvent(_id(row['event_id'],IdKind.EVENT),scope_load(row),row['event_sequence'],
        StoryRevision(row['story_revision']),StoryClock(row['logical_tick']),proposal,
        _id(row['accepted_by'],IdKind.PRINCIPAL),datetime.fromisoformat(row['accepted_at']))
    if (provenance_dump(provenance) != row['provenance'] or
            provenance.created_at != datetime.fromisoformat(row['created_at']) or
            event.accepted_at.utcoffset() is None or len(refs) > 32):
        fail(SC.STORAGE_CORRUPT)
    return event


def validate_story_data(db):
    """只读全量重放校验；发现不一致只拒绝，不修补。"""
    old = db.row_factory
    db.row_factory = sqlite3.Row
    try:
        scopes = {tuple(row) for row in db.execute('SELECT w.owner_id,w.soul_id,w.world_id,t.timeline_id '
            'FROM worlds w JOIN world_timelines t ON t.world_id=w.world_id')}
        states = {}
        for row in db.execute('SELECT * FROM story_collection_state'):
            state = _state(row)
            key = scope_values(state.scope)
            states[key] = state
        if set(states) != scopes:
            fail(SC.STORAGE_CORRUPT)
        events = {}
        for row in db.execute('SELECT * FROM story_events ORDER BY world_id,timeline_id,event_sequence'):
            event = _event(db,row)
            key = scope_values(event.scope)
            if key not in states:
                fail(SC.STORAGE_CORRUPT)
            events.setdefault(key,[]).append(event)
            if event.proposal.supersedes_event_id:
                target = db.execute('SELECT owner_id,soul_id,world_id,timeline_id,event_sequence '
                    'FROM story_events WHERE event_id=?',(str(event.proposal.supersedes_event_id),)).fetchone()
                if target is None or tuple(target[k] for k in ('owner_id','soul_id','world_id','timeline_id')) != key or target['event_sequence'] >= event.sequence:
                    fail(SC.STORAGE_CORRUPT)
            for character_id in _character_ids(event):
                if not db.execute('SELECT 1 FROM character_instances WHERE character_instance_id=? '
                    'AND world_id=? AND timeline_id=?',
                    (str(character_id),str(event.scope.world_id),str(event.scope.timeline_id))).fetchone():
                    fail(SC.STORAGE_CORRUPT)
        for key, state in states.items():
            if replay_story(state.scope,events.get(key,())) != state:
                fail(SC.STORAGE_CORRUPT)
        operations = {}
        for row in db.execute('SELECT * FROM story_operations'):
            _id(row['actor'],IdKind.PRINCIPAL)
            event = db.execute('SELECT * FROM story_events WHERE event_id=?',(row['event_id'],)).fetchone()
            if (event is None or row['operation'] != 'accept' or
                    tuple(row[k] for k in ('owner_id','soul_id','world_id','timeline_id')) !=
                    tuple(event[k] for k in ('owner_id','soul_id','world_id','timeline_id')) or
                    row['revision'] != event['story_revision'] or row['actor'] != event['accepted_by'] or
                    row['accepted_at'] != event['accepted_at']):
                fail(SC.STORAGE_CORRUPT)
            operations[row['sequence']] = row
        if len(operations) != sum(map(len,events.values())):
            fail(SC.STORAGE_CORRUPT)
        idempotency = set()
        for row in db.execute('SELECT * FROM story_idempotency'):
            _id(row['producer'],IdKind.PRINCIPAL)
            if not re.fullmatch('[0-9a-f]{64}',row['fingerprint']):
                fail(SC.STORAGE_CORRUPT)
            operation = operations.get(row['operation'])
            if (operation is None or operation['event_id'] != row['event_id'] or
                    operation['actor'] != row['producer'] or operation['revision'] != row['revision'] or
                    row['logical_tick'] != row['revision']):
                fail(SC.STORAGE_CORRUPT)
            idempotency.add(row['event_id'])
        if len(idempotency) != len(operations) or db.execute('PRAGMA foreign_key_check').fetchone():
            fail(SC.STORAGE_CORRUPT)
    except StoryRuntimeError:
        raise
    except (DomainError, ValueError, TypeError, KeyError, IndexError, AttributeError, sqlite3.DatabaseError):
        fail(SC.STORAGE_CORRUPT)
    finally:
        db.row_factory = old


def _character_ids(event):
    payload = event.proposal.payload
    result = []
    if event.proposal.character_actor_id:
        result.append(event.proposal.character_actor_id)
    if hasattr(payload,'character_id'):
        result.append(payload.character_id)
    if hasattr(payload,'source_id') and hasattr(payload,'target_id'):
        result.extend((payload.source_id,payload.target_id))
    return tuple(result)


class StoryTransaction:
    """单次事务内同时读取最新 World 围栏与 Story 状态。"""
    def __init__(self, db):
        self.db = db
        self.world = _SQLiteTransaction(db)

    def state(self, scope):
        row = self.db.execute('SELECT * FROM story_collection_state WHERE '+SCOPE_SQL,
                              scope_values(scope)).fetchone()
        if row is None:
            fail(SC.STORAGE_CORRUPT)
        return _state(row)

    def replay(self, identity, producer, fingerprint):
        row = self.db.execute('SELECT * FROM story_idempotency WHERE producer=? AND source=? AND slot=?',
            (str(producer),identity.source,identity.slot)).fetchone()
        if row is None:
            return None
        if row['fingerprint'] != fingerprint:
            fail(SC.IDEMPOTENCY_CONFLICT)
        return StoryReceipt(_id(row['event_id'],IdKind.EVENT), StoryRevision(row['revision']),
                            StoryClock(row['logical_tick']))

    def cas(self, scope, expected):
        values = (expected.value+1,*scope_values(scope),expected.value)
        result = self.db.execute('UPDATE story_collection_state SET revision=? WHERE '+SCOPE_SQL+
            ' AND revision=?', values)
        if result.rowcount != 1:
            fail(SC.REVISION_CONFLICT)

    def event(self, scope, event_id):
        row = self.db.execute('SELECT * FROM story_events WHERE event_id=? AND '+SCOPE_SQL,
            (str(event_id),*scope_values(scope))).fetchone()
        return _event(self.db,row) if row else None

    def events(self, scope, *, after=0, limit=100):
        rows = self.db.execute('SELECT * FROM story_events WHERE '+SCOPE_SQL+
            ' AND event_sequence>? ORDER BY event_sequence LIMIT ?',(*scope_values(scope),after,limit)).fetchall()
        return tuple(_event(self.db,row) for row in rows)

    def insert(self, event, state, identity, fingerprint):
        s = scope_values(event.scope)
        p = event.proposal
        self.db.execute('INSERT INTO story_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (str(event.event_id),*s,event.sequence,event.revision.value,event.clock.logical_tick,
             p.kind.value,p.payload_version,payload_dump(p.kind,p.payload),provenance_dump(p.provenance),
             str(event.accepted_by),str(p.character_actor_id) if p.character_actor_id else None,
             str(p.supersedes_event_id) if p.supersedes_event_id else None,
             p.provenance.created_at.isoformat(),event.accepted_at.isoformat()))
        for position,ref in enumerate(p.source_refs):
            self.db.execute('INSERT INTO story_event_sources VALUES(?,?,?,?)',
                (str(event.event_id),position,ref.kind.value,ref.identity))
        result = self.db.execute('UPDATE story_collection_state SET logical_tick=?,last_event_sequence=?, '
            'projection_version=?,projection=? WHERE '+SCOPE_SQL+' AND revision=?',
            (state.clock.logical_tick,state.last_event_sequence,state.projection_version,state_dump(state),
             *s,state.revision.value))
        if result.rowcount != 1:
            fail(SC.REVISION_CONFLICT)
        op = self.db.execute('INSERT INTO story_operations(event_id,owner_id,soul_id,world_id,timeline_id,'
            'actor,operation,revision,accepted_at) VALUES(?,?,?,?,?,?,?,?,?)',
            (str(event.event_id),*s,str(event.accepted_by),'accept',event.revision.value,
             event.accepted_at.isoformat())).lastrowid
        self.db.execute('INSERT INTO story_idempotency VALUES(?,?,?,?,?,?,?,?)',
            (str(event.accepted_by),identity.source,identity.slot,fingerprint,str(event.event_id),
             event.revision.value,event.clock.logical_tick,op))


class SQLiteStoryRepository:
    """使用现有 life.db 和 World runtime_id；构造不会触发第二次恢复。"""
    def __init__(self, root, instance_id, *, runtime_id, timeout=5):
        from .durable import registry, state_home
        self.root, self.instance_id = Path(root).resolve(), instance_id
        if type(runtime_id) is not str or not runtime_id or not 0 < timeout <= 60:
            raise ValueError('必须附着现有 World 运行代次')
        self.runtime_id,self.timeout,self.closed = runtime_id,timeout,False
        reg = registry(self.root)
        inst = reg['instances'][instance_id]
        self.generation = inst['generation']
        self.path = state_home(self.root,inst)/'agents'/inst['agent_id']/'life.db'
        with self.transaction() as tx:
            validate_story_data(tx.db)

    @contextmanager
    def transaction(self):
        from .durable import locked, registry
        if self.closed:
            fail(SC.RECOVERY_REQUIRED)
        db = None
        try:
            with locked(self.root,'management',self.timeout), locked(self.root,self.instance_id,self.timeout):
                reg = registry(self.root)
                if reg['instances'][self.instance_id]['generation'] != self.generation:
                    fail(SC.RECOVERY_REQUIRED)
                db = sqlite3.connect(self.path.as_uri()+'?mode=rw',uri=True,
                    isolation_level=None,timeout=self.timeout)
                db.row_factory = sqlite3.Row
                db.execute('PRAGMA foreign_keys=ON')
                # WorldRuntime 直接写同库；读取也需挡住 EXIT 穿插。
                db.execute('BEGIN IMMEDIATE')
                validate_schema(db)
                row = db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()
                if row is None or row[0] != self.runtime_id:
                    fail(SC.RECOVERY_REQUIRED)
                tx = StoryTransaction(db)
                try:
                    yield tx
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
                finally:
                    tx.world._open = False
        except TimeoutError:
            fail(SC.STORAGE_BUSY)
        except sqlite3.Error as exc:
            number = getattr(exc,'sqlite_errorcode',0)&255
            fail(SC.STORAGE_BUSY if number in (sqlite3.SQLITE_BUSY,sqlite3.SQLITE_LOCKED)
                 else SC.STORAGE_CORRUPT if number in (sqlite3.SQLITE_CORRUPT,sqlite3.SQLITE_NOTADB)
                 else SC.PERSISTENCE_FAILURE)
        except WorldRuntimeError as exc:
            fail(SC.SCHEMA_MISMATCH if exc.code is WC.SCHEMA_MISMATCH else SC.STORAGE_CORRUPT)
        finally:
            if db is not None:
                db.close()

    def close(self):
        self.closed = True
