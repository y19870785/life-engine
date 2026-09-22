"""同 life.db 的 Memory 仓储；仅附着既有 runtime_id，不触发 World recovery。"""
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from .domain import DomainId, WorldScope, IdKind, check_id, require
from .memory import (MemoryRecord, MemoryKind, MemoryLifecycle, MemoryAudience, AudienceKind,
                     MemorySubject, SubjectKind, MemoryCollectionRevision, MemoryReceipt, IdempotencyIdentity)
from .memory_control import control, scope_values, append_intent
from .memory_repository import MemoryFailure as MC, deny
from .world_codec import provenance_dump, provenance_load
from .world_repository import FailureCode as WC, fail
from .world_schema import validate_schema
from .world_sqlite_repository import _SQLiteTransaction, storage_errors

SCOPE_SQL = 'owner_id=? AND soul_id=? AND world_id=? AND timeline_id=?'


def load_record(db, row):
    """无修复解码；坏类型、枚举、来源或顺序统一为损坏数据。"""
    try:
        mid = row['memory_id']
        audience_rows = db.execute('SELECT * FROM memory_audiences WHERE memory_id=? ORDER BY position', (mid,)).fetchall()
        subject_rows = db.execute('SELECT * FROM memory_subjects WHERE memory_id=? ORDER BY position', (mid,)).fetchall()
        for rows in (audience_rows, subject_rows):
            if [r['position'] for r in rows] != list(range(len(rows))):
                fail(WC.STORAGE_CORRUPT)
        audience = tuple(MemoryAudience(AudienceKind(r['kind']), DomainId.parse(r['target']) if r['target'] else None) for r in audience_rows)
        subjects = tuple(MemorySubject(SubjectKind(r['kind']), DomainId.parse(r['target']) if r['target'] else None, r['text']) for r in subject_rows)
        result = MemoryRecord(DomainId.parse(mid), WorldScope(*(DomainId.parse(row[k]) for k in
            ('owner_id','soul_id','world_id','timeline_id'))), MemoryKind(row['memory_kind']), row['content'],
            row['content_version'], provenance_load(row['provenance']), audience, subjects,
            MemoryLifecycle(row['lifecycle']), datetime.fromisoformat(row['created_at']),
            DomainId.parse(row['predecessor']) if row['predecessor'] else None,
            DomainId.parse(row['superseded_by']) if row['superseded_by'] else None,
            tuple(DomainId.parse(r[0]) for r in db.execute('SELECT source_id FROM memory_lineage WHERE memory_id=? ORDER BY source_id', (mid,))))
        if result.audience != audience:
            fail(WC.STORAGE_CORRUPT)
        return result
    except (ValueError, TypeError, KeyError, IndexError):
        fail(WC.STORAGE_CORRUPT)


class MemoryTransaction:
    """受信内部适配；业务授权由 MemoryRuntime 在同一事务内执行。"""
    def __init__(self, db, entries, instance_id):
        self.db, self.entries, self.instance_id = db, entries, instance_id
        self.world = _SQLiteTransaction(db)

    def revision(self, scope):
        row = self.db.execute('SELECT revision FROM memory_collection_state WHERE ' + SCOPE_SQL, scope_values(scope)).fetchone()
        if row is None:
            fail(WC.STORAGE_CORRUPT)
        return MemoryCollectionRevision(row[0])

    def cas(self, scope, expected):
        if self.db.execute('UPDATE memory_collection_state SET revision=revision+1 WHERE ' + SCOPE_SQL + ' AND revision=?',
                           (*scope_values(scope), expected.value)).rowcount != 1:
            deny(MC.REVISION_CONFLICT)
        return expected.next()

    def get(self, scope, memory_id):
        row = self.db.execute('SELECT * FROM world_memories WHERE ' + SCOPE_SQL + ' AND memory_id=?',
                              (*scope_values(scope), str(memory_id))).fetchone()
        return load_record(self.db, row) if row else None

    def insert(self, record):
        r = record
        self.db.execute('INSERT INTO world_memories VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (str(r.memory_id), *scope_values(r.scope), r.kind.value, r.content, r.content_version,
             provenance_dump(r.provenance), r.lifecycle.value, str(r.predecessor) if r.predecessor else None,
             str(r.superseded_by) if r.superseded_by else None, r.created_at.isoformat()))
        self.db.executemany('INSERT INTO memory_audiences VALUES(?,?,?,?)',
            [(str(r.memory_id), i, a.kind.value, str(a.target) if a.target else None) for i,a in enumerate(r.audience)])
        self.db.executemany('INSERT INTO memory_subjects VALUES(?,?,?,?,?)',
            [(str(r.memory_id), i, s.kind.value, str(s.target) if s.target else None, s.text) for i,s in enumerate(r.subjects)])
        self.db.executemany('INSERT INTO memory_lineage VALUES(?,?)', [(str(r.memory_id), str(source)) for source in r.lineage])

    def blocked(self, scope, *, memory_id=None, producer=None, identity=None, source=None):
        for e in self.entries:
            if e['instance_id'] != self.instance_id or json.loads(e['scope']) != scope_values(scope):
                continue
            blocked = json.loads(e['blocked'])
            if memory_id is not None and str(memory_id) in blocked['memories']:
                return True
            if identity is not None and [str(producer), identity.source, identity.slot] in blocked['keys']:
                return True
            if source is not None and list(source) in blocked['sources']:
                return True
        return False

    def guard(self, scope):
        for e in self.entries:
            if e['instance_id'] == self.instance_id and json.loads(e['scope']) == scope_values(scope):
                if not self.db.execute('SELECT 1 FROM memory_applied_controls WHERE sequence=? AND fingerprint=?',
                                       (e['sequence'],e['fingerprint'])).fetchone():
                    deny(MC.CONTROL_REQUIRED)

    def audit(self, context, action, record, revision, identity, fingerprint):
        op = self.db.execute('INSERT INTO memory_operations(world_id,timeline_id,memory_id,actor,action,predecessor,created_at,revision) '
            'VALUES(?,?,?,?,?,?,?,?)', (str(record.scope.world_id),str(record.scope.timeline_id),str(record.memory_id),
            str(context.principal.principal_id),action,str(record.predecessor) if record.predecessor else None,
            datetime.now(timezone.utc).isoformat(),revision.value)).lastrowid
        self.db.execute('INSERT INTO memory_idempotency VALUES(?,?,?,?,?,?,?,?,?,?,?)',
            (*scope_values(context.scope),str(context.principal.principal_id),identity.source,identity.slot,
             fingerprint,str(record.memory_id),revision.value,op))
        return MemoryReceipt(record.memory_id, revision)

    def replay(self, context, identity, fingerprint):
        if self.blocked(context.scope, producer=context.principal.principal_id, identity=identity):
            deny(MC.NOT_AVAILABLE)
        row = self.db.execute('SELECT * FROM memory_idempotency WHERE ' + SCOPE_SQL + ' AND producer=? AND source=? AND slot=?',
            (*scope_values(context.scope),str(context.principal.principal_id),identity.source,identity.slot)).fetchone()
        if row:
            if row['fingerprint'] != fingerprint:
                deny(MC.IDEMPOTENCY_CONFLICT)
            return MemoryReceipt(DomainId.parse(row['memory_id']), MemoryCollectionRevision(row['revision']))


def reconcile_db(db, entries, instance_id):
    """协调器持有管理/实例/控制锁；每个持久意图只推进一次集合修订。"""
    old_factory = db.row_factory
    db.row_factory = sqlite3.Row
    try:
        for e in entries:
            if e['instance_id'] != instance_id:
                continue
            applied = db.execute('SELECT fingerprint FROM memory_applied_controls WHERE sequence=?', (e['sequence'],)).fetchone()
            if applied:
                if applied[0] != e['fingerprint']:
                    deny(MC.CONTROL_REQUIRED)
                continue
            blocked = json.loads(e['blocked'])
            scope = json.loads(e['scope'])
            changed = 0
            for mid in blocked['memories']:
                changed += db.execute("UPDATE world_memories SET lifecycle='tombstoned' WHERE " + SCOPE_SQL +
                    " AND memory_id=? AND lifecycle<>'tombstoned'", (*scope,mid)).rowcount
            if changed:
                current = db.execute('SELECT revision FROM memory_collection_state WHERE '+SCOPE_SQL,scope).fetchone()[0]
                if db.execute('UPDATE memory_collection_state SET revision=revision+1 WHERE ' + SCOPE_SQL + ' AND revision=?',
                              (*scope,current)).rowcount != 1:
                    deny(MC.REVISION_CONFLICT)
                revision = db.execute('SELECT revision FROM memory_collection_state WHERE ' + SCOPE_SQL, scope).fetchone()[0]
                operation = db.execute('INSERT INTO memory_operations(world_id,timeline_id,memory_id,actor,action,created_at,revision) '
                    'VALUES(?,?,?,?,?,?,?)', (scope[2],scope[3],e['memory_id'],e['actor'],'delete',e['created_at'],revision))
                producer,source,slot,stamp = blocked['request']
                db.execute('INSERT INTO memory_idempotency VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                           (*scope,producer,source,slot,stamp,e['memory_id'],revision,operation.lastrowid))
            db.execute('INSERT INTO memory_applied_controls VALUES(?,?)', (e['sequence'],e['fingerprint']))
        db.execute("UPDATE meta SET value=? WHERE key='last_applied_memory_control_seq'", (str(len(entries)),))
    finally:
        db.row_factory = old_factory


class SQLiteMemoryRepository:
    """只允许已登记安装的活动 generation；每个操作关闭全部连接与锁。"""
    def __init__(self, root, instance_id, *, runtime_id, timeout=5):
        self.root, self.instance_id = Path(root).resolve(), instance_id
        if not isinstance(runtime_id, str) or not runtime_id or not 0 < timeout <= 60:
            raise ValueError('必须提供既有运行代次与有界超时')
        self.runtime_id, self.timeout, self.closed = runtime_id, timeout, False
        from .durable import registry, state_home
        reg = registry(self.root)
        inst = reg['instances'][instance_id]
        self.path = state_home(self.root, inst) / 'agents' / inst['agent_id'] / 'life.db'
        self.generation = inst['generation']
        with self.transaction() as tx:
            validate_memory_data(tx.db)

    @contextmanager
    def transaction(self, *, recovery=False):
        from .durable import locked, registry
        if self.closed:
            fail(WC.TRANSACTION_CLOSED)
        db = None
        try:
            with locked(self.root,'management',self.timeout), locked(self.root,self.instance_id,self.timeout):
                reg = registry(self.root)
                if reg['instances'][self.instance_id]['generation'] != self.generation:
                    fail(WC.RECOVERY_REQUIRED)
                with control(self.root, reg.get('memory_install_id')) as (control_db, entries), storage_errors():
                    db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True, isolation_level=None, timeout=self.timeout)
                    db.row_factory = sqlite3.Row
                    db.execute('PRAGMA foreign_keys=ON')
                    db.execute('BEGIN IMMEDIATE')
                    validate_schema(db)
                    runtime = db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()
                    if runtime is None or runtime[0] != self.runtime_id:
                        fail(WC.RECOVERY_REQUIRED)
                    watermark = db.execute("SELECT value FROM meta WHERE key='last_applied_memory_control_seq'").fetchone()
                    if watermark is None or not watermark[0].isdigit() or int(watermark[0]) > len(entries):
                        deny(MC.CONTROL_REQUIRED)
                    for applied in db.execute('SELECT sequence,fingerprint FROM memory_applied_controls'):
                        seq = applied[0]
                        if not 1<=seq<=len(entries) or entries[seq-1]['instance_id']!=self.instance_id or entries[seq-1]['fingerprint']!=applied[1]:
                            deny(MC.CONTROL_REQUIRED)
                    tx = MemoryTransaction(db, entries, self.instance_id)
                    tx.control_db, tx.install_id = control_db, reg['memory_install_id']
                    try:
                        yield tx
                        db.commit()
                    except BaseException:
                        db.rollback()
                        raise
                    finally:
                        tx.world._open = False
        except TimeoutError:
            fail(WC.STORAGE_BUSY)
        finally:
            if db is not None:
                db.close()

    def reconcile(self):
        with self.transaction(recovery=True) as tx:
            reconcile_db(tx.db, tx.entries, self.instance_id)
            sequences = tuple(r[0] for r in tx.db.execute('SELECT sequence FROM memory_applied_controls'))
        self._complete_controls(tx.install_id,sequences)

    def _complete_controls(self, install_id, sequences):
        from .durable import locked
        with locked(self.root,'management'),locked(self.root,self.instance_id),control(self.root,install_id) as (db,_):
            db.executemany('UPDATE intents SET completed=1 WHERE instance_id=? AND sequence=?',
                           [(self.instance_id,seq) for seq in sequences])

    def delete(self, context, memory_id, expected_revision, identity):
        """意图提交后出错仍拒绝读写；显式 reconcile 收敛，不返回虚假成功。"""
        from .memory_runtime import authorize
        from .memory_control import fingerprint
        require(expected_revision,MemoryCollectionRevision)
        require(identity,IdempotencyIdentity)
        check_id(memory_id,IdKind.MEMORY)
        with self.transaction() as tx:
            authorize(tx,context,owner=True,deletion=True)
            stamp = fingerprint(['delete',scope_values(context.scope),str(memory_id)])
            replay = tx.replay(context,identity,stamp)
            if replay:
                return replay
            record = tx.get(context.scope,memory_id)
            if record is None:
                deny(MC.NOT_AVAILABLE)
            if record.lifecycle is MemoryLifecycle.TOMBSTONED:
                return MemoryReceipt(memory_id,tx.revision(context.scope))
            if tx.revision(context.scope) != expected_revision:
                deny(MC.REVISION_CONFLICT)
            # 删除保护覆盖替代后继和派生记录；不在账本中复制正文。
            ids = {str(memory_id)}
            pending = list(ids)
            while pending:
                source = pending.pop()
                children = tx.db.execute('SELECT memory_id FROM memory_lineage WHERE source_id=? UNION '
                    'SELECT memory_id FROM world_memories WHERE predecessor=?',(source,source)).fetchall()
                for child in children:
                    if child[0] not in ids:
                        ids.add(child[0])
                        pending.append(child[0])
            keys, sources = [], []
            for mid in sorted(ids):
                keys.extend([list(r) for r in tx.db.execute('SELECT producer,source,slot FROM memory_idempotency WHERE memory_id=?',(mid,))])
                item = tx.get(context.scope,DomainId.parse(mid))
                if item is None:
                    fail(WC.STORAGE_CORRUPT)
                p = item.provenance
                sources.append([str(p.actor.principal_id),p.source_type.value,p.source_id])
            blocked = {'memories': sorted(ids),'keys':keys,'sources':sources,
                       'request': [str(context.principal.principal_id),identity.source,identity.slot,stamp]}
            entry = append_intent(self.root,tx.control_db,tx.entries,tx.install_id,self.instance_id,
                                  scope_values(context.scope),memory_id,context.principal.principal_id,blocked)
            self._after_delete_intent()
            reconcile_db(tx.db,[*tx.entries,entry],self.instance_id)
            receipt = MemoryReceipt(memory_id,tx.revision(context.scope))
        self._complete_controls(tx.install_id,(entry['sequence'],))
        return receipt

    def _after_delete_intent(self):
        """故障注入边界；生产路径没有外部副作用。"""

    def close(self):
        self.closed = True


def validate_memory_data(db):
    """检查完整 Memory 图和审计引用，不补齐缺行、不修复坏值。"""
    from .memory_runtime import validate_record
    old_factory = db.row_factory
    db.row_factory = sqlite3.Row
    try:
        expected = {tuple(r) for r in db.execute('SELECT w.owner_id,w.soul_id,w.world_id,t.timeline_id '
                    'FROM worlds w JOIN world_timelines t ON w.world_id=t.world_id')}
        collections = db.execute('SELECT * FROM memory_collection_state').fetchall()
        if {tuple(r)[:4] for r in collections} != expected:
            fail(WC.STORAGE_CORRUPT)
        for r in collections:
            MemoryCollectionRevision(r['revision'])
        tx = MemoryTransaction(db,[],None)
        records = {}
        for row in db.execute('SELECT * FROM world_memories'):
            record = load_record(db,row)
            validate_record(tx,record)
            records[record.memory_id] = record
        for record in records.values():
            if record.predecessor:
                previous = records[record.predecessor]
                if previous.scope != record.scope or previous.superseded_by != record.memory_id or previous.content_version+1 != record.content_version:
                    fail(WC.STORAGE_CORRUPT)
            elif record.content_version != 1:
                fail(WC.STORAGE_CORRUPT)
            if record.superseded_by:
                successor = records[record.superseded_by]
                if successor.predecessor != record.memory_id or record.lifecycle not in (MemoryLifecycle.SUPERSEDED,MemoryLifecycle.TOMBSTONED):
                    fail(WC.STORAGE_CORRUPT)
            for source in record.lineage:
                if records[source].scope != record.scope:
                    fail(WC.STORAGE_CORRUPT)
            visited, pending = set(), [(record.memory_id,frozenset())]
            while pending:
                ident, ancestors = pending.pop()
                if ident in ancestors:
                    fail(WC.STORAGE_CORRUPT)
                if ident in visited:
                    continue
                visited.add(ident)
                item = records[ident]
                pending.extend((p,ancestors|{ident}) for p in (*item.lineage,*((item.predecessor,) if item.predecessor else ())))
        for row in db.execute('SELECT * FROM memory_operations'):
            check_id(DomainId.parse(row['actor']),IdKind.PRINCIPAL)
            from .domain import aware
            aware(datetime.fromisoformat(row['created_at']))
            record = records[DomainId.parse(row['memory_id'])]
            if (str(record.scope.world_id),str(record.scope.timeline_id)) != (row['world_id'],row['timeline_id']) or row['revision']>tx.revision(record.scope).value:
                fail(WC.STORAGE_CORRUPT)
        for row in db.execute('SELECT * FROM memory_idempotency'):
            record = records[DomainId.parse(row['memory_id'])]
            if scope_values(record.scope) != [row[k] for k in ('owner_id','soul_id','world_id','timeline_id')]:
                fail(WC.STORAGE_CORRUPT)
            check_id(DomainId.parse(row['producer']),IdKind.PRINCIPAL)
            IdempotencyIdentity(row['source'],row['slot'])
            if len(row['fingerprint'])!=64 or row['revision']>tx.revision(record.scope).value:
                fail(WC.STORAGE_CORRUPT)
            operation = db.execute('SELECT * FROM memory_operations WHERE sequence=?',(row['operation'],)).fetchone()
            if operation is None or (operation['actor'],operation['memory_id'],operation['revision']) != (row['producer'],row['memory_id'],row['revision']):
                fail(WC.STORAGE_CORRUPT)
        watermark = db.execute("SELECT value FROM meta WHERE key='last_applied_memory_control_seq'").fetchone()
        if watermark is None or not watermark[0].isdigit():
            fail(WC.STORAGE_CORRUPT)
        for applied in db.execute('SELECT sequence,fingerprint FROM memory_applied_controls'):
            if applied[0]>int(watermark[0]) or len(applied[1])!=64:
                fail(WC.STORAGE_CORRUPT)
    except (ValueError,TypeError,KeyError,IndexError):
        fail(WC.STORAGE_CORRUPT)
    finally:
        db.row_factory = old_factory
