"""Fresh process fault hooks for disposable synthetic stores."""
import os
from pathlib import Path
import sys

from primitive import cas, connect, prepare, record, root_value
from isolation import fixture_path


path = fixture_path(Path(sys.argv[1]))
hook = sys.argv[2]
with connect(path) as db:
    if hook == "record_mid":
        item = record("CREATE", "fault-record-mid")
        db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO record VALUES(?,?,?,?)", ("incomplete", b"partial", item["transition_id"], item["payload_hash"]))
        os._exit(42)
    if hook == "prepared":
        prepare(db, record("CREATE", "fault-prepared"))
        os._exit(42)
    if hook == "before_commit":
        item = record("CREATE", "fault-before-commit")
        prepared = prepare(db, item)
        db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO soul_root VALUES(?,?,?,?)", ("synthetic", "S", 0,
                  b'{"active":"B0","branches":{},"retired":false,"revision":0}'))
        os._exit(42)
    if hook == "anchor_pending":
        item = record("CREATE", "fault-anchor-pending")
        prepared = prepare(db, item)
        assert cas(db, operation="CREATE", expected_revision=None, expected_source=None,
                   target="B0", record_hash=prepared) == "COMMITTED"
        assert root_value(db) is not None
        os._exit(42)
    if hook == "ack_lost":
        item = record("CREATE", "lost-ack-fresh")
        prepared = prepare(db, item)
        assert cas(db, operation="CREATE", expected_revision=None, expected_source=None,
                   target="B0", record_hash=prepared) == "COMMITTED"
        os._exit(42)  # Commit occurred; caller receives no response.
    raise ValueError(hook)
