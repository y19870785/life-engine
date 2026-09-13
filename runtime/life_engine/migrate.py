import json
import sqlite3
from datetime import datetime
from pathlib import Path


def migrate_v01(source, store):
    """Snapshot a legacy SQLite database and import history once, never mutate the source."""
    source = Path(source).expanduser().resolve()
    if not source.is_file() or source == store.path.resolve():
        raise ValueError("Select an existing v0.1 database, different from the target")
    uri = source.as_uri() + "?mode=ro"
    marker = "legacy-v01:" + str(source)
    with store.tx() as db:
        if db.execute("SELECT 1 FROM meta WHERE key=?", (marker,)).fetchone():
            return {"imported": False, "reason": "already_imported"}
    legacy = sqlite3.connect(uri, uri=True)
    legacy.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in legacy.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"events", "memories", "open_loops", "daily_states"}.issubset(tables):
            raise ValueError("Not a recognized v0.1 database")
        snapshot = store.path.parent / "legacy-v01.snapshot.db"
        if snapshot.exists():
            raise ValueError("Legacy snapshot already exists; inspect the previous migration")
        copy = sqlite3.connect(snapshot)
        try:
            legacy.backup(copy)
        finally:
            copy.close()
    finally:
        legacy.close()
    old = sqlite3.connect(snapshot)
    old.row_factory = sqlite3.Row
    counts = {"observations": 0, "memories": 0, "loops": 0, "contact_attempts": 0}

    def timestamp(value):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError("Legacy timestamp has no timezone; manual migration required")
        return parsed.timestamp()

    try:
        with store.tx() as db:
            if db.execute("SELECT 1 FROM meta WHERE key=?", (marker,)).fetchone():
                return {"imported": False, "reason": "already_imported"}
            for r in old.execute("SELECT * FROM events ORDER BY id"):
                at = timestamp(r["occurred_at"])
                if r["event_type"] == "inbound_message":
                    db.execute("INSERT INTO observations(at,summary,dedupe) VALUES(?,?,?)",
                               (at, r["summary"], f"legacy-v01:{r['id']}"))
                    counts["observations"] += 1
                elif r["event_type"] == "outbound_contact":
                    date = r["occurred_at"][:10]
                    db.execute("INSERT INTO contacts(id,day,slot,at,status,payload,summary,evidence) VALUES(?,?,?,?,?,?,?,?)",
                               (f"legacy-{r['id']}", date, f"legacy-{r['id']}", at, "unknown",
                                r["payload_json"], r["summary"], "v0.1 has no delivery receipt"))
                    counts["contact_attempts"] += 1
            for r in old.execute("SELECT * FROM memories ORDER BY id"):
                db.execute("INSERT INTO memories(at,kind,summary,provenance) VALUES(?,?,?,?)",
                           (timestamp(r["created_at"]), r["memory_type"], r["summary"], "legacy:" + r["source"]))
                counts["memories"] += 1
            for r in old.execute("SELECT * FROM open_loops ORDER BY id"):
                due = timestamp(r["due_at"]) if r["due_at"] else None
                db.execute("INSERT INTO loops(at,due,topic,status,resolution) VALUES(?,?,?,?,?)",
                           (timestamp(r["created_at"]), due, r["topic"], r["status"], r["resolution"] or ""))
                counts["loops"] += 1
            db.execute("INSERT INTO meta VALUES(?,?)", (marker, json.dumps(counts)))
    finally:
        old.close()
    return {"imported": True, "counts": counts, "snapshot": str(snapshot),
            "note": "Old daily plans/photos remain in the read-only migration snapshot; new settings take effect today."}
