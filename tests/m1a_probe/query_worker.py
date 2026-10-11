"""Fresh-process lookup of one synthetic transition after lost ACK."""
import json
from pathlib import Path
import sys

from isolation import fixture_path
from primitive import connect, digest, record, root_value


path = fixture_path(Path(sys.argv[1]))
transition_id = sys.argv[2]
with connect(path) as db:
    row = db.execute("SELECT hash,bytes,payload_hash FROM record WHERE transition_id=?", (transition_id,)).fetchone()
    root = root_value(db)
    if row is None or root is None:
        answer = {"outcome": "NOT_COMMITTED", "transition_id": transition_id}
    else:
        item = json.loads(row["bytes"])
        expected = record("CREATE", transition_id)
        linked = root["branches"]["B0"]["record"] == row["hash"]
        exact = digest(row["bytes"]) == row["hash"] and item == expected
        answer = {"outcome": "COMMITTED" if linked and exact else "UNKNOWN",
                  "transition_id": transition_id, "record_hash": row["hash"],
                  "payload_hash": row["payload_hash"], "root_revision": root["revision"],
                  "record_count": db.execute("SELECT count(*) FROM record").fetchone()[0]}
print(json.dumps(answer, sort_keys=True))
