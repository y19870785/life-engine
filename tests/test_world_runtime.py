"""SP-004D 原创合成验收；不读取私有语料，不访问数据库或宿主。"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from threading import Barrier
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine.domain import (BindingStatus, CanonStatus, DefinitionRef, DefinitionVersion,
    DomainId, IdKind, Principal, Provenance, RealityStatus, Revision, Soul, SourceType,
    Values, WorldKind, WorldScope, WorldStatus, WorldTimeline, WriterEpoch)
from life_engine.domain_lifecycle import create_world
from life_engine.domain_policy import BridgeDecision, BridgeRequest, evaluate_bridge
from life_engine.import_cards import parse_bytes
from life_engine.import_ir import project_definition
from life_engine.world_repository import (FailureCode as Code, InMemoryWorldRepository,
                                          WorldRuntimeError, WorldSnapshot)
from life_engine.world_runtime import WorldRuntime


def new(kind):
    return DomainId.new(kind)


class FailingRepository:
    """通过仓储协议注入保存或提交失败，验证应用事务回滚。"""
    def __init__(self, repository, fail_save=None, fail_commit=False):
        self.repository, self.fail_save, self.fail_commit = repository, fail_save, fail_commit

    @contextmanager
    def transaction(self):
        with self.repository.transaction() as tx:
            outer = self
            class TransactionProxy:
                count = 0
                def __getattr__(self, name):
                    return getattr(tx, name)
                def save_world(self, snapshot, revision):
                    tx.save_world(snapshot, revision)
                    self.count += 1
                    if self.count == outer.fail_save:
                        raise RuntimeError('测试注入保存失败')
            yield TransactionProxy()
            if self.fail_commit:
                raise RuntimeError('测试注入提交失败')


class WorldRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 16, tzinfo=timezone.utc)
        self.actor = Principal(new(IdKind.PRINCIPAL), new(IdKind.OWNER))
        self.soul = Soul(new(IdKind.SOUL), self.actor.owner_id, new(IdKind.WORLD))
        self.repo = InMemoryWorldRepository()
        self.runtime = WorldRuntime(self.repo)
        self.runtime.register_soul(self.actor, self.soul)
        raw = {'spec': 'chara_card_v3', 'spec_version': '3.0', 'data': {
            'name': '原创旅人', 'description': '用于世界隔离验收的原创人物。',
            'first_mes': '你好，欢迎进入测试世界。', 'group_only_greetings': [], 'extensions': {}}}
        self.ir = parse_bytes(json.dumps(raw).encode())
        self.definition = project_definition(self.ir, self.actor, self.now)
        self.runtime.register_definition(self.actor, self.definition)

    def make(self):
        created = self.runtime.create_roleplay_world(self.actor, self.soul.soul_id, self.now)
        return self.runtime.instantiate(self.actor, created.world.world_id, created.timeline.scope.timeline_id,
            self.definition.reference, created.world.revision, self.now)

    def open(self, s, resume=False, **kwargs):
        method = self.runtime.resume if resume else self.runtime.enter
        return method(self.actor, s.world.world_id, s.timeline.scope.timeline_id,
                      s.characters[0].character_instance_id if s.characters else None,
                      s.world.revision, s.world.writer_epoch, **kwargs)

    def close(self, s, suspend=False):
        method = self.runtime.suspend if suspend else self.runtime.exit
        return method(self.actor, s.world.world_id, s.timeline.scope.timeline_id, s.sessions[-1].session_id,
                      s.world.revision, s.world.writer_epoch)

    def write(self, s, **kwargs):
        args = dict(actor=self.actor, world_id=s.world.world_id, timeline_id=s.timeline.scope.timeline_id,
                    session_id=s.sessions[-1].session_id, character_id=s.characters[0].character_instance_id,
                    expected_revision=s.world.revision, writer_epoch=s.world.writer_epoch, at=self.now,
                    state=Values((('地点', '咖啡店'),)), relationships=Values((('用户', '熟悉'),)))
        args.update(kwargs)
        return self.runtime.update_character(**args)

    def switch(self, a, b, **kwargs):
        args = dict(actor=self.actor, source_world_id=a.world.world_id,
            source_timeline_id=a.timeline.scope.timeline_id, source_session_id=a.sessions[-1].session_id,
            source_revision=a.world.revision, source_epoch=a.world.writer_epoch,
            target_world_id=b.world.world_id, target_timeline_id=b.timeline.scope.timeline_id,
            target_character_id=b.characters[0].character_instance_id,
            target_revision=b.world.revision, target_epoch=b.world.writer_epoch)
        args.update(kwargs)
        return self.runtime.switch_world(**args)

    def assert_code(self, code, call):
        with self.assertRaises(WorldRuntimeError) as error:
            call()
        self.assertEqual(error.exception.code, code)

    def test_import_world_exit_resume_acceptance(self):
        a = self.make()
        b = self.make()
        self.assertEqual(a.characters[0].definition, self.definition.reference)
        active = self.open(a)
        exited = self.close(active)
        resumed = self.open(exited, resume=True)
        self.assertEqual(exited.world.status, WorldStatus.SUSPENDED)
        self.assertEqual(exited.sessions[0].status, BindingStatus.CLOSED)
        self.assertEqual(resumed.world.status, WorldStatus.ACTIVE)
        self.assertEqual(a.world.world_id, resumed.world.world_id)
        self.assertEqual(a.timeline, resumed.timeline)
        self.assertEqual(a.characters, resumed.characters)
        self.assertEqual(resumed.characters[0].definition, self.definition.reference)
        self.assertNotEqual(active.sessions[0].session_id, resumed.sessions[-1].session_id)
        self.assertEqual(resumed.world.writer_epoch.value, active.world.writer_epoch.value + 2)
        self.assertEqual(resumed.world.revision.value, active.world.revision.value + 2)
        self.assertEqual(self.runtime.snapshot(self.actor, b.world.world_id), b)

    def test_create_is_explicit_and_ids_are_unique(self):
        a = self.runtime.create_roleplay_world(self.actor, self.soul.soul_id, self.now)
        b = self.runtime.create_roleplay_world(self.actor, self.soul.soul_id, self.now)
        self.assertEqual(a.world.kind, WorldKind.ROLEPLAY)
        self.assertEqual(a.world.status, WorldStatus.CREATED)
        self.assertEqual(a.world.revision, Revision(0))
        self.assertEqual(a.world.writer_epoch, WriterEpoch(0))
        self.assertNotEqual(a.world.world_id, b.world.world_id)
        self.assertNotEqual(a.timeline.scope.timeline_id, b.timeline.scope.timeline_id)
        self.assertEqual(a.sessions, ())

    def test_multiworld_values_and_epochs_are_independent(self):
        a, b = self.open(self.make()), self.open(self.make())
        updated = self.write(a)
        self.assertNotEqual(a.characters[0].character_instance_id, b.characters[0].character_instance_id)
        self.assertNotEqual(updated.characters[0].state, b.characters[0].state)
        self.assertNotEqual(updated.characters[0].relationships, b.characters[0].relationships)
        self.close(updated)
        self.assertEqual(self.runtime.snapshot(self.actor, b.world.world_id), b)
        with self.assertRaises(FrozenInstanceError):
            updated.characters[0].state = Values()

    def test_definition_version_is_pinned_and_cannot_be_overwritten(self):
        a = self.make()
        v2 = replace(self.definition, reference=DefinitionRef(self.definition.reference.definition_id, DefinitionVersion(2)), name='新版原创旅人')
        self.runtime.register_definition(self.actor, v2)
        self.assertEqual(self.runtime.snapshot(self.actor, a.world.world_id).characters[0].definition,
                         self.definition.reference)
        self.assert_code(Code.DEFINITION_VERSION_CONFLICT,
                         lambda: self.runtime.register_definition(self.actor, replace(self.definition, name='偷偷改写')))
        b = self.runtime.create_roleplay_world(self.actor, self.soul.soul_id, self.now)
        b = self.runtime.instantiate(self.actor, b.world.world_id, b.timeline.scope.timeline_id,
                                     v2.reference, b.world.revision, self.now)
        self.assertEqual(b.characters[0].definition, v2.reference)
        self.assertEqual(a.characters[0].definition.version, DefinitionVersion(1))

    def test_suspend_closes_binding_and_resume_retains_identity(self):
        active = self.open(self.make())
        suspended = self.close(active, suspend=True)
        self.assertEqual(suspended.world.status, WorldStatus.SUSPENDED)
        self.assertEqual(suspended.sessions[-1].status, BindingStatus.CLOSED)
        self.assertEqual(self.open(suspended, resume=True).characters, active.characters)

    def test_old_epoch_rejected_after_exit_and_resume(self):
        active = self.open(self.make())
        exited = self.close(active)
        self.assert_code(Code.STALE_WRITER_EPOCH, lambda: self.write(active))
        resumed = self.open(exited, resume=True)
        for epoch in (active.world.writer_epoch, exited.world.writer_epoch):
            self.assert_code(Code.STALE_WRITER_EPOCH, lambda: self.write(resumed, writer_epoch=epoch))
        self.assert_code(Code.STALE_WRITER_EPOCH, lambda: self.write(resumed, session_id=active.sessions[-1].session_id))

    def test_revision_conflict_uses_repository_not_supplied_snapshot(self):
        active = self.open(self.make())
        updated = self.write(active)
        self.assert_code(Code.REVISION_CONFLICT, lambda: self.write(active))
        self.assertEqual(self.runtime.snapshot(self.actor, active.world.world_id), updated)

    def test_concurrent_compare_and_swap_has_one_winner(self):
        active = self.open(self.make())
        barrier = Barrier(2)
        def write():
            barrier.wait(timeout=5)
            try:
                self.write(active)
                return '成功'
            except WorldRuntimeError as error:
                return error.code.value
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: write(), range(2)))
        self.assertCountEqual(results, ['成功', Code.REVISION_CONFLICT.value])

    def test_cross_world_character_cannot_bind(self):
        a, b = self.make(), self.make()
        self.assert_code(Code.WORLD_MISMATCH, lambda: self.runtime.enter(self.actor,
            b.world.world_id, b.timeline.scope.timeline_id, a.characters[0].character_instance_id,
            b.world.revision, b.world.writer_epoch))
        self.assertEqual(self.runtime.snapshot(self.actor, b.world.world_id), b)

    def test_cross_timeline_cannot_bind_or_write(self):
        a, b = self.make(), self.make()
        self.assert_code(Code.TIMELINE_MISMATCH, lambda: self.runtime.enter(self.actor,
            a.world.world_id, b.timeline.scope.timeline_id, a.characters[0].character_instance_id,
            a.world.revision, a.world.writer_epoch))
        active = self.open(a)
        self.assert_code(Code.TIMELINE_MISMATCH, lambda: self.write(active, timeline_id=b.timeline.scope.timeline_id))

    def test_owner_and_principal_boundaries(self):
        a = self.make()
        foreign = Principal(new(IdKind.PRINCIPAL), new(IdKind.OWNER))
        self.assert_code(Code.OWNER_MISMATCH, lambda: self.runtime.snapshot(foreign, a.world.world_id))
        self.assert_code(Code.OWNER_MISMATCH, lambda: self.runtime.create_roleplay_world(foreign, self.soul.soul_id, self.now))
        foreign_definition = project_definition(self.ir, foreign, self.now)
        self.runtime.register_definition(foreign, foreign_definition)
        self.assert_code(Code.OWNER_MISMATCH, lambda: self.runtime.instantiate(self.actor, a.world.world_id,
            a.timeline.scope.timeline_id, foreign_definition.reference, a.world.revision, self.now))
        active = self.open(a)
        same_owner_other_principal = Principal(new(IdKind.PRINCIPAL), self.actor.owner_id)
        self.assert_code(Code.SESSION_BINDING_CONFLICT, lambda: self.write(active, actor=same_owner_other_principal))

    def test_missing_entities_are_structured(self):
        a = self.make()
        self.assert_code(Code.WORLD_NOT_FOUND, lambda: self.runtime.snapshot(self.actor, new(IdKind.WORLD)))
        self.assert_code(Code.DEFINITION_NOT_FOUND, lambda: self.runtime.instantiate(self.actor, a.world.world_id,
            a.timeline.scope.timeline_id, DefinitionRef(new(IdKind.DEFINITION), DefinitionVersion(1)), a.world.revision, self.now))
        self.assert_code(Code.CHARACTER_INSTANCE_NOT_FOUND, lambda: self.runtime.enter(self.actor,
            a.world.world_id, a.timeline.scope.timeline_id, new(IdKind.CHARACTER), a.world.revision, a.world.writer_epoch))

    def test_closed_session_and_illegal_lifecycle(self):
        a = self.make()
        self.assert_code(Code.INVALID_LIFECYCLE_TRANSITION, lambda: self.open(a, resume=True))
        active = self.open(a)
        self.assert_code(Code.SESSION_BINDING_CONFLICT, lambda: self.open(active))
        exited = self.close(active)
        self.assert_code(Code.SESSION_ALREADY_CLOSED, lambda: self.close(exited))
        self.assert_code(Code.INVALID_LIFECYCLE_TRANSITION, lambda: self.open(exited))

    def test_switch_created_and_suspended_targets(self):
        a, b = self.open(self.make()), self.make()
        switched = self.switch(a, b)
        self.assertEqual(switched.source.world.status, WorldStatus.SUSPENDED)
        self.assertEqual(switched.target.world.status, WorldStatus.ACTIVE)
        self.assert_code(Code.STALE_WRITER_EPOCH, lambda: self.write(a))
        self.assert_code(Code.WORLD_MISMATCH, lambda: self.write(switched.target, session_id=a.sessions[-1].session_id))
        back = self.switch(switched.target, switched.source)
        self.assertEqual(back.target.characters, a.characters)

    def test_switch_invalid_target_rolls_back_source(self):
        a, b = self.open(self.make()), self.make()
        self.assert_code(Code.REVISION_CONFLICT, lambda: self.switch(a, b, target_revision=Revision(999)))
        self.assertEqual(self.runtime.snapshot(self.actor, a.world.world_id), a)
        self.assertEqual(self.runtime.snapshot(self.actor, b.world.world_id), b)

    def test_enter_binding_failure_leaves_created_world(self):
        a, b = self.open(self.make()), self.make()
        self.assert_code(Code.SESSION_BINDING_CONFLICT,
                         lambda: self.open(b, session_id=a.sessions[-1].session_id))
        self.assertEqual(self.runtime.snapshot(self.actor, b.world.world_id), b)

    def test_switch_second_save_failure_rolls_back_both_worlds(self):
        a, b = self.open(self.make()), self.make()
        self.runtime.repository = FailingRepository(self.repo, fail_save=2)
        with self.assertRaisesRegex(RuntimeError, '测试注入保存失败'):
            self.switch(a, b)
        self.runtime.repository = self.repo
        self.assertEqual(self.runtime.snapshot(self.actor, a.world.world_id), a)
        self.assertEqual(self.runtime.snapshot(self.actor, b.world.world_id), b)

    def test_enter_commit_failure_rolls_back_world_and_binding(self):
        a = self.make()
        self.runtime.repository = FailingRepository(self.repo, fail_commit=True)
        with self.assertRaisesRegex(RuntimeError, '测试注入提交失败'):
            self.open(a)
        self.runtime.repository = self.repo
        self.assertEqual(self.runtime.snapshot(self.actor, a.world.world_id), a)

    def test_soul_world_close_keeps_active_and_can_rebind(self):
        provenance = Provenance(SourceType.OWNER_COMMAND, '测试创建', self.now, self.actor, RealityStatus.UNKNOWN)
        world = create_world(self.soul, self.actor, self.soul.soul_world_id, WorldKind.SOUL, provenance).world
        scope = WorldScope(self.actor.owner_id, self.soul.soul_id, world.world_id, new(IdKind.TIMELINE))
        original = WorldSnapshot(world, WorldTimeline(scope, provenance))
        with self.repo.transaction() as tx:
            tx.add_world(original)
        active = self.open(original)
        self.assert_code(Code.INVALID_LIFECYCLE_TRANSITION, lambda: self.close(active, suspend=True))
        exited = self.close(active)
        self.assertEqual(exited.world.status, WorldStatus.ACTIVE)
        rebound = self.open(exited)
        self.assertNotEqual(rebound.sessions[-1].session_id, active.sessions[-1].session_id)
        self.assertEqual(rebound.characters, ())

    def test_reality_canon_bridge_and_soul_unchanged(self):
        a, b = self.make(), self.make()
        exited = self.close(self.open(a))
        self.assertEqual(self.definition.provenance.reality_status, RealityStatus.UNKNOWN)
        self.assertEqual(self.definition.provenance.canon_status, CanonStatus.UNREVIEWED)
        for provenance in (exited.world.provenance, exited.timeline.provenance, exited.characters[0].provenance):
            self.assertEqual(provenance.reality_status, RealityStatus.FICTIONAL)
            self.assertEqual(provenance.canon_status, CanonStatus.UNREVIEWED)
        request = BridgeRequest(self.actor, a.timeline.scope, b.timeline.scope,
                                frozenset({'state'}), '状态', '测试', frozenset({'用户'}))
        self.assertEqual(evaluate_bridge(None, request, current_grant_revision=None, now=self.now), BridgeDecision.DENY)
        with self.repo.transaction() as tx:
            self.assertEqual(tx.get_soul(self.soul.soul_id), self.soul)

    def test_explicit_invalid_epoch_and_timeline_are_not_omitted(self):
        a = self.make()
        self.assert_code(Code.INVALID_ARGUMENT, lambda: self.runtime.enter(self.actor, a.world.world_id,
            a.timeline.scope.timeline_id, a.characters[0].character_instance_id, a.world.revision, None))
        self.assert_code(Code.INVALID_ARGUMENT, lambda: self.runtime.enter(self.actor, a.world.world_id,
            None, a.characters[0].character_instance_id, a.world.revision, a.world.writer_epoch))

    def test_duplicate_identity_and_cross_owner_definition_versions(self):
        a = self.make()
        self.assert_code(Code.IDENTITY_CONFLICT, lambda: self.runtime.create_roleplay_world(self.actor,
            self.soul.soul_id, self.now, timeline_id=a.timeline.scope.timeline_id))
        foreign = Principal(new(IdKind.PRINCIPAL), new(IdKind.OWNER))
        definition = project_definition(self.ir, foreign, self.now,
            DefinitionRef(self.definition.reference.definition_id, DefinitionVersion(2)))
        self.assert_code(Code.OWNER_MISMATCH, lambda: self.runtime.register_definition(foreign, definition))

    def test_resume_cannot_silently_change_character(self):
        a = self.make()
        a = self.runtime.instantiate(self.actor, a.world.world_id, a.timeline.scope.timeline_id,
                                    self.definition.reference, a.world.revision, self.now)
        exited = self.close(self.open(a))
        self.assert_code(Code.SESSION_BINDING_CONFLICT, lambda: self.runtime.resume(self.actor,
            exited.world.world_id, exited.timeline.scope.timeline_id, exited.characters[1].character_instance_id,
            exited.world.revision, exited.world.writer_epoch))

    def test_transaction_closed_and_nested_transaction_are_rejected(self):
        with self.repo.transaction() as tx:
            with self.assertRaises(WorldRuntimeError) as error:
                with self.repo.transaction():
                    pass
            self.assertEqual(error.exception.code, Code.NESTED_TRANSACTION)
        self.assert_code(Code.TRANSACTION_CLOSED, lambda: tx.get_soul(self.soul.soul_id))

    def test_repository_preserves_pinned_references_and_closed_history(self):
        a = self.make()
        v2 = replace(self.definition, reference=DefinitionRef(self.definition.reference.definition_id, DefinitionVersion(2)))
        self.runtime.register_definition(self.actor, v2)
        with self.assertRaises(WorldRuntimeError) as error:
            with self.repo.transaction() as tx:
                altered = replace(a, world=replace(a.world, revision=a.world.revision.next()),
                                  characters=(replace(a.characters[0], definition=v2.reference),))
                tx.save_world(altered, a.world.revision)
        self.assertEqual(error.exception.code, Code.DEFINITION_VERSION_CONFLICT)
        exited = self.close(self.open(a))
        with self.assertRaises(WorldRuntimeError) as error:
            with self.repo.transaction() as tx:
                tx.save_world(replace(exited, world=replace(exited.world, revision=exited.world.revision.next()),
                                      sessions=()), exited.world.revision)
        self.assertEqual(error.exception.code, Code.SESSION_BINDING_CONFLICT)
        self.assertEqual(self.runtime.snapshot(self.actor, a.world.world_id), exited)

    def test_new_application_reuses_existing_repository_and_original_ids(self):
        exited = self.close(self.open(self.make()))
        self.runtime = WorldRuntime(self.repo)
        stored = self.runtime.snapshot(self.actor, exited.world.world_id)
        self.assertEqual(stored, exited)
        self.assertEqual(self.open(stored, resume=True).characters, exited.characters)

    def test_instance_creation_rejects_active_world_without_partial_mutation(self):
        active = self.open(self.make())
        self.assert_code(Code.INVALID_LIFECYCLE_TRANSITION, lambda: self.runtime.instantiate(self.actor,
            active.world.world_id, active.timeline.scope.timeline_id, self.definition.reference,
            active.world.revision, self.now))
        self.assertEqual(self.runtime.snapshot(self.actor, active.world.world_id), active)

    def test_no_database_network_or_host_process(self):
        with patch('sqlite3.connect', side_effect=AssertionError('禁止数据库')), \
                patch('socket.create_connection', side_effect=AssertionError('禁止网络')), \
                patch('subprocess.run', side_effect=AssertionError('禁止宿主进程')):
            self.open(self.close(self.open(self.make())), resume=True)


if __name__ == '__main__':
    unittest.main()
