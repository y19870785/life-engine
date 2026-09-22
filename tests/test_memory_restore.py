"""删除意图、恢复前重放和控制域不可用时的拒绝服务验收。"""
from unittest.mock import patch
import unittest
from memory_fixture import *
from life_engine.memory_repository import MemoryRuntimeError,MemoryFailure as MC


class MemoryRestoreTests(MemoryFixture,unittest.TestCase):
    def backup(self):
        with d.locked(self.root,'management'),d.locked(self.root,self.key):
            return d.snapshot(self.root,d.registry(self.root),self.inst)

    def attach_restored(self):
        reg = d.registry(self.root)
        self.inst = reg['instances'][self.key]
        self.data = d.state_home(self.root,self.inst)
        self.path = self.data/'agents/synthetic/life.db'
        self.world_repo = SQLiteWorldRepository(self.path)
        self.repo = SQLiteMemoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id)
        self.memory = MemoryRuntime(self.repo)

    def delete(self,r):
        return self.memory.delete_memory(self.owner,r.memory_id,r.revision,IdempotencyIdentity('delete','1'))

    def test_delete_and_restore_never_resurrect(self):
        record = self.create()
        backup = self.backup()
        result = self.delete(record)
        self.assertEqual(result.revision.value,2)
        self.assertEqual(self.memory.query(self.owner,history=True).records,())
        d.restore(self.root,self.key,backup)
        self.attach_restored()
        self.assertEqual(self.memory.query(self.owner,history=True).records,())
        self.assertEqual(self.memory.collection_revision(self.owner).value,2)
        self.repo.reconcile()
        self.assertEqual(self.memory.collection_revision(self.owner).value,2)

    def test_restore_before_creation_blocks_source_replay(self):
        backup = self.backup()
        record = self.create()
        self.delete(record)
        d.restore(self.root,self.key,backup)
        self.attach_restored()
        with self.assertRaises(MemoryRuntimeError):
            self.create()
        with self.assertRaises(MemoryRuntimeError):
            self.create('新键',provenance=self.provenance(canon=CanonStatus.ACCEPTED))
        self.assertEqual(self.memory.collection_revision(self.owner).value,0)

    def test_intent_crash_fails_closed_until_reconcile(self):
        record = self.create()
        with patch.object(self.repo,'_after_delete_intent',side_effect=RuntimeError('意图之后崩溃')),self.assertRaises(RuntimeError):
            self.delete(record)
        with self.assertRaises(MemoryRuntimeError) as caught:
            self.memory.query(self.session)
        self.assertEqual(caught.exception.code,MC.CONTROL_REQUIRED)
        self.repo.reconcile()
        self.assertEqual(self.memory.query(self.owner).records,())
        self.assertEqual(self.memory.collection_revision(self.owner).value,2)
        self.repo.reconcile()
        self.assertEqual(self.memory.collection_revision(self.owner).value,2)

    def test_missing_control_refuses_queries_and_restore_activation(self):
        self.create()
        backup = self.backup()
        before = (self.root/'registry.json').read_bytes()
        control = self.root/'control/memory-control.db'
        control.rename(control.with_suffix('.saved'))
        with self.assertRaises(MemoryRuntimeError):
            self.memory.query(self.owner)
        with self.assertRaises(MemoryRuntimeError):
            d.restore(self.root,self.key,backup)
        self.assertEqual((self.root/'registry.json').read_bytes(),before)

    def test_delete_preserves_no_content_in_control(self):
        record = self.create(content='绝不进入删除账本的合成秘密')
        self.delete(record)
        control = self.root/'control/memory-control.db'
        self.assertNotIn('绝不进入删除账本的合成秘密'.encode(),control.read_bytes())
        moved = control.with_suffix('.moved')
        control.rename(moved)
        moved.rename(control)

    def test_source_deletion_blocks_derived_summary(self):
        source = self.create(provenance=Provenance(SourceType.MODEL,'源',self.now,self.actor,RealityStatus.FICTIONAL,CanonStatus.ACCEPTED))
        summary = self.create('summary',kind=MemoryKind.SUMMARY,
            provenance=Provenance(SourceType.MODEL,'摘要',self.now,self.actor,RealityStatus.FICTIONAL,CanonStatus.ACCEPTED),lineage=(source.memory_id,))
        self.memory.delete_memory(self.owner,source.memory_id,summary.revision,IdempotencyIdentity('delete','1'))
        self.assertEqual(self.memory.query(self.owner,history=True).records,())

    def test_control_corruption_sequence_and_identity_fail_closed(self):
        import sqlite3
        from contextlib import closing
        r = self.create()
        self.delete(r)
        path = self.root/'control/memory-control.db'
        original = path.read_bytes()
        for sql in ("UPDATE intents SET sequence=2", "UPDATE identity SET install_id='wrong'",
                    "UPDATE intents SET blocked='{}'", "DELETE FROM intents"):
            with self.subTest(sql=sql):
                path.write_bytes(original)
                with closing(sqlite3.connect(path)) as db,db:
                    db.execute(sql)
                with self.assertRaises(ValueError):
                    self.memory.query(self.owner)
                self.assertFalse(d.health(self.root)['ok'])
        path.write_bytes(original)

    def test_delete_replay_and_tombstone_cannot_unhide(self):
        r = self.create()
        first = self.delete(r)
        self.assertEqual(self.delete(r),first)
        with self.assertRaises(ValueError):
            self.memory.unhide_memory(self.owner,r.memory_id,first.revision,IdempotencyIdentity('unhide','1'))
        self.assertEqual(self.memory.collection_revision(self.owner),first.revision)

    def test_backup_restores_audience_subject_history_and_receipts(self):
        r = self.create(subjects=(MemorySubject(SubjectKind.TEXT,text='原创主题'),))
        before = self.memory.get_memory(self.owner,r.memory_id)
        backup = self.backup()
        self.memory.hide_memory(self.owner,r.memory_id,r.revision,IdempotencyIdentity('hide','1'))
        d.restore(self.root,self.key,backup)
        self.attach_restored()
        self.assertEqual(self.memory.get_memory(self.owner,r.memory_id),before)
        self.assertEqual(self.memory.collection_revision(self.owner),r.revision)

    def test_control_anchor_gap_after_commit_refuses_service(self):
        r = self.create()
        original = d.write
        def broken(path,value):
            if path.name=='identity.json':
                raise OSError('锚写入故障')
            original(path,value)
        with patch.object(d,'write',side_effect=broken),self.assertRaises(ValueError):
            self.delete(r)
        with self.assertRaises(ValueError):
            self.memory.query(self.owner)
