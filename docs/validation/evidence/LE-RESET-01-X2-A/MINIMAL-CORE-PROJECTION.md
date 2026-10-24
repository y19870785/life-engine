# C2 最小三文件 Core 投影

为避免Markdown空白检查歧义，diff中仅含一个ASCII空格的上下文行以可见符号 `␠` 表示；提取patch时将**整行** `␠` 还原为一个ASCII空格，其余字节不变。该符号不属于源码，台账hash对应还原后的patch。

临时审查对象，不是X2产品实施。剔除完整扫描、Prompt、provider/Host/安装器与角色卡变更。来源、hash与92项结果见[证据台账](../../LE-RESET-01-X2-A-REVIEW-EVIDENCE.md)。

~~~~~~~~diff
--- a/runtime/life_engine/domain.py
+++ b/runtime/life_engine/domain.py
@@ -132,6 +132,10 @@
     BRIDGE = 'bridge'
     LEGACY = 'legacy'
     OWNER_COMMAND = 'owner_command'
+    # 角色扮演回忆：Owner 把一次 RP 会话的派生摘要写入 Soul World。
+    # 证明"曾在该 RP 世界经历过此事"，不提升为现实事实，也不复制 RP 原文。
+    # 与 BRIDGE 的 prompt-only 语义不同（Bridge 永不写目标 Memory）。
+    ROLEPLAY_RECALL = 'roleplay_recall'
␠
␠
 @dataclass(frozen=True)
--- a/runtime/life_engine/memory_runtime.py
+++ b/runtime/life_engine/memory_runtime.py
@@ -14,7 +14,7 @@
 from .memory_control import fingerprint, scope_values
 from .memory_repository import MemoryFailure as MC, MemoryRuntimeError, deny
 from .world_codec import provenance_dump
-from .world_repository import WorldRuntimeError
+from .world_repository import FailureCode as WC, WorldRuntimeError
␠
␠
 def checked(method):
@@ -67,16 +67,37 @@
         SourceType.IMPORT: (RealityStatus.UNKNOWN,),
         SourceType.LEGACY: (RealityStatus.LEGACY_UNREVIEWED,),
         SourceType.OWNER_COMMAND: (RealityStatus.USER_CLAIMED,RealityStatus.FICTIONAL,RealityStatus.UNKNOWN),
+        # 角色扮演回忆只能以"虚构共同经历"存在，永远不能升级为现实事实。
+        SourceType.ROLEPLAY_RECALL: (RealityStatus.FICTIONAL_SHARED_EXPERIENCE,),
     }
     if p.source_type not in allowed or p.reality_status not in allowed[p.source_type]:
         deny(MC.INVALID_SOURCE)
-    if ((p.source_world_id is not None and p.source_world_id != scope.world_id) or
-            (p.source_timeline_id is not None and p.source_timeline_id != scope.timeline_id)):
-        deny(MC.INVALID_SOURCE)
-    if p.source_session_id is not None:
-        source_session = tx.world.get_session(p.source_session_id)
-        if source_session.scope != scope or source_session.principal != p.actor:
-            deny(MC.INVALID_SOURCE)
+    if p.source_type is SourceType.ROLEPLAY_RECALL:
+        # 回忆录必须指向**另一个**世界，且该世界由同一 Soul 持有。
+        # 这里只做结构校验、不查源世界：否则源 RP World 归档或删除后，
+        # 既有回忆录会在读路径被判为损坏。源世界的真实性在写入时校验。
+        if (p.source_world_id is None or p.source_timeline_id is None
+                or p.source_world_id == scope.world_id):
+            deny(MC.INVALID_SOURCE)
+        if p.source_session_id is not None:
+            # 首版不携带源会话引用，避免读路径跨世界查表。
+            deny(MC.INVALID_SOURCE)
+        if world.world.kind is not WorldKind.SOUL:
+            deny(MC.INVALID_SOURCE)
+        if record.kind is not MemoryKind.SHARED_EXPERIENCE:
+            deny(MC.INVALID_ARGUMENT)
+        if record.audience != (MemoryAudience(AudienceKind.SOUL, scope.soul_id),):
+            deny(MC.AUTHORIZATION_DENIED)
+        if any(subject.kind is not SubjectKind.TEXT for subject in record.subjects):
+            deny(MC.INVALID_SOURCE)
+    else:
+        if ((p.source_world_id is not None and p.source_world_id != scope.world_id) or
+                (p.source_timeline_id is not None and p.source_timeline_id != scope.timeline_id)):
+            deny(MC.INVALID_SOURCE)
+        if p.source_session_id is not None:
+            source_session = tx.world.get_session(p.source_session_id)
+            if source_session.scope != scope or source_session.principal != p.actor:
+                deny(MC.INVALID_SOURCE)
     for a in record.audience:
         if a.kind is AudienceKind.CHARACTER_INSTANCE:
             if tx.world.get_character(a.target).scope != scope:
@@ -96,6 +117,37 @@
             deny(MC.AUTHORIZATION_DENIED)
         if s.kind is SubjectKind.SOUL and s.target != scope.soul_id:
             deny(MC.AUTHORIZATION_DENIED)
+
+
+
+def recall_source_identity(provenance):
+    """Canon/生命周期与正文修订不是换源；来源引用变化则必须重新验源。"""
+    return (provenance.actor, provenance.source_type, provenance.source_id,
+            provenance.source_world_id, provenance.source_timeline_id, provenance.source_session_id)
+
+
+def validate_recall_write(tx, record, old):
+    """与 CAS/insert 同一事务封闭泛入口；旧回忆的生命周期不依赖源继续存在。"""
+    p = record.provenance
+    old_recall = old is not None and old.provenance.source_type is SourceType.ROLEPLAY_RECALL
+    if old_recall and p.source_type is not SourceType.ROLEPLAY_RECALL:
+        # 不能先把回忆录脱壳成普通来源，再绕过虚构与受众约束。
+        deny(MC.INVALID_SOURCE)
+    if p.source_type is not SourceType.ROLEPLAY_RECALL:
+        return
+    if old_recall and recall_source_identity(p) == recall_source_identity(old.provenance):
+        return
+    try:
+        source = tx.world.get_world(p.source_world_id)
+    except WorldRuntimeError as exc:
+        if exc.code is WC.WORLD_NOT_FOUND:
+            deny(MC.INVALID_SOURCE)
+        raise
+    if (source.world.kind is not WorldKind.ROLEPLAY
+            or (source.world.owner_id, source.world.soul_id) != (record.scope.owner_id, record.scope.soul_id)
+            or source.timeline.scope.timeline_id != p.source_timeline_id):
+        deny(MC.INVALID_SOURCE)
+
␠
␠
 def available(tx, record, seen=None):
@@ -158,6 +210,40 @@
         if provenance.source_type is SourceType.OBSERVATION:
             deny(MC.INVALID_SOURCE)
         return self._create(context, expected_revision, identity, content, kind, provenance, audience, subjects, lineage)
+
+    @checked
+    def create_roleplay_recall(self, context, expected_revision, identity, *, content, provenance,
+                               kind=None, audience=None, subjects=()):
+        """Owner 把一次角色扮演会话的派生摘要登记进 Soul World。
+
+        写入时确认源世界真实存在、属于同一 Owner/Soul 且为 ROLEPLAY，目标必须是
+        Soul World；读路径不回查源世界，因此源 RP World 归档后回忆录仍可读。
+        回忆录默认 CANDIDATE，须显式 accept 才进入正常会话检索。
+        subjects 只接受 TEXT：跨世界的 CHARACTER_INSTANCE/WORLD 主体会被拒绝。
+        """
+        if type(context) is not OwnerMemoryContext:
+            deny(MC.AUTHORIZATION_DENIED)
+        require(provenance, Provenance)
+        if provenance.actor != context.principal:
+            deny(MC.INVALID_SOURCE)
+        if provenance.source_type is not SourceType.ROLEPLAY_RECALL:
+            deny(MC.INVALID_SOURCE)
+        if provenance.source_world_id is None or provenance.source_timeline_id is None:
+            deny(MC.INVALID_SOURCE)
+        if kind is None:
+            kind = MemoryKind.SHARED_EXPERIENCE
+        require(kind, MemoryKind)
+        if kind is not MemoryKind.SHARED_EXPERIENCE:
+            deny(MC.INVALID_ARGUMENT)
+        soul_audience = (MemoryAudience(AudienceKind.SOUL, context.scope.soul_id),)
+        if audience is None:
+            audience = soul_audience
+        elif tuple(audience) != soul_audience:
+            # 回忆录只属于 Soul；不允许扩成 World 或角色受众。
+            deny(MC.AUTHORIZATION_DENIED)
+        return self._create(context, expected_revision, identity, content, kind, provenance,
+                            audience, subjects, ())
+
␠
     def _create(self, context, expected, identity, content, kind, provenance, audience, subjects, lineage):
         record = MemoryRecord(DomainId.new(IdKind.MEMORY),context.scope,kind,content,1,provenance,audience,subjects,
@@ -245,6 +331,7 @@
                         predecessor=old.memory_id,superseded_by=None,lifecycle=MemoryLifecycle.LIVE,
                         created_at=datetime.now(timezone.utc))
             validate_record(tx,record)
+            validate_recall_write(tx,record,old)
             p = record.provenance
             if tx.blocked(context.scope,source=(str(p.actor.principal_id),p.source_type.value,p.source_id)):
                 deny(MC.NOT_AVAILABLE)
--- /dev/null
+++ b/runtime/life_engine/roleplay_recall.py
@@ -0,0 +1,177 @@
+"""角色扮演回忆录：把一次 RP 会话的**派生摘要**登记进 Soul World。
+
+边界与保证（与 SP-006S0 的受控投影原则一致）：
+
+- 只写 Soul World；源必须是同一 Owner/Soul 下的 ROLEPLAY World。
+- 写出的记忆永远携带 ``RealityStatus.FICTIONAL_SHARED_EXPERIENCE``，不会被
+  提升为现实事实；``Provenance.source_world_id`` 保留"来自哪个扮演世界"。
+- 不复制完整对话。正文只含角色名、时间范围、轮次和至多若干**主题片段**。
+- 默认 ``CanonStatus.CANDIDATE``，须显式 accept 才进入正常会话检索。
+- 读路径不回查源世界，所以源 RP World 归档后回忆录依然可读。
+
+本模块不连宿主、不调模型、不联网。
+"""
+from dataclasses import dataclass, replace
+from datetime import datetime, timezone
+
+from .domain import (CanonStatus, Principal, Provenance, RealityStatus, SourceType,
+                     WorldScope, aware, require)
+from .memory import (AudienceKind, IdempotencyIdentity, MAX_CONTENT_BYTES, MemoryAudience,
+                     MemoryKind, MemoryLifecycle, MemorySubject, OwnerMemoryContext, SubjectKind, bounded_text)
+from .memory_repository import MemoryFailure, deny
+
+MAX_HIGHLIGHT_BYTES = 200
+MAX_HIGHLIGHTS = 8
+MAX_RECALL_BYTES = 4000
+MAX_SOURCE_REF_BYTES = 512
+MAX_NAME_BYTES = 120
+BOUNDARY = '这是一次角色扮演经历，不是真实发生过的事实。'
+
+
+@dataclass(frozen=True)
+class RecallSource:
+    """一次角色扮演会话的可登记事实；不含完整对话正文。"""
+    source_scope: WorldScope
+    character_name: str = ''
+    card_fingerprint: str = ''
+    turn_count: int = 0
+    started_at: datetime | None = None
+    ended_at: datetime | None = None
+    highlights: tuple[str, ...] = ()
+
+    def __post_init__(self):
+        require(self.source_scope, WorldScope)
+        for value, maximum in ((self.character_name, MAX_NAME_BYTES),
+                               (self.card_fingerprint, MAX_NAME_BYTES)):
+            if value:
+                bounded_text(value, maximum)
+        if type(self.turn_count) is not int or self.turn_count < 0:
+            raise ValueError('turn_count 必须是非负整数')
+        for moment in (self.started_at, self.ended_at):
+            if moment is not None:
+                aware(moment)
+        require(self.highlights, tuple)
+        if len(self.highlights) > MAX_HIGHLIGHTS:
+            raise ValueError('主题片段过多')
+        for item in self.highlights:
+            bounded_text(item, MAX_HIGHLIGHT_BYTES)
+
+
+def source_reference(source):
+    """写入 ``Provenance.source_id`` 的有界不透明引用。"""
+    parts = [f'rp-world:{source.source_scope.world_id}']
+    if source.card_fingerprint:
+        parts.append(f'card:{source.card_fingerprint}')
+    reference = '|'.join(parts)
+    if len(reference.encode('utf-8')) > MAX_SOURCE_REF_BYTES:
+        raise ValueError('来源引用越界')
+    return reference
+
+
+def _stamp(moment):
+    return moment.isoformat(timespec='minutes') if moment is not None else '未知'
+
+
+def digest(source, *, max_bytes=MAX_RECALL_BYTES):
+    """生成回忆录正文。确定性：相同输入产生相同文本。"""
+    lines = ['[角色扮演回忆]']
+    if source.character_name:
+        lines.append(f'我在角色扮演中扮演了「{source.character_name}」。')
+    else:
+        lines.append('我进行了一次未命名角色的角色扮演。')
+    lines.append(f'扮演世界：{source.source_scope.world_id}')
+    if source.started_at is not None or source.ended_at is not None:
+        lines.append(f'时间：{_stamp(source.started_at)} → {_stamp(source.ended_at)}')
+    lines.append(f'交互轮次：{source.turn_count}')
+    if source.highlights:
+        lines.append('期间记得的事：')
+        for item in source.highlights:
+            lines.append(f'- {item}')
+    lines.append(BOUNDARY)
+    content = '\n'.join(lines)
+    bounded_text(content, min(max_bytes, MAX_CONTENT_BYTES))
+    return content
+
+
+def build_provenance(source, actor, *, canon=CanonStatus.CANDIDATE, created_at=None):
+    """回忆录的来源断言：来源语义固定在 FICTIONAL_SHARED_EXPERIENCE。
+
+    ``created_at`` 缺省取这段经历结束（或开始）的时间，而不是写入时间：
+    回忆录记录的是**事情何时发生**，同一段经历重复登记也因而是确定的。
+    """
+    require(actor, Principal)
+    moment = created_at or source.ended_at or source.started_at or datetime.now(timezone.utc)
+    return Provenance(
+        SourceType.ROLEPLAY_RECALL,
+        source_reference(source),
+        moment,
+        actor,
+        RealityStatus.FICTIONAL_SHARED_EXPERIENCE,
+        canon,
+        source_world_id=source.source_scope.world_id,
+        source_timeline_id=source.source_scope.timeline_id,
+    )
+
+
+def recall_audience(soul_id):
+    return (MemoryAudience(AudienceKind.SOUL, soul_id),)
+
+
+def recall_subjects(source):
+    """只用 TEXT 主体：跨世界的实体引用会被 Memory 校验拒绝。"""
+    label = source.character_name or '角色扮演'
+    return (MemorySubject(SubjectKind.TEXT, text=label),)
+
+
+def record_recall(memory, owner_context, source, *, identity, accept=False):
+    """写入一条回忆录并返回 MemoryReceipt。
+
+    ``owner_context`` 必须是 Soul World 的 OwnerMemoryContext；
+    源世界真实性与归属由 ``MemoryRuntime.create_roleplay_recall`` 在写入时校验。
+    """
+    require(owner_context, OwnerMemoryContext)
+    require(identity, IdempotencyIdentity)
+    provenance = build_provenance(source, owner_context.principal)
+    receipt = memory.create_roleplay_recall(
+        owner_context,
+        memory.collection_revision(owner_context),
+        identity,
+        content=digest(source),
+        provenance=provenance,
+        kind=MemoryKind.SHARED_EXPERIENCE,
+        audience=recall_audience(owner_context.scope.soul_id),
+        subjects=recall_subjects(source),
+    )
+    # create 的历史回执不代表目标当前可见；候选只能通过 history 读取。
+    current = memory.get_memory(owner_context, receipt.memory_id, history=True)
+    _check_recall_shape(current, owner_context, provenance)
+    if not accept:
+        if current.lifecycle is not MemoryLifecycle.LIVE:
+            deny(MemoryFailure.NOT_AVAILABLE)
+        return receipt
+    if current.lifecycle not in (MemoryLifecycle.LIVE, MemoryLifecycle.SUPERSEDED):
+        deny(MemoryFailure.NOT_AVAILABLE)
+    # SUPERSEDED 原候选只能由同一个 accept 身份合法重放，不能借用其他操作的后继。
+    accepted = memory.accept_memory(
+        owner_context,
+        receipt.memory_id,
+        memory.collection_revision(owner_context),
+        IdempotencyIdentity(identity.source, f'{identity.slot}:accept'),
+    )
+    result = memory.get_memory(owner_context, accepted.memory_id)
+    _check_recall_shape(result, owner_context, replace(provenance, canon_status=CanonStatus.ACCEPTED))
+    if result.lifecycle is not MemoryLifecycle.LIVE or result.predecessor != receipt.memory_id:
+        deny(MemoryFailure.NOT_AVAILABLE)
+    return accepted
+
+
+def _check_recall_shape(record, owner, provenance):
+    """只核对既有回执的形状/来源，不新增源 World 存在依赖。"""
+    if (record.scope != owner.scope or record.kind is not MemoryKind.SHARED_EXPERIENCE
+            or record.audience != recall_audience(owner.scope.soul_id)
+            or record.provenance != provenance):
+        deny(MemoryFailure.NOT_AVAILABLE)
+
+
+def is_recall(record):
+    return record.provenance.source_type is SourceType.ROLEPLAY_RECALL
~~~~~~~~
