"""HLV4-R1: isolated Core authority and local intercept; never a Host/send test."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from pathlib import Path
import ast
import json
import os
import socket
import pickle
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from memory_fixture import MemoryFixture
import test_living_runtime as core
from life_engine.domain import (WorldScope, DomainId, IdKind, Provenance, SourceType,
    RealityStatus, CanonStatus, World, WorldKind, WorldStatus, WorldTimeline,
    WriterEpoch)
from life_engine.world_repository import WorldSnapshot
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime
from life_engine.living_domain import LivingContext, LivingError, fingerprint, canonical, scope_values
from life_engine.living_policy import policy
from life_engine.living_host_binding import BindingAuthority, RealDeliveryBindingFactory
from life_engine.living_host_facade import LivingHostFacade
from life_engine.living_real_delivery import (BindingMode, ExecutionPurpose, PolicyDecision,
    RealDeliveryPolicy, TrustedDeliveryTarget, RealDeliveryConsumer, SimulationConsumer)


class Allow(RealDeliveryPolicy):
    def decide(self, context):
        return PolicyDecision.ALLOW


class Explode(RealDeliveryPolicy):
    def decide(self, context):
        raise RuntimeError('policy failed')


class InvalidDecision(RealDeliveryPolicy):
    def decide(self, context):
        return True


class RealAuthorityTests(MemoryFixture, unittest.TestCase):
    op = core.LivingTests.op
    rev = core.LivingTests.rev
    follow = core.LivingTests.follow
    tick = core.LivingTests.tick
    reserve = core.LivingTests.reserve
    rows = core.LivingTests.rows
    fence_context = core.LivingTests.fence_context
    bump_world_revision = core.LivingTests.bump_world_revision

    def setUp(self):
        super().setUp()
        self.now = datetime(2026, 10, 4, 12, tzinfo=timezone.utc)
        self.scope = WorldScope(self.actor.owner_id, self.soul.soul_id,
            self.soul.soul_world_id, DomainId.new(IdKind.TIMELINE))
        prov = Provenance(SourceType.OWNER_COMMAND, 'R1 local fixture', self.now,
            self.actor, RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
        with self.world_repo.transaction() as tx:
            tx.add_world(WorldSnapshot(World(self.scope.world_id, self.scope.owner_id,
                self.scope.soul_id, WorldKind.SOUL, prov, WorldStatus.ACTIVE),
                WorldTimeline(self.scope, prov)))
        self.lr = LivingRepository(self.root, self.key, runtime_id=self.world_repo.runtime_id)
        self.ctx = LivingContext(self.actor, self.scope, self.lr.generation, 'r1-local')
        self.living = LivingRuntime(self.lr, clock=lambda: self.now)
        self.p = policy(quiet=[0, 0], cooldown=0, recent_inbound=60)
        self.seq = 0
        self.host_identity = 'R1:local:binding'
        self.target = TrustedDeliveryTarget('LOCAL', 'LOCAL_INTERCEPT', 'server', 'channel',
            str(self.actor.principal_id), 'profile', 'agent', self.host_identity)
        self.living.enroll(self.ctx, self.p, self.target.key, self.op())
        self.living.configure(self.ctx, self.rev(), self.op(), paused=False)
        self.session = self.fence_context().session
        self.directory = self.base / 'r1-authority'
        self.factory = RealDeliveryBindingFactory(Allow(), self.target)
        self.authority = self.open_authority(initialize=True)
        self.authority.set_mode('LIVING_PENDING')
        self.authority.set_mode('LIVING_ACTIVE')
        self.facade = LivingHostFacade(self.authority)
        self.consumer = RealDeliveryConsumer(self.authority)
        self.payload = 'R1 local validation text'

    def tearDown(self):
        self.authority.close()
        super().tearDown()

    def open_authority(self, initialize=False):
        return self.factory.create(self.living, self.directory, owner=self.actor,
            scope=self.scope, install_id='r1-local-install',
            host_identity=self.host_identity, producer='r1-local',
            initialize=initialize, isolated_test=True,
            test_key=b'R1 local deterministic isolated key!')

    def call(self, method, data, operation):
        e = self.authority.envelope('SESSION' if method == 'prepare_contact' else 'EXECUTOR',
            operation, session=self.session)
        cap = self.authority.issue(e, method, data)
        return getattr(self.facade, method)(e, cap, data)

    def claimed(self, *, grant=True):
        intent = self.reserve()
        self.call('prepare_contact', dict(intent_id=intent, material='R1 local',
            expected_revision=self.rev()), 'r1-prepare')
        if grant:
            self.factory.one_shot(self.authority, intent=intent, invocation='r1-claim',
                payload=self.payload)
        result = self.call('claim_attempt', dict(intent_id=intent,
            expected_revision=self.rev()), 'r1-claim')
        return intent, result

    def consume(self, original_intent, result, **changes):
        fields = dict(target=self.target, intent=original_intent,
            attempt=result.response['result']['attempt_id'], invocation='r1-claim',
            payload=self.payload)
        fields.update(changes)
        return self.consumer.intercept(result.permit, **fields)

    def reject(self, fn):
        with self.assertRaises(LivingError):
            fn()
        self.assertEqual(self.consumer.intercept_count, 0)

    def test_normal_replay_and_single_use(self):
        intent, result = self.claimed()
        self.assertTrue(result.response['result']['execute'])
        self.assertIsNotNone(result.permit)
        self.assertEqual(self.consume(intent, result), 'LOCAL_PRE_TRANSPORT_INTERCEPT')
        self.assertEqual(self.consumer.intercept_count, 1)
        with self.assertRaises(LivingError):
            self.consume(intent, result)
        replay = self.call('claim_attempt', dict(intent_id=intent,
            expected_revision=self.rev()), 'r1-claim')
        self.assertIsNone(replay.permit)
        self.assertFalse(replay.response['result']['execute'])
        self.assertEqual(self.consumer.intercept_count, 1)

    def test_default_and_policy_denials(self):
        intent, result = self.claimed(grant=False)
        self.assertIsNone(result.permit)
        self.assertTrue(result.response['result']['execute'])
        self.assertTrue(self.authority._reconcile)
        self.assertEqual(self.consumer.intercept_count, 0)

    def test_exception_policy_no_refund(self):
        self.factory.replace_policy(self.authority, Explode())
        intent, result = self.claimed()
        self.assertIsNone(result.permit)
        self.reject(lambda: self.factory.one_shot(self.authority, intent=intent,
            invocation='r1-claim', payload=self.payload))

    def test_unknown_policy_decision_denied(self):
        self.factory.replace_policy(self.authority, InvalidDecision())
        _, result = self.claimed()
        self.assertIsNone(result.permit)
        self.assertTrue(self.authority._reconcile)

    def test_grant_expiry_no_refund(self):
        intent = self.reserve()
        self.call('prepare_contact', dict(intent_id=intent, material='R1 local',
            expected_revision=self.rev()), 'r1-prepare')
        self.factory.one_shot(self.authority, intent=intent, invocation='r1-claim',
            payload=self.payload, ttl=1)
        self.now += timedelta(seconds=2)
        result = self.call('claim_attempt', dict(intent_id=intent,
            expected_revision=self.rev()), 'r1-claim')
        self.assertIsNone(result.permit)
        self.reject(lambda: self.factory.one_shot(self.authority, intent=intent,
            invocation='r1-claim', payload=self.payload))

    def test_wrong_fields_do_not_intercept(self):
        intent, result = self.claimed()
        self.reject(lambda: self.consume(intent, result, intent='wrong'))
        self.reject(lambda: self.consume(intent, result, attempt='wrong'))
        self.reject(lambda: self.consume(intent, result, invocation='wrong'))
        self.reject(lambda: self.consume(intent, result, payload='different'))
        wrong = TrustedDeliveryTarget('LOCAL', 'LOCAL_INTERCEPT', 'server', 'other',
            str(self.actor.principal_id), 'profile', 'agent', self.host_identity)
        self.reject(lambda: self.consume(intent, result, target=wrong))
        self.reject(lambda: self.consume(intent, result, target=None))
        self.reject(lambda: self.consume(intent, result, payload='@everyone'))
        self.assertEqual(self.consume(intent, result), 'LOCAL_PRE_TRANSPORT_INTERCEPT')

    def test_target_identity_and_unknown_policy_rejected(self):
        with self.assertRaises(LivingError):
            TrustedDeliveryTarget('LOCAL', 'LOCAL_INTERCEPT', 'server', '',
                str(self.actor.principal_id), 'profile', 'agent', self.host_identity)
        with self.assertRaisesRegex(LivingError, '^TARGET_AMBIGUOUS$'):
            TrustedDeliveryTarget('LOCAL', 'LOCAL_INTERCEPT', 'server', 'one,two',
                str(self.actor.principal_id), 'profile', 'agent', self.host_identity)
        other = TrustedDeliveryTarget('LOCAL', 'LOCAL_INTERCEPT', 'server', 'channel',
            'wrong-owner', 'profile', 'agent', self.host_identity)
        with self.assertRaises(LivingError):
            RealDeliveryBindingFactory(Allow(), other).create(self.living,
                self.base / 'wrong-owner', owner=self.actor, scope=self.scope,
                install_id='wrong', host_identity=self.host_identity,
                producer='r1-local', isolated_test=True)
        with self.assertRaises(LivingError):
            RealDeliveryBindingFactory(object(), self.target)

    def test_expiry_reload_policy_transition_and_restart(self):
        intent, result = self.claimed()
        self.now += timedelta(seconds=11)
        self.reject(lambda: self.consume(intent, result))
        self.now -= timedelta(seconds=11)
        self.authority.reload_plugin()
        self.reject(lambda: self.consume(intent, result))
        self.authority.close()
        self.authority = self.open_authority()
        self.consumer = RealDeliveryConsumer(self.authority)
        self.reject(lambda: self.consume(intent, result))

    def test_consumer_purpose_and_bool_flip(self):
        intent, result = self.claimed()
        self.reject(lambda: SimulationConsumer(self.authority).intercept(result.permit,
            target=self.target.key, attempt=result.response['result']['attempt_id'],
            invocation='r1-claim'))
        import life_engine.living_host_binding as binding
        original = binding.NO_REAL_SEND
        binding.NO_REAL_SEND = False
        try:
            self.reject(lambda: self.consume(intent, result, payload='changed'))
        finally:
            binding.NO_REAL_SEND = original
        self.assertEqual(self.consume(intent, result), 'LOCAL_PRE_TRANSPORT_INTERCEPT')

    def test_simulated_permit_cannot_enter_real_consumer(self):
        self.authority.close()
        self.authority = BindingAuthority(self.living, self.directory, owner=self.actor,
            scope=self.scope, install_id='r1-local-install',
            host_identity=self.host_identity, producer='r1-local',
            target=self.target.key, isolated_test=True,
            test_key=b'R1 local deterministic isolated key!')
        self.facade = LivingHostFacade(self.authority)
        self.consumer = RealDeliveryConsumer(self.authority)
        intent, result = self.claimed(grant=False)
        self.assertIsNotNone(result.permit)
        self.reject(lambda: self.consume(intent, result))
        self.assertEqual(SimulationConsumer(self.authority).intercept(result.permit,
            target=self.target.key, attempt=result.response['result']['attempt_id'],
            invocation='r1-claim'), 'LOCAL_SIMULATION_INTERCEPT')

    def test_nonisolated_default_cannot_claim_after_bool_flip(self):
        intent = self.reserve()
        self.call('prepare_contact', dict(intent_id=intent, material='R1 local',
            expected_revision=self.rev()), 'r1-prepare')
        self.authority.close()
        self.authority = BindingAuthority(self.living, self.base / 'nonisolated', owner=self.actor,
            scope=self.scope, install_id='r1-local-install',
            host_identity=self.host_identity, producer='r1-local',
            target=self.target.key, initialize=True, isolated_test=False)
        self.authority.set_mode('LIVING_PENDING')
        self.authority.set_mode('LIVING_ACTIVE')
        self.facade = LivingHostFacade(self.authority)
        self.consumer = RealDeliveryConsumer(self.authority)
        import life_engine.living_host_binding as binding
        original = binding.NO_REAL_SEND
        binding.NO_REAL_SEND = False
        try:
            self.reject(lambda: self.call('claim_attempt', dict(intent_id=intent,
                expected_revision=self.rev()), 'r1-claim'))
        finally:
            binding.NO_REAL_SEND = original

    def test_grant_and_permit_not_serializable(self):
        intent = self.reserve()
        grant = self.factory.one_shot(self.authority, intent=intent,
            invocation='r1-claim', payload=self.payload)
        with self.assertRaises(TypeError):
            pickle.dumps(grant)
        self.call('prepare_contact', dict(intent_id=intent, material='R1 local',
            expected_revision=self.rev()), 'r1-prepare')
        out = self.call('claim_attempt', dict(intent_id=intent,
            expected_revision=self.rev()), 'r1-claim')
        with self.assertRaises(TypeError):
            pickle.dumps(out.permit)

    def test_real_intercept_cannot_submit_sent(self):
        intent, result = self.claimed()
        self.consume(intent, result)
        envelope = self.authority.envelope('COLLECTOR', 'r1-delivery')
        data = dict(attempt_id=result.response['result']['attempt_id'],
            expected_revision=self.rev(), evidence_digest=fingerprint('fake'))
        cap = self.authority.issue(envelope, 'submit_delivery_result', data)
        with patch.object(self.living, 'record_delivery',
                          side_effect=AssertionError('Core delivery reached')):
            with self.assertRaisesRegex(LivingError, '^RECEIPT_UNVERIFIED$'):
                self.facade.submit_delivery_result(envelope, cap, data, None)
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'CLAIMED')

    def test_world_and_writer_fence_before_real_consume(self):
        intent, result = self.claimed()
        self.bump_world_revision()
        self.reject(lambda: self.consume(intent, result))

    def test_writer_epoch_fence_before_real_consume(self):
        intent, result = self.claimed()
        attempt = result.response['result']['attempt_id']
        self.authority._permit_sessions[attempt] = replace(self.session,
            writer_epoch=WriterEpoch(self.session.writer_epoch.value + 1))
        self.reject(lambda: self.consume(intent, result))

    def test_generation_transition_before_real_consume(self):
        from life_engine.durable import locked, registry, write
        intent, result = self.claimed()
        with locked(self.root, 'management'):
            data = registry(self.root)
            data['instances'][self.key]['generation'] = 'r1-new-generation'
            write(self.root / 'registry.json', data)
        self.reject(lambda: self.consume(intent, result))

    def test_target_transition_before_real_consume(self):
        intent, result = self.claimed()
        with self.authority.lifecycle_transition():
            self.living.configure(self.ctx, self.rev(), self.op(), target='r1-new-target')
            self.authority.update_target('r1-new-target')
        self.reject(lambda: self.consume(intent, result))

    def test_concurrent_consume(self):
        intent, result = self.claimed()
        start = threading.Barrier(3)
        def go():
            start.wait()
            try:
                return self.consume(intent, result)
            except LivingError:
                return 'REJECT'
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(go); second = pool.submit(go)
            start.wait()
            self.assertCountEqual([first.result(), second.result()],
                ['LOCAL_PRE_TRANSPORT_INTERCEPT', 'REJECT'])
        self.assertEqual(self.consumer.intercept_count, 1)

    def test_dependency_and_network_fence(self):
        files = [Path(__file__).parents[1] / 'runtime/life_engine' / name for name in
                 ('living_real_delivery.py', 'living_host_binding.py',
                  'living_host_facade.py')]
        forbidden = {'discord', 'telegram', 'wechat', 'httpx', 'requests', 'socket',
                     'gateway', 'hermes', 'openclaw'}
        for path in files:
            tree = ast.parse(path.read_text(encoding='utf-8'))
            roots = {node.module.split('.')[0] for node in ast.walk(tree)
                     if isinstance(node, ast.ImportFrom) and node.module}
            roots |= {alias.name.split('.')[0] for node in ast.walk(tree)
                      if isinstance(node, ast.Import) for alias in node.names}
            self.assertFalse(roots & forbidden)
        original_socket = socket.socket
        def deny(*args, **kwargs):
            raise AssertionError('R1_NETWORK_REACHED')
        socket.socket = deny
        try:
            intent, result = self.claimed()
            self.consume(intent, result)
        finally:
            socket.socket = original_socket
        self.assertEqual(self.consumer.intercept_count, 1)

    def test_default_simulation_and_missing_policy(self):
        self.authority.close()
        default = BindingAuthority(self.living, self.directory, owner=self.actor,
            scope=self.scope, install_id='r1-local-install',
            host_identity=self.host_identity, producer='r1-local',
            target=self.target.key, isolated_test=True,
            test_key=b'R1 local deterministic isolated key!')
        try:
            self.assertIs(default.execution_mode, BindingMode.SIMULATION)
            self.assertIsNone(default._real_policy)
            self.assertEqual(default._real_grants, {})
        finally:
            default.close()
        self.authority = self.open_authority()
        self.factory.replace_policy(self.authority, RealDeliveryPolicy())
        self.facade = LivingHostFacade(self.authority)
        intent, result = self.claimed()
        self.assertIsNone(result.permit)
        self.assertEqual(self.consumer.intercept_count, 0)

    def test_authority_restart_revokes_permit(self):
        intent, result = self.claimed()
        self.authority.close()
        old = result.permit
        self.authority = self.open_authority()
        self.consumer = RealDeliveryConsumer(self.authority)
        self.reject(lambda: self.consume(intent, result))
        self.assertIsNotNone(old)

    def test_grant_and_issue_concurrency(self):
        intent = self.reserve()
        self.call('prepare_contact', dict(intent_id=intent, material='R1 local',
            expected_revision=self.rev()), 'r1-prepare')
        start = threading.Barrier(3)
        def grant():
            start.wait()
            try:
                self.factory.one_shot(self.authority, intent=intent,
                    invocation='r1-claim', payload=self.payload)
                return 'GRANTED'
            except LivingError:
                return 'REJECT'
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(grant); b = pool.submit(grant); start.wait()
            self.assertCountEqual([a.result(), b.result()], ['GRANTED', 'REJECT'])
        start = threading.Barrier(3)
        def claim():
            start.wait()
            return self.call('claim_attempt', dict(intent_id=intent,
                expected_revision=self.rev()), 'r1-claim')
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(claim); b = pool.submit(claim); start.wait()
            results = [a.result(), b.result()]
        self.assertEqual(sum(out.permit is not None for out in results), 1)
        self.assertEqual(sum(out.response['result']['execute'] for out in results), 1)
        self.assertEqual(len(self.rows('living_attempts')), 1)

    def test_policy_transition_revokes_permit(self):
        intent, result = self.claimed()
        self.factory.replace_policy(self.authority, RealDeliveryPolicy())
        self.reject(lambda: self.consume(intent, result))
        self.assertEqual(self.consumer.intercept_count, 0)

    def test_lifecycle_pause_rejects(self):
        intent, result = self.claimed()
        with self.authority.lifecycle_transition():
            self.living.configure(self.ctx, self.rev(), self.op(), paused=True)
        self.reject(lambda: self.consume(intent, result))

    def test_admission_and_transition_order(self):
        intent, result = self.claimed()
        entered = threading.Event(); release = threading.Event()
        original = self.authority._vault.consume
        def consume_vault(*args, **kwargs):
            value = original(*args, **kwargs)
            entered.set()
            if not release.wait(20):
                raise AssertionError('barrier timeout')
            return value
        self.authority._vault.consume = consume_vault
        def transition():
            if not entered.wait(20):
                raise AssertionError('barrier timeout')
            with self.authority.lifecycle_transition():
                pass
            return 'TRANSITIONED'
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(self.consume, intent, result)
            b = pool.submit(transition)
            self.assertTrue(entered.wait(20))
            release.set()
            self.assertEqual(a.result(), 'LOCAL_PRE_TRANSPORT_INTERCEPT')
            self.assertEqual(b.result(), 'TRANSITIONED')
        self.assertEqual(self.consumer.intercept_count, 1)

    def transition_wins(self, action):
        intent, result = self.claimed()
        start = threading.Barrier(3)
        finished = threading.Event()
        def transition():
            start.wait()
            try:
                action()
            finally:
                finished.set()
        def consume():
            start.wait()
            if not finished.wait(20):
                raise AssertionError('transition barrier timeout')
            try:
                self.consume(intent, result)
                return 'UNEXPECTED_INTERCEPT'
            except LivingError:
                return 'REJECT'
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(transition); b = pool.submit(consume)
            start.wait(); a.result()
            self.assertEqual(b.result(), 'REJECT')
        self.assertEqual(self.consumer.intercept_count, 0)

    def test_concurrent_consume_vs_plugin_reload(self):
        self.transition_wins(self.authority.reload_plugin)

    def test_concurrent_consume_vs_authority_restart(self):
        def restart():
            self.authority.close()
            self.authority = self.open_authority()
            self.consumer = RealDeliveryConsumer(self.authority)
        self.transition_wins(restart)

    def test_concurrent_consume_vs_target_transition(self):
        def target():
            with self.authority.lifecycle_transition():
                self.living.configure(self.ctx, self.rev(), self.op(), target='r1-new-target')
                self.authority.update_target('r1-new-target')
        self.transition_wins(target)

    def test_concurrent_consume_vs_generation_transition(self):
        from life_engine.durable import locked, registry, write
        def generation():
            with locked(self.root, 'management'):
                data = registry(self.root)
                data['instances'][self.key]['generation'] = 'r1-new-generation'
                write(self.root / 'registry.json', data)
        self.transition_wins(generation)

    def test_generation_barrier_after_session_precheck(self):
        from life_engine.durable import locked, registry, write
        intent, result = self.claimed()
        checked = threading.Event(); release = threading.Event()
        original = self.living.status
        def status(context):
            value = original(context)
            if context.session is not None:
                checked.set()
                if not release.wait(20):
                    raise AssertionError('generation barrier timeout')
            return value
        def transition():
            if not checked.wait(20):
                raise AssertionError('generation precheck timeout')
            with locked(self.root, 'management'):
                data = registry(self.root)
                data['instances'][self.key]['generation'] = 'r1-new-generation'
                write(self.root / 'registry.json', data)
            release.set()
        with patch.object(self.living, 'status', side_effect=status):
            with ThreadPoolExecutor(max_workers=2) as pool:
                a = pool.submit(self.consume, intent, result)
                b = pool.submit(transition)
                with self.assertRaisesRegex(LivingError, '^GENERATION_STALE$'):
                    a.result()
                b.result()
        self.assertEqual(self.consumer.intercept_count, 0)

    def test_concurrent_consume_vs_pause(self):
        def pause():
            with self.authority.lifecycle_transition():
                self.living.configure(self.ctx, self.rev(), self.op(), paused=True)
        self.transition_wins(pause)

    def crash_case(self, mode, expected_code):
        intent = self.reserve()
        self.call('prepare_contact', dict(intent_id=intent, material='R1 local',
            expected_revision=self.rev()), 'r1-prepare')
        config = dict(root=str(self.root), instance=self.key,
            runtime_id=self.lr.runtime_id, principal=str(self.actor.principal_id),
            scope=scope_values(self.scope), now=self.now.isoformat(),
            directory=str(self.directory), expected=self.rev(), intent=intent,
            session=dict(id=str(self.session.session_id),
                writer_epoch=self.session.writer_epoch.value,
                world_revision=self.session.world_revision.value),
            phase=str(self.base / ('r1-' + mode + '-phase.json')))
        path = self.base / ('r1-' + mode + '-config.json')
        path.write_text(canonical(config), encoding='utf-8')
        self.authority.close()
        run = subprocess.run([sys.executable, '-X', 'utf8',
            str(Path(__file__).with_name('hlv4_r1_crash_worker.py')),
            str(path), mode], capture_output=True, text=True, encoding='utf-8', timeout=40)
        self.assertEqual(run.returncode, expected_code, run.stderr)
        self.assertEqual(run.stdout, '')
        phase = json.loads(Path(config['phase']).read_text(encoding='utf-8'))
        self.assertEqual(phase['exit_code'], expected_code)
        self.assertEqual(phase['network_send'], 0)
        self.assertEqual(phase['transport_invocation'], 0)
        self.authority = self.open_authority()
        self.facade = LivingHostFacade(self.authority)
        self.consumer = RealDeliveryConsumer(self.authority)
        self.assertEqual(self.authority._real_grants, {})
        self.assertEqual(self.authority._real_issued, set())
        envelope = self.authority.envelope('RECOVERY', 'recover-' + mode)
        data = {'operation_id': 'r1-claim'}
        cap = self.authority.issue(envelope, 'recover_operation', data)
        recovered = self.facade.recover_operation(envelope, cap, data)
        self.assertEqual(recovered['result']['status'], 'COMMITTED')
        self.assertNotIn('"permit":', canonical(recovered))
        self.assertNotIn('"execute":', canonical(recovered))
        self.assertEqual(self.consumer.intercept_count, 0)
        self.assertEqual(len(self.rows('living_attempts')), 1)
        self.assertEqual(self.rows('living_attempts')[0]['state'], 'CLAIMED')

    def test_cr01_claimed_before_permit(self):
        self.crash_case('CR01', 80)

    def test_cr02_permit_before_guard(self):
        self.crash_case('CR02', 81)

    def test_cr03_guard_before_consume(self):
        self.crash_case('CR03', 82)

    def test_cr04_consume_intercept_before_result(self):
        self.crash_case('CR04', 83)


if __name__ == '__main__':
    unittest.main()
