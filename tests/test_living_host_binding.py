"""A3 B01–B34：隔离安装、可信本地 authority、SIMULATED/NO_REAL_SEND。"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from datetime import timedelta
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from memory_fixture import MemoryFixture
import test_living_runtime as core_tests
from life_engine.living_domain import LivingError, fingerprint, scope_values, canonical
from life_engine.living_host_binding import BindingAuthority, HostIdentityEnvelope
from life_engine.living_host_capability import Capability, ExecutionPermit
from life_engine.living_host_evidence import FakeEvidenceValidator, DeterministicFakeTransport
from life_engine.living_host_facade import LivingHostFacade

TEST_KEY = b'A3 deterministic isolated authority key'
PROVIDER_KEY = b'A3 deterministic isolated provider key'


class HostBindingTests(MemoryFixture, unittest.TestCase):
    op = core_tests.LivingTests.op
    enroll = core_tests.LivingTests.enroll
    rev = core_tests.LivingTests.rev
    follow = core_tests.LivingTests.follow
    tick = core_tests.LivingTests.tick
    reserve = core_tests.LivingTests.reserve
    rows = core_tests.LivingTests.rows
    fence_context = core_tests.LivingTests.fence_context
    bump_world_revision = core_tests.LivingTests.bump_world_revision

    def setUp(self):
        super().setUp()
        from datetime import datetime, timezone
        from life_engine.domain import (WorldScope, DomainId, IdKind, Provenance, SourceType,
            RealityStatus, CanonStatus, World, WorldKind, WorldStatus, WorldTimeline)
        from life_engine.world_repository import WorldSnapshot
        from life_engine.living_repository import LivingRepository
        from life_engine.living_runtime import LivingRuntime
        from life_engine.living_domain import LivingContext
        from life_engine.living_policy import policy
        self.now = datetime(2026, 9, 28, 12, tzinfo=timezone.utc)
        self.scope = WorldScope(self.actor.owner_id, self.soul.soul_id, self.soul.soul_world_id, DomainId.new(IdKind.TIMELINE))
        prov = Provenance(SourceType.OWNER_COMMAND, 'A3 synthetic', self.now, self.actor, RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
        with self.world_repo.transaction() as tx:
            tx.add_world(WorldSnapshot(World(self.scope.world_id, self.scope.owner_id, self.scope.soul_id, WorldKind.SOUL, prov, WorldStatus.ACTIVE), WorldTimeline(self.scope, prov)))
        self.lr = LivingRepository(self.root, self.key, runtime_id=self.world_repo.runtime_id)
        self.ctx = LivingContext(self.actor, self.scope, self.lr.generation, 'test')
        self.living = LivingRuntime(self.lr, clock=lambda: self.now)
        self.p = policy(quiet=[0, 0], cooldown=0, recent_inbound=60)
        self.seq = 0
        if self._testMethodName != 'test_b20_legacy_pending_explicit':
            self.enroll()
        self.session = self.fence_context().session
        self.directory = self.base / 'authority'
        self.authority = self.new_authority(initialize=True)
        if self._testMethodName != 'test_b20_legacy_pending_explicit':
            self.authority.set_mode('LIVING_PENDING')
            self.authority.set_mode('LIVING_ACTIVE')
        self.facade = LivingHostFacade(self.authority)
        self.validator = FakeEvidenceValidator(PROVIDER_KEY, self.key, self.lr.generation)
        self.living.delivery_validator = self.validator
        self.transport = DeterministicFakeTransport(self.authority, self.validator, self.base / 'fake-provider.jsonl')

    def tearDown(self):
        self.authority.close()
        super().tearDown()

    def new_authority(self, initialize=False, **changes):
        args = dict(owner=self.actor, scope=self.scope, install_id='isolated-install',
                    host_identity='FAKE:profile:gateway:config:agent:workspace', producer='test',
                    target='本人合成目标', initialize=initialize, isolated_test=True, test_key=TEST_KEY)
        args.update(changes)
        return BindingAuthority(self.living, self.directory, **args)

    def ticket(self, method, data, operation=None, **changes):
        from life_engine.living_host_binding import ROLES
        args = dict(session=self.session if method in ('query_context', 'prepare_contact', 'claim_attempt') else None,
                    provenance='EXTERNAL_USER' if method == 'observe_inbound' else 'LOCAL_TRUSTED')
        args.update(changes)
        envelope = self.authority.envelope(ROLES[method], operation or self.op(), **args)
        return envelope, self.authority.issue(envelope, method, data)

    def call(self, method, data=None, operation=None, *, evidence=None, **changes):
        data = {} if data is None else data
        envelope, token = self.ticket(method, data, operation, **changes)
        if evidence is not None:
            return getattr(self.facade, method)(envelope, token, data, evidence)
        return getattr(self.facade, method)(envelope, token, data)

    def prepared(self):
        ident = self.reserve()
        data = dict(intent_id=ident, material='合成内容引用', expected_revision=self.rev())
        self.call('prepare_contact', data, 'host-prepare')
        return ident

    def claimed(self):
        ident = self.prepared()
        outcome = self.call('claim_attempt', dict(intent_id=ident, expected_revision=self.rev()), 'host-claim')
        self.assertTrue(outcome.response['result']['execute'])
        return ident, outcome

    def sent(self):
        ident, outcome = self.claimed()
        attempt = outcome.response['result']['attempt_id']
        evidence = self.transport.send(outcome.permit, target='本人合成目标', attempt=attempt, invocation='host-claim')
        return ident, outcome, evidence

    def submit(self, evidence, operation='host-delivery'):
        data = dict(attempt_id=evidence.attempt_id, expected_revision=self.rev(),
                    evidence_digest=fingerprint(evidence.identity()))
        return self.call('submit_delivery_result', data, operation, evidence=evidence)

    def error(self, code, fn):
        with self.assertRaisesRegex(LivingError, '^' + code + '$'):
            fn()

    def business_snapshot(self):
        with closing(sqlite3.connect(self.path)) as db:
            names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'living_%'")]
            return {name: db.execute('SELECT * FROM ' + name + ' ORDER BY rowid').fetchall() for name in names}

    def restart(self):
        self.authority.close()
        self.authority = self.new_authority()
        self.facade = LivingHostFacade(self.authority)
        self.transport = DeterministicFakeTransport(self.authority, self.validator, self.base / 'fake-provider.jsonl')

    def child(self, mode, intent=None, operation='child-claim'):
        config = dict(root=str(self.root), instance=self.key, path=str(self.path),
            runtime_id=self.lr.runtime_id, principal=str(self.actor.principal_id), scope=scope_values(self.scope),
            now=self.now.isoformat(), directory=str(self.directory), expected=self.rev(), intent=intent,
            operation=operation, session=dict(id=str(self.session.session_id),
                writer_epoch=self.session.writer_epoch.value, world_revision=self.session.world_revision.value),
            journal=str(self.base / 'fake-provider.jsonl'))
        path = self.base / ('a3-' + mode + '.json')
        path.write_text(canonical(config), encoding='utf-8')
        self.authority.close()
        result = subprocess.run([sys.executable, '-X', 'utf8', str(Path(__file__).with_name('living_host_process_fixture.py')),
            str(path), mode], capture_output=True, text=True, encoding='utf-8', timeout=40)
        self.authority = self.new_authority()
        self.facade = LivingHostFacade(self.authority)
        self.transport = DeterministicFakeTransport(self.authority, self.validator, self.base / 'fake-provider.jsonl')
        return result

    def test_b01_duplicate_tick_concurrent(self):
        self.follow()
        def run(_):
            return self.call('tick', operation='same-tick')['result']
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(run, range(2)))
        self.assertEqual(results[0], results[1])
        with ThreadPoolExecutor(3) as pool:
            list(pool.map(lambda n: self.call('tick', operation='other-tick-' + str(n)), range(3)))
        self.assertEqual(len(self.rows('living_intents')), 1)
        self.assertEqual(len(self.rows('living_days')), 1)

    def test_b02_generation_stale(self):
        data = {}; e, token = self.ticket('tick', data)
        with patch.object(self.authority, '_generation', return_value='restored-generation'):
            self.error('GENERATION_STALE', lambda: self.facade.tick(e, token, data))
        self.assertEqual(self.rows('living_attempts'), [])

    def test_b03_install_instance_host_identity(self):
        self.authority.close()
        for changes in ({'install_id': 'copied-install'}, {'host_identity': 'wrong-profile'}):
            self.error('BINDING_MISMATCH', lambda: self.new_authority(**changes))
        import shutil
        original_directory = self.directory
        copied = self.base / 'copied-authority'
        shutil.copytree(original_directory, copied)
        self.directory = copied
        self.error('BINDING_MISMATCH', lambda: self.new_authority())
        self.directory = original_directory
        self.authority = self.new_authority(); self.facade = LivingHostFacade(self.authority)
        e, cap = self.ticket('tick', {})
        self.error('AUTHORIZATION_DENIED', lambda: self.facade.tick(replace(e, instance_id='wrong'), cap, {}))

    def test_b04_principal_provenance_forgery(self):
        e, cap = self.ticket('observe_inbound', dict(event_id='x', content_digest='0'*64, expected_revision=self.rev()))
        self.error('AUTHORIZATION_DENIED', lambda: self.facade.observe_inbound(replace(e, provenance='FORWARDED'), cap,
            dict(event_id='x', content_digest='0'*64, expected_revision=self.rev())))
        self.error('SESSION_STALE', lambda: self.authority.envelope('SESSION', 'x', session={'owner': 'model'}))
        self.assertEqual(self.rows('living_inbound'), [])

    def test_b05_wrong_closed_session(self):
        from life_engine.domain import DomainId, IdKind
        wrong = replace(self.session, session_id=DomainId.new(IdKind.SESSION))
        self.error('SessionNotFound', lambda: self.call('query_context', session=wrong))
        self.error('SESSION_STALE', lambda: self.authority.envelope('EXECUTOR', 'no-session'))
        self.assertIn(self.call('tick')['result']['result'], ('SILENT', 'RECOVERY_IN_PROGRESS'))

    def test_b06_world_fence_prepare_claim_replay(self):
        ident = self.prepared()
        from life_engine.domain import WriterEpoch
        stale_writer = replace(self.session, writer_epoch=WriterEpoch(self.session.writer_epoch.value + 1))
        self.error('SESSION_STALE', lambda: self.call('claim_attempt',
            dict(intent_id=ident, expected_revision=self.rev()), session=stale_writer))
        self.bump_world_revision()
        before = self.business_snapshot()
        prepare = dict(intent_id=ident, material='合成内容引用', expected_revision=self.rev())
        claim = dict(intent_id=ident, expected_revision=self.rev())
        self.error('WORLD_STALE', lambda: self.call('prepare_contact', prepare, 'host-prepare'))
        self.error('WORLD_STALE', lambda: self.call('claim_attempt', claim))
        self.assertEqual(before, self.business_snapshot())
        self.session = self.fence_context().session
        self.call('prepare_contact', prepare, 'host-prepare')
        result = self.call('claim_attempt', claim, 'claim-fresh')
        self.bump_world_revision()
        self.error('WORLD_STALE', lambda: self.call('claim_attempt', claim, 'claim-fresh'))
        self.assertEqual(len(self.rows('living_attempts')), 1)
        self.assertIsNotNone(result.permit)

    def test_b07_snapshot_revalidation(self):
        self.call('tick')
        result = self.call('query_context')['result']
        handle = result['context_handle']
        self.assertLessEqual(len(canonical(result['snapshot']).encode('utf-8')), 8192)
        self.now += timedelta(minutes=2)
        self.error('SNAPSHOT_STALE', lambda: self.call('query_context', {'handle': handle}))
        self.assertNotIn('seal', result)

    def test_b08_reload_old_request(self):
        e, token = self.ticket('claim_attempt', dict(intent_id='not-claimed', expected_revision=self.rev()))
        before = self.business_snapshot()
        self.authority.reload_plugin()
        self.error('CAPABILITY_STALE', lambda: self.facade.claim_attempt(e, token, dict(intent_id='not-claimed', expected_revision=self.rev())))
        self.assertEqual(before, self.business_snapshot())

    def test_b09_host_reload_preserves_business(self):
        self.reserve()
        before = self.business_snapshot(); generation = self.lr.generation
        self.authority.reload_plugin()
        self.assertEqual(before, self.business_snapshot())
        self.assertEqual(self.authority._generation(), generation)

    def test_b10_authority_restart_epochs(self):
        e, cap = self.ticket('tick', {})
        epoch = self.authority.binding_runtime_epoch
        before = self.business_snapshot()
        self.restart()
        self.assertNotEqual(epoch, self.authority.binding_runtime_epoch)
        self.error('CAPABILITY_STALE', lambda: self.facade.tick(e, cap, {}))
        self.assertEqual(before, self.business_snapshot())
        result = self.child('restart')
        self.assertEqual(result.returncode, 84, result.stderr)
        self.assertEqual(json.loads(result.stdout)['generation'], self.lr.generation)

    def test_b11_restore_generation_all_credentials(self):
        _, out = self.claimed()
        e, cap = self.ticket('recover_operation', {'operation_id': 'host-claim'})
        self.error('GENERATION_STALE', lambda: self.authority.envelope('SESSION', 'old-generation',
            session=replace(self.session, generation='old-generation')))
        # 独立 Core restore 用既有回归；这里验证 Host 读取 durable registry 而非缓存 generation。
        from life_engine.durable import registry
        reg = registry(self.root)
        reg['instances'][self.key]['generation'] = 'changed'
        with patch('life_engine.living_host_binding.registry', return_value=reg):
            self.error('GENERATION_STALE', lambda: self.facade.recover_operation(e, cap, {'operation_id': 'host-claim'}))
            self.error('GENERATION_STALE', lambda: self.transport.send(out.permit, target='本人合成目标',
                attempt=out.response['result']['attempt_id'], invocation='host-claim'))

    def test_b12_prepare_replay_conflict_concurrent(self):
        ident = self.reserve()
        data = dict(intent_id=ident, material='合成内容引用', expected_revision=self.rev())
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: self.call('prepare_contact', data, 'same-prepare'), range(2)))
        self.assertEqual(results[0], results[1])
        self.error('IDEMPOTENCY_CONFLICT', lambda: self.call('prepare_contact', {**data, 'material': 'changed'}, 'same-prepare'))
        self.error('INVALID_ARGUMENT', lambda: self.call('prepare_contact', {**data, 'material': '字'*200}))
        self.assertEqual(self.rows('living_intents')[0]['state'], 'PREPARED')
        self.assertEqual(self.rows('living_attempts'), [])

    def test_b13_claim_replay_concurrent(self):
        ident = self.prepared(); data = dict(intent_id=ident, expected_revision=self.rev())
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: self.call('claim_attempt', data, 'same-claim'), range(2)))
        self.assertEqual(sum(x.permit is not None for x in results), 1)
        self.assertEqual(sum(x.response['result']['execute'] for x in results), 1)
        next_result = self.call('claim_attempt', {**data, 'expected_revision': self.rev()}, 'new-claim')
        self.assertIsNone(next_result.permit)
        self.assertEqual(len(self.rows('living_attempts')), 1)

    def test_b14_process_commit_response_lost_recovery(self):
        ident = self.prepared()
        result = self.child('claim-lost', ident)
        self.assertEqual(result.returncode, 81, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(self.authority._associations, {})
        self.bump_world_revision()
        before = self.business_snapshot()
        with patch.object(self.living, 'begin_attempt', side_effect=AssertionError('no mutation probe')):
            recovered = self.call('recover_operation', {'operation_id': 'child-claim'})
        projected = recovered['result']
        self.assertEqual(projected['status'], 'COMMITTED')
        self.assertEqual(projected['receipt']['historical_state'], 'CLAIMED')
        self.assertEqual(projected['attempt']['attempt_id'], self.rows('living_attempts')[0]['id'])
        self.assertIn('child-claim', self.authority._associations)
        self.assertNotIn('"execute":', canonical(recovered)); self.assertNotIn('"permit":', canonical(recovered))
        self.assertEqual(before, self.business_snapshot())
        self.assertFalse(self.transport.journal.exists())

    def test_b15_process_claimed_and_sent_crashes(self):
        ident = self.prepared()
        result = self.child('claimed-crash', ident)
        self.assertEqual(result.returncode, 82, result.stderr)
        recovered = self.call('recover_operation', {'operation_id': 'child-claim'})
        self.assertEqual(recovered['result']['attempt']['current_state'], 'CLAIMED')
        self.assertFalse(self.transport.journal.exists())
        self.error('RECONCILIATION_REQUIRED', lambda: self.call('claim_attempt', dict(intent_id=ident, expected_revision=self.rev())))

    def test_b15_p4_fake_send_before_result_crash(self):
        ident = self.prepared()
        result = self.child('sent-crash', ident)
        self.assertEqual(result.returncode, 83, result.stderr)
        self.assertEqual(len(self.transport.journal.read_text(encoding='utf-8').splitlines()), 1)
        recovered = self.call('recover_operation', {'operation_id': 'child-claim'})
        self.assertEqual(recovered['result']['continuation'], 'RECONCILIATION_REQUIRED')
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'CLAIMED')
        self.assertEqual(self.rows('living_delivery_results'), [])
        self.error('CAPABILITY_STALE', lambda: self.transport.send(ExecutionPermit('lost'), target='本人合成目标',
            attempt=recovered['result']['attempt']['attempt_id'], invocation='child-claim'))

    def test_b16_sent_ack_are_distinct(self):
        _, _, sent = self.sent()
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'CLAIMED')
        self.submit(sent)
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'SENT')
        self.restart()
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'SENT')
        ack = self.transport.acknowledgement(sent)
        self.submit(ack, 'host-ack')
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'ACKNOWLEDGED')

    def test_b17_delivery_duplicate_submit_concurrent(self):
        _, _, sent = self.sent()
        data = dict(attempt_id=sent.attempt_id, expected_revision=self.rev(), evidence_digest=fingerprint(sent.identity()))
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: self.call('submit_delivery_result', data, 'same-delivery', evidence=sent), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(len(self.rows('living_delivery_results')), 1)
        self.assertEqual(len(self.rows('living_attempts')), 1)

    def test_b18_untrusted_delivery_conflict(self):
        _, _, sent = self.sent()
        self.error('RECEIPT_UNVERIFIED', lambda: self.submit(replace(sent, target='wrong')))
        data = dict(attempt_id=sent.attempt_id, expected_revision=self.rev(), evidence_digest='0'*64)
        self.error('RECEIPT_UNVERIFIED', lambda: self.call('submit_delivery_result', data, evidence={'state': 'SENT'}))
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'CLAIMED')
        self.submit(sent)
        conflicting = self.validator._attest(replace(sent, message_id='another-provider-message'))
        out = self.submit(conflicting, 'conflict-delivery')
        self.assertEqual(out['result']['state'], 'RECONCILIATION_REQUIRED')
        self.assertEqual(self.rows('living_attempts')[0]['message_id'], sent.message_id)

    def test_b19_all_legacy_paths_fenced(self):
        effects = []
        for name in ('context', 'wake', 'status', 'prepare', 'ack', 'observe', 'photo', 'loops', 'pause', 'resume'):
            self.error('LIVING_HANDOFF_REQUIRED', lambda: self.authority.route(lambda: effects.append(name)))
        self.assertEqual(effects, [])
        self.error('LIVING_HANDOFF_REQUIRED', lambda: self.authority.set_mode('LEGACY'))

    def test_b20_legacy_pending_explicit(self):
        self.authority.close()
        other = self.base / 'legacy-authority'
        self.directory = other
        self.authority = self.new_authority(initialize=True)
        effects = []
        self.authority.route(lambda: effects.append('legacy'))
        self.assertEqual(effects, ['legacy'])
        self.authority.set_mode('LIVING_PENDING')
        self.error('LIVING_HANDOFF_REQUIRED', lambda: self.authority.route(lambda: effects.append('bad')))

    def test_b21_rp_and_model_envelope_rejected(self):
        from life_engine.prompt import PromptPurpose
        self.error('UNSUPPORTED_PURPOSE', lambda: self.ticket('query_context', {}, session=replace(self.session, purpose=PromptPurpose.ROLEPLAY_RESPONSE)))
        self.error('AUTHORIZATION_DENIED', lambda: self.facade.tick({'owner': 'model'}, Capability('forged'), {}))
        with self.assertRaises(TypeError):
            HostIdentityEnvelope(**{**self.authority.envelope('SCHEDULER', 'x').__dict__, 'execute': True})

    def test_b22_no_real_send_preview(self):
        from life_engine.living_host_binding import NO_REAL_SEND
        self.assertTrue(NO_REAL_SEND)
        before = self.rows('living_attempts')
        self.call('tick'); self.call('status')
        self.assertEqual(before, self.rows('living_attempts'))
        self.assertFalse(self.transport.journal.exists())
        ident = self.prepared()
        self.authority._isolated_test = False
        self.error('NO_REAL_SEND', lambda: DeterministicFakeTransport(self.authority, self.validator, self.base / 'x'))
        self.error('NO_REAL_SEND', lambda: self.call('claim_attempt', dict(intent_id=ident, expected_revision=self.rev())))
        self.assertEqual(self.rows('living_attempts'), [])

    def test_b23_inbound_stable_identity(self):
        data = dict(event_id='external-1', content_digest=fingerprint('hello'), expected_revision=self.rev())
        first = self.call('observe_inbound', data)
        self.now += timedelta(seconds=1)
        second = self.call('observe_inbound', {**data, 'expected_revision': self.rev()})
        self.assertEqual(first['result'], second['result'])
        self.error('IDEMPOTENCY_CONFLICT', lambda: self.call('observe_inbound', {**data, 'content_digest': fingerprint('different')}))
        self.error('INBOUND_UNVERIFIED', lambda: self.call('observe_inbound', {**data, 'event_id': ''}))
        self.assertEqual(len(self.rows('living_inbound')), 1)

    def test_b24_quota_no_self_cooldown(self):
        self.p.update(daily_cap=1, rolling_cap=1, cooldown=9000, spacing=9000)
        self.living.configure(self.ctx, self.rev(), self.op(), policy=self.p)
        _, outcome = self.claimed()
        self.assertTrue(outcome.response['result']['execute'])
        self.follow()
        self.assertEqual(self.tick()['result'], 'SILENT')

    def test_b25_claim_target_change_concurrent(self):
        ident = self.prepared(); data = dict(intent_id=ident, expected_revision=self.rev())
        e, cap = self.ticket('claim_attempt', data, 'target-race')
        start = threading.Barrier(2)
        def claim():
            start.wait()
            try:
                return self.facade.claim_attempt(e, cap, data)
            except LivingError as exc:
                return exc.code
        def target_change():
            start.wait()
            with self.authority.lifecycle_transition():
                self.living.configure(self.ctx, self.rev(), self.op(), target='new-target')
                self.authority.update_target('new-target')
        with ThreadPoolExecutor(2) as pool:
            a, b = pool.submit(claim), pool.submit(target_change)
            result = a.result(); b.result()
        if type(result) is str:
            self.assertEqual(result, 'CAPABILITY_STALE')
        else:
            self.error('TARGET_MISMATCH', lambda: self.transport.send(result.permit,
                target='本人合成目标', attempt=result.response['result']['attempt_id'], invocation='target-race'))
        self.assertLessEqual(len(self.rows('living_attempts')), 1)
        self.assertFalse(self.transport.journal.exists())

    def test_b26_metadata_corruption_missing_single_writer(self):
        self.error('AUTHORITY_ALREADY_RUNNING', lambda: self.new_authority())
        path = self.authority._metadata.path
        saved = path.read_bytes()
        path.write_text('{"version":1,"data":', encoding='utf-8')
        self.error('BINDING_CORRUPT', lambda: self.call('tick'))
        path.write_bytes(saved)
        path.unlink()
        self.error('BINDING_MISSING', lambda: self.authority.route(lambda: self.fail('legacy side effect')))

    def test_b27_capability_method_expiry_consume_bounds(self):
        e, cap = self.ticket('tick', {})
        self.error('CAPABILITY_DENIED', lambda: self.facade.status(e, cap, {}))
        self.facade.tick(e, cap, {})
        self.error('CAPABILITY_STALE', lambda: self.facade.tick(e, cap, {}))
        e, cap = self.ticket('tick', {})
        self.now += timedelta(seconds=61)
        self.error('CAPABILITY_EXPIRED', lambda: self.facade.tick(e, cap, {}))
        self.error('INVALID_ARGUMENT', lambda: self.call('tick', {'generation': 'model'}))
        self.assertNotIn(cap._handle, repr(cap))

    def test_b28_lifecycle_and_core_race_fence(self):
        ident = self.prepared(); data = dict(intent_id=ident, expected_revision=self.rev())
        e, cap = self.ticket('claim_attempt', data)
        original = self.living.begin_attempt
        def interleaved(*args):
            self.bump_world_revision()
            return original(*args)
        with patch.object(self.living, 'begin_attempt', side_effect=interleaved):
            self.error('WORLD_STALE', lambda: self.facade.claim_attempt(e, cap, data))
        self.assertEqual(self.rows('living_attempts'), [])
        self.session = self.fence_context().session
        out = self.call('claim_attempt', data, 'current-claim')
        generation = self.lr.generation; before = self.business_snapshot()
        self.authority.reload_plugin()
        self.error('CAPABILITY_STALE', lambda: self.transport.send(out.permit, target='本人合成目标',
            attempt=out.response['result']['attempt_id'], invocation='current-claim'))
        self.assertEqual(self.lr.generation, generation)
        self.assertEqual(before, self.business_snapshot())
        self.restart()
        self.assertEqual(before, self.business_snapshot())

    def test_b29_gateway_config_identity_bound(self):
        self.authority.close()
        self.error('BINDING_MISMATCH', lambda: self.new_authority(host_identity='FAKE:profile:other-gateway:other-config:agent:workspace'))
        self.authority = self.new_authority(); self.facade = LivingHostFacade(self.authority)

    def test_b30_status_bounds_cursor(self):
        result = self.call('status')['result']
        self.assertLessEqual(len(result['intents']), 20)
        self.assertNotIn('raw_receipts', result)
        self.error('INVALID_ARGUMENT', lambda: self.call('status', {'limit': 101}))
        self.error('INVALID_ARGUMENT', lambda: self.call('status', {'limit': True}))
        self.error('CURSOR_STALE', lambda: self.call('status', {'cursor': dict(revision=0, binding_revision=0, offset=0)}))
        state = self.living.status(self.ctx)
        state['intents'] = [dict(id=str(n), state='PREPARED', reserved_at=1, expires=2,
                                 prepared='private material', raw_receipt='forbidden') for n in range(120)]
        with patch.object(self.living, 'status', return_value=state):
            page = self.call('status')['result']
            self.assertEqual(len(page['intents']), 20)
            next_page = self.call('status', {'limit': 100, 'cursor': page['cursor']})['result']
            self.assertEqual(len(next_page['intents']), 100)
            self.assertIsNone(next_page['cursor'])
            self.assertNotIn('private material', canonical(next_page))
            self.assertNotIn('raw_receipt', canonical(next_page))

    def test_b31_prompt_template_unchanged(self):
        from life_engine.prompt import TEMPLATE_VERSION
        from life_engine.world_schema import DATA_SCHEMA, SIGNATURE
        self.assertEqual(TEMPLATE_VERSION, 'SP-004K-prompt-v1')
        self.assertEqual(DATA_SCHEMA, 8)
        self.assertEqual(SIGNATURE, 'SP-005A-living-runtime-v1')
        self.call('tick')
        result = self.call('query_context')['result']
        self.assertEqual(result['origin'], 'STRUCTURED_ONLY')

    def test_b32_reload_claimed_requires_reconciliation(self):
        ident, out = self.claimed()
        self.authority.reload_plugin()
        self.error('RECONCILIATION_REQUIRED', lambda: self.call('claim_attempt', dict(intent_id=ident, expected_revision=self.rev())))
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'CLAIMED')
        self.assertEqual(self.call('recover_operation', {'operation_id': 'host-claim'})['result']['status'], 'COMMITTED')

    def test_b33_result_only_after_session_closed(self):
        _, _, evidence = self.sent()
        from life_engine.domain import BindingStatus
        with self.world_repo.transaction() as tx:
            w = tx.get_world(self.scope.world_id)
        self.world.exit(self.actor, self.scope.world_id, self.scope.timeline_id,
                        self.session.session_id, w.world.revision, w.world.writer_epoch)
        self.error('SESSION_STALE', lambda: self.call('query_context'))
        self.submit(evidence)
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'SENT')
        e, cap = self.ticket('submit_delivery_result', dict(attempt_id=evidence.attempt_id,
            expected_revision=self.rev(), evidence_digest=fingerprint(evidence.identity())))
        self.error('CAPABILITY_DENIED', lambda: self.facade.claim_attempt(e, cap, dict(intent_id='x', expected_revision=self.rev())))

    def test_b34_permit_duplicate_concurrent_and_revoked(self):
        _, out = self.claimed()
        attempt = out.response['result']['attempt_id']
        def send(_):
            try:
                return self.transport.send(out.permit, target='本人合成目标', attempt=attempt, invocation='host-claim').state
            except LivingError as exc:
                return exc.code
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(send, range(2)))
        self.assertCountEqual(results, ['SENT', 'CAPABILITY_STALE'])
        self.assertEqual(len(self.transport.journal.read_text(encoding='utf-8').splitlines()), 1)

    def test_b1_09_recovery_capability_never_execution(self):
        ident, _ = self.claimed()
        data = {'operation_id': 'host-claim'}; e, cap = self.ticket('recover_operation', data)
        self.error('CAPABILITY_DENIED', lambda: self.facade.claim_attempt(e, cap, dict(intent_id=ident, expected_revision=self.rev())))
        before = self.business_snapshot()
        result = self.facade.recover_operation(e, cap, data)
        self.assertEqual(before, self.business_snapshot())
        self.assertNotIn('"execute":', canonical(result)); self.assertNotIn('"permit":', canonical(result))
        e, cap = self.ticket('recover_operation', data)
        self.authority.reload_plugin()
        self.error('CAPABILITY_STALE', lambda: self.facade.recover_operation(e, cap, data))

    def test_capability_concurrent_consume_once(self):
        e, cap = self.ticket('tick', {})
        def run(_):
            try:
                return self.facade.tick(e, cap, {})['result']['result']
            except LivingError as exc:
                return exc.code
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(run, range(2)))
        self.assertEqual(results.count('CAPABILITY_STALE'), 1)

    def test_process_commit_before_exit_no_guess(self):
        ident = self.prepared()
        result = self.child('before-claim', ident)
        self.assertEqual(result.returncode, 80, result.stderr)
        recovered = self.call('recover_operation', {'operation_id': 'child-claim'})
        self.assertEqual(recovered['result']['status'], 'NOT_COMMITTED')
        self.assertEqual(self.rows('living_attempts'), [])

    def test_lifecycle_races_claim_reload_restart(self):
        ident = self.prepared(); data = dict(intent_id=ident, expected_revision=self.rev())
        e, cap = self.ticket('claim_attempt', data, 'race-claim')
        old = self.authority; facade = self.facade
        start = threading.Barrier(2)
        def claim():
            start.wait()
            try:
                return facade.claim_attempt(e, cap, data)
            except LivingError as exc:
                return exc.code
        def reload():
            start.wait(); old.reload_plugin()
        with ThreadPoolExecutor(2) as pool:
            a, b = pool.submit(claim), pool.submit(reload)
            outcome = a.result(); b.result()
        if type(outcome) is not str:
            self.error('CAPABILITY_STALE', lambda: self.transport.send(outcome.permit,
                target='本人合成目标', attempt=outcome.response['result']['attempt_id'], invocation='race-claim'))
        else:
            self.assertEqual(outcome, 'CAPABILITY_STALE')
        self.assertFalse(self.transport.journal.exists())
        # 新鲜 capability 与 authority close 真正并发；两种线性化顺序均无可恢复 permit。
        if self.rows('living_attempts'):
            self.call('recover_operation', {'operation_id': 'race-claim'})
        e, cap = self.ticket('recover_operation', {'operation_id': 'host-prepare'})
        start = threading.Barrier(2)
        def recovery():
            start.wait()
            try:
                return facade.recover_operation(e, cap, {'operation_id': 'host-prepare'})
            except LivingError as exc:
                return exc.code
        def close():
            start.wait(); old.close()
        with ThreadPoolExecutor(2) as pool:
            a, b = pool.submit(recovery), pool.submit(close)
            result = a.result(); b.result()
        if type(result) is str:
            self.assertEqual(result, 'AUTHORITY_CLOSED')
        else:
            self.assertEqual(result['result']['status'], 'COMMITTED')
        self.authority = self.new_authority(); self.facade = LivingHostFacade(self.authority)

    def test_recovery_reload_barrier_and_no_privilege_upgrade(self):
        self.claimed(); data = {'operation_id': 'host-claim'}
        e, cap = self.ticket('recover_operation', data)
        entered, release = threading.Event(), threading.Event()
        original = self.living.query_operation_recovery
        def query(*args):
            entered.set()
            if not release.wait(5):
                raise AssertionError('barrier timeout')
            return original(*args)
        with patch.object(self.living, 'query_operation_recovery', side_effect=query):
            with ThreadPoolExecutor(2) as pool:
                result = pool.submit(self.facade.recover_operation, e, cap, data)
                self.assertTrue(entered.wait(5))
                reloaded = pool.submit(self.authority.reload_plugin)
                self.assertFalse(reloaded.done())
                release.set()
                self.assertNotIn('"execute":', canonical(result.result()))
                reloaded.result()
        self.error('CAPABILITY_STALE', lambda: self.facade.recover_operation(e, cap, data))
        e, cap = self.ticket('recover_operation', data)
        for method, value in (('prepare_contact', dict(intent_id='x', material='x', expected_revision=self.rev())),
                ('submit_delivery_result', dict(attempt_id='x', evidence_digest='0'*64, expected_revision=self.rev()))):
            self.error('CAPABILITY_DENIED', lambda: self.authority._claims(e, method, value))
        self.error('CAPABILITY_DENIED', lambda: self.authority._issue_permit(e, dict(execute=True, state='CLAIMED', attempt_id='forged')))

    def test_permit_wrong_fields_expired_and_authority_restart(self):
        _, out = self.claimed(); attempt = out.response['result']['attempt_id']
        for values, code in ((dict(target='wrong', attempt=attempt, invocation='host-claim'), 'TARGET_MISMATCH'),
                (dict(target='本人合成目标', attempt='wrong', invocation='host-claim'), 'CAPABILITY_DENIED'),
                (dict(target='本人合成目标', attempt=attempt, invocation='wrong'), 'CAPABILITY_DENIED')):
            self.error(code, lambda: self.transport.send(out.permit, **values))
        self.now += timedelta(seconds=11)
        self.error('CAPABILITY_EXPIRED', lambda: self.transport.send(out.permit, target='本人合成目标', attempt=attempt, invocation='host-claim'))
        self.restart()
        self.error('CAPABILITY_STALE', lambda: self.transport.send(out.permit, target='本人合成目标', attempt=attempt, invocation='host-claim'))
        self.assertFalse(self.transport.journal.exists())

    def test_metadata_contains_only_identity_and_missing_cannot_reinitialize(self):
        self.claimed()
        meta = self.authority._data()
        for value in meta['correlations'].values():
            self.assertEqual(set(value), {'instance_id', 'generation', 'scope', 'producer', 'operation_id',
                'action', 'original_actor', 'expected_payload_digest'})
        raw = self.authority._metadata.path.read_text(encoding='utf-8')
        self.assertNotIn('CLAIMED', raw); self.assertNotIn('attempt_id', raw)
        self.authority._metadata.path.unlink()
        self.authority.close()
        self.error('BINDING_MISSING', lambda: self.new_authority(initialize=True))

    def test_response_and_envelope_bounds(self):
        from life_engine.living_host_facade import bounded
        self.error('BUDGET_INPUT', lambda: bounded({'result': 'x'*16385}))
        e, cap = self.ticket('tick', {})
        self.error('BUDGET_INPUT', lambda: self.authority._seal(replace(e, provenance='x'*8193)))
        self.error('BUDGET_INPUT', lambda: self.call('prepare_contact', dict(intent_id='x', material='x'*8193, expected_revision=self.rev())))

    def test_claim_authority_restart_race(self):
        ident = self.prepared(); data = dict(intent_id=ident, expected_revision=self.rev())
        e, cap = self.ticket('claim_attempt', data, 'restart-race')
        old = self.authority; facade = self.facade
        start = threading.Barrier(2)
        def claim():
            start.wait()
            try:
                return facade.claim_attempt(e, cap, data)
            except LivingError as exc:
                return exc.code
        def restart():
            start.wait(); old.close()
        with ThreadPoolExecutor(2) as pool:
            a, b = pool.submit(claim), pool.submit(restart)
            outcome = a.result(); b.result()
        self.authority = self.new_authority(); self.facade = LivingHostFacade(self.authority)
        self.transport = DeterministicFakeTransport(self.authority, self.validator, self.base / 'fake-provider.jsonl')
        if type(outcome) is str:
            self.assertEqual(outcome, 'AUTHORITY_CLOSED')
        else:
            self.error('CAPABILITY_STALE', lambda: self.transport.send(outcome.permit,
                target='本人合成目标', attempt=outcome.response['result']['attempt_id'], invocation='restart-race'))
        self.assertFalse(self.transport.journal.exists())

    def test_permit_generation_barrier_after_core_precheck(self):
        from life_engine.durable import locked, registry, write
        _, out = self.claimed(); attempt = out.response['result']['attempt_id']
        checked, release, locked_event = threading.Event(), threading.Event(), threading.Event()
        original = self.living.status
        def status(context):
            result = original(context)
            if context.session is None:
                return result
            checked.set()
            if not release.wait(5):
                raise AssertionError('barrier timeout')
            return result
        def send():
            try:
                self.transport.send(out.permit, target='本人合成目标', attempt=attempt, invocation='host-claim')
                return 'unexpected-send'
            except LivingError as exc:
                return exc.code
        def generation_transition():
            self.assertTrue(checked.wait(5))
            with locked(self.root, 'management'):
                # 只注入 registry generation transition；真实 durable restore 另由 A1/B1 覆盖。
                data = registry(self.root)
                data['instances'][self.key]['generation'] = 'restored-generation'
                write(self.root / 'registry.json', data)
                locked_event.set()
                release.set()
        with patch.object(self.living, 'status', side_effect=status):
            with ThreadPoolExecutor(2) as pool:
                a, b = pool.submit(send), pool.submit(generation_transition)
                self.assertEqual(a.result(), 'GENERATION_STALE')
                b.result()
        self.assertTrue(locked_event.is_set())
        self.assertFalse(self.transport.journal.exists())

    def test_owner_pause_revokes_unconsumed_execution(self):
        _, out = self.claimed(); attempt = out.response['result']['attempt_id']
        with self.authority.lifecycle_transition():
            self.living.configure(self.ctx, self.rev(), self.op(), paused=True)
        self.error('EXECUTION_REVOKED', lambda: self.transport.send(out.permit,
            target='本人合成目标', attempt=attempt, invocation='host-claim'))
        self.living.configure(self.ctx, self.rev(), self.op(), paused=False)
        self.error('CAPABILITY_STALE', lambda: self.transport.send(out.permit,
            target='本人合成目标', attempt=attempt, invocation='host-claim'))
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'CLAIMED')
        self.assertFalse(self.transport.journal.exists())
