"""Fresh-process A1 inert-port crash points; never imports provider SDK."""
import asyncio
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys


NETWORK_ATTEMPTS = 0


def network_audit(event, args):
    global NETWORK_ATTEMPTS
    if event in ('socket.__new__', 'socket.connect', 'socket.sendto',
                 'socket.getaddrinfo'):
        NETWORK_ATTEMPTS += 1
        raise RuntimeError('A1_NETWORK_HARD_DENY')


# Windows event-loop setup creates an internal socketpair. Establish that
# infrastructure before denying all subsequent provider/network operations.
_loop = asyncio.new_event_loop()
sys.addaudithook(network_audit)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from life_engine.domain import DomainId, Principal, WorldScope, WriterEpoch, Revision
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime
from life_engine.living_host_binding import RealDeliveryBindingFactory
from life_engine.living_host_facade import LivingHostFacade
from life_engine.living_real_delivery import TrustedDeliveryTarget
from life_engine.prompt import PromptSessionContext, PromptPurpose
from life_engine.memory import MemoryAudience, AudienceKind
from life_engine.living_domain import canonical
from test_hlv4_r1_authority import Allow
from test_hlv4_a1_adapter import Adapter, InertExactTransport, adapter_module


def run(filename, mode):
    cfg = json.loads(Path(filename).read_text(encoding='utf-8'))
    scope = WorldScope(*map(DomainId.parse, cfg['scope']))
    owner = Principal(DomainId.parse(cfg['principal']), scope.owner_id)
    repo = LivingRepository(cfg['root'], cfg['instance'], runtime_id=cfg['runtime_id'])
    runtime = LivingRuntime(repo, clock=lambda: datetime.fromisoformat(cfg['now']))
    target = TrustedDeliveryTarget('life_engine_discord', 'discord', 'server',
        'channel', str(owner.principal_id), 'profile', 'agent', 'R1:local:binding')
    factory = RealDeliveryBindingFactory(Allow(), target)
    authority = factory.create(runtime, cfg['directory'], owner=owner, scope=scope,
        install_id='r1-local-install', host_identity='R1:local:binding',
        producer='r1-local', isolated_test=True,
        test_key=b'R1 local deterministic isolated key!')
    s = cfg['session']
    session = PromptSessionContext(owner, scope, DomainId.parse(s['id']),
        WriterEpoch(s['writer_epoch']), repo.runtime_id, repo.generation,
        MemoryAudience(AudienceKind.SOUL, scope.soul_id),
        Revision(s['world_revision']), PromptPurpose.SOUL_RESPONSE)
    facade = LivingHostFacade(authority)
    transport = InertExactTransport()
    identity = adapter_module.AdapterIdentity('profile', 'agent', 'fake-app',
        hashlib.sha256(b'fake-credential-identity').hexdigest())
    projection = adapter_module.ProtectedDeliveryRegistry(target, identity).project(authority)
    adapter = Adapter(object(), transport=transport)
    adapter.bind_trusted_host(projection, identity)
    if not _loop.run_until_complete(adapter.connect()):
        raise AssertionError('inert adapter not connected')
    data = dict(intent_id=cfg['intent'], expected_revision=cfg['expected'])
    envelope = authority.envelope('EXECUTOR', 'r1-claim', session=session)
    cap = authority.issue(envelope, 'claim_attempt', data)
    factory.one_shot(authority, intent=cfg['intent'], invocation='r1-claim',
                     payload='R1 local validation text')

    def phase(point, code):
        with Path(cfg['phase']).open('wb') as handle:
            handle.write(canonical(dict(point=point, exit_code=code,
                network_send=NETWORK_ATTEMPTS,
                transport_invocation=len(transport.calls))).encode())
            handle.flush(); os.fsync(handle.fileno())
        os._exit(code)

    def committed(point):
        if mode == 'CR01' and point == 'after_claim_commit':
            phase('CLAIMED_before_permit', 90)

    result = facade.claim_attempt(envelope, cap, data, crash=committed)
    if result.permit is None:
        raise AssertionError('real permit missing')
    if mode == 'CR02':
        phase('permit_before_guard', 91)

    if mode == 'CR03':
        authority._vault.consume = lambda *args, **kwargs: phase('guard_before_consume', 92)

    _loop.run_until_complete(adapter.deliver_authorized_real_contact(result.permit,
        target=target, intent=cfg['intent'],
        attempt=result.response['result']['attempt_id'],
        invocation='r1-claim', payload='R1 local validation text'))
    if mode == 'CR04':
        phase('consumed_at_inert_boundary', 93)
    raise AssertionError('unknown crash mode')


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
