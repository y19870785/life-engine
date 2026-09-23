"""实例 life.db 的 Lore 仓储；连接、锁和事务均由单次操作拥有。"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import sqlite3

from .domain import DomainError, DomainId, IdKind, WorldScope, check_id
from .import_ir import JsonValue, canonical
from .lore import (LoreBinding, LoreBindingRevision, LoreBookDefinition, LoreBookVersion,
                   LoreBookVersionRecord, LoreDiagnostic, LoreEntryDefinition, LoreReceipt)
from .lore_repository import LoreFailure as LC, LoreRuntimeError, fail
from .memory_control import scope_values
from .world_repository import FailureCode as WC, WorldRuntimeError
from .world_schema import validate_schema
from .world_sqlite_repository import _SQLiteTransaction

SCOPE_SQL = 'owner_id=? AND soul_id=? AND world_id=? AND timeline_id=?'


def _id(value, kind):
    result = DomainId.parse(value)
    check_id(result, kind)
    return result


def _json(value):
    result = JsonValue(value)
    if result.text != value:
        fail(LC.STORAGE_CORRUPT)
    return result


def decoded(fn):
    """持久行解码错误固定映射为损坏，不伪装成调用参数错误。"""
    def call(*args):
        try:
            return fn(*args)
        except LoreRuntimeError:
            raise
        except (DomainError, ValueError, TypeError, KeyError, IndexError, AttributeError):
            fail(LC.STORAGE_CORRUPT)
    return call


@decoded
def _book(row):
    return LoreBookDefinition(_id(row['book_id'], IdKind.LORE_BOOK), _id(row['owner_id'], IdKind.OWNER),
        row['display_name'], LoreBookVersion(row['current_version']), row['source_type'],
        _json(row['source_metadata']), datetime.fromisoformat(row['created_at']),
        _id(row['created_by'], IdKind.PRINCIPAL))


@decoded
def _version(row):
    if type(row['runtime_compatible']) is not int or row['runtime_compatible'] not in (0,1):
        fail(LC.STORAGE_CORRUPT)
    return LoreBookVersionRecord(_id(row['book_id'], IdKind.LORE_BOOK), LoreBookVersion(row['version']),
        row['source_type'], row['source_fingerprint'], row['payload_fingerprint'],
        _json(row['source_metadata']), row['registration_fingerprint'], row['entry_count'],
        bool(row['runtime_compatible']), datetime.fromisoformat(row['created_at']),
        _id(row['created_by'], IdKind.PRINCIPAL))


@decoded
def _entry(db, row, trigger_rows=None):
    triggers = (trigger_rows if trigger_rows is not None else
        db.execute('SELECT trigger_kind,position,text FROM lore_entry_triggers WHERE book_id=? '
        'AND book_version=? AND entry_id=? ORDER BY trigger_kind,position',
        (row['book_id'], row['book_version'], row['entry_id'])).fetchall())
    groups = {}
    for kind in ('primary', 'secondary'):
        subset = [r for r in triggers if r['trigger_kind'] == kind]
        if [r['position'] for r in subset] != list(range(len(subset))):
            fail(LC.STORAGE_CORRUPT)
        groups[kind] = tuple(r['text'] for r in subset)
    diagnostics = json.loads(_json(row['diagnostics']).text)
    if type(diagnostics) is not list:
        fail(LC.STORAGE_CORRUPT)
    return LoreEntryDefinition(_id(row['entry_id'], IdKind.LORE_ENTRY),
        _id(row['book_id'], IdKind.LORE_BOOK), LoreBookVersion(row['book_version']),
        bool(row['enabled']), bool(row['constant']), bool(row['selective']),
        bool(row['case_sensitive']), row['runtime_priority'], row['runtime_order'], row['text'],
        groups['primary'], groups['secondary'],
        LoreDiagnostic(row['runtime_disabled_reason']) if row['runtime_disabled_reason'] else None,
        _json(row['source_metadata']), tuple(LoreDiagnostic(x) for x in diagnostics))


@decoded
def _binding(row):
    scope = WorldScope(*(_id(row[k], kind) for k, kind in (
        ('owner_id', IdKind.OWNER), ('soul_id', IdKind.SOUL),
        ('world_id', IdKind.WORLD), ('timeline_id', IdKind.TIMELINE))))
    return LoreBinding(scope, _id(row['book_id'], IdKind.LORE_BOOK),
        LoreBookVersion(row['book_version']), bool(row['enabled']), row['binding_order'], row['source'])


def validate_lore_data(db):
    """只读验证全部 Lore 身份、引用、规范 JSON 与 Scope 完整性。"""
    old = db.row_factory
    db.row_factory = sqlite3.Row
    try:
        scopes = {tuple(r) for r in db.execute('SELECT w.owner_id,w.soul_id,w.world_id,t.timeline_id '
            'FROM worlds w JOIN world_timelines t ON t.world_id=w.world_id')}
        states = set()
        for r in db.execute('SELECT * FROM lore_binding_state'):
            values = tuple(r[k] for k in ('owner_id','soul_id','world_id','timeline_id'))
            WorldScope(*(_id(v,k) for v,k in zip(values,
                (IdKind.OWNER,IdKind.SOUL,IdKind.WORLD,IdKind.TIMELINE))))
            if type(r['revision']) is not int or r['revision'] < 0:
                fail(LC.STORAGE_CORRUPT)
            states.add(values)
        if scopes != states:
            fail(LC.STORAGE_CORRUPT)
        books = {}
        for r in db.execute('SELECT * FROM lore_books'):
            book = _book(r)
            books[r['book_id']] = book
        versions = {}
        for r in db.execute('SELECT * FROM lore_book_versions'):
            v = _version(r)
            versions[(r['book_id'],r['version'])] = v
            count = db.execute('SELECT count(*) FROM lore_entries WHERE book_id=? AND book_version=?',
                (r['book_id'],r['version'])).fetchone()[0]
            if count != v.entry_count or r['book_id'] not in books:
                fail(LC.STORAGE_CORRUPT)
        for key, book in books.items():
            registered = [v for b,v in versions if b==key]
            if not registered or book.current_version.value != max(registered):
                fail(LC.STORAGE_CORRUPT)
        grouped = {}
        for trigger in db.execute('SELECT * FROM lore_entry_triggers ORDER BY book_id,book_version,entry_id,trigger_kind,position'):
            grouped.setdefault((trigger['book_id'],trigger['book_version'],trigger['entry_id']),[]).append(trigger)
        for r in db.execute('SELECT * FROM lore_entries'):
            key=(r['book_id'],r['book_version'],r['entry_id'])
            entry = _entry(db,r,grouped.get(key,()))
            if ((r['book_id'],r['book_version']) not in versions or
                    entry.runtime_disabled_reason and entry.runtime_disabled_reason not in entry.diagnostics):
                fail(LC.STORAGE_CORRUPT)
        for r in db.execute('SELECT * FROM lore_world_bindings'):
            binding = _binding(r)
            book = books.get(r['book_id'])
            if (book is None or book.owner_id != binding.scope.owner_id or
                    (r['book_id'],r['book_version']) not in versions):
                fail(LC.STORAGE_CORRUPT)
        for r in db.execute('SELECT * FROM lore_operations'):
            _id(r['actor'],IdKind.PRINCIPAL)
            _id(r['owner_id'],IdKind.OWNER)
            if r['soul_id'] is not None:
                values = tuple(r[k] for k in ('owner_id','soul_id','world_id','timeline_id'))
                if values not in states:
                    fail(LC.STORAGE_CORRUPT)
                state = db.execute('SELECT revision FROM lore_binding_state WHERE '+SCOPE_SQL,values).fetchone()
                if r['revision'] is None or r['revision'] > state[0]:
                    fail(LC.STORAGE_CORRUPT)
            elif any(r[k] is not None for k in ('world_id','timeline_id','revision')):
                fail(LC.STORAGE_CORRUPT)
            if (r['book_id'],r['book_version']) not in versions:
                fail(LC.STORAGE_CORRUPT)
            if books[r['book_id']].owner_id != _id(r['owner_id'],IdKind.OWNER):
                fail(LC.STORAGE_CORRUPT)
            if datetime.fromisoformat(r['created_at']).utcoffset() is None:
                fail(LC.STORAGE_CORRUPT)
        for r in db.execute('SELECT * FROM lore_idempotency'):
            _id(r['producer'],IdKind.PRINCIPAL)
            if type(r['fingerprint']) is not str or not re.fullmatch('[0-9a-f]{64}',r['fingerprint']):
                fail(LC.STORAGE_CORRUPT)
            payload = _json(r['receipt']).value()
            if (type(payload) is not dict or
                    (payload.get('book_id'),payload.get('book_version')) not in versions):
                fail(LC.STORAGE_CORRUPT)
            op = db.execute('SELECT * FROM lore_operations WHERE sequence=?',(r['operation'],)).fetchone()
            if (op is None or op['actor'] != r['producer'] or op['book_id'] != payload['book_id'] or
                    op['book_version'] != payload['book_version'] or op['revision'] != payload.get('revision')):
                fail(LC.STORAGE_CORRUPT)
        if db.execute('PRAGMA foreign_key_check').fetchone():
            fail(LC.STORAGE_CORRUPT)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, sqlite3.DatabaseError):
        fail(LC.STORAGE_CORRUPT)
    finally:
        db.row_factory = old


class LoreTransaction:
    """同一 SQLite 快照内提供 World 围栏与 Lore 读取。"""
    def __init__(self, db):
        self.db = db
        self.world = _SQLiteTransaction(db)

    def revision(self, scope):
        row = self.db.execute('SELECT revision FROM lore_binding_state WHERE '+SCOPE_SQL,
            scope_values(scope)).fetchone()
        if row is None:
            fail(LC.STORAGE_CORRUPT)
        return LoreBindingRevision(row[0])

    def cas(self, scope, expected):
        if self.db.execute('UPDATE lore_binding_state SET revision=revision+1 WHERE '+SCOPE_SQL+
            ' AND revision=?', (*scope_values(scope),expected.value)).rowcount != 1:
            fail(LC.REVISION_CONFLICT)
        return expected.next()

    def book(self, book_id):
        row = self.db.execute('SELECT * FROM lore_books WHERE book_id=?',(str(book_id),)).fetchone()
        return _book(row) if row else None

    def version(self, book_id, version):
        row = self.db.execute('SELECT * FROM lore_book_versions WHERE book_id=? AND version=?',
            (str(book_id),version.value)).fetchone()
        return _version(row) if row else None

    def entries(self, book_id, version):
        rows = self.db.execute('SELECT * FROM lore_entries WHERE book_id=? AND book_version=? '
            'ORDER BY runtime_priority DESC,runtime_order,entry_id',
            (str(book_id),version.value)).fetchall()
        grouped = {}
        for trigger in self.db.execute('SELECT entry_id,trigger_kind,position,text FROM lore_entry_triggers '
                'WHERE book_id=? AND book_version=? ORDER BY entry_id,trigger_kind,position',
                (str(book_id),version.value)):
            grouped.setdefault(trigger['entry_id'],[]).append(trigger)
        return tuple(_entry(self.db,r,grouped.get(r['entry_id'],())) for r in rows)

    def bindings(self, scope):
        rows = self.db.execute('SELECT * FROM lore_world_bindings WHERE '+SCOPE_SQL+
            ' ORDER BY binding_order,book_id', scope_values(scope)).fetchall()
        return tuple(_binding(r) for r in rows)

    def owner_books(self, owner_id):
        return tuple(_book(r) for r in self.db.execute('SELECT * FROM lore_books WHERE owner_id=? ORDER BY book_id',
            (str(owner_id),)))

    def replay(self, identity, producer, stamp):
        row = self.db.execute('SELECT fingerprint,receipt FROM lore_idempotency '
            'WHERE producer=? AND source=? AND slot=?',
            (str(producer),identity.source,identity.slot)).fetchone()
        if row is None:
            return None
        if row['fingerprint'] != stamp:
            fail(LC.IDEMPOTENCY_CONFLICT)
        try:
            data=_json(row['receipt']).value()
            return LoreReceipt(_id(data['book_id'],IdKind.LORE_BOOK),LoreBookVersion(data['book_version']),
                LoreBindingRevision(data['revision']) if data['revision'] is not None else None)
        except (ValueError,TypeError,KeyError):
            fail(LC.STORAGE_CORRUPT)

    def audit(self, context, operation, book_id, version, identity, stamp, revision=None):
        scope=context.scope
        values=scope_values(scope) if scope else (str(context.principal.owner_id),None,None,None)
        op=self.db.execute('INSERT INTO lore_operations(actor,operation,owner_id,soul_id,world_id,timeline_id,'
            'book_id,book_version,revision,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
            (str(context.principal.principal_id),operation,*values,str(book_id),version.value,
             revision.value if revision else None,datetime.now(timezone.utc).isoformat())).lastrowid
        data=canonical({'book_id':str(book_id),'book_version':version.value,
            'revision':revision.value if revision else None})
        self.db.execute('INSERT INTO lore_idempotency VALUES(?,?,?,?,?,?)',
            (str(context.principal.principal_id),identity.source,identity.slot,stamp,op,data))
        return LoreReceipt(book_id,version,revision)

    def insert_book(self, book_id, owner_id, display_name, source_type, source_metadata, actor):
        self.db.execute('INSERT INTO lore_books VALUES(?,?,?,?,?,?,?,?)',
            (str(book_id),str(owner_id),display_name,1,source_type,source_metadata.text,
             datetime.now(timezone.utc).isoformat(),str(actor)))

    def advance_version(self, book_id, owner_id, expected, next_version):
        if self.db.execute('UPDATE lore_books SET current_version=? WHERE book_id=? AND owner_id=? '
                'AND current_version=?',(next_version.value,str(book_id),str(owner_id),expected.value)).rowcount!=1:
            fail(LC.VERSION_CONFLICT)

    def insert_version(self, book_id, version, proposal, stamp, actor):
        self.db.execute('INSERT INTO lore_book_versions VALUES(?,?,?,?,?,?,?,?,?,?,?)',
            (str(book_id),version.value,proposal.source_type,proposal.source_fingerprint,
             proposal.payload_fingerprint,proposal.source_metadata.text,stamp,len(proposal.entries),
             int(any(e.disabled_reason is None for e in proposal.entries)),
             datetime.now(timezone.utc).isoformat(),str(actor)))
        for e in proposal.entries:
            entry_id=DomainId.new(IdKind.LORE_ENTRY)
            self.db.execute('INSERT INTO lore_entries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (str(book_id),version.value,str(entry_id),int(e.enabled),int(e.constant),int(e.selective),
                 int(e.case_sensitive),e.priority,e.order,e.text,
                 e.disabled_reason.value if e.disabled_reason else None,e.metadata.text,
                 canonical([d.value for d in e.diagnostics])))
            for kind,triggers in (('primary',e.primary),('secondary',e.secondary)):
                self.db.executemany('INSERT INTO lore_entry_triggers VALUES(?,?,?,?,?,?)',
                    [(str(book_id),version.value,str(entry_id),kind,i,text)
                     for i,text in enumerate(triggers)])

    def insert_binding(self, scope, book_id, version, order, source):
        self.db.execute('INSERT INTO lore_world_bindings VALUES(?,?,?,?,?,?,?,?,?)',
            (*scope_values(scope),str(book_id),version.value,1,order,source))

    def delete_binding(self, scope, book_id):
        self.db.execute('DELETE FROM lore_world_bindings WHERE '+SCOPE_SQL+' AND book_id=?',
            (*scope_values(scope),str(book_id)))

    def set_enabled(self, scope, book_id, enabled):
        self.db.execute('UPDATE lore_world_bindings SET enabled=? WHERE '+SCOPE_SQL+' AND book_id=?',
            (int(enabled),*scope_values(scope),str(book_id)))

    def set_version(self, scope, book_id, version):
        self.db.execute('UPDATE lore_world_bindings SET book_version=? WHERE '+SCOPE_SQL+' AND book_id=?',
            (version.value,*scope_values(scope),str(book_id)))

    def scan_counts(self, book_id, version):
        count=self.db.execute('SELECT count(*) FROM lore_entries WHERE book_id=? AND book_version=? '
            'AND enabled=1 AND runtime_disabled_reason IS NULL',
            (str(book_id),version.value)).fetchone()[0]
        triggers=self.db.execute('SELECT count(*) FROM lore_entry_triggers WHERE book_id=? '
            'AND book_version=?',(str(book_id),version.value)).fetchone()[0]
        return count,triggers


class SQLiteLoreRepository:
    """附着现有 World runtime_id；不会再次执行重启恢复。"""
    def __init__(self, root, instance_id, *, runtime_id, timeout=5):
        from .durable import registry, state_home
        self.root, self.instance_id = Path(root).resolve(), instance_id
        if type(runtime_id) is not str or not runtime_id or not 0 < timeout <= 60:
            raise ValueError('必须提供既有 World 运行代次与有界超时')
        self.runtime_id, self.timeout, self.closed = runtime_id, timeout, False
        reg = registry(self.root)
        inst = reg['instances'][instance_id]
        self.generation = inst['generation']
        self.path = state_home(self.root,inst)/'agents'/inst['agent_id']/'life.db'
        with self.transaction() as tx:
            validate_lore_data(tx.db)

    @contextmanager
    def transaction(self, *, write=False):
        from .durable import locked, registry
        if self.closed:
            fail(LC.RECOVERY_REQUIRED)
        db = None
        try:
            with locked(self.root,'management',self.timeout), locked(self.root,self.instance_id,self.timeout):
                reg = registry(self.root)
                if reg['instances'][self.instance_id]['generation'] != self.generation:
                    fail(LC.RECOVERY_REQUIRED)
                db = sqlite3.connect(self.path.as_uri()+'?mode=rw',uri=True,
                    isolation_level=None,timeout=self.timeout)
                db.row_factory = sqlite3.Row
                db.execute('PRAGMA foreign_keys=ON')
                # WorldRuntime 不持有安装锁；读取也取得 SQLite 写入围栏以阻止 EXIT 穿插。
                db.execute('BEGIN IMMEDIATE')
                validate_schema(db)
                row = db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()
                if row is None or row[0] != self.runtime_id:
                    fail(LC.RECOVERY_REQUIRED)
                tx = LoreTransaction(db)
                try:
                    yield tx
                    db.commit()
                except BaseException:
                    db.rollback()
                    raise
                finally:
                    tx.world._open = False
        except TimeoutError:
            fail(LC.STORAGE_BUSY)
        except sqlite3.Error as exc:
            number = getattr(exc,'sqlite_errorcode',0)&255
            fail(LC.STORAGE_BUSY if number in (sqlite3.SQLITE_BUSY,sqlite3.SQLITE_LOCKED)
                 else LC.STORAGE_CORRUPT if number in (sqlite3.SQLITE_CORRUPT,sqlite3.SQLITE_NOTADB)
                 else LC.PERSISTENCE_FAILURE)
        except WorldRuntimeError as exc:
            fail(LC.SCHEMA_MISMATCH if exc.code is WC.SCHEMA_MISMATCH else LC.STORAGE_CORRUPT)
        finally:
            if db is not None:
                db.close()

    def close(self):
        self.closed = True
