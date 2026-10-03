"""SP-005A4-HLV3 TEST / VALIDATION ONLY; never imported by production.

Host-owned identity is read from an external protected fixture. CI uses a marked
local fixture, while the live runner requires a current Linux Gateway process.
Neither variant registers a Hermes transport or accepts provider credentials.
"""
from contextlib import contextmanager, closing
from dataclasses import replace
from datetime import datetime, timezone
import importlib.abc
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
import unittest

from memory_fixture import MemoryFixture
import test_living_runtime as core
from life_engine.domain import (DomainId, IdKind, WorldScope, Provenance, SourceType,
                               RealityStatus, CanonStatus, World, WorldKind,
                               WorldStatus, WorldTimeline)
from life_engine.world_repository import WorldSnapshot
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime
from life_engine.living_domain import LivingContext, LivingError, fail, fingerprint, canonical, instant
from life_engine.living_policy import policy
from life_engine.living_host_binding import BindingAuthority, ROLES
from life_engine.living_host_capability import ExecutionPermit
from life_engine.living_host_facade import LivingHostFacade
from life_engine.living_host_evidence import DeliveryEvidence, FakeEvidenceValidator
from life_engine.durable import locked


class TransportFence(importlib.abc.MetaPathFinder):
    forbidden = ('discord', 'telegram', 'wechat', 'httpx', 'requests',
                 'gateway.delivery', 'gateway.delivery_ledger',
                 'plugins.platforms', 'gateway.run')

    def __init__(self):
        self.real_transport_invocations = 0
        self.network_attempts = 0
        self.enabled = True

    def find_spec(self, fullname, path=None, target=None):
        if self.enabled and any(fullname == name or fullname.startswith(name + '.') for name in self.forbidden):
            self.real_transport_invocations += 1
            raise RuntimeError('HLV3_REAL_TRANSPORT_UNREACHABLE')
        return None

    def audit(self, event, args):
        if self.enabled and event in ('socket.__new__', 'socket.connect', 'socket.sendto', 'socket.getaddrinfo'):
            self.network_attempts += 1
            raise RuntimeError('HLV3_NETWORK_HARD_DENY')

    def install(self):
        if any(any(name == prefix or name.startswith(prefix + '.') for prefix in self.forbidden)
               for name in sys.modules):
            raise RuntimeError('HLV3_REAL_TRANSPORT_ALREADY_REGISTERED')
        sys.meta_path.insert(0, self)
        sys.addaudithook(self.audit)
        return self


FENCE = None


def install_fence():
    global FENCE
    if FENCE is None:
        FENCE = TransportFence().install()
    FENCE.enabled = True
    return FENCE


class HostGate:
    """Validation binding layer, independent of A3/Core contract.

    Identity parameters have only one source: a protected registry fixture.
    Request overrides are comparisons, never authority inputs.
    """
    def __init__(self, fixture):
        self.fixture = fixture
        self._mutex = threading.RLock()
        self.active = True
        self.snapshot = self.read_current()

    @staticmethod
    def process(pid):
        root = Path('/proc') / str(pid)
        parts = (root / 'stat').read_text().rsplit(') ', 1)[1].split()
        env = dict(item.split('=', 1) for item in (root / 'environ').read_text().split('\0') if '=' in item)
        return int(parts[19]), env.get('HERMES_HOME')

    def read_current(self):
        cfg = self.fixture
        if cfg['source'] == 'CI_SYNTHETIC':
            return dict(cfg['identity'])
        if cfg['source'] != 'REAL_HOST_VALIDATION':
            fail('VALIDATION_IDENTITY_DENIED')
        home = Path(cfg['home'])
        state = json.loads((home / 'gateway_state.json').read_text())
        birth, actual_home = self.process(state['pid'])
        expected = cfg['identity']
        if (state['gateway_state'] != 'running' or birth != state['start_time']
                or actual_home != cfg['home'] or state['hermes_home'] != cfg['home']
                or expected['profile'] not in state.get('served_profiles', [])
                or state['platforms']['discord']['state'] != 'connected'):
            fail('HOST_LIFECYCLE_STALE')
        if (home / 'install_id').read_text().strip() != expected['install']:
            fail('HOST_IDENTITY_STALE')
        return {**expected, 'process': [state['pid'], birth]}

    @contextmanager
    def current(self, **request_identity):
        with self._mutex:
            if not self.active or self.read_current() != self.snapshot:
                fail('HOST_LIFECYCLE_STALE')
            if any(self.snapshot.get(key) != value for key, value in request_identity.items()):
                fail('VALIDATION_IDENTITY_DENIED')
            yield

    def invalidate(self, authority):
        with self._mutex:
            self.active = False
            authority.close()

    @property
    def persistent_digest(self):
        return fingerprint({k: v for k, v in self.snapshot.items() if k != 'process'})


class LocalFakeTransport:
    """Fake-only DI: no adapter/channel/URL/credential or generic router parameter."""
    provider = 'LOCAL_FAKE'

    def __init__(self, authority, gate, validator, journal):
        self.authority, self.gate, self.validator = authority, gate, validator
        self.journal = Path(journal)
        self.attempt_count = self.commit_count = 0

    def send(self, permit, *, target, attempt, invocation, purpose='SIMULATED_CONTACT', crash=None):
        self.attempt_count += 1
        with self.gate.current(), self.authority.consume_permit(
                permit, target=target, attempt=attempt, invocation=invocation, purpose=purpose):
            now = instant(self.authority.runtime.clock())
            event = fingerprint([attempt, invocation, target, 'HLV3_LOCAL_FAKE'])
            evidence = self.validator._attest(DeliveryEvidence(
                self.validator.instance_id, self.validator.generation, attempt, target,
                'SENT', 'LOCAL_FAKE_SIMULATED', event, now, 'LOCAL_FAKE:' + event,
                'local-fake-' + event, now))
            record = dict(provider=self.provider, journal_event_id=event, attempt_id=attempt,
                invocation_id=invocation, target_digest=fingerprint(target), purpose=purpose,
                permit_reference_digest=fingerprint(permit._handle), timestamp=now,
                evidence_digest=fingerprint(evidence.identity()), evidence=evidence.identity())
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            with locked(self.journal.parent, 'hlv3-journal'):
                with self.journal.open('ab') as handle:
                    handle.write((canonical(record) + '\n').encode())
                    handle.flush()
                    os.fsync(handle.fileno())
            self.commit_count += 1
            if crash is not None:
                crash('after_fake_journal_fsync_before_record_delivery')
            return evidence


def fixture():
    filename = os.environ.get('LIFE_ENGINE_HLV3_HOST_FIXTURE')
    if filename:
        return json.loads(Path(filename).read_text())
    return dict(source='CI_SYNTHETIC', identity=dict(install='validation-install',
        profile='validation-profile', owner='validation-owner', server='validation-server',
        channel='validation-channel', platform='LOCAL_FAKE', process=[0, 'synthetic-birth']))


class HLV3Fixture(MemoryFixture, unittest.TestCase):
    op = core.LivingTests.op
    rev = core.LivingTests.rev
    follow = core.LivingTests.follow
    tick = core.LivingTests.tick
    reserve = core.LivingTests.reserve
    rows = core.LivingTests.rows
    fence_context = core.LivingTests.fence_context
    bump_world_revision = core.LivingTests.bump_world_revision

    def setUp(self):
        install_fence()
        self.gate = HostGate(fixture())
        # Validate actual Host facts before any fixture/Core mutation.
        with self.gate.current():
            super().setUp()
        self.now = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)
        self.scope = WorldScope(self.actor.owner_id, self.soul.soul_id, self.soul.soul_world_id,
                               DomainId.new(IdKind.TIMELINE))
        prov = Provenance(SourceType.OWNER_COMMAND, 'VALIDATION_SESSION / NOT_REAL_INBOUND',
                          self.now, self.actor, RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
        with self.world_repo.transaction() as tx:
            tx.add_world(WorldSnapshot(World(self.scope.world_id, self.scope.owner_id,
                self.scope.soul_id, WorldKind.SOUL, prov, WorldStatus.ACTIVE), WorldTimeline(self.scope, prov)))
        self.lr = LivingRepository(self.root, self.key, runtime_id=self.world_repo.runtime_id)
        self.ctx = LivingContext(self.actor, self.scope, self.lr.generation, 'hlv3-validation')
        self.living = LivingRuntime(self.lr, clock=lambda: self.now)
        self.p = policy(quiet=[0, 0], cooldown=0, recent_inbound=60)
        self.seq = 0
        # Actual protected provider target becomes a digest, never a network target.
        self.target = 'LOCAL_FAKE:' + fingerprint([self.gate.snapshot['platform'],
            self.gate.snapshot['server'], self.gate.snapshot['channel']])
        self.living.enroll(self.ctx, self.p, self.target, self.op())
        self.living.configure(self.ctx, self.rev(), self.op(), paused=False)
        self.session = self.fence_context().session
        self.directory = self.base / 'validation-authority'
        self.authority = self.new_authority(initialize=True)
        self.addCleanup(lambda: self.authority.close())
        self.authority.set_mode('LIVING_PENDING')
        self.authority.set_mode('LIVING_ACTIVE')
        self.bind_consumers()

    def new_authority(self, initialize=False):
        with self.gate.current():
            return BindingAuthority(self.living, self.directory, owner=self.actor, scope=self.scope,
                install_id=self.gate.snapshot['install'], host_identity=self.gate.persistent_digest,
                producer=self.ctx.producer, target=self.target, initialize=initialize,
                isolated_test=True, test_key=b'HLV3 validation-only authority key!')

    def bind_consumers(self):
        self.facade = LivingHostFacade(self.authority)
        self.validator = FakeEvidenceValidator(b'HLV3 LOCAL_FAKE validation-only key!', self.key, self.lr.generation)
        self.living.delivery_validator = self.validator
        self.transport = LocalFakeTransport(self.authority, self.gate, self.validator, self.base / 'LOCAL_FAKE.jsonl')

    def ticket(self, method, data, operation=None, *, session=None):
        if session is None and method in ('prepare_contact', 'claim_attempt', 'query_context'):
            session = self.session
        envelope = self.authority.envelope(ROLES[method], operation or self.op(), session=session)
        return envelope, self.authority.issue(envelope, method, data)

    def call(self, method, data, operation=None, *, evidence=None, session=None, identity=None):
        with self.gate.current(**(identity or {})):
            e, cap = self.ticket(method, data, operation, session=session)
            fn = getattr(self.facade, method)
            return fn(e, cap, data) if evidence is None else fn(e, cap, data, evidence)

    def prepared(self):
        intent = self.reserve()
        self.call('prepare_contact', dict(intent_id=intent, material='HLV3 合成内容引用',
                  expected_revision=self.rev()), 'prepare')
        return intent

    def claimed(self):
        intent = self.prepared()
        outcome = self.call('claim_attempt', dict(intent_id=intent, expected_revision=self.rev()), 'claim')
        self.assertTrue(outcome.response['result']['execute'])
        self.assertIsInstance(outcome.permit, ExecutionPermit)
        return intent, outcome

    def send(self, outcome, **changes):
        values = dict(target=self.target, attempt=outcome.response['result']['attempt_id'], invocation='claim')
        values.update(changes)
        return self.transport.send(outcome.permit, **values)

    def submit(self, evidence, operation='delivery'):
        return self.call('submit_delivery_result', dict(attempt_id=evidence.attempt_id,
            expected_revision=self.rev(), evidence_digest=fingerprint(evidence.identity())),
            operation, evidence=evidence)

    def reject(self, code, action):
        with self.assertRaises(LivingError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)

    def business_snapshot(self):
        with closing(sqlite3.connect(self.path)) as db:
            names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'living_%'")]
            return {name: db.execute('SELECT * FROM ' + name + ' ORDER BY rowid').fetchall() for name in names}

    def restart_authority(self):
        self.authority.close()
        self.authority = self.new_authority()
        self.bind_consumers()

    def tearDown(self):
        self.authority.close()
        evidence_dir = os.environ.get('LIFE_ENGINE_HLV3_EVIDENCE_DIR')
        if evidence_dir:
            destination = Path(evidence_dir) / self._testMethodName
            destination.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(destination, 0o700)
            for source in [self.transport.journal, self.base / 'phase.json']:
                if source.exists():
                    path = destination / source.name
                    path.write_bytes(source.read_bytes())
                    os.chmod(path, 0o600)
            path = destination / 'durable-state.json'
            path.write_text(json.dumps(dict(host=self.gate.snapshot,
                business=self.business_snapshot(),
                real_transport=FENCE.real_transport_invocations,
                network_attempts=FENCE.network_attempts), default=str), encoding='utf-8')
            os.chmod(path, 0o600)
        try:
            self.assertEqual(FENCE.real_transport_invocations, 0)
            self.assertEqual(FENCE.network_attempts, 0)
        finally:
            FENCE.enabled = False
        super().tearDown()
