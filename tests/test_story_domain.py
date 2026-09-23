"""Story 身份、载荷与纯 reducer 的原创合成验收。"""
from datetime import datetime, timezone
import unittest

from memory_fixture import *
from life_engine.domain import DomainError
from life_engine.story import (FactPayload, NarrativePayload, RelationshipPayload, StoryClock,
    StoryEvent, StoryEventKind as K, StoryEventProposal, StoryRevision, StoryState,
    StoryThreadStatus, ThreadPayload, CharacterPayload)
from life_engine.story_reducer import reduce_story, replay_story
from life_engine.story_codec import state_dump, state_load


class StoryDomainTests(unittest.TestCase):
    def setUp(self):
        self.owner=DomainId.new(IdKind.OWNER)
        self.actor=Principal(DomainId.new(IdKind.PRINCIPAL),self.owner)
        self.scope=WorldScope(self.owner,DomainId.new(IdKind.SOUL),DomainId.new(IdKind.WORLD),DomainId.new(IdKind.TIMELINE))
        self.provenance=Provenance(SourceType.USER_REPORT,'原创故事',datetime(2026,9,23,tzinfo=timezone.utc),
            self.actor,RealityStatus.FICTIONAL,CanonStatus.CANDIDATE)

    def event(self,kind,payload,seq):
        return StoryEvent(DomainId.new(IdKind.EVENT),self.scope,seq,StoryRevision(seq),StoryClock(seq),
            StoryEventProposal(kind,payload,self.provenance),self.actor.principal_id,
            datetime(2026,9,23,tzinfo=timezone.utc))

    def test_identity_revision_and_payload_validation(self):
        self.assertEqual(DomainId.parse(str(DomainId.new(IdKind.STORY_THREAD))).kind,IdKind.STORY_THREAD)
        with self.assertRaises(DomainError): StoryRevision(True)
        with self.assertRaises(DomainError): StoryClock(True)
        with self.assertRaises(DomainError): StoryEventProposal(K.WORLD_FACT_SET,FactPayload('place','city'),self.provenance)
        with self.assertRaises(DomainError): StoryEventProposal(K.NARRATIVE_EVENT,NarrativePayload('甲'*6000),self.provenance)
        with self.assertRaises(DomainError): RelationshipPayload(DomainId.new(IdKind.CHARACTER),DomainId.new(IdKind.WORLD),'key','value')

    def test_fact_character_relationship_thread_and_narrative_replay(self):
        a,b=DomainId.new(IdKind.CHARACTER),DomainId.new(IdKind.CHARACTER)
        thread=DomainId.new(IdKind.STORY_THREAD)
        sequence=[
            (K.WORLD_FACT_SET,FactPayload('place','city','钟楼')),
            (K.CHARACTER_STATE_SET,CharacterPayload(a,'location','钟楼')),
            (K.RELATIONSHIP_SET,RelationshipPayload(a,b,'status','ally')),
            (K.THREAD_OPENED,ThreadPayload(thread,'灯塔','等待线索')),
            (K.NARRATIVE_EVENT,NarrativePayload('两人在雨夜相遇')),
            (K.THREAD_UPDATED,ThreadPayload(thread,None,'发现线索')),
            (K.THREAD_RESOLVED,ThreadPayload(thread)),
            (K.RELATIONSHIP_REMOVED,RelationshipPayload(a,b,'status')),
            (K.CHARACTER_STATE_REMOVED,CharacterPayload(a,'location')),
            (K.WORLD_FACT_REMOVED,FactPayload('place','city'))]
        events=tuple(self.event(kind,payload,n) for n,(kind,payload) in enumerate(sequence,1))
        state=replay_story(self.scope,events)
        self.assertEqual((state.revision.value,state.clock.logical_tick,state.last_event_sequence),(10,10,10))
        self.assertEqual((state.world_facts,state.character_states,state.relationships),((),(),()))
        self.assertEqual(state.threads[0].status,StoryThreadStatus.RESOLVED)
        text=state_dump(state)
        self.assertEqual(state,state_load(self.scope,10,10,10,state.projection_version,text))
        self.assertEqual(text,state_dump(replay_story(self.scope,events)))

    def test_remove_missing_and_closed_thread_rejected(self):
        with self.assertRaises(DomainError):
            reduce_story(StoryState(self.scope),self.event(K.WORLD_FACT_REMOVED,FactPayload('x','y'),1))
        thread=DomainId.new(IdKind.STORY_THREAD)
        opened=self.event(K.THREAD_OPENED,ThreadPayload(thread,'悬念',''),1)
        resolved=self.event(K.THREAD_CANCELLED,ThreadPayload(thread),2)
        state=replay_story(self.scope,(opened,resolved))
        with self.assertRaises(DomainError):
            reduce_story(state,self.event(K.THREAD_UPDATED,ThreadPayload(thread,None,'晚到'),3))
