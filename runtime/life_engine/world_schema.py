"""识别历史 Schema 2/3 与 canonical Schema 4；仅迁移副本，不修复未知库。"""
from contextlib import closing
from functools import lru_cache
import sqlite3

from .world_repository import FailureCode as Code, fail

DATA_SCHEMA = 4
SCHEMA_SIGNATURES = {3: 'SP-004E-world-runtime-v1', 4: 'SP-004B-world-memory-v1'}
SIGNATURE = SCHEMA_SIGNATURES[4]
WORLD_DDL = (
    """CREATE TABLE souls (
        soul_id TEXT PRIMARY KEY NOT NULL, owner_id TEXT NOT NULL,
        soul_world_id TEXT NOT NULL UNIQUE, UNIQUE(soul_id,owner_id))""",
    """CREATE TABLE character_definitions (
        definition_id TEXT NOT NULL, version INTEGER NOT NULL CHECK(version>=1),
        owner_id TEXT NOT NULL, name TEXT NOT NULL, traits TEXT NOT NULL,
        provenance TEXT NOT NULL, PRIMARY KEY(definition_id,version))""",
    """CREATE TABLE worlds (
        world_id TEXT PRIMARY KEY NOT NULL, owner_id TEXT NOT NULL,
        soul_id TEXT NOT NULL REFERENCES souls(soul_id),
        kind TEXT NOT NULL CHECK(kind IN ('soul','roleplay')),
        status TEXT NOT NULL CHECK(status IN ('created','active','suspended','archived','tombstoned')),
        revision INTEGER NOT NULL CHECK(revision>=0),
        writer_epoch INTEGER NOT NULL CHECK(writer_epoch>=0), provenance TEXT NOT NULL,
        FOREIGN KEY(soul_id,owner_id) REFERENCES souls(soul_id,owner_id), UNIQUE(world_id,owner_id))""",
    """CREATE TABLE world_timelines (
        timeline_id TEXT PRIMARY KEY NOT NULL, world_id TEXT NOT NULL UNIQUE REFERENCES worlds(world_id),
        revision INTEGER NOT NULL CHECK(revision>=0), logical_tick INTEGER NOT NULL CHECK(logical_tick>=0),
        provenance TEXT NOT NULL, UNIQUE(world_id,timeline_id))""",
    """CREATE TABLE character_instances (
        character_instance_id TEXT PRIMARY KEY NOT NULL,
        world_id TEXT NOT NULL, timeline_id TEXT NOT NULL,
        definition_id TEXT NOT NULL, version INTEGER NOT NULL,
        position INTEGER NOT NULL CHECK(position>=0),
        state TEXT NOT NULL, relationships TEXT NOT NULL, provenance TEXT NOT NULL,
        FOREIGN KEY(world_id,timeline_id) REFERENCES world_timelines(world_id,timeline_id),
        FOREIGN KEY(definition_id,version) REFERENCES character_definitions(definition_id,version),
        UNIQUE(world_id,position), UNIQUE(world_id,timeline_id,character_instance_id))""",
    """CREATE TABLE session_bindings (
        session_id TEXT PRIMARY KEY NOT NULL, principal_id TEXT NOT NULL, owner_id TEXT NOT NULL,
        world_id TEXT NOT NULL, timeline_id TEXT NOT NULL, character_instance_id TEXT,
        writer_epoch INTEGER NOT NULL CHECK(writer_epoch>=0),
        status TEXT NOT NULL CHECK(status IN ('open','closed')),
        position INTEGER NOT NULL CHECK(position>=0),
        FOREIGN KEY(world_id,owner_id) REFERENCES worlds(world_id,owner_id),
        FOREIGN KEY(world_id,timeline_id) REFERENCES world_timelines(world_id,timeline_id),
        FOREIGN KEY(world_id,timeline_id,character_instance_id)
            REFERENCES character_instances(world_id,timeline_id,character_instance_id),
        UNIQUE(world_id,position))""",
    "CREATE UNIQUE INDEX one_open_session_per_world ON session_bindings(world_id) WHERE status='open'",
    "CREATE INDEX sessions_character ON session_bindings(character_instance_id)",
    "CREATE INDEX instances_definition ON character_instances(definition_id,version)",
    """CREATE TRIGGER fixed_character_definition BEFORE UPDATE OF definition_id,version ON character_instances
        WHEN NEW.definition_id<>OLD.definition_id OR NEW.version<>OLD.version
        BEGIN SELECT RAISE(ABORT,'DefinitionVersionConflict'); END""",
    """CREATE TRIGGER closed_session_history BEFORE UPDATE OF status ON session_bindings
        WHEN OLD.status='closed' AND NEW.status<>'closed'
        BEGIN SELECT RAISE(ABORT,'SessionBindingConflict'); END""",
)


def structure(db):
    """比较实际建表语句，覆盖列、约束、外键、索引谓词与触发器。"""
    return tuple((kind, name, ' '.join(sql.split())) for kind, name, sql in db.execute(
        "SELECT type,name,sql FROM sqlite_master WHERE name NOT GLOB 'sqlite_*' ORDER BY type,name") if sql)


@lru_cache(maxsize=3)
def expected_structure(version):
    from .store import SCHEMA
    with closing(sqlite3.connect(':memory:')) as db:
        db.executescript(SCHEMA)
        if version in (3, 4):
            for sql in WORLD_DDL:
                db.execute(sql)
        if version == 4:
            from .memory_schema import MEMORY_DDL
            for sql in MEMORY_DDL:
                db.execute(sql)
        return structure(db)


def validate_schema(db, expected=DATA_SCHEMA, agent_id=None):
    """先识别再验证；只读检查永远不建表、不迁移、不覆写元数据。"""
    try:
        meta = dict(db.execute('SELECT key,value FROM meta'))
        if expected not in (2, 3, 4) or meta.get('schema_version') != str(expected):
            fail(Code.SCHEMA_MISMATCH)
        if structure(db) != expected_structure(expected):
            fail(Code.SCHEMA_MISMATCH)
        if expected >= 3 and meta.get('world_schema') != SCHEMA_SIGNATURES[expected]:
            fail(Code.SCHEMA_MISMATCH)
        if agent_id is not None and meta.get('agent_id') != agent_id:
            fail(Code.SCHEMA_MISMATCH)
        if not meta.get('agent_id'):
            fail(Code.SCHEMA_MISMATCH)
        if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchone():
            fail(Code.STORAGE_CORRUPT)
    except sqlite3.DatabaseError as exc:
        code = getattr(exc, 'sqlite_errorcode', 0) & 255
        fail(Code.STORAGE_BUSY if code in (5, 6) else Code.SCHEMA_MISMATCH)


def create_world_schema(db, version=DATA_SCHEMA):
    for sql in WORLD_DDL:
        db.execute(sql)
    db.execute("INSERT INTO meta VALUES('world_schema',?)", (SCHEMA_SIGNATURES[version],))
    if version == 4:
        from .memory_schema import create_memory_schema
        create_memory_schema(db)


def migrate_2_to_3(db):
    """仅供 durable 的非活动副本调用；调用者拥有事务和 generation 边界。"""
    validate_schema(db, 2)
    tables = ('days', 'contacts', 'observations', 'memories', 'loops', 'photos', 'meta')
    before = {table: db.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall() for table in tables}
    create_world_schema(db, 3)
    db.execute("UPDATE meta SET value='3' WHERE key='schema_version'")
    for table, rows in before.items():
        actual = db.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall()
        if table == 'meta':
            actual = [(k, '2' if k == 'schema_version' else v) for k, v in actual if k != 'world_schema']
        if actual != rows:
            fail(Code.STORAGE_CORRUPT)
    validate_schema(db, 3)
    if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        fail(Code.STORAGE_CORRUPT)


def migrate_3_to_4(db):
    """仅迁移已验证的副本；不修改任何旧业务行或触发 World recovery。"""
    from .memory_schema import create_memory_schema
    from .world_sqlite_repository import validate_world_data
    validate_schema(db, 3)
    validate_world_data(db)
    create_memory_schema(db)
    db.execute("UPDATE meta SET value='4' WHERE key='schema_version'")
    db.execute("UPDATE meta SET value=? WHERE key='world_schema'", (SIGNATURE,))
    validate_schema(db, 4)


def migrate_copy(db):
    """副本升级的兼容入口；每个历史阶段分别识别、迁移、验证。"""
    version = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
    if version == '2':
        migrate_2_to_3(db)
        version = '3'
    if version == '3':
        migrate_3_to_4(db)
    else:
        validate_schema(db, 4)
