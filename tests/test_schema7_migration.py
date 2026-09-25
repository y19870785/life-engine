"""真实 canonical Schema 6 发行包 → Schema 7 副本迁移。"""
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
import zipfile

from memory_fixture import ROOT, d
from life_engine.config import defaults
from life_engine.world_schema import validate_schema
from life_engine.bridge_sqlite_repository import validate_bridge_data

BASE = 'cd51d2d97ff4de18b681f4176e57d84f12ed679d'


class Schema7MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = tempfile.TemporaryDirectory(prefix='Schema 6 原版 ')
        cls.package = Path(cls.old.name)
        archived = subprocess.run(['git', 'archive', '--format=zip', BASE, 'runtime'],
            cwd=ROOT, capture_output=True, check=True).stdout
        with zipfile.ZipFile(io.BytesIO(archived)) as package:
            package.extractall(cls.package)

    @classmethod
    def tearDownClass(cls):
        cls.old.cleanup()

    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='Schema 7 迁移 ')
        self.addCleanup(folder.cleanup)
        self.base = Path(folder.name).resolve()
        self.root = self.base / 'install'

    def old_run(self, code, *args):
        done = subprocess.run([sys.executable, '-c',
            'import sys; sys.path.insert(0,sys.argv[1]); ' + code,
            str(self.package / 'runtime'), *map(str, args)], capture_output=True,
            text=True, encoding='utf-8', env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
            timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def install(self, name):
        host = self.base / name
        host.mkdir()
        cfg = defaults('synthetic')
        cfg['integration'].update(adapter='hermes', host_home=str(host))
        config_path = self.base / (name + '.json')
        d.write(config_path, cfg)
        installed = json.loads(self.old_run(
            'from life_engine.durable import create_install,read; import json; '
            'print(json.dumps(create_install(sys.argv[2],sys.argv[3],read(sys.argv[4]))))',
            self.package, self.root, config_path))
        reg = d.registry(self.root, allow_schema2=True)
        inst = reg['instances'][installed['instance']]
        path = d.state_home(self.root, inst) / 'agents/synthetic/life.db'
        return inst, path

    def test_real_schema6_copy_preserves_world_memory_lore_story_and_starts_empty_bridge(self):
        inst, path = self.install('a')
        script = '''from life_engine.domain import *
from life_engine.world_runtime import WorldRuntime
from life_engine.world_sqlite_repository import SQLiteWorldRepository
from life_engine.memory import *
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.lore import *
from life_engine.lore_runtime import LoreRuntime
from life_engine.lore_sqlite_repository import SQLiteLoreRepository
from life_engine.story import *
from life_engine.story_runtime import StoryRuntime
from life_engine.story_sqlite_repository import SQLiteStoryRepository
from life_engine.import_ir import JsonValue,LoreIR
from datetime import datetime,timezone
from hashlib import sha256
import json
path,root,key=sys.argv[2:5]
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
scope=w.timeline.scope
memory_repo=SQLiteMemoryRepository(root,key,runtime_id=repo.runtime_id)
memory=MemoryRuntime(memory_repo)
ctx=OwnerMemoryContext(actor,scope)
provenance=Provenance(SourceType.USER_REPORT,'原创记录',now,actor,RealityStatus.USER_CLAIMED,CanonStatus.ACCEPTED)
memory.create_owner_memory(ctx,MemoryCollectionRevision(),IdempotencyIdentity('migration','memory'),content='保留记忆',kind=MemoryKind.EPISODIC,provenance=provenance,audience=(MemoryAudience(AudienceKind.WORLD),))
lore_repo=SQLiteLoreRepository(root,key,runtime_id=repo.runtime_id)
lore=LoreRuntime(lore_repo)
ir=LoreIR(JsonValue.of({'name':'原创世界书'}),(JsonValue.of({'triggers':['钟楼'],'text':'旧版设定','enabled':True,'settings':{}}),),sha256(b'original-lore').hexdigest())
book=lore.register_book(OwnerLoreContext(actor),'原创世界书',ir,LoreRegistrationIdentity('migration','book'))
lore.bind(OwnerLoreContext(actor,scope),book.book_id,book.book_version,0,LoreBindingRevision(),LoreRegistrationIdentity('migration','bind'))
story_repo=SQLiteStoryRepository(root,key,runtime_id=repo.runtime_id)
story=StoryRuntime(story_repo)
sc=OwnerStoryContext(actor,scope)
proposal=StoryEventProposal(StoryEventKind.NARRATIVE_EVENT,NarrativePayload('雨夜钟楼'),Provenance(SourceType.OWNER_COMMAND,'bootstrap',now,actor,RealityStatus.FICTIONAL,CanonStatus.ACCEPTED))
story.accept_story_event(sc,StoryRevision(),proposal,StoryIdempotencyIdentity('migration','story'))
print(json.dumps({'world':str(w.world.world_id)}))
story_repo.close();lore_repo.close();memory_repo.close();repo.close()'''
        self.old_run(script, path, self.root, inst['id'])
        with closing(sqlite3.connect(path)) as db:
            validate_schema(db, 6)
            names = ('worlds', 'world_memories', 'lore_books', 'lore_world_bindings',
                     'story_events', 'story_collection_state', 'memory_applied_controls')
            before = {name: db.execute('SELECT * FROM ' + name + ' ORDER BY rowid').fetchall()
                      for name in names}
        result = d.upgrade(self.root, ROOT)
        reg = d.registry(self.root)
        self.assertEqual(reg['data_schema'], 7)
        self.assertTrue(reg['instances'][inst['id']]['generation'].startswith('schema7-'))
        newpath = d.state_home(self.root, reg['instances'][inst['id']]) / 'agents/synthetic/life.db'
        with closing(sqlite3.connect(newpath)) as db:
            validate_schema(db, 7)
            validate_bridge_data(db)
            for name, rows in before.items():
                self.assertEqual(db.execute('SELECT * FROM ' + name + ' ORDER BY rowid').fetchall(), rows, name)
            self.assertEqual(db.execute('SELECT count(*) FROM bridge_grants').fetchone()[0], 0)
        self.assertTrue(d.health(self.root)['ok'])
        self.assertEqual(d.verify_backup(result['backups'][0], inst, expected_schema=6)['data_schema'], 6)


if __name__ == '__main__':
    unittest.main()
