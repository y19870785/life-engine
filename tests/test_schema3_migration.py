"""从授权基线原版运行时创建 Schema 2 安装，验证整安装升级与回退。"""
from contextlib import closing
from dataclasses import replace
from datetime import datetime, timezone
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine import durable as d
from life_engine.config import defaults
from life_engine.domain import DomainId, IdKind, Principal, Soul
from life_engine.import_cards import parse_bytes
from life_engine.import_ir import project_definition
from life_engine.store import Store, SCHEMA
from life_engine.world_repository import FailureCode as Code, WorldRuntimeError
from life_engine.world_runtime import WorldRuntime
from life_engine.world_schema import migrate_copy
from life_engine.world_sqlite_repository import SQLiteWorldRepository

ROOT = Path(__file__).resolve().parents[1]
BASE = '399b084a8a5dfd76eb2aa3d0aac9ebbaafd35260'


class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_temp = tempfile.TemporaryDirectory(prefix='原版 Schema 2 ')
        cls.old_package = Path(cls.old_temp.name)
        archive = subprocess.run(['git', 'archive', '--format=zip', BASE, 'runtime'], cwd=ROOT,
                                 capture_output=True, check=True, timeout=30).stdout
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            zipped.extractall(cls.old_package)

    @classmethod
    def tearDownClass(cls):
        cls.old_temp.cleanup()

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='Schema 迁移验收 ')
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name).resolve()
        self.root = self.base / 'installation'

    def old_run(self, code, *args):
        result = subprocess.run([sys.executable, '-c',
            'import sys; sys.path.insert(0,sys.argv[1]); ' + code, str(self.old_package / 'runtime'), *map(str, args)],
            capture_output=True, text=True, encoding='utf-8', timeout=30,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result.stdout

    def install_old(self, name='a'):
        host = self.base / name
        host.mkdir()
        cfg = defaults('synthetic')
        cfg['integration'].update(adapter='hermes', host_home=str(host))
        cfg['social']['recent_chat_minutes'] = 222
        path = self.base / (name + '.json')
        d.write(path, cfg)
        result = json.loads(self.old_run(
            'from life_engine.durable import create_install,read; import json; '
            'print(json.dumps(create_install(sys.argv[2],sys.argv[3],read(sys.argv[4]))))',
            self.old_package, self.root, path))
        reg = d.registry(self.root, allow_schema2=True)
        inst = reg['instances'][result['instance']]
        data = d.state_home(self.root, inst)
        dbpath = data / 'agents/synthetic/life.db'
        photo = data / 'agents/synthetic/photos/original.png'
        photo.parent.mkdir()
        photo.write_bytes(b'synthetic-image-asset')
        with closing(sqlite3.connect(dbpath)) as db, db:
            db.execute("INSERT INTO days VALUES('2026-09-20',?)", (json.dumps(
                {'day': '2026-09-20', 'slots': [], 'visual': {}, 'routine': []}),))
            db.execute("INSERT INTO contacts(id,day,slot,at,status,payload) VALUES('c','2026-09-20','am',1,'delivered','{}')")
            db.execute("INSERT INTO observations(at,summary,dedupe) VALUES(1,'合成观察','observation-1')")
            db.execute("INSERT INTO memories(at,kind,summary,provenance) VALUES(1,'test','合成记忆','test')")
            db.execute("INSERT INTO loops(at,topic) VALUES(1,'合成话题')")
            db.execute("INSERT INTO photos(id,contact_id,day,at,status,path) VALUES('p','c','2026-09-20',1,'ready',?)", (str(photo),))
        return reg, inst, data

    def rows(self, data):
        with closing(sqlite3.connect(data / 'agents/synthetic/life.db')) as db:
            return {table: db.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall()
                    for table in ('days', 'contacts', 'observations', 'memories', 'loops', 'photos', 'meta')}

    def assert_old_works(self, inst, data):
        d.db_check(data / 'agents/synthetic/life.db', 'synthetic', expected_schema=2)
        result = subprocess.run([sys.executable, str(self.root / 'life.py'), '--instance', inst['id'], 'status'],
                                capture_output=True, text=True, encoding='utf-8', timeout=30,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn('合成记忆', result.stdout)

    def test_real_old_install_upgrade_preserves_data_assets_and_bindings(self):
        reg, inst, data = self.install_old()
        before = self.rows(data)
        settings = (data / 'agents/synthetic/agent.json').read_bytes()
        result = d.upgrade(self.root, ROOT)
        active = d.registry(self.root)
        new_inst = active['instances'][inst['id']]
        new_data = d.state_home(self.root, new_inst)
        after = self.rows(new_data)
        self.assertEqual(active['data_schema'], d.DATA_SCHEMA)
        self.assertNotEqual(new_inst['generation'], inst['generation'])
        self.assertEqual({k:v for k,v in new_inst.items() if k != 'generation'},
                         {k:v for k,v in inst.items() if k != 'generation'})
        self.assertEqual((new_data / 'agents/synthetic/agent.json').read_bytes(), settings)
        for table in ('days', 'contacts', 'observations', 'memories', 'loops'):
            self.assertEqual(before[table], after[table])
        self.assertEqual(after['photos'][0][:-2], before['photos'][0][:-2])
        self.assertEqual(Path(after['photos'][0][-2]).read_bytes(), b'synthetic-image-asset')
        self.assertEqual(self.rows(data), before)
        saved = Path(result['backups'][0])
        manifest = d.verify_backup(saved, inst, expected_schema=2)
        self.assertEqual(manifest['reason'], 'before-schema-4-migration')
        self.old_run('from life_engine.durable import verify_backup; import json; '
                     'verify_backup(sys.argv[2],json.loads(sys.argv[3]))', saved, json.dumps(inst))
        self.assertTrue(d.health(self.root)['ok'])
        repo = SQLiteWorldRepository(new_data / 'agents/synthetic/life.db')
        repo.close()
        before_again = (self.root / 'registry.json').read_bytes()
        d.upgrade(self.root, ROOT)
        self.assertEqual((self.root / 'registry.json').read_bytes(), before_again)
        self.assertTrue(data.exists())
        self.assertTrue((self.root / 'releases' / reg['release']).is_dir())

    def test_two_instances_activate_together(self):
        self.install_old('a')
        old, _, _ = self.install_old('b')
        result = d.upgrade(self.root, ROOT)
        active = d.registry(self.root)
        self.assertEqual(len(result['backups']), 2)
        for key, inst in active['instances'].items():
            self.assertNotEqual(inst['generation'], old['instances'][key]['generation'])
            d.db_check(d.state_home(self.root, inst) / 'agents/synthetic/life.db')

    def test_second_instance_failure_keeps_entire_registry_and_old_runtime(self):
        self.install_old('a')
        reg, inst, data = self.install_old('b')
        before = (self.root / 'registry.json').read_bytes()
        original = d.migrate_generation
        count = 0
        def fail_second(*args):
            nonlocal count
            count += 1
            original(*args)
            if count == 2:
                raise RuntimeError('第二个实例迁移后故障')
        with patch.object(d, 'migrate_generation', side_effect=fail_second), self.assertRaises(RuntimeError):
            d.upgrade(self.root, ROOT)
        self.assertEqual((self.root / 'registry.json').read_bytes(), before)
        for instance in reg['instances'].values():
            self.assert_old_works(instance, d.state_home(self.root, instance))
        self.assertEqual(d.upgrade(self.root, ROOT)['settings_and_data_preserved'], True)

    def test_migration_mid_sql_failure_preserves_active_and_retry(self):
        _, inst, data = self.install_old()
        before = (self.root / 'registry.json').read_bytes()
        def broken(db):
            db.execute('CREATE TABLE unfinished(value TEXT)')
            raise RuntimeError('迁移中断')
        with patch.object(d, 'migrate_copy', side_effect=broken), self.assertRaises(RuntimeError):
            d.upgrade(self.root, ROOT)
        self.assertEqual((self.root / 'registry.json').read_bytes(), before)
        self.assert_old_works(inst, data)
        d.upgrade(self.root, ROOT)

    def test_registry_activation_failure_preserves_old_install(self):
        _, inst, data = self.install_old()
        before = (self.root / 'registry.json').read_bytes()
        original = d.write
        def broken(path, value):
            if path == self.root / 'registry.json':
                raise OSError('registry 激活故障')
            original(path, value)
        with patch.object(d, 'write', side_effect=broken), self.assertRaises(OSError):
            d.upgrade(self.root, ROOT)
        self.assertEqual((self.root / 'registry.json').read_bytes(), before)
        self.assert_old_works(inst, data)

    def test_active_generation_migration_is_forbidden(self):
        _, inst, data = self.install_old()
        before = self.rows(data)
        with self.assertRaisesRegex(ValueError, '活动 generation'):
            d.migrate_generation(self.root, data, inst)
        self.assertEqual(self.rows(data), before)

    def test_schema_rollback_blocks_code_only_and_restores_whole_tuple(self):
        old, inst, data = self.install_old()
        result = d.upgrade(self.root, ROOT)
        new = d.registry(self.root)
        with self.assertRaises(ValueError):
            d.rollback_code(self.root, old['release'])
        d.rollback_schema(self.root, Path(result['schema_rollback']))
        self.assertEqual(d.registry(self.root, allow_schema2=True), old)
        self.assertTrue(d.state_home(self.root, new['instances'][inst['id']]).exists())
        self.assert_old_works(inst, data)

    def test_pre_migration_backup_includes_committed_wal(self):
        _, inst, data = self.install_old()
        path = data / 'agents/synthetic/life.db'
        with closing(sqlite3.connect(path)) as live:
            live.execute('PRAGMA journal_mode=WAL')
            live.execute('PRAGMA wal_autocheckpoint=0')
            live.execute("INSERT INTO memories(at,kind,summary,provenance) VALUES(2,'test','WAL-only','test')")
            live.commit()
            self.assertTrue(Path(str(path) + '-wal').exists())
            result = d.upgrade(self.root, ROOT)
            saved = Path(result['backups'][0])
            d.verify_backup(saved, inst, expected_schema=2)
            with closing(sqlite3.connect(saved / 'data/agents/synthetic/life.db')) as db:
                self.assertEqual(db.execute("SELECT count(*) FROM memories WHERE summary='WAL-only'").fetchone()[0], 1)

    def test_unknown_or_pr3_style_schema3_is_unchanged(self):
        for version in ('3', '999'):
            with self.subTest(version=version):
                path = self.base / (version + '.db')
                with closing(sqlite3.connect(path)) as db:
                    db.executescript(SCHEMA)
                    db.execute("INSERT INTO meta VALUES('agent_id','synthetic')")
                    db.execute("INSERT INTO meta VALUES('schema_version',?)", (version,))
                    db.execute('CREATE TABLE roleplay_sessions(id INTEGER PRIMARY KEY, card_id INTEGER, status TEXT)')
                    db.commit()
                before = path.read_bytes()
                for action in (lambda: d.db_check(path), lambda: Store(path, 'synthetic'), lambda: SQLiteWorldRepository(path)):
                    with self.assertRaises(WorldRuntimeError) as caught:
                        action()
                    self.assertEqual(caught.exception.code, Code.SCHEMA_MISMATCH)
                    self.assertEqual(path.read_bytes(), before)

    def test_schema3_backup_restore_world_and_reject_schema2_backup(self):
        _, inst, _ = self.install_old()
        result = d.upgrade(self.root, ROOT)
        reg = d.registry(self.root)
        inst = reg['instances'][inst['id']]
        data = d.state_home(self.root, inst)
        path = data / 'agents/synthetic/life.db'
        runtime = WorldRuntime(SQLiteWorldRepository(path))
        actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
        soul = Soul(DomainId.new(IdKind.SOUL), actor.owner_id, DomainId.new(IdKind.WORLD))
        runtime.register_soul(actor, soul)
        now = datetime.now(timezone.utc)
        ir = parse_bytes(json.dumps({'spec': 'chara_card_v3', 'spec_version': '3.0', 'data': {
            'name': '原创档案员', 'description': '用于备份验收', 'first_mes': '欢迎',
            'group_only_greetings': [], 'extensions': {}}}).encode())
        definition = project_definition(ir, actor, now)
        runtime.register_definition(actor, definition)
        created = runtime.create_roleplay_world(actor, soul.soul_id, now)
        created = runtime.instantiate(actor, created.world.world_id, created.timeline.scope.timeline_id,
                                      definition.reference, created.world.revision, now)
        created = runtime.enter(actor, created.world.world_id, created.timeline.scope.timeline_id,
                                created.characters[0].character_instance_id, created.world.revision, created.world.writer_epoch)
        created = runtime.exit(actor, created.world.world_id, created.timeline.scope.timeline_id,
                               created.sessions[0].session_id, created.world.revision, created.world.writer_epoch)
        with d.locked(self.root, inst['id']):
            saved = d.snapshot(self.root, reg, inst)
        with runtime.repository.transaction() as tx:
            tx.save_world(replace(created, world=replace(created.world, revision=created.world.revision.next())), created.world.revision)
        before = (self.root / 'registry.json').read_bytes()
        with self.assertRaises(ValueError):
            d.restore(self.root, inst['id'], result['backups'][0])
        self.assertEqual((self.root / 'registry.json').read_bytes(), before)
        restored = d.restore(self.root, inst['id'], saved)
        restored_repo = SQLiteWorldRepository(Path(restored['active_data']) / 'agents/synthetic/life.db')
        with restored_repo.transaction() as tx:
            self.assertEqual(tx.get_world(created.world.world_id), created)

    def test_health_reports_missing_generation_and_structural_damage(self):
        _, inst, _ = self.install_old()
        d.upgrade(self.root, ROOT)
        reg = d.registry(self.root)
        data = d.state_home(self.root, reg['instances'][inst['id']])
        with closing(sqlite3.connect(data / 'agents/synthetic/life.db')) as db:
            db.execute('DROP INDEX one_open_session_per_world')
        self.assertFalse(d.health(self.root)['ok'])
        reg['instances'][inst['id']]['generation'] = 'missing-generation'
        d.write(self.root / 'registry.json', reg)
        self.assertFalse(d.health(self.root)['ok'])


if __name__ == '__main__':
    unittest.main()
