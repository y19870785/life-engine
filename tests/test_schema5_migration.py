"""真实 Schema 4 副本迁移、结构冻结和 Schema 5 恢复门禁。"""
from contextlib import closing
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from memory_fixture import ROOT, d, MemoryFixture, SQLiteWorldRepository
from life_engine.config import defaults
from life_engine.world_schema import (expected_structure, validate_schema, migrate_copy,
                                      SCHEMA_SIGNATURES)
from life_engine.lore_repository import LoreRuntimeError
from life_engine.lore_sqlite_repository import validate_lore_data
from life_engine.world_repository import WorldRuntimeError, FailureCode
from life_engine.domain import DomainId, IdKind, Principal
from life_engine.memory import OwnerMemoryContext, IdempotencyIdentity
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.memory_repository import MemoryRuntimeError

BASE='0fe1a416b70a90914581d7698a30cc066b4c1ba1'


class Schema5MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=tempfile.TemporaryDirectory(prefix='Schema 4 原版 ')
        cls.package=Path(cls.old.name)
        archive=subprocess.run(['git','archive','--format=zip',BASE,'runtime'],cwd=ROOT,
            capture_output=True,check=True).stdout
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            z.extractall(cls.package)

    @classmethod
    def tearDownClass(cls):
        cls.old.cleanup()

    def setUp(self):
        folder=tempfile.TemporaryDirectory(prefix='Schema 5 迁移 ')
        self.addCleanup(folder.cleanup)
        self.base=Path(folder.name).resolve()
        self.root=self.base/'install'

    def old_run(self,code,*args):
        done=subprocess.run([sys.executable,'-c','import sys; sys.path.insert(0,sys.argv[1]); '+code,
            str(self.package/'runtime'),*map(str,args)],capture_output=True,text=True,encoding='utf-8',
            env={**os.environ,'PYTHONIOENCODING':'utf-8'},timeout=40)
        self.assertEqual(done.returncode,0,done.stderr)
        return done.stdout

    def install(self,name):
        host=self.base/name
        host.mkdir()
        cfg=defaults('synthetic')
        cfg['integration'].update(adapter='hermes',host_home=str(host))
        config=self.base/(name+'.json')
        d.write(config,cfg)
        result=json.loads(self.old_run('from life_engine.durable import create_install,read; import json; '
            'print(json.dumps(create_install(sys.argv[2],sys.argv[3],read(sys.argv[4]))))',
            self.package,self.root,config))
        reg=d.registry(self.root,allow_schema2=True)
        inst=reg['instances'][result['instance']]
        path=d.state_home(self.root,inst)/'agents/synthetic/life.db'
        self.old_run('from life_engine.store import Store; '
            'Store(sys.argv[2],"synthetic").remember(1,"原创","旧日常记忆","合成来源")',path)
        self.old_run('from life_engine.domain import *; from life_engine.world_runtime import WorldRuntime; '
            'from life_engine.world_sqlite_repository import SQLiteWorldRepository; '
            'from datetime import datetime,timezone; r=SQLiteWorldRepository(sys.argv[2]); w=WorldRuntime(r); '
            'p=Principal(DomainId.new(IdKind.PRINCIPAL),DomainId.new(IdKind.OWNER)); '
            's=Soul(DomainId.new(IdKind.SOUL),p.owner_id,DomainId.new(IdKind.WORLD)); '
            'w.register_soul(p,s); w.create_roleplay_world(p,s.soul_id,datetime.now(timezone.utc)); r.close()',path)
        return reg,inst,path

    def test_old_exact_schema_and_copy_migration(self):
        reg,inst,path=self.install('a')
        with closing(sqlite3.connect(path)) as db:
            validate_schema(db,4)
            before={table:db.execute('SELECT * FROM '+table).fetchall() for table in
                ('meta','memories','worlds','world_timelines','world_memories','memory_collection_state')}
            old_structure=expected_structure(4)
        result=d.upgrade(self.root,ROOT)
        current=d.registry(self.root)
        self.assertEqual(current['data_schema'],6)
        self.assertEqual(expected_structure(4),old_structure)
        self.assertNotEqual(current['instances'][inst['id']]['generation'],inst['generation'])
        self.assertTrue(path.exists())
        newpath=d.state_home(self.root,current['instances'][inst['id']])/'agents/synthetic/life.db'
        with closing(sqlite3.connect(newpath)) as db:
            validate_schema(db,6)
            for table,rows in before.items():
                if table=='meta':
                    continue
                self.assertEqual(db.execute('SELECT * FROM '+table).fetchall(),rows)
            self.assertEqual(db.execute('SELECT revision FROM lore_binding_state').fetchall(),[(0,)])
            self.assertEqual(db.execute('SELECT count(*) FROM lore_books').fetchone()[0],0)
        self.assertTrue(Path(result['backups'][0]).exists())
        self.assertEqual(d.verify_backup(result['backups'][0],inst,expected_schema=4)['data_schema'],4)
        frozen=(self.root/'registry.json').read_bytes()
        d.upgrade(self.root,ROOT)
        self.assertEqual((self.root/'registry.json').read_bytes(),frozen)

    def test_two_instances_failure_keeps_schema4_active(self):
        self.install('a')
        self.install('b')
        before=(self.root/'registry.json').read_bytes()
        original=d.migrate_generation
        calls=[]
        def broken(*args):
            result=original(*args)
            calls.append(1)
            if len(calls)==2:
                raise RuntimeError('第二实例模拟失败')
            return result
        with patch.object(d,'migrate_generation',side_effect=broken),self.assertRaises(RuntimeError):
            d.upgrade(self.root,ROOT)
        self.assertEqual((self.root/'registry.json').read_bytes(),before)
        reg=d.registry(self.root,allow_schema2=True)
        for inst in reg['instances'].values():
            d.db_check(d.state_home(self.root,inst)/'agents/synthetic/life.db',expected_schema=4)

    def test_false_schema5_and_damaged_lore_rejected(self):
        _,inst,path=self.install('a')
        with closing(sqlite3.connect(path)) as db:
            db.execute("UPDATE meta SET value='5' WHERE key='schema_version'")
            db.execute("UPDATE meta SET value=? WHERE key='world_schema'",(SCHEMA_SIGNATURES[5],))
            with self.assertRaises(ValueError):
                validate_schema(db,5)
            db.rollback()
        d.upgrade(self.root,ROOT)
        current=d.registry(self.root)
        newpath=d.state_home(self.root,current['instances'][inst['id']])/'agents/synthetic/life.db'
        with closing(sqlite3.connect(newpath)) as db:
            db.execute('DELETE FROM lore_binding_state')
            db.commit()
            with self.assertRaises(LoreRuntimeError):
                validate_lore_data(db)

    def test_schema4_memory_control_survives_upgrade_and_schema5_restore(self):
        reg,inst,path=self.install('a')
        script='''from life_engine.domain import *
from life_engine.memory import *
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.world_sqlite_repository import SQLiteWorldRepository
from datetime import datetime,timezone
import sqlite3,json
path,root,key=sys.argv[2:5]
with sqlite3.connect(path) as db:
    wid=db.execute("SELECT world_id FROM worlds ORDER BY world_id LIMIT 1").fetchone()[0]
w=SQLiteWorldRepository(path)
with w.transaction() as tx:
    snapshot=tx.get_world(DomainId.parse(wid))
actor=Principal(DomainId.new(IdKind.PRINCIPAL),snapshot.world.owner_id)
repo=SQLiteMemoryRepository(root,key,runtime_id=w.runtime_id)
runtime=MemoryRuntime(repo)
scope=snapshot.timeline.scope
ctx=OwnerMemoryContext(actor,scope)
provenance=Provenance(SourceType.USER_REPORT,"原创来源",datetime.now(timezone.utc),actor,
    RealityStatus.USER_CLAIMED,CanonStatus.ACCEPTED)
receipt=runtime.create_owner_memory(ctx,MemoryCollectionRevision(),IdempotencyIdentity("pre-upgrade","create"),
    content="升级前的原创记忆",kind=MemoryKind.EPISODIC,provenance=provenance,
    audience=(MemoryAudience(AudienceKind.WORLD),))
survivor=runtime.create_owner_memory(ctx,receipt.revision,IdempotencyIdentity("pre-upgrade","survivor"),
    content="升级后仍在的原创记忆",kind=MemoryKind.EPISODIC,provenance=provenance,
    audience=(MemoryAudience(AudienceKind.WORLD),))
print(json.dumps({"principal":str(actor.principal_id),"world":wid,
    "memory":str(receipt.memory_id),"survivor":str(survivor.memory_id)}))
repo.close(); w.close()'''
        info=json.loads(self.old_run(script,path,self.root,inst['id']))
        with d.locked(self.root,'management'),d.locked(self.root,inst['id']):
            old_backup=d.snapshot(self.root,d.registry(self.root,allow_schema2=True),inst)
        deletion='''from life_engine.domain import *
from life_engine.memory import *
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.world_sqlite_repository import SQLiteWorldRepository
path,root,key,principal,world_id,memory_id=sys.argv[2:8]
w=SQLiteWorldRepository(path)
with w.transaction() as tx:
    scope=tx.get_world(DomainId.parse(world_id)).timeline.scope
actor=Principal(DomainId.parse(principal),scope.owner_id)
repo=SQLiteMemoryRepository(root,key,runtime_id=w.runtime_id)
runtime=MemoryRuntime(repo)
ctx=OwnerMemoryContext(actor,scope)
runtime.delete_memory(ctx,DomainId.parse(memory_id),runtime.collection_revision(ctx),
    IdempotencyIdentity("pre-upgrade","delete"))
repo.close(); w.close()'''
        self.old_run(deletion,path,self.root,inst['id'],info['principal'],info['world'],info['memory'])
        d.upgrade(self.root,ROOT)
        current=d.registry(self.root)
        current_inst=current['instances'][inst['id']]
        newpath=d.state_home(self.root,current_inst)/'agents/synthetic/life.db'
        world_repo=SQLiteWorldRepository(newpath)
        mem_repo=SQLiteMemoryRepository(self.root,inst['id'],runtime_id=world_repo.runtime_id)
        memory=MemoryRuntime(mem_repo)
        with world_repo.transaction() as tx:
            scope=tx.get_world(DomainId.parse(info['world'])).timeline.scope
        actor=Principal(DomainId.parse(info['principal']),scope.owner_id)
        owner=OwnerMemoryContext(actor,scope)
        with self.assertRaises(MemoryRuntimeError):
            memory.get_memory(owner,DomainId.parse(info['memory']))
        with self.assertRaises(ValueError):
            d.restore(self.root,inst['id'],old_backup)
        record=memory.get_memory(owner,DomainId.parse(info['survivor']))
        with d.locked(self.root,'management'),d.locked(self.root,inst['id']):
            backup=d.snapshot(self.root,current,current_inst)
        memory.delete_memory(owner,record.memory_id,memory.collection_revision(owner),
            IdempotencyIdentity('post-upgrade','delete'))
        self.assertEqual(memory.query(owner,history=True).records,())
        d.restore(self.root,inst['id'],backup)
        restored=d.registry(self.root)['instances'][inst['id']]
        restored_path=d.state_home(self.root,restored)/'agents/synthetic/life.db'
        fresh_world=SQLiteWorldRepository(restored_path)
        fresh_repo=SQLiteMemoryRepository(self.root,inst['id'],runtime_id=fresh_world.runtime_id)
        fresh_memory=MemoryRuntime(fresh_repo)
        self.assertEqual(fresh_memory.query(owner,history=True).records,())
        fresh_repo.close(); fresh_world.close(); mem_repo.close(); world_repo.close()

    def test_missing_lore_index_and_bad_foreign_key_rejected(self):
        _,inst,_=self.install('a')
        d.upgrade(self.root,ROOT)
        current=d.registry(self.root)
        path=d.state_home(self.root,current['instances'][inst['id']])/'agents/synthetic/life.db'
        with closing(sqlite3.connect(path)) as db:
            db.execute('DROP INDEX lore_books_owner')
            db.commit()
            with self.assertRaises(ValueError):
                validate_schema(db,6)
            db.execute('CREATE INDEX lore_books_owner ON lore_books(owner_id,book_id)')
            owner,soul=db.execute('SELECT owner_id,soul_id FROM worlds LIMIT 1').fetchone()
            db.execute('INSERT INTO lore_binding_state VALUES(?,?,?,?,0)',
                (owner,soul,str(DomainId.new(IdKind.WORLD)),str(DomainId.new(IdKind.TIMELINE))))
            db.commit()
            with self.assertRaises(ValueError):
                validate_schema(db,6)

    def test_unknown_schema_copy_fails_closed(self):
        with closing(sqlite3.connect(':memory:')) as db:
            with self.assertRaises(WorldRuntimeError) as caught:
                migrate_copy(db)
            self.assertEqual(caught.exception.code,FailureCode.SCHEMA_MISMATCH)


if __name__=='__main__':
    unittest.main()
