"""真实 Schema 5 安装的副本升级、Story 空初始化及失败原子性。"""
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

from memory_fixture import ROOT, d
from life_engine.config import defaults
from life_engine.domain import DomainId, Principal
from life_engine.memory import OwnerMemoryContext
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.world_sqlite_repository import SQLiteWorldRepository
from life_engine.story_sqlite_repository import validate_story_data
from life_engine.world_schema import expected_structure, validate_schema

BASE = '10b75a6f8fe6fd94b98e82a6e903cdcfcb8c6d1e'


class Schema6MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = tempfile.TemporaryDirectory(prefix='Schema 5 原版 ')
        cls.package = Path(cls.old.name)
        archived = subprocess.run(['git','archive','--format=zip',BASE,'runtime'],cwd=ROOT,
            capture_output=True,check=True).stdout
        with zipfile.ZipFile(io.BytesIO(archived)) as package:
            package.extractall(cls.package)

    @classmethod
    def tearDownClass(cls):
        cls.old.cleanup()

    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='Schema 6 迁移 ')
        self.addCleanup(folder.cleanup)
        self.base = Path(folder.name).resolve()
        self.root = self.base/'install'

    def old_run(self, code, *args):
        done = subprocess.run([sys.executable,'-c',
            'import sys; sys.path.insert(0,sys.argv[1]); '+code,
            str(self.package/'runtime'),*map(str,args)],capture_output=True,text=True,
            encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'},timeout=60)
        self.assertEqual(done.returncode,0,done.stderr)
        return done.stdout

    def install(self, name):
        host = self.base/name
        host.mkdir()
        cfg = defaults('synthetic')
        cfg['integration'].update(adapter='hermes',host_home=str(host))
        path = self.base/(name+'.json')
        d.write(path,cfg)
        installed = json.loads(self.old_run('from life_engine.durable import create_install,read; '
            'import json; print(json.dumps(create_install(sys.argv[2],sys.argv[3],read(sys.argv[4]))))',
            self.package,self.root,path))
        reg = d.registry(self.root,allow_schema2=True)
        inst = reg['instances'][installed['instance']]
        db_path = d.state_home(self.root,inst)/'agents/synthetic/life.db'
        return inst,db_path

    def test_real_schema5_copy_preserves_data_and_starts_empty_story(self):
        inst,path = self.install('a')
        script = '''from life_engine.domain import *
from life_engine.world_runtime import WorldRuntime
from life_engine.world_sqlite_repository import SQLiteWorldRepository
from life_engine.memory import *
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.lore import *
from life_engine.lore_runtime import LoreRuntime
from life_engine.lore_sqlite_repository import SQLiteLoreRepository
from life_engine.import_ir import JsonValue,LoreIR
from datetime import datetime,timezone
from hashlib import sha256
import json
from life_engine.store import Store
path,root,key=sys.argv[2:5]
Store(path,'synthetic').remember(1,'原创','旧日常记录','合成来源')
now=datetime(2026,9,24,tzinfo=timezone.utc)
actor=Principal(DomainId.new(IdKind.PRINCIPAL),DomainId.new(IdKind.OWNER))
repo=SQLiteWorldRepository(path); world=WorldRuntime(repo)
soul=Soul(DomainId.new(IdKind.SOUL),actor.owner_id,DomainId.new(IdKind.WORLD))
world.register_soul(actor,soul)
definition=CharacterDefinition(DefinitionRef(DomainId.new(IdKind.DEFINITION),DefinitionVersion(1)),actor.owner_id,'原创角色',Values(),Provenance(SourceType.IMPORT,'原创卡',now,actor,RealityStatus.UNKNOWN,CanonStatus.UNREVIEWED))
world.register_definition(actor,definition)
w=world.create_roleplay_world(actor,soul.soul_id,now)
w=world.instantiate(actor,w.world.world_id,w.timeline.scope.timeline_id,definition.reference,w.world.revision,now)
w=world.enter(actor,w.world.world_id,w.timeline.scope.timeline_id,w.characters[0].character_instance_id,w.world.revision,w.world.writer_epoch)
w=world.exit(actor,w.world.world_id,w.timeline.scope.timeline_id,w.sessions[-1].session_id,w.world.revision,w.world.writer_epoch)
w=world.resume(actor,w.world.world_id,w.timeline.scope.timeline_id,w.characters[0].character_instance_id,w.world.revision,w.world.writer_epoch)
scope=w.timeline.scope
memory_repo=SQLiteMemoryRepository(root,key,runtime_id=repo.runtime_id)
memory=MemoryRuntime(memory_repo)
ctx=OwnerMemoryContext(actor,scope)
provenance=Provenance(SourceType.USER_REPORT,'原创记录',now,actor,RealityStatus.USER_CLAIMED,CanonStatus.ACCEPTED)
receipt=memory.create_owner_memory(ctx,MemoryCollectionRevision(),IdempotencyIdentity('migration','memory'),content='保留记忆',kind=MemoryKind.EPISODIC,provenance=provenance,audience=(MemoryAudience(AudienceKind.WORLD),))
memory.delete_memory(ctx,receipt.memory_id,receipt.revision,IdempotencyIdentity('migration','delete'))
lore_repo=SQLiteLoreRepository(root,key,runtime_id=repo.runtime_id)
lore=LoreRuntime(lore_repo)
ir=LoreIR(JsonValue.of({'name':'原创世界书'}),(JsonValue.of({'triggers':['钟楼'],'text':'旧版设定','enabled':True,'settings':{}}),),sha256(b'original-lore').hexdigest())
book=lore.register_book(OwnerLoreContext(actor),'原创世界书',ir,LoreRegistrationIdentity('migration','book'))
lore.bind(OwnerLoreContext(actor,scope),book.book_id,book.book_version,0,LoreBindingRevision(),LoreRegistrationIdentity('migration','bind'))
print(json.dumps({'book':str(book.book_id),'memory':str(receipt.memory_id),
    'principal':str(actor.principal_id),'world':str(w.world.world_id)}))
lore_repo.close();memory_repo.close();repo.close()'''
        info = json.loads(self.old_run(script,path,self.root,inst['id']))
        with closing(sqlite3.connect(path)) as db:
            validate_schema(db,5)
            before = {table:db.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall()
                for table in ('memories','worlds','world_timelines','character_instances',
                    'session_bindings','world_memories','lore_books','lore_book_versions',
                    'lore_world_bindings','lore_binding_state')}
            self.assertEqual(db.execute('SELECT book_version FROM lore_world_bindings').fetchone()[0],1)
        old_structure = expected_structure(5)
        result = d.upgrade(self.root,ROOT)
        self.assertEqual(expected_structure(5),old_structure)
        reg = d.registry(self.root)
        self.assertEqual(reg['data_schema'],6)
        self.assertNotEqual(reg['instances'][inst['id']]['generation'],inst['generation'])
        self.assertTrue(path.exists())
        newpath = d.state_home(self.root,reg['instances'][inst['id']])/'agents/synthetic/life.db'
        with closing(sqlite3.connect(newpath)) as db:
            validate_schema(db,6)
            validate_story_data(db)
            for table,rows in before.items():
                self.assertEqual(db.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall(),rows,table)
            self.assertEqual(db.execute('SELECT revision,logical_tick,last_event_sequence '
                'FROM story_collection_state').fetchall(),[(0,0,0)])
            self.assertEqual(db.execute('SELECT count(*) FROM story_events').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT book_id,book_version FROM lore_world_bindings').fetchone(),(info['book'],1))
        world_repo = SQLiteWorldRepository(newpath)
        memory_repo = SQLiteMemoryRepository(self.root,inst['id'],runtime_id=world_repo.runtime_id)
        with world_repo.transaction() as tx:
            scope = tx.get_world(DomainId.parse(info['world'])).timeline.scope
        owner = OwnerMemoryContext(Principal(DomainId.parse(info['principal']),scope.owner_id),scope)
        self.assertEqual(MemoryRuntime(memory_repo).query(owner,history=True).records,())
        memory_repo.close();world_repo.close()
        self.assertEqual(d.verify_backup(result['backups'][0],inst,expected_schema=5)['data_schema'],5)
        frozen = (self.root/'registry.json').read_bytes()
        d.upgrade(self.root,ROOT)
        self.assertEqual((self.root/'registry.json').read_bytes(),frozen)

    def test_second_instance_failure_preserves_old_active_install(self):
        self.install('a')
        self.install('b')
        before = (self.root/'registry.json').read_bytes()
        original = d.migrate_generation
        calls = []
        def broken(*args):
            result = original(*args)
            calls.append(result)
            if len(calls) == 2:
                raise RuntimeError('第二实例模拟迁移失败')
            return result
        with patch.object(d,'migrate_generation',side_effect=broken),self.assertRaises(RuntimeError):
            d.upgrade(self.root,ROOT)
        self.assertEqual((self.root/'registry.json').read_bytes(),before)
        reg = d.registry(self.root,allow_schema2=True)
        self.assertEqual(reg['data_schema'],5)
        for inst in reg['instances'].values():
            path = d.state_home(self.root,inst)/'agents/synthetic/life.db'
            d.db_check(path,expected_schema=5)

    def test_schema5_fake_six_and_structural_damage_rejected(self):
        inst,path = self.install('a')
        with closing(sqlite3.connect(path)) as db:
            db.execute("UPDATE meta SET value='6' WHERE key='schema_version'")
            db.execute("UPDATE meta SET value='SP-004C-story-runtime-v1' WHERE key='world_schema'")
            with self.assertRaises(ValueError):
                validate_schema(db,6)
            db.rollback()
        d.upgrade(self.root,ROOT)
        reg = d.registry(self.root)
        newpath = d.state_home(self.root,reg['instances'][inst['id']])/'agents/synthetic/life.db'
        with closing(sqlite3.connect(newpath)) as db:
            db.execute("INSERT INTO story_collection_state VALUES(?,?,?,?,?,?,?,?,?)",
                ('bad-owner','bad-soul','bad-world','bad-timeline',0,0,0,
                 'SP-004C-story-projection-v1',
                 '{"character_states":[],"relationships":[],"threads":[],"world_facts":[]}'))
            db.commit()
            with self.assertRaises(Exception):
                validate_story_data(db)


if __name__ == '__main__':
    unittest.main()
