"""Bridge 撤销的非回滚控制域；不保存来源正文。"""
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
import sqlite3
from uuid import uuid4

from .bridge import BridgeFailure as BC, BridgeRuntimeError, deny
from .bridge_codec import digest
from .world_sqlite_repository import storage_errors

CONTROL_DDL = (
    'CREATE TABLE identity (install_id TEXT PRIMARY KEY NOT NULL)',
    '''CREATE TABLE intents (sequence INTEGER PRIMARY KEY, instance_id TEXT NOT NULL,
       grant_id TEXT NOT NULL, revoked_revision INTEGER NOT NULL CHECK(revoked_revision=2),
       actor TEXT NOT NULL, created_at TEXT NOT NULL, previous TEXT NOT NULL,
       fingerprint TEXT NOT NULL, completed INTEGER NOT NULL CHECK(completed IN (0,1)))''',
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


def initialize_control(root, reg):
    """只有安装/升级协调器可创建。缺失的既有控制域绝不自动修复。"""
    from .durable import read, write
    directory = root / 'control'
    path, anchor = directory / 'bridge-control.db', directory / 'bridge-identity.json'
    identity = reg.get('bridge_install_id')
    if identity:
        with control(root, identity):
            pass
        return
    if path.exists() and anchor.exists():
        candidate = read(anchor)['install_id']
        with control(root, candidate) as (_, entries):
            if entries:
                deny(BC.CONTROL_REQUIRED)
        reg['bridge_install_id'] = candidate
        return
    if path.exists() or anchor.exists():
        deny(BC.CONTROL_REQUIRED)
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
    write(anchor, {'format': 1, 'install_id': identity, 'sequence': 0, 'fingerprint': ''})
    reg['bridge_install_id'] = identity


@contextmanager
def control(root, identity):
    from .durable import read
    path = root / 'control' / 'bridge-control.db'
    if not identity or not path.is_file():
        deny(BC.CONTROL_REQUIRED)
    db = None
    try:
        anchor = read(root / 'control' / 'bridge-identity.json')
        if (type(anchor) is not dict or anchor.get('format') != 1 or
                anchor.get('install_id') != identity or
                type(anchor.get('sequence')) is not int or anchor['sequence'] < 0):
            deny(BC.CONTROL_REQUIRED)
        with storage_errors():
            db = sqlite3.connect(path.resolve().as_uri() + '?mode=rw', uri=True,
                                 isolation_level=None, timeout=5)
            db.row_factory = sqlite3.Row
            db.execute('BEGIN IMMEDIATE')
            from .world_schema import structure
            if structure(db) != control_structure() or db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                deny(BC.CONTROL_REQUIRED)
            ids = db.execute('SELECT install_id FROM identity').fetchall()
            if len(ids) != 1 or ids[0][0] != identity:
                deny(BC.CONTROL_REQUIRED)
            entries = db.execute('SELECT * FROM intents ORDER BY sequence').fetchall()
            previous = ''
            for seq, row in enumerate(entries, 1):
                values = [row[k] for k in ('sequence', 'instance_id', 'grant_id',
                          'revoked_revision', 'actor', 'created_at', 'previous')]
                if (row['sequence'] != seq or row['previous'] != previous or
                        row['revoked_revision'] != 2 or row['fingerprint'] != digest(values)):
                    deny(BC.CONTROL_REQUIRED)
                previous = row['fingerprint']
            if (anchor['sequence'], anchor.get('fingerprint')) != (len(entries), previous):
                deny(BC.CONTROL_REQUIRED)
            yield db, entries
            db.commit()
    except BridgeRuntimeError:
        raise
    except (OSError, ValueError, TypeError, AttributeError, KeyError, IndexError, sqlite3.DatabaseError):
        deny(BC.CONTROL_REQUIRED)
    finally:
        if db is not None:
            if db.in_transaction:
                db.rollback()
            db.close()


def append_intent(root, db, entries, identity, instance_id, grant_id, actor):
    """先同步外部撤销，再修改业务库；锚故障只会拒绝服务。"""
    from .durable import write
    seq = len(entries) + 1
    values = [seq, instance_id, str(grant_id), 2, str(actor),
              datetime.now(timezone.utc).isoformat(), entries[-1]['fingerprint'] if entries else '']
    stamp = digest(values)
    db.execute('INSERT INTO intents VALUES(?,?,?,?,?,?,?,?,0)', (*values, stamp))
    db.commit()
    write(root / 'control' / 'bridge-identity.json',
          {'format': 1, 'install_id': identity, 'sequence': seq, 'fingerprint': stamp})
    db.execute('BEGIN IMMEDIATE')
    return {'sequence': seq, 'instance_id': instance_id, 'grant_id': str(grant_id),
            'fingerprint': stamp, 'actor': str(actor), 'created_at': values[5]}
