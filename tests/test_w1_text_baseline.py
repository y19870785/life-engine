"""Offline admission checks for the bounded T1 helper; never import Hermes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / 'tools/hermes_text_baseline_probe.py'
spec = importlib.util.spec_from_file_location('t1_probe', HELPER)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class T1ProbeTests(unittest.TestCase):
    def test_new_root_refuses_existing_or_missing_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(probe.new_root(root / 'new'), root / 'new')
            self.assertFalse((root / 'new').exists())
            for path in (root, root / 'missing/new'):
                with self.assertRaisesRegex(ValueError, 'NEW_ROOT_REQUIRED'):
                    probe.new_root(path)

    def test_digest_binds_paths_and_python_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root / 'a.py'
            source.write_text('one', encoding='utf-8')
            first = probe.tree_digest(root)
            source.write_text('two', encoding='utf-8')
            self.assertNotEqual(first, probe.tree_digest(root))
            source.write_text('one', encoding='utf-8')
            source.rename(root / 'b.py')
            self.assertNotEqual(first, probe.tree_digest(root))

    def test_bad_digest_has_no_target_directory_side_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'new'
            result = subprocess.run([sys.executable, '-B', str(HELPER), '--host-root', temp,
                                     '--root', str(target), '--expected-runtime-sha256', 'bad'],
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('RUNTIME_HASH_MISMATCH', result.stderr)
            self.assertFalse(target.exists())

    def test_parent_and_exact_child_deny_network_and_other_processes(self):
        # Audit hooks are permanent: install only inside this fresh worker.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); runtime = root / 'runtime'
            package = runtime / 'life_engine'; package.mkdir(parents=True)
            (package / '__init__.py').write_text('', encoding='utf-8')
            (package / 'character_continuity.py').write_text(
                "import json,socket,sys\n"
                "try:\n socket.socket()\nexcept RuntimeError:\n"
                " print(json.dumps({'network_denied':True,'no_bytecode':sys.dont_write_bytecode}))\n",
                encoding='utf-8')
            script = '''
import importlib.util,json,pathlib,socket,subprocess,sys
spec=importlib.util.spec_from_file_location('probe',sys.argv[1]);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
root=pathlib.Path(sys.argv[2]);profile=root/'profiles/synthetic'
c={'python':sys.executable,'runtime':str(root/'runtime'),'root':str(root/'world')}
p.restrict_processes(c,profile)
denied=[]
for action in (lambda: socket.socket(),lambda: subprocess.run([sys.executable,'-c','print(1)'])):
 try: action()
 except RuntimeError: denied.append(True)
cmd=[sys.executable,'-I','-X','utf8','-c',p.RUNNER,c['runtime'],'character-continuity','context','--root',c['root'],'--profile-home',str(profile),'--card',str(profile/'plugins/life-engine-character-card/card.json')]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=10,shell=False)
print(json.dumps({'denied':denied,'child':json.loads(r.stdout),'returncode':r.returncode}))
'''
            result = subprocess.run([sys.executable, '-B', '-c', script, str(HELPER), str(root)],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value['denied'], [True, True])
            self.assertEqual(value['child'], {'network_denied': True, 'no_bytecode': True})
            self.assertEqual(value['returncode'], 0)
            self.assertEqual(list(runtime.rglob('__pycache__')), [])


if __name__ == '__main__':
    unittest.main()
