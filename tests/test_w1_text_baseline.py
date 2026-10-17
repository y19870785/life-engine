"""Offline admission checks for the bounded T1 helper; never import Hermes."""
import importlib.util
import json
import os
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
            self.assertEqual(probe.new_root(root / 'new'), (root / 'new').resolve())
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
                                     '--root', str(target), '--expected-runtime-sha256', 'bad',
                                     '--dependency-site', temp, '--expected-dependency-sha256', 'bad'],
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('RUNTIME_HASH_MISMATCH', result.stderr)
            self.assertFalse(target.exists())

    def test_missing_dependency_writes_failure_report_without_installing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'new'
            result = subprocess.run(
                [sys.executable, '-B', str(HELPER), '--host-root', temp, '--root', str(root),
                 '--expected-runtime-sha256', probe.tree_digest(HELPER.parents[1] / 'runtime'),
                 '--dependency-site', temp, '--expected-dependency-sha256', 'bad'],
                capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((root / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(report['state'], 'T1_FAILED')
            self.assertEqual(report['error_type'], 'FileNotFoundError')
            self.assertEqual(report['cleanup']['errors'], [])
            self.assertFalse((root / 'profiles/synthetic/plugins').exists())

    def test_setup_failures_restore_plugin_and_disable_activation(self):
        # Synthetic module imports only; tests cleanup after real ci.apply succeeds.
        with tempfile.TemporaryDirectory() as temp:
            script = r"""
import importlib.util,hashlib,os,pathlib,sys,types
h=pathlib.Path(sys.argv[1]);base=pathlib.Path(sys.argv[2]);root=base/'new'
spec=importlib.util.spec_from_file_location('probe',h);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
site=base/('python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor))/'site-packages'
marker=site/'ruamel/yaml/__init__.py';marker.parent.mkdir(parents=True);marker.write_text('',encoding='utf-8')
def module(name,**values):
 m=types.ModuleType(name);m.__file__=str(base/(name+'.py'));m.__dict__.update(values);sys.modules[name]=m;return m
ruamel=module('ruamel');ruamel.yaml=module('ruamel.yaml');ruamel.yaml.__file__=str(marker)
def db_fail(**kwargs):
 (root/'reached-stage').write_text('session_db',encoding='utf-8')
 if stage == 'exit7':
  try: subprocess.run([sys.executable,'-c',"raise RuntimeError('SYNTHETIC_SECRET_TOKEN')",'--api-key','SYNTHETIC_SECRET_TOKEN'],env={'PRIVATE_KEY':'SYNTHETIC_ENV_SECRET'})
  except RuntimeError: raise SystemExit(7)
 if stage == 'exit0': raise SystemExit(0)
 raise OSError('synthetic DB initialization failure')
module('hermes_state',SessionDB=db_fail)
module('agent');module('agent.message_metadata',stamp_message_uid=lambda value: None)
stage=sys.argv[3]
module('hermes_constants',get_hermes_home=lambda:root/'different-profile' if stage=='host_mismatch' else pathlib.Path(os.environ['HERMES_HOME']))
cli=module('hermes_cli');cli.plugins=module('hermes_cli.plugins')
module('hermes_cli.middleware',apply_llm_request_middleware=lambda *a,**k: None)
sys.path.insert(0,str(h.parents[1]/'runtime'))
from life_engine import character_continuity as cc
def fail(*a,**k):
 (root/'reached-stage').write_text('world_init',encoding='utf-8')
 raise OSError('synthetic world initialization failure')
if sys.argv[3] == 'world_init':
 cc.init=fail
else:
 for name in cc.HOST_FILES:
  f=base/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('# synthetic host file',encoding='utf-8')
original_activation=cc.activation
def activation(*args,**kwargs):
 result=original_activation(*args,**kwargs)
 if stage=='cleanup_exit' and args[3] is False: raise SystemExit(9)
 return result
cc.activation=activation
sys.argv=[str(h),'--host-root',str(base),'--root',str(root),'--expected-runtime-sha256',p.tree_digest(h.parents[1]/'runtime'),'--dependency-site',str(site),'--expected-dependency-sha256',hashlib.sha256(marker.read_bytes()).hexdigest()]
# Capture the actual durable command without replacing its implementation.
import subprocess,json
original_restrict=p.restrict_processes
def observe(config,profile):
 original_restrict(config,profile)
 guarded=subprocess.Popen
 def record(command,*a,**k):
  if not (root/'actual-child.json').exists():
   (root/'actual-child.json').write_text(json.dumps({'argv':command,'startup':sys.executable,'base':getattr(sys,'_base_executable',None)}),encoding='utf-8')
  return guarded(command,*a,**k)
 subprocess.Popen=record
p.restrict_processes=observe
p.main()
"""
            for stage in ('world_init', 'session_db', 'host_mismatch', 'exit7', 'exit0', 'cleanup_exit'):
                with self.subTest(stage=stage), tempfile.TemporaryDirectory() as scenario:
                    result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', script,
                                             str(HELPER), scenario, stage],
                                            capture_output=True, text=True, timeout=30)
                    if stage == 'exit0':
                        self.assertEqual(result.returncode, 0)
                    else:
                        self.assertNotEqual(result.returncode, 0)
                    root = Path(scenario) / 'new'
                    report = json.loads((root / 'report.json').read_text(encoding='utf-8'))
                    if stage == 'host_mismatch':
                        self.assertEqual(report['error_type'], 'ValueError', result.stderr)
                        self.assertIn('HOST_HOME_MISMATCH', result.stderr)
                        self.assertFalse((root/'reached-stage').exists())
                        self.assertFalse((root/'profiles/synthetic/plugins').exists())
                        continue
                    expected_type = 'SystemExit' if stage.startswith('exit') else 'OSError'
                    self.assertEqual(report['error_type'], expected_type, result.stderr)
                    self.assertEqual(report['state'], 'T1_CLEANUP_INCOMPLETE' if stage=='cleanup_exit' else 'T1_FAILED')
                    failed_stage = 'session_db' if stage.startswith('exit') or stage=='cleanup_exit' else stage
                    self.assertEqual((root/'reached-stage').read_text(encoding='utf-8'), failed_stage)
                    self.assertEqual(report['failure']['stage'], failed_stage)
                    self.assertIn({'stage': failed_stage, 'event': 'enter'}, report['stages'])
                    self.assertNotIn({'stage': failed_stage, 'event': 'return'}, report['stages'])
                    self.assertTrue(all(set(frame)=={'file','function','line'} for frame in report['failure']['stack']))
                    if stage.startswith('exit'):
                        self.assertEqual(result.returncode, int(stage[4:]))
                        self.assertEqual(report['failure']['exit_code'], int(stage[4:]))
                    if stage == 'exit7':
                        raw = json.dumps(report)
                        self.assertNotIn('SYNTHETIC_SECRET_TOKEN', raw)
                        self.assertNotIn('SYNTHETIC_ENV_SECRET', raw)
                        denial = report['denied_processes'][0]
                        self.assertIn('db_fail', [frame['function'] for frame in denial['stack']])
                        self.assertTrue(all(set(frame)=={'file','function','line'} for frame in denial['stack']))
                        self.assertEqual(denial['argv']['arguments'][1]['token'], '-c')
                        self.assertNotIn('token', denial['argv']['arguments'][2])
                    if stage == 'cleanup_exit':
                        self.assertEqual(result.returncode, 1)  # Original OSError wins over cleanup SystemExit(9).
                        self.assertEqual(report['cleanup']['errors'][0]['exit_code'], 9)
                        self.assertEqual(report['cleanup']['errors'][0]['step'], 'disable_v2')
                        self.assertIn({'stage':'cleanup_restore_plugin','event':'return'},report['stages'])
                    else:
                        self.assertEqual(report['cleanup']['errors'], [])
                    plugin = root / 'profiles/synthetic/plugins/life-engine-character-card'
                    self.assertEqual(list(plugin.iterdir()), [])
                    activation = root / 'profiles/synthetic/.life-engine-continuity.json'
                    if stage == 'world_init':
                        self.assertFalse(activation.exists())
                    else:
                        child = json.loads((root/'actual-child.json').read_text(encoding='utf-8'))
                        self.assertTrue(Path(child['argv'][0]).samefile(child['startup']))
                        self.assertEqual(Path(child['argv'][0]), Path(child['base']).resolve())
                        self.assertIn('from life_engine import cli, deploy_cli, durable', child['argv'][2])
                        self.assertFalse(json.loads(activation.read_text(encoding='utf-8'))['enabled'])

    def test_diagnostic_values_do_not_expose_opaque_text(self):
        value = probe.safe_argv(['/tmp/secret-path/unknown-executable', '-c', 'install',
                                 '--token=SYNTHETIC_SECRET', 'SYNTHETIC_SECRET'])
        rendered = json.dumps(value)
        self.assertNotIn('secret-path', rendered)
        self.assertNotIn('SYNTHETIC_SECRET', rendered)
        self.assertNotIn('token', value['arguments'][2])
        self.assertEqual(value['arguments'][2]['bytes'], len('install'))
        self.assertEqual(len(value['arguments'][2]['sha256']), 64)
        self.assertNotIn('SYNTHETIC_SECRET', json.dumps(probe.safe_value('SYNTHETIC_SECRET')))

    def test_optional_version_queries_are_denied_with_native_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            host = Path(temp)
            (host / 'hermes_cli').mkdir()
            (host / 'hermes_cli/version_info.py').write_text(
                "import subprocess\n"
                "def _run_git(command,cwd):\n"
                " try: return subprocess.run(command,cwd=cwd,capture_output=True,text=True).stdout\n"
                " except (OSError,subprocess.SubprocessError): return None\n", encoding='utf-8')
            script = r"""
import importlib.util,json,pathlib,sys,subprocess
h=pathlib.Path(sys.argv[1]);host=pathlib.Path(sys.argv[2])
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=load('probe',h);v=load('version_info',host/'hermes_cli/version_info.py')
(host/'version_info.py').write_bytes((host/'hermes_cli/version_info.py').read_bytes())
wrong=load('wrong_version_info',host/'version_info.py')
c={'python':sys.executable,'runtime':'','root':str(host/'world'),'host_root':str(host)}
p.restrict_processes(c,host/'profile')
results=[v._run_git(list(q),str(host)) for q in p.VERSION_QUERIES]
denied=[]
for command,cwd in ((['git','rev-parse','HEAD'],str(host/'other')),(['git','fetch'],str(host)),(['git','show','v1:pyproject.toml'],str(host)),(['git','rev-list','--count','v1..HEAD'],str(host))):
 try: v._run_git(command,cwd)
 except RuntimeError: denied.append(True)
try: wrong._run_git(['git','rev-parse','HEAD'],str(host))
except RuntimeError: denied.append(True)
try: subprocess.run(['git','rev-parse','HEAD'],cwd=str(host))
except RuntimeError: denied.append(True)
print(json.dumps({'results':results,'denied':denied,'logged':c['version_query_denials']}))
"""
            result = subprocess.run([sys.executable, '-B', '-c', script, str(HELPER), str(host)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['results'], [None] * 7)
            self.assertEqual(report['denied'], [True] * 6)
            self.assertEqual(report['logged'], [list(q) for q in probe.VERSION_QUERIES])

    @unittest.skipUnless(os.name == 'nt', 'Windows short names only')
    def test_real_windows_short_paths_reach_setup_and_version_fallback(self):
        import ctypes
        with tempfile.TemporaryDirectory(prefix='w1 long path identity ') as temp:
            buffer = ctypes.create_unicode_buffer(32768)
            if not ctypes.windll.kernel32.GetShortPathNameW(temp, buffer, len(buffer)):
                self.skipTest('Windows short-path API unavailable')
            short = Path(buffer.value)
            if str(short) == str(Path(temp)):
                self.skipTest('Filesystem does not supply distinct short names')
            self.assertTrue(short.samefile(temp))
            self.assertNotEqual(str(short), str(short.resolve()))
            script = """
import sys,tempfile,unittest
sys.path.insert(0,sys.argv[1]);tempfile.tempdir=sys.argv[2]
from test_w1_text_baseline import T1ProbeTests
suite=unittest.TestSuite(T1ProbeTests(name) for name in ('test_setup_failures_restore_plugin_and_disable_activation','test_optional_version_queries_are_denied_with_native_fallback'))
r=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not r.wasSuccessful())
"""
            result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', script,
                                     str(HELPER.parents[1]/'tests'), str(short)],
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipIf(os.name == 'nt', 'Unix interpreter symlink regression')
    def test_real_interpreter_alias_reaches_durable_and_db_fault(self):
        with tempfile.TemporaryDirectory() as temp:
            alias = Path(temp)/'python-alias'
            alias.symlink_to(Path(sys.executable).resolve())
            self.assertTrue(alias.samefile(sys.executable))
            script = """
import sys,unittest
sys.path.insert(0,sys.argv[1])
from test_w1_text_baseline import T1ProbeTests
r=unittest.TextTestRunner(verbosity=2).run(T1ProbeTests('test_setup_failures_restore_plugin_and_disable_activation'));sys.exit(not r.wasSuccessful())
"""
            result = subprocess.run([str(alias), '-B', '-X', 'utf8', '-c', script,
                                     str(HELPER.parents[1]/'tests')],
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)

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
(root/'foreign-python').write_text('not the pinned interpreter',encoding='utf-8')
p.restrict_processes(c,profile)
denied=[]
for action in (lambda: socket.socket(),lambda: subprocess.run([sys.executable,'-c','print(1)']),
 lambda: subprocess.run([str(root/'foreign-python'),'-c',p.IMPORT_PROBE,c['runtime'],'8']),
 lambda: subprocess.run([sys.executable,'-c',p.IMPORT_PROBE+'# changed',c['runtime'],'8']),
 lambda: subprocess.run([sys.executable,'-c',p.IMPORT_PROBE,c['runtime'],'8']),
 lambda: subprocess.run([sys.executable,'-c',p.IMPORT_PROBE,c['runtime'],'9']),
 lambda: subprocess.run([sys.executable,'-c',p.IMPORT_PROBE,str(root/'world/releases/unverified/runtime'),'8'])):
 try: action()
 except RuntimeError: denied.append(True)
cmd=[sys.executable,'-I','-X','utf8','-c',p.RUNNER,c['runtime'],'character-continuity','context','--root',c['root'],'--profile-home',str(profile),'--card',str(profile/'plugins/life-engine-character-card/card.json')]
try: subprocess.run(cmd,executable=str(root/'foreign-python'))
except RuntimeError: denied.append(True)
r=subprocess.run(cmd,capture_output=True,text=True,timeout=10,shell=False)
print(json.dumps({'denied':denied,'child':json.loads(r.stdout),'returncode':r.returncode}))
'''
            result = subprocess.run([sys.executable, '-B', '-c', script, str(HELPER), str(root)],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value['denied'], [True] * 8)
            self.assertEqual(value['child'], {'network_denied': True, 'no_bytecode': True})
            self.assertEqual(value['returncode'], 0)
            self.assertEqual(list(runtime.rglob('__pycache__')), [])


if __name__ == '__main__':
    unittest.main()
