"""同一 life.db 内的世界事务仓储；每次事务独占连接并显式关闭。"""
from contextlib import contextmanager
from dataclasses import replace
from functools import wraps
from pathlib import Path
import sqlite3
from threading import local
from uuid import uuid4

from .domain import (BindingStatus, CharacterDefinition, CharacterInstance, DefinitionRef, DefinitionVersion,
    DomainId, IdKind, Principal, Revision, Soul, World, WorldKind, WorldScope, WorldStatus, WorldTimeline,
    WriterEpoch, SessionBinding, check_id, require)
from .world_codec import provenance_dump, provenance_load, values_dump, values_load
from .world_repository import (FailureCode as Code, WorldRuntimeError, WorldSnapshot, fail, validate_update)
from .world_schema import validate_schema


@contextmanager
def storage_errors():
    """基础设施错误不会伪装成找不到世界或 CAS 冲突。"""
    try:
        yield
    except sqlite3.Error as exc:
        number = getattr(exc, 'sqlite_errorcode', 0) & 255
        if number in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            fail(Code.STORAGE_BUSY)
        if number in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB):
            fail(Code.STORAGE_CORRUPT)
        fail(Code.PERSISTENCE_FAILURE)


def decoded(method):
    """读取坏数据时返回存储错误，保留实体不存在的正常结果。"""
    @wraps(method)
    def call(*args, **kwargs):
        args[0]._check()
        value = args[1] if len(args) > 1 else next(iter(kwargs.values()))
        if method.__name__ == 'get_definition':
            require(value, DefinitionRef)
        else:
            check_id(value, {'get_soul': IdKind.SOUL, 'get_world': IdKind.WORLD,
                             'get_character': IdKind.CHARACTER, 'get_session': IdKind.SESSION}[method.__name__])
        try:
            return method(*args, **kwargs)
        except WorldRuntimeError:
            raise
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            fail(Code.STORAGE_CORRUPT)
    return call


class _SQLiteTransaction:
    """连接仅在所属上下文中有效，聚合排序保留领域 tuple 的插入顺序。"""
    def __init__(self, db):
        self.db = db
        self._open = True

    def _check(self):
        if not self._open:
            fail(Code.TRANSACTION_CLOSED)

    def _one(self, sql, args, missing):
        self._check()
        row = self.db.execute(sql, args).fetchone()
        if row is None:
            fail(missing)
        return row

    @decoded
    def get_soul(self, soul_id):
        check_id(soul_id, IdKind.SOUL)
        r = self._one('SELECT * FROM souls WHERE soul_id=?', (str(soul_id),), Code.SOUL_NOT_FOUND)
        return Soul(DomainId.parse(r['soul_id']), DomainId.parse(r['owner_id']), DomainId.parse(r['soul_world_id']))

    @decoded
    def get_definition(self, reference):
        require(reference, DefinitionRef)
        r = self._one('SELECT * FROM character_definitions WHERE definition_id=? AND version=?',
                      (str(reference.definition_id), reference.version.value), Code.DEFINITION_NOT_FOUND)
        return CharacterDefinition(DefinitionRef(DomainId.parse(r['definition_id']), DefinitionVersion(r['version'])),
            DomainId.parse(r['owner_id']), r['name'], values_load(r['traits']), provenance_load(r['provenance']))

    def _scope(self, world_id, timeline_id):
        r = self._one('SELECT owner_id,soul_id FROM worlds WHERE world_id=?', (world_id,), Code.STORAGE_CORRUPT)
        return WorldScope(DomainId.parse(r['owner_id']), DomainId.parse(r['soul_id']),
                          DomainId.parse(world_id), DomainId.parse(timeline_id))

    def _character(self, r):
        result = CharacterInstance(DomainId.parse(r['character_instance_id']), self._scope(r['world_id'], r['timeline_id']),
            DefinitionRef(DomainId.parse(r['definition_id']), DefinitionVersion(r['version'])),
            provenance_load(r['provenance']), values_load(r['state']), values_load(r['relationships']))
        try:
            result.validate_definition(self.get_definition(result.definition))
        except ValueError:
            fail(Code.STORAGE_CORRUPT)
        return result

    def _session(self, r):
        return SessionBinding(DomainId.parse(r['session_id']),
            Principal(DomainId.parse(r['principal_id']), DomainId.parse(r['owner_id'])),
            self._scope(r['world_id'], r['timeline_id']),
            DomainId.parse(r['character_instance_id']) if r['character_instance_id'] is not None else None,
            WriterEpoch(r['writer_epoch']), BindingStatus(r['status']))

    @decoded
    def get_character(self, character_id):
        check_id(character_id, IdKind.CHARACTER)
        return self._character(self._one('SELECT * FROM character_instances WHERE character_instance_id=?',
            (str(character_id),), Code.CHARACTER_INSTANCE_NOT_FOUND))

    @decoded
    def get_session(self, session_id):
        check_id(session_id, IdKind.SESSION)
        return self._session(self._one('SELECT * FROM session_bindings WHERE session_id=?',
            (str(session_id),), Code.SESSION_NOT_FOUND))

    @decoded
    def get_world(self, world_id):
        check_id(world_id, IdKind.WORLD)
        r = self._one('SELECT * FROM worlds WHERE world_id=?', (str(world_id),), Code.WORLD_NOT_FOUND)
        try:
            world = World(DomainId.parse(r['world_id']), DomainId.parse(r['owner_id']), DomainId.parse(r['soul_id']),
                WorldKind(r['kind']), provenance_load(r['provenance']), WorldStatus(r['status']),
                Revision(r['revision']), WriterEpoch(r['writer_epoch']))
            t = self._one('SELECT * FROM world_timelines WHERE world_id=?', (str(world_id),), Code.STORAGE_CORRUPT)
            timeline = WorldTimeline(self._scope(t['world_id'], t['timeline_id']), provenance_load(t['provenance']),
                                     Revision(t['revision']), t['logical_tick'])
            characters = self.db.execute('SELECT * FROM character_instances WHERE world_id=? ORDER BY position',
                                         (str(world_id),)).fetchall()
            sessions = self.db.execute('SELECT * FROM session_bindings WHERE world_id=? ORDER BY position',
                                       (str(world_id),)).fetchall()
            for rows in (characters, sessions):
                if [row['position'] for row in rows] != list(range(len(rows))):
                    fail(Code.STORAGE_CORRUPT)
            result = WorldSnapshot(world, timeline, tuple(self._character(c) for c in characters),
                                   tuple(self._session(s) for s in sessions))
            self._validate(result)
            return result
        except ValueError:
            fail(Code.STORAGE_CORRUPT)

    def add_soul(self, soul):
        self._check()
        require(soul, Soul)
        if self.db.execute('SELECT 1 FROM souls WHERE soul_id=? OR soul_world_id=?',
                           (str(soul.soul_id), str(soul.soul_world_id))).fetchone() or self.db.execute(
                'SELECT 1 FROM worlds WHERE world_id=?', (str(soul.soul_world_id),)).fetchone():
            fail(Code.IDENTITY_CONFLICT)
        self.db.execute('INSERT INTO souls VALUES(?,?,?)', tuple(map(str, (soul.soul_id, soul.owner_id, soul.soul_world_id))))

    def add_definition(self, definition):
        self._check()
        require(definition, CharacterDefinition)
        ref = definition.reference
        rows = self.db.execute('SELECT version,owner_id FROM character_definitions WHERE definition_id=?',
                               (str(ref.definition_id),)).fetchall()
        if any(r['version'] == ref.version.value for r in rows):
            fail(Code.DEFINITION_VERSION_CONFLICT)
        if any(r['owner_id'] != str(definition.owner_id) for r in rows):
            fail(Code.OWNER_MISMATCH)
        self.db.execute('INSERT INTO character_definitions VALUES(?,?,?,?,?,?)',
            (str(ref.definition_id), ref.version.value, str(definition.owner_id), definition.name,
             values_dump(definition.traits), provenance_dump(definition.provenance)))

    def _validate(self, snapshot):
        require(snapshot, WorldSnapshot)
        soul = self.get_soul(snapshot.world.soul_id)
        if soul.owner_id != snapshot.world.owner_id:
            fail(Code.OWNER_MISMATCH)
        if (snapshot.world.kind is WorldKind.SOUL) != (snapshot.world.world_id == soul.soul_world_id):
            fail(Code.WORLD_MISMATCH)
        if self.db.execute('SELECT 1 FROM souls WHERE soul_world_id=? AND soul_id<>?',
                           (str(snapshot.world.world_id), str(soul.soul_id))).fetchone():
            fail(Code.IDENTITY_CONFLICT)
        for character in snapshot.characters:
            character.validate_definition(self.get_definition(character.definition))

    def _identities(self, snapshot):
        wid = str(snapshot.world.world_id)
        if self.db.execute('SELECT 1 FROM world_timelines WHERE timeline_id=? AND world_id<>?',
                           (str(snapshot.timeline.scope.timeline_id), wid)).fetchone():
            fail(Code.IDENTITY_CONFLICT)
        for table, column, objects, code in (
                ('character_instances', 'character_instance_id', snapshot.characters, Code.IDENTITY_CONFLICT),
                ('session_bindings', 'session_id', snapshot.sessions, Code.SESSION_BINDING_CONFLICT)):
            for obj in objects:
                if self.db.execute(f'SELECT 1 FROM {table} WHERE {column}=? AND world_id<>?',
                                   (str(getattr(obj, column)), wid)).fetchone():
                    fail(code)

    def _children(self, snapshot, current=None):
        wid, tid = str(snapshot.world.world_id), str(snapshot.timeline.scope.timeline_id)
        old_characters = {c.character_instance_id for c in current.characters} if current else set()
        old_sessions = {s.session_id for s in current.sessions} if current else set()
        # 暂移既有位置，允许完整保存调用方 tuple 顺序而不触发中间唯一冲突。
        if current:
            self.db.execute('UPDATE character_instances SET position=position+? WHERE world_id=?',
                            (len(snapshot.characters) + 1, wid))
            self.db.execute('UPDATE session_bindings SET position=position+? WHERE world_id=?',
                            (len(snapshot.sessions) + 1, wid))
        for position, c in enumerate(snapshot.characters):
            if c.character_instance_id in old_characters:
                self.db.execute('UPDATE character_instances SET state=?,relationships=?,provenance=?,position=? WHERE character_instance_id=?',
                    (values_dump(c.state), values_dump(c.relationships), provenance_dump(c.provenance), position, str(c.character_instance_id)))
            else:
                self.db.execute('INSERT INTO character_instances VALUES(?,?,?,?,?,?,?,?,?)',
                    (str(c.character_instance_id), wid, tid, str(c.definition.definition_id), c.definition.version.value,
                     position, values_dump(c.state), values_dump(c.relationships), provenance_dump(c.provenance)))
        # 先关闭已有会话，再插入新会话，始终满足部分唯一索引。
        for position, s in enumerate(snapshot.sessions):
            if s.session_id in old_sessions:
                self.db.execute('UPDATE session_bindings SET status=?,position=? WHERE session_id=?', (s.status.value, position, str(s.session_id)))
        for position, s in enumerate(snapshot.sessions):
            if s.session_id not in old_sessions:
                self.db.execute('INSERT INTO session_bindings VALUES(?,?,?,?,?,?,?,?,?)',
                    (str(s.session_id), str(s.principal.principal_id), str(s.principal.owner_id), wid, tid,
                     str(s.character_instance_id) if s.character_instance_id else None,
                     s.writer_epoch.value, s.status.value, position))

    def add_world(self, snapshot):
        self._check()
        self._validate(snapshot)
        w, t = snapshot.world, snapshot.timeline
        if self.db.execute('SELECT 1 FROM worlds WHERE world_id=?', (str(w.world_id),)).fetchone():
            fail(Code.IDENTITY_CONFLICT)
        self._identities(snapshot)
        self.db.execute('INSERT INTO worlds VALUES(?,?,?,?,?,?,?,?)',
            (str(w.world_id), str(w.owner_id), str(w.soul_id), w.kind.value, w.status.value,
             w.revision.value, w.writer_epoch.value, provenance_dump(w.provenance)))
        self.db.execute('INSERT INTO world_timelines VALUES(?,?,?,?,?)',
            (str(t.scope.timeline_id), str(w.world_id), t.revision.value, t.logical_tick, provenance_dump(t.provenance)))
        self._children(snapshot)

    def save_world(self, snapshot, expected_revision):
        self._check()
        require(snapshot, WorldSnapshot)
        require(expected_revision, Revision)
        current = self.get_world(snapshot.world.world_id)
        if snapshot.world.revision != expected_revision.next() or current.world.revision != expected_revision:
            fail(Code.REVISION_CONFLICT)
        validate_update(current, snapshot)
        self._validate(snapshot)
        self._identities(snapshot)
        w = snapshot.world
        changed = self.db.execute('UPDATE worlds SET status=?,revision=?,writer_epoch=?,provenance=? '
                                 'WHERE world_id=? AND revision=?',
            (w.status.value, w.revision.value, w.writer_epoch.value, provenance_dump(w.provenance),
             str(w.world_id), expected_revision.value)).rowcount
        if changed != 1:
            fail(Code.REVISION_CONFLICT)
        self._children(snapshot, current)


def validate_world_data(db):
    """启动及健康检查执行完整领域验证，普通单世界读取只按索引取该世界。"""
    old_factory = db.row_factory
    db.row_factory = sqlite3.Row
    tx = _SQLiteTransaction(db)
    try:
        for r in db.execute('SELECT soul_id FROM souls'):
            tx.get_soul(DomainId.parse(r[0]))
        for r in db.execute('SELECT definition_id,version FROM character_definitions'):
            tx.get_definition(DefinitionRef(DomainId.parse(r[0]), DefinitionVersion(r[1])))
        if db.execute('SELECT definition_id FROM character_definitions GROUP BY definition_id HAVING count(DISTINCT owner_id)>1').fetchone():
            fail(Code.STORAGE_CORRUPT)
        for r in db.execute('SELECT world_id FROM worlds'):
            tx.get_world(DomainId.parse(r[0]))
    except (ValueError, TypeError, KeyError):
        fail(Code.STORAGE_CORRUPT)
    finally:
        tx._open = False
        db.row_factory = old_factory


class SQLiteWorldRepository:
    """默认启动新运行代次并围住旧会话；同代次工作连接显式传入 runtime_id。"""
    def __init__(self, path, *, runtime_id=None, timeout=5):
        self.path = Path(path).resolve()
        if not 0 < timeout <= 60:
            raise ValueError('SQLite timeout 必须大于 0 且不超过 60 秒')
        self.timeout = timeout
        self._local = local()
        self._closed = False
        self.runtime_id = runtime_id or uuid4().hex
        with self._connection() as db:
            validate_schema(db)
            validate_world_data(db)
            if runtime_id is None:
                tx = _SQLiteTransaction(db)
                self._recover(tx)
                db.execute("INSERT INTO meta VALUES('world_runtime_id',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                           (self.runtime_id,))
                tx._open = False
            else:
                self._check_runtime(db)

    @contextmanager
    def _connection(self):
        db = None
        with storage_errors():
            try:
                db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True,
                                     timeout=self.timeout, isolation_level=None)
                db.row_factory = sqlite3.Row
                db.execute('PRAGMA foreign_keys=ON')
                db.execute('BEGIN IMMEDIATE')
                yield db
                db.commit()
            except BaseException:
                if db is not None:
                    db.rollback()
                raise
            finally:
                if db is not None:
                    db.close()

    def _check_runtime(self, db):
        row = db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()
        if row is None or row[0] != self.runtime_id:
            fail(Code.RECOVERY_REQUIRED)

    @contextmanager
    def transaction(self):
        if self._closed:
            fail(Code.TRANSACTION_CLOSED)
        if getattr(self._local, 'active', False):
            fail(Code.NESTED_TRANSACTION)
        self._local.active = True
        try:
            with self._connection() as db:
                self._check_runtime(db)
                tx = _SQLiteTransaction(db)
                try:
                    yield tx
                finally:
                    tx._open = False
        finally:
            self._local.active = False

    @staticmethod
    def _recover(tx):
        worlds = tx.db.execute("SELECT world_id FROM session_bindings WHERE status='open' ORDER BY world_id").fetchall()
        for row in worlds:
            current = tx.get_world(DomainId.parse(row[0]))
            w = current.world
            recovered = replace(current, world=replace(w, revision=w.revision.next(), writer_epoch=w.writer_epoch.next(),
                status=WorldStatus.SUSPENDED if w.kind is WorldKind.ROLEPLAY else WorldStatus.ACTIVE),
                sessions=tuple(replace(s, status=BindingStatus.CLOSED) for s in current.sessions))
            tx.save_world(recovered, w.revision)
        return len(worlds)

    def recover_open_sessions(self):
        """仅在停止接收写入后显式调用；无 OPEN 会话时不推进任何世界围栏。"""
        with self.transaction() as tx:
            return self._recover(tx)

    def close(self):
        """仓储不持有长期连接；关闭后禁止新事务。"""
        self._closed = True
