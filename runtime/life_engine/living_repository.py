"""同连接校验 World 与 Living；安装锁先于 SQLite 事务。"""
from contextlib import contextmanager
from pathlib import Path
import json
import sqlite3

from .living_domain import fail, fingerprint, scope_values, LivingError, REASONS
from .living_policy import validate_policy
from .world_schema import validate_schema
from .world_sqlite_repository import _SQLiteTransaction
from .world_repository import WorldRuntimeError, FailureCode

TABLES = ('living_roots','living_policies','living_days','living_locations','living_activities',
          'living_followups','living_observations','living_choices','living_opportunities',
          'living_schedule','living_decisions','living_intents','living_attempts','living_delivery_results','living_inbound')


def state_digest(db, root):
    return fingerprint({table:[dict(r) for r in db.execute(
        f'SELECT * FROM {table} WHERE root_id=? ORDER BY rowid',(root,))] for table in TABLES})


def validate_living_data(db):
    old=db.row_factory; db.row_factory=sqlite3.Row
    try:
        from .world_sqlite_repository import validate_world_data
        validate_world_data(db)
        if db.execute('PRAGMA foreign_key_check').fetchone(): fail('STATE_CORRUPT')
        world=_SQLiteTransaction(db)
        for root in db.execute('SELECT * FROM living_roots'):
            from .domain import DomainId, WorldKind
            w=world.get_world(DomainId.parse(root['world_id']))
            if scope_values(w.timeline.scope)!=tuple(root[k] for k in ('owner_id','soul_id','world_id','timeline_id')) or w.world.kind is not WorldKind.SOUL:
                fail('STATE_CORRUPT')
            if not db.execute('SELECT 1 FROM living_policies WHERE root_id=? AND revision=?',(root['root_id'],root['policy_revision'])).fetchone(): fail('STATE_CORRUPT')
            logs=list(db.execute('SELECT * FROM living_transitions WHERE root_id=? ORDER BY revision',(root['root_id'],)))
            if [r['revision'] for r in logs]!=list(range(1,root['revision']+1)): fail('STATE_CORRUPT')
            for r in logs:
                if r['previous_revision']!=r['revision']-1 or fingerprint(json.loads(r['changes']))!=r['fingerprint']: fail('STATE_CORRUPT')
            if logs and json.loads(logs[-1]['changes'])['state_digest']!=state_digest(db,root['root_id']): fail('STATE_CORRUPT')
        for row in db.execute('SELECT * FROM living_policies'):
            if fingerprint(validate_policy(json.loads(row['payload'])))!=row['fingerprint']: fail('STATE_CORRUPT')
        for row in db.execute('SELECT * FROM living_choices'):
            if fingerprint(json.loads(row['input']))!=row['input_fingerprint'] or fingerprint([row['input_fingerprint'],json.loads(row['value'])])!=row['fingerprint']: fail('STATE_CORRUPT')
            inp=json.loads(row['input'])
            if inp[0]!=[row['root_id'],row['event'],row['purpose'],row['algorithm'],row['policy_revision']] or json.loads(row['value']) not in inp[1]: fail('STATE_CORRUPT')
        for table in ('living_observations','living_delivery_results','living_operations'):
            for row in db.execute(f'SELECT * FROM {table}'):
                if fingerprint(json.loads(row['payload']))!=row['fingerprint']: fail('STATE_CORRUPT')
        sources={'DAY':'living_days','ACTIVITY':'living_activities','OPPORTUNITY':'living_opportunities',
                 'FOLLOWUP':'living_followups','OBSERVATION':'living_observations','CHOICE':'living_choices'}
        for row in db.execute('SELECT * FROM living_schedule'):
            table=sources[row['subject_type']]
            if not db.execute(f'SELECT 1 FROM {table} WHERE root_id=? AND id=?',(row['root_id'],row['subject'])).fetchone(): fail('STATE_CORRUPT')
        for row in db.execute('SELECT * FROM living_opportunities'):
            if row['reason'] not in REASONS: fail('STATE_CORRUPT')
            if row['source_type']!='LEGACY':
                table=sources[row['source_type']]
                if not db.execute(f'SELECT 1 FROM {table} WHERE root_id=? AND id=?',(row['root_id'],row['source_ref'])).fetchone(): fail('STATE_CORRUPT')
        if db.execute("SELECT 1 FROM living_intents i JOIN living_decisions d ON i.decision_id=d.id WHERE d.result!='ALLOW' OR d.opportunity!=i.opportunity").fetchone(): fail('STATE_CORRUPT')
        if db.execute('SELECT 1 FROM living_days d JOIN living_roots r ON r.root_id=d.root_id WHERE d.epoch>r.timezone_epoch').fetchone(): fail('STATE_CORRUPT')
        if db.execute("SELECT 1 FROM living_activities a JOIN living_activities b ON a.root_id=b.root_id AND a.id<b.id WHERE a.state NOT IN ('CANCELLED','SKIPPED') AND b.state NOT IN ('CANCELLED','SKIPPED') AND a.start<b.end AND b.start<a.end").fetchone(): fail('STATE_CORRUPT')
        if db.execute("SELECT 1 FROM living_activities WHERE (state IN ('ACTIVE','COMPLETED') AND (activated_at IS NULL OR activated_at<start OR activated_at>=end)) OR (state='SKIPPED' AND activated_at IS NOT NULL) OR (state='COMPLETED' AND (ended_at IS NULL OR ended_at<end))").fetchone(): fail('STATE_CORRUPT')
        if db.execute("SELECT 1 FROM living_attempts a JOIN living_intents i ON i.id=a.intent WHERE a.root_id!=i.root_id OR i.state!='ATTEMPTED' OR a.claimed_at<i.reserved_at OR a.target!=i.target OR (a.state IN ('SENT','ACKNOWLEDGED') AND (a.message_id IS NULL OR a.sent_at IS NULL OR a.sent_at<a.claimed_at))").fetchone(): fail('STATE_CORRUPT')
        for row in db.execute('SELECT * FROM living_operations'):
            receipt=json.loads(row['receipt'])
            if fingerprint(receipt)!=row['receipt_fingerprint']: fail('STATE_CORRUPT')
            if receipt.get('revision')!=row['revision'] or not db.execute('SELECT 1 FROM living_transitions WHERE root_id=? AND revision=?',(row['root_id'],row['revision'])).fetchone(): fail('STATE_CORRUPT')
        for row in db.execute('SELECT * FROM living_inbound'):
            if row['fingerprint']!=fingerprint([row['source'],row['event_id'],row['received_at']]): fail('STATE_CORRUPT')
    except LivingError as exc:
        if exc.code=='STATE_CORRUPT': raise
        fail('STATE_CORRUPT')
    except (ValueError,TypeError,KeyError,sqlite3.Error):
        fail('STATE_CORRUPT')
    finally:
        db.row_factory=old


class LivingRepository:
    def __init__(self, root, instance_id, *, runtime_id):
        from .durable import registry, state_home
        self.root=Path(root).resolve(); self.instance_id=instance_id; self.runtime_id=runtime_id
        reg=registry(self.root); inst=reg['instances'][instance_id]
        self.generation=inst['generation']
        self.path=state_home(self.root,inst)/'agents'/inst['agent_id']/'life.db'

    @contextmanager
    def recovery_read_transaction(self):
        """只读一致快照；授权后由 recovery projection 有界校验选中的记录。

        不运行 mutation transaction 的全库 receipt materialization，也不新建 incarnation。
        安装锁阻止 restore/受信 writer 交错；mode=ro 和 query_only 双重禁止写入。
        """
        from .durable import locked, registry
        db = None
        try:
            with locked(self.root, 'management'), locked(self.root, self.instance_id):
                if registry(self.root)['instances'][self.instance_id]['generation'] != self.generation:
                    fail('GENERATION_STALE')
                db = sqlite3.connect(self.path.as_uri()+'?mode=ro', uri=True,
                                     isolation_level=None, timeout=5)
                db.row_factory = sqlite3.Row
                db.execute('PRAGMA query_only=ON')
                db.execute('BEGIN')
                validate_schema(db)
                row = db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()
                if not row or row[0] != self.runtime_id:
                    fail('GENERATION_STALE')
                yield db
        except WorldRuntimeError as exc:
            if exc.code in (FailureCode.STORAGE_CORRUPT, FailureCode.SCHEMA_MISMATCH):
                fail('STATE_CORRUPT')
            raise
        except sqlite3.Error:
            fail('STATE_CORRUPT')
        finally:
            if db is not None:
                db.rollback()
                db.close()

    @contextmanager
    def transaction(self):
        from .durable import locked, registry
        db=None
        try:
            with locked(self.root,'management'),locked(self.root,self.instance_id):
                reg=registry(self.root)
                if reg['instances'][self.instance_id]['generation']!=self.generation: fail('GENERATION_STALE')
                db=sqlite3.connect(self.path.as_uri()+'?mode=rw',uri=True,isolation_level=None,timeout=5)
                db.row_factory=sqlite3.Row; db.execute('PRAGMA foreign_keys=ON'); db.execute('BEGIN IMMEDIATE')
                validate_schema(db)
                row=db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()
                if not row or row[0]!=self.runtime_id: fail('GENERATION_STALE')
                validate_living_data(db)
                yield db
                validate_living_data(db)
                db.commit()
        except BaseException:
            if db is not None: db.rollback()
            raise
        finally:
            if db is not None: db.close()
