"""原创合成 Memory 安装，不接真实宿主或角色卡。"""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
from life_engine import durable as d
from life_engine.config import defaults
from life_engine.domain import *
from life_engine.memory import *
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.world_runtime import WorldRuntime
from life_engine.world_sqlite_repository import SQLiteWorldRepository

ROOT = Path(__file__).resolve().parents[1]


class MemoryFixture:
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='Memory 合成验收 ')
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name).resolve()
        self.root = self.base/'install'
        host = self.base/'host'
        host.mkdir()
        cfg = defaults('synthetic')
        cfg['integration'].update(adapter='hermes',host_home=str(host))
        result = d.create_install(ROOT,self.root,cfg)
        self.key = result['instance']
        self.reg = d.registry(self.root)
        self.inst = self.reg['instances'][self.key]
        self.data = d.state_home(self.root,self.inst)
        self.path = self.data/'agents/synthetic/life.db'
        self.now = datetime(2026,9,21,tzinfo=timezone.utc)
        self.actor = Principal(DomainId.new(IdKind.PRINCIPAL),DomainId.new(IdKind.OWNER))
        self.soul = Soul(DomainId.new(IdKind.SOUL),self.actor.owner_id,DomainId.new(IdKind.WORLD))
        self.world_repo = SQLiteWorldRepository(self.path)
        self.world = WorldRuntime(self.world_repo)
        self.world.register_soul(self.actor,self.soul)
        self.definition = CharacterDefinition(DefinitionRef(DomainId.new(IdKind.DEFINITION),DefinitionVersion(1)),
            self.actor.owner_id,'原创角色',Values(),Provenance(SourceType.IMPORT,'原创卡',self.now,self.actor,RealityStatus.UNKNOWN,CanonStatus.UNREVIEWED))
        self.world.register_definition(self.actor,self.definition)
        self.a = self.make_world()
        self.repo = SQLiteMemoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id)
        self.memory = MemoryRuntime(self.repo)
        self.owner = OwnerMemoryContext(self.actor,self.a.timeline.scope)
        self.session = self.context(self.a)

    def make_world(self):
        w = self.world.create_roleplay_world(self.actor,self.soul.soul_id,self.now)
        w = self.world.instantiate(self.actor,w.world.world_id,w.timeline.scope.timeline_id,self.definition.reference,w.world.revision,self.now)
        return self.world.enter(self.actor,w.world.world_id,w.timeline.scope.timeline_id,w.characters[0].character_instance_id,w.world.revision,w.world.writer_epoch)

    def context(self,w):
        b = w.sessions[-1]
        return SessionMemoryContext(self.actor,w.timeline.scope,b.session_id,b.writer_epoch,
            MemoryAudience(AudienceKind.CHARACTER_INSTANCE,b.character_instance_id))

    def provenance(self, source='原创来源', *, session=False, canon=CanonStatus.CANDIDATE):
        return Provenance(SourceType.MODEL if session else SourceType.USER_REPORT,source,self.now,self.actor,
            RealityStatus.FICTIONAL if session else RealityStatus.USER_CLAIMED,canon,
            self.a.world.world_id if session else None,self.a.timeline.scope.timeline_id if session else None,
            self.a.sessions[-1].session_id if session else None)

    def create(self, source='原创来源', **kwargs):
        params = dict(content='原创记忆正文',kind=MemoryKind.EPISODIC,provenance=self.provenance(source,canon=CanonStatus.ACCEPTED),
                      audience=(self.session.viewer,))
        params.update(kwargs)
        return self.memory.create_owner_memory(self.owner,self.memory.collection_revision(self.owner),IdempotencyIdentity(source,'create'),**params)
