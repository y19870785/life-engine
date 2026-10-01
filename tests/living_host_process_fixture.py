"""A3 真实 fresh Python / os._exit 故障边界；只写隔离 fake journal。"""
from datetime import datetime
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine.domain import DomainId, Principal, WorldScope, WriterEpoch, Revision
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime
from life_engine.living_host_binding import BindingAuthority
from life_engine.living_host_facade import LivingHostFacade
from life_engine.living_host_evidence import FakeEvidenceValidator, DeterministicFakeTransport
from life_engine.prompt import PromptSessionContext, PromptPurpose
from life_engine.memory import MemoryAudience, AudienceKind
from life_engine.living_domain import canonical


if __name__ == '__main__':
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    mode = sys.argv[2]
    scope = WorldScope(*map(DomainId.parse, cfg['scope']))
    owner = Principal(DomainId.parse(cfg['principal']), scope.owner_id)
    repo = LivingRepository(cfg['root'], cfg['instance'], runtime_id=cfg['runtime_id'])
    runtime = LivingRuntime(repo, clock=lambda: datetime.fromisoformat(cfg['now']))
    authority = BindingAuthority(runtime, cfg['directory'], owner=owner, scope=scope,
        install_id='isolated-install', host_identity='FAKE:profile:gateway:config:agent:workspace',
        producer='test', target='本人合成目标', isolated_test=True,
        test_key=b'A3 deterministic isolated authority key')
    if mode == 'restart':
        print(canonical(dict(epoch=authority.binding_runtime_epoch, generation=repo.generation)), flush=True)
        os._exit(84)
    s = cfg['session']
    session = PromptSessionContext(owner, scope, DomainId.parse(s['id']), WriterEpoch(s['writer_epoch']),
        repo.runtime_id, repo.generation, MemoryAudience(AudienceKind.SOUL, scope.soul_id),
        Revision(s['world_revision']), PromptPurpose.SOUL_RESPONSE)
    facade = LivingHostFacade(authority)
    data = dict(intent_id=cfg['intent'], expected_revision=cfg['expected'])
    envelope = authority.envelope('EXECUTOR', cfg['operation'], session=session)
    cap = authority.issue(envelope, 'claim_attempt', data)
    if mode == 'before-claim':
        authority.correlate(envelope, 'begin_attempt', cfg['intent'])
        os._exit(80)
    def crash(point):
        if mode == 'claim-lost' and point == 'after_claim_commit':
            os._exit(81)
    result = facade.claim_attempt(envelope, cap, data, crash=crash)
    if mode == 'claimed-crash':
        os._exit(82)
    validator = FakeEvidenceValidator(b'A3 deterministic isolated provider key', repo.instance_id, repo.generation)
    transport = DeterministicFakeTransport(authority, validator, cfg['journal'])
    def after_send(point):
        if point == 'after_send':
            os._exit(83)
    transport.send(result.permit, target='本人合成目标', attempt=result.response['result']['attempt_id'],
                   invocation=cfg['operation'], crash=after_send)
