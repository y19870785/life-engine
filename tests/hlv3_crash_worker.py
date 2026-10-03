"""HLV3 VALIDATION ONLY: fresh process crash points, no real transport."""
from datetime import datetime
import json
import os
from pathlib import Path
import sys

from hlv3_validation_support import (install_fence, HostGate, LocalFakeTransport,
    BindingAuthority, LivingHostFacade, FakeEvidenceValidator, LivingRepository,
    LivingRuntime, DomainId, WorldScope, canonical)
from life_engine.domain import Principal, WriterEpoch, Revision
from life_engine.prompt import PromptSessionContext, PromptPurpose
from life_engine.memory import MemoryAudience, AudienceKind
import hlv3_validation_support as support


def run(filename, mode):
    install_fence()
    cfg = json.loads(Path(filename).read_text())
    gate = HostGate(cfg['host_fixture'])
    with gate.current():
        scope = WorldScope(*map(DomainId.parse, cfg['scope']))
        owner = Principal(DomainId.parse(cfg['principal']), scope.owner_id)
        repo = LivingRepository(cfg['root'], cfg['instance'], runtime_id=cfg['runtime_id'])
        runtime = LivingRuntime(repo, clock=lambda: datetime.fromisoformat(cfg['now']))
        authority = BindingAuthority(runtime, cfg['directory'], owner=owner, scope=scope,
            install_id=gate.snapshot['install'], host_identity=gate.persistent_digest,
            producer='hlv3-validation', target=cfg['target'], isolated_test=True,
            test_key=b'HLV3 validation-only authority key!')
        session = PromptSessionContext(owner, scope, DomainId.parse(cfg['session']['id']),
            WriterEpoch(cfg['session']['writer_epoch']), repo.runtime_id, repo.generation,
            MemoryAudience(AudienceKind.SOUL, scope.soul_id), Revision(cfg['session']['world_revision']),
            PromptPurpose.SOUL_RESPONSE)
        facade = LivingHostFacade(authority)
        data = dict(intent_id=cfg['intent'], expected_revision=cfg['expected'])
        envelope = authority.envelope('EXECUTOR', 'crash-claim', session=session)
        capability = authority.issue(envelope, 'claim_attempt', data)

        def phase(point, code, **extra):
            if support.FENCE.real_transport_invocations or support.FENCE.network_attempts:
                raise AssertionError('HLV3_TRANSPORT_FENCE_VIOLATION')
            value = dict(point=point, exit_code=code, provider='LOCAL_FAKE',
                real_transport_invocations=0, network_attempts=0, **extra)
            with Path(cfg['phase']).open('wb') as handle:
                handle.write(canonical(value).encode())
                handle.flush()
                os.fsync(handle.fileno())
            os._exit(code)

        if mode == 'CR_01':
            authority.correlate(envelope, 'begin_attempt', cfg['intent'])
            phase('after_correlation_before_begin_attempt', 80, permit_issued=0)

        def committed(point):
            if mode == 'CR_02' and point == 'after_claim_commit':
                phase('after_claim_commit_before_response_and_permit', 81, permit_issued=0)

        result = facade.claim_attempt(envelope, capability, data, crash=committed)
        if result.permit is None:
            raise AssertionError('first CLAIMED did not issue permit')
        if mode == 'CR_06':
            phase('after_permit_issue_before_consume', 82, permit_issued=1, permit_consumed=0)
        validator = FakeEvidenceValidator(b'HLV3 LOCAL_FAKE validation-only key!', repo.instance_id, repo.generation)
        transport = LocalFakeTransport(authority, gate, validator, cfg['journal'])

        def durable(point):
            phase(point, 83, permit_issued=1, permit_consumed=1, journal_committed=1)

        if mode != 'CR_07':
            raise AssertionError('unknown crash mode')
        transport.send(result.permit, target=cfg['target'], attempt=result.response['result']['attempt_id'],
                       invocation='crash-claim', crash=durable)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
