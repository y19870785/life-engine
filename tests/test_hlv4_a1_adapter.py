"""A1 local-only contract tests; no Hermes Home, provider SDK or Gateway."""
import ast
import asyncio
from dataclasses import dataclass
import hashlib
import importlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import types
import unittest
from unittest.mock import patch

import test_hlv4_r1_authority as r1
from life_engine.living_domain import LivingError, canonical, scope_values
from life_engine.living_host_binding import BindingAuthority, RealDeliveryBindingFactory
from life_engine.living_host_facade import LivingHostFacade
from life_engine.living_real_delivery import (RealDeliveryConsumer, TrustedDeliveryTarget,
    validation_text)


@dataclass
class StubSendResult:
    success: bool
    message_id: str | None = None
    error: str | None = None
    retryable: bool = False


class StubBasePlatformAdapter:
    def __init__(self, config, platform):
        self.config, self.platform = config, platform


class StubRegistry:
    def __init__(self):
        self.entries = {}

    def get(self, name):
        return self.entries.get(name)


def import_with_exact_seam_fixture():
    registry = StubRegistry()
    gateway = types.ModuleType('gateway')
    config = types.ModuleType('gateway.config')
    config.Platform = lambda name: name
    platform_registry = types.ModuleType('gateway.platform_registry')
    platform_registry.platform_registry = registry
    platforms = types.ModuleType('gateway.platforms')
    base = types.ModuleType('gateway.platforms.base')
    base.BasePlatformAdapter = StubBasePlatformAdapter
    base.SendResult = StubSendResult
    stubs = {'gateway': gateway, 'gateway.config': config,
        'gateway.platform_registry': platform_registry,
        'gateway.platforms': platforms, 'gateway.platforms.base': base}
    with patch.dict(sys.modules, stubs):
        module = importlib.import_module('integrations.hermes_living.adapter')
    return module, registry


adapter_module, registry = import_with_exact_seam_fixture()
Adapter = adapter_module.LifeEngineDiscordAdapter


class StubPluginContext:
    def __init__(self):
        self.entries = []

    def register_platform(self, **kwargs):
        # Snapshot of the exact 0.21.3 PluginContext -> PlatformEntry seam.
        required = {'name', 'label', 'adapter_factory', 'check_fn'}
        allowed = required | {'max_message_length', 'cron_deliver_env_var',
            'send_message_handler', 'standalone_sender_fn', 'parse_target_ref_fn',
            'validate_target_ref_fn'}
        if not required <= kwargs.keys() or not kwargs.keys() <= allowed:
            raise TypeError('Hermes 0.21.3 platform contract mismatch')
        self.entries.append(kwargs)
        registry.entries[kwargs['name']] = kwargs
        return object()


class InertExactTransport:
    def __init__(self, *, result='LOCAL_INERT', error=None):
        self.calls = []
        self.result = result
        self.error = error

    async def invoke_exact(self, channel, payload):
        self.calls.append((channel, payload))
        if self.error:
            raise self.error
        return self.result


class AdapterContractTests(unittest.TestCase):
    def setUp(self):
        registry.entries.clear()
        self.adapter = Adapter(object(), transport=InertExactTransport())

    def test_a1_01_and_registration_has_no_side_entry(self):
        ctx = StubPluginContext()
        adapter_module.register(ctx)
        self.assertEqual(len(ctx.entries), 1)
        entry = ctx.entries[0]
        self.assertEqual(entry['name'], 'life_engine_discord')
        self.assertIs(entry['adapter_factory'], Adapter)
        for name in ('send_message_handler', 'standalone_sender_fn',
                     'parse_target_ref_fn', 'validate_target_ref_fn'):
            self.assertIsNone(entry[name])
        self.assertEqual(entry['cron_deliver_env_var'], '')
        self.assertEqual(entry['max_message_length'], 1024)
        self.assertIsInstance(entry['adapter_factory'](object()), StubBasePlatformAdapter)
        with self.assertRaises(LivingError):
            adapter_module.register(ctx)

    def test_a1_02_to_11_generic_surfaces_fail_closed(self):
        async def run():
            metadata = {'thread_id': 'evil', 'target': 'other',
                        'enable_real_send': True}
            cases = [
                self.adapter.send('last-route', 'hello', reply_to='reply', metadata=metadata),
                self.adapter.send_final_ledgered('event', 'session', 'hello', metadata, reply_to='reply'),
                self.adapter._send_with_retry(chat_id='other', content='hello'),
                self.adapter.send_draft('other', 1, 'hello'),
                self.adapter.send_multiple_images('other', [('x', 'y')]),
                self.adapter.send_image('other', 'http://inert.invalid/image'),
                self.adapter.send_animation('other', 'http://inert.invalid/animation'),
                self.adapter.send_voice('other', 'file'),
                self.adapter.send_video('other', 'file'),
                self.adapter.send_document('other', 'file'),
                self.adapter.send_image_file('other', 'file'),
                self.adapter.send_private_notice('other', None, 'hello'),
                self.adapter.send_exec_approval('other', 'cmd', 'session'),
                self.adapter.send_slash_confirm('other', 'x', 'y', 'z', 'id'),
                self.adapter.send_clarify('other', 'x', [], 'id', 'session'),
                self.adapter.edit_message('other', 'id', 'hello'),
            ]
            for case in cases:
                value = await case
                result = value[0] if isinstance(value, tuple) else value
                self.assertFalse(result.success)
                self.assertEqual(result.error, 'REAL_CONTACT_AUTHORITY_REQUIRED')
                self.assertFalse(result.retryable)
            for case in (self.adapter.send_typing('other'),
                         self.adapter.delete_message('other', 'id'),
                         self.adapter.create_handoff_thread('other', 'thread')):
                with self.assertRaises(LivingError):
                    await case
        asyncio.run(run())
        self.assertEqual(self.adapter._transport.calls, [])
        self.assertFalse(asyncio.run(Adapter(object()).connect()))

    def test_exact_hermes_0213_base_surface_snapshot(self):
        # Read-only source audit of SHA 01382698...; executable CI fixture checks
        # the adapter's explicit override list without importing Hermes itself.
        required = {'send', 'send_final_ledgered', '_send_with_retry', 'send_draft',
            'send_multiple_images', 'send_image', 'send_animation', 'send_voice',
            'send_video', 'send_document', 'send_image_file', 'send_private_notice',
            'send_exec_approval', 'send_slash_confirm', 'send_clarify', 'send_typing',
            'edit_message', 'delete_message', 'create_handoff_thread'}
        tree = ast.parse((Path(__file__).parents[1] /
            'integrations/hermes_living/adapter.py').read_text(encoding='utf-8'))
        cls = next(x for x in tree.body if isinstance(x, ast.ClassDef)
                   and x.name == 'LifeEngineDiscordAdapter')
        actual = {x.name for x in cls.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue(required <= actual)
        self.assertNotIn('DiscordAdapter', {base.id for base in cls.bases if isinstance(base, ast.Name)})
        self.assertEqual(self.adapter._transport.calls, [])

    def test_post_consume_path_is_single_fixed_invoke(self):
        adapter_tree = ast.parse((Path(__file__).parents[1] /
            'integrations/hermes_living/adapter.py').read_text(encoding='utf-8'))
        port = next(x for x in adapter_tree.body if isinstance(x, ast.ClassDef)
                    and x.name == '_ExactPort')
        invoke = next(x for x in port.body if isinstance(x, ast.AsyncFunctionDef)
                      and x.name == 'invoke_exact')
        self.assertEqual(len([x for x in ast.walk(invoke) if isinstance(x, ast.Await)]), 1)
        self.assertFalse(any(isinstance(x, (ast.For, ast.While, ast.Try))
                             for x in ast.walk(invoke)))
        calls = [x for x in ast.walk(invoke) if isinstance(x, ast.Call)]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].func.attr, 'invoke_exact')
        consumer_tree = ast.parse((Path(__file__).parents[1] /
            'runtime/life_engine/living_real_delivery.py').read_text(encoding='utf-8'))
        consumer = next(x for x in consumer_tree.body if isinstance(x, ast.ClassDef)
                        and x.name == 'RealDeliveryConsumer')
        deliver = next(x for x in consumer.body if isinstance(x, ast.AsyncFunctionDef)
                       and x.name == 'deliver_bound')
        self.assertEqual(len([x for x in ast.walk(deliver) if isinstance(x, ast.Await)]), 1)

    def test_network_dependency_fence(self):
        path = Path(__file__).parents[1] / 'integrations/hermes_living/adapter.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        imports = {node.module.split('.')[0] for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom) and node.module}
        imports |= {alias.name.split('.')[0] for node in ast.walk(tree)
                    if isinstance(node, ast.Import) for alias in node.names}
        self.assertFalse(imports & {'discord', 'httpx', 'requests', 'socket',
                                    'telegram', 'openclaw'})
        loop = asyncio.new_event_loop()
        try:
            with patch.object(socket.socket, 'connect', side_effect=AssertionError('NETWORK_REACHED')):
                loop.run_until_complete(self.adapter.send('other', 'hello'))
        finally:
            loop.close()
        self.assertEqual(self.adapter._transport.calls, [])


class RealAdapterAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.h = r1.RealAuthorityTests(methodName='runTest')
        self.h.setUp()
        h = self.h
        h.authority.close()
        h.target = TrustedDeliveryTarget('life_engine_discord', 'discord', 'server',
            'channel', str(h.actor.principal_id), 'profile', 'agent', h.host_identity)
        h.living.configure(h.ctx, h.rev(), h.op(), target=h.target.key)
        h.directory = h.base / 'a1-authority'
        h.factory = RealDeliveryBindingFactory(r1.Allow(), h.target)
        h.authority = h.open_authority(initialize=True)
        h.authority.set_mode('LIVING_PENDING')
        h.authority.set_mode('LIVING_ACTIVE')
        h.facade = LivingHostFacade(h.authority)
        h.consumer = RealDeliveryConsumer(h.authority)
        self.transport = InertExactTransport()
        self.adapter = Adapter(object(), transport=self.transport)
        self.identity = adapter_module.AdapterIdentity('profile', 'agent', 'fake-app',
            hashlib.sha256(b'fake-credential-identity').hexdigest())
        self.adapter.bind_trusted_host(h.authority, h.target, self.identity)
        self.assertTrue(asyncio.run(self.adapter.connect()))

    def tearDown(self):
        self.h.tearDown()

    def claimed(self):
        return self.h.claimed()

    def deliver(self, original_intent, result, **changes):
        h = self.h
        fields = dict(target=h.target, intent=original_intent,
            attempt=result.response['result']['attempt_id'], invocation='r1-claim',
            payload=h.payload)
        fields.update(changes)
        return asyncio.run(self.adapter.deliver_authorized_real_contact(result.permit, **fields))

    def test_a1_normal_replay_and_no_second_transport(self):
        intent, result = self.claimed()
        self.assertEqual(self.deliver(intent, result), 'LOCAL_INERT')
        self.assertEqual(self.transport.calls, [('channel', self.h.payload)])
        with self.assertRaises(LivingError):
            self.deliver(intent, result)
        replay = self.h.call('claim_attempt', dict(intent_id=intent,
            expected_revision=self.h.rev()), 'r1-claim')
        self.assertIsNone(replay.permit)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(self.h.rows('living_attempts')[0]['state'], 'CLAIMED')

    def test_a1_generic_send_stays_denied_after_real_binding(self):
        intent, result = self.claimed()
        for metadata in ({'thread_id': 'other'}, {'enable_real_send': True},
                         {'channel': 'other'}, None):
            response = asyncio.run(self.adapter.send('channel', self.h.payload,
                reply_to='other', metadata=metadata))
            self.assertFalse(response.success)
            self.assertEqual(response.error, 'REAL_CONTACT_AUTHORITY_REQUIRED')
        self.assertEqual(self.transport.calls, [])
        self.assertEqual(self.deliver(intent, result), 'LOCAL_INERT')
        self.assertEqual(len(self.transport.calls), 1)

    def test_a1_purpose_target_payload_and_oversize(self):
        intent, result = self.claimed()
        for changes in (dict(payload='changed'), dict(payload='x' * 1025),
                        dict(intent='wrong'), dict(invocation='wrong'),
                        dict(attempt='wrong'),
                        dict(target=TrustedDeliveryTarget('life_engine_discord', 'discord',
                            'server', 'wrong', self.h.target.owner, 'profile', 'agent',
                            self.h.host_identity)),
                        dict(target=TrustedDeliveryTarget('life_engine_discord', 'discord',
                            'wrong', 'channel', self.h.target.owner, 'profile', 'agent',
                            self.h.host_identity)),
                        dict(target=TrustedDeliveryTarget('life_engine_discord', 'discord',
                            'server', 'channel', 'wrong-owner', 'profile', 'agent',
                            self.h.host_identity))):
            with self.assertRaises(LivingError):
                self.deliver(intent, result, **changes)
        self.assertEqual(self.transport.calls, [])
        self.assertEqual(self.deliver(intent, result), 'LOCAL_INERT')

    def test_a1_stale_plugin_authority_and_credential(self):
        intent, result = self.claimed()
        self.h.authority.reload_plugin()
        with self.assertRaises(LivingError):
            self.deliver(intent, result)
        self.assertEqual(self.transport.calls, [])

    def test_a1_credential_rotation_revokes(self):
        intent, result = self.claimed()
        self.adapter.credential_identity_changed(hashlib.sha256(b'other-fake-id').hexdigest())
        with self.assertRaises(LivingError):
            self.deliver(intent, result)
        self.assertEqual(self.transport.calls, [])

    def test_a1_adapter_recreation_revokes(self):
        intent, result = self.claimed()
        asyncio.run(self.adapter.disconnect())
        replacement = Adapter(object(), transport=InertExactTransport())
        replacement.bind_trusted_host(self.h.authority, self.h.target, self.identity)
        self.assertTrue(asyncio.run(replacement.connect()))
        with self.assertRaises(LivingError):
            asyncio.run(replacement.deliver_authorized_real_contact(result.permit,
                target=self.h.target, intent=intent,
                attempt=result.response['result']['attempt_id'],
                invocation='r1-claim', payload=self.h.payload))
        self.assertEqual(self.transport.calls, [])

    def test_a1_application_rotation_revokes(self):
        intent, result = self.claimed()
        self.adapter.application_identity_changed('other-fake-app')
        with self.assertRaises(LivingError):
            self.deliver(intent, result)
        self.assertEqual(self.transport.calls, [])

    def test_a1_paused_core_and_target_transition(self):
        intent, result = self.claimed()
        with self.h.authority.lifecycle_transition():
            self.h.living.configure(self.h.ctx, self.h.rev(), self.h.op(), paused=True)
        with self.assertRaises(LivingError):
            self.deliver(intent, result)
        self.assertEqual(self.transport.calls, [])

    def test_a1_simulated_permit_cannot_enter_trusted_entry(self):
        h = self.h
        h.authority.close()
        h.authority = BindingAuthority(h.living, h.base / 'a1-simulation',
            owner=h.actor, scope=h.scope, install_id='a1-simulation',
            host_identity=h.host_identity, producer='r1-local',
            target=h.target.key, initialize=True, isolated_test=True,
            test_key=b'A1 local deterministic simulated key')
        h.authority.set_mode('LIVING_PENDING')
        h.authority.set_mode('LIVING_ACTIVE')
        h.facade = LivingHostFacade(h.authority)
        intent, result = h.claimed(grant=False)
        self.assertIsNotNone(result.permit)
        with self.assertRaises(LivingError):
            self.deliver(intent, result)
        other = Adapter(object(), transport=InertExactTransport())
        with self.assertRaises(LivingError):
            other.bind_trusted_host(h.authority, h.target, self.identity)
        self.assertEqual(self.transport.calls, [])

    def test_a1_transport_exception_and_unknown_do_not_retry(self):
        self.transport.error = RuntimeError('LOCAL_INERT_EXCEPTION')
        intent, result = self.claimed()
        with self.assertRaises(RuntimeError):
            self.deliver(intent, result)
        self.assertEqual(len(self.transport.calls), 1)
        with self.assertRaises(LivingError):
            self.deliver(intent, result)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(self.h.rows('living_attempts')[0]['state'], 'CLAIMED')

    def test_a1_unknown_result_is_not_sent_or_retried(self):
        self.transport.result = 'UNKNOWN'
        intent, result = self.claimed()
        self.assertEqual(self.deliver(intent, result), 'UNKNOWN')
        self.assertEqual(len(self.transport.calls), 1)
        with self.assertRaises(LivingError):
            self.deliver(intent, result)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(self.h.rows('living_attempts')[0]['state'], 'CLAIMED')

    def test_a1_recovery_does_not_authorize_adapter(self):
        intent, result = self.claimed()
        h = self.h
        envelope = h.authority.envelope('RECOVERY', 'a1-recovery')
        data = {'operation_id': 'r1-claim'}
        cap = h.authority.issue(envelope, 'recover_operation', data)
        recovered = h.facade.recover_operation(envelope, cap, data)
        self.assertEqual(recovered['result']['status'], 'COMMITTED')
        self.assertNotIn('permit', recovered['result'])
        self.assertNotIn('execute', recovered['result'])
        self.assertEqual(self.transport.calls, [])

    def test_a1_concurrent_same_permit(self):
        intent, result = self.claimed()
        gate = threading.Barrier(3)
        outcomes = []
        def worker():
            gate.wait()
            try:
                outcomes.append(self.deliver(intent, result))
            except LivingError:
                outcomes.append('REJECT')
        a = threading.Thread(target=worker); b = threading.Thread(target=worker)
        a.start(); b.start(); gate.wait(); a.join(); b.join()
        self.assertCountEqual(outcomes, ['LOCAL_INERT', 'REJECT'])
        self.assertEqual(len(self.transport.calls), 1)

    def test_a1_network_hard_deny_during_authorized_local_path(self):
        intent, result = self.claimed()
        loop = asyncio.new_event_loop()
        fields = dict(target=self.h.target, intent=intent,
            attempt=result.response['result']['attempt_id'], invocation='r1-claim',
            payload=self.h.payload)
        try:
            with patch.object(socket.socket, 'connect', side_effect=AssertionError('NETWORK_REACHED')):
                self.assertEqual(loop.run_until_complete(
                    self.adapter.deliver_authorized_real_contact(result.permit, **fields)),
                    'LOCAL_INERT')
        finally:
            loop.close()
        self.assertEqual(len(self.transport.calls), 1)

    def crash_case(self, mode, expected_code, expected_invocations):
        h = self.h
        intent = h.reserve()
        h.call('prepare_contact', dict(intent_id=intent, material='R1 local',
            expected_revision=h.rev()), 'r1-prepare')
        config = dict(root=str(h.root), instance=h.key,
            runtime_id=h.lr.runtime_id, principal=str(h.actor.principal_id),
            scope=scope_values(h.scope), now=h.now.isoformat(),
            directory=str(h.directory), expected=h.rev(), intent=intent,
            session=dict(id=str(h.session.session_id),
                writer_epoch=h.session.writer_epoch.value,
                world_revision=h.session.world_revision.value),
            phase=str(h.base / ('a1-' + mode + '-phase.json')))
        path = h.base / ('a1-' + mode + '-config.json')
        path.write_text(canonical(config), encoding='utf-8')
        h.authority.close()
        run = subprocess.run([sys.executable, '-X', 'utf8',
            str(Path(__file__).with_name('hlv4_a1_crash_worker.py')),
            str(path), mode], capture_output=True, text=True,
            encoding='utf-8', timeout=40)
        self.assertEqual(run.returncode, expected_code, run.stderr)
        self.assertEqual(run.stdout, '')
        phase = json.loads(Path(config['phase']).read_text(encoding='utf-8'))
        self.assertEqual(phase['exit_code'], expected_code)
        self.assertEqual(phase['network_send'], 0)
        self.assertEqual(phase['transport_invocation'], expected_invocations)
        h.authority = h.open_authority()
        h.facade = LivingHostFacade(h.authority)
        self.assertEqual(h.authority._real_grants, {})
        self.assertEqual(h.authority._real_issued, set())
        envelope = h.authority.envelope('RECOVERY', 'a1-recover-' + mode)
        data = {'operation_id': 'r1-claim'}
        cap = h.authority.issue(envelope, 'recover_operation', data)
        recovered = h.facade.recover_operation(envelope, cap, data)
        self.assertEqual(recovered['result']['status'], 'COMMITTED')
        self.assertNotIn('permit', recovered['result'])
        self.assertNotIn('execute', recovered['result'])
        self.assertEqual(self.transport.calls, [])
        self.assertEqual(h.rows('living_attempts')[0]['state'], 'CLAIMED')

    def test_a1_cr01_claimed_before_real_permit(self):
        self.crash_case('CR01', 90, 0)

    def test_a1_cr02_real_permit_before_guard(self):
        self.crash_case('CR02', 91, 0)

    def test_a1_cr03_guard_before_consume(self):
        self.crash_case('CR03', 92, 0)

    def test_a1_cr04_consumed_at_inert_boundary(self):
        self.crash_case('CR04', 93, 1)


if __name__ == '__main__':
    unittest.main()
