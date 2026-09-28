"""Living 的合成安装验证；不接真实宿主。"""
from contextlib import closing
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import sqlite3
import unittest

from memory_fixture import MemoryFixture
from life_engine.domain import World, WorldScope, WorldKind, WorldStatus, WorldTimeline, DomainId, IdKind, Provenance, SourceType, RealityStatus, CanonStatus
from life_engine.world_repository import WorldSnapshot
from life_engine.living_domain import LivingContext, LivingError
from life_engine.living_policy import policy, time_context, local_instant
from life_engine.living_repository import LivingRepository
from life_engine.living_runtime import LivingRuntime


class LivingTests(MemoryFixture,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.now=datetime(2026,9,28,12,tzinfo=timezone.utc)
        self.scope=WorldScope(self.actor.owner_id,self.soul.soul_id,self.soul.soul_world_id,DomainId.new(IdKind.TIMELINE))
        prov=Provenance(SourceType.OWNER_COMMAND,'合成测试',self.now,self.actor,RealityStatus.FICTIONAL,CanonStatus.ACCEPTED)
        with self.world_repo.transaction() as tx:
            tx.add_world(WorldSnapshot(World(self.scope.world_id,self.scope.owner_id,self.scope.soul_id,WorldKind.SOUL,prov,WorldStatus.ACTIVE),WorldTimeline(self.scope,prov)))
        self.lr=LivingRepository(self.root,self.key,runtime_id=self.world_repo.runtime_id)
        self.ctx=LivingContext(self.actor,self.scope,self.lr.generation,'test')
        self.living=LivingRuntime(self.lr,clock=lambda:self.now)
        self.p=policy(quiet=[0,0],cooldown=0,recent_inbound=60)
        self.seq=0

    def op(self):
        self.seq+=1
        return 'op-'+str(self.seq)

    def enroll(self,**changes):
        self.p.update(changes)
        self.living.enroll(self.ctx,self.p,'本人合成目标',self.op())
        self.living.configure(self.ctx,self.rev(),self.op(),paused=False)

    def rev(self):
        return self.living.status(self.ctx)['root']['revision']

    def follow(self,**changes):
        args=dict(due=self.now,expires=self.now+timedelta(hours=4),topic='合成跟进',provenance='Owner 明确登记')
        args.update(changes)
        return self.living.create_followup(self.ctx,self.rev(),self.op(),**args)['id']

    def tick(self):
        for _ in range(20):
            out=self.living.tick(self.ctx,self.op())
            if out['result']!='RECOVERY_IN_PROGRESS': return out
        self.fail('恢复未收敛')

    def reserve(self):
        self.follow()
        out=self.tick()
        self.assertEqual(out['result'],'RESERVED')
        return out['intent_id']

    def prepare(self,i):
        self.living.prepare_intent(self.ctx,self.rev(),self.op(),i,'合成内容引用')

    def rows(self,table):
        with closing(sqlite3.connect(self.path)) as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute('SELECT * FROM '+table)]

    def test_c13_last_quota_execution(self):
        self.enroll(daily_cap=1,rolling_cap=1)
        i=self.reserve(); self.prepare(i)
        out=self.living.begin_attempt(self.ctx,self.rev(),self.op(),i)
        self.assertTrue(out['execute']); self.assertEqual(out['state'],'CLAIMED')
        self.assertEqual(len(self.rows('living_intents')),1)

    def test_c14_no_self_cooldown(self):
        for cooldown,spacing in [(9000,0),(0,9000),(9000,9000)]:
            with self.subTest(cooldown=cooldown,spacing=spacing):
                if not self.rows('living_roots'): self.enroll(cooldown=cooldown,spacing=spacing)
                else:
                    self.now+=timedelta(days=2)
                    self.p.update(cooldown=cooldown,spacing=spacing)
                    self.living.configure(self.ctx,self.rev(),self.op(),policy=self.p)
                i=self.reserve(); self.prepare(i); self.now+=timedelta(seconds=1)
                self.assertTrue(self.living.begin_attempt(self.ctx,self.rev(),self.op(),i)['execute'])

    def test_c15_other_intent_still_cooldown(self):
        self.enroll(cooldown=9000); self.reserve(); self.follow()
        self.assertEqual(self.tick()['result'],'SILENT')
        self.assertEqual(len(self.rows('living_intents')),1)
        self.assertIn('COOLDOWN',self.rows('living_decisions')[-1]['blockers'])

    def test_c16_policy_lower_cap_raise_spacing(self):
        self.enroll(daily_cap=2,rolling_cap=2)
        a=self.reserve(); b=self.reserve(); self.prepare(a); self.prepare(b)
        self.p.update(daily_cap=1,rolling_cap=1,cooldown=9000,spacing=9000)
        self.living.configure(self.ctx,self.rev(),self.op(),policy=self.p)
        for i in (a,b): self.assertTrue(self.living.begin_attempt(self.ctx,self.rev(),self.op(),i)['execute'])
        self.follow(); self.assertEqual(self.tick()['result'],'SILENT')
        self.assertEqual(len(self.rows('living_intents')),2)

    def test_c17_quiet_execution_cancels_without_refund(self):
        self.now=self.now.replace(hour=22,minute=58)
        self.enroll(quiet=[1380,480]); i=self.reserve(); self.prepare(i)
        self.now+=timedelta(minutes=4)
        self.assertFalse(self.living.begin_attempt(self.ctx,self.rev(),self.op(),i)['execute'])
        self.assertEqual(self.rows('living_intents')[0]['state'],'CANCELLED')
        self.assertEqual(self.rows('living_opportunities')[0]['state'],'OPEN')
        self.assertEqual(self.rows('living_attempts'),[])

    def test_c18_inbound_cancels_and_new_reservation(self):
        self.enroll(); i=self.reserve(); self.prepare(i)
        self.now+=timedelta(seconds=1)
        self.living.observe_inbound(self.ctx,self.rev(),self.op(),source='fixture',event_id='one',received_at=self.now)
        self.assertFalse(self.living.begin_attempt(self.ctx,self.rev(),self.op(),i)['execute'])
        self.now+=timedelta(seconds=61)
        j=self.tick()['intent_id']
        self.assertNotEqual(i,j); self.assertEqual(len(self.rows('living_intents')),2)
        self.assertNotEqual(*[x['decision_id'] for x in self.rows('living_intents')])


    def process(self, mode='tick', token='one', *, wait=True, intent=None):
        import subprocess,sys
        from pathlib import Path
        from life_engine.living_domain import scope_values
        config=dict(root=str(self.root),instance=self.key,path=str(self.path),runtime_id=self.lr.runtime_id,
                    principal=str(self.actor.principal_id),scope=scope_values(self.scope),now=self.now.isoformat(),
                    intent=intent,send_file=str(self.base/'fake-send.json'))
        path=self.base/('child-'+token+'.json');path.write_text(json.dumps(config),encoding='utf-8')
        child=subprocess.Popen([sys.executable,'-X','utf8',str(Path(__file__).with_name('living_process_fixture.py')),str(path),mode,token],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
        if not wait: return child
        out,err=child.communicate(timeout=30)
        if mode in ('before','inside','after','claimed','sent'):
            self.assertIn(child.returncode,(71,72,73,74),err);return None
        self.assertEqual(child.returncode,0,err)
        return json.loads(out)

    def activity(self,start=15,end=16):
        return self.living.reschedule_activity(self.ctx,self.rev(),self.op(),ident=None,
            start=self.now.replace(hour=start),end=self.now.replace(hour=end),name='咖啡店工作',location='合成咖啡店',category='CAFE')['id']

    def test_t01_midnight_local_budget_and_rolling(self):
        from living_time_fixture import zones
        with zones():
            self.now=self.now.replace(hour=15,minute=58)
            self.enroll(timezone='Asia/Shanghai',daily_cap=1,rolling_cap=1)
            self.reserve();self.now+=timedelta(minutes=3)
            self.follow();self.tick();self.tick()
            self.assertEqual([d['state'] for d in self.rows('living_days')],['CLOSED','OPEN'])
            self.assertEqual(len(self.rows('living_intents')),1)
            self.assertIn('ROLLING_BUDGET',self.rows('living_decisions')[-1]['blockers'])
            day=self.rows('living_days')[-1]
            self.assertEqual(datetime.fromtimestamp(day['start'],timezone.utc).hour,16)

    def test_t02_t03_fresh_process_activity_window(self):
        self.enroll();self.activity()
        spec=json.loads(self.rows('living_schedule')[-1]['local_spec'])
        self.assertEqual(spec['timezone'],'UTC');self.assertEqual(spec['fold'],0)
        self.assertEqual(spec['tzdata_fingerprint'],'UTC-fixed-offset-zero')
        self.now=self.now.replace(hour=14,minute=20);self.process()
        self.assertEqual(self.rows('living_activities')[0]['state'],'PLANNED')
        self.now=self.now.replace(hour=15,minute=40);self.process(token='two')
        a=self.rows('living_activities')[0]
        self.assertEqual(a['state'],'ACTIVE');self.assertEqual(a['activated_at'],self.now.timestamp())
        self.assertEqual(a['inferred'],1)
        self.assertEqual(self.living.status(self.ctx)['location']['category'],'CAFE')

    def test_t04_missed_activity_not_fabricated(self):
        self.enroll();self.activity();self.now=self.now.replace(hour=16,minute=10)
        self.process();a=self.rows('living_activities')[0]
        self.assertEqual(a['state'],'SKIPPED');self.assertIsNone(a['activated_at']);self.assertIsNone(a['ended_at'])

    def test_t05_active_completion(self):
        self.enroll();self.activity();self.now=self.now.replace(hour=15,minute=10);self.tick()
        self.now=self.now.replace(hour=17);self.process()
        a=self.rows('living_activities')[0]
        self.assertEqual(a['state'],'COMPLETED');self.assertEqual(a['ended_at'],self.now.timestamp())

    def test_t06_backlog_128_and_long_stop(self):
        contacts=[dict(start=n,end=n+1,reason='SOCIAL_IMPULSE',grace=60) for n in range(200)]
        self.enroll(contacts=contacts);self.now+=timedelta(days=5)
        result=self.living.tick(self.ctx,self.op())
        self.assertEqual(result['result'],'RECOVERY_IN_PROGRESS')
        self.assertEqual(self.rows('living_intents'),[])
        self.assertEqual(sum(x['state']!='PENDING' for x in self.rows('living_schedule')),128)
        self.tick()
        self.assertEqual(len(self.rows('living_days')),2)
        self.assertEqual(self.rows('living_intents'),[])

    def test_t07_t13_same_time_activity_and_overlap(self):
        self.enroll();self.activity(14,15);self.activity(15,16)
        with self.assertRaisesRegex(LivingError,'ACTIVITY_OVERLAP'):self.activity(14,16)
        self.now=self.now.replace(hour=14,minute=1);self.tick()
        self.now=self.now.replace(hour=15,minute=0);self.tick()
        acts=self.rows('living_activities');self.assertEqual([a['state'] for a in acts],['COMPLETED','ACTIVE'])
        self.living.cancel_activity(self.ctx,self.rev(),self.op(),acts[1]['id'])
        self.assertIsNone(self.living.status(self.ctx)['location'])

    def test_t08_timezone_change_cancels_unclaimed(self):
        from living_time_fixture import zones
        with zones():
            self.enroll(daily_cap=2,rolling_cap=2);self.activity();i=self.reserve();self.prepare(i)
            self.p.update(timezone='Asia/Shanghai')
            self.living.configure(self.ctx,self.rev(),self.op(),policy=self.p)
            self.assertEqual(self.rows('living_intents')[0]['state'],'CANCELLED')
            self.assertEqual(self.rows('living_days')[0]['state'],'PARTIAL')
            self.assertEqual(self.rows('living_roots')[0]['timezone_epoch'],1)
            self.assertEqual(self.rows('living_activities')[0]['state'],'CANCELLED')

    def test_t09_t10_dst_day_and_gap_fold(self):
        from living_time_fixture import zones
        from datetime import date
        with zones() as ny:
            p=policy(timezone='America/New_York',tzdata_source='fixture-2026')
            for d,hours in [(datetime(2026,3,8,12,tzinfo=timezone.utc),23),(datetime(2026,11,1,12,tzinfo=timezone.utc),25)]:
                t=time_context(d.timestamp(),p,0);self.assertEqual(t['end_utc']-t['start_utc'],hours*3600)
            self.assertEqual(local_instant(date(2026,3,8),150,ny),datetime(2026,3,8,7,tzinfo=timezone.utc).timestamp())
            self.assertEqual(local_instant(date(2026,11,1),90,ny),datetime(2026,11,1,5,30,tzinfo=timezone.utc).timestamp())
            self.now=datetime(2026,11,1,5,30,tzinfo=timezone.utc)
            self.enroll(timezone='America/New_York',tzdata_source='fixture-2026',daily_cap=1,rolling_cap=1,
                        contacts=[dict(start=90,end=91,reason='MORNING_GREETING',grace=7200)])
            self.tick();self.now+=timedelta(hours=1);self.tick()
            self.assertEqual(len(self.rows('living_intents')),1)
            self.assertEqual(self.living.status(self.ctx)['time']['fold'],1)

    def test_t11_t12_tzdata_clock_regression(self):
        self.enroll();self.tick();before=self.rows('living_roots')
        self.now-=timedelta(seconds=1)
        with self.assertRaisesRegex(LivingError,'CLOCK_REGRESSION'):self.living.tick(self.ctx,self.op())
        self.assertEqual(before,self.rows('living_roots'))
        self.now+=timedelta(seconds=1);self.p['tzdata_source']='explicit-new-source'
        self.living.configure(self.ctx,self.rev(),self.op(),policy=self.p)
        self.assertEqual(self.rows('living_roots')[0]['timezone_epoch'],1)

    def test_c01_c05_c07_decision_followup_idempotency(self):
        self.enroll(cooldown=9000);self.assertEqual(self.tick()['result'],'SILENT')
        self.reserve();self.follow();self.tick()
        count=len(self.rows('living_decisions'));self.tick();self.tick()
        self.assertEqual(count,len(self.rows('living_decisions')))
        op=self.op();expected=self.rev();args=dict(due=self.now,expires=self.now+timedelta(hours=4),topic='约定',provenance='Owner')
        a=self.living.create_followup(self.ctx,expected,op,**args)
        self.assertEqual(a,self.living.create_followup(self.ctx,expected,op,**args))
        self.living.resolve_followup(self.ctx,self.rev(),self.op(),a['id'])
        self.assertEqual(self.rows('living_followups')[-1]['state'],'RESOLVED')

    def test_c02_quiet_boundary(self):
        self.now=self.now.replace(hour=7,minute=59)
        self.enroll(quiet=[1380,480]);self.follow();self.assertEqual(self.tick()['result'],'SILENT')
        d=self.rows('living_decisions')[-1];self.assertEqual(d['primary_blocker'],'QUIET_HOURS')
        self.assertEqual(d['next_check'],self.now.replace(hour=8,minute=0).timestamp())
        self.now=self.now.replace(hour=8,minute=0);self.assertEqual(self.tick()['result'],'RESERVED')

    def test_c10_assistant_only_explicit_followup(self):
        self.enroll(mode='assistant',contacts=[dict(start=720,end=721,reason='SOCIAL_IMPULSE')],
                    routine=[dict(start=720,end=780,name='工作',location='公司',category='WORK')])
        self.assertEqual(self.tick()['result'],'SILENT');self.assertEqual(self.rows('living_activities'),[])
        self.reserve()
        self.follow(reason='USER_PROMISED_FOLLOWUP');self.tick()
        self.assertIn('USER_PROMISED_FOLLOWUP',[o['reason'] for o in self.rows('living_opportunities')])
        with self.assertRaisesRegex(LivingError,'INVALID_REASON'):self.follow(reason='MODEL_GUESS')

    def test_c11_c12_media_opportunities_no_jobs(self):
        self.enroll(photo=True,contacts=[dict(start=720,end=721,reason='PHOTO_SHARING',photo=True)])
        self.tick();self.tick()
        opps=self.rows('living_opportunities')
        self.assertEqual(sum(o['kind']=='PHOTO' for o in opps),1)
        self.assertEqual(sum(o['kind']=='VOICE' for o in opps),0)
        self.assertEqual(self.rows('photos'),[])
        self.p['voice']=True;self.living.configure(self.ctx,self.rev(),self.op(),policy=self.p)
        self.now+=timedelta(days=1);self.tick();self.tick()
        self.assertEqual(sum(o['kind']=='VOICE' for o in self.rows('living_opportunities')),1)
        self.assertEqual(self.rows('photos'),[])

    def test_p01_p02_two_process_quota(self):
        self.enroll(daily_cap=1,rolling_cap=1);self.follow()
        self.tick_preparation_only()
        children=[self.process(token=str(i),wait=False) for i in range(2)]
        for child in children:
            out,err=child.communicate(timeout=30);self.assertEqual(child.returncode,0,err)
        self.assertEqual(len(self.rows('living_intents')),1)
        count=len(self.rows('living_intents'));self.tick();self.assertEqual(len(self.rows('living_intents')),count)

    def tick_preparation_only(self):
        self.assertEqual(self.living.tick(self.ctx,self.op())['result'],'RECOVERY_IN_PROGRESS')

    def test_p03_operation_revision_generation_conflicts(self):
        self.enroll();op=self.op();rev=self.rev()
        self.living.configure(self.ctx,rev,op,paused=True)
        with self.assertRaisesRegex(LivingError,'IDEMPOTENCY_CONFLICT'):self.living.configure(self.ctx,rev,op,paused=False)
        with self.assertRaisesRegex(LivingError,'REVISION_CONFLICT'):self.living.configure(self.ctx,rev,self.op(),paused=False)
        with self.assertRaisesRegex(LivingError,'GENERATION_STALE'):self.living.tick(replace(self.ctx,generation='old'),self.op())

    def test_p04_crash_before_inside_after_commit(self):
        self.enroll();self.follow();self.tick_preparation_only()
        before=self.rows('living_roots')
        self.process('before');self.process('inside')
        self.assertEqual(before,self.rows('living_roots'));self.assertEqual(self.rows('living_intents'),[])
        self.process('after');self.assertEqual(len(self.rows('living_intents')),1)
        self.process(token='retry');self.assertEqual(len(self.rows('living_intents')),1)

    def test_p05_claimed_crash_unknown_no_retry(self):
        self.enroll();i=self.reserve();self.prepare(i)
        self.process('claimed',intent=i)
        self.assertEqual(self.rows('living_attempts')[0]['state'],'CLAIMED')
        result=self.process('restart',token='new')
        self.assertEqual(result['result'],'RECONCILIATION_REQUIRED')
        self.assertEqual(self.rows('living_attempts')[0]['state'],'UNKNOWN')
        self.process('restart',token='again')
        self.assertEqual(len(self.rows('living_attempts')),1)

    def test_p05_send_before_db_result(self):
        self.enroll();i=self.reserve();self.prepare(i);self.process('sent',intent=i)
        self.assertTrue((self.base/'fake-send.json').is_file());self.process('restart',token='new')
        self.assertEqual(self.rows('living_attempts')[0]['state'],'UNKNOWN')
        self.assertEqual(self.rows('living_delivery_results'),[])

    def test_p06_p07_persisted_choice_across_processes(self):
        self.enroll(visual={'outfit':['蓝','红']},contacts=[dict(start=730,end=750,reason='SOCIAL_IMPULSE')])
        original=self.rows('living_choices');self.process();self.process(token='reload')
        self.assertEqual(original,self.rows('living_choices'))
        self.p['visual']={'outfit':['绿']};self.living.configure(self.ctx,self.rev(),self.op(),policy=self.p)
        self.tick();self.assertEqual(original,self.rows('living_choices'))

    def test_p08_restore_generation_fence(self):
        from memory_fixture import d
        self.enroll();self.reserve()
        backup=d.snapshot(self.root,d.registry(self.root),self.inst,reason='living-test')
        d.restore(self.root,self.key,backup)
        with self.assertRaisesRegex(LivingError,'GENERATION_STALE'):self.living.tick(self.ctx,self.op())
        reg=d.registry(self.root);path=d.state_home(self.root,reg['instances'][self.key])/'agents/synthetic/life.db'
        with closing(sqlite3.connect(path)) as db:
            self.assertEqual(db.execute('SELECT paused,reconciliation FROM living_roots').fetchone(),(1,1))
            self.assertEqual(db.execute('SELECT state FROM living_intents').fetchone()[0],'QUARANTINED')

    def test_p09_corruption_fail_closed(self):
        self.enroll(visual={'outfit':['蓝','红']})
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE living_choices SET value='\"篡改\"'");db.commit()
        with self.assertRaisesRegex(LivingError,'STATE_CORRUPT'):self.living.tick(self.ctx,self.op())
        self.assertEqual(self.rows('living_intents'),[])

    def test_p10_scope_and_closed_world_fail_closed(self):
        self.enroll()
        with self.assertRaisesRegex(LivingError,'SCOPE_MISMATCH'):self.living.tick(replace(self.ctx,scope=self.a.timeline.scope),self.op())
        with self.world_repo.transaction() as tx:
            w=tx.get_world(self.scope.world_id)
            tx.save_world(replace(w,world=replace(w.world,status=WorldStatus.SUSPENDED,revision=w.world.revision.next())),w.world.revision)
        with self.assertRaisesRegex(LivingError,'SCOPE_MISMATCH'):self.living.tick(self.ctx,self.op())

    def test_p12_activities_do_not_write_other_domains(self):
        tables=('world_memories','story_events','lore_books')
        with closing(sqlite3.connect(self.path)) as db:
            names={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue(set(tables)<=names)
        before={t:self.rows(t) for t in tables}
        self.enroll();self.activity();self.now=self.now.replace(hour=15);self.tick()
        self.assertEqual(before,{t:self.rows(t) for t in tables})

    def test_p16_schema8_legacy_until_enrollment(self):
        from life_engine.config import load
        from life_engine.store import Store
        from life_engine.engine import Engine
        cfg,_=load(self.data,'synthetic');engine=Engine(cfg,Store(self.path,'synthetic'))
        self.assertIsInstance(engine.status(self.now),dict)
        self.assertEqual(self.rows('living_roots'),[])

    def test_p11_snapshot_bound_readonly_revalidation(self):
        from life_engine.prompt import PromptSessionContext,PromptPurpose,TEMPLATE_VERSION
        from life_engine.memory import MemoryAudience,AudienceKind
        from life_engine.living_projection import query,revalidate
        self.enroll();self.tick()
        with self.world_repo.transaction() as tx:w=tx.get_world(self.scope.world_id)
        w=self.world.enter(self.actor,w.world.world_id,w.timeline.scope.timeline_id,None,w.world.revision,w.world.writer_epoch)
        b=w.sessions[-1]
        context=PromptSessionContext(self.actor,self.scope,b.session_id,b.writer_epoch,self.lr.runtime_id,self.lr.generation,
            MemoryAudience(AudienceKind.SOUL,self.scope.soul_id),w.world.revision,PromptPurpose.SOUL_RESPONSE)
        before=self.rows('living_roots');snap=query(self.living,context)
        self.assertLessEqual(len(snap.payload.encode()),8192);self.assertTrue(revalidate(self.living,context,snap))
        self.assertEqual(before,self.rows('living_roots'))
        self.assertEqual(TEMPLATE_VERSION,'SP-004K-prompt-v1')
        with self.assertRaisesRegex(LivingError,'UNSUPPORTED_PURPOSE'):query(self.living,replace(context,purpose=PromptPurpose.ROLEPLAY_RESPONSE))
        with self.assertRaisesRegex(LivingError,'BUDGET_INPUT'):query(self.living,context,maximum_bytes=32)
        self.living.configure(self.ctx,self.rev(),self.op(),paused=True)
        with self.assertRaisesRegex(LivingError,'SNAPSHOT_STALE'):revalidate(self.living,context,snap)
        snap=query(self.living,context);self.now+=timedelta(minutes=1)
        with self.assertRaisesRegex(LivingError,'SNAPSHOT_STALE'):revalidate(self.living,context,snap)
        with self.assertRaisesRegex(LivingError,'SNAPSHOT_UNTRUSTED'):revalidate(LivingRuntime(self.lr,clock=lambda:self.now),context,snap)

    def test_c08_c09_verified_fake_delivery_only(self):
        self.enroll();i=self.reserve();self.prepare(i)
        a=self.living.begin_attempt(self.ctx,self.rev(),self.op(),i)['attempt_id']
        with self.assertRaisesRegex(LivingError,'RECEIPT_UNVERIFIED'):
            self.living.record_delivery(self.ctx,self.rev(),self.op(),a,{'state':'ACKNOWLEDGED'})
        class FixtureValidator:
            def verify(_,value):return value
        self.living.delivery_validator=FixtureValidator()
        evidence=dict(attempt_id=a,target='本人合成目标',state='SENT',message_id='fake-1',sent_at=self.now.timestamp(),source='fixture',event_id='sent')
        bad={**evidence,'state':'ACKNOWLEDGED'}
        self.assertEqual(self.living.record_delivery(self.ctx,self.rev(),self.op(),a,bad)['state'],'RECONCILIATION_REQUIRED')
        self.assertEqual(self.rows('living_roots')[0]['reconciliation'],1)
        self.living.record_delivery(self.ctx,self.rev(),self.op(),a,evidence)
        ack={**evidence,'state':'ACKNOWLEDGED','event_id':'ack'}
        self.living.record_delivery(self.ctx,self.rev(),self.op(),a,ack)
        self.assertEqual(self.rows('living_attempts')[0]['state'],'ACKNOWLEDGED')
        self.assertEqual(self.rows('living_followups')[0]['state'],'OPEN')
        self.assertFalse(self.living.begin_attempt(self.ctx,self.rev(),self.op(),i)['execute'])

    def test_p14_handoff_preserves_and_fences(self):
        from life_engine.config import load
        from life_engine.store import Store
        from life_engine.engine import Engine
        cfg,_=load(self.data,'synthetic');cfg['timezone']='UTC'
        (self.data/'agents/synthetic/agent.json').write_text(json.dumps(cfg),encoding='utf-8')
        store=Store(self.path,'synthetic');engine=Engine(cfg,store)
        engine.status(self.now)
        plan=json.loads(self.rows('days')[0]['plan'])
        loop=store.loop_add(self.now.timestamp(),'旧跟进',None)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO contacts(id,day,slot,at,status,payload) VALUES(?,?,?,?,?,?)",('old',self.now.date().isoformat(),'slot',self.now.timestamp(),'claimed','{}'));db.commit()
        self.p['timezone']='UTC'
        op=self.op();args=dict(legacy_plan=plan,loop_mapping={str(loop):dict(due=self.now.timestamp(),expires=(self.now+timedelta(hours=1)).timestamp())})
        from unittest.mock import patch
        with patch('life_engine.config.tz',return_value=timezone.utc):
            result=self.living.enroll(self.ctx,self.p,'本人合成目标',op,**args)
            self.assertEqual(result,self.living.enroll(self.ctx,self.p,'本人合成目标',op,**args))
        self.assertEqual(json.loads(self.rows('living_days')[0]['visual']),plan['visual'])
        self.assertEqual(len(self.rows('living_intents')),1);self.assertEqual(self.rows('living_intents')[0]['state'],'QUARANTINED')
        self.assertEqual(len(self.rows('living_followups')),1);self.assertEqual(self.rows('living_attempts'),[])
        for action in [lambda:engine.wake(self.now),lambda:store.prepare('old','文本'),lambda:store.loop_add(self.now.timestamp(),'新',None)]:
            with self.assertRaisesRegex(LivingError,'LIVING_HANDOFF_REQUIRED'):action()

    def test_t14_observation_expiry_and_special_date(self):
        self.enroll(region='synthetic');self.assertEqual(self.living.observation_context(self.ctx)['WEATHER']['status'],'UNKNOWN')
        self.living.observe_environment(self.ctx,self.rev(),self.op(),kind='WEATHER',provider='fixture',event_id='rain',observed=self.now,
            fetched=self.now,expires=self.now+timedelta(minutes=1),summary='合成降雨',region='synthetic')
        self.assertEqual(self.living.observation_context(self.ctx)['WEATHER']['status'],'VALID')
        self.now+=timedelta(minutes=2)
        self.assertEqual(self.living.observation_context(self.ctx)['WEATHER'],dict(status='STALE',id=self.rows('living_observations')[0]['id'],expires=self.rows('living_observations')[0]['expires'],summary=None))
        self.tick();self.assertEqual(self.rows('living_intents'),[])
        p=policy(special_dates=['02-29'])
        for year,month,day,result in [(2024,2,29,True),(2026,3,1,False),(2026,2,28,False)]:
            self.assertEqual(time_context(datetime(year,month,day,tzinfo=timezone.utc).timestamp(),p,0)['special_date'],result)

    def test_c03_combined_blockers_and_verified_outbound(self):
        self.enroll(cooldown=300,spacing=600,recent_inbound=120,recent_outbound=900)
        i=self.reserve();self.prepare(i);a=self.living.begin_attempt(self.ctx,self.rev(),self.op(),i)['attempt_id']
        class Fixture:
            def verify(_,e):return e
        self.living.delivery_validator=Fixture()
        self.living.record_delivery(self.ctx,self.rev(),self.op(),a,dict(attempt_id=a,target='本人合成目标',state='SENT',message_id='fixture-only',sent_at=self.now.timestamp(),source='fixture',event_id='1'))
        self.living.observe_inbound(self.ctx,self.rev(),self.op(),source='fixture',event_id='1',received_at=self.now)
        self.follow();self.tick();decision=self.rows('living_decisions')[-1]
        self.assertEqual(json.loads(decision['blockers']),['COOLDOWN','RECENT_INBOUND','RECENT_OUTBOUND'])
        self.assertEqual(decision['next_check'],self.now.timestamp()+900)
        self.process(token='outbound');self.assertEqual(len(self.rows('living_intents')),1)

    def test_c17_c18_expired_intent_never_reopens(self):
        self.enroll();self.follow(expires=self.now+timedelta(seconds=2));i=self.tick()['intent_id'];self.prepare(i)
        self.now+=timedelta(seconds=3)
        self.living.observe_inbound(self.ctx,self.rev(),self.op(),source='fixture',event_id='late',received_at=self.now)
        out=self.living.begin_attempt(self.ctx,self.rev(),self.op(),i)
        self.assertFalse(out['execute']);self.assertEqual(self.rows('living_intents')[0]['state'],'EXPIRED')
        self.assertEqual(self.rows('living_opportunities')[0]['state'],'EXPIRED');self.assertEqual(self.rows('living_attempts'),[])
        self.tick();self.assertEqual(len(self.rows('living_intents')),1)

    def test_p10_scope_race_same_sqlite_transaction(self):
        self.enroll();self.follow();self.tick_preparation_only()
        children=[self.process('scope','scope',wait=False),self.process('tick','tick',wait=False)]
        results=[]
        for child in children:
            out,err=child.communicate(timeout=30);results.append((child.returncode,err))
        self.assertEqual(results[0][0],0,results)
        self.assertIn(results[1][0],(0,1))
        if results[1][0]:self.assertIn('SCOPE_MISMATCH',results[1][1])
        self.assertLessEqual(len(self.rows('living_intents')),1)
        with self.assertRaisesRegex(LivingError,'SCOPE_MISMATCH'):self.living.tick(self.ctx,self.op())

    def test_p09_doctor_structural_corruption_matrix(self):
        from life_engine.living_repository import validate_living_data
        self.enroll(visual={'outfit':['蓝']});self.activity();self.reserve()
        damages=["UPDATE living_roots SET revision=revision+1",
                 "UPDATE living_schedule SET subject='missing'",
                 "UPDATE living_activities SET location_id='missing'",
                 "UPDATE living_days SET epoch=99",
                 "UPDATE living_decisions SET input_version='tampered'",
                 "UPDATE living_operations SET receipt='{}'"]
        for sql in damages:
            with self.subTest(sql=sql),closing(sqlite3.connect(self.path)) as db:
                db.execute('BEGIN');db.execute(sql)
                with self.assertRaisesRegex(LivingError,'STATE_CORRUPT'):validate_living_data(db)
                db.rollback()
        self.tick()

    def test_t13_spontaneous_choice_persisted(self):
        self.enroll(spontaneous=True)
        args=dict(ident=None,start=self.now,end=self.now+timedelta(minutes=20),name='散步',location='公园',category='PARK',spontaneous=True)
        op=self.op();rev=self.rev();result=self.living.reschedule_activity(self.ctx,rev,op,**args)
        self.assertEqual(result,self.living.reschedule_activity(self.ctx,rev,op,**args))
        self.assertEqual(len(self.rows('living_choices')),1);self.tick()
        self.assertEqual(self.living.status(self.ctx)['location']['origin'],'FICTIONAL_ROLE_STATE')

    def test_t06_deterministic_recovery_partitions(self):
        import shutil
        contacts=[dict(start=n,end=n+1,reason='SOCIAL_IMPULSE',grace=60) for n in range(70)]
        self.enroll(contacts=contacts,visual={'outfit':['红','蓝']})
        backup=self.base/'same-input.db';shutil.copyfile(self.path,backup)
        self.now+=timedelta(days=2)
        self.tick()
        names=('living_days','living_activities','living_choices','living_schedule','living_opportunities','living_intents')
        first={n:self.rows(n) for n in names}
        shutil.copyfile(backup,self.path)
        self.living=LivingRuntime(self.lr,clock=lambda:self.now,recovery_limit=32)
        self.tick()
        self.assertEqual(first,{n:self.rows(n) for n in names})

    def test_t11_tzdata_change_requires_explicit_policy(self):
        from unittest.mock import patch
        import struct,zoneinfo
        import life_engine.living_policy as rules
        zone_dir=self.base/'tzdata';zone_file=zone_dir/'A1'/'Test'
        zone_file.parent.mkdir(parents=True)
        def tzif(offset):
            return b'TZif\0'+b'\0'*15+struct.pack('>6l',0,0,0,0,1,4)+struct.pack('>lbb',offset,0,0)+b'FIX\0'
        previous=zoneinfo.TZPATH
        zone_file.write_bytes(tzif(3600))
        try:
            zoneinfo.reset_tzpath([str(zone_dir)])
            with patch.object(rules,'TZPATH',(str(zone_dir),)):
                cached=zoneinfo.ZoneInfo('A1/Test')
                self.enroll(timezone='A1/Test')
                self.assertEqual(self.living.status(self.ctx)['time']['utc_offset'],3600)
                rev=self.rev();zone_file.write_bytes(tzif(7200))
                with self.assertRaisesRegex(LivingError,'TZDATA_REVALIDATION_REQUIRED'):self.living.tick(self.ctx,self.op())
                self.living.configure(self.ctx,rev,self.op(),policy=self.p)
                self.assertEqual(self.rows('living_roots')[0]['timezone_epoch'],1)
                self.assertEqual(self.living.status(self.ctx)['time']['utc_offset'],7200)
                self.assertEqual(cached.utcoffset(self.now).total_seconds(),3600)
        finally:
            zoneinfo.reset_tzpath(previous)
            zoneinfo.ZoneInfo.clear_cache(only_keys=['A1/Test'])

    def test_c16_each_reservation_rule_change(self):
        self.enroll(daily_cap=2,rolling_cap=2)
        for change in [dict(daily_cap=1),dict(rolling_cap=1),dict(cooldown=9000),dict(spacing=9000)]:
            with self.subTest(change=change):
                self.now+=timedelta(days=2)
                self.p.update(daily_cap=2,rolling_cap=2,cooldown=0,spacing=0)
                self.living.configure(self.ctx,self.rev(),self.op(),policy=self.p)
                a=self.reserve();b=self.reserve();self.prepare(a);self.prepare(b)
                self.p.update(change);self.living.configure(self.ctx,self.rev(),self.op(),policy=self.p)
                for intent in (a,b):self.assertTrue(self.living.begin_attempt(self.ctx,self.rev(),self.op(),intent)['execute'])
                before=len(self.rows('living_intents'));self.follow();self.tick()
                self.assertEqual(len(self.rows('living_intents')),before)

    def test_c18_reopened_opportunity_two_processes(self):
        self.enroll();i=self.reserve();self.prepare(i)
        self.living.observe_inbound(self.ctx,self.rev(),self.op(),source='fixture',event_id='race',received_at=self.now)
        self.living.begin_attempt(self.ctx,self.rev(),self.op(),i);self.now+=timedelta(seconds=61)
        children=[self.process(token='reopen-'+str(n),wait=False) for n in range(2)]
        for child in children:
            out,err=child.communicate(timeout=30);self.assertEqual(child.returncode,0,err)
        intents=self.rows('living_intents')
        self.assertEqual(len(intents),2);self.assertEqual(sum(i['state']=='DECIDED' for i in intents),1)
        self.assertEqual(self.rows('living_attempts'),[])

    def test_c11_media_budget_expiry(self):
        self.enroll(photo=True,daily_cap=0,contacts=[dict(start=720,end=721,reason='PHOTO_SHARING',photo=True,grace=60)])
        self.tick();self.tick();self.assertEqual(self.rows('living_intents'),[])
        self.assertEqual(sum(o['kind']=='PHOTO' for o in self.rows('living_opportunities')),1)
        self.now+=timedelta(minutes=2);self.tick()
        self.assertTrue(all(o['state']=='EXPIRED' for o in self.rows('living_opportunities')))
        self.assertEqual(self.rows('photos'),[])

    def test_p06_independent_choice_order(self):
        import shutil
        self.enroll();backup=self.base/'choice-input.db';shutil.copyfile(self.path,backup)
        def choose(event):
            return self.living._command(self.ctx,self.rev(),self.op(),'fixture-choice',event,
                lambda db,r,p,at:dict(choice=self.living._choice(db,r,p,event,'fixture',['红','蓝','绿'])))
        choose('a');choose('b');first=sorted(self.rows('living_choices'),key=lambda x:x['id'])
        shutil.copyfile(backup,self.path);choose('b');choose('a')
        self.assertEqual(first,sorted(self.rows('living_choices'),key=lambda x:x['id']))

    def test_c05_pause_suppression_retains_opportunity(self):
        self.enroll();self.follow();self.living.configure(self.ctx,self.rev(),self.op(),paused=True)
        self.tick();before=len(self.rows('living_decisions'));self.tick()
        self.assertEqual(self.rows('living_opportunities')[0]['state'],'OPEN')
        self.assertIsNone(self.rows('living_decisions')[0]['next_check'])
        self.assertEqual(len(self.rows('living_decisions')),before)
        self.living.configure(self.ctx,self.rev(),self.op(),paused=False)
        self.assertEqual(self.tick()['result'],'RESERVED')

    def test_t13_activity_recreate_cancelled_window(self):
        self.enroll();old=self.activity()
        self.living.cancel_activity(self.ctx,self.rev(),self.op(),old)
        new=self.activity()
        self.assertNotEqual(old,new)
        self.assertEqual([r['state'] for r in self.rows('living_activities')],['CANCELLED','PLANNED'])

    def test_c11_photo_cancel_tracks_activity(self):
        self.enroll(photo=True,routine=[dict(start=780,end=840,name='咖啡店',location='咖啡店',category='CAFE')],
            contacts=[dict(start=790,end=791,reason='PHOTO_SHARING',photo=True)])
        activity=self.rows('living_activities')[0]['id']
        self.living.cancel_activity(self.ctx,self.rev(),self.op(),activity)
        photo=next(r for r in self.rows('living_opportunities') if r['kind']=='PHOTO')
        self.assertEqual(photo['state'],'CANCELLED')
        self.now=self.now.replace(hour=13,minute=10);self.tick()
        self.assertEqual(self.rows('living_intents'),[])
