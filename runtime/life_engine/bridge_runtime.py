"""默认拒绝的 Prompt-only Bridge；不读写 Memory/Story 表或调用模型。

目标持久化另立合同：当前 Memory 拒绝 SourceType.BRIDGE 且 lineage 限同 Scope；
Story source reference 也没有完整的 Bridge scope/grant/projection lineage。
这里不伪造 provenance 或调用目标 Runtime 绕开 B/C 的真源语义。
"""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import hmac
import secrets

from .bridge import (BridgeBudget, BridgeDataClass as DC, BridgeFailure as BC,
                     BridgeGrant, BridgeGrantProposal, BridgeGrantRevision, BridgeGrantStatus,
                     BridgeIdempotencyIdentity, BridgeItem, BridgeLineage, BridgeMemorySource,
                     BridgePreview, BridgeProjection, BridgeProjectionRequest, BridgePurpose,
                     BridgeRuntimeError, BridgeStorySource, OwnerBridgeContext,
                     SessionBridgeContext, _SOURCE_SEAL, deny)
from .bridge_codec import (audience_data, digest, item_data, lineage_data, preview_data,
                           projection_data, proposal_data, scope_data)
from .bridge_control import append_intent
from .domain import (BindingStatus, CanonStatus, DomainId, IdKind, RealityStatus,
                     Revision, WorldKind, WorldStatus, aware)
from .domain_policy import BridgeDecision, BridgePolicy, BridgeRequest, evaluate_bridge
from .memory import AudienceKind
from .world_codec import dumps
from .world_repository import WorldRuntimeError


class BridgeRuntime:
    def __init__(self, repository, world_runtime, memory_runtime, story_runtime, *, clock=None):
        self.repository, self.world, self.memory, self.story = repository, world_runtime, memory_runtime, story_runtime
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._token_key = secrets.token_bytes(32)
        for runtime in (world_runtime, memory_runtime, story_runtime):
            if runtime.repository.runtime_id != repository.runtime_id:
                deny(BC.RECOVERY_REQUIRED)
        for runtime in (memory_runtime, story_runtime):
            if runtime.repository.generation != repository.generation:
                deny(BC.RECOVERY_REQUIRED)

    def _now(self):
        now = self.clock()
        aware(now)
        return now

    def _token(self, fingerprint):
        return hmac.new(self._token_key, fingerprint.encode('ascii'), hashlib.sha256).hexdigest()

    @staticmethod
    def _worlds(tx, source_scope, target_scope):
        if source_scope.owner_id != target_scope.owner_id or source_scope.world_id == target_scope.world_id:
            deny(BC.AUTHORIZATION_DENIED)
        try:
            src = tx.world.get_world(source_scope.world_id)
            dst = tx.world.get_world(target_scope.world_id)
        except WorldRuntimeError:
            deny(BC.AUTHORIZATION_DENIED)
        if src.timeline.scope != source_scope or dst.timeline.scope != target_scope:
            deny(BC.AUTHORIZATION_DENIED)
        if (src.world.status in (WorldStatus.ARCHIVED, WorldStatus.TOMBSTONED) or
                dst.world.status in (WorldStatus.ARCHIVED, WorldStatus.TOMBSTONED)):
            deny(BC.AUTHORIZATION_DENIED)
        if (src.world.kind, dst.world.kind) not in ((WorldKind.SOUL, WorldKind.ROLEPLAY),
                                                     (WorldKind.ROLEPLAY, WorldKind.SOUL)):
            deny(BC.UNSUPPORTED_DIRECTION)
        return src, dst

    @staticmethod
    def _audience(tx, proposal, dst):
        audience = proposal.target_audience
        if dst.world.kind is WorldKind.SOUL:
            if audience.kind is not AudienceKind.SOUL or audience.target != proposal.target_scope.soul_id:
                deny(BC.AUDIENCE_DENIED)
        else:
            if audience.kind is not AudienceKind.CHARACTER_INSTANCE:
                deny(BC.AUDIENCE_DENIED)
            try:
                character = tx.world.get_character(audience.target)
            except WorldRuntimeError:
                deny(BC.AUDIENCE_DENIED)
            if character.scope != proposal.target_scope:
                deny(BC.AUDIENCE_DENIED)

    def preview_grant(self, context, proposal):
        if type(context) is not OwnerBridgeContext or type(proposal) is not BridgeGrantProposal:
            deny(BC.INVALID_ARGUMENT)
        if proposal.purpose is not BridgePurpose.PROMPT_CONTEXT:
            deny(BC.UNSUPPORTED_PURPOSE)
        if (context.source_scope, context.target_scope) != (proposal.source_scope, proposal.target_scope):
            deny(BC.AUTHORIZATION_DENIED)
        if proposal.expires_at <= self._now():
            deny(BC.GRANT_EXPIRED)
        with self.repository.transaction() as tx:
            _, dst = self._worlds(tx, proposal.source_scope, proposal.target_scope)
            self._audience(tx, proposal, dst)
        preview = BridgePreview(DomainId.new(IdKind.GRANT), context.principal, proposal,
                                self.repository.runtime_id, self.repository.generation, '', '')
        fingerprint = digest(preview_data(preview))
        return replace(preview, fingerprint=fingerprint, token=self._token(fingerprint))

    def _check_preview(self, context, preview):
        if type(context) is not OwnerBridgeContext or type(preview) is not BridgePreview:
            deny(BC.PREVIEW_STALE)
        computed = digest(preview_data(preview))
        if (not hmac.compare_digest(computed, preview.fingerprint) or
                not hmac.compare_digest(self._token(computed), preview.token) or
                (preview.principal, preview.proposal.source_scope, preview.proposal.target_scope) !=
                (context.principal, context.source_scope, context.target_scope) or
                preview.runtime_id != self.repository.runtime_id or
                preview.generation != self.repository.generation or
                preview.proposal.expires_at <= self._now()):
            deny(BC.PREVIEW_STALE)

    def confirm_grant(self, context, preview, identity):
        self._check_preview(context, preview)
        if type(identity) is not BridgeIdempotencyIdentity:
            deny(BC.INVALID_ARGUMENT)
        stamp = digest(['create', preview.fingerprint])
        with self.repository.transaction() as tx:
            replay = tx.replay(identity, stamp)
            if replay:
                return replay
            _, dst = self._worlds(tx, preview.proposal.source_scope, preview.proposal.target_scope)
            self._audience(tx, preview.proposal, dst)
            if preview.proposal.expires_at <= self._now():
                deny(BC.PREVIEW_STALE)
            grant = BridgeGrant(preview.grant_id, context.principal, preview.proposal,
                                BridgeGrantRevision(1), BridgeGrantStatus.ACTIVE, self._now())
            return tx.insert_grant(grant, identity, stamp)

    def get_grant(self, context, grant_id):
        if type(context) is not OwnerBridgeContext:
            deny(BC.AUTHORIZATION_DENIED)
        with self.repository.transaction() as tx:
            grant = tx.grant(grant_id)
            if grant is None or grant.principal.owner_id != context.principal.owner_id or (
                    grant.proposal.source_scope, grant.proposal.target_scope) != (
                        context.source_scope, context.target_scope):
                deny(BC.GRANT_NOT_FOUND)
            return grant

    def list_grants(self, context, *, after='', limit=100):
        if type(context) is not OwnerBridgeContext or type(after) is not str or type(limit) is not int or not 1 <= limit <= 100:
            deny(BC.INVALID_ARGUMENT)
        with self.repository.transaction() as tx:
            rows = tx.db.execute('SELECT grant_id FROM bridge_grants WHERE owner_id=? AND source_soul_id=? AND source_world_id=? AND source_timeline_id=? AND target_soul_id=? AND target_world_id=? AND target_timeline_id=? AND grant_id>? ORDER BY grant_id LIMIT ?',
                (str(context.principal.owner_id), str(context.source_scope.soul_id),
                 str(context.source_scope.world_id),
                 str(context.source_scope.timeline_id), str(context.target_scope.soul_id),
                 str(context.target_scope.world_id), str(context.target_scope.timeline_id), after, limit)).fetchall()
            return tuple(tx.grant(DomainId.parse(row[0])) for row in rows)

    def revoke_grant(self, context, grant_id, expected_revision, identity):
        if (type(context) is not OwnerBridgeContext or type(expected_revision) is not BridgeGrantRevision or
                type(identity) is not BridgeIdempotencyIdentity):
            deny(BC.INVALID_ARGUMENT)
        stamp = digest(['revoke', str(grant_id), expected_revision.value,
                        scope_data(context.source_scope), scope_data(context.target_scope),
                        str(context.principal.principal_id)])
        with self.repository.transaction() as tx:
            replay = tx.replay(identity, stamp)
            if replay:
                return replay
            grant = tx.grant(grant_id)
            if grant is None or grant.principal.owner_id != context.principal.owner_id or (
                    grant.proposal.source_scope, grant.proposal.target_scope) != (
                        context.source_scope, context.target_scope):
                deny(BC.GRANT_NOT_FOUND)
            if tx.effective_revoked(grant_id) or grant.status is BridgeGrantStatus.REVOKED:
                deny(BC.GRANT_REVOKED)
            if grant.revision != expected_revision:
                deny(BC.GRANT_REVISION_CONFLICT)
            entry = append_intent(self.repository.root, tx.control_db, tx.entries, tx.install_id,
                                  self.repository.instance_id, grant_id, context.principal.principal_id,
                                  identity, stamp)
            return tx.revoke(grant, context.principal, datetime.fromisoformat(entry['created_at']),
                             identity, stamp, entry)

    @staticmethod
    def _session(tx, context):
        if context.runtime_id != tx.repository_runtime_id or context.generation != tx.repository_generation:
            deny(BC.TARGET_STALE)
        try:
            snap = tx.world.get_world(context.target_scope.world_id)
            binding = tx.world.get_session(context.session_id)
        except WorldRuntimeError:
            deny(BC.TARGET_STALE)
        if (snap.timeline.scope != context.target_scope or snap.world.status is not WorldStatus.ACTIVE or
                snap.world.writer_epoch != context.writer_epoch or binding.status is not BindingStatus.OPEN or
                binding.scope != context.target_scope or binding.principal != context.principal or
                binding.writer_epoch != context.writer_epoch):
            deny(BC.TARGET_STALE)
        actual = (context.target_scope.soul_id if snap.world.kind is WorldKind.SOUL else binding.character_instance_id)
        if context.viewer.target != actual or context.viewer.kind is not (
                AudienceKind.SOUL if snap.world.kind is WorldKind.SOUL else AudienceKind.CHARACTER_INSTANCE):
            deny(BC.AUDIENCE_DENIED)

    def _grant_for_project(self, tx, request, target):
        tx.repository_runtime_id = self.repository.runtime_id
        tx.repository_generation = self.repository.generation
        grant = tx.grant(request.grant_id)
        if grant is None:
            deny(BC.GRANT_NOT_FOUND)
        if tx.effective_revoked(grant.grant_id) or grant.status is BridgeGrantStatus.REVOKED:
            deny(BC.GRANT_REVOKED)
        if grant.proposal.expires_at <= self._now():
            deny(BC.GRANT_EXPIRED)
        if request.purpose is not BridgePurpose.PROMPT_CONTEXT:
            deny(BC.UNSUPPORTED_PURPOSE)
        label = request.target_audience.kind.value + ':' + str(request.target_audience.target)
        policy = BridgePolicy(grant.grant_id, grant.principal, grant.proposal.source_scope,
            grant.proposal.target_scope, frozenset(grant.proposal.allowed_fields),
            grant.proposal.data_class.value, grant.proposal.purpose.value, frozenset((label,)),
            grant.proposal.expires_at, Revision(grant.revision.value))
        eligibility = BridgeRequest(request.principal, request.source_scope,
            request.target_scope, frozenset(request.fields), request.data_class.value,
            request.purpose.value, frozenset((label,)))
        if evaluate_bridge(policy, eligibility, current_grant_revision=Revision(grant.revision.value),
                           now=self._now()) is not BridgeDecision.ALLOW:
            deny(BC.AUTHORIZATION_DENIED)
        if (target.target_scope != request.target_scope or target.viewer != request.target_audience or
                target.principal != request.principal):
            deny(BC.AUDIENCE_DENIED)
        src, dst = self._worlds(tx, request.source_scope, request.target_scope)
        self._audience(tx, grant.proposal, dst)
        self._session(tx, target)
        return grant

    def _fresh_source(self, source, data_class, scope):
        if data_class is DC.MEMORY:
            if (type(source) is not BridgeMemorySource or source._seal is not _SOURCE_SEAL or
                    source._runtime is not self.memory or source.context.scope != scope or
                    source.runtime_id != self.repository.runtime_id or source.generation != self.repository.generation):
                deny(BC.SOURCE_STALE)
            try:
                result = self.memory.query(source.context, query=source.query, limit=source.limit,
                                           history=False, memory_id=source.memory_id)
                source.validate_records(source.context, result)
            except Exception:
                deny(BC.SOURCE_STALE)
            if result.version != source.result.version:
                deny(BC.SOURCE_STALE)
            return result.version, result
        if (type(source) is not BridgeStorySource or source._seal is not _SOURCE_SEAL or
                source._runtime is not self.story or source.context.scope != scope or
                source.runtime_id != self.repository.runtime_id or source.generation != self.repository.generation):
            deny(BC.SOURCE_STALE)
        try:
            result = self.story.get_story_projection(source.context)
        except Exception:
            deny(BC.SOURCE_STALE)
        if (result.scope != source.result.scope or result.viewer != source.result.viewer or
                result.revision != source.result.revision or result.clock != source.result.clock or
                result.projection_version != source.result.projection_version or
                result.snapshot_token != source.result.snapshot_token):
            deny(BC.SOURCE_STALE)
        return result.snapshot_token, result

    @staticmethod
    def _item(item_id, fields, lineage):
        size = len(dumps([item_id, list(map(list, fields)), lineage_data(lineage)]).encode('utf-8'))
        return BridgeItem(item_id, fields, lineage, size)

    def _items(self, grant, request, source, version, result):
        items = []
        if request.data_class is DC.MEMORY:
            for record in result.records:
                data = {'content': record.content, 'kind': record.kind.value,
                        'subjects': dumps([[s.kind.value, str(s.target) if s.target else s.text] for s in record.subjects]),
                        'reality_status': record.provenance.reality_status.value,
                        'canon_status': record.provenance.canon_status.value,
                        'source_reference': record.provenance.source_id}
                lineage = BridgeLineage(request.source_scope, DC.MEMORY, str(record.memory_id),
                    version, record.audience, record.provenance.reality_status,
                    record.provenance.canon_status, grant.grant_id, grant.revision)
                items.append(self._item(str(record.memory_id), tuple((key, data[key]) for key in request.fields), lineage))
        else:
            # StoryProjection 可含内部 world_facts/open_threads；Bridge 只显式取这两种 viewer 子集。
            reality = (RealityStatus.FICTIONAL if source.context.viewer.kind is AudienceKind.CHARACTER_INSTANCE
                       else RealityStatus.UNKNOWN)
            if 'character_state' in request.fields:
                for key, value in result.character_state:
                    lineage = BridgeLineage(request.source_scope, DC.STORY_PROJECTION,
                        'character_state:' + key, version, (source.context.viewer,), reality,
                        CanonStatus.ACCEPTED, grant.grant_id, grant.revision)
                    items.append(self._item('character_state:' + key, (('character_state', dumps([key, value])),), lineage))
            if 'viewer_relationships' in request.fields:
                for src, dst, key, value in result.relationships:
                    if source.context.viewer.target not in (src, dst):
                        continue
                    identity = '|'.join((str(src), str(dst), key))
                    lineage = BridgeLineage(request.source_scope, DC.STORY_PROJECTION,
                        'relationship:' + identity, version, (source.context.viewer,), reality,
                        CanonStatus.ACCEPTED, grant.grant_id, grant.revision)
                    items.append(self._item('relationship:' + identity,
                        (('viewer_relationships', dumps([str(src), str(dst), key, value])),), lineage))
        used, kept = 0, []
        for item in items:
            if (len(kept) >= request.budget.max_items or item.byte_size > request.budget.max_item_bytes or
                    used + item.byte_size > request.budget.max_total_bytes):
                break
            kept.append(item)
            used += item.byte_size
        return tuple(kept), used

    def project(self, request, source, target):
        if (type(request) is not BridgeProjectionRequest or type(target) is not SessionBridgeContext or
                request.purpose is not BridgePurpose.PROMPT_CONTEXT):
            deny(BC.UNSUPPORTED_PURPOSE)
        with self.repository.transaction() as tx:
            grant = self._grant_for_project(tx, request, target)
        if source.context.principal != request.principal:
            deny(BC.SOURCE_STALE)
        version, result = self._fresh_source(source, request.data_class, request.source_scope)
        items, used = self._items(grant, request, source, version, result)
        context = source.context
        projection = BridgeProjection(grant.grant_id, grant.revision, request.source_scope,
            request.target_scope, request.data_class, request.purpose, request.fields,
            request.target_audience, version, context.principal, context.viewer,
            context.session_id, context.writer_epoch,
            source.runtime_id, source.generation, target, items, request.budget, used, '', '')
        fingerprint = digest(projection_data(projection))
        projection = replace(projection, fingerprint=fingerprint, projection_token=self._token(fingerprint))
        object.__setattr__(projection, '_runtime', self)
        object.__setattr__(projection, '_source', source)
        return self.revalidate_projection(projection)

    def revalidate_projection(self, projection):
        if type(projection) is not BridgeProjection or projection._runtime is not self:
            deny(BC.PROJECTION_STALE)
        fingerprint = digest(projection_data(projection))
        if (not hmac.compare_digest(fingerprint, projection.fingerprint) or
                not hmac.compare_digest(self._token(fingerprint), projection.projection_token)):
            deny(BC.PROJECTION_STALE)
        source = projection._source
        if (source is None or source.context.principal != projection.source_principal or
                source.context.viewer != projection.source_viewer or
                source.context.session_id != projection.source_session_id or
                source.context.writer_epoch != projection.source_writer_epoch or
                source.runtime_id != projection.source_runtime_id or
                source.generation != projection.source_generation):
            deny(BC.PROJECTION_STALE)
        request = BridgeProjectionRequest(projection.grant_id, projection.target_session.principal,
            projection.source_scope, projection.target_scope, projection.data_class,
            projection.fields, projection.purpose, projection.target_audience, projection.budget)
        try:
            with self.repository.transaction() as tx:
                grant = self._grant_for_project(tx, request, projection.target_session)
                if grant.revision != projection.grant_revision:
                    deny(BC.PROJECTION_STALE)
        except BridgeRuntimeError:
            deny(BC.PROJECTION_STALE)
        try:
            version, result = self._fresh_source(source, projection.data_class, projection.source_scope)
        except BridgeRuntimeError:
            deny(BC.PROJECTION_STALE)
        if version != projection.source_version:
            deny(BC.PROJECTION_STALE)
        items, used = self._items(grant, request, source, version, result)
        if items != projection.items or used != projection.budget_used:
            deny(BC.PROJECTION_STALE)
        try:
            with self.repository.transaction() as tx:
                self._grant_for_project(tx, request, projection.target_session)
        except BridgeRuntimeError:
            deny(BC.PROJECTION_STALE)
        return projection
