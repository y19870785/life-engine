"""B1 synthetic Core recovery 验收；无 Host、token、transport 或真实发送。"""
from contextlib import closing, contextmanager
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from memory_fixture import MemoryFixture, d
import test_living_runtime as existing
from life_engine.domain import (World, WorldScope, WorldKind, WorldStatus, WorldTimeline,
    DomainId, IdKind, Provenance, SourceType, RealityStatus, CanonStatus, Principal)
from life_engine.world_repository import WorldSnapshot
from life_engine.living_domain import LivingContext, LivingError, fingerprint, canonical, scope_values
from life_engine.living_policy import policy
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime
from life_engine.living_recovery import (LivingRecoveryContext, RecoveryDelegation,
    OperationRecoveryRequest, PrepareRecoveryReceipt, ClaimRecoveryReceipt,
    query_operation_recovery)


class RecoveryTests(MemoryFixture, unittest.TestCase):
    op = existing.LivingTests.op
    enroll = existing.LivingTests.enroll
    rev = existing.LivingTests.rev
    follow = existing.LivingTests.follow
    tick = existing.LivingTests.tick
    reserve = existing.LivingTests.reserve
    rows = existing.LivingTests.rows
    fence_context = existing.LivingTests.fence_context
    bump_world_revision = existing.LivingTests.bump_world_revision
    process = existing.LivingTests.process

    def setUp(self):
        super().setUp()
        self.now = datetime(2026, 9, 28, 12, tzinfo=timezone.utc)
        self.scope = WorldScope(self.actor.owner_id, self.soul.soul_id, self.soul.soul_world_id,
                                DomainId.new(IdKind.TIMELINE))
        prov = Provenance(SourceType.OWNER_COMMAND, 'B1 synthetic', self.now, self.actor,
                           RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
        with self.world_repo.transaction() as tx:
            tx.add_world(WorldSnapshot(World(self.scope.world_id, self.scope.owner_id,
                self.scope.soul_id, WorldKind.SOUL, prov, WorldStatus.ACTIVE), WorldTimeline(self.scope, prov)))
        self.lr = LivingRepository(self.root, self.key, runtime_id=self.world_repo.runtime_id)
        self.ctx = LivingContext(self.actor, self.scope, self.lr.generation, 'test')
        self.living = LivingRuntime(self.lr, clock=lambda: self.now)
        self.p = policy(quiet=[0, 0], cooldown=0, recent_inbound=60)
        self.seq = 0
        self.enroll()
        self.reader = Principal(DomainId.new(IdKind.PRINCIPAL), self.actor.owner_id)
        self.delegation = RecoveryDelegation(self.actor, self.reader, self.actor, self.scope,
                    self.key, self.lr.generation, 'test', 'synthetic local Owner delegation')
        self.recovery = LivingRecoveryContext(self.reader, self.delegation)

    def request(self, action='prepare', payload=None, operation='prepare', **changes):
        args = dict(instance_id=self.key, generation=self.lr.generation, scope=self.scope,
                    producer='test', operation_id=operation, action=action,
                    expected_payload_digest=fingerprint([action, payload, scope_values(self.scope),
                                                         str(self.actor.principal_id)]))
        args.update(changes)
        return OperationRecoveryRequest(**args)

    def prepared(self):
        ident = self.reserve()
        self.material = '合成内容引用'
        self.prepared_result = self.living.prepare_intent(self.ctx, self.rev(), 'prepare', ident, self.material)
        return ident, self.request(payload=[ident, self.material])

    def claimed(self):
        ident, _ = self.prepared()
        self.claimed_result = self.living.begin_attempt(self.ctx, self.rev(), 'claim', ident)
        return ident, self.request('begin_attempt', ident, 'claim')

    def snapshot(self):
        with closing(sqlite3.connect(self.path)) as db:
            names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            return {name: db.execute('SELECT * FROM "'+name+'" ORDER BY rowid').fetchall() for name in names}

    def query(self, request, context=None):
        before = self.snapshot()
        # 回归门禁：不能把 mutation API 当 lookup，全部路径均做全表比较。
        with patch.object(self.living, '_command', side_effect=AssertionError('mutation forbidden')):
            try:
                result = self.living.query_operation_recovery(context or self.recovery, request)
                self.assertNotIn('"execute"', result.to_json())
                self.assertLessEqual(len(result.to_json().encode('utf-8')), 16384)
                return result
            finally:
                self.assertEqual(before, self.snapshot())

    def error(self, code, request, context=None):
        with self.assertRaisesRegex(LivingError, '^'+code+'$'):
            self.query(request, context)

    def alter_operation(self, request, **changes):
        """仅 corruption fixture，正式读取始终走 public API。"""
        with closing(sqlite3.connect(self.path)) as db:
            for field, value in changes.items():
                db.execute('UPDATE living_operations SET '+field+'=? WHERE operation_id=? AND producer=?',
                           (value, request.operation_id, request.producer))
            db.commit()

    def test_b1_01_absent_exact_identity(self):
        _, request = self.prepared()
        self.assertEqual(self.query(replace(request, operation_id='absent')).status, 'NOT_COMMITTED')
        other = replace(self.recovery, delegation=replace(self.delegation, producer='another'))
        out = self.query(replace(request, producer='another'), other)
        self.assertEqual(out.status, 'NOT_COMMITTED')
        self.assertIsNone(out.receipt)
        self.assertIsNone(out.attempt)

    def test_b1_02_prepare_typed_receipt(self):
        ident, request = self.prepared()
        out = self.query(request)
        self.assertEqual(out.status, 'COMMITTED')
        self.assertEqual(out.receipt, PrepareRecoveryReceipt(ident, self.prepared_result['revision']))
        self.assertEqual(out.receipt_digest, fingerprint(self.prepared_result))
        self.assertIsNone(out.attempt)

    def test_b1_03_claim_association_and_historical_state(self):
        _, request = self.claimed()
        out = self.query(request)
        self.assertIsInstance(out.receipt, ClaimRecoveryReceipt)
        self.assertEqual(out.receipt.attempt_id, self.claimed_result['attempt_id'])
        self.assertEqual(out.attempt.current_state, 'CLAIMED')
        self.assertEqual(out.receipt_digest, fingerprint(self.claimed_result))
        # 显式独立 lifecycle 恢复，不是 query 的副作用。
        self.process('restart', token='new')
        with closing(sqlite3.connect(self.path)) as db:
            runtime_id = db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()[0]
        self.lr = LivingRepository(self.root, self.key, runtime_id=runtime_id)
        self.living = LivingRuntime(self.lr, clock=lambda: self.now)
        out = self.query(request)
        self.assertEqual(out.receipt.historical_state, 'CLAIMED')
        self.assertEqual(out.attempt.current_state, 'UNKNOWN')
        self.assertEqual(out.receipt_digest, fingerprint(self.claimed_result))

    def test_b1_03_committed_blockers_without_attempt(self):
        ident, _ = self.prepared()
        self.living.configure(self.ctx, self.rev(), 'pause', paused=True)
        result = self.living.begin_attempt(self.ctx, self.rev(), 'blocked', ident)
        out = self.query(self.request('begin_attempt', ident, 'blocked'))
        self.assertEqual(out.status, 'COMMITTED')
        self.assertIsNone(out.attempt)
        self.assertIsNone(out.receipt.attempt_id)
        self.assertEqual(list(out.receipt.blockers), result['blockers'])
        self.assertEqual(self.rows('living_attempts'), [])

    def test_b1_03_broken_associations_fail_closed(self):
        ident, request = self.claimed()
        for column, value in [('id', 'missing'), ('root_id', 'wrong'), ('intent', 'wrong')]:
            with self.subTest(column=column):
                with closing(sqlite3.connect(self.path)) as db:
                    original = db.execute('SELECT '+column+' FROM living_attempts').fetchone()[0]
                    db.execute('UPDATE living_attempts SET '+column+'=?', (value,)); db.commit()
                self.error('STATE_CORRUPT', request)
                with closing(sqlite3.connect(self.path)) as db:
                    db.execute('UPDATE living_attempts SET '+column+'=?', (original,)); db.commit()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('UPDATE living_intents SET generation=? WHERE id=?', ('wrong', ident)); db.commit()
        self.error('STATE_CORRUPT', request)

    def test_b1_04_digest_action_canonical_and_actor(self):
        ident, request = self.prepared()
        self.error('IDEMPOTENCY_CONFLICT', replace(request, expected_payload_digest='0'*64))
        self.error('IDEMPOTENCY_CONFLICT', replace(request, action='begin_attempt'))
        self.error('INVALID_ARGUMENT', replace(request, action='enroll'))
        reordered = dict(reversed(list(asdict(request).items())))
        reordered['scope'] = self.scope
        self.assertEqual(self.query(OperationRecoveryRequest(**reordered)), self.query(request))
        self.assertEqual(fingerprint({'中文': '值', 'a': 1}), fingerprint({'a': 1, '中文': '值'}))
        self.assertNotEqual(self.reader, self.actor)
        wrong = fingerprint(['prepare', [ident, self.material], scope_values(self.scope), str(self.reader.principal_id)])
        self.error('IDEMPOTENCY_CONFLICT', replace(request, expected_payload_digest=wrong))
        bad = replace(self.recovery, delegation=replace(self.delegation, original_actor=self.reader))
        self.error('AUTHORIZATION_DENIED', request, bad)

    def test_b1_05_generation_and_restore(self):
        _, request = self.prepared()
        self.error('GENERATION_STALE', replace(request, generation='old'))
        backup = d.snapshot(self.root, d.registry(self.root), self.inst, reason='b1-synthetic')
        d.restore(self.root, self.key, backup)
        self.error('GENERATION_STALE', request)
        reg = d.registry(self.root)
        self.path = d.state_home(self.root, reg['instances'][self.key])/'agents/synthetic/life.db'
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM living_operations WHERE operation_id=?', ('prepare',)).fetchone()[0], 1)
            rid = db.execute("SELECT value FROM meta WHERE key='world_runtime_id'").fetchone()[0]
        self.lr = LivingRepository(self.root, self.key, runtime_id=rid)
        self.living = LivingRuntime(self.lr, clock=lambda: self.now)
        self.error('GENERATION_STALE', request)

    def test_b1_06_scope_producer_and_input_isolation(self):
        _, request = self.prepared()
        self.error('SCOPE_MISMATCH', replace(request, instance_id='wrong'))
        for attr, kind in [('owner_id', IdKind.OWNER), ('soul_id', IdKind.SOUL),
                           ('world_id', IdKind.WORLD), ('timeline_id', IdKind.TIMELINE)]:
            with self.subTest(attr=attr):
                self.error('SCOPE_MISMATCH', replace(request, scope=replace(self.scope, **{attr: DomainId.new(kind)})))
        self.error('AUTHORIZATION_DENIED', replace(request, producer='other'))
        for value in ('*', 'prefix*', '?', '', 'x'*513):
            self.error('INVALID_ARGUMENT', replace(request, operation_id=value))
        self.error('INVALID_ARGUMENT', 'prepare')
        self.error('INVALID_ARGUMENT', asdict(request))
        self.error('AUTHORIZATION_DENIED', request, self.ctx)
        self.error('AUTHORIZATION_DENIED', request, {'owner': str(self.actor.owner_id)})
        with self.assertRaises(TypeError):
            OperationRecoveryRequest(**{**request.__dict__, 'admin': True})

    def test_b1_06_current_world_and_root_authorization(self):
        _, request = self.prepared()
        # context 与 request 一同更换 Scope 也不能绕过数据库当前 Scope。
        bad_scope = replace(self.scope, timeline_id=DomainId.new(IdKind.TIMELINE))
        bad = replace(self.recovery, delegation=replace(self.delegation, scope=bad_scope))
        self.error('SCOPE_MISMATCH', replace(request, scope=bad_scope), bad)
        with self.world_repo.transaction() as tx:
            w = tx.get_world(self.scope.world_id)
            tx.save_world(replace(w, world=replace(w.world, status=WorldStatus.SUSPENDED,
                                                  revision=w.world.revision.next())), w.world.revision)
        self.error('SCOPE_MISMATCH', request)

    def test_b1_07_session_authorization_before_lookup(self):
        _, request = self.prepared()
        ctx = self.fence_context()
        self.assertEqual(self.query(request, ctx).status, 'COMMITTED')
        self.bump_world_revision()
        import life_engine.living_recovery as module
        with patch.object(module, '_project', side_effect=AssertionError('lookup before authorization')):
            self.error('WORLD_STALE', request, ctx)
            stale_writer = replace(ctx, session=replace(ctx.session, writer_epoch=ctx.session.writer_epoch.next()))
            self.error('SESSION_STALE', request, stale_writer)
        fresh = self.fence_context()
        self.assertEqual(self.query(request, fresh).status, 'COMMITTED')
        s = fresh.session
        self.world.exit(self.actor, self.scope.world_id, self.scope.timeline_id,
                        s.session_id, s.world_revision, s.writer_epoch)
        self.error('SESSION_STALE', request, fresh)
        self.assertEqual(self.query(request).status, 'COMMITTED')

    def test_b1_08_core_process_crash_before_association(self):
        ident, _ = self.prepared()
        ctx = self.fence_context()
        request = self.request('begin_attempt', ident, 'lost')
        self.process('claim-lost', token='lost', intent=ident, context=ctx, expected=self.rev())
        config = dict(root=str(self.root), instance=self.key, runtime_id=self.lr.runtime_id,
                      generation=self.lr.generation, scope=scope_values(self.scope),
                      actor=str(self.actor.principal_id), reader=str(self.reader.principal_id),
                      operation='lost', digest=request.expected_payload_digest, now=self.now.isoformat())
        path = self.base/'recovery.json'; path.write_text(canonical(config), encoding='utf-8')
        before = self.snapshot()
        child = subprocess.run([sys.executable, '-X', 'utf8', str(Path(__file__).with_name('living_recovery_process_fixture.py')),
                                str(path)], capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(child.returncode, 0, child.stderr)
        result = json.loads(child.stdout)
        self.assertEqual(result['status'], 'COMMITTED')
        self.assertEqual(result['attempt']['attempt_id'], self.rows('living_attempts')[0]['id'])
        self.assertNotIn('"execute"', child.stdout)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(len(self.rows('living_attempts')), 1)

    def test_b1_09_core_context_cannot_widen_privilege(self):
        _, request = self.prepared()
        for field, value in [('grantee', self.actor), ('producer', 'other'),
                             ('instance_id', 'other'), ('generation', 'old')]:
            with self.subTest(field=field):
                changed = replace(self.recovery, delegation=replace(self.delegation, **{field: value}))
                with self.assertRaises(LivingError): self.query(request, changed)
        foreign = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
        for field in ('owner_authority', 'grantee', 'original_actor'):
            with self.subTest(field=field):
                self.error('AUTHORIZATION_DENIED', request,
                           replace(self.recovery, delegation=replace(self.delegation, **{field: foreign})))
        self.error('AUTHORIZATION_DENIED', request, replace(self.recovery, delegation=self.ctx))
        before = self.snapshot()
        for method, args in [('prepare_intent', (self.rev(), 'forbidden', 'id', 'content')),
                             ('begin_attempt', (self.rev(), 'forbidden', 'id')),
                             ('tick', ('forbidden',)), ('configure', (self.rev(), 'forbidden')),
                             ('enroll', (self.p, 'synthetic', 'forbidden'))]:
            with self.subTest(method=method), self.assertRaisesRegex(LivingError, 'AUTHORIZATION_DENIED'):
                getattr(self.living, method)(self.recovery, *args)
        self.assertEqual(before, self.snapshot())

        with patch.object(self.living, 'delivery_validator') as validator:
            with self.assertRaisesRegex(LivingError, 'AUTHORIZATION_DENIED'):
                self.living.record_delivery(self.recovery, 0, 'forbidden', 'id', {})
            validator.verify.assert_not_called()

    def test_b1_10_corrupt_current_state_checksum(self):
        _, request = self.claimed()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE living_attempts SET state='UNKNOWN'"); db.commit()
        self.error('STATE_CORRUPT', request)

    def test_b1_10_corrupt_record_and_unknown_receipt_fields(self):
        _, request = self.prepared()
        original = next(r for r in self.rows('living_operations') if r['operation_id']=='prepare')
        for changes in ({'payload': '{'}, {'fingerprint': '0'*64}, {'receipt': '{'},
                        {'receipt_fingerprint': '0'*64}, {'revision': 9999}):
            with self.subTest(changes=changes):
                self.alter_operation(request, **changes)
                self.error('STATE_CORRUPT', request)
                self.alter_operation(request, **{k: original[k] for k in changes})
        receipt = json.loads(original['receipt']); receipt['secret'] = 'not allowed'
        self.alter_operation(request, receipt=canonical(receipt), receipt_fingerprint=fingerprint(receipt))
        self.error('STATE_CORRUPT', request)

    def test_b1_10_bounds_before_json_materialization(self):
        _, request = self.prepared()
        for value in ('A'*64, '0'*63, '0'*65):
            self.error('INVALID_ARGUMENT', replace(request, expected_payload_digest=value))
        self.error('INVALID_ARGUMENT', replace(request, operation_id='中'*171))
        self.assertEqual(self.query(replace(request, operation_id='é'*256)).status, 'NOT_COMMITTED')
        oversized = replace(request, instance_id='\x00'*512, generation='\x00'*512,
                             producer='\x00'*512, operation_id='\x00'*512)
        self.error('BUDGET_INPUT', oversized)
        original = next(r for r in self.rows('living_operations') if r['operation_id']=='prepare')
        import life_engine.living_recovery as module
        for field in ('payload', 'receipt'):
            self.alter_operation(request, **{field: ' '*8193})
            with patch.object(module, '_json', side_effect=AssertionError('materialized oversized JSON')):
                self.error('BUDGET_INPUT', request)
            self.alter_operation(request, **{field: original[field]})
        # 边界处允许合法 JSON 的 padding；digest 仍按 canonical 值计算。
        padded = original['receipt']+' '*(8192-len(original['receipt'].encode('utf-8')))
        self.alter_operation(request, receipt=padded)
        self.assertEqual(self.query(request).status, 'COMMITTED')
        with patch.object(module, 'RESPONSE_LIMIT', 1):
            self.error('BUDGET_INPUT', request)

    def test_b1_10_readonly_connection_and_consistent_snapshot(self):
        _, request = self.claimed()
        before = self.snapshot()
        with self.lr.recovery_read_transaction() as db:
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('UPDATE living_roots SET revision=revision+1')
        self.assertEqual(before, self.snapshot())
        entered, release, writer_started = threading.Event(), threading.Event(), threading.Event()
        results, errors = [], []
        original = self.lr.recovery_read_transaction
        class BarrierConnection:
            def __init__(self, db): self.db = db
            def execute(self, sql, *args):
                if sql.startswith('SELECT a.id'):
                    # 此时 operation/receipt 已读取，Attempt association 尚未读取。
                    entered.set()
                    if not release.wait(10): raise AssertionError('reader timeout')
                return self.db.execute(sql, *args)
        @contextmanager
        def paused():
            with original() as db:
                yield BarrierConnection(db)
        def reader():
            try: results.append(self.living.query_operation_recovery(self.recovery, request))
            except BaseException as exc: errors.append(exc)
        def writer():
            try:
                writer_started.set()
                self.living.reconcile(self.ctx, self.rev(), 'parallel', evidence_ref='synthetic',
                                      blocked_until=self.now+timedelta(days=2))
            except BaseException as exc: errors.append(exc)
        with patch.object(self.lr, 'recovery_read_transaction', paused):
            a = threading.Thread(target=reader); a.start()
            self.assertTrue(entered.wait(10))
            b = threading.Thread(target=writer); b.start()
            self.assertTrue(writer_started.wait(10))
            self.assertEqual(before, self.snapshot())
            release.set(); a.join(15); b.join(15)
            self.assertFalse(a.is_alive() or b.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(results[0].living_revision, self.claimed_result['revision'])
        self.assertEqual(results[0].attempt.current_state, 'CLAIMED')
        self.assertEqual(self.rev(), self.claimed_result['revision']+1)
        after = self.query(request)
        self.assertEqual(after.living_revision, self.rev())
        self.assertEqual(after.attempt.current_state, 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
