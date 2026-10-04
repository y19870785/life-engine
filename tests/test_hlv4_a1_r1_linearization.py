"""A1-R1 exact Host identity and deterministic lifecycle admission tests."""
import asyncio
from contextlib import contextmanager
import hashlib
import threading
import unittest

import test_hlv4_a1_adapter as a1
from life_engine.living_domain import LivingError
from life_engine.living_real_delivery import TrustedDeliveryTarget


class ExactIdentityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = a1.RealAdapterAdmissionTests(methodName='runTest')
        self.fixture.setUp()

    def tearDown(self):
        self.fixture.tearDown()

    def test_r1_07_correct_application_is_authority_projected(self):
        f = self.fixture
        self.assertIs(f.projection.authority, f.h.authority)
        self.assertIs(a1.adapter_module._PROJECTIONS[f.h.authority], f.projection)
        self.assertEqual(f.projection.expected.application, 'fake-app')
        intent, result = f.claimed()
        self.assertEqual(f.deliver(intent, result), 'LOCAL_INERT')

    def test_r1_08_wrong_application_initial_bind_denied(self):
        f = self.fixture
        wrong = a1.adapter_module.AdapterIdentity('profile', 'agent', 'wrong-app',
                                               f.identity.credential_digest)
        candidate = a1.Adapter(object(), transport=a1.InertExactTransport())
        with self.assertRaises(LivingError):
            candidate.bind_trusted_host(f.projection, wrong)
        with self.assertRaises(LivingError):
            a1.adapter_module.ProtectedDeliveryRegistry(f.h.target, wrong).project(f.h.authority)
        self.assertFalse(asyncio.run(candidate.connect()))
        self.assertEqual(candidate._transport.calls, [])

    def test_r1_09_missing_application_initial_bind_denied(self):
        f = self.fixture
        with self.assertRaises(LivingError):
            a1.adapter_module.AdapterIdentity('profile', 'agent', '',
                                           f.identity.credential_digest)
        candidate = a1.Adapter(object(), transport=a1.InertExactTransport())
        with self.assertRaises(LivingError):
            candidate.bind_trusted_host(f.projection, None)
        self.assertFalse(asyncio.run(candidate.connect()))

    def test_r1_10_observed_application_change_before_consume_denied(self):
        f = self.fixture
        intent, result = f.claimed()
        # Even direct corruption of the observed projection cannot replace the
        # authority-pinned application identity.
        f.adapter._identity = a1.adapter_module.AdapterIdentity('profile', 'agent',
            'wrong-app', f.identity.credential_digest)
        with self.assertRaises(LivingError):
            f.deliver(intent, result)
        self.assertEqual(f.transport.calls, [])


class LifecycleLinearizationTests(unittest.TestCase):
    """Each operation is run at three controlled points with fresh authority."""
    OPERATIONS = ('disconnect', 'plugin_reload', 'credential_rotation',
                  'application_rotation', 'adapter_recreation', 'target_transition')
    ADAPTER_LOCKED = {'disconnect', 'credential_rotation', 'application_rotation'}
    AUTHORITY_ONLY = {'plugin_reload', 'target_transition', 'adapter_recreation'}

    def _transition(self, f, operation):
        if operation == 'disconnect':
            asyncio.run(f.adapter.disconnect())
        elif operation == 'plugin_reload':
            f.h.authority.reload_plugin()
        elif operation == 'credential_rotation':
            f.adapter.credential_identity_changed(
                hashlib.sha256(b'rotated-fake-credential-identity').hexdigest())
        elif operation == 'application_rotation':
            f.adapter.application_identity_changed('rotated-fake-app')
        elif operation == 'adapter_recreation':
            replacement = a1.Adapter(object(), transport=a1.InertExactTransport())
            replacement.bind_trusted_host(f.projection, f.identity)
            self.assertTrue(asyncio.run(replacement.connect()))
        elif operation == 'target_transition':
            old = f.h.target
            changed = TrustedDeliveryTarget(old.platform, old.provider, old.server,
                'rotated-channel', old.owner, old.profile, old.agent, old.binding)
            with f.h.authority.lifecycle_transition():
                f.h.living.configure(f.h.ctx, f.h.rev(), f.h.op(), target=changed.key)
                f.h.authority.update_target(changed.key)
        else:
            raise AssertionError(operation)

    @staticmethod
    def _start_delivery(f, intent, result):
        outcome = []
        def deliver():
            try:
                outcome.append(f.deliver(intent, result))
            except LivingError:
                outcome.append('DENY')
            except BaseException as exc:
                outcome.append(exc)
        worker = threading.Thread(target=deliver, daemon=True)
        worker.start()
        return worker, outcome

    def _race(self, operation, stage):
        f = a1.RealAdapterAdmissionTests(methodName='runTest')
        f.setUp()
        worker = transition_worker = None
        release = threading.Event()
        try:
            intent, result = f.claimed()
            if stage == 'before_admission':
                lock = (f.adapter._lifecycle_lock if operation in self.ADAPTER_LOCKED
                        else f.h.authority._mutex)
                with lock:
                    worker, outcome = self._start_delivery(f, intent, result)
                    self._transition(f, operation)
                expected = 'DENY'
            else:
                arrived = threading.Event()
                if stage == 'after_admission':
                    port = f.adapter._consumer._port
                    original = port.execution_window
                    @contextmanager
                    def staged_window(*args):
                        with original(*args) as transport:
                            arrived.set()
                            if not release.wait(15):
                                raise AssertionError('admission barrier timed out')
                            yield transport
                    port.execution_window = staged_window
                elif stage == 'after_consume':
                    authority = f.h.authority
                    original = authority._consume_real_permit
                    @contextmanager
                    def staged_consume(*args, **kwargs):
                        with original(*args, **kwargs):
                            arrived.set()
                            if not release.wait(15):
                                raise AssertionError('consume barrier timed out')
                            yield
                    authority._consume_real_permit = staged_consume
                else:
                    raise AssertionError(stage)

                worker, outcome = self._start_delivery(f, intent, result)
                self.assertTrue(arrived.wait(15), 'delivery did not reach controlled point')
                # At both checkpoints the final Host lifecycle lease is held.
                self.assertFalse(f.adapter._lifecycle_lock.acquire(blocking=False))
                if stage == 'after_admission' and operation in self.AUTHORITY_ONLY:
                    # Authority-only transition wins before permit consume.
                    self._transition(f, operation)
                    expected = 'DENY'
                else:
                    started = threading.Event()
                    transition_outcome = []
                    def transition():
                        started.set()
                        try:
                            self._transition(f, operation)
                            transition_outcome.append('DONE')
                        except BaseException as exc:
                            transition_outcome.append(exc)
                    transition_worker = threading.Thread(target=transition, daemon=True)
                    transition_worker.start()
                    self.assertTrue(started.wait(15))
                    # The delivery lease bars adapter transitions; after
                    # consume the authority lock bars direct transitions too.
                    if stage == 'after_consume':
                        self.assertFalse(f.h.authority._mutex.acquire(blocking=False))
                    expected = 'LOCAL_INERT'
                release.set()

            worker.join(15)
            self.assertFalse(worker.is_alive(), 'delivery deadlocked')
            if transition_worker is not None:
                transition_worker.join(15)
                self.assertFalse(transition_worker.is_alive(), 'transition deadlocked')
                self.assertEqual(transition_outcome, ['DONE'])
            self.assertEqual(outcome, [expected])
            self.assertEqual(len(f.transport.calls), 1 if expected == 'LOCAL_INERT' else 0)
        finally:
            release.set()
            if worker is not None:
                worker.join(15)
            if transition_worker is not None:
                transition_worker.join(15)
            f.tearDown()

    def test_r1_01_delivery_vs_disconnect(self):
        for stage in ('before_admission', 'after_admission', 'after_consume'):
            with self.subTest(stage=stage):
                self._race('disconnect', stage)

    def test_r1_02_delivery_vs_plugin_reload(self):
        for stage in ('before_admission', 'after_admission', 'after_consume'):
            with self.subTest(stage=stage):
                self._race('plugin_reload', stage)

    def test_r1_03_delivery_vs_credential_rotation(self):
        for stage in ('before_admission', 'after_admission', 'after_consume'):
            with self.subTest(stage=stage):
                self._race('credential_rotation', stage)

    def test_r1_04_delivery_vs_application_rotation(self):
        for stage in ('before_admission', 'after_admission', 'after_consume'):
            with self.subTest(stage=stage):
                self._race('application_rotation', stage)

    def test_r1_05_delivery_vs_adapter_recreation(self):
        for stage in ('before_admission', 'after_admission', 'after_consume'):
            with self.subTest(stage=stage):
                self._race('adapter_recreation', stage)

    def test_r1_06_delivery_vs_target_transition(self):
        for stage in ('before_admission', 'after_admission', 'after_consume'):
            with self.subTest(stage=stage):
                self._race('target_transition', stage)

    def test_transport_reference_frozen_after_consume(self):
        f = a1.RealAdapterAdmissionTests(methodName='runTest')
        f.setUp()
        try:
            intent, result = f.claimed()
            old = f.transport
            replacement = a1.InertExactTransport()
            original = f.h.authority._consume_real_permit
            @contextmanager
            def replace_after_consume(*args, **kwargs):
                with original(*args, **kwargs):
                    f.adapter._transport = replacement
                    yield
            f.h.authority._consume_real_permit = replace_after_consume
            self.assertEqual(f.deliver(intent, result), 'LOCAL_INERT')
            self.assertEqual(len(old.calls), 1)
            self.assertEqual(replacement.calls, [])
        finally:
            f.tearDown()


if __name__ == '__main__':
    unittest.main()
