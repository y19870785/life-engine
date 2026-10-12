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
            initial = self.command('status', '--sandbox', sandbox)['virtual_daily']
            self.assertEqual({x['name']: x['state'] for x in initial},
                             {'在书房读书': 'ACTIVE', '散步': 'PLANNED'})
            day0_prompt = self.command_text('hermes-prompt', '--day', '0', '--sandbox', sandbox)
            self.assertIn('在书房读书／书房：ACTIVE', day0_prompt)
            self.assertIn('散步／公园：PLANNED', day0_prompt)
            preview = self.command('day0', '--sandbox', sandbox)
            self.assertEqual(preview['accepted_memory'], [])
            day0 = self.command('day0', '--accept', '--sandbox', sandbox)
            day1 = self.command('day1', '--sandbox', sandbox)
            self.assertNotEqual(day0['session'], day1['session'])
            self.assertEqual(day1['memory'][0]['content'], day0['accepted_memory'][0]['content'])
            self.assertEqual(day1['memory'][0]['scope'], ready['world'])
            activities = {(x['local_date'], x['name']): x for x in day1['virtual_daily']}
            self.assertEqual(activities['2026-09-28', '散步']['state'], 'COMPLETED')
            self.assertFalse(any(day == '2026-09-29' for day, _ in activities))
            self.assertEqual(day1['current_activity'], 'UNKNOWN')
            self.assertEqual(activities['2026-09-28', '散步']['location_source'], 'FICTIONAL_ROLE_STATE')
            self.assertEqual(self.command('isolation-check', '--sandbox', sandbox)['status'], 'ISOLATED')
            prompt = self.command_text('hermes-prompt', '--day', '1', '--sandbox', sandbox)
            self.assertIn('明天下午有个面试', prompt)
            self.assertIn('PLANNED 只能说计划', prompt)
            self.assertIn('今天当前活动未知', prompt)
            self.assertNotIn('2026-09-29', prompt)
            self.assertNotIn('RP_ONLY_SECRET', prompt)
            stale = subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPT),
                                    'hermes-prompt', '--day', '0', '--sandbox', sandbox],
                                   capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn('CLOCK_REGRESSION', stale.stderr)
            self.assertEqual(self.command('forget', '--sandbox', sandbox)['normal_query'], [])
            self.assertEqual(self.command('day1', '--sandbox', sandbox)['memory'], [])
            forgotten_prompt = self.command_text('hermes-prompt', '--day', '1', '--sandbox', sandbox)
            self.assertNotIn('面试', forgotten_prompt)
            self.assertEqual(self.command('day0', '--accept', '--sandbox', sandbox)['accepted_memory'], [])
            self.assertEqual(self.command('reset', '--sandbox', sandbox)['status'], 'SYNTHETIC_SANDBOX_REMOVED')
            self.assertFalse(Path(sandbox).exists())

    @unittest.skipUnless(sys.platform == 'win32', 'Windows 8.3 path aliases')
    def test_windows_short_path_reopens_same_sandbox(self):
        import ctypes
        from ctypes import wintypes
        short_path = ctypes.WinDLL('kernel32', use_last_error=True).GetShortPathNameW
        short_path.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        short_path.restype = wintypes.DWORD
        with tempfile.TemporaryDirectory(prefix='life-engine-x1-long-path-') as temp:
            buffer = ctypes.create_unicode_buffer(32768)
            length = short_path(str(Path(temp).resolve()), buffer, len(buffer))
            self.assertGreater(length, 0)
            self.assertLess(length, len(buffer))
            if buffer.value.lower() == str(Path(temp).resolve()).lower():
                self.skipTest('8.3 aliases are disabled on this volume')
            alias = str(Path(buffer.value) / 'trial')
            ready = self.command('init', '--sandbox', alias)
            self.assertEqual(Path(ready['sandbox']), (Path(temp) / 'trial').resolve())
            self.assertEqual(self.command('status', '--sandbox', alias)['memory'], [])
            self.command('reset', '--sandbox', alias)
            self.assertFalse((Path(temp) / 'trial').exists())

    def test_temp_root_is_never_a_sandbox(self):
        result = subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPT), 'reset',
                                 '--sandbox', tempfile.gettempdir()], capture_output=True,
                                text=True, encoding='utf-8', timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SANDBOX_PATH_REQUIRED', result.stderr)

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
