"""从固定 canonical Schema 7 真实发行包迁移；禁止改活动库。"""
from contextlib import closing
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from memory_fixture import ROOT,d
from life_engine.config import defaults
from life_engine.world_schema import validate_schema


class Schema8MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=tempfile.TemporaryDirectory(prefix='Schema7 canonical ')
        cls.package=Path(cls.old.name)
        archive=subprocess.run(['git','archive','--format=zip','9159c493ad435cf947ed8c0fef278e1f5fb9dc83','runtime'],cwd=ROOT,capture_output=True,check=True).stdout
        with zipfile.ZipFile(io.BytesIO(archive)) as z:z.extractall(cls.package)

    @classmethod
    def tearDownClass(cls):cls.old.cleanup()

    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='Living copy ');self.addCleanup(temp.cleanup)
        self.base=Path(temp.name).resolve();self.root=self.base/'install'

    def old_run(self,code,*args,success=True):
        done=subprocess.run([sys.executable,'-X','utf8','-c','import sys;sys.path.insert(0,sys.argv[1]);'+code,
            str(self.package/'runtime'),*map(str,args)],capture_output=True,text=True,encoding='utf-8',timeout=60)
        if success:self.assertEqual(done.returncode,0,done.stderr)
        else:self.assertNotEqual(done.returncode,0)
        return done.stdout

    def install(self,name):
        host=self.base/name;host.mkdir();cfg=defaults(name);cfg['integration'].update(adapter='hermes',host_home=str(host))
        path=self.base/(name+'.json');d.write(path,cfg)
        out=json.loads(self.old_run('import json;from life_engine.durable import create_install,read;print(json.dumps(create_install(sys.argv[2],sys.argv[3],read(sys.argv[4]))))',self.package,self.root,path))
        key=out['instance'];reg=d.registry(self.root,allow_schema2=True);inst=reg['instances'][key]
        dbpath=d.state_home(self.root,inst)/'agents'/name/'life.db'
        self.old_run('from life_engine.store import Store;s=Store(sys.argv[2],sys.argv[3]);s.loop_add(1,"迁移跟进",2);s.remember(1,"fact","旧记忆","用户");s.observe(1,"旧入站","old");s.pause(True)',dbpath,name)
        return key,inst,dbpath

    def test_p13_copy_all_rows_and_empty_enrollment(self):
        key,inst,path=self.install('a');before_bytes=path.read_bytes()
        with closing(sqlite3.connect(path)) as db:
            names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name!='meta'")]
            before={n:db.execute('SELECT * FROM '+n+' ORDER BY rowid').fetchall() for n in names}
        result=d.upgrade(self.root,ROOT);reg=d.registry(self.root)
        self.assertEqual(reg['data_schema'],8);self.assertEqual(path.read_bytes(),before_bytes)
        newpath=d.state_home(self.root,reg['instances'][key])/'agents/a/life.db'
        with closing(sqlite3.connect(newpath)) as db:
            validate_schema(db,8)
            for name,rows in before.items():self.assertEqual(rows,db.execute('SELECT * FROM '+name+' ORDER BY rowid').fetchall(),name)
            self.assertEqual(db.execute('SELECT count(*) FROM living_roots').fetchone()[0],0)
        self.assertEqual(d.verify_backup(result['backups'][0],inst,expected_schema=7)['data_schema'],7)
        self.assertTrue(d.health(self.root)['ok'])

    def test_p13_second_instance_failure_keeps_registry(self):
        self.install('a');self.install('b');before=(self.root/'registry.json').read_bytes()
        original=d.migrate_generation;calls=[]
        def failure(*args):
            calls.append(1)
            original(*args)
            if len(calls)==2:raise ValueError('合成第二实例校验失败')
        with patch.object(d,'migrate_generation',side_effect=failure):
            with self.assertRaisesRegex(ValueError,'合成'):d.upgrade(self.root,ROOT)
        self.assertEqual(before,(self.root/'registry.json').read_bytes())

    def test_p15_verified_backup_old_release_rollback(self):
        key,inst,path=self.install('a');result=d.upgrade(self.root,ROOT);new=d.registry(self.root)
        newpath=d.state_home(self.root,new['instances'][key])/'agents/a/life.db'
        self.old_run('from life_engine.store import Store;Store(sys.argv[2],"a")',newpath,success=False)
        rollback=d.rollback_schema(self.root,result['schema_rollback'])
        self.assertEqual(rollback['data_schema'],7);self.assertTrue(rollback['proactive_paused'])
        restored=d.registry(self.root,allow_schema2=True)
        self.assertNotEqual(restored['instances'][key]['generation'],inst['generation'])
        target=d.state_home(self.root,restored['instances'][key])/'agents/a/life.db'
        with closing(sqlite3.connect(target)) as db:
            validate_schema(db,7);self.assertEqual(db.execute("SELECT value FROM meta WHERE key='paused'").fetchone()[0],'true')
        self.assertTrue(newpath.is_file())
