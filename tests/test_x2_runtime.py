"""实际 Core 控制器、身份、来源与故障重开；全部原创合成数据。"""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'tools'),
                str(Path(__file__).resolve().parents[1] / 'runtime')]
from x2_runtime import Controller, X2Error, MANAGED, fixture_path, initialize, d
from life_engine.domain import DomainId
from life_engine.memory import OwnerMemoryContext
from life_engine.memory_repository import MemoryRuntimeError


def request(**kw):
    return dict(request=os.urandom(16).hex(), **kw)


def prepare(c):
    c.mutate('new', {})
    c.mutate('turn', request(text='我们在蓝灯书店找到地图，约定明天去灯塔。'))
    c.mutate('finish', request())


class RuntimeTests(unittest.TestCase):
    def controller(self, identifier=None):
        c = Controller(identifier)
        self.addCleanup(c.close)
        return c

    def test_candidate_accept_end_reopen_source_feedback(self):
        c = self.controller()
        prepare(c)
        before = c.view('蓝灯书店')
        self.assertEqual(before['recalls'], [])
        self.assertEqual(before['candidate']['canon'], 'candidate')
        accept = request(revision=before['revision'])
        c.mutate('accept', accept)
        c.mutate('accept', accept)
        c.mutate('end', {})
        identifier = c.identifier
        c.close()
        reopened = self.controller(identifier)
        result = reopened.view('蓝灯书店')['recalls']
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['source'], 'roleplay_recall')
        self.assertEqual(result[0]['reality'], 'fictional_shared_experience')
        self.assertIn('rp-world:', result[0]['source_reference'])
        self.assertNotEqual(result[0]['predecessor'], 'None')
        reopened.mutate('feedback', dict(rating='useful', reason='source'))
        report = json.dumps(reopened.export(), ensure_ascii=False)
        for forbidden in ('蓝灯书店', str(MANAGED), 'Bearer', 'prompt', 'source_reference'):
            self.assertNotIn(forbidden, report)
        self.assertEqual(reopened.export()['feedback'], [dict(rating='useful', reason='source')])

    def test_boundaries_replay_and_revision(self):
        c = self.controller()
        with self.assertRaises(X2Error):
            c.mutate('turn', request(text='未开始'))
        c.mutate('new', {})
        for bad in ('', '字' * 401, '\ud800'):
            with self.assertRaises(X2Error):
                c.mutate('turn', request(text=bad))
        body = request(text='蓝灯书店')
        c.mutate('turn', body)
        c.mutate('turn', body)
        self.assertEqual(len(c.current()['turns']), 1)
        with self.assertRaises(X2Error):
            c.mutate('turn', dict(body, text='偷换'))
        for _ in range(3):
            c.mutate('turn', request(text='地图'))
        with self.assertRaisesRegex(X2Error, 'SESSION_LIMIT_REACHED'):
            c.mutate('turn', request(text='第5轮'))
        c.mutate('finish', request())
        with self.assertRaisesRegex(X2Error, 'REVISION_CONFLICT'):
            c.mutate('accept', request(revision=-1))
        self.assertEqual(c.view()['recalls'], [])
        with self.assertRaises(X2Error):
            c.mutate('turn', dict(request(text='注入'), world='other'))

    def test_seven_sessions_limit(self):
        c = self.controller()
        for _ in range(7):
            prepare(c)
            c.mutate('accept', request(revision=c.view()['revision']))
            c.mutate('end', {})
        self.assertEqual(c.export()['accepted'], 7)
        self.assertEqual(len(c.memory.query(c.soul_session, limit=100).records), 7)
        with self.assertRaisesRegex(X2Error, 'FIXTURE_LIMIT_REACHED'):
            c.mutate('new', {})

    def test_foreign_fixture_memory_and_source_rejected(self):
        a, b = self.controller(), self.controller()
        prepare(a)
        prepare(b)
        foreign = DomainId.parse(a.current()['candidate'])
        with self.assertRaises(MemoryRuntimeError):
            b.memory.get_memory(b.soul_owner, foreign, history=True)
        # 将外国成员 ID 塞入本 fixture 的摘录清单也不能读回。
        b.current()['turns'][0]['user'] = a.current()['turns'][0]['user']
        b.current()['phase'] = 'roleplay'
        b.save()
        with self.assertRaisesRegex(X2Error, 'RECOVERY_REQUIRED'):
            b.mutate('finish', request())
        self.assertIsNotNone(b.state['pending'])

    def test_actual_fault_windows_reopen_without_duplicates(self):
        for stage in ('after_user', 'after_pair', 'after_candidate', 'after_accept', 'before_index'):
            with self.subTest(stage=stage):
                c = self.controller()
                c.mutate('new', {})
                if stage in ('after_candidate', 'after_accept'):
                    c.mutate('turn', request(text='蓝灯书店地图'))
                if stage == 'after_accept':
                    c.mutate('finish', request())
                action = 'accept' if stage == 'after_accept' else ('finish' if stage == 'after_candidate' else 'turn')
                payload = request(**({'revision': c.view()['revision']} if action == 'accept'
                                    else {'text': '蓝灯书店地图'} if action == 'turn' else {}))
                def fault(point):
                    if point == stage:
                        raise OSError('injected synthetic failure')
                c.fault = fault
                with self.assertRaisesRegex(X2Error, 'RECOVERY_REQUIRED'):
                    c.mutate(action, payload)
                ident = c.identifier
                c.close()
                if stage == 'after_user':
                    with self.assertRaisesRegex(X2Error, 'INCOMPLETE_TURN'):
                        Controller(ident)
                    continue
                reopened = self.controller(ident)
                self.assertIsNone(reopened.state['pending'])
                self.assertEqual(len(reopened.current()['turns']), 1)
                from x2_runtime import scope
                owner = OwnerMemoryContext(reopened.actor, scope(reopened.current()['scope']))
                self.assertEqual(len(reopened.memory.query(owner, history=True, limit=100).records), 2)
                self.assertEqual(len(reopened.view()['recalls']), 1 if action == 'accept' else 0)
                if action == 'finish':
                    self.assertEqual(len(reopened.memory.query(reopened.soul_owner, history=True, limit=100).records), 1)

    def test_unknown_recovery_stops_without_new_write(self):
        c = self.controller()
        c.mutate('new', {})
        c.state['pending'] = dict(action='turn', payload=request(text='合成'), fingerprint='invalid', time='bad')
        c.save()
        ident = c.identifier
        c.close()
        with self.assertRaisesRegex(X2Error, 'RECOVERY_REQUIRED'):
            Controller(ident)

    def test_world_creation_unknown_outcome_never_rekeys(self):
        c = self.controller()
        def fault(stage):
            if stage == 'after_world':
                raise OSError('synthetic world interruption')
        c.fault = fault
        with self.assertRaises(OSError):
            c.mutate('new', {})
        self.assertEqual(c.state['pending']['action'], 'new')
        with self.assertRaisesRegex(X2Error, 'RECOVERY_REQUIRED'):
            c.mutate('new', {})
        identifier = c.identifier
        c.close()
        with self.assertRaisesRegex(X2Error, 'RECOVERY_REQUIRED'):
            Controller(identifier)

    def test_paths_marker_registry_and_lock(self):
        for value in ('../production', 'C:\\Users', 'a' * 33, 'A' * 32):
            with self.assertRaises(X2Error):
                fixture_path(value)
        c = self.controller()
        with self.assertRaises(TimeoutError):
            Controller(c.identifier)
        old = copy.deepcopy(c.state)
        d.write(c.root / 'x2.json', dict(old, version='999'))
        with self.assertRaisesRegex(X2Error, 'CONTROL_CHANGED'):
            c.view()
        ident = c.identifier
        c.close()
        with self.assertRaisesRegex(X2Error, 'FIXTURE_VERSION_MISMATCH'):
            Controller(ident)
        d.write(c.root / 'x2.json', old)
        reg = d.read(c.root / 'install/registry.json')
        reg['instances'][old['instance']]['host_home'] = str(c.root.parent / 'production-sentinel')
        d.write(c.root / 'install/registry.json', reg)
        with self.assertRaisesRegex(X2Error, 'REGISTRY_TARGET_DENIED'):
            Controller(ident)

    def test_unknown_control_fields_and_export_payload_fail_closed(self):
        c = self.controller()
        from x2_runtime import offline_report
        identifier = c.identifier
        original = copy.deepcopy(c.state)
        c.close()
        for malformed in (dict(original, unexpected='do not export'),
                          dict(original, probe=dict(original['probe'], token='secret')),
                          dict(original, feedback=[{'rating':'useful','reason':'none','text':'private'}])):
            d.write(c.root / 'x2.json', malformed)
            with self.assertRaisesRegex(X2Error, 'RECOVERY_REQUIRED'):
                Controller(identifier)
            with self.assertRaisesRegex(X2Error, 'RECOVERY_REQUIRED'):
                offline_report(identifier)

    def test_symlink_or_junction_denied(self):
        c = self.controller()
        link = c.root / 'foreign'
        target = c.root / 'synthetic-host'
        if os.name == 'nt':
            import subprocess
            done = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True)
            self.assertEqual(done.returncode, 0)
            self.addCleanup(os.rmdir, link)
        else:
            link.symlink_to(target, target_is_directory=True)
            self.addCleanup(link.unlink)
        with self.assertRaisesRegex(X2Error, 'PATH_LINK_DENIED'):
            c.view()

    def test_initializer_probe_rejects_unknown_subprocess(self):
        c = self.controller()
        self.assertEqual(c.export()['initializer'], dict(isolated=True, no_site=True, module_inside_release=True))
        from x2_runtime import subprocess
        real = d.probe_release
        def bad_probe(*args):
            subprocess.run([sys.executable, '-c', 'print("not approved")'])
        # 函数常量仍来自已审脚本，实际调用则故意换成未知 argv。
        from types import SimpleNamespace
        fake = SimpleNamespace(__code__=real.__code__, __call__=bad_probe)
        class Probe:
            __code__ = real.__code__
            def __call__(self, *args):
                return bad_probe(*args)
        with tempfile.TemporaryDirectory(prefix='x2-probe-test-') as directory:
            with patch.object(d, 'probe_release', Probe()):
                with self.assertRaisesRegex(X2Error, 'INITIALIZER_PROBE_DENIED'):
                    initialize(Path(directory))
