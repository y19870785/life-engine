"""同 life.db 的 Bridge Grant 仓储；只查询授权与 World 围栏，不读 Memory/Story 正文。"""
from contextlib import closing, contextmanager
from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
import sqlite3

from .bridge import (BridgeDataClass, BridgeFailure as BC, BridgeGrant, BridgeGrantProposal,
                     BridgeGrantRevision, BridgeGrantStatus, BridgePurpose, BridgeReceipt,
                     checked_fields, deny)
from .bridge_control import append_intent, control
from .domain import DomainId, IdKind, Principal, WorldScope
from .memory import AudienceKind, MemoryAudience
from .world_codec import dumps
from .world_repository import FailureCode as WC, WorldRuntimeError
from .world_schema import validate_schema
from .world_sqlite_repository import _SQLiteTransaction, storage_errors


def _grant(row):
    source = WorldScope(*(DomainId.parse(row[k]) for k in (
        'source_owner_id', 'source_soul_id', 'source_world_id', 'source_timeline_id')))
    target = WorldScope(*(DomainId.parse(row[k]) for k in (
        'target_owner_id', 'target_soul_id', 'target_world_id', 'target_timeline_id')))
    fields = json.loads(row['allowed_fields'])
    if type(fields) is not list or dumps(fields) != row['allowed_fields']:
        deny(BC.STORAGE_CORRUPT)
    data_class = BridgeDataClass(row['data_class'])
    checked_fields(data_class, tuple(fields))
    proposal = BridgeGrantProposal(source, target, data_class, tuple(fields),
        BridgePurpose(row['purpose']),
        MemoryAudience(AudienceKind(row['audience_kind']), DomainId.parse(row['audience_target'])),
        datetime.fromisoformat(row['expires_at']))
    principal = Principal(DomainId.parse(row['created_by']), DomainId.parse(row['owner_id']))
    revoked_by = (Principal(DomainId.parse(row['revoked_by']), principal.owner_id)
                  if row['revoked_by'] else None)
    return BridgeGrant(DomainId.parse(row['grant_id']), principal, proposal,
        BridgeGrantRevision(row['revision']), BridgeGrantStatus(row['status']),
        datetime.fromisoformat(row['created_at']), revoked_by,
        datetime.fromisoformat(row['revoked_at']) if row['revoked_at'] else None)


def validate_bridge_data(db):
    """Reject-only business consistency; external control is validated by coordinator/repository."""
    old_factory = db.row_factory
    try:
        db.row_factory = sqlite3.Row
        grants = db.execute('SELECT * FROM bridge_grants ORDER BY grant_id').fetchall()
        for row in grants:
            value = _grant(row)
            if (value.grant_id.kind is not IdKind.GRANT or value.principal.owner_id != value.proposal.source_scope.owner_id or
                    value.principal.owner_id != value.proposal.target_scope.owner_id or
                    value.proposal.source_scope.world_id == value.proposal.target_scope.world_id or
                    value.proposal.purpose is not BridgePurpose.PROMPT_CONTEXT):
                deny(BC.STORAGE_CORRUPT)
            for scope in (value.proposal.source_scope, value.proposal.target_scope):
                world = db.execute('SELECT owner_id,soul_id FROM worlds WHERE world_id=?', (str(scope.world_id),)).fetchone()
                timeline = db.execute('SELECT world_id FROM world_timelines WHERE timeline_id=?',
                                      (str(scope.timeline_id),)).fetchone()
                if (world is None or timeline is None or world['owner_id'] != str(scope.owner_id) or
                        world['soul_id'] != str(scope.soul_id) or timeline['world_id'] != str(scope.world_id)):
                    deny(BC.STORAGE_CORRUPT)
            if value.proposal.target_audience.kind is AudienceKind.SOUL:
                if value.proposal.target_audience.target != value.proposal.target_scope.soul_id:
                    deny(BC.STORAGE_CORRUPT)
            else:
                char = db.execute('SELECT world_id,timeline_id FROM character_instances WHERE character_instance_id=?',
                                  (str(value.proposal.target_audience.target),)).fetchone()
                if char is None or (char['world_id'], char['timeline_id']) != (
                        str(value.proposal.target_scope.world_id), str(value.proposal.target_scope.timeline_id)):
                    deny(BC.STORAGE_CORRUPT)
            source_kind = db.execute('SELECT kind FROM worlds WHERE world_id=?',
                (str(value.proposal.source_scope.world_id),)).fetchone()[0]
            target_kind = db.execute('SELECT kind FROM worlds WHERE world_id=?',
                (str(value.proposal.target_scope.world_id),)).fetchone()[0]
            if (source_kind, target_kind) not in (('soul', 'roleplay'), ('roleplay', 'soul')):
                deny(BC.STORAGE_CORRUPT)
            if (target_kind == 'soul') != (value.proposal.target_audience.kind is AudienceKind.SOUL):
                deny(BC.STORAGE_CORRUPT)
            ops = db.execute('SELECT operation,revision,actor,created_at,fingerprint FROM bridge_operations WHERE grant_id=? ORDER BY revision',
                             (str(value.grant_id),)).fetchall()
            if [(r['operation'], r['revision']) for r in ops] != (
                    [('create', 1)] if value.status is BridgeGrantStatus.ACTIVE else [('create', 1), ('revoke', 2)]):
                deny(BC.STORAGE_CORRUPT)
            if (ops[0]['actor'] != row['created_by'] or ops[0]['created_at'] != row['created_at'] or
                    any(len(op['fingerprint']) != 64 or any(c not in '0123456789abcdef'
                        for c in op['fingerprint']) for op in ops)):
                deny(BC.STORAGE_CORRUPT)
            if len(ops) == 2 and (ops[1]['actor'] != row['revoked_by'] or
                                  ops[1]['created_at'] != row['revoked_at']):
                deny(BC.STORAGE_CORRUPT)
        for row in db.execute('SELECT * FROM bridge_idempotency'):
            op = db.execute('SELECT operation,fingerprint FROM bridge_operations WHERE grant_id=? AND revision=?',
                            (row['grant_id'], row['revision'])).fetchone()
            if (row['operation'], row['revision']) not in (('create', 1), ('revoke', 2)) or (
                    op is None or (op['operation'], op['fingerprint']) !=
                    (row['operation'], row['fingerprint'])):
                deny(BC.STORAGE_CORRUPT)
        for row in db.execute('SELECT sequence,fingerprint FROM bridge_applied_controls'):
            if row['sequence'] < 1 or len(row['fingerprint']) != 64:
                deny(BC.STORAGE_CORRUPT)
    except (sqlite3.DatabaseError, ValueError, KeyError, TypeError, AttributeError):
        deny(BC.STORAGE_CORRUPT)
    finally:
        db.row_factory = old_factory


def reconcile_db(db, entries, instance_id):
    """先重放独立撤销事实，未知 Grant 的事实仍保留以阻断以后恢复旧备份。"""
    expected = {entry['sequence']: entry['fingerprint'] for entry in entries
                if entry['instance_id'] == instance_id}
    applied = dict(db.execute('SELECT sequence,fingerprint FROM bridge_applied_controls'))
    if not set(applied.items()) <= set(expected.items()):
        deny(BC.CONTROL_REQUIRED)
    for entry in entries:
        if entry['instance_id'] != instance_id:
            continue
        existing = db.execute('SELECT fingerprint FROM bridge_applied_controls WHERE sequence=?',
                              (entry['sequence'],)).fetchone()
        if existing is not None:
            if existing[0] != entry['fingerprint']:
                deny(BC.CONTROL_REQUIRED)
        row = db.execute('SELECT status FROM bridge_grants WHERE grant_id=?', (entry['grant_id'],)).fetchone()
        if row and row[0] == 'active':
            db.execute("UPDATE bridge_grants SET status='revoked',revision=2,revoked_by=?,revoked_at=? WHERE grant_id=?",
                       (entry['actor'], entry['created_at'], entry['grant_id']))
            db.execute("INSERT OR IGNORE INTO bridge_operations(grant_id,actor,operation,revision,created_at,fingerprint) VALUES(?,?,'revoke',2,?,?)",
                       (entry['grant_id'], entry['actor'], entry['created_at'], entry['fingerprint']))
        if existing is None:
            db.execute('INSERT INTO bridge_applied_controls VALUES(?,?)',
                       (entry['sequence'], entry['fingerprint']))


class BridgeTransaction:
    def __init__(self, db, entries, instance_id):
        self.db, self.entries, self.instance_id = db, entries, instance_id
        self.world = _SQLiteTransaction(db)

    def grant(self, grant_id):
        row = self.db.execute('SELECT * FROM bridge_grants WHERE grant_id=?', (str(grant_id),)).fetchone()
        return _grant(row) if row else None

    def effective_revoked(self, grant_id):
        return any(row['instance_id'] == self.instance_id and row['grant_id'] == str(grant_id)
                   for row in self.entries)

    def replay(self, identity, fingerprint):
        row = self.db.execute('SELECT fingerprint,grant_id,revision,operation FROM bridge_idempotency WHERE producer=? AND source=? AND slot=?',
                              (identity.producer, identity.source, identity.slot)).fetchone()
        if row is None:
            return None
        if row['fingerprint'] != fingerprint:
            deny(BC.IDEMPOTENCY_CONFLICT)
        return BridgeReceipt(DomainId.parse(row['grant_id']), BridgeGrantRevision(row['revision']),
                             BridgeGrantStatus.ACTIVE if row['revision'] == 1 else BridgeGrantStatus.REVOKED)

    def remember(self, identity, fingerprint, operation, receipt):
        self.db.execute('INSERT INTO bridge_idempotency VALUES(?,?,?,?,?,?,?)',
                        (identity.producer, identity.source, identity.slot, fingerprint, operation,
                         str(receipt.grant_id), receipt.revision.value))

    def insert_grant(self, grant, identity, fingerprint):
        p, s, t = grant.proposal, grant.proposal.source_scope, grant.proposal.target_scope
        self.db.execute('INSERT INTO bridge_grants VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (str(grant.grant_id), str(grant.principal.owner_id), str(grant.principal.principal_id),
             str(s.owner_id), str(s.soul_id), str(s.world_id), str(s.timeline_id),
             str(t.owner_id), str(t.soul_id), str(t.world_id), str(t.timeline_id),
             p.data_class.value, dumps(list(p.allowed_fields)), p.purpose.value,
             p.target_audience.kind.value, str(p.target_audience.target), p.expires_at.isoformat(),
             1, 'active', grant.created_at.isoformat(), None, None))
        self.db.execute("INSERT INTO bridge_operations(grant_id,actor,operation,revision,created_at,fingerprint) VALUES(?,?,'create',1,?,?)",
                        (str(grant.grant_id), str(grant.principal.principal_id), grant.created_at.isoformat(), fingerprint))
        receipt = BridgeReceipt(grant.grant_id, grant.revision, grant.status)
        self.remember(identity, fingerprint, 'create', receipt)
        return receipt

    def revoke(self, grant, actor, at, identity, fingerprint, control_entry):
        changed = self.db.execute("UPDATE bridge_grants SET status='revoked',revision=2,revoked_by=?,revoked_at=? WHERE grant_id=? AND revision=1 AND status='active'",
            (str(actor.principal_id), at.isoformat(), str(grant.grant_id))).rowcount
        if changed != 1:
            deny(BC.GRANT_REVISION_CONFLICT)
        self.db.execute("INSERT INTO bridge_operations(grant_id,actor,operation,revision,created_at,fingerprint) VALUES(?,?,'revoke',2,?,?)",
                        (str(grant.grant_id), str(actor.principal_id), at.isoformat(), fingerprint))
        self.db.execute('INSERT INTO bridge_applied_controls VALUES(?,?)',
                        (control_entry['sequence'], control_entry['fingerprint']))
        receipt = BridgeReceipt(grant.grant_id, BridgeGrantRevision(2), BridgeGrantStatus.REVOKED)
        self.remember(identity, fingerprint, 'revoke', receipt)
        return receipt


class SQLiteBridgeRepository:
    """附着既有 World runtime_id；不会触发第二次 World startup recovery。"""
    def __init__(self, root, instance_id, *, runtime_id, timeout=5):
        self.root, self.instance_id = Path(root).resolve(), instance_id
        if type(runtime_id) is not str or not runtime_id or not 0 < timeout <= 60:
            deny(BC.INVALID_ARGUMENT)
        self.runtime_id, self.timeout, self.closed = runtime_id, timeout, False
        from .durable import registry, state_home
        reg = registry(self.root)
        inst = reg['instances'][instance_id]
        self.path = state_home(self.root, inst) / 'agents' / inst['agent_id'] / 'life.db'
        self.generation = inst['generation']
        self.reconcile()
        with self.transaction() as tx:
            validate_bridge_data(tx.db)

    @contextmanager
    def transaction(self):
        from .durable import locked, registry
        if self.closed:
            deny(BC.RECOVERY_REQUIRED)
        db = None
        try:
            with locked(self.root, 'management', self.timeout), locked(self.root, self.instance_id, self.timeout):
                reg = registry(self.root)
                if reg['instances'][self.instance_id]['generation'] != self.generation:
                    deny(BC.RECOVERY_REQUIRED)
                with control(self.root, reg.get('bridge_install_id')) as (control_db, entries), storage_errors():
                    db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True,
                                         isolation_level=None, timeout=self.timeout)
                    db.row_factory = sqlite3.Row
                    db.execute('PRAGMA foreign_keys=ON')
                    db.execute('BEGIN IMMEDIATE')
                    validate_schema(db)
                    runtime = db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()
                    if runtime is None or runtime[0] != self.runtime_id:
                        deny(BC.RECOVERY_REQUIRED)
                    applied = dict(db.execute('SELECT sequence,fingerprint FROM bridge_applied_controls'))
                    expected_applied = {entry['sequence']: entry['fingerprint'] for entry in entries
                                        if entry['instance_id'] == self.instance_id}
                    if applied != expected_applied:
                        # 备份/控制域不一致时，业务库不能单独决定授权是否有效。
                        deny(BC.CONTROL_REQUIRED)
                    for entry in entries:
                        if entry['instance_id'] == self.instance_id:
                            current = db.execute('SELECT status FROM bridge_grants WHERE grant_id=?',
                                                 (entry['grant_id'],)).fetchone()
                            if current is not None and current[0] != 'revoked':
                                deny(BC.CONTROL_REQUIRED)
                    tx = BridgeTransaction(db, entries, self.instance_id)
                    tx.control_db, tx.install_id = control_db, reg['bridge_install_id']
                    try:
                        yield tx
                        db.commit()
                    except BaseException:
                        db.rollback()
                        raise
                    finally:
                        tx.world._open = False
        except TimeoutError:
            deny(BC.STORAGE_BUSY)
        except WorldRuntimeError as exc:
            deny(BC.SCHEMA_MISMATCH if exc.code is WC.SCHEMA_MISMATCH else BC.STORAGE_CORRUPT)
        finally:
            if db is not None:
                db.close()

    def reconcile(self):
        """外部撤销事实优先；用于 restore/启动 crash 收敛。"""
        from .durable import locked, registry
        with locked(self.root, 'management', self.timeout), locked(self.root, self.instance_id, self.timeout):
            reg = registry(self.root)
            if reg['instances'][self.instance_id]['generation'] != self.generation:
                deny(BC.RECOVERY_REQUIRED)
            with control(self.root, reg.get('bridge_install_id')) as (cdb, entries):
                with closing(sqlite3.connect(self.path)) as db:
                    with db:
                        db.execute('BEGIN IMMEDIATE')
                        validate_schema(db)
                        current = db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()
                        if current is None or current[0] != self.runtime_id:
                            deny(BC.RECOVERY_REQUIRED)
                        reconcile_db(db, entries, self.instance_id)
                cdb.executemany('UPDATE intents SET completed=1 WHERE instance_id=? AND sequence=?',
                    [(self.instance_id, e['sequence']) for e in entries if e['instance_id'] == self.instance_id])

    def close(self):
        self.closed = True
