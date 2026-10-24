"""角色扮演回忆录：跨世界派生摘要的授权、边界与反例。"""
import json
import unittest
from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from memory_fixture import MemoryFixture

from life_engine import roleplay_recall as R
from life_engine import prompt_runtime
from life_engine.prompt import PromptPurpose
from life_engine.domain import (CanonStatus, DomainError, DomainId, IdKind, Provenance,
                                RealityStatus, SourceType, World, WorldKind, WorldScope,
                                WorldStatus, WorldTimeline)
from life_engine.memory import (AudienceKind, IdempotencyIdentity, MemoryAudience, MemoryKind,
                                MemorySubject, OwnerMemoryContext, SessionMemoryContext, SubjectKind)
from life_engine.memory_repository import MemoryRuntimeError
from life_engine.world_repository import WorldSnapshot


class RoleplayRecallTests(MemoryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        # 回忆录的目标：一个 ACTIVE 的 Soul World。
        self.soul_scope = WorldScope(self.actor.owner_id, self.soul.soul_id,
                                     self.soul.soul_world_id, DomainId.new(IdKind.TIMELINE))
        prov = Provenance(SourceType.OWNER_COMMAND, '合成 Soul 世界', self.now, self.actor,
                          RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
        with self.world.repository.transaction() as tx:
            tx.add_world(WorldSnapshot(
                World(self.soul_scope.world_id, self.soul_scope.owner_id, self.soul_scope.soul_id,
                      WorldKind.SOUL, prov, WorldStatus.ACTIVE),
                WorldTimeline(self.soul_scope, prov)))
        self.soul_owner = OwnerMemoryContext(self.actor, self.soul_scope)
        self.soul_session = self.open_soul_session()

    # --- 辅助 ---------------------------------------------------------------

    def open_soul_session(self):
        snapshot = self.world.snapshot(self.actor, self.soul_scope.world_id)
        current = next((s for s in snapshot.sessions if s.status.value == 'open'), None)
        if current:
            snapshot = self.world.exit(self.actor, self.soul_scope.world_id,
                                       self.soul_scope.timeline_id, current.session_id,
                                       snapshot.world.revision, snapshot.world.writer_epoch)
        opened = self.world.enter(self.actor, self.soul_scope.world_id, self.soul_scope.timeline_id,
                                  None, snapshot.world.revision, snapshot.world.writer_epoch)
        binding = opened.sessions[-1]
        return SessionMemoryContext(self.actor, self.soul_scope, binding.session_id,
                                    binding.writer_epoch,
                                    MemoryAudience(AudienceKind.SOUL, self.soul_scope.soul_id))

    def source(self, **kwargs):
        params = dict(source_scope=self.a.timeline.scope, character_name='原创角色',
                      card_fingerprint='fp-synthetic-1', turn_count=6,
                      started_at=self.now, ended_at=self.now + timedelta(hours=1),
                      highlights=('谈到了明天的面试', '约定下周继续写作'))
        params.update(kwargs)
        return R.RecallSource(**params)

    def record(self, *, accept=False, identity_slot='1', **kwargs):
        return R.record_recall(self.memory, self.soul_owner, self.source(**kwargs),
                               identity=IdempotencyIdentity('rp-recall', identity_slot),
                               accept=accept)

    def soul_contents(self):
        return [r.content for r in self.memory.query(self.soul_session).records]

    # --- 正向：闭环 ---------------------------------------------------------

    def test_recall_is_candidate_until_accepted(self):
        self.record()
        self.assertEqual(self.soul_contents(), [],
                         '未接受的回忆录不应进入正常会话检索')
        receipt = self.record(identity_slot='2', accept=True)
        contents = self.soul_contents()
        self.assertEqual(len(contents), 1)
        self.assertIn('角色扮演回忆', contents[0])
        record = self.memory.get_memory(self.soul_session, receipt.memory_id)
        self.assertIs(record.provenance.source_type, SourceType.ROLEPLAY_RECALL)
        self.assertIs(record.kind, MemoryKind.SHARED_EXPERIENCE)

    def test_recall_keeps_fictional_shared_experience_and_source_world(self):
        receipt = self.record(accept=True)
        p = self.memory.get_memory(self.soul_session, receipt.memory_id).provenance
        self.assertIs(p.reality_status, RealityStatus.FICTIONAL_SHARED_EXPERIENCE)
        self.assertNotEqual(p.reality_status, RealityStatus.OBSERVED_REAL_WORLD_FACT)
        self.assertEqual(p.source_world_id, self.a.world.world_id)
        self.assertEqual(p.source_timeline_id, self.a.timeline.scope.timeline_id)
        self.assertIn('rp-world:', p.source_id)
        self.assertIn('fp-synthetic-1', p.source_id)

    def test_recall_body_states_the_roleplay_boundary(self):
        receipt = self.record(accept=True)
        content = self.memory.get_memory(self.soul_session, receipt.memory_id).content
        self.assertIn(R.BOUNDARY, content)
        self.assertIn(str(self.a.world.world_id.value), content)
        self.assertIn('原创角色', content)

    def test_digest_is_deterministic_and_bounded(self):
        source = self.source()
        self.assertEqual(R.digest(source), R.digest(source))
        long_item = '很长的片段' * 40
        with self.assertRaises(ValueError):
            R.digest(self.source(highlights=(long_item,)))

    def test_provenance_time_is_the_experience_not_the_wall_clock(self):
        """回忆录记录事情何时发生；同一段经历重复登记结果确定。"""
        first = R.build_provenance(self.source(), self.actor)
        second = R.build_provenance(self.source(), self.actor)
        self.assertEqual(first.created_at, second.created_at)
        self.assertEqual(first.created_at, self.now + timedelta(hours=1))

    def test_repeat_exit_does_not_duplicate_the_recall(self):
        """同一次扮演重复登记只保留一条回忆录。"""
        first = self.record(accept=True)
        second = self.record(accept=True)
        self.assertEqual(first.memory_id, second.memory_id)
        self.assertEqual(len(self.soul_contents()), 1)

    # --- 反例：边界必须仍然关闭 --------------------------------------------

    def test_recall_rejects_roleplay_target_instead_of_soul(self):
        with self.assertRaises(MemoryRuntimeError):
            R.record_recall(self.memory, self.owner, self.source(),
                            identity=IdempotencyIdentity('rp-recall', 'rp-target'))

    def test_recall_rejects_non_roleplay_source_world(self):
        provenance = R.build_provenance(
            self.source(source_scope=self.soul_scope), self.actor)
        with self.assertRaises(MemoryRuntimeError):
            self.memory.create_roleplay_recall(
                self.soul_owner, self.memory.collection_revision(self.soul_owner),
                IdempotencyIdentity('rp-recall', 'soul-source'),
                content='伪造回忆录', provenance=provenance)

    def test_recall_rejects_reality_upgrade_attempt(self):
        """来源语义不得提升：扮演不能被说成现实事实。"""
        prov = R.build_provenance(self.source(), self.actor)
        # 领域层已经拒绝把 ROLEPLAY_RECALL 声明为观测事实。
        with self.assertRaises(DomainError):
            replace(prov, reality_status=RealityStatus.OBSERVED_REAL_WORLD_FACT)
        # Memory 层再拒绝任何不属于该来源的 reality status。
        upgraded = replace(prov, reality_status=RealityStatus.USER_CLAIMED)
        with self.assertRaises(MemoryRuntimeError):
            self.memory.create_roleplay_recall(
                self.soul_owner, self.memory.collection_revision(self.soul_owner),
                IdempotencyIdentity('rp-recall', 'upgrade'),
                content='把扮演说成真的', provenance=upgraded)

    def test_recall_rejects_source_session_reference(self):
        prov = R.build_provenance(self.source(), self.actor)
        with_session = replace(
            prov, source_session_id=self.a.sessions[-1].session_id)
        with self.assertRaises(MemoryRuntimeError):
            self.memory.create_roleplay_recall(
                self.soul_owner, self.memory.collection_revision(self.soul_owner),
                IdempotencyIdentity('rp-recall', 'session-ref'),
                content='携带源会话引用', provenance=with_session)

    def test_recall_rejects_timeline_mismatch(self):
        """来源时间线与源世界不符时拒绝。"""
        provenance = replace(R.build_provenance(self.source(), self.actor),
                             source_timeline_id=DomainId.new(IdKind.TIMELINE))
        with self.assertRaises(MemoryRuntimeError):
            self.memory.create_roleplay_recall(
                self.soul_owner, self.memory.collection_revision(self.soul_owner),
                IdempotencyIdentity('rp-recall', 'timeline-mismatch'),
                content='时间线不符的回忆录', provenance=provenance)

    # --- 隔离与遗忘 ---------------------------------------------------------

    def test_rp_memory_text_is_not_copied_into_soul(self):
        secret = 'RP_ONLY_SECRET'
        self.memory.create_owner_memory(
            self.owner, self.memory.collection_revision(self.owner),
            IdempotencyIdentity('rp','secret'), content=secret, kind=MemoryKind.EPISODIC,
            provenance=self.provenance('RP 密语'), audience=(self.session.viewer,))
        self.record(accept=True)
        joined = '\n'.join(self.soul_contents())
        self.assertNotIn(secret, joined, 'RP 原文不得复制进 Soul World')

    def test_forgotten_recall_stays_forgotten(self):
        receipt = self.record(accept=True)
        self.assertEqual(len(self.soul_contents()), 1)
        self.memory.delete_memory(self.soul_owner, receipt.memory_id,
                                  self.memory.collection_revision(self.soul_owner),
                                  IdempotencyIdentity('rp-recall', 'forget'))
        self.assertEqual(self.soul_contents(), [])
        self.assertEqual(self.soul_contents(), [], '遗忘后不得因重查复活')

    def test_recall_readable_after_leaving_cosplay(self):
        receipt = self.record(accept=True)
        snapshot = self.world.snapshot(self.actor, self.a.world.world_id)
        session = next(s for s in snapshot.sessions if s.status.value == 'open')
        self.world.exit(self.actor, self.a.world.world_id, self.a.timeline.scope.timeline_id,
                        session.session_id, snapshot.world.revision, snapshot.world.writer_epoch)
        record = self.memory.get_memory(self.soul_session, receipt.memory_id)
        self.assertIs(record.provenance.reality_status,
                      RealityStatus.FICTIONAL_SHARED_EXPERIENCE)
        self.assertIn(R.BOUNDARY, record.content)

    def test_bridge_source_still_denied(self):
        """既有安全边界不变：Bridge 仍然不能写目标 Memory。"""
        prov = replace(
            R.build_provenance(self.source(), self.actor), source_type=SourceType.BRIDGE)
        with self.assertRaises(MemoryRuntimeError):
            self.memory.create_owner_memory(
                self.soul_owner, self.memory.collection_revision(self.soul_owner),
                IdempotencyIdentity('rp-recall', 'bridge'),
                content='bridge 写入', kind=MemoryKind.EPISODIC, provenance=prov,
                audience=(MemoryAudience(AudienceKind.SOUL, self.soul_scope.soul_id),))

    # 泛入口也必须守住回忆录契约；以下只新增拒绝断言，不修改原安全测试。
    def generic_recall(self, slot='generic', **kwargs):
        params = dict(content='合成回忆录', kind=MemoryKind.SHARED_EXPERIENCE,
                      provenance=R.build_provenance(self.source(), self.actor,
                                                    canon=CanonStatus.ACCEPTED),
                      audience=R.recall_audience(self.soul_scope.soul_id))
        params.update(kwargs)
        return self.memory.create_owner_memory(
            self.soul_owner, self.memory.collection_revision(self.soul_owner),
            IdempotencyIdentity('generic-recall', slot), **params)

    def memory_state(self):
        with self.repo.transaction() as tx:
            return (tx.revision(self.soul_scope),
                    tuple(tuple(row) for row in tx.db.execute('SELECT * FROM world_memories ORDER BY memory_id')),
                    tuple(tuple(row) for row in tx.db.execute('SELECT * FROM memory_operations ORDER BY sequence')))

    def denied_unchanged(self, operation):
        before = self.memory_state()
        with self.assertRaises(MemoryRuntimeError):
            operation()
        self.assertEqual(self.memory_state(), before, '拒绝不能推进修订、改旧记录或新增审计')

    def test_generic_recall_rejects_missing_source(self):
        source = self.source(source_scope=WorldScope(
            self.actor.owner_id, self.soul.soul_id, DomainId.new(IdKind.WORLD),
            DomainId.new(IdKind.TIMELINE)))
        self.denied_unchanged(lambda: self.generic_recall(
            provenance=R.build_provenance(source, self.actor, canon=CanonStatus.ACCEPTED)))

    def test_generic_recall_rejects_bad_timeline(self):
        provenance = replace(R.build_provenance(self.source(), self.actor),
                             source_timeline_id=DomainId.new(IdKind.TIMELINE))
        self.denied_unchanged(lambda: self.generic_recall(provenance=provenance))

    def test_generic_recall_rejects_other_soul_source(self):
        from life_engine.domain import Soul
        other = Soul(DomainId.new(IdKind.SOUL), self.actor.owner_id, DomainId.new(IdKind.WORLD))
        self.world.register_soul(self.actor, other)
        world = self.world.create_roleplay_world(self.actor, other.soul_id, self.now)
        source = self.source(source_scope=world.timeline.scope)
        self.denied_unchanged(lambda: self.generic_recall(
            provenance=R.build_provenance(source, self.actor)))

    def test_generic_recall_rejects_other_owner_source(self):
        from life_engine.domain import Principal, Soul
        actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
        soul = Soul(DomainId.new(IdKind.SOUL), actor.owner_id, DomainId.new(IdKind.WORLD))
        self.world.register_soul(actor, soul)
        world = self.world.create_roleplay_world(actor, soul.soul_id, self.now)
        source = self.source(source_scope=world.timeline.scope)
        self.denied_unchanged(lambda: self.generic_recall(
            provenance=R.build_provenance(source, self.actor)))

    def test_generic_recall_rejects_wrong_kind_audience_and_subject(self):
        changes = ({'kind': MemoryKind.EPISODIC},
                   {'audience': (MemoryAudience(AudienceKind.WORLD),)},
                   {'subjects': (MemorySubject(SubjectKind.SOUL, self.soul_scope.soul_id),)})
        for index, change in enumerate(changes):
            with self.subTest(change=change):
                self.denied_unchanged(lambda: self.generic_recall(str(index), **change))

    def test_generic_recall_rejects_roleplay_target(self):
        other = self.make_world()
        provenance = R.build_provenance(self.source(source_scope=other.timeline.scope), self.actor)
        self.denied_unchanged(lambda: self.memory.create_owner_memory(
            self.owner, self.memory.collection_revision(self.owner), IdempotencyIdentity('bad-target', '1'),
            content='合成回忆录', kind=MemoryKind.SHARED_EXPERIENCE, provenance=provenance,
            audience=(MemoryAudience(AudienceKind.WORLD),)))

    def test_recall_audience_cannot_expand_through_generic_change(self):
        receipt = self.record(accept=True)
        self.denied_unchanged(lambda: self.memory.change_audience(
            self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
            IdempotencyIdentity('recall-expand', '1'), audience=(MemoryAudience(AudienceKind.WORLD),)))

    def test_supersede_generic_memory_cannot_introduce_forged_recall(self):
        ordinary = self.memory.create_owner_memory(
            self.soul_owner, self.memory.collection_revision(self.soul_owner),
            IdempotencyIdentity('ordinary', '1'), content='普通合成记忆', kind=MemoryKind.SHARED_EXPERIENCE,
            provenance=Provenance(SourceType.OWNER_COMMAND, '合成正控', self.now, self.actor,
                                  RealityStatus.FICTIONAL, CanonStatus.ACCEPTED),
            audience=R.recall_audience(self.soul_scope.soul_id))
        provenance = replace(R.build_provenance(self.source(), self.actor),
                             source_world_id=DomainId.new(IdKind.WORLD),
                             source_timeline_id=DomainId.new(IdKind.TIMELINE))
        self.denied_unchanged(lambda: self.memory.supersede_memory(
            self.soul_owner, ordinary.memory_id, self.memory.collection_revision(self.soul_owner),
            IdempotencyIdentity('forge-supersede', '1'), content='伪造回忆', provenance=provenance))

    def test_supersede_generic_memory_cannot_introduce_wrong_recall_shape(self):
        provenance = Provenance(SourceType.OWNER_COMMAND, '普通合成来源', self.now, self.actor,
                                RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
        for index, (kind, audience) in enumerate((
                (MemoryKind.EPISODIC, R.recall_audience(self.soul_scope.soul_id)),
                (MemoryKind.SHARED_EXPERIENCE, (MemoryAudience(AudienceKind.WORLD),)))):
            with self.subTest(kind=kind, audience=audience):
                ordinary = self.memory.create_owner_memory(
                    self.soul_owner, self.memory.collection_revision(self.soul_owner),
                    IdempotencyIdentity('ordinary-shape', str(index)), content='普通合成记忆',
                    kind=kind, provenance=provenance, audience=audience)
                self.denied_unchanged(lambda: self.memory.supersede_memory(
                    self.soul_owner, ordinary.memory_id, self.memory.collection_revision(self.soul_owner),
                    IdempotencyIdentity('shape-supersede', str(index)), content='非法回忆录布局',
                    provenance=R.build_provenance(self.source(), self.actor)))

    def test_supersede_can_introduce_or_change_to_verified_roleplay_source(self):
        ordinary = self.memory.create_owner_memory(
            self.soul_owner, self.memory.collection_revision(self.soul_owner),
            IdempotencyIdentity('valid-supersede', 'ordinary'), content='普通合成记忆',
            kind=MemoryKind.SHARED_EXPERIENCE,
            provenance=Provenance(SourceType.OWNER_COMMAND, '合成正控', self.now, self.actor,
                                  RealityStatus.FICTIONAL, CanonStatus.ACCEPTED),
            audience=R.recall_audience(self.soul_scope.soul_id))
        receipt = self.memory.supersede_memory(
            self.soul_owner, ordinary.memory_id, self.memory.collection_revision(self.soul_owner),
            IdempotencyIdentity('valid-supersede', 'introduce'), content='合法回忆录',
            provenance=R.build_provenance(self.source(), self.actor, canon=CanonStatus.ACCEPTED))
        other = self.make_world()
        provenance = R.build_provenance(self.source(source_scope=other.timeline.scope), self.actor,
                                        canon=CanonStatus.ACCEPTED)
        receipt = self.memory.supersede_memory(
            self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
            IdempotencyIdentity('valid-supersede', 'change-source'), content='合法换源回忆录',
            provenance=provenance)
        self.assertEqual(self.memory.get_memory(self.soul_owner, receipt.memory_id).provenance, provenance)

    def test_supersede_recall_cannot_replace_with_missing_source_or_wrong_timeline(self):
        receipt = self.record(accept=True)
        provenance = self.memory.get_memory(self.soul_owner, receipt.memory_id).provenance
        changes = ({'source_world_id': DomainId.new(IdKind.WORLD)},
                   {'source_timeline_id': DomainId.new(IdKind.TIMELINE)})
        for index, change in enumerate(changes):
            with self.subTest(change=change):
                self.denied_unchanged(lambda: self.memory.supersede_memory(
                    self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
                    IdempotencyIdentity('change-source', str(index)), content='修改回忆',
                    provenance=replace(provenance, **change)))

    def test_supersede_recall_cannot_shed_fictional_source_identity(self):
        receipt = self.record(accept=True)
        ordinary = Provenance(SourceType.OWNER_COMMAND, '来源脱壳', self.now, self.actor,
                              RealityStatus.USER_CLAIMED, CanonStatus.ACCEPTED)
        self.denied_unchanged(lambda: self.memory.supersede_memory(
            self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
            IdempotencyIdentity('shed-source', '1'), content='声称真实经历', provenance=ordinary))

    def test_dedicated_create_validates_source_in_the_write_transaction(self):
        revision = self.memory.collection_revision(self.soul_owner)
        with patch.object(self.repo, 'transaction', wraps=self.repo.transaction) as transactions:
            self.memory.create_roleplay_recall(
                self.soul_owner, revision, IdempotencyIdentity('single-transaction', '1'),
                content='合法合成回忆', provenance=R.build_provenance(self.source(), self.actor))
        self.assertEqual(transactions.call_count, 1, '验源与写入不能分为两个事务')

    def test_source_unavailable_does_not_break_existing_recall_lifecycle(self):
        receipt = self.record()
        with self.repo.transaction() as tx:
            world_tx_class = type(tx.world)
        original = world_tx_class.get_world

        def unavailable_source(tx, world_id):
            if world_id == self.a.world.world_id:
                from life_engine.world_repository import FailureCode, WorldRuntimeError
                raise WorldRuntimeError(FailureCode.WORLD_NOT_FOUND)
            return original(tx, world_id)

        with patch.object(world_tx_class, 'get_world', unavailable_source):
            self.denied_unchanged(lambda: self.generic_recall('source-gone-new'))
            receipt = self.memory.accept_memory(
                self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
                IdempotencyIdentity('unavailable-source', 'accept'))
            self.assertEqual(len(self.soul_contents()), 1)
            self.memory.hide_memory(self.soul_owner, receipt.memory_id,
                                    self.memory.collection_revision(self.soul_owner),
                                    IdempotencyIdentity('unavailable-source', 'hide'))
            self.memory.unhide_memory(self.soul_owner, receipt.memory_id,
                                      self.memory.collection_revision(self.soul_owner),
                                      IdempotencyIdentity('unavailable-source', 'unhide'))
            receipt = self.memory.change_audience(
                self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
                IdempotencyIdentity('unavailable-source', 'same-audience'),
                audience=R.recall_audience(self.soul_scope.soul_id))
            old = self.memory.get_memory(self.soul_owner, receipt.memory_id)
            self.denied_unchanged(lambda: self.memory.supersede_memory(
                self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
                IdempotencyIdentity('unavailable-source', 'changed-source'), content='更改来源引用',
                provenance=replace(old.provenance, source_id='新来源引用')))
            receipt = self.memory.supersede_memory(
                self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
                IdempotencyIdentity('unavailable-source', 'same-source-text'),
                content='同来源的摘要修订', provenance=old.provenance)
            self.assertEqual(self.soul_contents(), ['同来源的摘要修订'])
            self.memory.delete_memory(self.soul_owner, receipt.memory_id,
                                      self.memory.collection_revision(self.soul_owner),
                                      IdempotencyIdentity('unavailable-source', 'forget'))
            self.assertEqual(self.soul_contents(), [])

    def test_archived_or_tombstoned_source_does_not_break_recall_reads(self):
        self.record(accept=True)
        for status in (WorldStatus.ARCHIVED, WorldStatus.TOMBSTONED):
            with self.world.repository.transaction() as tx:
                tx.db.execute('UPDATE worlds SET status=? WHERE world_id=?',
                              (status.value, str(self.a.world.world_id)))
            self.assertEqual(len(self.soul_contents()), 1)
