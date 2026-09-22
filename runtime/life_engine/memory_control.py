"""不随业务 generation 回退的删除控制账本；不存 Memory 正文。"""
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import sqlite3
from uuid import uuid4

from .memory_repository import MemoryFailure as MC, MemoryRuntimeError, deny
from .world_repository import WorldRuntimeError
from .world_codec import dumps
from .world_sqlite_repository import storage_errors

CONTROL_DDL = (
    'CREATE TABLE identity (install_id TEXT PRIMARY KEY NOT NULL)',
    '''CREATE TABLE intents (sequence INTEGER PRIMARY KEY, instance_id TEXT NOT NULL,
       scope TEXT NOT NULL, memory_id TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL,
       blocked TEXT NOT NULL, previous TEXT NOT NULL, fingerprint TEXT NOT NULL,
       completed INTEGER NOT NULL CHECK(completed IN (0,1)))''',
)


@lru_cache(maxsize=1)
def control_structure():
    from .world_schema import structure
    db = sqlite3.connect(':memory:')
    try:
        for statement in CONTROL_DDL:
            db.execute(statement)
        return structure(db)
    finally:
        db.close()


def fingerprint(values):
    return hashlib.sha256(dumps(values).encode('utf-8')).hexdigest()


def initialize_control(root, reg):
    """仅安装/升级协调器创建控制域，运行时缺失绝不补建。调用者持管理锁。"""
    from .durable import write
    directory = root / 'control'
    path = directory / 'memory-control.db'
    identity = reg.get('memory_install_id')
    if identity:
        with control(root, identity):
            pass
        return
    if path.exists() and (directory / 'identity.json').exists():
        from .durable import read
        candidate = read(directory / 'identity.json')['install_id']
        with control(root,candidate) as (_, entries):
            if entries:
                deny(MC.CONTROL_REQUIRED)
        reg['memory_install_id'] = candidate
        return
    if path.exists() or (directory / 'identity.json').exists():
        deny(MC.CONTROL_REQUIRED)
    directory.mkdir(parents=True, exist_ok=True)
    identity = uuid4().hex
    db = sqlite3.connect(path)
    try:
        with db:
            for statement in CONTROL_DDL:
                db.execute(statement)
            db.execute('INSERT INTO identity VALUES(?)', (identity,))
    finally:
        db.close()
    write(directory / 'identity.json', {'format':1, 'install_id': identity, 'sequence': 0, 'fingerprint': ''})
    reg['memory_install_id'] = identity


@contextmanager
def control(root, identity):
    """身份、连续序号和哈希链全部检查；独立持久锚防止账本单独回退。"""
    from .durable import read
    path = root / 'control' / 'memory-control.db'
    if not identity or not path.is_file():
        deny(MC.CONTROL_REQUIRED)
    db = None
    try:
        anchor = read(root / 'control' / 'identity.json')
        if type(anchor) is not dict or type(anchor.get('sequence')) is not int or anchor['sequence']<0:
            deny(MC.CONTROL_REQUIRED)
        with storage_errors():
            db = sqlite3.connect(path.resolve().as_uri() + '?mode=rw', uri=True,
                                 isolation_level=None, timeout=5)
            db.row_factory = sqlite3.Row
            db.execute('BEGIN IMMEDIATE')
            from .world_schema import structure
            if structure(db)!=control_structure():
                deny(MC.CONTROL_REQUIRED)
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                deny(MC.CONTROL_REQUIRED)
            identities = db.execute('SELECT install_id FROM identity').fetchall()
            if len(identities) != 1 or identities[0][0] != identity or anchor['install_id'] != identity or anchor.get('format')!=1:
                deny(MC.CONTROL_REQUIRED)
            entries = db.execute('SELECT * FROM intents ORDER BY sequence').fetchall()
            previous = ''
            for seq, row in enumerate(entries, 1):
                values = [row[k] for k in ('sequence','instance_id','scope','memory_id','actor','created_at','blocked','previous')]
                if row['sequence'] != seq or row['previous'] != previous or row['fingerprint'] != fingerprint(values):
                    deny(MC.CONTROL_REQUIRED)
                previous = row['fingerprint']
            if (anchor['sequence'], anchor['fingerprint']) != (len(entries), previous):
                deny(MC.CONTROL_REQUIRED)
            yield db, entries
            db.commit()
    except (MemoryRuntimeError,WorldRuntimeError):
        raise
    except (OSError, ValueError, TypeError, AttributeError, IndexError, KeyError, sqlite3.DatabaseError):
        deny(MC.CONTROL_REQUIRED)
    finally:
        if db is not None:
            if db.in_transaction:
                db.rollback()
            db.close()


def append_intent(root, db, entries, identity, instance_id, scope, memory_id, actor, blocked):
    """先同步拒绝意图再修改正文库；提交与锚更新之间崩溃会拒绝服务。"""
    from .durable import write
    seq = len(entries) + 1
    values = [seq, instance_id, dumps(scope), str(memory_id), str(actor),
              datetime.now(timezone.utc).isoformat(), dumps(blocked),
              entries[-1]['fingerprint'] if entries else '']
    stamp = fingerprint(values)
    db.execute('INSERT INTO intents VALUES(?,?,?,?,?,?,?,?,?,0)', (*values, stamp))
    db.commit()
    write(root / 'control' / 'identity.json', {'format':1, 'install_id': identity, 'sequence': seq, 'fingerprint': stamp})
    db.execute('BEGIN IMMEDIATE')
    return dict(zip(('sequence','instance_id','scope','memory_id','actor','created_at','blocked','previous','fingerprint'), (*values, stamp)))


def scope_values(scope):
    return [str(scope.owner_id), str(scope.soul_id), str(scope.world_id), str(scope.timeline_id)]
