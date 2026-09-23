"""使用已合并 Schema 3 原版 release 验证迁移副本和整安装激活。"""
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

from memory_fixture import ROOT
from life_engine import durable as d
from life_engine.config import defaults
from life_engine.world_schema import validate_schema,migrate_3_to_4

BASE = '4d628ca1b7b68609cd6fcf95e835c25ffa638c6b'


class Schema4MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = tempfile.TemporaryDirectory(prefix='Schema 3 原版 ')
        cls.package = Path(cls.old.name)
        archive = subprocess.run(['git','archive','--format=zip',BASE,'runtime'],cwd=ROOT,capture_output=True,check=True).stdout
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            z.extractall(cls.package)

    @classmethod
    def tearDownClass(cls):
        cls.old.cleanup()

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='Schema 4 迁移 ')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.root = self.base/'install'

    def old_run(self,code,*args):
        done = subprocess.run([sys.executable,'-c','import sys; sys.path.insert(0,sys.argv[1]); '+code,
            str(self.package/'runtime'),*map(str,args)],capture_output=True,text=True,encoding='utf-8',
            env={**os.environ,'PYTHONIOENCODING':'utf-8'},timeout=30)
        self.assertEqual(done.returncode,0,done.stderr)
        return done.stdout

    def install(self,name='a'):
        host = self.base/name
        host.mkdir()
        cfg = defaults('synthetic')
        cfg['integration'].update(adapter='hermes',host_home=str(host))
        config = self.base/(name+'.json')
        d.write(config,cfg)
        result = json.loads(self.old_run('from life_engine.durable import create_install,read; import json; '
            'print(json.dumps(create_install(sys.argv[2],sys.argv[3],read(sys.argv[4]))))',self.package,self.root,config))
        reg = d.registry(self.root,allow_schema2=True)
        inst = reg['instances'][result['instance']]
        data = d.state_home(self.root,inst)
        path = data/'agents/synthetic/life.db'
        self.old_run('from life_engine.store import Store; Store(sys.argv[2],"synthetic").remember(1,"原创","旧生活记忆","合成来源")',path)
        self.old_run('from life_engine.domain import *; from life_engine.world_runtime import WorldRuntime; '
            'from life_engine.world_sqlite_repository import SQLiteWorldRepository; from datetime import datetime,timezone; '
            'r=SQLiteWorldRepository(sys.argv[2]); w=WorldRuntime(r); '
            'p=Principal(DomainId.new(IdKind.PRINCIPAL),DomainId.new(IdKind.OWNER)); '
            's=Soul(DomainId.new(IdKind.SOUL),p.owner_id,DomainId.new(IdKind.WORLD)); '
            'w.register_soul(p,s); w.create_roleplay_world(p,s.soul_id,datetime.now(timezone.utc)); r.close()',path)
        return reg,inst,data

    def test_canonical3_rows_preserved_and_empty4_collection(self):
        reg,inst,data = self.install()
        oldpath = data/'agents/synthetic/life.db'
        with closing(sqlite3.connect(oldpath)) as db:
            validate_schema(db,3)
            before = {t:db.execute('SELECT * FROM '+t).fetchall() for t in ('days','contacts','observations','memories','loops','photos','souls','worlds','world_timelines','character_definitions','character_instances','session_bindings')}
        result = d.upgrade(self.root,ROOT)
        new = d.registry(self.root)
        self.assertEqual(new['data_schema'],5)
        self.assertNotEqual(new['instances'][inst['id']]['generation'],inst['generation'])
        with closing(sqlite3.connect(d.state_home(self.root,new['instances'][inst['id']])/'agents/synthetic/life.db')) as db:
            validate_schema(db,5)
            for table,rows in before.items():
                self.assertEqual(db.execute('SELECT * FROM '+table).fetchall(),rows)
            self.assertEqual(db.execute('SELECT count(*) FROM world_memories').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT revision FROM memory_collection_state').fetchall(),[(0,)])
            self.assertEqual(db.execute('SELECT revision FROM lore_binding_state').fetchall(),[(0,)])
            self.assertEqual(db.execute('SELECT count(*) FROM lore_books').fetchone()[0],0)
        d.db_check(oldpath,expected_schema=3)
        self.assertTrue(Path(result['backups'][0]).exists())
        saved = (self.root/'registry.json').read_bytes()
        d.upgrade(self.root,ROOT)
        self.assertEqual((self.root/'registry.json').read_bytes(),saved)

    def test_second_instance_failure_keeps_registry_and_old_release_usable(self):
        self.install('a')
        reg,inst,data = self.install('b')
        before = (self.root/'registry.json').read_bytes()
        original = d.migrate_generation
        calls = []
        def broken(*args):
            original(*args)
            calls.append(1)
            if len(calls)==2:
                raise RuntimeError('第二实例故障')
        with patch.object(d,'migrate_generation',side_effect=broken),self.assertRaises(RuntimeError):
            d.upgrade(self.root,ROOT)
        self.assertEqual((self.root/'registry.json').read_bytes(),before)
        for old in reg['instances'].values():
            d.db_check(d.state_home(self.root,old)/'agents/synthetic/life.db',expected_schema=3)
        self.old_run('from life_engine.store import Store; assert Store(sys.argv[2],"synthetic").path.exists()',data/'agents/synthetic/life.db')
        d.upgrade(self.root,ROOT)

    def test_extra_table_or_missing_trigger_schema3_rejected_unchanged(self):
        _,_,data = self.install()
        path = data/'agents/synthetic/life.db'
        with closing(sqlite3.connect(path)) as db,db:
            db.execute('CREATE TABLE unexpected_memory(value TEXT)')
        before = path.read_bytes()
        with closing(sqlite3.connect(path)) as db,self.assertRaises(ValueError):
            migrate_3_to_4(db)
        self.assertEqual(path.read_bytes(),before)

    def test_schema3_backup_cannot_restore_directly_into4(self):
        _,inst,_ = self.install()
        result = d.upgrade(self.root,ROOT)
        before = (self.root/'registry.json').read_bytes()
        with self.assertRaises(ValueError):
            d.restore(self.root,inst['id'],Path(result['backups'][0]))
        self.assertEqual((self.root/'registry.json').read_bytes(),before)

    def test_schema5_refuses_automatic_downgrade(self):
        old,inst,data = self.install()
        result = d.upgrade(self.root,ROOT)
        with self.assertRaises(ValueError):
            d.rollback_code(self.root,old['release'])
        with self.assertRaises(ValueError):
            d.rollback_schema(self.root,Path(result['schema_rollback']))
        self.assertEqual(d.registry(self.root)['data_schema'],5)
