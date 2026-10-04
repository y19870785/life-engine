"""每安装一个可信本地 authority；不实现 Living policy 或真实 Host adapter。"""
from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import hmac
import threading
from pathlib import Path
from uuid import uuid4

from .domain import Principal, WorldScope, DomainId, IdKind
from .durable import registry, locked
from .living_domain import (LivingContext, LivingTickContext, canonical, fail, fingerprint,
                            instant, scope_values, text, LivingError)
from .living_host_capability import Capability, ExecutionPermit, CredentialVault
from .living_host_metadata import BindingMetadata
from .living_real_delivery import (BindingMode, ExecutionPurpose, PolicyDecision,
    RealDeliveryPolicy, TrustedDeliveryTarget, DeliveryContext,
    OneShotRealDeliveryGrant, validation_text)
from .living_recovery import LivingRecoveryContext, RecoveryDelegation, OperationRecoveryRequest
from .prompt import PromptSessionContext, PromptPurpose

MODES = ('LEGACY', 'LIVING_PENDING', 'LIVING_ACTIVE')
ROLES = {'tick': 'SCHEDULER', 'query_context': 'SESSION', 'prepare_contact': 'SESSION',
         'claim_attempt': 'EXECUTOR', 'observe_inbound': 'CONNECTOR',
         'submit_delivery_result': 'COLLECTOR', 'status': 'OWNER', 'recover_operation': 'RECOVERY'}
NO_REAL_SEND = True
_REAL_FACTORY_SEAL = object()


@dataclass(frozen=True)
class HostIdentityEnvelope:
    install_id: str
    instance_id: str
    host_identity: str
    principal: Principal
    scope: WorldScope
    producer: str
    invocation_id: str
    role: str
    provenance: str
    generation: str
    binding_revision: int
    binding_runtime_epoch: str
    plugin_epoch: str
    session: PromptSessionContext | None = None
    _seal: str = field(default='', repr=False)

    def identity(self):
        s = self.session
        return dict(install_id=self.install_id, instance_id=self.instance_id,
                    host_identity=self.host_identity, principal=str(self.principal.principal_id),
                    scope=scope_values(self.scope), producer=self.producer,
                    invocation_id=self.invocation_id, role=self.role, provenance=self.provenance,
                    generation=self.generation, binding_revision=self.binding_revision,
                    authority_epoch=self.binding_runtime_epoch, plugin_epoch=self.plugin_epoch,
                    session=None if s is None else dict(session_id=str(s.session_id),
                        writer_epoch=s.writer_epoch.value, world_revision=s.world_revision.value,
                        runtime_id=s.runtime_id, generation=s.generation, purpose=s.purpose.value,
                        principal=str(s.principal.principal_id), scope=scope_values(s.scope),
                        viewer=[s.viewer.kind.value, str(s.viewer.target)]))


class BindingAuthority:
    """仅可信部署代码可调用管理/签发 API；未提供模型 tool 或 JSON 权限入口。

    runtime/session factory 由可信部署拥有，reload 不重建 Core runtime。
    authority restart 接受该 factory 的当前 runtime，独立 epoch 不改 generation。
    """
    def __init__(self, runtime, directory, *, owner, scope, install_id, host_identity,
                 producer, target, initialize=False, isolated_test=False, test_key=None,
                 _real_factory=None, _real_target=None, _real_policy=None):
        if type(owner) is not Principal or type(scope) is not WorldScope or owner.owner_id != scope.owner_id:
            fail('AUTHORIZATION_DENIED')
        if test_key is not None and not isolated_test:
            fail('AUTHORIZATION_DENIED')
        for value in (install_id, host_identity, producer, target):
            text(value)
        self.runtime = runtime
        self.owner, self.scope = owner, scope
        self._recovery_principal = Principal(DomainId.new(IdKind.PRINCIPAL), owner.owner_id)
        self.install_id, self.host_identity, self.producer = install_id, host_identity, producer
        self._installation_evidence = fingerprint([str(runtime.repository.root), str(Path(directory).resolve())])
        self._isolated_test = isolated_test
        if _real_factory is not None and _real_factory is not _REAL_FACTORY_SEAL:
            fail('AUTHORIZATION_DENIED')
        if _real_factory is _REAL_FACTORY_SEAL:
            if (type(_real_target) is not TrustedDeliveryTarget
                    or target != _real_target.key
                    or not isinstance(_real_policy, RealDeliveryPolicy)
                    or _real_target.binding != host_identity
                    or _real_target.owner != str(owner.principal_id)):
                fail('REAL_POLICY_DENIED')
        self.execution_mode = (BindingMode.REAL_DELIVERY if _real_factory is _REAL_FACTORY_SEAL
                               else BindingMode.SIMULATION)
        self._real_target = _real_target
        self._real_policy = _real_policy
        self._real_grants = {}
        self._real_grant_history = set()
        self._real_issued = set()
        self._mutex = threading.RLock()
        self._closed = False
        self.binding_runtime_epoch, self.plugin_epoch = uuid4().hex, uuid4().hex
        initial = dict(install_id=install_id, instance_id=runtime.repository.instance_id,
                       installation_evidence=self._installation_evidence,
                       host_identity=host_identity, owner=str(owner.principal_id),
                       scope=scope_values(scope), producer=producer, target=target,
                       mode='LIVING_PENDING', revision=1, correlations={}, inbound={}) if initialize else None
        if initial is not None:
            try:
                runtime.status(self.context())
            except LivingError as exc:
                if exc.code != 'LIVING_BINDING_REQUIRED':
                    raise
                initial['mode'] = 'LEGACY'
        self._install_lease = locked(runtime.repository.root, 'binding-' + fingerprint(install_id), timeout=0)
        try:
            self._install_lease.__enter__()
        except TimeoutError:
            fail('AUTHORITY_ALREADY_RUNNING')
        try:
            self._metadata = BindingMetadata(directory, initial=initial, test_key=test_key)
        except BaseException:
            self._install_lease.__exit__(None, None, None)
            self._install_lease = None
            raise
        self._vault = CredentialVault(self._metadata._key)
        self._associations = {}  # Core 投影的当前进程关联；不持久声明 Attempt truth。
        self._pending = set()
        self._permit_sessions = {}
        self._snapshots = {}
        try:
            data = self._data()
            if data['target'] != target:
                fail('BINDING_MISMATCH')
            self._reconcile = any(x['action'] == 'begin_attempt' for x in data['correlations'].values())
        except BaseException:
            self.close()
            raise

    def __repr__(self):
        return '<BindingAuthority local NO_REAL_SEND>'

    def _generation(self):
        repo = self.runtime.repository
        current = registry(repo.root)['instances'][repo.instance_id]['generation']
        if current != repo.generation:
            fail('GENERATION_STALE')
        return current

    def _data(self):
        if self._closed:
            fail('AUTHORITY_CLOSED')
        data = self._metadata.read()
        required = {'install_id', 'instance_id', 'installation_evidence', 'host_identity', 'owner', 'scope', 'producer',
                    'target', 'mode', 'revision', 'correlations', 'inbound'}
        if type(data) is not dict or set(data) != required or data['mode'] not in MODES:
            fail('BINDING_CORRUPT')
        expected = dict(install_id=self.install_id, instance_id=self.runtime.repository.instance_id,
                        installation_evidence=self._installation_evidence,
                        host_identity=self.host_identity, owner=str(self.owner.principal_id),
                        scope=list(scope_values(self.scope)), producer=self.producer)
        if any(data[k] != v for k, v in expected.items()):
            fail('BINDING_MISMATCH')
        return data

    def close(self):
        with self._mutex:
            self._closed = True
            self._vault.revoke()
            self._revoke_real_grants()
            self._snapshots.clear()
            self._metadata.close()
            if self._install_lease is not None:
                self._install_lease.__exit__(None, None, None)
                self._install_lease = None

    def route(self, legacy_callback):
        """唯一 legacy dispatch fence；决定在回调及任何副作用之前完成。"""
        with self._mutex:
            if self._data()['mode'] != 'LEGACY':
                fail('LIVING_HANDOFF_REQUIRED')
            # metadata 决定路由；Core enrollment 真源只用于拒绝不一致的 legacy side effect。
            try:
                self.runtime.status(self.context())
            except LivingError as exc:
                if exc.code != 'LIVING_BINDING_REQUIRED':
                    raise
            else:
                fail('LIVING_HANDOFF_REQUIRED')
            return legacy_callback()

    def set_mode(self, mode):
        """受信本地 Owner 管理面；不能由 tool 参数调用。"""
        with self._mutex:
            data = self._data()
            if mode not in MODES:
                fail('INVALID_ARGUMENT')
            if data['mode'] != 'LEGACY' and mode == 'LEGACY':
                fail('LIVING_HANDOFF_REQUIRED')
            if mode == 'LIVING_ACTIVE':
                state = self.runtime.status(self.context())
                if state['root']['target'] != data['target']:
                    fail('TARGET_MISMATCH')
            data['mode'], data['revision'] = mode, data['revision'] + 1
            self._metadata.write(data)
            self._revoke()

    def update_target(self, target):
        """只更新已被 Core Owner command 确认的路由；不修改业务 target。"""
        with self._mutex:
            text(target)
            data = self._data()
            if self.runtime.status(self.context())['root']['target'] != target:
                fail('TARGET_MISMATCH')
            data['target'], data['revision'] = target, data['revision'] + 1
            self._metadata.write(data)
            self._revoke()

    def _revoke(self):
        self._vault.revoke()
        self._revoke_real_grants()
        self._snapshots.clear()
        self._permit_sessions.clear()
        if self._pending:
            self._reconcile = True

    def reload_plugin(self):
        with self._mutex:
            self._data()
            self.plugin_epoch = uuid4().hex
            self._revoke()

    @contextmanager
    def lifecycle_transition(self):
        """可信管理面把 Core pause/target/restore 等 transition 与外部消费串行。

        不决定 Core policy；调用者仅在此执行已授权的 Core 管理操作，不运行 transport。
        即使管理操作失败也撤销旧权限，不恢复旧执行资格。
        """
        with self._mutex:
            self._data()
            try:
                yield
            finally:
                self._revoke()

    def context(self, envelope=None):
        return LivingContext(self.owner, self.scope, self._generation(), self.producer,
                             None if envelope is None else envelope.session)

    def envelope(self, role, invocation_id, *, session=None, provenance='LOCAL_TRUSTED'):
        """来自认证 connector/executor 的受信输入；模型 JSON 无法构造有效 seal。"""
        with self._mutex:
            data = self._data(); text(invocation_id)
            if role not in set(ROLES.values()) or provenance not in ('LOCAL_TRUSTED', 'EXTERNAL_USER'):
                fail('AUTHORIZATION_DENIED')
            if role in ('SESSION', 'EXECUTOR') and type(session) is not PromptSessionContext:
                fail('SESSION_STALE')
            if session is not None:
                if type(session) is not PromptSessionContext:
                    fail('SESSION_STALE')
                if session.principal != self.owner or session.scope != self.scope:
                    fail('SCOPE_MISMATCH')
                if session.runtime_id != self.runtime.repository.runtime_id:
                    fail('SESSION_STALE')
                if session.generation != self._generation():
                    fail('GENERATION_STALE')
                if session.purpose is not PromptPurpose.SOUL_RESPONSE:
                    fail('UNSUPPORTED_PURPOSE')
            e = HostIdentityEnvelope(self.install_id, self.runtime.repository.instance_id,
                self.host_identity, self.owner, self.scope, self.producer, invocation_id, role,
                provenance, self._generation(), data['revision'], self.binding_runtime_epoch,
                self.plugin_epoch, session)
            from dataclasses import replace
            return replace(e, _seal=self._seal(e))

    def _seal(self, envelope):
        raw = canonical(envelope.identity()).encode('utf-8')
        if len(raw) > 8192:
            fail('BUDGET_INPUT')
        return hmac.new(self._metadata._key, raw, hashlib.sha256).hexdigest()

    def _validate_envelope(self, e, method):
        data = self._data()
        if type(e) is not HostIdentityEnvelope:
            fail('AUTHORIZATION_DENIED')
        if e.role != ROLES.get(method):
            fail('CAPABILITY_DENIED')
        if e.generation != self._generation():
            fail('GENERATION_STALE')
        if (e.binding_runtime_epoch != self.binding_runtime_epoch or e.plugin_epoch != self.plugin_epoch
                or e.binding_revision != data['revision']):
            fail('CAPABILITY_STALE')
        if not hmac.compare_digest(e._seal, self._seal(e)):
            fail('AUTHORIZATION_DENIED')
        if data['mode'] != 'LIVING_ACTIVE':
            fail('LIVING_NOT_ACTIVE')
        if method == 'observe_inbound' and e.provenance != 'EXTERNAL_USER':
            fail('INBOUND_UNVERIFIED')
        return data

    def _claims(self, envelope, method, payload):
        data = self._validate_envelope(envelope, method)
        claims = dict(identity=fingerprint(envelope.identity()), install_id=self.install_id,
                    instance_id=self.runtime.repository.instance_id, revision=data['revision'],
                    authority_epoch=self.binding_runtime_epoch, plugin_epoch=self.plugin_epoch,
                    generation=self._generation(), method=method, invocation=envelope.invocation_id,
                    target=data['target'], payload_digest=fingerprint(payload))
        if method == 'recover_operation':
            if type(payload) is not dict or set(payload) != {'operation_id'}:
                fail('INVALID_ARGUMENT')
            text(payload['operation_id'])
            _, request = self.recovery(payload['operation_id'])
            from dataclasses import asdict
            from .living_domain import scope_values
            identity = asdict(request)
            identity['scope'] = scope_values(request.scope)
            claims['recovery_identity_digest'] = fingerprint(identity)
        return claims

    def issue(self, envelope, method, payload, *, ttl=30):
        with self._mutex:
            if type(ttl) is not int or not 0 < ttl <= 60:
                fail('INVALID_ARGUMENT')
            claims = self._claims(envelope, method, payload)
            claims['expiry'] = instant(self.runtime.clock()) + ttl
            return self._vault.issue(Capability, claims)

    @contextmanager
    def authorized(self, envelope, capability, method, payload):
        with self._mutex:
            claims = self._claims(envelope, method, payload)
            self._vault.consume(capability, Capability, claims, instant(self.runtime.clock()))
            from .world_repository import WorldRuntimeError
            try:
                yield self._data()
            except WorldRuntimeError as exc:
                fail(exc.code.value)

    def correlate(self, envelope, action, payload):
        """先于 Core command 原子保存；不保存 receipt、Attempt 或执行状态。"""
        data = self._data()
        identity = dict(instance_id=self.runtime.repository.instance_id, generation=self._generation(),
                        scope=list(scope_values(self.scope)), producer=self.producer,
                        operation_id=envelope.invocation_id, action=action,
                        original_actor=str(self.owner.principal_id),
                        expected_payload_digest=fingerprint([action, payload, scope_values(self.scope),
                                                             str(self.owner.principal_id)]))
        key = fingerprint([identity['generation'], self.producer, envelope.invocation_id])
        old = data['correlations'].get(key)
        if old is not None and old != identity:
            fail('IDEMPOTENCY_CONFLICT')
        data['correlations'][key] = identity
        self._metadata.write(data)
        return key

    def recovery(self, operation_id):
        """当前认证 Owner、exact Scope、原 actor/producer 委托，只包装 B1。"""
        data = self._data()
        generation = self._generation()
        key = fingerprint([generation, self.producer, operation_id])
        identity = data['correlations'].get(key)
        if identity is None:
            fail('RECOVERY_IDENTITY_MISSING')
        delegation = RecoveryDelegation(self.owner, self._recovery_principal, self.owner, self.scope,
            self.runtime.repository.instance_id, generation, self.producer,
            'binding-authority:' + self.binding_runtime_epoch)
        request = OperationRecoveryRequest(self.runtime.repository.instance_id, generation,
            self.scope, self.producer, operation_id, identity['action'], identity['expected_payload_digest'])
        return LivingRecoveryContext(self._recovery_principal, delegation), request

    def _issue_permit(self, e, result):
        if self.execution_mode is not BindingMode.SIMULATION:
            fail('CAPABILITY_DENIED')
        if result.get('execute') is not True or result.get('state') != 'CLAIMED':
            fail('CAPABILITY_DENIED')
        claims = self._claims(e, 'claim_attempt', {})
        claims.update(attempt=result['attempt_id'], purpose='SIMULATED_CONTACT',
                      expiry=instant(self.runtime.clock()) + 10)
        self._pending.add(result['attempt_id'])
        self._permit_sessions[result['attempt_id']] = e.session
        return self._vault.issue(ExecutionPermit, claims)

    def _revoke_real_grants(self):
        for grant in self._real_grants.values():
            grant.revoke()
        self._real_grants.clear()
        self._real_issued.clear()

    def _real_context(self, e, intent, attempt, payload_digest):
        if (self.execution_mode is not BindingMode.REAL_DELIVERY
                or type(self._real_target) is not TrustedDeliveryTarget or e.session is None):
            fail('REAL_POLICY_DENIED')
        data = self._validate_envelope(e, 'claim_attempt')
        if data['target'] != self._real_target.key:
            fail('TARGET_MISMATCH')
        return DeliveryContext(self.host_identity, self.binding_runtime_epoch,
            self.plugin_epoch, self._generation(), self._real_target, intent, attempt,
            e.invocation_id, ExecutionPurpose.REAL_CONTACT, data['mode'], e.session,
            payload_digest)

    def _issue_real_permit(self, e, result, intent):
        """Only the first Core execute=true result may spend a preinstalled grant."""
        if result.get('execute') is not True or result.get('state') != 'CLAIMED':
            fail('CAPABILITY_DENIED')
        grant = self._real_grants.get((intent, e.invocation_id))
        if grant is None:
            self._reconcile = True
            return None
        now = instant(self.runtime.clock())
        try:
            context = self._real_context(e, intent, result['attempt_id'], grant.payload_digest)
            grant.reserve(self, context, now)
            decision = self._real_policy.decide(context)
            if decision is not PolicyDecision.ALLOW:
                fail('REAL_POLICY_DENIED')
            claims = self._claims(e, 'claim_attempt', {})
            claims.update(binding=self.host_identity, intent=intent, attempt=result['attempt_id'],
                          target=self._real_target.key,
                          purpose=ExecutionPurpose.REAL_CONTACT.value,
                          real_payload_digest=grant.payload_digest,
                          expiry=min(now + 10, grant.expiry))
            if claims['expiry'] <= now:
                fail('REAL_GRANT_DENIED')
            permit = self._vault.issue(ExecutionPermit, claims)
            grant.state = 'SPENT'
            self._real_issued.add(result['attempt_id'])
            self._permit_sessions[result['attempt_id']] = e.session
            self._pending.add(result['attempt_id'])
            return permit
        except Exception:
            grant.revoke()
            self._reconcile = True
            return None

    @contextmanager
    def consume_permit(self, permit, *, target, attempt, invocation, purpose='SIMULATED_CONTACT'):
        """锁覆盖 consume→本地 fake side effect，Core transaction 已结束。"""
        with self._mutex:
            if self.execution_mode is not BindingMode.SIMULATION:
                fail('CAPABILITY_DENIED')
            if purpose != ExecutionPurpose.SIMULATED_CONTACT.value:
                fail('CAPABILITY_DENIED')
            data = self._data()
            if data['mode'] != 'LIVING_ACTIVE':
                fail('LIVING_NOT_ACTIVE')
            expected = dict(install_id=self.install_id, instance_id=self.runtime.repository.instance_id,
                revision=data['revision'], generation=self._generation(),
                authority_epoch=self.binding_runtime_epoch, plugin_epoch=self.plugin_epoch,
                target=target, attempt=attempt, invocation=invocation, purpose=purpose)
            root = self.runtime.status(self.context())['root']
            if target != data['target'] or root['target'] != target:
                fail('TARGET_MISMATCH')
            if root['paused'] or not root['enabled']:
                self._revoke()
                fail('EXECUTION_REVOKED')
            session = self._permit_sessions.get(attempt)
            if session is not None:
                from .living_domain import LivingContext
                self.runtime.status(LivingContext(self.owner, self.scope, self._generation(), self.producer, session))
            # restore 使用同一 management barrier；最后 generation fence 与消费原子排序。
            # 不在该非重入锁内调用 Core，不把安装锁带入外部 transport。
            with locked(self.runtime.repository.root, 'management'):
                expected['generation'] = self._generation()
                self._vault.consume(permit, ExecutionPermit, expected, instant(self.runtime.clock()))
            self._permit_sessions.pop(attempt, None)
            yield

    @contextmanager
    def _consume_real_permit(self, permit, *, target, intent, attempt, invocation, payload):
        """One atomic local admission; the caller may only enter a local intercept."""
        with self._mutex:
            data = self._data()
            if (self.execution_mode is not BindingMode.REAL_DELIVERY
                    or data['mode'] != 'LIVING_ACTIVE'
                    or type(target) is not TrustedDeliveryTarget
                    or target != self._real_target or target.key != data['target']):
                fail('REAL_POLICY_DENIED')
            digest = validation_text(payload)
            grant = self._real_grants.get((intent, invocation))
            if (grant is None or grant.state != 'SPENT' or grant.attempt != attempt
                    or grant.payload_digest != digest or grant.target != target):
                fail('REAL_GRANT_DENIED')
            if attempt not in self._real_issued:
                fail('CAPABILITY_STALE')
            root = self.runtime.status(self.context())['root']
            if root['target'] != target.key or root['paused'] or not root['enabled']:
                self._revoke()
                fail('EXECUTION_REVOKED')
            session = self._permit_sessions.get(attempt)
            if session is None:
                fail('SESSION_STALE')
            self.runtime.status(LivingContext(self.owner, self.scope, self._generation(),
                                              self.producer, session))
            context = DeliveryContext(self.host_identity, self.binding_runtime_epoch,
                self.plugin_epoch, self._generation(), target, intent, attempt, invocation,
                ExecutionPurpose.REAL_CONTACT, data['mode'], session, digest)
            try:
                decision = self._real_policy.decide(context)
            except Exception:
                decision = PolicyDecision.DENY
            if decision is not PolicyDecision.ALLOW:
                self._revoke()
                fail('REAL_POLICY_DENIED')
            expected = dict(install_id=self.install_id,
                instance_id=self.runtime.repository.instance_id, revision=data['revision'],
                generation=self._generation(), binding=self.host_identity,
                authority_epoch=self.binding_runtime_epoch,
                plugin_epoch=self.plugin_epoch, target=target.key, intent=intent,
                attempt=attempt, invocation=invocation,
                purpose=ExecutionPurpose.REAL_CONTACT.value,
                real_payload_digest=digest)
            with locked(self.runtime.repository.root, 'management'):
                expected['generation'] = self._generation()
                self._vault.consume(permit, ExecutionPermit, expected,
                                    instant(self.runtime.clock()))
            self._real_issued.remove(attempt)
            self._permit_sessions.pop(attempt, None)
            yield


class RealDeliveryBindingFactory:
    """Trusted local deployment surface; never expose it as a model/tool API."""
    def __init__(self, policy, target):
        if not isinstance(policy, RealDeliveryPolicy) or type(target) is not TrustedDeliveryTarget:
            fail('REAL_POLICY_DENIED')
        self.policy, self.target = policy, target

    def create(self, runtime, directory, *, owner, scope, install_id, host_identity,
               producer, initialize=False, isolated_test=False, test_key=None):
        return BindingAuthority(runtime, directory, owner=owner, scope=scope,
            install_id=install_id, host_identity=host_identity, producer=producer,
            target=self.target.key, initialize=initialize, isolated_test=isolated_test,
            test_key=test_key, _real_factory=_REAL_FACTORY_SEAL,
            _real_target=self.target, _real_policy=self.policy)

    def one_shot(self, authority, *, intent, invocation, payload, ttl=30):
        if type(ttl) is not int or not 0 < ttl <= 60:
            fail('INVALID_ARGUMENT')
        text(intent); text(invocation)
        digest = validation_text(payload)
        with authority._mutex:
            authority._data()
            if (authority.execution_mode is not BindingMode.REAL_DELIVERY
                    or authority._real_policy is not self.policy
                    or authority._real_target != self.target):
                fail('REAL_POLICY_DENIED')
            if authority._generation() != authority.runtime.repository.generation:
                fail('GENERATION_STALE')
            key = (intent, invocation)
            if key in authority._real_grant_history:
                fail('REAL_GRANT_SPENT')
            grant = OneShotRealDeliveryGrant(authority, self.target, intent,
                invocation, digest, instant(authority.runtime.clock()) + ttl)
            authority._real_grants[key] = grant
            authority._real_grant_history.add(key)
            return grant

    def replace_policy(self, authority, policy):
        if not isinstance(policy, RealDeliveryPolicy):
            fail('REAL_POLICY_DENIED')
        with authority._mutex:
            authority._data()
            if authority._real_policy is not self.policy:
                fail('REAL_POLICY_DENIED')
            authority._real_policy = policy
            authority._revoke()
        self.policy = policy
