"""使用临时安装、模拟宿主与真实子进程；不访问生产 Host。"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from life_engine.config import defaults
from life_engine.domain import DomainError
from life_engine.domain_policy import HostCapabilities
from life_engine.durable import create_install, registry
from life_engine.sandbox import FORMAT, delivery_trace, identity, report, validate_probe


def capture(expected):
    return {'format': FORMAT, 'at': datetime.now(timezone.utc).isoformat(),
            'plugin_epoch': '模拟加载代次', 'hook_runtime': expected,
            'host': {'kind': expected['host_kind'], 'profile': expected['host_home'],
                     'workspace': expected['host_home'], 'agent_id': expected['host_agent_id'],
                     'version': '模拟版本', 'installation': '模拟安装目录', 'executable': '模拟可执行文件',
                     'origin': 'https://github.com/NousResearch/hermes-agent.git'},
            'probes': {name: {'ok': True, 'runtime': expected} for name in ('status', 'doctor', 'wake', 'photo')}}


class AttestationTests(unittest.TestCase):
    def setUp(self):
        self.expected = {'host_kind': 'hermes', 'host_home': str(ROOT), 'host_agent_id': '',
                         'instance_id': '模拟实例', 'generation': 'initial-test', 'release': '模拟版本'}

    def test_matching_and_wrong_profile_or_agent(self):
        self.assertEqual(validate_probe(capture(self.expected), self.expected), [])
        wrong = capture(self.expected)
        wrong['host']['profile'] = str(ROOT.parent)
        self.assertIn('HOST_BINDING_MISMATCH', validate_probe(wrong, self.expected))
        self.expected.update(host_kind='openclaw', host_agent_id='sandbox')
        wrong = capture(self.expected)
        wrong['host']['agent_id'] = 'production'
        self.assertIn('HOST_AGENT_MISMATCH', validate_probe(wrong, self.expected))

    def test_missing_invalid_stale_and_future_attestation(self):
        for value in (None, [], {}, {'format': '错误版本'}):
            self.assertEqual(validate_probe(value, self.expected), ['INVALID_ATTESTATION'])
        for delta in (-301, 20):
            value = capture(self.expected)
            value['at'] = (datetime.now(timezone.utc) + timedelta(seconds=delta)).isoformat()
            self.assertIn('ATTESTATION_EXPIRED', validate_probe(value, self.expected))
        value['at'] = '2026-09-27T10:00:00'
        self.assertIn('INVALID_TIMESTAMP', validate_probe(value, self.expected))

    def test_unknown_version_and_nonofficial_hermes_are_not_attested(self):
        value = capture(self.expected)
        value['host']['version'] = 'UNKNOWN'
        value['host']['origin'] = 'https://github.com/y19870785/hermes-agent.git'
        errors = validate_probe(value, self.expected)
        self.assertIn('HOST_VERSION_UNKNOWN', errors)
        self.assertIn('OFFICIAL_HERMES_NOT_ATTESTED', errors)

    def test_status_doctor_identity_and_reload_require_fresh_hook(self):
        for action in ('status', 'doctor', 'wake', 'photo'):
            value = copy.deepcopy(capture(self.expected))
            value['probes'][action]['runtime']['generation'] = '错误代次'
            self.assertIn(action.upper() + '_PROBE_FAILED', validate_probe(value, self.expected))
        value = capture(self.expected)
        value['hook_runtime'] = None
        self.assertIn('HOOK_REVALIDATION_REQUIRED', validate_probe(value, self.expected))

    def test_receipt_cannot_skip_prepare_or_trust_text(self):
        events = [{'state': state, 'operation_id': 'op-1', 'target': '本人测试目标',
                   'message_id': 'msg-1', 'receipt': '模型声称已送达'}
                  for state in ('GENERATED', 'PREPARED', 'SENT', 'ACKNOWLEDGED')]
        with self.assertRaises(ValueError):
            delivery_trace(events[2:])
        result = delivery_trace(events)
        self.assertEqual(result['state'], 'PREPARED')
        self.assertEqual(result['result'], 'UNVERIFIED_RECEIPT')
        result = delivery_trace(events, verify_receipt=lambda event: event['state'] == 'SENT')
        self.assertEqual(result['state'], 'SENT')
        self.assertEqual(delivery_trace(events, verify_receipt=lambda event: True)['state'], 'ACKNOWLEDGED')
        events[-1]['message_id'] = '另一条消息'
        with self.assertRaises(ValueError):
            delivery_trace(events, verify_receipt=lambda event: True)

    def test_sandbox_consistency_pass_never_unlocks_private_rp(self):
        self.assertEqual(validate_probe(capture(self.expected), self.expected), [])
        with self.assertRaises(DomainError):
            HostCapabilities().require_private_context_isolation()


class SandboxProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='life sandbox ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'installation'
        self.host = self.base / 'isolated profile'
        self.host.mkdir()
        self.cfg = defaults('sandbox')
        self.cfg['integration'].update(adapter='hermes', host_home=str(self.host))
        self.key = create_install(ROOT, self.root, self.cfg)['instance']
        reg = registry(self.root)
        self.expected = identity(self.root, reg, reg['instances'][self.key])

    def test_manager_report_fresh_processes_and_optional_photo(self):
        done = subprocess.run([sys.executable, '-X', 'utf8', str(self.root / 'manage.py'), 'sandbox',
                               '--instance', self.key], capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        result = json.loads(done.stdout)
        self.assertEqual(result['runtime'], self.expected)
        self.assertEqual(result['life_engine_restart'], 'PASS_FRESH_PROCESSES')
        self.assertEqual(result['photo'], 'DISABLED')
        self.assertEqual(result['host_probe_errors'], ['MISSING_ATTESTATION'])
        self.assertEqual(result['validation_result'], 'PENDING_REAL_HOST_VALIDATION')
        self.assertEqual(result['full_private_rp'], 'BLOCKED')

    def test_reload_comparison_and_generation_drift(self):
        probe = capture(self.expected)
        first = report(self.root, self.key, probe=probe, evidence_kind='simulated')
        probe['plugin_epoch'] = '模拟重新加载'
        second = report(self.root, self.key, probe=probe, previous=first, evidence_kind='simulated')
        self.assertEqual(second['reload_comparison'], 'NEW_PLUGIN_EPOCH_OBSERVED')
        self.assertEqual(second['host_probe_consistency'], 'PASS')
        self.assertEqual(second['validation_result'], 'PENDING_REAL_HOST_VALIDATION')
        self.cfg['social']['recent_chat_minutes'] = 80
        create_install(ROOT, self.root, self.cfg, reconfigure=True)
        changed = report(self.root, self.key, probe=probe, previous=second, evidence_kind='simulated')
        self.assertEqual(changed['runtime']['instance_id'], self.key)
        self.assertNotEqual(changed['runtime']['generation'], first['runtime']['generation'])
        self.assertEqual(changed['reload_comparison'], 'REVALIDATION_REQUIRED')
        self.assertEqual(changed['host_probe_consistency'], 'FAIL')
        self.assertEqual(changed['validation_result'], 'FAIL')

    def test_invalid_capture_is_failure_not_local_pass(self):
        result = report(self.root, self.key, probe={'format': '错误版本'})
        self.assertEqual(result['local_validation'], 'PASS')
        self.assertEqual(result['validation_result'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
