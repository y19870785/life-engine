"""HLV3 TEST / VALIDATION ONLY. CI fixture evidence is SIMULATED_PASS.

The external live runner supplies authenticated process/Home/profile facts;
these tests never start a Gateway, manufacture inbound or register transport.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import hlv3_validation_support as support
from hlv3_validation_support import HLV3Fixture
from life_engine.living_domain import canonical, fingerprint, scope_values
from life_engine.living_host_capability import ExecutionPermit
from life_engine.durable import registry, write, locked


class HLV3ValidationTests(HLV3Fixture):
    def test_NORMAL_01(self):
        _, outcome = self.claimed()
        evidence = self.send(outcome)
        result = self.submit(evidence)
        self.assertEqual(len(self.rows('living_attempts')), 1)
        self.assertEqual(result['result']['state'], 'SENT')
        self.assertEqual(evidence.source, 'LOCAL_FAKE_SIMULATED')
        self.assertEqual((self.transport.attempt_count, self.transport.commit_count), (1, 1))
        self.assertNotIn('permit', json.loads(outcome.to_json()))

    def test_NORMAL_02(self):
        intent, first = self.claimed()
        self.send(first)
        again = self.call('claim_attempt', dict(intent_id=intent, expected_revision=self.rev()), 'claim')
        self.assertFalse(again.response['result']['execute'])
        self.assertIsNone(again.permit)
        self.assertEqual(len(self.rows('living_attempts')), 1)
        self.assertEqual(self.transport.commit_count, 1)

    def test_DUP_01(self):
        intent = self.reserve()
        data = dict(intent_id=intent, material='HLV3 合成内容引用', expected_revision=self.rev())
        a = self.call('prepare_contact', data, 'same-prepare')
        b = self.call('prepare_contact', data, 'same-prepare')
        self.assertEqual(a, b)
        self.reject('IDEMPOTENCY_CONFLICT', lambda: self.call('prepare_contact',
            {**data, 'material': '不同合成引用'}, 'same-prepare'))

    def test_DUP_02(self):
        intent = self.prepared()
        data = dict(intent_id=intent, expected_revision=self.rev())
        start = threading.Barrier(2)
        def claim():
            start.wait(timeout=10)
            return self.call('claim_attempt', data, 'concurrent-claim')
        with ThreadPoolExecutor(2) as pool:
            results = [future.result() for future in [pool.submit(claim), pool.submit(claim)]]
        self.assertEqual(sum(x.response['result']['execute'] for x in results), 1)
        self.assertEqual(sum(x.permit is not None for x in results), 1)
        self.assertEqual(len(self.rows('living_attempts')), 1)

    def test_DUP_03(self):
        _, outcome = self.claimed()
        start = threading.Barrier(2)
        def consume():
            start.wait(timeout=10)
            try:
                self.send(outcome)
                return 'COMMITTED_LOCAL_FAKE'
            except support.LivingError as exc:
                return exc.code
        with ThreadPoolExecutor(2) as pool:
            results = [future.result() for future in [pool.submit(consume), pool.submit(consume)]]
        self.assertCountEqual(results, ['COMMITTED_LOCAL_FAKE', 'CAPABILITY_STALE'])
        self.assertEqual(len(self.transport.journal.read_text().splitlines()), 1)

    def test_PERMIT_01(self):
        _, outcome = self.claimed()
        self.send(outcome)
        self.reject('CAPABILITY_STALE', lambda: self.send(outcome))
        self.assertEqual(self.transport.commit_count, 1)

    def wrong_permit(self, code, **changes):
        _, outcome = self.claimed()
        self.reject(code, lambda: self.send(outcome, **changes))
        self.assertFalse(self.transport.journal.exists())

    def test_PERMIT_02(self):
        self.wrong_permit('TARGET_MISMATCH', target='LOCAL_FAKE:wrong')

    def test_PERMIT_03(self):
        self.wrong_permit('CAPABILITY_DENIED', attempt='wrong-attempt')

    def test_PERMIT_04(self):
        self.wrong_permit('CAPABILITY_DENIED', invocation='wrong-invocation')

    def test_PERMIT_05(self):
        self.wrong_permit('CAPABILITY_DENIED', purpose='WRONG_PURPOSE')

    def test_PERMIT_06(self):
        _, outcome = self.claimed()
        self.restart_authority()
        self.reject('CAPABILITY_STALE', lambda: self.send(outcome))

    def stale_generation(self):
        with locked(self.root, 'management'):
            value = registry(self.root)
            value['instances'][self.key]['generation'] = 'HLV3-validation-new-generation'
            write(self.root / 'registry.json', value)

    def test_PERMIT_07(self):
        _, outcome = self.claimed()
        self.stale_generation()
        self.reject('GENERATION_STALE', lambda: self.send(outcome))

    def test_PERMIT_08(self):
        _, outcome = self.claimed()
        self.now += timedelta(seconds=11)
        self.reject('CAPABILITY_EXPIRED', lambda: self.send(outcome))
        self.assertFalse(self.transport.journal.exists())

    def test_PERMIT_09(self):
        _, outcome = self.claimed()
        with self.authority.lifecycle_transition():
            self.living.configure(self.ctx, self.rev(), self.op(), paused=True)
        self.reject('EXECUTION_REVOKED', lambda: self.send(outcome))
        self.assertFalse(self.transport.journal.exists())

    def crash(self, mode, exit_code):
        intent = self.prepared()
        cfg = dict(root=str(self.root), instance=self.key, runtime_id=self.lr.runtime_id,
            scope=scope_values(self.scope), principal=str(self.actor.principal_id),
            directory=str(self.directory), target=self.target, now=self.now.isoformat(),
            session=dict(id=str(self.session.session_id), writer_epoch=self.session.writer_epoch.value,
                         world_revision=self.session.world_revision.value), intent=intent,
            expected=self.rev(), journal=str(self.transport.journal), phase=str(self.base / 'phase.json'),
            host_fixture=self.gate.fixture)
        config = self.base / 'crash-config.json'
        config.write_text(canonical(cfg), encoding='utf-8')
        self.authority.close()
        # Allowlisted environment: no Host/provider credential is inherited.
        env = {k: v for k, v in os.environ.items() if k in
               ('PATH', 'HOME', 'USERPROFILE', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LANG', 'TZ')}
        env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
        child = subprocess.run([sys.executable, '-X', 'utf8', str(Path(__file__).with_name('hlv3_crash_worker.py')),
            str(config), mode], capture_output=True, text=True, encoding='utf-8', env=env, timeout=60)
        self.assertEqual(child.returncode, exit_code, child.stderr)
        self.assertEqual(child.stdout, '')
        phase = json.loads((self.base / 'phase.json').read_text())
        self.assertEqual(phase['exit_code'], exit_code)
        self.assertEqual(phase['real_transport_invocations'], 0)
        self.assertEqual(phase['network_attempts'], 0)
        self.authority = self.new_authority()
        self.bind_consumers()
        before = self.business_snapshot()
        recovered = self.call('recover_operation', {'operation_id': 'crash-claim'})
        self.assertEqual(before, self.business_snapshot())
        self.assertNotIn('"permit":', canonical(recovered))
        self.assertNotIn('"execute":', canonical(recovered))
        self.assertEqual((self.transport.attempt_count, self.transport.commit_count), (0, 0))
        return recovered, phase

    def test_CR_01(self):
        result, phase = self.crash('CR_01', 80)
        self.assertEqual(result['result']['status'], 'NOT_COMMITTED')
        self.assertEqual(self.rows('living_attempts'), [])
        self.assertFalse(self.transport.journal.exists())

    def test_CR_02(self):
        result, phase = self.crash('CR_02', 81)
        self.assertEqual(result['result']['status'], 'COMMITTED')
        self.assertEqual(result['result']['attempt']['current_state'], 'CLAIMED')
        self.assertIn('crash-claim', self.authority._associations)
        self.assertEqual(phase['permit_issued'], 0)
        self.assertFalse(self.transport.journal.exists())

    def recovered_claim(self):
        self.claimed()
        self.authority._associations.clear()
        self.restart_authority()
        before = self.business_snapshot()
        value = self.call('recover_operation', {'operation_id': 'claim'})
        self.assertEqual(before, self.business_snapshot())
        self.assertEqual(value['result']['status'], 'COMMITTED')
        self.assertIn('claim', self.authority._associations)
        self.assertNotIn('"permit":', canonical(value))
        self.assertNotIn('"execute":', canonical(value))
        self.assertEqual(len(self.rows('living_attempts')), 1)
        self.assertFalse(self.transport.journal.exists())
        return value

    def test_CR_03(self):
        self.recovered_claim()

    def test_CR_04(self):
        self.recovered_claim()
        data = {'operation_id': 'claim'}
        e, cap = self.ticket('recover_operation', data)
        self.reject('CAPABILITY_DENIED', lambda: self.authority._issue_permit(
            e, dict(execute=True, state='CLAIMED', attempt_id='forged')))

    def test_CR_05(self):
        self.recovered_claim()
        intent = self.rows('living_intents')[0]['id']
        self.reject('RECONCILIATION_REQUIRED', lambda: self.call('claim_attempt',
            dict(intent_id=intent, expected_revision=self.rev()), 'retry-history'))

    def test_CR_06(self):
        result, phase = self.crash('CR_06', 82)
        self.assertEqual(result['result']['attempt']['current_state'], 'CLAIMED')
        self.assertEqual(phase['permit_issued'], 1)
        self.assertFalse(any(kind is ExecutionPermit for kind, claims in self.authority._vault._entries.values()))
        self.assertFalse(self.transport.journal.exists())

    def test_CR_07(self):
        result, phase = self.crash('CR_07', 83)
        journal = self.transport.journal.read_bytes()
        self.assertEqual(len(journal.splitlines()), 1)
        self.assertEqual(json.loads(journal)['provider'], 'LOCAL_FAKE')
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'CLAIMED')
        self.assertEqual(self.rows('living_delivery_results'), [])
        self.assertEqual(result['result']['continuation'], 'RECONCILIATION_REQUIRED')
        self.call('recover_operation', {'operation_id': 'crash-claim'})
        self.assertEqual(journal, self.transport.journal.read_bytes())
        self.assertEqual(self.transport.commit_count, 0)

    def test_CR_08(self):
        _, outcome = self.claimed()
        evidence = self.send(outcome)
        self.submit(evidence)
        self.submit(evidence, 'delivery-duplicate')
        self.assertEqual(len(self.rows('living_delivery_results')), 1)
        original = self.rows('living_delivery_results')[0]
        changed = self.validator._attest(replace(evidence, provider_reference='LOCAL_FAKE:conflicting'))
        result = self.submit(changed, 'delivery-conflicting')
        self.assertEqual(result['result']['state'], 'RECONCILIATION_REQUIRED')
        self.assertEqual(self.rows('living_delivery_results')[0], original)
        self.assertEqual(self.transport.commit_count, 1)

    def test_CR_09(self):
        _, outcome = self.claimed()
        attempt = outcome.response['result']['attempt_id']
        evidence = self.validator._attest(support.DeliveryEvidence(self.key, self.lr.generation,
            attempt, self.target, 'UNKNOWN', 'LOCAL_FAKE_SIMULATED', 'local-uncertain',
            support.instant(self.now), 'LOCAL_FAKE:unknown'))
        self.assertEqual(self.submit(evidence)['result']['state'], 'UNKNOWN')
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'UNKNOWN')
        self.assertTrue(self.living.status(self.ctx)['root']['reconciliation'])
        self.assertFalse(self.transport.journal.exists())

    def test_CR_10(self):
        self.claimed()
        data = {'operation_id': 'claim'}
        # Both orders are explicitly synchronized at the validation binding barrier.
        e, cap = self.ticket('recover_operation', data)
        entered, release, transition_requested, transitioned = [threading.Event() for _ in range(4)]
        def recover_first():
            with self.gate.current():
                entered.set()
                self.assertTrue(release.wait(10))
                return self.facade.recover_operation(e, cap, data)
        def transition():
            transition_requested.set()
            self.gate.invalidate(self.authority)
            transitioned.set()
        with ThreadPoolExecutor(2) as pool:
            a = pool.submit(recover_first)
            self.assertTrue(entered.wait(10))
            b = pool.submit(transition)
            self.assertTrue(transition_requested.wait(10))
            self.assertFalse(transitioned.is_set())
            release.set()
            self.assertEqual(a.result()['result']['status'], 'COMMITTED')
            b.result()
        self.reject('HOST_LIFECYCLE_STALE', lambda: self.call('recover_operation', data))
        self.assertFalse(self.transport.journal.exists())

    def test_WRONG_OWNER(self):
        self.reject('VALIDATION_IDENTITY_DENIED', lambda: self.call('recover_operation',
            {'operation_id': 'nonexistent'}, identity={'owner': 'wrong-owner'}))
        self.reject('VALIDATION_IDENTITY_DENIED', lambda: self.call('claim_attempt',
            {'intent_id': 'nonexistent', 'expected_revision': 0}, identity={'owner': 'wrong-owner'}))

    def test_WRONG_CHANNEL(self):
        self.reject('VALIDATION_IDENTITY_DENIED', lambda: self.call('recover_operation',
            {'operation_id': 'nonexistent'}, identity={'channel': 'wrong-channel'}))
        self.reject('VALIDATION_IDENTITY_DENIED', lambda: self.call('claim_attempt',
            {'intent_id': 'nonexistent', 'expected_revision': 0}, identity={'channel': 'wrong-channel'}))

    def test_WRONG_PROFILE_AGENT(self):
        self.reject('VALIDATION_IDENTITY_DENIED', lambda: self.call('recover_operation',
            {'operation_id': 'nonexistent'}, identity={'profile': 'wrong-profile'}))
        self.reject('VALIDATION_IDENTITY_DENIED', lambda: self.call('claim_attempt',
            {'intent_id': 'nonexistent', 'expected_revision': 0}, identity={'profile': 'wrong-profile'}))

    def test_WORLD_REVISION_FENCE(self):
        intent = self.prepared()
        self.bump_world_revision()
        self.reject('WORLD_STALE', lambda: self.call('prepare_contact', dict(intent_id=intent,
            material='HLV3 合成内容引用', expected_revision=self.rev()), 'prepare'))
        self.reject('WORLD_STALE', lambda: self.call('claim_attempt',
            dict(intent_id=intent, expected_revision=self.rev()), 'world-stale-claim'))

    def test_WRITER_EPOCH_FENCE(self):
        intent = self.prepared()
        stale = replace(self.session, writer_epoch=self.session.writer_epoch.next())
        self.reject('SESSION_STALE', lambda: self.call('claim_attempt',
            dict(intent_id=intent, expected_revision=self.rev()), session=stale))

    def test_GENERATION_FENCE(self):
        intent, outcome = self.claimed()
        self.stale_generation()
        for method, data in [('claim_attempt', dict(intent_id=intent, expected_revision=0)),
                             ('recover_operation', {'operation_id': 'claim'})]:
            self.reject('GENERATION_STALE', lambda: self.call(method, data))
        self.reject('GENERATION_STALE', lambda: self.send(outcome))

    def test_RECOVERY_PRIVACY(self):
        self.claimed()
        before = self.business_snapshot()
        for operation in ['claim', 'absent-operation']:
            for key in ['owner', 'profile', 'channel', 'server', 'install']:
                self.reject('VALIDATION_IDENTITY_DENIED', lambda: self.call('recover_operation',
                    {'operation_id': operation}, identity={key: 'wrong-identity'}))
        envelope, capability = self.ticket('recover_operation', {'operation_id': 'claim'})
        self.restart_authority()
        for data in [{'operation_id': 'claim'}, {'operation_id': 'absent-operation'}]:
            self.reject('CAPABILITY_STALE', lambda: self.facade.recover_operation(envelope, capability, data))
        self.stale_generation()
        for operation in ['claim', 'absent-operation']:
            self.reject('GENERATION_STALE', lambda: self.call('recover_operation', {'operation_id': operation}))
        self.assertEqual(before, self.business_snapshot())

    def test_fake_transport_has_no_override_or_fallback_surface(self):
        _, outcome = self.claimed()
        for kwargs in [dict(metadata={'thread_id': 'wrong'}), dict(reply_to='wrong'),
                       dict(channel='wrong'), dict(url='wrong')]:
            with self.assertRaises(TypeError):
                self.send(outcome, **kwargs)
        self.assertFalse(self.transport.journal.exists())
        self.send(outcome)
        self.assertEqual(self.transport.commit_count, 1)
