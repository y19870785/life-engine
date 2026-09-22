"""独立连接 CAS、幂等、回滚、读取候选范围和数据损坏验收。"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from threading import Barrier
from unittest.mock import patch
import sqlite3
import unittest
from memory_fixture import *
from life_engine.memory_repository import MemoryRuntimeError,MemoryFailure as MC
from life_engine.memory_sqlite_repository import MemoryTransaction


class MemorySQLiteTests(MemoryFixture,unittest.TestCase):
    def test_two_independent_repositories_cas(self):
        peer = MemoryRuntime(SQLiteMemoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id))
        barrier = Barrier(2)
        def write(index):
            barrier.wait(timeout=10)
            try:
                return (self.memory if index==0 else peer).create_owner_memory(self.owner,MemoryCollectionRevision(),
                    IdempotencyIdentity(str(index),'create'),content='竞争写入',kind=MemoryKind.EPISODIC,
                    provenance=self.provenance(str(index)),audience=(self.session.viewer,))
            except MemoryRuntimeError as exc:
                return exc.code
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(write,range(2)))
        self.assertEqual(results.count(MC.REVISION_CONFLICT),1)
        self.assertEqual(self.memory.collection_revision(self.owner),MemoryCollectionRevision(1))

    def test_idempotency_fingerprint_ignores_expected_revision(self):
        first = self.create()
        second = self.create()
        self.assertEqual(first,second)
        with self.assertRaises(MemoryRuntimeError) as caught:
            self.create(content='不同正文')
        self.assertEqual(caught.exception.code,MC.IDEMPOTENCY_CONFLICT)
        third = self.create('另一个来源')
        self.assertNotEqual(first.memory_id,third.memory_id)
        self.assertEqual(third.revision.value,2)

    def test_rollback_after_insert_and_connection_release(self):
        original = MemoryTransaction.audit
        def broken(*args):
            original(*args)
            raise RuntimeError('提交前故障')
        with patch.object(MemoryTransaction,'audit',new=broken),self.assertRaises(RuntimeError):
            self.create()
        self.assertEqual(self.memory.collection_revision(self.owner).value,0)
        self.assertEqual(self.memory.query(self.owner).records,())
        self.create()
        renamed = self.path.with_suffix('.renamed')
        self.path.rename(renamed)
        renamed.rename(self.path)

    def test_attach_never_recovers_world(self):
        before = self.world.snapshot(self.actor,self.a.world.world_id)
        peer = SQLiteMemoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id)
        self.assertEqual(self.world.snapshot(self.actor,self.a.world.world_id),before)
        peer.close()
        with self.assertRaises(ValueError):
            MemoryRuntime(peer).query(self.owner)

    def test_scope_and_audience_in_sql_before_candidates(self):
        self.create()
        self.create('secret',audience=(MemoryAudience(AudienceKind.USER,self.actor.owner_id),))
        seen = []
        from life_engine import memory_runtime as mr
        from life_engine import memory_sqlite_repository as sr
        original = sr.load_record
        def capture(db,row):
            seen.append(row['memory_id'])
            return original(db,row)
        with patch.object(sr,'load_record',side_effect=capture):
            result = self.memory.query(self.session,limit=1)
        self.assertEqual(seen,[str(result.records[0].memory_id)])

    def test_corrupt_persistent_data_is_not_repaired(self):
        r = self.create()
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('DROP TRIGGER memory_immutable')
            from life_engine.memory_schema import MEMORY_DDL
            db.execute("UPDATE world_memories SET provenance='{}' WHERE memory_id=?",(str(r.memory_id),))
            db.execute(MEMORY_DDL[-1])
        with self.assertRaises(ValueError):
            d.db_check(self.path)
        with self.assertRaises(ValueError):
            SQLiteMemoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id)

    def test_scope_revision_independent(self):
        b = self.make_world()
        self.create()
        self.assertEqual(self.memory.collection_revision(OwnerMemoryContext(self.actor,b.timeline.scope)).value,0)

    def test_restart_preserves_content_revision_and_replay(self):
        first = self.create()
        self.repo.close()
        self.world_repo.close()
        self.world_repo = SQLiteWorldRepository(self.path)
        new = MemoryRuntime(SQLiteMemoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id))
        self.assertEqual(new.get_memory(self.owner,first.memory_id).content,'原创记忆正文')
        self.assertEqual(new.collection_revision(self.owner),first.revision)
        replay = new.create_owner_memory(self.owner,MemoryCollectionRevision(),IdempotencyIdentity('原创来源','create'),
            content='原创记忆正文',kind=MemoryKind.EPISODIC,provenance=self.provenance(canon=CanonStatus.ACCEPTED),audience=(self.session.viewer,))
        self.assertEqual(first,replay)

    def test_malformed_rows_and_foreign_references(self):
        r = self.create()
        original = self.path.read_bytes()
        cases = (
            "UPDATE memory_audiences SET target='character_definition:00000000-0000-4000-8000-000000000000'",
            "UPDATE memory_audiences SET kind='soul',target='soul:00000000-0000-4000-8000-000000000000'",
            "DELETE FROM memory_audiences",
            "UPDATE memory_collection_state SET revision=-1",
            "UPDATE world_memories SET content_version=3",
            "UPDATE world_memories SET lifecycle='invalid'",
            "UPDATE memory_operations SET actor='bad'",
            "UPDATE memory_idempotency SET operation=999",
        )
        from life_engine.memory_schema import MEMORY_DDL
        for sql in cases:
            with self.subTest(sql=sql):
                self.path.write_bytes(original)
                with closing(sqlite3.connect(self.path)) as db,db:
                    db.execute('PRAGMA ignore_check_constraints=ON')
                    db.execute('DROP TRIGGER memory_immutable')
                    db.execute(sql)
                    db.execute(MEMORY_DDL[-1])
                before = self.path.read_bytes()
                with self.assertRaises(ValueError):
                    d.db_check(self.path)
                self.assertEqual(self.path.read_bytes(),before)
        self.path.write_bytes(original)

    def test_storage_busy_not_revision_conflict(self):
        from life_engine.world_repository import WorldRuntimeError,FailureCode
        self.repo.timeout = 0.05
        with closing(sqlite3.connect(self.path,isolation_level=None)) as db:
            db.execute('BEGIN IMMEDIATE')
            with self.assertRaises(WorldRuntimeError) as caught:
                self.memory.query(self.owner)
            self.assertEqual(caught.exception.code,FailureCode.STORAGE_BUSY)
            db.rollback()
