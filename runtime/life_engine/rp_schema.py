"""Explicit SQLite 2 -> 3 migration. Caller migrates an inactive, backed-up copy."""
SCHEMA_VERSION = 3

TABLES = [
    """CREATE TABLE roleplay_cards (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE COLLATE NOCASE,
        source_path TEXT NOT NULL, raw_json TEXT NOT NULL, parsed_json TEXT NOT NULL,
        avatar BLOB, created_at REAL NOT NULL)""",
    """CREATE TABLE roleplay_lorebook_entries (
        id INTEGER PRIMARY KEY, card_id INTEGER NOT NULL REFERENCES roleplay_cards(id) ON DELETE CASCADE,
        book_name TEXT NOT NULL, entry_json TEXT NOT NULL)""",
    """CREATE TABLE roleplay_sessions (
        id INTEGER PRIMARY KEY, agent_id TEXT NOT NULL,
        card_id INTEGER NOT NULL REFERENCES roleplay_cards(id) ON DELETE CASCADE,
        started_at REAL NOT NULL, ended_at REAL,
        status TEXT NOT NULL CHECK(status IN ('active','ended')),
        summary TEXT NOT NULL DEFAULT '', UNIQUE(id,card_id),
        CHECK((status='active' AND ended_at IS NULL) OR (status='ended' AND ended_at IS NOT NULL)))""",
    "CREATE UNIQUE INDEX one_active_roleplay ON roleplay_sessions(status) WHERE status='active'",
    """CREATE TABLE roleplay_messages (
        id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL, card_id INTEGER NOT NULL,
        at REAL NOT NULL, role TEXT NOT NULL CHECK(role IN ('user','assistant')),
        content TEXT NOT NULL, event_key TEXT,
        FOREIGN KEY(session_id,card_id) REFERENCES roleplay_sessions(id,card_id) ON DELETE CASCADE,
        UNIQUE(session_id,event_key))""",
    """CREATE TABLE memories_v3 (
        id INTEGER PRIMARY KEY, at REAL NOT NULL, kind TEXT NOT NULL,
        summary TEXT NOT NULL, provenance TEXT NOT NULL,
        scope TEXT NOT NULL DEFAULT 'soul' CHECK(scope IN ('soul','persona')),
        card_id INTEGER REFERENCES roleplay_cards(id) ON DELETE CASCADE,
        session_id INTEGER,
        FOREIGN KEY(session_id,card_id) REFERENCES roleplay_sessions(id,card_id) ON DELETE CASCADE,
        CHECK((scope='soul' AND card_id IS NULL AND session_id IS NULL)
           OR (scope='persona' AND card_id IS NOT NULL AND session_id IS NOT NULL)))""",
    "INSERT INTO memories_v3(id,at,kind,summary,provenance) SELECT id,at,kind,summary,provenance FROM memories",
    "DROP TABLE memories",
    "ALTER TABLE memories_v3 RENAME TO memories",
    "CREATE INDEX memory_namespace ON memories(scope,card_id,id)",
]


def migrate(db):
    version = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
    if version == str(SCHEMA_VERSION):
        return
    if version != '2':
        raise ValueError('Unsupported SQLite schema for roleplay migration')
    for sql in TABLES:
        db.execute(sql)
    if db.execute('PRAGMA foreign_key_check').fetchone():
        raise ValueError('Foreign key check failed')
    db.execute("UPDATE meta SET value=? WHERE key='schema_version'", (str(SCHEMA_VERSION),))
