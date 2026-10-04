"""有界 Host-neutral facade；所有业务真源、CAS、receipt 和 recovery 仍由 Core 决定。"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from uuid import uuid4

from .living_domain import canonical, fail, fingerprint, instant, text, LivingTickContext
from .living_host_evidence import DeliveryEvidence
from .living_real_delivery import BindingMode
from .living_projection import query, revalidate


def bounded(value):
    if len(canonical(value).encode('utf-8')) > 16384:
        fail('BUDGET_INPUT')
    return value


def payload(value, required, optional=()):
    if type(value) is not dict or set(value) - set(required) - set(optional) or set(required) - set(value):
        fail('INVALID_ARGUMENT')
    if len(canonical(value).encode('utf-8')) > 8192:
        fail('BUDGET_INPUT')


@dataclass(frozen=True)
class ClaimOutcome:
    """只能交给可信 executor；普通 JSON 永远不包含 opaque permit。"""
    response: dict
    permit: object = field(default=None, repr=False)

    def to_json(self):
        return canonical(bounded(self.response))


class LivingHostFacade:
    def __init__(self, authority):
        self.authority = authority
        self.runtime = authority.runtime

    def _response(self, envelope, result):
        data = self.authority._data()
        return bounded(dict(contract_version='SP-005A3-host-binding-v1',
            invocation_id=envelope.invocation_id, command_executed=True, result=result,
            error_code=None, retry_disposition='TRUSTED_DECISION_REQUIRED',
            binding_revision=data['revision'], generation=self.authority._generation(),
            living_revision=result.get('revision', result.get('living_revision'))))

    def tick(self, envelope, capability, data):
        payload(data, ())
        with self.authority.authorized(envelope, capability, 'tick', data):
            state = self.runtime.status(self.authority.context())
            ctx = LivingTickContext(self.authority.scope, self.runtime.repository.instance_id,
                self.authority._generation(), state['root']['policy_revision'], self.authority.producer)
            return self._response(envelope, self.runtime.tick(ctx, envelope.invocation_id))

    def query_context(self, envelope, capability, data):
        payload(data, (), ('handle',))
        with self.authority.authorized(envelope, capability, 'query_context', data):
            if 'handle' in data:
                entry = self.authority._snapshots.get(data['handle'])
                if entry is None or entry[0] != envelope.session:
                    fail('SNAPSHOT_STALE')
                revalidate(self.runtime, envelope.session, entry[1])
                snapshot = entry[1]
                handle = data['handle']
            else:
                snapshot = query(self.runtime, envelope.session)
                handle = uuid4().hex
                self.authority._snapshots[handle] = (envelope.session, snapshot)
            # 输出有界结构，seal 留在 authority；不修改 PromptSnapshot。
            return self._response(envelope, dict(context_handle=handle,
                snapshot=json.loads(snapshot.payload), origin='STRUCTURED_ONLY'))

    def observe_inbound(self, envelope, capability, data):
        payload(data, ('event_id', 'content_digest', 'expected_revision'))
        if not data['event_id']:
            fail('INBOUND_UNVERIFIED')
        text(data['event_id'])
        digest = data['content_digest']
        import re
        if type(digest) is not str or re.fullmatch('[0-9a-f]{64}', digest) is None:
            fail('INBOUND_UNVERIFIED')
        with self.authority.authorized(envelope, capability, 'observe_inbound', data):
            meta = self.authority._data()
            key = fingerprint([self.authority.install_id, self.authority.host_identity,
                               meta['target'], data['event_id']])
            old = meta['inbound'].get(key)
            if old and old['digest'] != digest:
                fail('IDEMPOTENCY_CONFLICT')
            if old is None:
                old = dict(digest=digest, received_at=instant(self.runtime.clock()))
                meta['inbound'][key] = old
                self.authority._metadata.write(meta)
            received = datetime.fromtimestamp(old['received_at'], timezone.utc)
            # event ID 而非每次 connector invocation 决定 operation；首次时间持久复用。
            result = self.runtime.observe_inbound(self.authority.context(), data['expected_revision'],
                'inbound-' + key, source=self.authority.producer, event_id=key, received_at=received)
            return self._response(envelope, result)

    def prepare_contact(self, envelope, capability, data):
        payload(data, ('intent_id', 'material', 'expected_revision'))
        text(data['intent_id']); text(data['material'])
        with self.authority.authorized(envelope, capability, 'prepare_contact', data):
            self.authority.correlate(envelope, 'prepare', [data['intent_id'], data['material']])
            result = self.runtime.prepare_intent(self.authority.context(envelope), data['expected_revision'],
                envelope.invocation_id, data['intent_id'], data['material'])
            return self._response(envelope, result)

    def claim_attempt(self, envelope, capability, data, *, crash=None):
        payload(data, ('intent_id', 'expected_revision'))
        text(data['intent_id'])
        with self.authority.authorized(envelope, capability, 'claim_attempt', data):
            if (self.authority.execution_mode is BindingMode.SIMULATION
                    and not self.authority._isolated_test):
                fail('NO_REAL_SEND')
            # 先走 Core session authorization；replay 不绕过 World fence。
            if self.authority._reconcile:
                fail('RECONCILIATION_REQUIRED')
            self.authority.correlate(envelope, 'begin_attempt', data['intent_id'])
            result = self.runtime.begin_attempt(self.authority.context(envelope), data['expected_revision'],
                envelope.invocation_id, data['intent_id'])
            if crash is not None:
                if not self.authority._isolated_test:
                    fail('NO_REAL_SEND')
                crash('after_claim_commit')
            permit = None
            if result.get('execute') is True and result.get('state') == 'CLAIMED':
                # Core transaction 已结束；只在本次首次成功响应签发。
                if self.authority.execution_mode is BindingMode.REAL_DELIVERY:
                    permit = self.authority._issue_real_permit(envelope, result, data['intent_id'])
                else:
                    permit = self.authority._issue_permit(envelope, result)
            return ClaimOutcome(self._response(envelope, result), permit)

    def recover_operation(self, envelope, capability, data):
        payload(data, ('operation_id',))
        text(data['operation_id'])
        with self.authority.authorized(envelope, capability, 'recover_operation', data):
            context, request = self.authority.recovery(data['operation_id'])
            projected = self.runtime.query_operation_recovery(context, request)
            if projected.attempt is not None:
                self.authority._associations[data['operation_id']] = projected.attempt
                self.authority._reconcile = True
            result = asdict(projected)
            result['continuation'] = 'RECONCILIATION_REQUIRED'
            # 无 execute、permit 或 transport；NOT_COMMITTED 也不是执行资格。
            return self._response(envelope, result)

    def submit_delivery_result(self, envelope, capability, data, evidence):
        payload(data, ('attempt_id', 'expected_revision', 'evidence_digest'))
        # R1 has no real-provider validator. A local intercept is never SENT.
        if self.authority.execution_mode is BindingMode.REAL_DELIVERY:
            fail('RECEIPT_UNVERIFIED')
        if type(evidence) is not DeliveryEvidence or fingerprint(evidence.identity()) != data['evidence_digest']:
            fail('RECEIPT_UNVERIFIED')
        if evidence.generation != self.authority._generation():
            fail('GENERATION_STALE')
        with self.authority.authorized(envelope, capability, 'submit_delivery_result', data):
            result = self.runtime.record_delivery(self.authority.context(), data['expected_revision'],
                envelope.invocation_id, data['attempt_id'], evidence)
            if result.get('state') in ('SENT', 'ACKNOWLEDGED', 'FAILED'):
                self.authority._pending.discard(data['attempt_id'])
            return self._response(envelope, result)

    def status(self, envelope, capability, data):
        payload(data, (), ('limit', 'cursor'))
        limit = data.get('limit', 20)
        if type(limit) is not int or not 1 <= limit <= 100:
            fail('INVALID_ARGUMENT')
        with self.authority.authorized(envelope, capability, 'status', data):
            state = self.runtime.status(self.authority.context())
            root = state['root']
            offset = 0
            if 'cursor' in data:
                cursor = data['cursor']
                if type(cursor) is not dict or set(cursor) != {'revision', 'binding_revision', 'offset'}:
                    fail('INVALID_ARGUMENT')
                if cursor['revision'] != root['revision'] or cursor['binding_revision'] != self.authority._data()['revision']:
                    fail('CURSOR_STALE')
                offset = cursor['offset']
                if type(offset) is not int or offset < 0:
                    fail('INVALID_ARGUMENT')
            items = state['intents'][offset:offset + limit]
            safe = [{k: x[k] for k in ('id', 'state', 'reserved_at', 'expires')} for x in items]
            next_offset = offset + len(items)
            cursor = None if next_offset >= len(state['intents']) else dict(revision=root['revision'],
                binding_revision=self.authority._data()['revision'], offset=next_offset)
            return self._response(envelope, dict(revision=root['revision'], paused=bool(root['paused']),
                reconciliation=bool(root['reconciliation']) or self.authority._reconcile,
                intents=safe, cursor=cursor, no_real_send=True))
