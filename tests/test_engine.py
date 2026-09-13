import copy
import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from life_engine.config import defaults, now_in, validate
from life_engine.engine import Engine
from life_engine.store import Store
from life_engine.cli import simulate


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "life.db"
        self.cfg = defaults("morgan")
        self.cfg["mode"] = "companion"
        self.cfg["social"].update({"enabled": True, "daily_min": 1, "daily_max": 2,
                                  "windows": [["10:00", "10:01"]], "quiet_hours": ["23:00", "08:00"]})
        self.store = Store(self.path, "morgan")
        self.engine = Engine(self.cfg, self.store)
        self.now = now_in(self.cfg, "2026-09-13T10:00:00+08:00")

    def tearDown(self):
        self.temp.cleanup()

    def test_simultaneous_wake_only_claims_once(self):
        def wake(_):
            return Engine(self.cfg, Store(self.path, "morgan")).wake(self.now)
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(wake, range(5)))
        self.assertEqual(sum(r["action"] == "contact" for r in results), 1)

    def test_soul_identity_not_injected_into_core(self):
        result = self.engine.status(self.now)
        self.assertEqual(result["moment"]["visual"], {})
        self.assertNotIn("activity", result["moment"])

    def test_assistant_contacts_only_for_recorded_due_loop(self):
        self.cfg["mode"] = "assistant"
        self.assertEqual(self.engine.wake(self.now)["reason"], "no_due_followup")
        self.store.loop_add(self.now.timestamp() - 100, "Follow up with owner", self.now.timestamp() - 1)
        self.assertEqual(self.engine.wake(self.now)["action"], "contact")

    def test_preview_never_consumes_contact_budget(self):
        self.assertEqual(self.engine.wake(self.now, preview=True)["action"], "contact")
        self.assertEqual(self.engine.wake(self.now)["action"], "contact")

    def test_simulation_leaves_live_database_identical(self):
        before = self.path.read_bytes()
        result = simulate(self.cfg, "2026-09-13")
        self.assertTrue(result["simulation"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_recent_owner_contact_and_quiet_hours_suppress(self):
        self.store.observe(self.now.timestamp() - 60, "Owner just replied", "message-1")
        self.assertEqual(self.engine.wake(self.now)["reason"], "recent_conversation")
        self.assertEqual(self.engine.wake(now_in(self.cfg, "2026-09-14T00:30:00+08:00"))["reason"], "quiet_hours")

    def test_visual_state_is_stable_across_restarts(self):
        self.cfg["world"]["visual_options"] = {"outfit": ["blue", "black"], "hair": ["short", "long"]}
        a = self.engine.status(self.now)["moment"]["visual"]
        b = Engine(self.cfg, Store(self.path, "morgan")).status(self.now)["moment"]["visual"]
        self.assertEqual(a, b)

    def test_databases_reject_mismatched_agent_id(self):
        with self.assertRaisesRegex(ValueError, "different agent"):
            Store(self.path, "xiaoxue")

    def test_memory_cannot_cross_agent_stores(self):
        self.store.remember(self.now.timestamp(), "preference", "Morgan fact", "owner")
        other = Store(Path(self.temp.name) / "other.db", "other")
        with other.tx() as db:
            self.assertEqual(other.context(db)["memories"], [])

    def test_prepared_is_not_delivery_proof(self):
        contact = self.engine.wake(self.now)["contact_id"]
        self.store.prepare(contact, "Ready to greet")
        with self.store.tx() as db:
            self.assertEqual(db.execute("SELECT status FROM contacts WHERE id=?", (contact,)).fetchone()[0], "prepared")
        self.store.acknowledge(contact, "delivered", "mock platform receipt 123")
        with self.assertRaises(ValueError):
            self.store.acknowledge(contact, "failed", "contradictory receipt")

    def test_invalid_time_and_assistant_routine_rejected(self):
        self.cfg["social"]["quiet_hours"][0] = "26:00"
        with self.assertRaises(ValueError):
            validate(self.cfg)
        self.cfg["social"]["quiet_hours"][0] = "23:00"
        self.cfg["mode"] = "assistant"
        self.cfg["world"]["routine"] = [{"start": "09:00", "end": "10:00",
                                          "location": "cafe", "activity": "rest"}]
        with self.assertRaises(ValueError):
            validate(self.cfg)
