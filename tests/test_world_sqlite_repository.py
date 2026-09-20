"""SQLite 与内存仓储共用领域合同，并增加重启、竞争和坏数据验收。"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
from threading import Barrier
import unittest
from unittest.mock import patch

import test_world_runtime as contract
from life_engine.domain import (BindingStatus, DefinitionRef, DefinitionVersion, WorldStatus, Values, Revision,
    CanonStatus, RealityStatus, SourceType, Provenance)
from life_engine.store import Store
from life_engine.world_repository import FailureCode as Code, WorldRuntimeError
from life_engine.world_runtime import WorldRuntime
from life_engine.world_sqlite_repository import SQLiteWorldRepository
from life_engine.durable import db_check


class SQLiteWorldTests(contract.WorldRuntimeContract, unittest.TestCase):
    def make_repository(self):
        self.directory = tempfile.TemporaryDirectory(prefix='世界 SQLite ')
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'life.db'
        Store(self.path, 'synthetic')
        return SQLiteWorldRepository(self.path)

    def restart(self):
        self.repo.close()
        self.repo = SQLiteWorldRepository(self.path)
        self.runtime = WorldRuntime(self.repo)

    def test_v3_restart_resume_preserves_all_values(self):
        active = self.write(self.open(self.make()))
        exited = self.close(active)
        v2 = replace(self.definition, reference=DefinitionRef(self.definition.reference.definition_id, DefinitionVersion(2)))
        self.runtime.register_definition(self.actor, v2)
        self.restart()
        with self.repo.transaction() as tx:
            self.assertEqual(tx.get_soul(self.soul.soul_id), self.soul)
            self.assertEqual(tx.get_definition(self.definition.reference), self.definition)
            self.assertEqual(tx.get_world(exited.world.world_id), exited)
            self.assertEqual(tx.get_character(exited.characters[0].character_instance_id), exited.characters[0])
            self.assertEqual(tx.get_session(exited.sessions[0].session_id), exited.sessions[0])
        resumed = self.open(exited, resume=True)
        updated = self.write(resumed, state=Values((('地点', '书店'),)))
        self.assertEqual(updated.world.world_id, exited.world.world_id)
        self.assertEqual(updated.timeline, exited.timeline)
        self.assertEqual(updated.characters[0].character_instance_id, exited.characters[0].character_instance_id)
        self.assertEqual(updated.characters[0].definition, self.definition.reference)
        self.assertEqual(updated.world.revision.value, exited.world.revision.value + 2)
        self.assertEqual(updated.world.writer_epoch.value, exited.world.writer_epoch.value + 1)
        self.assertNotEqual(updated.sessions[-1].session_id, exited.sessions[-1].session_id)
        self.assertEqual(updated.sessions[0].status, BindingStatus.CLOSED)
        db_check(self.path)

    def test_crash_recovery_is_idempotent_and_fences_old_repository(self):
        active = self.open(self.make())
        old = self.repo
        self.repo = SQLiteWorldRepository(self.path)
        self.runtime = WorldRuntime(self.repo)
        recovered = self.runtime.snapshot(self.actor, active.world.world_id)
        self.assertEqual(recovered.world.status, WorldStatus.SUSPENDED)
        self.assertEqual(recovered.world.writer_epoch, active.world.writer_epoch.next())
        self.assertEqual(recovered.world.revision, active.world.revision.next())
        self.assertEqual(recovered.characters, active.characters)
        self.assertEqual(recovered.timeline, active.timeline)
        self.assertEqual(recovered.sessions[0].status, BindingStatus.CLOSED)
        self.assert_code(Code.RECOVERY_REQUIRED, lambda: WorldRuntime(old).snapshot(self.actor, active.world.world_id))
        self.assert_code(Code.STALE_WRITER_EPOCH, lambda: self.write(active))
        self.assertEqual(self.repo.recover_open_sessions(), 0)
        self.assertEqual(self.runtime.snapshot(self.actor, active.world.world_id), recovered)
        self.open(recovered, resume=True)

    def test_soul_crash_keeps_active_and_rebinds(self):
        self.test_soul_world_close_keeps_active_and_can_rebind()
        before = self.runtime.snapshot(self.actor, self.soul.soul_world_id)
        self.restart()
        after = self.runtime.snapshot(self.actor, self.soul.soul_world_id)
        self.assertEqual(after.world.status, WorldStatus.ACTIVE)
        self.assertEqual(after.timeline, before.timeline)
        self.assertEqual(after.sessions[-1].status, BindingStatus.CLOSED)
        self.assertEqual(self.open(after).world.writer_epoch, after.world.writer_epoch.next())

    def test_independent_connections_database_cas(self):
        active = self.open(self.make())
        peer = SQLiteWorldRepository(self.path, runtime_id=self.repo.runtime_id)
        barrier = Barrier(2)
        def save(repo):
            barrier.wait(timeout=5)
            try:
                with repo.transaction() as tx:
                    tx.save_world(replace(active, world=replace(active.world, revision=active.world.revision.next())),
                                  active.world.revision)
                return '成功'
            except WorldRuntimeError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(save, (self.repo, peer))), ['成功', Code.REVISION_CONFLICT])

    def test_independent_connections_open_race_and_index(self):
        created = self.make()
        peer = SQLiteWorldRepository(self.path, runtime_id=self.repo.runtime_id)
        barrier = Barrier(2)
        def enter(repo):
            barrier.wait(timeout=5)
            try:
                return WorldRuntime(repo).enter(self.actor, created.world.world_id, created.timeline.scope.timeline_id,
                    created.characters[0].character_instance_id, created.world.revision, created.world.writer_epoch)
            except WorldRuntimeError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(enter, (self.repo, peer)))
        self.assertEqual(sum(x is not None for x in result), 1)
        with closing(sqlite3.connect(self.path)) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO session_bindings SELECT 'other',principal_id,owner_id,world_id,timeline_id,"
                           "character_instance_id,writer_epoch,status,position+1 FROM session_bindings WHERE status='open'")
            db.rollback()
            self.assertEqual(db.execute("SELECT count(*) FROM session_bindings WHERE status='open'").fetchone()[0], 1)

    def test_busy_is_not_revision_conflict_and_connection_released(self):
        peer = SQLiteWorldRepository(self.path, runtime_id=self.repo.runtime_id, timeout=.02)
        with closing(sqlite3.connect(self.path)) as lock:
            lock.execute('BEGIN IMMEDIATE')
            self.assert_code(Code.STORAGE_BUSY, lambda: WorldRuntime(peer).snapshot(self.actor, contract.new(contract.IdKind.WORLD)))
            lock.rollback()
        with peer.transaction() as tx:
            self.assertEqual(tx.get_soul(self.soul.soul_id), self.soul)
        moved = self.path.with_name('renamed.db')
        self.path.rename(moved)
        moved.rename(self.path)

    def test_full_provenance_and_timezone_roundtrip(self):
        from datetime import timezone, timedelta
        provenance = Provenance(SourceType.MODEL, '完整来源', self.now.astimezone(timezone(timedelta(hours=8))),
            self.actor, RealityStatus.AGENT_INFERRED, CanonStatus.ACCEPTED,
            contract.new(contract.IdKind.WORLD), contract.new(contract.IdKind.TIMELINE),
            contract.new(contract.IdKind.SESSION), contract.new(contract.IdKind.EVENT))
        definition = replace(self.definition, reference=DefinitionRef(self.definition.reference.definition_id,
                             DefinitionVersion(2)), provenance=provenance)
        self.runtime.register_definition(self.actor, definition)
        self.restart()
        with self.repo.transaction() as tx:
            restored = tx.get_definition(definition.reference)
        self.assertEqual(restored, definition)
        self.assertEqual(restored.provenance.created_at.utcoffset(), timedelta(0))

    def test_epoch_nine_survives_restart_then_resume_is_ten(self):
        world = self.make()
        for index in range(4):
            world = self.close(self.open(world, resume=index > 0))
        self.assertEqual(world.world.writer_epoch.value, 8)
        world = replace(world, world=replace(world.world, writer_epoch=world.world.writer_epoch.next(),
                                            revision=world.world.revision.next()))
        with self.repo.transaction() as tx:
            tx.save_world(world, Revision(world.world.revision.value - 1))
        self.restart()
        restored = self.runtime.snapshot(self.actor, world.world.world_id)
        self.assertEqual(restored, world)
        resumed = self.open(restored, resume=True)
        self.assertEqual(resumed.world.writer_epoch.value, 10)

    def test_sql_definition_pin_trigger_and_snapshot_order(self):
        world = self.make()
        world = self.runtime.instantiate(self.actor, world.world.world_id, world.timeline.scope.timeline_id,
            self.definition.reference, world.world.revision, self.now)
        reordered = replace(world, world=replace(world.world, revision=world.world.revision.next()),
                            characters=tuple(reversed(world.characters)))
        with self.repo.transaction() as tx:
            tx.save_world(reordered, world.world.revision)
        self.restart()
        self.assertEqual(self.runtime.snapshot(self.actor, world.world.world_id), reordered)
        with closing(sqlite3.connect(self.path)) as db:
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'DefinitionVersionConflict'):
                db.execute('UPDATE character_instances SET version=2')

    def test_switch_sql_rollback_survives_reopen(self):
        a, b = self.open(self.make()), self.make()
        self.runtime.repository = contract.FailingRepository(self.repo, fail_save=1)
        with self.assertRaises(RuntimeError):
            self.switch(a, b)
        peer = SQLiteWorldRepository(self.path, runtime_id=self.repo.runtime_id)
        with peer.transaction() as tx:
            self.assertEqual(tx.get_world(a.world.world_id), a)
            self.assertEqual(tx.get_world(b.world.world_id), b)

    def test_real_commit_failure_closes_and_rolls_back(self):
        created = self.make()
        original = sqlite3.connect
        class FailedCommit(sqlite3.Connection):
            def commit(self):
                raise sqlite3.OperationalError('测试提交故障')
        with patch('life_engine.world_sqlite_repository.sqlite3.connect',
                   side_effect=lambda *a, **k: original(*a, **k, factory=FailedCommit)):
            self.assert_code(Code.PERSISTENCE_FAILURE, lambda: self.open(created))
        with self.repo.transaction() as tx:
            self.assertEqual(tx.get_world(created.world.world_id), created)

    def test_malformed_data_fail_closed_without_repair(self):
        active = self.close(self.open(self.make()))
        mutations = [
            'DROP TABLE session_bindings',
            'ALTER TABLE worlds DROP COLUMN provenance',
            'DROP INDEX one_open_session_per_world',
            "DROP INDEX one_open_session_per_world; CREATE INDEX one_open_session_per_world ON session_bindings(status)",
            "UPDATE meta SET value='999' WHERE key='schema_version'",
            "UPDATE meta SET value='other-schema' WHERE key='world_schema'",
            "UPDATE character_instances SET state='invalid-json'",
            "PRAGMA ignore_check_constraints=ON; UPDATE worlds SET status='bad'",
            "UPDATE souls SET owner_id='world:00000000-0000-4000-8000-000000000001'",
            'DELETE FROM character_definitions',
            "UPDATE worlds SET soul_id='missing'",
        ]
        for i, sql in enumerate(mutations):
            with self.subTest(sql=sql):
                path = self.path.with_name(f'broken-{i}.db')
                with closing(sqlite3.connect(self.path)) as source, closing(sqlite3.connect(path)) as db:
                    source.backup(db)
                    db.executescript(sql)
                    db.commit()
                before = path.read_bytes()
                with self.assertRaises(WorldRuntimeError) as caught:
                    SQLiteWorldRepository(path)
                self.assertIn(caught.exception.code, (Code.SCHEMA_MISMATCH, Code.STORAGE_CORRUPT))
                self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
