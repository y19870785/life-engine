import base64
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from life_engine.config import defaults, load
from life_engine.install import apply_plan, build_plan, inspect_host, rollback
from life_engine.setup import guide, main


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.host = Path(self.temp.name) / "existing agent"
        self.host.mkdir()
        self.soul = b"\xef\xbb\xbfName: Morgan\r\nUse a formal tone. Respect existing rules.\r\n"
        (self.host / "SOUL.md").write_bytes(self.soul)
        self.config = b"model: custom\nunknown_setting: preserve-this\n"
        (self.host / "config.yaml").write_bytes(self.config)
        (self.host / ".env").write_text("TEST_TOKEN=local-only-sentinel", encoding="utf-8")
        self.cfg = defaults("morgan")
        self.cfg["integration"].update({"adapter": "hermes", "host_home": str(self.host)})

    def tearDown(self):
        self.temp.cleanup()

    def install(self, append=False):
        plan = build_plan(ROOT, self.cfg, append)
        result = apply_plan(plan)
        return plan, result

    def test_readonly_detection_does_not_expose_credentials(self):
        info = inspect_host(self.host, "hermes")
        self.assertEqual(info["name_suggestion"], "Morgan")
        self.assertTrue(info["credentials_present"])
        self.assertNotIn("local-only-sentinel", json.dumps(info))
        self.assertFalse((self.host / "life-engine").exists())

    def test_preview_changes_nothing(self):
        before = {str(p): p.read_bytes() for p in self.host.iterdir()}
        plan = build_plan(ROOT, self.cfg, True)
        self.assertGreater(len(plan["writes"]), 3)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.host.iterdir()})

    def test_sidecar_preserves_soul_config_env(self):
        self.install()
        self.assertEqual((self.host / "SOUL.md").read_bytes(), self.soul)
        self.assertEqual((self.host / "config.yaml").read_bytes(), self.config)
        self.assertEqual((self.host / ".env").read_text(), "TEST_TOKEN=local-only-sentinel")

    def test_appended_hook_preserves_original_bytes_and_rolls_back(self):
        _, result = self.install(True)
        self.assertTrue((self.host / "SOUL.md").read_bytes().startswith(self.soul))
        rollback(result["journal"])
        self.assertEqual((self.host / "SOUL.md").read_bytes(), self.soul)
        self.assertFalse((self.host / "skills" / "life-engine-morgan" / "SKILL.md").exists())

    def test_repeated_setup_is_idempotent(self):
        self.install(True)
        self.cfg, _ = load(self.host / "life-engine", "morgan")
        second = build_plan(ROOT, self.cfg, True)
        self.assertEqual(second["writes"], [])

    def test_reconfiguration_retains_manual_agent_settings(self):
        self.install()
        cfg_path = self.host / "life-engine" / "agents" / "morgan" / "agent.json"
        current = json.loads(cfg_path.read_text())
        current["social"]["recent_chat_minutes"] = 121
        cfg_path.write_text(json.dumps(current))
        # Guide preserves current values when accepting defaults.
        answers = iter(["", "", "", "", "", "", "", ""])
        result, _, _ = guide(self.host, "hermes", lambda _: next(answers), lambda _: None)
        self.assertEqual(result["social"]["recent_chat_minutes"], 121)

    def test_changed_soul_after_preview_aborts_before_writes(self):
        plan = build_plan(ROOT, self.cfg, True)
        (self.host / "SOUL.md").write_bytes(self.soul + b"New user rule.\r\n")
        with self.assertRaisesRegex(ValueError, "Source changed"):
            apply_plan(plan)
        self.assertFalse((self.host / "life-engine").exists())

    def test_existing_skill_collision_is_not_overwritten(self):
        collision = self.host / "skills" / "life-engine-morgan" / "SKILL.md"
        collision.parent.mkdir(parents=True)
        collision.write_text("User-owned content")
        with self.assertRaisesRegex(ValueError, "collision"):
            build_plan(ROOT, self.cfg)
        self.assertEqual(collision.read_text(), "User-owned content")

    def test_tampered_managed_file_needs_review(self):
        self.install()
        path = self.host / "life-engine" / "life.py"
        path.write_text("User edit")
        with self.assertRaisesRegex(ValueError, "edited"):
            build_plan(ROOT, self.cfg)

    def test_rollback_refuses_to_erase_later_user_edits(self):
        _, result = self.install(True)
        installed = (self.host / "SOUL.md").read_bytes()
        (self.host / "SOUL.md").write_bytes(installed + b"Added after install")
        with self.assertRaisesRegex(ValueError, "edited"):
            rollback(result["journal"])
        self.assertTrue((self.host / "SOUL.md").read_bytes().endswith(b"Added after install"))

    def test_fail_mid_apply_restores_written_files(self):
        plan = build_plan(ROOT, self.cfg, True)
        import life_engine.install as installer
        original = installer.atomic_write
        def failing(path, content, mode=0o600):
            if str(path).endswith("INTEGRATION.md"):
                raise OSError("Injected disk failure")
            return original(path, content, mode)
        with patch.object(installer, "atomic_write", failing):
            with self.assertRaises(OSError):
                apply_plan(plan)
        self.assertEqual((self.host / "SOUL.md").read_bytes(), self.soul)
        self.assertFalse((self.host / "life-engine" / "life.py").exists())

    def test_installed_skill_launcher_binds_host_independent_of_environment(self):
        self.install()
        launcher = self.host / "skills" / "life-engine-morgan" / "run.py"
        result = subprocess.run([sys.executable, str(launcher), "status"], cwd=self.temp.name,
                                env={**os.environ, "HERMES_HOME": "/unrelated"},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["agent_id"], "morgan")

    def test_cli_guided_preview_and_apply(self):
        answers = Path(self.temp.name) / "answers.json"
        answers.write_text(json.dumps({"agent_id": "morgan", "display_name": "Morgan"}))
        out = Path(self.temp.name) / "plan.json"
        code = main(ROOT, ["--home", str(self.host), "--adapter", "hermes",
                          "--answers", str(answers), "--out", str(out)], output=lambda _: None)
        self.assertEqual(code, 0)
        self.assertFalse((self.host / "life-engine").exists())
        code = main(ROOT, ["--apply-plan", str(out)], output=lambda _: None)
        self.assertEqual(code, 0)
        self.assertTrue((self.host / "life-engine" / "agents" / "morgan" / "agent.json").exists())

    def test_second_agent_cannot_bind_same_persona(self):
        self.install()
        other = copy.deepcopy(self.cfg)
        other["agent_id"] = "other"
        with self.assertRaisesRegex(ValueError, "separate"):
            build_plan(ROOT, other)

    @unittest.skipUnless(hasattr(os, "symlink") and os.name != "nt", "symlink test on Unix")
    def test_symlink_soul_is_not_followed(self):
        (self.host / "SOUL.md").unlink()
        real = Path(self.temp.name) / "elsewhere.md"
        real.write_text("Other persona")
        (self.host / "SOUL.md").symlink_to(real)
        with self.assertRaisesRegex(ValueError, "symlink"):
            build_plan(ROOT, self.cfg, True)
        self.assertEqual(real.read_text(), "Other persona")
