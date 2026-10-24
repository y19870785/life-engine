"""Memory 授权服务；不接宿主、模型、Story、Lore 或跨域 Bridge。"""
from dataclasses import replace
from datetime import datetime, timezone
from functools import wraps
import hashlib
import hmac
import secrets

from .domain import (BindingStatus, CanonStatus, DomainError, DomainId, IdKind, SourceType, Provenance,
                     WorldKind, WorldStatus, require, check_id, RealityStatus)
from .memory import (AudienceKind, MemoryAudience, MemoryCollectionRevision, MemoryKind,
    MemoryLifecycle, MemoryRecord, MemoryQueryResult, OwnerMemoryContext, SessionMemoryContext,
    IdempotencyIdentity, MAX_QUERY_BYTES, MAX_LIMIT, bounded_text, SubjectKind)
from .memory_control import fingerprint, scope_values
from .memory_repository import MemoryFailure as MC, MemoryRuntimeError, deny
from .world_codec import provenance_dump
from .world_repository import FailureCode as WC, WorldRuntimeError


def checked(method):
    @wraps(method)
    def call(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except (MemoryRuntimeError, WorldRuntimeError):
            raise
        except (DomainError, TypeError):
            deny(MC.INVALID_ARGUMENT)
    return call


def authorize(tx, context, *, owner=False, deletion=False):
    if type(context) not in (OwnerMemoryContext, SessionMemoryContext) or (owner and type(context) is not OwnerMemoryContext):
        deny(MC.AUTHORIZATION_DENIED)
    scope = context.scope
    world = tx.world.get_world(scope.world_id)
    if world.timeline.scope != scope or context.principal.owner_id != scope.owner_id:
        deny(MC.AUTHORIZATION_DENIED)
    if world.world.status is WorldStatus.TOMBSTONED and not (deletion and type(context) is OwnerMemoryContext):
        deny(MC.NOT_AVAILABLE)
    if type(context) is SessionMemoryContext:
        binding = tx.world.get_session(context.session_id)
        if (binding.principal != context.principal or binding.scope != scope or binding.status is not BindingStatus.OPEN
                or world.world.status is not WorldStatus.ACTIVE or binding.writer_epoch != context.writer_epoch
                or binding.writer_epoch != world.world.writer_epoch):
            deny(MC.AUTHORIZATION_DENIED)
        viewer = MemoryAudience(AudienceKind.CHARACTER_INSTANCE, binding.character_instance_id) if world.world.kind is WorldKind.ROLEPLAY else MemoryAudience(AudienceKind.SOUL, scope.soul_id)
        if viewer != context.viewer:
            deny(MC.AUTHORIZATION_DENIED)
    tx.guard(scope)
    return world


def validate_record(tx, record):
    """持久不变式与来源资格检查；读取坏行时调用方映射为损坏。"""
    scope, p = record.scope, record.provenance
    bounded_text(p.source_id,512)
    world = tx.world.get_world(scope.world_id)
    if world.timeline.scope != scope:
        deny(MC.AUTHORIZATION_DENIED)
    if p.source_type is SourceType.BRIDGE or p.source_event_id is not None:
        deny(MC.INVALID_SOURCE)
    allowed = {
        SourceType.MODEL: (RealityStatus.FICTIONAL,RealityStatus.AGENT_INFERRED),
        SourceType.USER_REPORT: (RealityStatus.USER_CLAIMED,),
        SourceType.SIMULATION: (RealityStatus.SIMULATED_LIFE_STATE,),
        SourceType.IMPORT: (RealityStatus.UNKNOWN,),
        SourceType.LEGACY: (RealityStatus.LEGACY_UNREVIEWED,),
        SourceType.OWNER_COMMAND: (RealityStatus.USER_CLAIMED,RealityStatus.FICTIONAL,RealityStatus.UNKNOWN),
        # 角色扮演回忆只能以"虚构共同经历"存在，永远不能升级为现实事实。
        SourceType.ROLEPLAY_RECALL: (RealityStatus.FICTIONAL_SHARED_EXPERIENCE,),
    }
    if p.source_type not in allowed or p.reality_status not in allowed[p.source_type]:
        deny(MC.INVALID_SOURCE)
    if p.source_type is SourceType.ROLEPLAY_RECALL:
        # 回忆录必须指向**另一个**世界，且该世界由同一 Soul 持有。
        # 这里只做结构校验、不查源世界：否则源 RP World 归档或删除后，
        # 既有回忆录会在读路径被判为损坏。源世界的真实性在写入时校验。
        if (p.source_world_id is None or p.source_timeline_id is None
                or p.source_world_id == scope.world_id):
            deny(MC.INVALID_SOURCE)
        if p.source_session_id is not None:
            # 首版不携带源会话引用，避免读路径跨世界查表。
            deny(MC.INVALID_SOURCE)
        if world.world.kind is not WorldKind.SOUL:
            deny(MC.INVALID_SOURCE)
        if record.kind is not MemoryKind.SHARED_EXPERIENCE:
            deny(MC.INVALID_ARGUMENT)
        if record.audience != (MemoryAudience(AudienceKind.SOUL, scope.soul_id),):
            deny(MC.AUTHORIZATION_DENIED)
        if any(subject.kind is not SubjectKind.TEXT for subject in record.subjects):
            deny(MC.INVALID_SOURCE)
    else:
        if ((p.source_world_id is not None and p.source_world_id != scope.world_id) or
                (p.source_timeline_id is not None and p.source_timeline_id != scope.timeline_id)):
            deny(MC.INVALID_SOURCE)
        if p.source_session_id is not None:
            source_session = tx.world.get_session(p.source_session_id)
            if source_session.scope != scope or source_session.principal != p.actor:
                deny(MC.INVALID_SOURCE)
    for a in record.audience:
        if a.kind is AudienceKind.CHARACTER_INSTANCE:
            if tx.world.get_character(a.target).scope != scope:
                deny(MC.AUTHORIZATION_DENIED)
        elif a.kind is AudienceKind.USER and a.target != scope.owner_id:
            deny(MC.AUTHORIZATION_DENIED)
        elif a.kind is AudienceKind.SOUL:
            if world.world.kind is not WorldKind.SOUL or a.target != scope.soul_id:
                deny(MC.AUTHORIZATION_DENIED)
        elif a.kind is AudienceKind.PRINCIPAL:
            # 首版没有主体登记服务，不能将 UUID 当成受信登记证明。
            deny(MC.AUTHORIZATION_DENIED)
    for s in record.subjects:
        if s.kind is SubjectKind.CHARACTER_INSTANCE and tx.world.get_character(s.target).scope != scope:
            deny(MC.AUTHORIZATION_DENIED)
        if s.kind is SubjectKind.WORLD and s.target != scope.world_id:
            deny(MC.AUTHORIZATION_DENIED)
        if s.kind is SubjectKind.SOUL and s.target != scope.soul_id:
            deny(MC.AUTHORIZATION_DENIED)



def recall_source_identity(provenance):
    """Canon/生命周期与正文修订不是换源；来源引用变化则必须重新验源。"""
    return (provenance.actor, provenance.source_type, provenance.source_id,
            provenance.source_world_id, provenance.source_timeline_id, provenance.source_session_id)


def validate_recall_write(tx, record, old):
    """与 CAS/insert 同一事务封闭泛入口；旧回忆的生命周期不依赖源继续存在。"""
    p = record.provenance
    old_recall = old is not None and old.provenance.source_type is SourceType.ROLEPLAY_RECALL
    if old_recall and p.source_type is not SourceType.ROLEPLAY_RECALL:
        # 不能先把回忆录脱壳成普通来源，再绕过虚构与受众约束。
        deny(MC.INVALID_SOURCE)
    if p.source_type is not SourceType.ROLEPLAY_RECALL:
        return
    if old_recall and recall_source_identity(p) == recall_source_identity(old.provenance):
        return
    try:
        source = tx.world.get_world(p.source_world_id)
    except WorldRuntimeError as exc:
        if exc.code is WC.WORLD_NOT_FOUND:
            deny(MC.INVALID_SOURCE)
        raise
    if (source.world.kind is not WorldKind.ROLEPLAY
            or (source.world.owner_id, source.world.soul_id) != (record.scope.owner_id, record.scope.soul_id)
            or source.timeline.scope.timeline_id != p.source_timeline_id):
        deny(MC.INVALID_SOURCE)



def available(tx, record, seen=None):
    pending, visited = [(record,frozenset())], set()
    while pending:
        current, ancestors = pending.pop()
        if current is None or current.lifecycle in (MemoryLifecycle.HIDDEN, MemoryLifecycle.TOMBSTONED):
            return False
        if tx.blocked(current.scope,memory_id=current.memory_id):
            return False
        if current.memory_id in ancestors:
            deny(MC.INVALID_SOURCE)
        if current.memory_id in visited:
            continue
        visited.add(current.memory_id)
        if len(visited)>1000:
            deny(MC.INVALID_SOURCE)
        pending.extend((tx.get(current.scope,source),ancestors|{current.memory_id}) for source in current.lineage)
    return True


class MemoryRuntime:
    """Owner 管理与会话用途明确分离，Principal 的真实性由可信入口负责。"""
    def __init__(self, repository):
        self.repository = repository
        self._version_key = secrets.token_bytes(32)

    @checked
    def collection_revision(self, context):
        with self.repository.transaction() as tx:
            authorize(tx, context, owner=True)
            return tx.revision(context.scope)

    @checked
    def create_session_candidate(self, context, expected_revision, identity, *, content, kind, provenance,
                                 audience=None, subjects=(), lineage=()):
        require(context, SessionMemoryContext)
        require(provenance,Provenance)
        if provenance.canon_status is not CanonStatus.CANDIDATE or provenance.actor != context.principal:
            deny(MC.INVALID_SOURCE)
        if provenance.source_type is not SourceType.MODEL or provenance.reality_status not in (RealityStatus.FICTIONAL, RealityStatus.AGENT_INFERRED):
            deny(MC.INVALID_SOURCE)
        if (provenance.source_world_id,provenance.source_timeline_id,provenance.source_session_id) != (
                context.scope.world_id,context.scope.timeline_id,context.session_id):
            deny(MC.INVALID_SOURCE)
        audience = (context.viewer,) if audience is None else audience
        if audience != (context.viewer,):
            deny(MC.AUTHORIZATION_DENIED)
        return self._create(context, expected_revision, identity, content, kind, provenance, audience, subjects, lineage)

    @checked
    def create_owner_memory(self, context, expected_revision, identity, *, content, kind, provenance,
                            audience, subjects=(), lineage=()):
        if type(context) is not OwnerMemoryContext:
            deny(MC.AUTHORIZATION_DENIED)
        require(provenance,Provenance)
        if provenance.actor != context.principal:
            deny(MC.INVALID_SOURCE)
        # 没有可信观测适配器时，管理断言也不能伪装为观测证据。
        if provenance.source_type is SourceType.OBSERVATION:
            deny(MC.INVALID_SOURCE)
        return self._create(context, expected_revision, identity, content, kind, provenance, audience, subjects, lineage)

    @checked
    def create_roleplay_recall(self, context, expected_revision, identity, *, content, provenance,
                               kind=None, audience=None, subjects=()):
        """Owner 把一次角色扮演会话的派生摘要登记进 Soul World。

        写入时确认源世界真实存在、属于同一 Owner/Soul 且为 ROLEPLAY，目标必须是
        Soul World；读路径不回查源世界，因此源 RP World 归档后回忆录仍可读。
        回忆录默认 CANDIDATE，须显式 accept 才进入正常会话检索。
        subjects 只接受 TEXT：跨世界的 CHARACTER_INSTANCE/WORLD 主体会被拒绝。
        """
        if type(context) is not OwnerMemoryContext:
            deny(MC.AUTHORIZATION_DENIED)
        require(provenance, Provenance)
        if provenance.actor != context.principal:
            deny(MC.INVALID_SOURCE)
        if provenance.source_type is not SourceType.ROLEPLAY_RECALL:
            deny(MC.INVALID_SOURCE)
        if provenance.source_world_id is None or provenance.source_timeline_id is None:
            deny(MC.INVALID_SOURCE)
        if kind is None:
            kind = MemoryKind.SHARED_EXPERIENCE
        require(kind, MemoryKind)
        if kind is not MemoryKind.SHARED_EXPERIENCE:
            deny(MC.INVALID_ARGUMENT)
        soul_audience = (MemoryAudience(AudienceKind.SOUL, context.scope.soul_id),)
        if audience is None:
            audience = soul_audience
        elif tuple(audience) != soul_audience:
            # 回忆录只属于 Soul；不允许扩成 World 或角色受众。
            deny(MC.AUTHORIZATION_DENIED)
        return self._create(context, expected_revision, identity, content, kind, provenance,
                            audience, subjects, ())


    def _create(self, context, expected, identity, content, kind, provenance, audience, subjects, lineage):
        record = MemoryRecord(DomainId.new(IdKind.MEMORY),context.scope,kind,content,1,provenance,audience,subjects,
                              MemoryLifecycle.LIVE,datetime.now(timezone.utc),lineage=tuple(sorted(lineage,key=str)))
        return self._mutate(context, expected, identity, 'create', record=record)

    @checked
    def accept_memory(self, context, memory_id, expected_revision, identity):
        return self._mutate(context,expected_revision,identity,'accept',target=memory_id)

    @checked
    def reject_memory(self, context, memory_id, expected_revision, identity):
        return self._mutate(context,expected_revision,identity,'reject',target=memory_id)

    @checked
    def supersede_memory(self, context, memory_id, expected_revision, identity, *, content, provenance):
        require(provenance,Provenance)
        from .memory import MAX_CONTENT_BYTES
        bounded_text(content,MAX_CONTENT_BYTES)
        return self._mutate(context,expected_revision,identity,'supersede',target=memory_id,content=content,provenance=provenance)

    @checked
    def change_audience(self, context, memory_id, expected_revision, identity, *, audience):
        from .memory import audiences
        audience = audiences(audience)
        return self._mutate(context,expected_revision,identity,'audience_change',target=memory_id,audience=audience)

    @checked
    def hide_memory(self, context, memory_id, expected_revision, identity):
        return self._mutate(context,expected_revision,identity,'hide',target=memory_id)

    @checked
    def unhide_memory(self, context, memory_id, expected_revision, identity):
        return self._mutate(context,expected_revision,identity,'unhide',target=memory_id)

    @checked
    def delete_memory(self, context, memory_id, expected_revision, identity):
        return self.repository.delete(context,memory_id,expected_revision,identity)

    def _mutate(self, context, expected, identity, action, *, record=None, target=None, content=None, provenance=None, audience=None):
        require(expected, MemoryCollectionRevision)
        require(identity, IdempotencyIdentity)
        if target is not None:
            check_id(target,IdKind.MEMORY)
        payload = [action,scope_values(context.scope),str(target),content,
                   provenance_dump(provenance) if provenance else None,
                   [(a.kind.value,str(a.target)) for a in audience] if audience else None]
        if record:
            payload += [record.content,record.kind.value,provenance_dump(record.provenance),
                        [(a.kind.value,str(a.target)) for a in record.audience],
                        [(s.kind.value,str(s.target),s.text) for s in record.subjects],list(map(str,record.lineage))]
        stamp = fingerprint(payload)
        with self.repository.transaction() as tx:
            authorize(tx,context,owner=action!='create')
            replay = tx.replay(context,identity,stamp)
            if replay:
                return replay
            old = tx.get(context.scope,target) if target else None
            if target:
                if old is None or old.superseded_by or old.lifecycle is MemoryLifecycle.TOMBSTONED or tx.blocked(context.scope,memory_id=target):
                    deny(MC.NOT_AVAILABLE)
                if action in ('accept','reject') and old.provenance.canon_status not in (CanonStatus.CANDIDATE,CanonStatus.UNREVIEWED):
                    deny(MC.INVALID_ARGUMENT)
                if action in ('hide','unhide'):
                    desired = MemoryLifecycle.HIDDEN if action=='hide' else MemoryLifecycle.LIVE
                    if old.lifecycle is desired:
                        if tx.revision(context.scope) != expected:
                            deny(MC.REVISION_CONFLICT)
                        from .memory import MemoryReceipt
                        return MemoryReceipt(old.memory_id,tx.revision(context.scope))
                    if old.lifecycle not in (MemoryLifecycle.LIVE,MemoryLifecycle.HIDDEN):
                        deny(MC.NOT_AVAILABLE)
                    record = replace(old,lifecycle=desired)
                else:
                    p = old.provenance
                    if action in ('accept','reject'):
                        p = replace(p,canon_status=CanonStatus.ACCEPTED if action=='accept' else CanonStatus.REJECTED)
                    if action=='supersede':
                        p = provenance
                        if p.actor != context.principal or p.source_type is SourceType.OBSERVATION:
                            deny(MC.INVALID_SOURCE)
                    record = replace(old,memory_id=DomainId.new(IdKind.MEMORY),content_version=old.content_version+1,
                        content=content if content is not None else old.content,provenance=p,
                        audience=audience if audience is not None else old.audience,
                        predecessor=old.memory_id,superseded_by=None,lifecycle=MemoryLifecycle.LIVE,
                        created_at=datetime.now(timezone.utc))
            validate_record(tx,record)
            validate_recall_write(tx,record,old)
            p = record.provenance
            if tx.blocked(context.scope,source=(str(p.actor.principal_id),p.source_type.value,p.source_id)):
                deny(MC.NOT_AVAILABLE)
            source_canons = set()
            for source_id in record.lineage:
                source = tx.get(context.scope,source_id)
                if not available(tx,source):
                    deny(MC.INVALID_SOURCE)
                source_canons.add(source.provenance.canon_status)
                if (source.provenance.reality_status != p.reality_status or
                        (MemoryAudience(AudienceKind.WORLD) not in source.audience and not set(record.audience)<=set(source.audience))):
                    deny(MC.INVALID_SOURCE)
            if len(source_canons)>1:
                deny(MC.INVALID_SOURCE)
            if record.kind is MemoryKind.SUMMARY and (not record.lineage or p.source_type is not SourceType.MODEL):
                deny(MC.INVALID_SOURCE)
            revision = tx.cas(context.scope,expected)
            if action in ('hide','unhide'):
                tx.db.execute('UPDATE world_memories SET lifecycle=? WHERE memory_id=?',(record.lifecycle.value,str(target)))
            else:
                tx.insert(record)
                if old:
                    tx.db.execute("UPDATE world_memories SET lifecycle='superseded',superseded_by=? WHERE memory_id=?",
                                  (str(record.memory_id),str(old.memory_id)))
            return tx.audit(context,action,record,revision,identity,stamp)

    @checked
    def query(self, context, *, query='', limit=20, history=False, memory_id=None):
        from .memory_sqlite_repository import SCOPE_SQL,load_record
        bounded_text(query,MAX_QUERY_BYTES,empty=True)
        require(history,bool)
        if type(limit) is not int or not 1<=limit<=MAX_LIMIT:
            deny(MC.INVALID_ARGUMENT)
        if memory_id is not None:
            check_id(memory_id,IdKind.MEMORY)
        if history and type(context) is not OwnerMemoryContext:
            deny(MC.AUTHORIZATION_DENIED)
        with self.repository.transaction() as tx:
            authorize(tx,context)
            sql = 'SELECT m.* FROM world_memories m WHERE ' + ' AND '.join('m.'+c+'=?' for c in ('owner_id','soul_id','world_id','timeline_id'))
            args = scope_values(context.scope)
            if type(context) is SessionMemoryContext:
                sql += " AND EXISTS(SELECT 1 FROM memory_audiences a WHERE a.memory_id=m.memory_id AND (a.kind='world' OR (a.kind=? AND a.target=?)))"
                args += [context.viewer.kind.value,str(context.viewer.target)]
            if not history:
                sql += " AND m.lifecycle='live' AND json_extract(m.provenance,'$.canon_status')='accepted'"
            else:
                sql += " AND m.lifecycle<>'tombstoned'"
            if memory_id:
                sql += ' AND m.memory_id=?'
                args.append(str(memory_id))
            sql += ' AND instr(m.content,?)>0 ORDER BY m.memory_id LIMIT 1000'
            args.append(query)
            result = []
            # 游标逐行读取当前 Scope 的授权候选，禁止先全库载入再过滤。
            for row in tx.db.execute(sql,args):
                record = load_record(tx.db,row)
                try:
                    validate_record(tx,record)
                except ValueError:
                    from .world_repository import FailureCode,fail
                    fail(FailureCode.STORAGE_CORRUPT)
                if tx.blocked(context.scope,memory_id=record.memory_id):
                    continue
                if not history and not available(tx,record):
                    continue
                if history and not all(available(tx,tx.get(context.scope,s)) for s in record.lineage):
                    continue
                result.append(record)
                if len(result)==limit:
                    break
            # 连接的 IMMEDIATE 事务及控制锁覆盖授权、扫描和返回投影构造。
            version_data = fingerprint([self.repository.runtime_id,self.repository.generation,scope_values(context.scope),
                                   str(context.principal.principal_id),str(getattr(context,'viewer','owner')),
                                   str(getattr(context,'session_id',None)),str(getattr(context,'writer_epoch',None)),
                                   tx.revision(context.scope).value,len(tx.entries),
                                   query,limit,history,[str(r.memory_id) for r in result]])
            version = hmac.new(self._version_key,version_data.encode('ascii'),hashlib.sha256).hexdigest()
            return MemoryQueryResult(tuple(result),version)

    @checked
    def get_memory(self, context, memory_id, *, history=False):
        result = self.query(context,memory_id=memory_id,history=history,limit=1)
        if not result.records:
            deny(MC.NOT_AVAILABLE)
        return result.records[0]

    def query_owner_memory(self, context, **kwargs):
        if type(context) is not OwnerMemoryContext:
            deny(MC.AUTHORIZATION_DENIED)
        return self.query(context,**kwargs)
