"""Fresh-profile scope, capability-only inheritance and optimistic hash guards."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine import hermes_profile_setup as hs


class ProfileSetupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.source = self.base / 'source'; self.source.mkdir()
        self.target = self.base / 'profiles/new-role'; self.target.mkdir(parents=True)
        (self.source / 'skills').mkdir()
        self.source_cfg = {'model': {'api_key': 'synthetic-source-secret', 'default': 'source-model'},
            'mcp_servers': {'private': {'command': 'never-copy'}}, 'platform_toolsets': {'cli': ['terminal', 'skills']},
            'skills': {'disabled': ['source-hidden']}, 'plugins': {'enabled': ['source-agent-plugin']}}
        self.target_cfg = {'model': {'default': 'target-model', 'api_key': 'synthetic-target-secret'},
            'agent': {'max_iterations': 7}, 'platform_toolsets': {'telegram': []},
            'tools': {'tool_search': {'defer': ['browser_vault']}}}
        self.write(self.source, self.source_cfg); self.write(self.target, self.target_cfg)
        self.yaml = types.SimpleNamespace(safe_load=json.loads,
            safe_dump=lambda value, **kwargs: json.dumps(value, ensure_ascii=False))
        patcher = patch.dict(sys.modules, {'hermes_yaml': self.yaml}); patcher.start(); self.addCleanup(patcher.stop)

    @staticmethod
    def write(home, value):
        (home / 'config.yaml').write_text(json.dumps(value), encoding='utf-8')

    def test_capability_inheritance_preserves_identity_and_source(self):
        source_before = (self.source / 'config.yaml').read_bytes()
        soul = self.target / 'SOUL.md'; soul.write_text('fresh Host soul', encoding='utf-8')
        plan = hs.prepare(self.source, self.target)
        self.assertNotIn('synthetic-source-secret', json.dumps(plan))
        self.assertNotIn('synthetic-target-secret', json.dumps(plan))
        self.assertFalse((self.target / hs.MARKER).exists())
        receipt = hs.apply(plan)
        result = json.loads((self.target / 'config.yaml').read_bytes())
        self.assertEqual(result['model'], self.target_cfg['model'])
        self.assertEqual(result['agent'], self.target_cfg['agent'])
        self.assertEqual(result['platform_toolsets']['telegram'], [])
        self.assertEqual(result['platform_toolsets']['cli'], ['terminal', 'skills'])
        self.assertEqual(result['tools']['tool_search'], {'enabled': 'off', 'defer': ['browser_vault']})
        self.assertEqual(result['plugins']['enabled'], ['life-engine-character-card'])
        self.assertIn(str(self.source / 'skills'), result['skills']['external_dirs'])
        self.assertIn('source-hidden', result['skills']['disabled'])
        self.assertNotIn('mcp_servers', result)
        self.assertEqual((self.source / 'config.yaml').read_bytes(), source_before)
        self.assertEqual(soul.read_text(), 'fresh Host soul')
        hs.restore(receipt)
        self.assertEqual(json.loads((self.target / 'config.yaml').read_bytes()), self.target_cfg)

    def test_source_or_target_config_drift_refuses_write(self):
        plan = hs.prepare(self.source, self.target)
        self.source_cfg['model']['default'] = 'changed'; self.write(self.source, self.source_cfg)
        with self.assertRaisesRegex(ValueError, 'SOURCE_CONFIG_CHANGED'): hs.apply(plan)
        self.assertEqual(json.loads((self.target / 'config.yaml').read_bytes()), self.target_cfg)
        plan = hs.prepare(self.source, self.target)
        self.target_cfg['agent']['max_iterations'] = 8; self.write(self.target, self.target_cfg)
        with self.assertRaisesRegex(ValueError, 'TARGET_CONFIG_CHANGED'): hs.apply(plan)

    def test_plan_tamper_and_rollback_drift_refused(self):
        plan = hs.prepare(self.source, self.target)
        bad = deepcopy(plan); bad['changes']['cli_toolsets'] = ['all']
        with self.assertRaisesRegex(ValueError, 'SETUP_PLAN_CHANGED'): hs.apply(bad)
        receipt = hs.apply(plan)
        (self.target / 'config.yaml').write_text('user modified config', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'TARGET_CONFIG_CHANGED'): hs.restore(receipt)
        self.assertEqual((self.target / 'config.yaml').read_text(), 'user modified config')

    def test_existing_role_and_history_are_not_reconfigured(self):
        for name in ('state.db', 'MEMORY.md', '.life-engine-continuity.json'):
            file = self.target / name; file.write_text('not inspected', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'TARGET_NOT_FRESH'): hs.prepare(self.source, self.target)
            file.unlink()
        plugin = self.target / 'plugins/other'; plugin.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'TARGET_NOT_FRESH'): hs.prepare(self.source, self.target)

    def test_default_profile_and_missing_host_yaml_refused(self):
        with self.assertRaisesRegex(ValueError, 'NAMED_PROFILE_REQUIRED'): hs.prepare(self.source, self.source)
        with patch.dict(sys.modules, {'hermes_yaml': None}):
            with self.assertRaisesRegex(ValueError, 'HOST_YAML_UNAVAILABLE'): hs.prepare(self.source, self.target)
        self.assertFalse((self.target / hs.MARKER).exists())

    def test_shared_create_and_external_dirs_and_explicit_empty_tools(self):
        extra = self.source / 'shared'; extra.mkdir()
        create = self.source / 'created'; create.mkdir()
        self.source_cfg['skills'].update(external_dirs='shared', create_dir='created')
        self.source_cfg['platform_toolsets']['cli'] = []
        self.write(self.source, self.source_cfg)
        plan = hs.prepare(self.source, self.target, disabled_skills=['specific-role'])
        self.assertEqual(plan['changes']['cli_toolsets'], [])
        self.assertIn(str(extra), plan['changes']['external_skill_dirs'])
        self.assertIn(str(create), plan['changes']['external_skill_dirs'])
        self.assertEqual(plan['changes']['disabled_skills'], ['source-hidden', 'specific-role'])

    def test_prepared_receipt_recovers_before_or_after_config_write(self):
        for point in ('before_config', 'after_config'):
            with self.subTest(point=point):
                plan = hs.prepare(self.source, self.target)
                before = (self.target/'config.yaml').read_bytes()
                original = hs.atomic
                def interrupted(path, payload):
                    if ((point == 'before_config' and path == self.target/'config.yaml') or
                        (point == 'after_config' and path == self.target/hs.MARKER
                         and json.loads(payload).get('state') == 'APPLIED')):
                        raise OSError('synthetic config checkpoint interruption')
                    return original(path, payload)
                with patch.object(hs, 'atomic', side_effect=interrupted):
                    with self.assertRaisesRegex(OSError, 'checkpoint interruption'):
                        hs.apply(plan)
                receipt = json.loads((self.target/hs.MARKER).read_bytes())
                self.assertEqual(receipt['state'], 'PREPARED')
                hs.restore(receipt)
                self.assertEqual((self.target/'config.yaml').read_bytes(), before)
                (self.target/hs.MARKER).unlink()


if __name__ == '__main__': unittest.main()
