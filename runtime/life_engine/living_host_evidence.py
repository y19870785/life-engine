"""DeliveryEvidence v1：仅可信结果；本实现只有无网络 deterministic fake provider。"""
from dataclasses import asdict, dataclass, field
import hashlib
import hmac
import json
import os
from pathlib import Path

from .durable import locked
from .living_domain import canonical, fail, fingerprint, instant, text


@dataclass(frozen=True)
class DeliveryEvidence:
    instance_id: str
    generation: str
    attempt_id: str
    target: str
    state: str
    source: str
    event_id: str
    observed_at: float
    provider_reference: str
    message_id: str | None = None
    sent_at: float | None = None
    validator_version: str = 'DeliveryEvidence-v1-SIMULATED'
    _seal: str = field(default='', repr=False)

    def identity(self):
        out = asdict(self)
        del out['_seal']
        return out


class FakeEvidenceValidator:
    """独立 test key；不能用于生产 provider attestation。"""
    def __init__(self, key, instance_id, generation):
        if type(key) is not bytes or len(key) < 32:
            fail('INVALID_ARGUMENT')
        self._key = key
        self.instance_id, self.generation = instance_id, generation

    def __repr__(self):
        return '<FakeEvidenceValidator SIMULATED>'

    def _seal(self, value):
        raw = canonical(value).encode('utf-8')
        if len(raw) > 8192:
            fail('BUDGET_INPUT')
        return hmac.new(self._key, raw, hashlib.sha256).hexdigest()

    def _attest(self, evidence):
        from dataclasses import replace
        return replace(evidence, _seal=self._seal(evidence.identity()))

    def verify(self, evidence):
        if type(evidence) is not DeliveryEvidence:
            fail('RECEIPT_UNVERIFIED')
        if not hmac.compare_digest(evidence._seal, self._seal(evidence.identity())):
            fail('RECEIPT_UNVERIFIED')
        if evidence.generation != self.generation:
            fail('GENERATION_STALE')
        if evidence.instance_id != self.instance_id or evidence.source != 'LOCAL_FAKE_SIMULATED':
            fail('RECEIPT_UNVERIFIED')
        if evidence.state not in ('SENT', 'ACKNOWLEDGED', 'FAILED', 'UNKNOWN'):
            fail('RECEIPT_UNVERIFIED')
        for value in (evidence.attempt_id, evidence.target, evidence.event_id, evidence.provider_reference):
            text(value)
        if type(evidence.observed_at) not in (float, int):
            fail('RECEIPT_UNVERIFIED')
        if evidence.state in ('SENT', 'ACKNOWLEDGED'):
            text(evidence.message_id)
            if type(evidence.sent_at) not in (float, int) or evidence.sent_at > evidence.observed_at:
                fail('RECEIPT_UNVERIFIED')
        return dict(attempt_id=evidence.attempt_id, target=evidence.target, state=evidence.state,
                    source=evidence.source, event_id=evidence.event_id,
                    message_id=evidence.message_id, sent_at=evidence.sent_at,
                    observed_at=evidence.observed_at, provider_reference=evidence.provider_reference,
                    validator_version=evidence.validator_version)


class DeterministicFakeTransport:
    """仅隔离测试，外部副作用为本地 append+fsync；没有网络/channel 参数。"""
    def __init__(self, authority, validator, journal):
        if not authority._isolated_test or type(validator) is not FakeEvidenceValidator:
            fail('NO_REAL_SEND')
        self.authority, self.validator = authority, validator
        self.journal = Path(journal)

    def send(self, permit, *, target, attempt, invocation, crash=None):
        with self.authority.consume_permit(permit, target=target, attempt=attempt, invocation=invocation):
            if crash is not None:
                crash('after_consume')
            sent_at = instant(self.authority.runtime.clock())
            evidence = DeliveryEvidence(self.validator.instance_id, self.validator.generation,
                attempt, target, 'SENT', 'LOCAL_FAKE_SIMULATED', fingerprint([attempt, 'SENT']),
                sent_at, fingerprint([attempt, target, 'local-fake-provider-v1']),
                'simulated-' + fingerprint([attempt, target]), sent_at)
            evidence = self.validator._attest(evidence)
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            with locked(self.journal.parent, 'fake-provider'):
                with self.journal.open('ab') as handle:
                    handle.write((canonical(evidence.identity()) + '\n').encode('utf-8'))
                    handle.flush(); os.fsync(handle.fileno())
            if crash is not None:
                crash('after_send')
            return evidence

    def acknowledgement(self, sent):
        """独立 fake provider ACK event；必须先有可验证 SENT 和已落盘 message。"""
        self.validator.verify(sent)
        if sent.state != 'SENT' or not self.journal.exists():
            fail('RECEIPT_UNVERIFIED')
        with locked(self.journal.parent, 'fake-provider'):
            messages = [json.loads(row) for row in self.journal.read_text(encoding='utf-8').splitlines()]
        if sent.identity() not in messages:
            fail('RECEIPT_UNVERIFIED')
        from dataclasses import replace
        return self.validator._attest(replace(sent, state='ACKNOWLEDGED',
            event_id=fingerprint([sent.attempt_id, 'ACKNOWLEDGED']),
            observed_at=instant(self.authority.runtime.clock())))

    def uncertain(self, attempt, target, *, state='UNKNOWN'):
        if state not in ('UNKNOWN', 'FAILED'):
            fail('RECEIPT_UNVERIFIED')
        return self.validator._attest(DeliveryEvidence(self.validator.instance_id,
            self.validator.generation, attempt, target, state, 'LOCAL_FAKE_SIMULATED',
            fingerprint([attempt, state]), instant(self.authority.runtime.clock()),
            fingerprint([attempt, state, 'local-observation'])))
