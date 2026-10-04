"""R1 validation worker: local-only authority, fresh-process os._exit points."""
from datetime import datetime
import json
import os
from pathlib import Path
import sys


NETWORK_ATTEMPTS = 0


def network_audit(event, args):
    global NETWORK_ATTEMPTS
    if event in ('socket.__new__', 'socket.connect', 'socket.sendto', 'socket.getaddrinfo'):
        NETWORK_ATTEMPTS += 1
        raise RuntimeError('R1_NETWORK_HARD_DENY')


sys.addaudithook(network_audit)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine.domain import DomainId, Principal, WorldScope, WriterEpoch, Revision
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime
from life_engine.living_host_binding import RealDeliveryBindingFactory
from life_engine.living_host_facade import LivingHostFacade
from life_engine.living_real_delivery import (TrustedDeliveryTarget, RealDeliveryPolicy,
    PolicyDecision, RealDeliveryConsumer)
from life_engine.prompt import PromptSessionContext, PromptPurpose
from life_engine.memory import MemoryAudience, AudienceKind
from life_engine.living_domain import canonical


class Allow(RealDeliveryPolicy):
    def decide(self, context):
        return PolicyDecision.ALLOW


def run(filename, mode):
    cfg = json.loads(Path(filename).read_text(encoding='utf-8'))
    scope = WorldScope(*map(DomainId.parse, cfg['scope']))
    owner = Principal(DomainId.parse(cfg['principal']), scope.owner_id)
    repo = LivingRepository(cfg['root'], cfg['instance'], runtime_id=cfg['runtime_id'])
    runtime = LivingRuntime(repo, clock=lambda: datetime.fromisoformat(cfg['now']))
    target = TrustedDeliveryTarget('LOCAL', 'LOCAL_INTERCEPT', 'server', 'channel',
        str(owner.principal_id), 'profile', 'agent', 'R1:local:binding')
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
    data = dict(intent_id=cfg['intent'], expected_revision=cfg['expected'])
    envelope = authority.envelope('EXECUTOR', 'r1-claim', session=session)
    cap = authority.issue(envelope, 'claim_attempt', data)
    factory.one_shot(authority, intent=cfg['intent'], invocation='r1-claim',
                     payload='R1 local validation text')

    def phase(point, code):
        with Path(cfg['phase']).open('wb') as handle:
            handle.write(canonical(dict(point=point, exit_code=code,
                network_send=NETWORK_ATTEMPTS, transport_invocation=0)).encode())
            handle.flush(); os.fsync(handle.fileno())
        os._exit(code)

    def committed(point):
        if mode == 'CR01' and point == 'after_claim_commit':
            phase('CLAIMED_before_permit', 80)

    result = facade.claim_attempt(envelope, cap, data, crash=committed)
    if result.permit is None:
        raise AssertionError('real permit missing')
    if mode == 'CR02':
        phase('permit_before_guard', 81)

    if mode == 'CR03':
        # Child-only instrumentation at the exact vault.consume entry. The
        # consumer has completed all final checks but has not consumed.
        def before_consume(*args, **kwargs):
            phase('guard_before_consume', 82)
        authority._vault.consume = before_consume

    consumer = RealDeliveryConsumer(authority)
    consumer.intercept(result.permit, target=target, intent=cfg['intent'],
        attempt=result.response['result']['attempt_id'], invocation='r1-claim',
        payload='R1 local validation text')
    if mode == 'CR04':
        phase('consumed_after_local_intercept', 83)
    raise AssertionError('unknown crash mode')


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
