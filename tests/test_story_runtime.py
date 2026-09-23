"""Story 受信接受、独立修订、会话围栏与持久恢复。"""
from dataclasses import replace
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
import sqlite3
import unittest

from memory_fixture import MemoryFixture, d, DomainId, IdKind, Principal, Provenance, SourceType, RealityStatus, CanonStatus
from life_engine.story import (FactPayload, CharacterPayload, RelationshipPayload, ThreadPayload,
    NarrativePayload, OwnerStoryContext, SessionStoryContext, StoryEventKind as K,
    StoryEventProposal, StoryIdempotencyIdentity, StoryRevision)
from life_engine.story_repository import StoryRuntimeError, StoryFailure as SC
from life_engine.story_runtime import StoryRuntime
from life_engine.story_sqlite_repository import SQLiteStoryRepository
from life_engine.world_sqlite_repository import SQLiteWorldRepository
from life_engine.world_runtime import WorldRuntime


class StoryRuntimeTests(MemoryFixture,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.story_repo=SQLiteStoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id)
        self.story=StoryRuntime(self.story_repo)
        self.story_owner=OwnerStoryContext(self.actor,self.a.timeline.scope)
        self.story_session=SessionStoryContext(self.actor,self.session.scope,self.session.session_id,
            self.session.writer_epoch,self.world_repo.runtime_id,self.session.viewer)

    def proposal(self,kind,payload,*,supersedes=None):
        return StoryEventProposal(kind,payload,self.provenance('原创故事',canon=CanonStatus.CANDIDATE),
            supersedes_event_id=supersedes)

    def accept(self,kind,payload,slot='one',*,context=None,expected=None,supersedes=None):
        current=self.story.get_story_state(self.story_owner).revision if expected is None else expected
        return self.story.accept_story_event(context or self.story_owner,current,
            self.proposal(kind,payload,supersedes=supersedes),StoryIdempotencyIdentity('synthetic',slot))

    def test_owner_accept_idempotency_correction_and_restart(self):
        before_world=self.world.snapshot(self.actor,self.a.world.world_id)
        before_memory=self.memory.collection_revision(self.owner)
        first=self.accept(K.WORLD_FACT_SET,FactPayload('place','city','Paris'))
        self.assertEqual(first,self.accept(K.WORLD_FACT_SET,FactPayload('place','city','Paris'),expected=StoryRevision()))
        with self.assertRaises(StoryRuntimeError) as caught:
            self.accept(K.WORLD_FACT_SET,FactPayload('place','city','wrong'),expected=StoryRevision())
        self.assertEqual(caught.exception.code,SC.IDEMPOTENCY_CONFLICT)
        second=self.accept(K.WORLD_FACT_SET,FactPayload('place','city','London'),'two',supersedes=first.event_id)
        self.assertEqual((second.revision.value,second.clock.logical_tick),(2,2))
        self.assertEqual(self.story.get_story_state(self.story_owner).world_facts,(('place','city','London'),))
        self.assertEqual(tuple(e.proposal.payload.value for e in self.story.list_story_events(self.story_owner)),('Paris','London'))
        self.assertEqual(self.story.replay_verify(self.story_owner),self.story.get_story_state(self.story_owner))
        self.assertEqual(self.world.snapshot(self.actor,self.a.world.world_id),before_world)
        self.assertEqual(self.memory.collection_revision(self.owner),before_memory)
        self.story_repo.close()
        self.story_repo=SQLiteStoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id)
        self.story=StoryRuntime(self.story_repo)
        self.assertEqual(self.story.get_story_state(self.story_owner).world_facts,(('place','city','London'),))
        d.db_check(self.path)

    def test_all_kinds_scope_and_session_projection(self):
        created=self.world.create_roleplay_world(self.actor,self.soul.soul_id,self.now)
        first=self.world.instantiate(self.actor,created.world.world_id,created.timeline.scope.timeline_id,
            self.definition.reference,created.world.revision,self.now)
        second=self.world.instantiate(self.actor,first.world.world_id,first.timeline.scope.timeline_id,
            self.definition.reference,first.world.revision,self.now)
        entered=self.world.enter(self.actor,second.world.world_id,second.timeline.scope.timeline_id,
            second.characters[0].character_instance_id,second.world.revision,second.world.writer_epoch)
        self.story_owner=OwnerStoryContext(self.actor,entered.timeline.scope)
        binding=entered.sessions[-1]
        self.story_session=SessionStoryContext(self.actor,entered.timeline.scope,binding.session_id,
            binding.writer_epoch,self.world_repo.runtime_id,
            self.context(entered).viewer)
        char=second.characters[0].character_instance_id
        other=second.characters[1].character_instance_id
        self.accept(K.CHARACTER_STATE_SET,CharacterPayload(char,'health','well'))
        self.accept(K.RELATIONSHIP_SET,RelationshipPayload(char,other,'status','ally'),'relation')
        thread=DomainId.new(IdKind.STORY_THREAD)
        self.accept(K.THREAD_OPENED,ThreadPayload(thread,'钟楼','未完成'),'thread')
        self.accept(K.NARRATIVE_EVENT,NarrativePayload('只是叙事'),'narrative')
        projection=self.story.get_story_projection(self.story_session)
        self.assertEqual(projection.character_state,(('health','well'),))
        self.assertEqual(len(projection.relationships),1)
        self.assertEqual(len(projection.open_threads),1)
        b=self.make_world()
        self.assertEqual(self.story.get_story_state(OwnerStoryContext(self.actor,b.timeline.scope)).revision.value,0)

    def test_revision_conflict_and_session_fencing(self):
        self.accept(K.NARRATIVE_EVENT,NarrativePayload('事件一'),context=self.story_session)
        with self.assertRaises(StoryRuntimeError) as caught:
            self.accept(K.NARRATIVE_EVENT,NarrativePayload('事件二'),'two',expected=StoryRevision())
        self.assertEqual(caught.exception.code,SC.REVISION_CONFLICT)
        with self.assertRaises(StoryRuntimeError) as caught:
            self.story.get_story_projection(replace(self.story_session,runtime_id='wrong'))
        self.assertEqual(caught.exception.code,SC.SESSION_STALE)
        current=self.world.snapshot(self.actor,self.a.world.world_id)
        self.world.exit(self.actor,current.world.world_id,current.timeline.scope.timeline_id,
            self.session.session_id,current.world.revision,current.world.writer_epoch)
        with self.assertRaises(StoryRuntimeError) as caught:
            self.story.accept_story_event(self.story_session,StoryRevision(1),
                self.proposal(K.NARRATIVE_EVENT,NarrativePayload('晚到')),
                StoryIdempotencyIdentity('synthetic','late'))
        self.assertEqual(caught.exception.code,SC.SESSION_STALE)

    def test_invalid_subject_and_supersedes_rollback(self):
        before=self.story.get_story_state(self.story_owner)
        with self.assertRaises(StoryRuntimeError):
            self.accept(K.CHARACTER_STATE_SET,CharacterPayload(DomainId.new(IdKind.CHARACTER),'x','y'))
        with self.assertRaises(StoryRuntimeError):
            self.accept(K.NARRATIVE_EVENT,NarrativePayload('修正'),'another',supersedes=DomainId.new(IdKind.EVENT))
        self.assertEqual(self.story.get_story_state(self.story_owner),before)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM story_events').fetchone()[0],0)

    def test_projection_budget_rejects_whole_event(self):
        with patch('life_engine.story_runtime.MAX_STORY_STATE_BYTES',16):
            with self.assertRaises(StoryRuntimeError) as caught:
                self.accept(K.WORLD_FACT_SET,FactPayload('place','key','value'))
        self.assertEqual(caught.exception.code,SC.BUDGET_INPUT)
        self.assertEqual(self.story.get_story_state(self.story_owner).revision.value,0)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM story_events').fetchone()[0],0)

    def test_database_event_is_immutable(self):
        first=self.accept(K.NARRATIVE_EVENT,NarrativePayload('原文'))
        with closing(sqlite3.connect(self.path)) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('UPDATE story_events SET payload=? WHERE event_id=?',('{}',str(first.event_id)))
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('DELETE FROM story_events WHERE event_id=?',(str(first.event_id),))

    def test_backup_restore_exact_revision_and_old_session_fence(self):
        first=self.accept(K.NARRATIVE_EVENT,NarrativePayload('备份前'))
        with d.locked(self.root,'management'),d.locked(self.root,self.key):
            backup=d.snapshot(self.root,d.registry(self.root),self.inst)
        manifest=d.verify_backup(backup,self.inst)
        self.assertEqual(manifest['data_schema'],6)
        self.assertIsNotNone(manifest['memory_control_watermark'])
        self.assertEqual(manifest['memory_install_id'],self.reg['memory_install_id'])
        self.accept(K.NARRATIVE_EVENT,NarrativePayload('备份后'),'two')
        d.restore(self.root,self.key,backup)
        with self.assertRaises(StoryRuntimeError) as caught:
            self.story.get_story_projection(self.story_session)
        self.assertEqual(caught.exception.code,SC.RECOVERY_REQUIRED)
        current=d.registry(self.root)
        path=d.state_home(self.root,current['instances'][self.key])/'agents/synthetic/life.db'
        self.world_repo.close();self.story_repo.close()
        self.world_repo=SQLiteWorldRepository(path)
        self.story_repo=SQLiteStoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id)
        self.story=StoryRuntime(self.story_repo)
        state=self.story.get_story_state(self.story_owner)
        self.assertEqual((state.revision.value,state.clock.logical_tick,state.last_event_sequence),(1,1,1))
        self.assertEqual(self.story.list_story_events(self.story_owner)[0].event_id,first.event_id)
        with self.assertRaises(StoryRuntimeError):
            self.story.get_story_projection(self.story_session)
        self.assertEqual(self.story.replay_verify(self.story_owner),state)

    def test_two_repositories_one_revision_and_corrupt_projection(self):
        peer=StoryRuntime(SQLiteStoryRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id))
        barrier=Barrier(2)
        def attempt(runtime,slot):
            barrier.wait()
            try:
                return runtime.accept_story_event(self.story_owner,StoryRevision(),
                    self.proposal(K.NARRATIVE_EVENT,NarrativePayload(slot)),
                    StoryIdempotencyIdentity('race',slot))
            except StoryRuntimeError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(attempt,self.story,'a')
            b=pool.submit(attempt,peer,'b')
            outcomes=(a.result(),b.result())
        self.assertEqual(sum(x==SC.REVISION_CONFLICT for x in outcomes),1)
        self.assertEqual(self.story.get_story_state(self.story_owner).revision.value,1)
        peer.repository.close()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('UPDATE story_collection_state SET projection=?',('{}',))
            db.commit()
            with self.assertRaises(StoryRuntimeError) as caught:
                from life_engine.story_sqlite_repository import validate_story_data
                validate_story_data(db)
            self.assertEqual(caught.exception.code,SC.STORAGE_CORRUPT)
