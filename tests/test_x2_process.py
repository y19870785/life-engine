"""真实子进程服务、崩溃、重开；不以同进程对象代替跨进程证据。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_x2_runtime import request
from test_x2_web import Client

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(Path(getattr(sys, '_base_executable', sys.executable)).resolve())
FLAGS = [PYTHON, '-I', '-S', '-B', '-X', 'utf8']


class ProcessTests(unittest.TestCase):
    def launch(self, identifier=None, env=None):
        args = FLAGS + [str(ROOT / 'tools/experience_x2.py'), 'start', '--offline']
        args += ['--fixture', identifier] if identifier else ['--new']
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding='utf8', env=env)
        self.addCleanup(self.cleanup_process, proc)
        data = json.loads(proc.stdout.readline())
        return proc, data

    def cleanup_process(self, proc):
        if proc.poll() is None:
            proc.kill()
        proc.communicate(timeout=10)

    def test_http_process_close_reopen_full_loop(self):
        with tempfile.TemporaryDirectory(prefix='x2-production-sentinel-') as directory:
            sentinel = Path(directory) / 'production.txt'
            sentinel.write_text('DO NOT OPEN OR MODIFY', encoding='utf8')
            poison = Path(directory) / 'life_engine'
            poison.mkdir()
            (poison / '__init__.py').write_text('raise RuntimeError("POISON_IMPORT")', encoding='utf8')
            env = dict(os.environ, PYTHONPATH=directory, HOME=directory, USERPROFILE=directory)
            p, first = self.launch(env=env)
            c = Client(first['url']); c.bootstrap()
            self.assertEqual(c.send('POST', '/api/new', {})[0], 200)
            self.assertEqual(c.send('POST', '/api/turn', request(text='蓝灯书店找到地图'))[0], 200)
            self.assertEqual(c.send('POST', '/api/finish', request())[0], 200)
            state = c.bootstrap()
            self.assertEqual(state['recalls'], [])
            self.assertEqual(c.send('POST', '/api/accept', request(revision=state['revision']))[0], 200)
            c.send('POST', '/api/end', {})
            # 第二个实际进程持锁失败；不改变 fixture。
            second, denied = self.launch(first['fixture'])
            self.assertEqual(denied['code'], 'FIXTURE_BUSY')
            self.assertEqual(second.wait(timeout=10), 1)
            c.send('POST', '/api/stop', {})
            self.assertEqual(p.wait(timeout=10), 0)
            reopened, info = self.launch(first['fixture'])
            self.assertEqual(info['fixture'], first['fixture'])
            newer = Client(info['url']); newer.bootstrap()
            newer.token = c.token
            self.assertEqual(newer.send('GET', '/api/bootstrap')[0], 403)
            newer = Client(info['url']); newer.bootstrap()
            result = newer.send('POST', '/api/query', {'query':'蓝灯书店'})[1]
            self.assertEqual(len(result['recalls']), 1)
            self.assertEqual(result['recalls'][0]['reality'], 'fictional_shared_experience')
            newer.send('POST', '/api/feedback', {'rating':'useful','reason':'source'})
            self.assertEqual(newer.send('GET', '/api/export')[1]['accepted'], 1)
            newer.send('POST', '/api/stop', {})
            self.assertEqual(reopened.wait(timeout=10), 0)
            self.assertEqual(sentinel.read_text(encoding='utf8'), 'DO NOT OPEN OR MODIFY')
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ['life_engine', 'production.txt'])

    def test_abrupt_process_death_at_four_commit_windows(self):
        script = '''
import sys,json,os
sys.path[:0]=[sys.argv[1]+'/tools',sys.argv[1]+'/runtime']
from x2_runtime import Controller
def request(**kw):return dict(request=os.urandom(16).hex(),**kw)
c=Controller(); c.mutate('new',{})
stage=sys.argv[2]
if stage in ('after_candidate','after_accept'): c.mutate('turn',request(text='蓝灯书店地图'))
if stage=='after_accept': c.mutate('finish',request())
print(json.dumps({'fixture':c.identifier}),flush=True)
def fault(point):
 if point==stage:os._exit(73)
c.fault=fault
if stage=='after_candidate':c.mutate('finish',request())
elif stage=='after_accept':c.mutate('accept',request(revision=c.view()['revision']))
else:c.mutate('turn',request(text='蓝灯书店地图'))
'''
        for stage in ('after_user','after_candidate','after_accept','before_index'):
            with self.subTest(stage=stage):
                result = subprocess.run(FLAGS + ['-c', script, str(ROOT), stage],
                    capture_output=True, text=True, encoding='utf8', timeout=40)
                self.assertEqual(result.returncode, 73, result.stderr)
                identifier = json.loads(result.stdout)['fixture']
                p, opened = self.launch(identifier)
                if stage == 'after_user':
                    self.assertEqual(opened['code'], 'INCOMPLETE_TURN')
                    self.assertEqual(p.wait(timeout=10), 1)
                    continue
                client = Client(opened['url']); state = client.bootstrap()
                self.assertEqual(len(state['turns']), 1)
                if stage == 'after_candidate':
                    self.assertEqual(state['candidate']['canon'], 'candidate')
                    self.assertEqual(state['recalls'], [])
                if stage == 'after_accept':
                    self.assertEqual(len(state['recalls']), 1)
                if stage == 'before_index':
                    self.assertEqual(state['phase'], 'interrupted')
                    self.assertEqual(client.send('POST','/api/finish',request())[0], 200)
                client.send('POST','/api/stop',{})
                self.assertEqual(p.wait(timeout=10), 0)

    def test_offline_network_and_production_sentinel_audit(self):
        script = '''
import sys,json,socket,os
from pathlib import Path
sys.path[:0]=[sys.argv[1]+'/tools',sys.argv[1]+'/runtime']
from experience_x2 import offline_guard
from x2_runtime import Controller,X2Error
sentinel=Path(sys.argv[2]).absolute()
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  if Path(os.fsdecode(args[0])).absolute().is_relative_to(sentinel):raise RuntimeError('PRODUCTION_OPEN_ATTEMPT')
sys.addaudithook(audit);sys.addaudithook(offline_guard)
denied=[]
for name,call in [('connect',lambda:socket.create_connection(('127.0.0.1',11434))),
 ('dns',lambda:socket.getaddrinfo('example.invalid',80)),
 ('external_bind',lambda:socket.socket().bind(('0.0.0.0',0)))]:
 try:call()
 except X2Error:denied.append(name)
c=Controller();print(json.dumps({'denied':denied,'probe':c.export()['initializer']}));c.close()
'''
        with tempfile.TemporaryDirectory(prefix='x2-never-open-') as directory:
            result = subprocess.run(FLAGS + ['-c', script, str(ROOT), directory],
                capture_output=True, text=True, encoding='utf8', timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['denied'], ['connect','dns','external_bind'])
