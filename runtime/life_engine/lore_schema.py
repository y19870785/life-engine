"""Schema 5 的实例本地 Lore 资产、绑定、审计和幂等结构。"""

LORE_DDL = (
    """CREATE TABLE lore_books (
        book_id TEXT PRIMARY KEY NOT NULL, owner_id TEXT NOT NULL,
        display_name TEXT NOT NULL, current_version INTEGER NOT NULL CHECK(current_version>=1),
        source_type TEXT NOT NULL, source_metadata TEXT NOT NULL,
        created_at TEXT NOT NULL, created_by TEXT NOT NULL,
        UNIQUE(book_id,owner_id))""",
    "CREATE INDEX lore_books_owner ON lore_books(owner_id,book_id)",
    """CREATE TABLE lore_book_versions (
        book_id TEXT NOT NULL REFERENCES lore_books(book_id),
        version INTEGER NOT NULL CHECK(version>=1), source_type TEXT NOT NULL,
        source_fingerprint TEXT NOT NULL, payload_fingerprint TEXT,
        source_metadata TEXT NOT NULL, registration_fingerprint TEXT NOT NULL,
        entry_count INTEGER NOT NULL CHECK(entry_count>=0), runtime_compatible INTEGER NOT NULL
            CHECK(runtime_compatible IN (0,1)), created_at TEXT NOT NULL, created_by TEXT NOT NULL,
        PRIMARY KEY(book_id,version))""",
    """CREATE TABLE lore_entries (
        book_id TEXT NOT NULL, book_version INTEGER NOT NULL, entry_id TEXT NOT NULL,
        enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
        constant INTEGER NOT NULL CHECK(constant IN (0,1)),
        selective INTEGER NOT NULL CHECK(selective IN (0,1)),
        case_sensitive INTEGER NOT NULL CHECK(case_sensitive IN (0,1)),
        runtime_priority INTEGER NOT NULL, runtime_order INTEGER NOT NULL CHECK(runtime_order>=0),
        text TEXT NOT NULL, runtime_disabled_reason TEXT,
        source_metadata TEXT NOT NULL, diagnostics TEXT NOT NULL,
        PRIMARY KEY(book_id,book_version,entry_id),
        FOREIGN KEY(book_id,book_version) REFERENCES lore_book_versions(book_id,version))""",
    "CREATE INDEX lore_entries_order ON lore_entries(book_id,book_version,runtime_priority,runtime_order,entry_id)",
    """CREATE TABLE lore_entry_triggers (
        book_id TEXT NOT NULL, book_version INTEGER NOT NULL, entry_id TEXT NOT NULL,
        trigger_kind TEXT NOT NULL CHECK(trigger_kind IN ('primary','secondary')),
        position INTEGER NOT NULL CHECK(position>=0), text TEXT NOT NULL,
        PRIMARY KEY(book_id,book_version,entry_id,trigger_kind,position),
        FOREIGN KEY(book_id,book_version,entry_id) REFERENCES lore_entries(book_id,book_version,entry_id))""",
    """CREATE TABLE lore_binding_state (
        owner_id TEXT NOT NULL, soul_id TEXT NOT NULL, world_id TEXT NOT NULL,
        timeline_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=0),
        PRIMARY KEY(owner_id,soul_id,world_id,timeline_id), UNIQUE(world_id,timeline_id),
        FOREIGN KEY(world_id,owner_id) REFERENCES worlds(world_id,owner_id),
        FOREIGN KEY(world_id,timeline_id) REFERENCES world_timelines(world_id,timeline_id))""",
    """CREATE TRIGGER lore_binding_created AFTER INSERT ON world_timelines
        BEGIN INSERT INTO lore_binding_state SELECT owner_id,soul_id,world_id,NEW.timeline_id,0
        FROM worlds WHERE world_id=NEW.world_id; END""",
    """CREATE TABLE lore_world_bindings (
        owner_id TEXT NOT NULL, soul_id TEXT NOT NULL, world_id TEXT NOT NULL,
        timeline_id TEXT NOT NULL, book_id TEXT NOT NULL, book_version INTEGER NOT NULL,
        enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
        binding_order INTEGER NOT NULL CHECK(binding_order BETWEEN 0 AND 2147483647),
        source TEXT NOT NULL,
        PRIMARY KEY(owner_id,soul_id,world_id,timeline_id,book_id),
        FOREIGN KEY(owner_id,soul_id,world_id,timeline_id)
            REFERENCES lore_binding_state(owner_id,soul_id,world_id,timeline_id),
        FOREIGN KEY(book_id,book_version) REFERENCES lore_book_versions(book_id,version))""",
    "CREATE INDEX lore_bindings_book ON lore_world_bindings(book_id,book_version)",
    """CREATE TABLE lore_operations (
        sequence INTEGER PRIMARY KEY, actor TEXT NOT NULL,
        operation TEXT NOT NULL CHECK(operation IN ('register_book','register_version','bind','unbind','enable','disable','rebind')),
        owner_id TEXT NOT NULL, soul_id TEXT, world_id TEXT, timeline_id TEXT,
        book_id TEXT NOT NULL REFERENCES lore_books(book_id), book_version INTEGER NOT NULL,
        revision INTEGER, created_at TEXT NOT NULL,
        FOREIGN KEY(book_id,book_version) REFERENCES lore_book_versions(book_id,version))""",
    "CREATE INDEX lore_operations_scope ON lore_operations(world_id,timeline_id,sequence)",
    """CREATE TABLE lore_idempotency (
        producer TEXT NOT NULL, source TEXT NOT NULL, slot TEXT NOT NULL,
        fingerprint TEXT NOT NULL, operation INTEGER NOT NULL REFERENCES lore_operations(sequence),
        receipt TEXT NOT NULL, PRIMARY KEY(producer,source,slot))""",
    """CREATE TRIGGER lore_version_immutable BEFORE UPDATE ON lore_book_versions
        BEGIN SELECT RAISE(ABORT,'LoreVersionImmutable'); END""",
    """CREATE TRIGGER lore_version_no_delete BEFORE DELETE ON lore_book_versions
        BEGIN SELECT RAISE(ABORT,'LoreVersionImmutable'); END""",
    """CREATE TRIGGER lore_entry_immutable BEFORE UPDATE ON lore_entries
        BEGIN SELECT RAISE(ABORT,'LoreEntryImmutable'); END""",
    """CREATE TRIGGER lore_entry_no_delete BEFORE DELETE ON lore_entries
        BEGIN SELECT RAISE(ABORT,'LoreEntryImmutable'); END""",
    """CREATE TRIGGER lore_trigger_immutable BEFORE UPDATE ON lore_entry_triggers
        BEGIN SELECT RAISE(ABORT,'LoreTriggerImmutable'); END""",
    """CREATE TRIGGER lore_trigger_no_delete BEFORE DELETE ON lore_entry_triggers
        BEGIN SELECT RAISE(ABORT,'LoreTriggerImmutable'); END""",
)


def create_lore_schema(db):
    """在全新库或已迁移副本创建结构，并补齐现有 World 的零修订。"""
    for statement in LORE_DDL:
        db.execute(statement)
    db.execute('INSERT INTO lore_binding_state SELECT w.owner_id,w.soul_id,w.world_id,t.timeline_id,0 '
               'FROM worlds w JOIN world_timelines t ON t.world_id=w.world_id')
