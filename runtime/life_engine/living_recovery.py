"""B1 Core 只读恢复；可信本地断言不是 Host credential，也不授予 mutation 权限。"""
from dataclasses import asdict, dataclass
import json
import re

from .domain import Principal, WorldScope
from .living_domain import LivingContext, LivingError, canonical, fail, fingerprint, instant, scope_values, text
from .prompt import PromptSessionContext
from .living_repository import state_digest

REQUEST_LIMIT = RECEIPT_LIMIT = 8192
RESPONSE_LIMIT = 16384
ACTIONS = ('prepare', 'begin_attempt')
ATTEMPT_STATES = ('CLAIMED', 'SENT', 'ACKNOWLEDGED', 'FAILED', 'UNKNOWN')


def _identity(value):
    try:
        text(value)
    except UnicodeError:
        fail('INVALID_ARGUMENT')
    if '*' in value or '?' in value:
        fail('INVALID_ARGUMENT')


@dataclass(frozen=True)
class RecoveryDelegation:
    """由可信本地部署给出的 Owner 委托断言；不得从模型/普通 JSON 构造。

    与现有 Principal 相同的进程内信任边界，非 token 或可反序列化的凭证。
    委托固定到一个 grantee、原 actor、Scope、producer、instance 和 generation。
    """
    owner_authority: Principal
    grantee: Principal
    original_actor: Principal
    scope: WorldScope
    instance_id: str
    generation: str
    producer: str
    provenance: str


@dataclass(frozen=True)
class LivingRecoveryContext:
    """独立 recovery-only 权限；不继承 LivingContext，不能用于 mutation。"""
    principal: Principal
    delegation: RecoveryDelegation


@dataclass(frozen=True)
class OperationRecoveryRequest:
    instance_id: str
    generation: str
    scope: WorldScope
    producer: str
    operation_id: str
    action: str
    expected_payload_digest: str


@dataclass(frozen=True)
class PrepareRecoveryReceipt:
    intent_id: str
    revision: int


@dataclass(frozen=True)
class ClaimRecoveryReceipt:
    revision: int
    attempt_id: str | None = None
    historical_state: str | None = None
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecoveryAttempt:
    attempt_id: str
    current_state: str


@dataclass(frozen=True)
class OperationRecoveryProjection:
    status: str
    instance_id: str
    generation: str
    scope: tuple[str, ...]
    producer: str
    operation_id: str
    action: str
    living_revision: int
    receipt_digest: str | None = None
    receipt: PrepareRecoveryReceipt | ClaimRecoveryReceipt | None = None
    attempt: RecoveryAttempt | None = None

    def to_json(self):
        result = canonical(asdict(self))
        if len(result.encode('utf-8')) > RESPONSE_LIMIT:
            fail('BUDGET_INPUT')
        return result


def _request(request):
    if type(request) is not OperationRecoveryRequest:
        fail('INVALID_ARGUMENT')
    for value in (request.instance_id, request.generation, request.producer, request.operation_id):
        _identity(value)
    if request.action not in ACTIONS:
        fail('INVALID_ARGUMENT')
    digest = request.expected_payload_digest
    if type(digest) is not str or re.fullmatch('[0-9a-f]{64}', digest) is None:
        fail('INVALID_ARGUMENT')
    scope = scope_values(request.scope)
    for value in scope:
        _identity(value)
    # 字段先逐项有界，再序列化；未知字段由严格 dataclass 签名/类型拒绝。
    if len(canonical([request.instance_id, request.generation, scope, request.producer,
                      request.operation_id, request.action, digest]).encode('utf-8')) > REQUEST_LIMIT:
        fail('BUDGET_INPUT')


def _context(runtime, context, request):
    """验证可信类型及委托范围；不读取 operation 或 receipt。"""
    if request.generation != runtime.repository.generation:
        fail('GENERATION_STALE')
    if request.instance_id != runtime.repository.instance_id:
        fail('SCOPE_MISMATCH')
    if type(context) is LivingContext:
        if type(context.session) is not PromptSessionContext:
            fail('AUTHORIZATION_DENIED')
        s = context.session
        if (s.principal != context.principal or s.scope != context.scope
                or s.generation != context.generation or s.runtime_id != runtime.repository.runtime_id):
            fail('SESSION_STALE')
        actor = context.principal
        ctx = context
    elif type(context) is LivingRecoveryContext:
        d = context.delegation
        if type(d) is not RecoveryDelegation or any(type(p) is not Principal for p in
                (context.principal, d.owner_authority, d.grantee, d.original_actor)):
            fail('AUTHORIZATION_DENIED')
        if type(d.scope) is not WorldScope:
            fail('SCOPE_MISMATCH')
        for value in (d.instance_id, d.generation, d.producer, d.provenance):
            _identity(value)
        if context.principal != d.grantee:
            fail('AUTHORIZATION_DENIED')
        if any(p.owner_id != d.scope.owner_id for p in (d.owner_authority, d.grantee, d.original_actor)):
            fail('AUTHORIZATION_DENIED')
        if d.instance_id != request.instance_id:
            fail('SCOPE_MISMATCH')
        if d.generation != request.generation:
            fail('GENERATION_STALE')
        actor = d.original_actor
        # 仅 Core 内部复用现有 World/root 授权；外部普通 session=None 不被接受。
        ctx = LivingContext(d.grantee, d.scope, d.generation, d.producer)
    else:
        fail('AUTHORIZATION_DENIED')
    if ctx.generation != request.generation:
        fail('GENERATION_STALE')
    if ctx.scope != request.scope:
        fail('SCOPE_MISMATCH')
    if ctx.producer != request.producer:
        fail('AUTHORIZATION_DENIED')
    return ctx, str(actor.principal_id)


def _json(value):
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                fail('STATE_CORRUPT')
            result[key] = item
        return result
    try:
        return json.loads(value, object_pairs_hook=pairs,
                          parse_constant=lambda _: fail('STATE_CORRUPT'))
    except (ValueError, TypeError, RecursionError):
        fail('STATE_CORRUPT')


def _stored_text(value):
    try:
        text(value)
    except LivingError:
        fail('STATE_CORRUPT')
    return value


def _project(db, root, request, actor):
    key = (root['root_id'], request.generation, request.producer, request.operation_id)
    where = 'root_id=? AND generation=? AND producer=? AND operation_id=?'
    # SQLite 只计算长度；超限 payload/receipt 不进入 Python、不被反序列化。
    lengths = db.execute('SELECT length(CAST(payload AS BLOB)),length(CAST(receipt AS BLOB)) '
                         'FROM living_operations WHERE '+where, key).fetchone()
    if lengths is None:
        return None, None, None
    if any(type(n) is not int or n > RECEIPT_LIMIT for n in lengths):
        fail('BUDGET_INPUT')
    row = db.execute('SELECT payload,fingerprint,receipt,receipt_fingerprint,revision '
                     'FROM living_operations WHERE '+where, key).fetchone()
    stored, receipt = _json(row['payload']), _json(row['receipt'])
    if (type(stored) is not list or len(stored) != 4 or type(stored[0]) is not str
            or stored[2] != list(scope_values(request.scope))):
        fail('STATE_CORRUPT')
    if stored[3] != actor:
        fail('AUTHORIZATION_DENIED')
    if fingerprint(stored) != row['fingerprint'] or fingerprint(receipt) != row['receipt_fingerprint']:
        fail('STATE_CORRUPT')
    if type(receipt) is not dict or type(receipt.get('revision')) is not int:
        fail('STATE_CORRUPT')
    rev = row['revision']
    if receipt['revision'] != rev or not 0 < rev <= root['revision']:
        fail('STATE_CORRUPT')
    transition = db.execute('SELECT action,previous_revision FROM living_transitions '
                            'WHERE root_id=? AND revision=?', (root['root_id'], rev)).fetchone()
    if not transition or transition['action'] != stored[0] or transition['previous_revision'] != rev-1:
        fail('STATE_CORRUPT')
    if stored[0] != request.action or row['fingerprint'] != request.expected_payload_digest:
        fail('IDEMPOTENCY_CONFLICT')
    payload = stored[1]
    attempt = None
    if request.action == 'prepare':
        if type(payload) is not list or len(payload) != 2:
            fail('STATE_CORRUPT')
        intent_id = _stored_text(payload[0]); _stored_text(payload[1])
        if set(receipt) != {'id', 'revision'} or receipt['id'] != intent_id:
            fail('STATE_CORRUPT')
        projected = PrepareRecoveryReceipt(intent_id, rev)
    else:
        intent_id = _stored_text(payload)
        if set(receipt) == {'blockers', 'execute', 'revision'}:
            blockers = receipt['blockers']
            if (receipt['execute'] is not False or type(blockers) is not list or not blockers
                    or any(type(b) is not str for b in blockers)):
                fail('STATE_CORRUPT')
            for b in blockers:
                _stored_text(b)
            projected = ClaimRecoveryReceipt(rev, blockers=tuple(blockers))
        elif set(receipt) == {'attempt_id', 'state', 'execute', 'revision'}:
            aid = _stored_text(receipt['attempt_id'])
            if type(receipt['execute']) is not bool or receipt['state'] not in ATTEMPT_STATES:
                fail('STATE_CORRUPT')
            if receipt['execute'] and receipt['state'] != 'CLAIMED':
                fail('STATE_CORRUPT')
            a = db.execute('SELECT a.id,a.root_id,a.intent,a.state,a.target,a.request_fingerprint,'
                           'i.generation,i.state AS intent_state,i.prepared,i.target AS intent_target '
                           'FROM living_attempts a JOIN living_intents i ON i.id=a.intent WHERE a.id=?',
                           (aid,)).fetchone()
            if (a is None or a['root_id'] != root['root_id'] or a['intent'] != intent_id
                    or a['generation'] != request.generation or a['intent_state'] != 'ATTEMPTED'
                    or a['state'] not in ATTEMPT_STATES or a['target'] != a['intent_target']
                    or a['request_fingerprint'] != fingerprint([intent_id, a['prepared'], a['target']])):
                fail('STATE_CORRUPT')
            attempt = RecoveryAttempt(aid, a['state'])
            projected = ClaimRecoveryReceipt(rev, aid, receipt['state'])
        else:
            fail('STATE_CORRUPT')
    intent = db.execute('SELECT root_id,generation FROM living_intents WHERE id=?', (intent_id,)).fetchone()
    if not intent or intent['root_id'] != root['root_id'] or intent['generation'] != request.generation:
        fail('STATE_CORRUPT')
    return projected, attempt, row['receipt_fingerprint']


def _root_integrity(db, root):
    # 使用既有业务真源 checksum；不扫描/反序列化其它 operation receipts。
    row = db.execute("SELECT previous_revision,CASE WHEN length(json_extract(changes,'$.state_digest'))=64 "
                     "THEN json_extract(changes,'$.state_digest') END AS digest FROM living_transitions "
                     "WHERE root_id=? AND revision=?", (root['root_id'], root['revision'])).fetchone()
    if (row is None or row['previous_revision'] != root['revision']-1
            or row['digest'] != state_digest(db, root['root_id'])):
        fail('STATE_CORRUPT')


def query_operation_recovery(runtime, context: LivingContext | LivingRecoveryContext,
                             request: OperationRecoveryRequest) -> OperationRecoveryProjection:
    """公开 Core API；trusted context 必须由本地可信调用方提供，拒绝普通 JSON。"""
    _request(request)
    ctx, actor = _context(runtime, context, request)
    with runtime.repository.recovery_read_transaction() as db:
        root = runtime._root(db, ctx, instant(runtime.clock()))
        try:
            _root_integrity(db, root)
            receipt, attempt, digest = _project(db, root, request, actor)
        except LivingError:
            raise
        except (ValueError, TypeError, RecursionError):
            fail('STATE_CORRUPT')
        result = OperationRecoveryProjection('COMMITTED' if receipt else 'NOT_COMMITTED',
                    request.instance_id, request.generation, scope_values(request.scope),
                    request.producer, request.operation_id, request.action, root['revision'],
                    digest, receipt, attempt)
        result.to_json()  # 返回对象之前也强制检查完整输出边界。
        return result
