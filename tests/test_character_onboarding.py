"""Story entry preserves author openings and isolates new installations."""
import json
import io
from contextlib import redirect_stdout
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine import character_onboarding as onboarding, hermes_card_import as ci

PACKAGE = Path(__file__).resolve().parents[1]


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.source = self.base / 'card.json'
        self.source.write_bytes(ci.json_bytes({'name': '岚', 'description': 'SECRET_AUTHOR_DESCRIPTION',
            'scenario': '{{user}}是岚的邻居。', 'first_mes': '进来避雨吧，{{user}}。',
            'alternate_greetings': ['{{user}}，一起去码头吗？'],
            'character_book': {'entries': [{'keys': ['码头'], 'content': 'SECRET_WORLDBOOK'}]}}))
        self.plan = self.base / 'plan.json'

    def prepared(self, opening=1):
        view = onboarding.inspect(self.source)
        return onboarding.prepare(self.source, self.plan, opening,
            acknowledged=[i['id'] for i in view['compatibility']])

    def test_intro_all_openings_and_optional_details(self):
        raw = self.source.read_bytes()
        view = onboarding.inspect(self.source, user_name='旅人')
        self.assertIn('邻居', view['scenario'])
        self.assertEqual([i['index'] for i in view['openings']], [0, 1])
        self.assertEqual(view['openings'][1]['text'], '旅人，一起去码头吗？')
        self.assertNotIn('SECRET_', json.dumps(view))
        full = onboarding.inspect(self.source, details=True)
        self.assertEqual(full['author_character_description'], 'SECRET_AUTHOR_DESCRIPTION')
        self.assertEqual(self.source.read_bytes(), raw)

    def test_selection_preserves_author_card_and_requires_explicit_compatibility_review(self):
        with self.assertRaisesRegex(ValueError, 'COMPATIBILITY_REVIEW_REQUIRED'):
            onboarding.prepare(self.source, self.plan, 1)
        self.assertFalse(self.plan.exists())
        result = self.prepared()
        plan = json.loads(self.plan.read_bytes())
        self.assertEqual(plan['options']['greeting_index'], 1)
        self.assertEqual(plan['review_only']['original'], json.loads(self.source.read_bytes()))
        self.assertIn('码头', result['opening'])
        with self.assertRaises(FileExistsError):
            self.prepared()
        with self.assertRaises(ValueError):
            onboarding.prepare(self.source, self.base/'bad.json', 20)

    def test_install_pipeline_creates_world_and_capabilities_without_touching_source(self):
        prepared = self.prepared()
        home = self.base / 'profiles/trial'; home.mkdir(parents=True)
        source_home = self.base / 'main'; source_home.mkdir()
        original = b'main identity and private state'; (source_home/'SOUL.md').write_bytes(original)
        host = self.base / 'host'
        for name in onboarding.continuity.HOST_FILES:
            target = host/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_text('host source')
        names = self.base/'tools.json'; names.write_text('["terminal","skill_view"]')
        fake = types.SimpleNamespace(configure_host=lambda *a: {}, prepare=lambda *a: {'prepared': True},
                                     apply=lambda *a: {'config_after_sha256': 'synthetic'})
        root = self.base/'world'
        with patch.dict(sys.modules, {'life_engine.hermes_profile_setup': fake}):
            result = onboarding.install(self.plan, prepared['sha256'], home, source_home,
                                        root, host, names, PACKAGE)
        self.assertEqual(result['state'], 'INSTALLED')
        self.assertTrue(result['world'].startswith('world:'))
        self.assertEqual((source_home/'SOUL.md').read_bytes(), original)
        self.assertEqual(json.loads((home/'.life-engine-character-capabilities.json').read_bytes())['allowed_tools'],
                         ['skill_view','terminal'])
        self.assertTrue(json.loads((home/'.life-engine-continuity.json').read_bytes())['enabled'])
        self.assertFalse((home/'.life-engine-onboarding.lock').exists())
        with self.assertRaisesRegex(ValueError, 'NEW_SEPARATE_WORLD_ROOT_REQUIRED'):
            onboarding.install(self.plan, prepared['sha256'], home, source_home, root, host, names, PACKAGE)

    def test_failed_configuration_records_stage_and_refuses_implicit_retry(self):
        prepared = self.prepared()
        home = self.base/'profiles/new'; home.mkdir(parents=True)
        host = self.base/'host'
        for name in onboarding.continuity.HOST_FILES:
            target=host/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_text('source')
        names=self.base/'tools.json'; names.write_text('["terminal"]')
        def fail(*args):
            raise OSError('synthetic config failure')
        fake=types.SimpleNamespace(configure_host=lambda *a: {}, prepare=lambda *a: {}, apply=fail)
        with patch.dict(sys.modules, {'life_engine.hermes_profile_setup': fake}):
            with self.assertRaisesRegex(OSError, 'synthetic config failure'):
                onboarding.install(self.plan, prepared['sha256'], home, self.base/'source',
                                   self.base/'world', host, names, PACKAGE)
            receipt=json.loads((home/'.life-engine-onboarding.json').read_bytes())
            self.assertEqual((receipt['state'],receipt['stage']), ('FAILED_PARTIAL','CONFIG'))
            with self.assertRaisesRegex(ValueError, 'ONBOARDING_ALREADY_STARTED'):
                onboarding.install(self.plan, prepared['sha256'], home, self.base/'source',
                                   self.base/'world', host, names, PACKAGE)
        self.assertFalse((home/'.life-engine-onboarding.lock').exists())

    def test_tool_manifest_recheck_uses_the_same_bytes_as_install(self):
        home = self.base/'profiles/tool-check'; home.mkdir(parents=True)
        card = home/'plugins/life-engine-character-card/card.json'; card.parent.mkdir(parents=True)
        card.write_text('{}')
        names = self.base/'tools.json'; names.write_text('["terminal"]')
        expected = ci.digest(names.read_bytes())
        names.write_text('["terminal","write_file"]')
        with self.assertRaisesRegex(ValueError, 'TOOLS_CHANGED'):
            onboarding.configure(home, names, ci.digest(card.read_bytes()), expected_tools_sha=expected)
        self.assertFalse((home/'.life-engine-character-capabilities.json').exists())

    def test_recovery_cli_binds_receipt_to_the_requested_profile(self):
        a=self.base/'profiles/a'; a.mkdir(parents=True)
        b=self.base/'profiles/b'; b.mkdir()
        fake=types.SimpleNamespace(MARKER='.life-engine-profile-setup.json',restore=Mock())
        marker=a/fake.MARKER
        marker.write_bytes(ci.json_bytes({'target_home':str(b),'state':'APPLIED'}))
        with patch.dict(sys.modules, {'life_engine.hermes_profile_setup':fake}), redirect_stdout(io.StringIO()):
            self.assertEqual(onboarding.main(['recover-config','--profile-home',str(a)]),1)
            fake.restore.assert_not_called()
            marker.write_bytes(ci.json_bytes({'target_home':str(a),'state':'APPLIED'}))
            self.assertEqual(onboarding.main(['recover-config','--profile-home',str(a)]),0)
            fake.restore.assert_called_once()


if __name__ == '__main__': unittest.main()
