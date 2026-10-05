"""A2-R1 fake-only provider boundary tests. No Hermes Home or Discord token."""

import asyncio
from dataclasses import dataclass
import json
import socket
import threading
import unittest
from unittest.mock import patch

import test_hlv4_a1_adapter as a1
import test_hlv4_r1_authority as r1
from integrations.hermes_living.provider_ownership import (
    CredentialClaim, ProtectedCredentialInventory, DiscordRestOwnership,
    ProviderBoundaryError, RateLimitDomain)
from integrations.hermes_living.provider_transport import (
    OneShotDiscordTransport, FrozenUtf8TextJson, ProviderResultClass,
    AiohttpOneShotSessionFactory, ResolvedTextChannel,
    TrustedProviderTransportFactory, _AiohttpOneShotSession)
from life_engine.living_host_binding import RealDeliveryBindingFactory
from life_engine.living_host_facade import LivingHostFacade
from life_engine.living_real_delivery import TrustedDeliveryTarget


@dataclass
class FakeResponse:
    status: int
    body: bytes = b'{}'
    headers: dict = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class FakeSession:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []
        self.closed = False

    async def post_once(self, url, *, headers, data):
        self.calls.append((url, dict(headers), data))
        if not self.responses:
            raise ConnectionResetError('fake response lost')
        result = self.responses.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result

    async def close(self):
        self.closed = True


class FakeSessionFactory:
    def __init__(self, session=None):
        self.session = session or FakeSession()
        self.calls = 0

    def create(self, token):
        self.calls += 1
        return self.session


class FakeProtectedResolver:
    def __init__(self, *, channel_type='guild_text'):
        self.channel_type = channel_type
        self.calls = 0

    def resolve(self, target):
        self.calls += 1
        return ResolvedTextChannel(target.server, target.channel, 'fake-app',
                                   self.channel_type)


@dataclass
class PlatformConfig:
    token: str
    enabled: bool = True


def candidate(token='fake-token-A', platform='life_engine_discord', profile='test',
              owner='adapter-one'):
    return CredentialClaim(platform, profile, owner, token)


def ownership(claim, claims=None, session=None):
    factory = FakeSessionFactory(session)
    instance = DiscordRestOwnership.create(candidate=claim,
        inventory=ProtectedCredentialInventory(claims or [claim], complete=True),
        session_factory=factory, lifecycle=None)
    return instance, factory


class CredentialGateTests(unittest.TestCase):
    def test_official_platform_config_token_is_only_factory_source(self):
        factory = FakeSessionFactory()
        c = candidate('fake-token-A')
        with self.assertRaisesRegex(ProviderBoundaryError, 'CONFIG_REQUIRED'):
            TrustedProviderTransportFactory().create(PlatformConfig(c.token, False),
                profile=c.profile, adapter_owner=c.owner,
                inventory=ProtectedCredentialInventory([c], complete=True),
                resolver=FakeProtectedResolver(), session_factory=factory,
                application='fake-app')
        self.assertEqual(factory.calls, 0)
        transport = TrustedProviderTransportFactory().create(PlatformConfig(c.token),
            profile=c.profile, adapter_owner=c.owner,
            inventory=ProtectedCredentialInventory([c], complete=True),
            resolver=FakeProtectedResolver(), session_factory=factory,
            application='fake-app')
        self.assertEqual(factory.calls, 1)
        asyncio.run(transport._ownership.close())

    def test_complete_inventory_required_before_session(self):
        c = candidate()
        factory = FakeSessionFactory()
        with self.assertRaisesRegex(ProviderBoundaryError, 'UNPROVEN'):
            DiscordRestOwnership.create(candidate=c,
                inventory=ProtectedCredentialInventory([c]),
                session_factory=factory, lifecycle=None)
        self.assertEqual(factory.calls, 0)

    def test_cross_platform_profile_and_same_platform_duplicates(self):
        for other in (candidate(platform='discord'),
                      candidate(platform='other_plugin'),
                      candidate(profile='secondary'),
                      candidate(owner='adapter-two')):
            c = candidate()
            factory = FakeSessionFactory()
            with self.subTest(other=(other.platform, other.profile, other.owner)):
                with self.assertRaisesRegex(ProviderBoundaryError, 'DUPLICATE'):
                    DiscordRestOwnership.create(candidate=c,
                        inventory=ProtectedCredentialInventory([c, other], complete=True),
                        session_factory=factory, lifecycle=None)
                self.assertEqual(factory.calls, 0)

    def test_different_credential_does_not_collide(self):
        c = candidate()
        owner, factory = ownership(c, [c, candidate('fake-token-B', 'discord')])
        self.assertEqual(factory.calls, 1)
        asyncio.run(owner.close())

    def test_second_rest_owner_denied_until_first_closed(self):
        c = candidate()
        first, _ = ownership(c)
        first.revoke()
        second = candidate(owner='adapter-two')
        factory = FakeSessionFactory()
        with self.assertRaisesRegex(ProviderBoundaryError, 'SECOND_REST_OWNER'):
            DiscordRestOwnership.create(candidate=second,
                inventory=ProtectedCredentialInventory([second], complete=True),
                session_factory=factory, lifecycle=None)
        self.assertEqual(factory.calls, 0)
        asyncio.run(first.close())
        next_owner, _ = ownership(second)
        asyncio.run(next_owner.close())

    def test_secret_does_not_enter_repr_or_error(self):
        c = candidate('fake-token-secret')
        owner, _ = ownership(c)
        self.assertNotIn(c.token, repr(c))
        self.assertNotIn(c.token, repr(owner))
        asyncio.run(owner.close())


class RateLimitAndPayloadTests(unittest.TestCase):
    def test_global_limit_from_other_rest_route_blocks_message_create(self):
        clock = [100.0]
        domain = RateLimitDomain(clock=lambda: clock[0])
        domain.observe('GET /users/@me', 429,
                       {'Retry-After': '5', 'X-RateLimit-Global': 'true'})
        with self.assertRaisesRegex(ProviderBoundaryError, 'PRE_CONSUME'):
            domain.admit_now('POST /channels/{channel_id}/messages')
        clock[0] = 105.0
        domain.admit_now('POST /channels/{channel_id}/messages')
        with self.assertRaisesRegex(ProviderBoundaryError, 'PRE_CONSUME'):
            domain.admit_now('GET /channels/{channel_id}')
        domain.release()

    def test_route_limit_blocks_pre_consume(self):
        clock = [100.0]
        domain = RateLimitDomain(clock=lambda: clock[0])
        route = 'POST /channels/{channel_id}/messages'
        domain.observe(route, 200,
                       {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset-After': '4'})
        with self.assertRaises(ProviderBoundaryError):
            domain.admit_now(route)
        clock[0] = 104.0
        domain.admit_now(route)
        domain.release()

    def test_ambiguous_429_blocks_credential_globally(self):
        clock = [100.0]
        domain = RateLimitDomain(clock=lambda: clock[0])
        domain.observe('POST /channels/{channel_id}/messages', 429,
                       {'Retry-After': '3'})
        with self.assertRaisesRegex(ProviderBoundaryError, 'PRE_CONSUME'):
            domain.admit_now('GET /users/@me')

    def test_payload_is_frozen_exact_text_and_mentions_disabled(self):
        payload = FrozenUtf8TextJson.freeze('A2 local text')
        self.assertEqual(json.loads(payload.body),
                         {'content': 'A2 local text', 'allowed_mentions': {'parse': []}})
        with self.assertRaises(Exception):
            FrozenUtf8TextJson.freeze('x' * 1025)
        with self.assertRaises(Exception):
            FrozenUtf8TextJson.freeze('@everyone')


class RealAuthorityProviderTests(unittest.TestCase):
    """Real R1 Core permit; fake provider session and numeric exact target."""

    def setUp(self):
        self.h = r1.RealAuthorityTests(methodName='runTest')
        self.h.setUp()
        h = self.h
        h.authority.close()
        h.target = TrustedDeliveryTarget('life_engine_discord', 'discord',
            '123456', '789012', str(h.actor.principal_id), 'profile', 'agent',
            h.host_identity)
        h.living.configure(h.ctx, h.rev(), h.op(), target=h.target.key)
        h.directory = h.base / 'a2-r1-authority'
        h.factory = RealDeliveryBindingFactory(r1.Allow(), h.target)
        h.authority = h.open_authority(initialize=True)
        h.authority.set_mode('LIVING_PENDING')
        h.authority.set_mode('LIVING_ACTIVE')
        h.facade = LivingHostFacade(h.authority)
        self.session = FakeSession()
        self.claim = candidate('fake-token-provider-integration')
        self.session_factory = FakeSessionFactory(self.session)
        self.resolver = FakeProtectedResolver()
        self.config = PlatformConfig(self.claim.token)
        self.transport = TrustedProviderTransportFactory().create(
            self.config, profile=self.claim.profile,
            adapter_owner=self.claim.owner,
            inventory=ProtectedCredentialInventory([self.claim], complete=True),
            resolver=self.resolver, session_factory=self.session_factory,
            application='fake-app')
        self.owner = self.transport._ownership
        self.adapter = a1.Adapter(self.config)
        self.adapter.install_trusted_provider_transport(self.transport)
        self.identity = a1.adapter_module.AdapterIdentity('profile', 'agent',
            'fake-app', 'a' * 64)
        self.projection = a1.adapter_module.ProtectedDeliveryRegistry(
            h.target, self.identity).project(h.authority)
        self.adapter.bind_trusted_host(self.projection, self.identity)
        self.assertTrue(asyncio.run(self.adapter.connect()))

    def tearDown(self):
        asyncio.run(self.owner.close())
        self.h.tearDown()

    def deliver(self, intent, result):
        return asyncio.run(self.adapter.deliver_authorized_real_contact(
            result.permit, target=self.h.target, intent=intent,
            attempt=result.response['result']['attempt_id'],
            invocation='r1-claim', payload=self.h.payload))

    def test_no_grant_no_provider_attempt(self):
        intent, result = self.h.claimed(grant=False)
        with self.assertRaises(Exception):
            self.deliver(intent, result)
        self.assertEqual(self.session.calls, [])

    def test_provider_transport_cannot_install_from_other_config(self):
        other = a1.Adapter(PlatformConfig('fake-token-B'))
        with self.assertRaises(Exception):
            other.install_trusted_provider_transport(self.transport)
        self.assertIsNone(other._transport)
        with self.assertRaises(Exception):
            self.adapter.install_trusted_provider_transport(self.transport)

    def test_direct_prepared_invoke_denied_without_consumed_permit(self):
        prepared = self.transport.prepare_exact(self.projection, self.h.target,
                                                 self.h.payload)
        with self.assertRaisesRegex(ProviderBoundaryError, 'ADMISSION_MISSING'):
            asyncio.run(prepared.invoke_exact(self.h.target.channel, self.h.payload))
        self.assertEqual(self.session.calls, [])
        self.transport.release_admission()

    def test_missing_or_wrong_protected_channel_resolution_denied(self):
        self.transport._resolver = None
        with self.assertRaisesRegex(ProviderBoundaryError, 'RESOLVER_MISSING'):
            self.transport.prepare_exact(self.projection, self.h.target, self.h.payload)
        self.transport._resolver = FakeProtectedResolver(channel_type='forum')
        with self.assertRaisesRegex(ProviderBoundaryError, 'TEXT_CHANNEL'):
            self.transport.prepare_exact(self.projection, self.h.target, self.h.payload)
        self.assertEqual(self.session.calls, [])

    def test_success_single_request_no_ack_and_replay(self):
        self.session.responses.append(FakeResponse(200,
            b'{"id":"24680","channel_id":"789012"}'))
        intent, result = self.h.claimed()
        real_connect = socket.socket.connect
        def deny_external(sock, address):
            if isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1'):
                return real_connect(sock, address)
            raise AssertionError('external network')
        with patch.object(socket.socket, 'connect', deny_external):
            outcome = self.deliver(intent, result)
        self.assertIs(outcome.classification,
                      ProviderResultClass.PROVIDER_CONFIRMED_SUCCESS)
        self.assertTrue(outcome.sent_candidate)
        self.assertEqual(len(self.session.calls), 1)
        url, headers, body = self.session.calls[0]
        self.assertEqual(url,
            'https://discord.com/api/v10/channels/789012/messages')
        self.assertEqual(json.loads(body)['content'], self.h.payload)
        self.assertEqual(json.loads(body)['allowed_mentions'], {'parse': []})
        self.assertNotIn('fake-token-provider-integration', repr(outcome))
        with self.assertRaises(Exception):
            self.deliver(intent, result)
        self.assertEqual(len(self.session.calls), 1)

    def test_429_no_retry_unknown_bucket(self):
        self.session.responses.append(FakeResponse(429, headers={'Retry-After': '5'}))
        intent, result = self.h.claimed()
        outcome = self.deliver(intent, result)
        self.assertIs(outcome.classification, ProviderResultClass.RATE_LIMITED_NO_RETRY)
        self.assertEqual(len(self.session.calls), 1)
        with self.assertRaises(ProviderBoundaryError):
            self.owner.domain.admit_now('POST /channels/{channel_id}/messages')

    def _unknown_case(self, event):
        self.session.responses.append(event if isinstance(event, (BaseException, FakeResponse))
                                      else FakeResponse(event))
        intent, result = self.h.claimed()
        outcome = self.deliver(intent, result)
        self.assertIs(outcome.classification, ProviderResultClass.UNKNOWN)
        self.assertEqual(len(self.session.calls), 1)
        with self.assertRaises(Exception):
            self.deliver(intent, result)
        self.assertEqual(len(self.session.calls), 1)

    def test_500_no_retry(self): self._unknown_case(500)
    def test_502_no_retry(self): self._unknown_case(502)
    def test_504_no_retry(self): self._unknown_case(504)
    def test_524_no_retry(self): self._unknown_case(524)
    def test_reset_no_retry(self): self._unknown_case(ConnectionResetError())
    def test_timeout_no_retry(self): self._unknown_case(TimeoutError())
    def test_redirect_no_follow(self):
        self._unknown_case(FakeResponse(302, headers={'Location': 'https://other'}))
    def test_wrong_channel_not_sent_candidate(self):
        self._unknown_case(FakeResponse(200, b'{"id":"24680","channel_id":"999"}'))
    def test_missing_message_id_not_sent_candidate(self):
        self._unknown_case(FakeResponse(200, b'{"channel_id":"789012"}'))

    def test_rate_limit_deny_before_permit_consume(self):
        self.owner.domain.observe('GET /users/@me', 429,
            {'Retry-After': '100', 'X-RateLimit-Global': 'true'})
        intent, result = self.h.claimed()
        outcome = self.deliver(intent, result)
        self.assertIs(outcome.classification, ProviderResultClass.PRE_SEND_DENY)
        self.assertEqual(self.session.calls, [])
        self.assertIn(result.response['result']['attempt_id'],
                      self.h.authority._real_issued)

    def test_lifecycle_rotation_denies_before_provider(self):
        intent, result = self.h.claimed()
        self.adapter.application_identity_changed('rotated-app')
        with self.assertRaises(Exception):
            self.deliver(intent, result)
        self.assertEqual(self.session.calls, [])

    def test_generic_send_still_denied(self):
        response = asyncio.run(self.adapter.send('789012', 'local',
            metadata={'thread_id': '999'}, reply_to='999'))
        self.assertFalse(response.success)
        self.assertEqual(self.session.calls, [])

    def test_mutable_adapter_reread_cannot_redirect_after_consume(self):
        self.session.responses.append(FakeResponse(200,
            b'{"id":"24680","channel_id":"789012"}'))
        original = self.session.post_once
        async def mutate_during_provider_await(url, *, headers, data):
            self.adapter._transport = object()
            self.h.target = TrustedDeliveryTarget('life_engine_discord', 'discord',
                '123456', '999999', self.h.target.owner, 'profile', 'agent',
                self.h.host_identity)
            return await original(url, headers=headers, data=data)
        self.session.post_once = mutate_during_provider_await
        intent, result = self.h.claimed()
        outcome = self.deliver(intent, result)
        self.assertIs(outcome.classification,
                      ProviderResultClass.PROVIDER_CONFIRMED_SUCCESS)
        self.assertEqual(len(self.session.calls), 1)
        self.assertIn('/789012/messages', self.session.calls[0][0])

    def test_application_transition_wins_before_admission(self):
        intent, result = self.h.claimed()
        outcomes = []
        def deliver():
            try:
                outcomes.append(self.deliver(intent, result))
            except Exception:
                outcomes.append('DENY')
        with self.adapter._lifecycle_lock:
            worker = threading.Thread(target=deliver)
            worker.start()
            self.adapter.application_identity_changed('rotated-app')
        worker.join(15)
        self.assertFalse(worker.is_alive())
        self.assertEqual(outcomes, ['DENY'])
        self.assertEqual(self.session.calls, [])

    def test_delivery_window_wins_then_rotation_waits(self):
        entered, release, transition_started = (threading.Event() for _ in range(3))
        self.session.responses.append(FakeResponse(200,
            b'{"id":"24680","channel_id":"789012"}'))
        original = self.session.post_once
        async def held_provider(url, *, headers, data):
            entered.set()
            if not await asyncio.to_thread(release.wait, 15):
                raise AssertionError('provider barrier timed out')
            return await original(url, headers=headers, data=data)
        self.session.post_once = held_provider
        intent, result = self.h.claimed()
        outcome = []
        worker = threading.Thread(target=lambda: outcome.append(self.deliver(intent, result)))
        worker.start()
        try:
            self.assertTrue(entered.wait(15))
            def rotate():
                transition_started.set()
                self.adapter.application_identity_changed('rotated-app')
            transition = threading.Thread(target=rotate)
            transition.start()
            self.assertTrue(transition_started.wait(15))
            self.assertFalse(self.adapter._lifecycle_lock.acquire(blocking=False))
        finally:
            release.set()
        worker.join(15)
        transition.join(15)
        self.assertFalse(worker.is_alive())
        self.assertFalse(transition.is_alive())
        self.assertEqual(len(self.session.calls), 1)
        self.assertIs(outcome[0].classification,
                      ProviderResultClass.PROVIDER_CONFIRMED_SUCCESS)

    def test_same_event_loop_disconnect_waits_for_inflight_request(self):
        self.session.responses.append(FakeResponse(200,
            b'{"id":"24680","channel_id":"789012"}'))
        entered = asyncio.Event()
        release = asyncio.Event()
        wait_started = threading.Event()
        original_post = self.session.post_once
        async def held_post(url, *, headers, data):
            entered.set()
            await release.wait()
            return await original_post(url, headers=headers, data=data)
        self.session.post_once = held_post
        intent, result = self.h.claimed()
        original_wait = self.adapter._idle.wait
        def observed_wait(*args, **kwargs):
            wait_started.set()
            return original_wait(*args, **kwargs)
        async def run():
            delivery = asyncio.create_task(
                self.adapter.deliver_authorized_real_contact(result.permit,
                    target=self.h.target, intent=intent,
                    attempt=result.response['result']['attempt_id'],
                    invocation='r1-claim', payload=self.h.payload))
            await entered.wait()
            with patch.object(self.adapter._idle, 'wait', observed_wait):
                stopping = asyncio.create_task(self.adapter.disconnect())
                self.assertTrue(await asyncio.to_thread(wait_started.wait, 15))
                self.assertFalse(stopping.done())
                release.set()
                outcome = await delivery
                await stopping
            return outcome
        outcome = asyncio.run(run())
        self.assertIs(outcome.classification,
                      ProviderResultClass.PROVIDER_CONFIRMED_SUCCESS)
        self.assertEqual(len(self.session.calls), 1)
        self.assertTrue(self.session.closed)


class StaticNetworkFenceTests(unittest.TestCase):
    def test_default_adapter_has_no_transport_and_no_network(self):
        self.assertFalse(asyncio.run(a1.Adapter(object()).connect()))
        self.assertFalse(hasattr(a1.Adapter(object()), '_provider_session'))

    def test_production_factory_not_used_by_default(self):
        self.assertIsNotNone(AiohttpOneShotSessionFactory)
        self.assertIsNone(a1.Adapter(object())._transport)

    def test_production_http_boundary_disables_redirect(self):
        calls = []
        class Response:
            status = 302
            headers = {'Location': 'https://other.invalid'}
            async def read(self): return b''
        class RequestContext:
            async def __aenter__(self): return Response()
            async def __aexit__(self, *args): return False
        class FakeAiohttpClient:
            def post(self, url, **kwargs):
                calls.append((url, kwargs))
                return RequestContext()
        session = _AiohttpOneShotSession(FakeAiohttpClient())
        response = asyncio.run(session.post_once('https://discord.invalid',
            headers={'Authorization': 'Bot fake'}, data=b'{}'))
        self.assertEqual(response.status, 302)
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][1]['allow_redirects'], False)


if __name__ == '__main__':
    unittest.main()
