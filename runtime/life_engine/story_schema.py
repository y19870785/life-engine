"""Schema 6 的 Story 日志、投影、审计和幂等结构。"""
from .story import PROJECTION_VERSION

EMPTY_PROJECTION = '{"character_states":[],"relationships":[],"threads":[],"world_facts":[]}'

STORY_DDL = (
    """CREATE TABLE story_collection_state (
        owner_id TEXT NOT NULL, soul_id TEXT NOT NULL, world_id TEXT NOT NULL,
        timeline_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=0),
        logical_tick INTEGER NOT NULL CHECK(logical_tick>=0),
        last_event_sequence INTEGER NOT NULL CHECK(last_event_sequence>=0),
        projection_version TEXT NOT NULL, projection TEXT NOT NULL,
        PRIMARY KEY(owner_id,soul_id,world_id,timeline_id), UNIQUE(world_id,timeline_id),
        FOREIGN KEY(world_id,owner_id) REFERENCES worlds(world_id,owner_id),
        FOREIGN KEY(world_id,timeline_id) REFERENCES world_timelines(world_id,timeline_id))""",
    """CREATE TRIGGER story_collection_created AFTER INSERT ON world_timelines
        BEGIN INSERT INTO story_collection_state
        SELECT owner_id,soul_id,world_id,NEW.timeline_id,0,0,0,
        'SP-004C-story-projection-v1','{"character_states":[],"relationships":[],"threads":[],"world_facts":[]}'
        FROM worlds WHERE world_id=NEW.world_id; END""",
    """CREATE TABLE story_events (
        event_id TEXT PRIMARY KEY NOT NULL, owner_id TEXT NOT NULL, soul_id TEXT NOT NULL,
        world_id TEXT NOT NULL, timeline_id TEXT NOT NULL,
        event_sequence INTEGER NOT NULL CHECK(event_sequence>=1),
        story_revision INTEGER NOT NULL CHECK(story_revision>=1),
        logical_tick INTEGER NOT NULL CHECK(logical_tick>=1),
        event_kind TEXT NOT NULL CHECK(event_kind IN (
            'world_fact_set','world_fact_removed','character_state_set','character_state_removed',
            'relationship_set','relationship_removed','thread_opened','thread_updated',
            'thread_resolved','thread_cancelled','narrative_event')),
        payload_version INTEGER NOT NULL CHECK(payload_version=1), payload TEXT NOT NULL,
        provenance TEXT NOT NULL, accepted_by TEXT NOT NULL,
        character_actor_id TEXT, supersedes_event_id TEXT REFERENCES story_events(event_id),
        created_at TEXT NOT NULL, accepted_at TEXT NOT NULL,
        FOREIGN KEY(owner_id,soul_id,world_id,timeline_id)
            REFERENCES story_collection_state(owner_id,soul_id,world_id,timeline_id),
        FOREIGN KEY(world_id,timeline_id,character_actor_id)
            REFERENCES character_instances(world_id,timeline_id,character_instance_id),
        UNIQUE(owner_id,soul_id,world_id,timeline_id,event_sequence),
        UNIQUE(owner_id,soul_id,world_id,timeline_id,story_revision),
        UNIQUE(owner_id,soul_id,world_id,timeline_id,logical_tick))""",
    "CREATE INDEX story_events_scope ON story_events(world_id,timeline_id,event_sequence)",
    "CREATE INDEX story_events_supersedes ON story_events(supersedes_event_id)",
    """CREATE TABLE story_event_sources (
        event_id TEXT NOT NULL REFERENCES story_events(event_id),
        position INTEGER NOT NULL CHECK(position>=0),
        source_kind TEXT NOT NULL CHECK(source_kind IN ('story_event','memory','lore_entry','external_message')),
        source_identity TEXT NOT NULL,
        PRIMARY KEY(event_id,position))""",
    """CREATE TABLE story_operations (
        sequence INTEGER PRIMARY KEY, event_id TEXT NOT NULL UNIQUE REFERENCES story_events(event_id),
        owner_id TEXT NOT NULL, soul_id TEXT NOT NULL, world_id TEXT NOT NULL,
        timeline_id TEXT NOT NULL, actor TEXT NOT NULL,
        operation TEXT NOT NULL CHECK(operation='accept'),
        revision INTEGER NOT NULL CHECK(revision>=1), accepted_at TEXT NOT NULL,
        FOREIGN KEY(owner_id,soul_id,world_id,timeline_id)
            REFERENCES story_collection_state(owner_id,soul_id,world_id,timeline_id))""",
    "CREATE INDEX story_operations_scope ON story_operations(world_id,timeline_id,sequence)",
    """CREATE TABLE story_idempotency (
        producer TEXT NOT NULL, source TEXT NOT NULL, slot TEXT NOT NULL,
        fingerprint TEXT NOT NULL, event_id TEXT NOT NULL UNIQUE REFERENCES story_events(event_id),
        revision INTEGER NOT NULL CHECK(revision>=1), logical_tick INTEGER NOT NULL CHECK(logical_tick>=1),
        operation INTEGER NOT NULL UNIQUE REFERENCES story_operations(sequence),
        PRIMARY KEY(producer,source,slot))""",
    """CREATE TRIGGER story_event_immutable BEFORE UPDATE ON story_events
        BEGIN SELECT RAISE(ABORT,'StoryEventImmutable'); END""",
    """CREATE TRIGGER story_event_no_delete BEFORE DELETE ON story_events
        BEGIN SELECT RAISE(ABORT,'StoryEventImmutable'); END""",
    """CREATE TRIGGER story_source_immutable BEFORE UPDATE ON story_event_sources
        BEGIN SELECT RAISE(ABORT,'StorySourceImmutable'); END""",
    """CREATE TRIGGER story_source_no_delete BEFORE DELETE ON story_event_sources
        BEGIN SELECT RAISE(ABORT,'StorySourceImmutable'); END""",
)


def create_story_schema(db):
    """创建空 Story 表并给每个既有 Scope 建零修订投影。"""
    for statement in STORY_DDL:
        db.execute(statement)
    db.execute('INSERT INTO story_collection_state '
        'SELECT w.owner_id,w.soul_id,w.world_id,t.timeline_id,0,0,0,?,? '
        'FROM worlds w JOIN world_timelines t ON t.world_id=w.world_id',
        (PROJECTION_VERSION, EMPTY_PROJECTION))
