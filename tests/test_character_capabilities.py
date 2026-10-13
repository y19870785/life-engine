"""Owner permissions intersect offered Host tools without altering story identity."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine import hermes_card_import as ci, hermes_card_runtime as rt

PACKAGE = Path(__file__).resolve().parents[1]


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.home = Path(temp.name).resolve() / 'profiles/actor'; self.home.mkdir(parents=True)
        plan = rt.compile_plan({'name': '岚', 'scenario': '{{user}}是老朋友。'}, 'card-source')
        plan['options']['acknowledged'] = [i['id'] for i in plan['issues']]
        path = self.home.parent / 'plan.json'; path.write_bytes(ci.json_bytes(plan))
        ci.apply(path, self.home, ci.digest(path.read_bytes()))
        folder = self.home / 'plugins/life-engine-character-card'
        self.raw = (folder / 'card.json').read_bytes()
        spec = importlib.util.spec_from_file_location('capability_test_plugin', folder / '__init__.py',
                                                    submodule_search_locations=[str(folder)])
        self.module = importlib.util.module_from_spec(spec)
        self.modules = patch.dict(sys.modules, {'capability_test_plugin': self.module,
                   'hermes_constants': types.SimpleNamespace(get_hermes_home=lambda: self.home)})
        self.modules.start(); self.addCleanup(self.modules.stop)
        spec.loader.exec_module(self.module)
        self.kw = dict(session_id='s', turn_id='t', platform='cli')
        self.path = self.home / '.life-engine-character-capabilities.json'
        self.config = {'format': 'life-engine-character-capabilities-v1', 'enabled': True,
                      'profile': str(self.home), 'card_sha256': ci.digest(self.raw),
                      'allowed_tools': ['terminal', 'tts', 'not_offered']}
        self.request = {'messages': [{'role': 'user', 'content': '帮我拍照'}], 'tools': [
            {'type': 'function', 'function': {'name': name}} for name in ('terminal', 'tts', 'other')]}

    def write(self):
        self.path.write_bytes(ci.json_bytes(self.config))

    def test_owner_permission_intersects_offered_tools_and_preserves_card(self):
        self.write(); self.module.before(**self.kw)
        out = self.module.rewrite(request=self.request, **self.kw)['request']
        self.assertEqual([t['function']['name'] for t in out['tools']], ['terminal', 'tts'])
        self.assertIsNone(self.module.guard_tool(tool_name='terminal', **self.kw))
        for name in ('not_offered', 'other'):
            self.assertEqual(self.module.guard_tool(tool_name=name, **self.kw)['action'], 'block')
        self.assertEqual((self.home / 'plugins/life-engine-character-card/card.json').read_bytes(), self.raw)
        self.assertIn('老朋友', json.dumps(out, ensure_ascii=False))
        self.assertIn('实际操作是否成功必须以工具结果为准', json.dumps(out, ensure_ascii=False))
        twice = self.module.rewrite(request=out, **self.kw)['request']
        self.assertEqual(out, twice)
        out['tools'] = [t for t in out['tools'] if t['function']['name'] == 'tts']
        smaller = self.module.rewrite(request=out, **self.kw)['request']
        self.assertEqual(smaller['messages'], out['messages'])
        self.assertEqual(self.module.guard_tool(tool_name='terminal', **self.kw)['action'], 'block')

    def test_forced_tool_must_have_an_actual_filtered_host_schema(self):
        self.write(); self.module.before(**self.kw)
        self.request['tool_choice'] = {'type': 'function', 'function': {'name': 'not_offered'}}
        out = self.module.rewrite(request=self.request, **self.kw)['request']
        self.assertEqual(out['tool_choice'], 'auto')
        self.request['tool_choice']['function']['name'] = 'terminal'
        out = self.module.rewrite(request=self.request, **self.kw)['request']
        self.assertEqual(out['tool_choice']['function']['name'], 'terminal')

    def test_no_owner_permission_and_disabled_permission_keep_original_restriction(self):
        self.module.before(**self.kw)
        self.assertNotIn('tools', self.module.rewrite(request=self.request, **self.kw)['request'])
        self.config['enabled'] = False; self.write()
        self.assertNotIn('tools', self.module.rewrite(request=self.request, **self.kw)['request'])

    def test_permission_drift_and_wrong_profile_are_rejected(self):
        self.write(); self.module.before(**self.kw)
        self.module.rewrite(request=self.request, **self.kw)
        self.config['allowed_tools'].append('other'); self.write()
        self.assertEqual(self.module.guard_tool(tool_name='terminal', **self.kw)['action'], 'block')
        self.config['profile'] += '-other'; self.write()
        self.assertEqual(self.module.rewrite(request=self.request, **self.kw)['reason'], 'UNAVAILABLE')
        self.assertEqual(self.module.guard_tool(tool_name='terminal', **self.kw)['action'], 'block')

    def test_tools_require_current_request_and_do_not_leak_to_later_turn(self):
        self.write(); self.module.before(**self.kw)
        self.assertEqual(self.module.guard_tool(tool_name='terminal', **self.kw)['action'], 'block')
        self.module.rewrite(request=self.request, **self.kw)
        self.module.ended(**self.kw)
        next_turn = dict(self.kw, turn_id='next')
        self.module.before(**next_turn)
        self.assertEqual(self.module.guard_tool(tool_name='terminal', **next_turn)['action'], 'block')

    def test_management_configures_and_backs_up_without_rebinding_world(self):
        spec = importlib.util.spec_from_file_location('capability_management', PACKAGE / 'tools/hermes_capabilities.py')
        manage = importlib.util.module_from_spec(spec); spec.loader.exec_module(manage)
        names = self.home.parent / 'tools.json'; names.write_text('["terminal", "tts", "terminal"]')
        result = manage.configure(self.home, names, ci.digest(self.raw))
        self.assertTrue(result['card_unchanged']); self.assertEqual(result['tools'], 2)
        before = self.path.read_bytes()
        names.write_text('["terminal"]')
        manage.configure(self.home, names, ci.digest(self.raw))
        backups = list((self.home / '.life-engine-capability-backups').glob('*.json'))
        self.assertEqual(backups[0].read_bytes(), before)
        with self.assertRaisesRegex(ValueError, 'CARD_CHANGED'):
            manage.configure(self.home, names, 'wrong-card')

    def test_removed_or_disabled_owner_config_does_not_fall_back_mid_turn(self):
        card = json.loads(self.raw); card['options']['allowed_tools'] = ['terminal']
        self.raw = ci.json_bytes(card)
        (self.home / 'plugins/life-engine-character-card/card.json').write_bytes(self.raw)
        self.config.update(card_sha256=ci.digest(self.raw), allowed_tools=['tts'])
        for remove in (False, True):
            self.config['enabled'] = True; self.write()
            self.module.before(**self.kw); self.module.rewrite(request=self.request, **self.kw)
            if remove:
                self.path.unlink()
            else:
                self.config['enabled'] = False; self.write()
            self.assertEqual(self.module.guard_tool(tool_name='terminal', **self.kw)['action'], 'block')


if __name__ == '__main__': unittest.main()
