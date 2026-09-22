"""Schema 4 新增结构；历史 World DDL 保持原样。"""
MEMORY_DDL = (
    """CREATE TABLE memory_collection_state (
        owner_id TEXT NOT NULL, soul_id TEXT NOT NULL, world_id TEXT NOT NULL,
        timeline_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=0),
        PRIMARY KEY(owner_id,soul_id,world_id,timeline_id), UNIQUE(world_id,timeline_id),
        FOREIGN KEY(world_id,timeline_id) REFERENCES world_timelines(world_id,timeline_id))""",
    """CREATE TRIGGER memory_collection_created AFTER INSERT ON world_timelines
        BEGIN INSERT INTO memory_collection_state SELECT owner_id,soul_id,world_id,NEW.timeline_id,0
        FROM worlds WHERE world_id=NEW.world_id; END""",
    """CREATE TABLE world_memories (
        memory_id TEXT PRIMARY KEY NOT NULL, owner_id TEXT NOT NULL, soul_id TEXT NOT NULL,
        world_id TEXT NOT NULL, timeline_id TEXT NOT NULL,
        memory_kind TEXT NOT NULL CHECK(memory_kind IN ('episodic','semantic','summary','observation',
            'preference','relationship_experience','shared_experience')),
        content TEXT NOT NULL CHECK(length(CAST(content AS BLOB)) BETWEEN 1 AND 65536),
        content_version INTEGER NOT NULL CHECK(content_version>=1), provenance TEXT NOT NULL,
        lifecycle TEXT NOT NULL CHECK(lifecycle IN ('live','hidden','superseded','tombstoned')),
        predecessor TEXT UNIQUE REFERENCES world_memories(memory_id),
        superseded_by TEXT UNIQUE REFERENCES world_memories(memory_id), created_at TEXT NOT NULL,
        FOREIGN KEY(owner_id,soul_id,world_id,timeline_id)
            REFERENCES memory_collection_state(owner_id,soul_id,world_id,timeline_id))""",
    "CREATE INDEX memories_scope ON world_memories(owner_id,soul_id,world_id,timeline_id,lifecycle,memory_id)",
    """CREATE TABLE memory_audiences (
        memory_id TEXT NOT NULL REFERENCES world_memories(memory_id), position INTEGER NOT NULL CHECK(position>=0),
        kind TEXT NOT NULL CHECK(kind IN ('world','character_instance','user','soul','principal')), target TEXT,
        CHECK((kind='world' AND target IS NULL) OR (kind<>'world' AND target IS NOT NULL)),
        PRIMARY KEY(memory_id,position))""",
    "CREATE UNIQUE INDEX memory_audience_set ON memory_audiences(memory_id,kind,coalesce(target,''))",
    "CREATE INDEX memory_audience_target ON memory_audiences(kind,target,memory_id)",
    """CREATE TABLE memory_subjects (
        memory_id TEXT NOT NULL REFERENCES world_memories(memory_id), position INTEGER NOT NULL CHECK(position>=0),
        kind TEXT NOT NULL CHECK(kind IN ('world','character_instance','soul','text')), target TEXT, text TEXT NOT NULL,
        CHECK((kind='text' AND target IS NULL AND length(text)>0) OR (kind<>'text' AND target IS NOT NULL AND text='')),
        PRIMARY KEY(memory_id,position))""",
    """CREATE TABLE memory_lineage (
        memory_id TEXT NOT NULL REFERENCES world_memories(memory_id),
        source_id TEXT NOT NULL REFERENCES world_memories(memory_id),
        PRIMARY KEY(memory_id,source_id), CHECK(memory_id<>source_id))""",
    "CREATE INDEX memory_lineage_source ON memory_lineage(source_id,memory_id)",
    """CREATE TABLE memory_operations (
        sequence INTEGER PRIMARY KEY, world_id TEXT NOT NULL, timeline_id TEXT NOT NULL,
        memory_id TEXT NOT NULL REFERENCES world_memories(memory_id), actor TEXT NOT NULL,
        action TEXT NOT NULL CHECK(action IN ('create','accept','reject','supersede','hide','unhide','delete','audience_change')),
        predecessor TEXT REFERENCES world_memories(memory_id), created_at TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK(revision>=1),
        FOREIGN KEY(world_id,timeline_id) REFERENCES world_timelines(world_id,timeline_id))""",
    """CREATE TABLE memory_idempotency (
        owner_id TEXT NOT NULL, soul_id TEXT NOT NULL, world_id TEXT NOT NULL, timeline_id TEXT NOT NULL,
        producer TEXT NOT NULL, source TEXT NOT NULL, slot TEXT NOT NULL,
        fingerprint TEXT NOT NULL, memory_id TEXT NOT NULL REFERENCES world_memories(memory_id),
        revision INTEGER NOT NULL CHECK(revision>=1), operation INTEGER NOT NULL REFERENCES memory_operations(sequence),
        PRIMARY KEY(owner_id,soul_id,world_id,timeline_id,producer,source,slot))""",
    """CREATE TABLE memory_applied_controls (
        sequence INTEGER PRIMARY KEY CHECK(sequence>0), fingerprint TEXT NOT NULL)""",
    """CREATE TRIGGER memory_immutable BEFORE UPDATE OF memory_id,owner_id,soul_id,world_id,timeline_id,
        memory_kind,content,content_version,provenance,predecessor,created_at ON world_memories
        BEGIN SELECT RAISE(ABORT,'MemoryImmutable'); END""",
)


def create_memory_schema(db):
    for statement in MEMORY_DDL:
        db.execute(statement)
    db.execute('INSERT INTO memory_collection_state SELECT w.owner_id,w.soul_id,w.world_id,t.timeline_id,0 '
               'FROM worlds w JOIN world_timelines t ON t.world_id=w.world_id')
    db.execute("INSERT INTO meta VALUES('last_applied_memory_control_seq','0')")
