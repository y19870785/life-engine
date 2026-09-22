from contextlib import contextmanager
import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS days (day TEXT PRIMARY KEY, plan TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY, day TEXT NOT NULL, slot TEXT NOT NULL, at REAL NOT NULL,
    status TEXT NOT NULL, payload TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '',
    evidence TEXT NOT NULL DEFAULT '', UNIQUE(day, slot));
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY, at REAL NOT NULL, summary TEXT NOT NULL, dedupe TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY, at REAL NOT NULL, kind TEXT NOT NULL, summary TEXT NOT NULL,
    provenance TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS loops (
    id INTEGER PRIMARY KEY, at REAL NOT NULL, due REAL, topic TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open', resolution TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS photos (
    id TEXT PRIMARY KEY, contact_id TEXT UNIQUE, day TEXT NOT NULL,
    at REAL NOT NULL, status TEXT NOT NULL, prompt_id TEXT, path TEXT, prompt TEXT,
    FOREIGN KEY(contact_id) REFERENCES contacts(id));
"""


class Store:
    def __init__(self, path, agent_id):
        from .world_schema import DATA_SCHEMA, create_world_schema, validate_schema
        self.path = Path(path)
        existed = self.path.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.tx() as db:
            if existed:
                validate_schema(db, agent_id=agent_id)
            else:
                for query in SCHEMA.split(";"):
                    if query.strip():
                        db.execute(query)
                db.execute("INSERT INTO meta VALUES ('agent_id',?)", (agent_id,))
                db.execute("INSERT INTO meta VALUES ('schema_version',?)", (str(DATA_SCHEMA),))
                create_world_schema(db)
        self.agent_id = agent_id

    @contextmanager
    def tx(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def observe(self, at, summary, dedupe=None):
        with self.tx() as db:
            db.execute("INSERT OR IGNORE INTO observations(at,summary,dedupe) VALUES(?,?,?)",
                       (at, summary, dedupe))

    def remember(self, at, kind, summary, provenance):
        with self.tx() as db:
            return db.execute("INSERT INTO memories(at,kind,summary,provenance) VALUES(?,?,?,?)",
                              (at, kind, summary, provenance)).lastrowid

    def loop_add(self, at, topic, due=None):
        with self.tx() as db:
            return db.execute("INSERT INTO loops(at,due,topic) VALUES(?,?,?)",
                              (at, due, topic)).lastrowid

    def loop_close(self, loop_id, resolution):
        with self.tx() as db:
            count = db.execute("UPDATE loops SET status='resolved',resolution=? WHERE id=? AND status='open'",
                               (resolution, loop_id)).rowcount
            if count != 1:
                raise ValueError("Open loop not found")

    def prepare(self, contact_id, summary):
        with self.tx() as db:
            row = db.execute("SELECT * FROM contacts WHERE id=?", (contact_id,)).fetchone()
            if not row:
                raise ValueError("Unknown contact")
            if row["status"] == "prepared" and row["summary"] == summary:
                return
            if row["status"] != "claimed":
                raise ValueError("Contact is no longer claimable for preparation")
            db.execute("UPDATE contacts SET status='prepared',summary=? WHERE id=?", (summary, contact_id))

    def acknowledge(self, contact_id, outcome, evidence):
        if outcome not in ("delivered", "failed", "unknown") or not evidence.strip():
            raise ValueError("A delivery outcome and actual receipt/error evidence are required")
        with self.tx() as db:
            row = db.execute("SELECT status,evidence FROM contacts WHERE id=?", (contact_id,)).fetchone()
            if not row:
                raise ValueError("Unknown contact")
            if row["status"] == outcome and row["evidence"] == evidence:
                return
            if row["status"] not in ("prepared", "unknown"):
                raise ValueError("Contact must be prepared; delivery acknowledgements cannot overwrite a final result")
            db.execute("UPDATE contacts SET status=?,evidence=? WHERE id=?", (outcome, evidence, contact_id))

    def context(self, db):
        return {
            "recent_contacts": [dict(r) for r in db.execute(
                "SELECT id,at,status,summary FROM contacts ORDER BY at DESC LIMIT 5")],
            "recent_user_messages": [dict(r) for r in db.execute(
                "SELECT at,summary FROM observations ORDER BY at DESC LIMIT 5")],
            "memories": [dict(r) for r in db.execute("SELECT * FROM memories ORDER BY id DESC LIMIT 8")],
            "open_loops": [dict(r) for r in db.execute(
                "SELECT * FROM loops WHERE status='open' ORDER BY COALESCE(due,9e12),id LIMIT 8")],
        }

    def pause(self, paused):
        with self.tx() as db:
            db.execute("INSERT INTO meta VALUES('paused',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                       ("true" if paused else "false",))
