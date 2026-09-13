import base64
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from life_engine.config import defaults, now_in
from life_engine.engine import Engine
from life_engine.store import Store
from life_engine.photos import photo, inspect_workflow
from life_engine.migrate import migrate_v01

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")
GRAPH = {
    "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "{{POSITIVE_PROMPT}}"}},
    "2": {"class_type": "KSampler", "inputs": {"seed": "{{SEED}}"}},
    "3": {"class_type": "SaveImage", "inputs": {"images": ["2", 0]}},
}


class PhotosTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / "agent with spaces"
        self.home.mkdir()
        (self.home / "workflow.json").write_text(json.dumps(GRAPH))
        self.cfg = defaults("pho")
        self.cfg["photos"].update({"enabled": True, "workflow": "workflow.json",
                                  "identity_prompt": "the agent's existing adult character"})
        self.cfg["mode"] = "companion"
        self.store = Store(self.home / "state.db", "pho")
        self.engine = Engine(self.cfg, self.store)
        self.now = now_in(self.cfg, "2026-09-13T10:00:00+08:00")

    def tearDown(self):
        self.temp.cleanup()

    def test_dry_run_patches_types_without_network_or_budget(self):
        result = photo(self.cfg, self.home, self.store, self.engine, self.now, dry_run=True)
        self.assertIsInstance(result["workflow"]["2"]["inputs"]["seed"], int)
        self.assertIn("existing adult character", result["prompt"])
        with self.store.tx() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM photos").fetchone()[0], 0)

    def test_http_pipeline_and_reuse_without_duplicate_queue(self):
        posts = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_POST(self):
                posts.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"prompt_id":"test-prompt"}')
            def do_GET(self):
                if self.path.startswith("/history/"):
                    payload = json.dumps({"test-prompt": {"outputs": {"3": {"images": [
                        {"filename": "test.png", "type": "output", "subfolder": ""}
                    ]}}, "status": {"status_str": "success"}}}).encode()
                else:
                    payload = PNG
                self.send_response(200)
                self.end_headers()
                self.wfile.write(payload)
        self.cfg["social"].update({"enabled": True, "windows": [["10:00", "10:01"]]})
        contact = self.engine.wake(self.now)["contact_id"]
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.cfg["photos"]["base_url"] = f"http://127.0.0.1:{server.server_port}"
            result = photo(self.cfg, self.home, self.store, self.engine, self.now, contact)
            again = photo(self.cfg, self.home, self.store, self.engine, self.now, contact)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        self.assertEqual(len(posts), 1)
        self.assertEqual(Path(result["path"]).read_bytes(), PNG)
        self.assertEqual(result["media"], again["media"])
        self.assertTrue(result["media"].startswith('MEDIA:"'))

    def test_ambiguous_photo_attempt_not_requeued(self):
        self.cfg["social"].update({"enabled": True, "windows": [["10:00", "10:01"]]})
        contact = self.engine.wake(self.now)["contact_id"]
        class Client:
            def generate(self, graph, timeout, queued):
                queued("accepted-but-disconnected")
                raise TimeoutError()
        with self.assertRaises(TimeoutError):
            photo(self.cfg, self.home, self.store, self.engine, self.now, contact, client=Client())
        with self.assertRaisesRegex(ValueError, "already attempted"):
            photo(self.cfg, self.home, self.store, self.engine, self.now, contact, client=Client())

    def test_ui_graph_rejected_before_network(self):
        (self.home / "workflow.json").write_text('{"nodes":[]}')
        with self.assertRaisesRegex(ValueError, "API graph"):
            inspect_workflow(self.home / "workflow.json")

    def test_migration_preserves_source_and_is_idempotent(self):
        source = self.home / "v01.db"
        with sqlite3.connect(source) as db:
            db.executescript("""
                CREATE TABLE events(id INTEGER PRIMARY KEY,occurred_at TEXT,event_type TEXT,status TEXT,summary TEXT,payload_json TEXT);
                CREATE TABLE memories(id INTEGER PRIMARY KEY,created_at TEXT,memory_type TEXT,summary TEXT,source TEXT);
                CREATE TABLE open_loops(id INTEGER PRIMARY KEY,created_at TEXT,due_at TEXT,topic TEXT,status TEXT,resolution TEXT);
                CREATE TABLE daily_states(day TEXT,plan_json TEXT);
                INSERT INTO events VALUES(1,'2026-09-12T21:00:00+08:00','outbound_contact','sent','Evening greeting','{}');
                INSERT INTO memories VALUES(1,'2026-09-12T21:00:00+08:00','preference','Keep old preference','conversation');
            """)
        before = source.read_bytes()
        result = migrate_v01(source, self.store)
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(result["counts"]["memories"], 1)
        self.assertEqual(migrate_v01(source, self.store)["reason"], "already_imported")
        with self.store.tx() as db:
            self.assertEqual(db.execute("SELECT status FROM contacts").fetchone()[0], "unknown")
