"""Cross-process checks for the isolated, synthetic X1 trial."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'examples' / 'experience_x1.py'


class ExperienceX1Tests(unittest.TestCase):
    def command_text(self, name, *args):
        result = subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPT), name, *args],
                                capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def command(self, name, *args):
        return json.loads(self.command_text(name, *args))

    def test_reopen_forget_and_world_isolation(self):
        with tempfile.TemporaryDirectory(prefix='life-engine-x1-test-') as temp:
            sandbox = str(Path(temp) / 'trial')
            ready = self.command('init', '--sandbox', sandbox)
            self.assertEqual(ready['status'], 'SYNTHETIC_READY')
            preview = self.command('day0', '--sandbox', sandbox)
            self.assertEqual(preview['accepted_memory'], [])
            day0 = self.command('day0', '--accept', '--sandbox', sandbox)
            day1 = self.command('day1', '--sandbox', sandbox)
            self.assertNotEqual(day0['session'], day1['session'])
            self.assertEqual(day1['memory'][0]['content'], day0['accepted_memory'][0]['content'])
            self.assertEqual(day1['memory'][0]['scope'], ready['world'])
            activities = {(x['local_date'], x['name']): x for x in day1['virtual_daily']}
            self.assertEqual(activities['2026-09-28', '散步']['state'], 'COMPLETED')
            self.assertEqual(activities['2026-09-29', '散步']['state'], 'PLANNED')
            self.assertEqual(activities['2026-09-28', '散步']['location_source'], 'FICTIONAL_ROLE_STATE')
            self.assertEqual(self.command('isolation-check', '--sandbox', sandbox)['status'], 'ISOLATED')
            prompt = self.command_text('hermes-prompt', '--day', '1', '--sandbox', sandbox)
            self.assertIn('明天下午有个面试', prompt)
            self.assertIn('PLANNED 只能说计划', prompt)
            self.assertNotIn('RP_ONLY_SECRET', prompt)
            self.assertEqual(self.command('forget', '--sandbox', sandbox)['normal_query'], [])
            self.assertEqual(self.command('day1', '--sandbox', sandbox)['memory'], [])
            forgotten_prompt = self.command_text('hermes-prompt', '--day', '1', '--sandbox', sandbox)
            self.assertNotIn('明天下午有个面试', forgotten_prompt)
            self.assertEqual(self.command('day0', '--accept', '--sandbox', sandbox)['accepted_memory'], [])

    def test_card_is_preview_only(self):
        with tempfile.TemporaryDirectory(prefix='life-engine-x1-card-') as temp:
            card = Path(temp) / 'card.json'
            card.write_text(json.dumps({'name': '合成角色', 'description': '原创测试',
                                        'first_mes': '你好', 'scenario': '纸面设定'}, ensure_ascii=False),
                            encoding='utf-8')
            result = self.command('card-preview', '--card', str(card))
            self.assertEqual(result['profile']['display_name'], '合成角色')
            self.assertFalse(result['imported_to_world'])


if __name__ == '__main__':
    unittest.main()
