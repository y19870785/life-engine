"""Schema 7 Bridge business state；瞬时投影不入库。"""

BRIDGE_DDL = (
    """CREATE TABLE bridge_grants (
        grant_id TEXT PRIMARY KEY NOT NULL,
        owner_id TEXT NOT NULL, created_by TEXT NOT NULL,
        source_owner_id TEXT NOT NULL, source_soul_id TEXT NOT NULL,
        source_world_id TEXT NOT NULL, source_timeline_id TEXT NOT NULL,
        target_owner_id TEXT NOT NULL, target_soul_id TEXT NOT NULL,
        target_world_id TEXT NOT NULL, target_timeline_id TEXT NOT NULL,
        data_class TEXT NOT NULL CHECK(data_class IN ('memory','story_projection')),
        allowed_fields TEXT NOT NULL, purpose TEXT NOT NULL CHECK(purpose='prompt_context'),
        audience_kind TEXT NOT NULL CHECK(audience_kind IN ('soul','character_instance')),
        audience_target TEXT NOT NULL, expires_at TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK(revision IN (1,2)),
        status TEXT NOT NULL CHECK(status IN ('active','revoked')),
        created_at TEXT NOT NULL, revoked_by TEXT, revoked_at TEXT,
        FOREIGN KEY(source_world_id,source_owner_id) REFERENCES worlds(world_id,owner_id),
        FOREIGN KEY(source_world_id,source_timeline_id) REFERENCES world_timelines(world_id,timeline_id),
        FOREIGN KEY(target_world_id,target_owner_id) REFERENCES worlds(world_id,owner_id),
        FOREIGN KEY(target_world_id,target_timeline_id) REFERENCES world_timelines(world_id,timeline_id),
        CHECK(source_world_id<>target_world_id), CHECK(owner_id=source_owner_id AND owner_id=target_owner_id),
        CHECK((status='active' AND revision=1 AND revoked_by IS NULL AND revoked_at IS NULL)
           OR (status='revoked' AND revision=2 AND revoked_by IS NOT NULL AND revoked_at IS NOT NULL)))""",
    "CREATE INDEX bridge_grants_owner ON bridge_grants(owner_id,grant_id)",
    """CREATE TABLE bridge_operations (
        sequence INTEGER PRIMARY KEY AUTOINCREMENT, grant_id TEXT NOT NULL REFERENCES bridge_grants(grant_id),
        actor TEXT NOT NULL, operation TEXT NOT NULL CHECK(operation IN ('create','revoke')),
        revision INTEGER NOT NULL CHECK(revision IN (1,2)), created_at TEXT NOT NULL,
        fingerprint TEXT NOT NULL, UNIQUE(grant_id,revision))""",
    """CREATE TABLE bridge_idempotency (
        producer TEXT NOT NULL, source TEXT NOT NULL, slot TEXT NOT NULL,
        fingerprint TEXT NOT NULL, operation TEXT NOT NULL CHECK(operation IN ('create','revoke')),
        grant_id TEXT NOT NULL REFERENCES bridge_grants(grant_id),
        revision INTEGER NOT NULL CHECK(revision IN (1,2)),
        PRIMARY KEY(producer,source,slot))""",
    """CREATE TABLE bridge_applied_controls (
        sequence INTEGER PRIMARY KEY CHECK(sequence>=1), fingerprint TEXT NOT NULL)""",
    """CREATE TRIGGER bridge_grant_policy_immutable BEFORE UPDATE ON bridge_grants
        WHEN NEW.grant_id<>OLD.grant_id OR NEW.owner_id<>OLD.owner_id OR NEW.created_by<>OLD.created_by
          OR NEW.source_owner_id<>OLD.source_owner_id OR NEW.source_soul_id<>OLD.source_soul_id
          OR NEW.source_world_id<>OLD.source_world_id OR NEW.source_timeline_id<>OLD.source_timeline_id
          OR NEW.target_owner_id<>OLD.target_owner_id OR NEW.target_soul_id<>OLD.target_soul_id
          OR NEW.target_world_id<>OLD.target_world_id OR NEW.target_timeline_id<>OLD.target_timeline_id
          OR NEW.data_class<>OLD.data_class OR NEW.allowed_fields<>OLD.allowed_fields
          OR NEW.purpose<>OLD.purpose OR NEW.audience_kind<>OLD.audience_kind
          OR NEW.audience_target<>OLD.audience_target OR NEW.expires_at<>OLD.expires_at
          OR NEW.created_at<>OLD.created_at OR OLD.status<>'active' OR NEW.status<>'revoked'
          OR OLD.revision<>1 OR NEW.revision<>2 OR NEW.revoked_by IS NULL OR NEW.revoked_at IS NULL
        BEGIN SELECT RAISE(ABORT,'BridgeGrantImmutable'); END""",
    """CREATE TRIGGER bridge_grant_nodelete BEFORE DELETE ON bridge_grants
        BEGIN SELECT RAISE(ABORT,'BridgeGrantImmutable'); END""",
    """CREATE TRIGGER bridge_operations_immutable BEFORE UPDATE ON bridge_operations
        BEGIN SELECT RAISE(ABORT,'BridgeOperationImmutable'); END""",
    """CREATE TRIGGER bridge_operations_nodelete BEFORE DELETE ON bridge_operations
        BEGIN SELECT RAISE(ABORT,'BridgeOperationImmutable'); END""",
    """CREATE TRIGGER bridge_applied_controls_immutable BEFORE UPDATE ON bridge_applied_controls
        BEGIN SELECT RAISE(ABORT,'BridgeControlImmutable'); END""",
    """CREATE TRIGGER bridge_applied_controls_nodelete BEFORE DELETE ON bridge_applied_controls
        BEGIN SELECT RAISE(ABORT,'BridgeControlImmutable'); END""",
    """CREATE TRIGGER bridge_idempotency_immutable BEFORE UPDATE ON bridge_idempotency
        BEGIN SELECT RAISE(ABORT,'BridgeIdempotencyImmutable'); END""",
    """CREATE TRIGGER bridge_idempotency_nodelete BEFORE DELETE ON bridge_idempotency
        BEGIN SELECT RAISE(ABORT,'BridgeIdempotencyImmutable'); END""",
)


def create_bridge_schema(db):
    for statement in BRIDGE_DDL:
        db.execute(statement)
