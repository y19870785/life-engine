"""授权、接受权、隔离和晚到结果验收。"""
from dataclasses import replace
import unittest
from memory_fixture import *
from life_engine.memory_repository import MemoryRuntimeError, MemoryFailure as MC


class MemoryRuntimeTests(MemoryFixture,unittest.TestCase):
    def test_candidate_acceptance_preserves_source_and_world(self):
        before = self.world.snapshot(self.actor,self.a.world.world_id)
        result = self.memory.create_session_candidate(self.session,MemoryCollectionRevision(),IdempotencyIdentity('model-1','create'),
            content='到过原创城堡',kind=MemoryKind.EPISODIC,provenance=self.provenance(session=True))
        self.assertEqual(self.memory.query(self.session).records,())
        with self.assertRaises(MemoryRuntimeError):
            self.memory.accept_memory(self.session,result.memory_id,result.revision,IdempotencyIdentity('accept','1'))
        accepted = self.memory.accept_memory(self.owner,result.memory_id,result.revision,IdempotencyIdentity('accept','1'))
        actual = self.memory.get_memory(self.session,accepted.memory_id)
        self.assertEqual(actual.provenance.source_type,SourceType.MODEL)
        self.assertEqual(actual.provenance.reality_status,RealityStatus.FICTIONAL)
        self.assertEqual(actual.content_version,2)
        self.assertEqual(actual.predecessor,result.memory_id)
        self.assertEqual(self.world.snapshot(self.actor,self.a.world.world_id),before)
        d.db_check(self.path)

    def test_cross_world_definition_direct_id_and_user_audience(self):
        first = self.create()
        b = self.make_world()
        self.assertEqual(b.characters[0].definition,self.a.characters[0].definition)
        self.assertEqual(self.memory.query(self.context(b),query='原创').records,())
        with self.assertRaises(MemoryRuntimeError) as caught:
            self.memory.get_memory(self.context(b),first.memory_id)
        self.assertEqual(caught.exception.code,MC.NOT_AVAILABLE)
        private = self.create('private',audience=(MemoryAudience(AudienceKind.USER,self.actor.owner_id),),
                              subjects=(MemorySubject(SubjectKind.CHARACTER_INSTANCE,self.session.viewer.target),))
        with self.assertRaises(MemoryRuntimeError):
            self.memory.get_memory(self.session,private.memory_id)
        self.assertEqual(len(self.memory.query_owner_memory(self.owner).records),2)

    def test_late_exit_and_restart(self):
        self.world.exit(self.actor,self.a.world.world_id,self.a.timeline.scope.timeline_id,self.session.session_id,
                        self.a.world.revision,self.a.world.writer_epoch)
        args = dict(content='迟到',kind=MemoryKind.EPISODIC,provenance=self.provenance(session=True))
        with self.assertRaises(MemoryRuntimeError):
            self.memory.create_session_candidate(self.session,MemoryCollectionRevision(),IdempotencyIdentity('late','1'),**args)
        SQLiteWorldRepository(self.path).close()
        with self.assertRaises(ValueError):
            self.memory.query(self.owner)

    def test_reject_hide_unhide_and_user_claim_accept(self):
        r = self.create(provenance=self.provenance())
        accepted = self.memory.accept_memory(self.owner,r.memory_id,r.revision,IdempotencyIdentity('accept','1'))
        self.assertEqual(self.memory.get_memory(self.owner,accepted.memory_id).provenance.reality_status,RealityStatus.USER_CLAIMED)
        hidden = self.memory.hide_memory(self.owner,accepted.memory_id,accepted.revision,IdempotencyIdentity('hide','1'))
        self.assertEqual(self.memory.query(self.session).records,())
        self.memory.unhide_memory(self.owner,hidden.memory_id,hidden.revision,IdempotencyIdentity('unhide','1'))
        self.assertEqual(len(self.memory.query(self.session).records),1)

    def test_story_bridge_and_audience_expansion_denied(self):
        for p in (replace(self.provenance(),source_type=SourceType.BRIDGE),
                  replace(self.provenance(session=True),source_event_id=DomainId.new(IdKind.EVENT))):
            with self.assertRaises(MemoryRuntimeError):
                self.create(provenance=p)
        with self.assertRaises(MemoryRuntimeError):
            self.memory.create_session_candidate(self.session,MemoryCollectionRevision(),IdempotencyIdentity('world','1'),
                content='私有',kind=MemoryKind.EPISODIC,provenance=self.provenance(session=True),audience=(MemoryAudience(AudienceKind.WORLD),))

    def test_wrong_principal_scope_character_epoch_are_rejected(self):
        b = self.make_world()
        contexts = (
            replace(self.session,principal=Principal(DomainId.new(IdKind.PRINCIPAL),self.actor.owner_id)),
            replace(self.session,scope=b.timeline.scope),
            replace(self.session,viewer=self.context(b).viewer),
            replace(self.session,writer_epoch=self.session.writer_epoch.next()),
        )
        for context in contexts:
            with self.subTest(context=context),self.assertRaises(ValueError):
                self.memory.create_session_candidate(context,MemoryCollectionRevision(),IdempotencyIdentity('wrong','1'),
                    content='不能保存',kind=MemoryKind.EPISODIC,provenance=self.provenance(session=True))
        self.assertEqual(self.memory.collection_revision(self.owner).value,0)

    def test_late_switch_does_not_route_to_target(self):
        b = self.make_world()
        self.world.exit(self.actor,b.world.world_id,b.timeline.scope.timeline_id,b.sessions[-1].session_id,b.world.revision,b.world.writer_epoch)
        b = self.world.snapshot(self.actor,b.world.world_id)
        self.world.switch_world(self.actor,self.a.world.world_id,self.a.timeline.scope.timeline_id,self.session.session_id,
            self.a.world.revision,self.a.world.writer_epoch,b.world.world_id,b.timeline.scope.timeline_id,
            b.characters[0].character_instance_id,b.world.revision,b.world.writer_epoch)
        with self.assertRaises(ValueError):
            self.memory.create_session_candidate(self.session,MemoryCollectionRevision(),IdempotencyIdentity('late','1'),
                content='迟到',kind=MemoryKind.EPISODIC,provenance=self.provenance(session=True))
        self.assertEqual(self.memory.collection_revision(OwnerMemoryContext(self.actor,b.timeline.scope)).value,0)

    def test_late_suspend_denied(self):
        self.world.suspend(self.actor,self.a.world.world_id,self.a.timeline.scope.timeline_id,self.session.session_id,
                           self.a.world.revision,self.a.world.writer_epoch)
        with self.assertRaises(ValueError):
            self.memory.create_session_candidate(self.session,MemoryCollectionRevision(),IdempotencyIdentity('late','1'),
                content='迟到',kind=MemoryKind.EPISODIC,provenance=self.provenance(session=True))

    def test_soul_roleplay_bidirectional_isolation(self):
        from life_engine.world_repository import WorldSnapshot
        p = Provenance(SourceType.OWNER_COMMAND,'默认生活',self.now,self.actor,RealityStatus.SIMULATED_LIFE_STATE)
        scope = WorldScope(self.actor.owner_id,self.soul.soul_id,self.soul.soul_world_id,DomainId.new(IdKind.TIMELINE))
        with self.world_repo.transaction() as tx:
            tx.add_world(WorldSnapshot(World(self.soul.soul_world_id,self.actor.owner_id,self.soul.soul_id,WorldKind.SOUL,p),WorldTimeline(scope,p)))
        active = self.world.enter(self.actor,scope.world_id,scope.timeline_id,None,Revision(),WriterEpoch())
        soul_session = SessionMemoryContext(self.actor,scope,active.sessions[-1].session_id,active.world.writer_epoch,
                                            MemoryAudience(AudienceKind.SOUL,self.soul.soul_id))
        owner = OwnerMemoryContext(self.actor,scope)
        record = self.memory.create_owner_memory(owner,MemoryCollectionRevision(),IdempotencyIdentity('soul','1'),
            content='默认生活私有记忆',kind=MemoryKind.SEMANTIC,provenance=self.provenance(canon=CanonStatus.ACCEPTED),audience=(soul_session.viewer,))
        role = self.create()
        for context,mid in ((self.session,record.memory_id),(soul_session,role.memory_id)):
            with self.assertRaises(MemoryRuntimeError) as caught:
                self.memory.get_memory(context,mid)
            self.assertEqual(caught.exception.code,MC.NOT_AVAILABLE)

    def test_supersede_reject_and_fixed_history(self):
        first = self.create(provenance=self.provenance())
        rejected = self.memory.reject_memory(self.owner,first.memory_id,first.revision,IdempotencyIdentity('reject','1'))
        self.assertEqual(self.memory.query(self.session).records,())
        old = self.memory.get_memory(self.owner,first.memory_id,history=True)
        self.assertEqual(old.lifecycle,MemoryLifecycle.SUPERSEDED)
        self.assertEqual(old.superseded_by,rejected.memory_id)
        self.assertEqual(old.provenance.canon_status,CanonStatus.CANDIDATE)
        with self.assertRaises(ValueError):
            self.memory.supersede_memory(self.owner,first.memory_id,rejected.revision,IdempotencyIdentity('fork','1'),
                content='不能产生第二后继',provenance=self.provenance())
        new = self.memory.supersede_memory(self.owner,rejected.memory_id,rejected.revision,IdempotencyIdentity('correct','1'),
            content='修正后的陈述',provenance=self.provenance('修正来源'))
        self.assertEqual(self.memory.get_memory(self.owner,new.memory_id,history=True).content_version,3)
        d.db_check(self.path)
