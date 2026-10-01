"""持久 Living Core；无网络、模型、媒体或宿主调用。"""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
from uuid import uuid4
from zoneinfo import ZoneInfo

from .domain import WorldKind, WorldStatus, BindingStatus
from .living_domain import (LivingContext, LivingTickContext, LivingError, canonical, fingerprint,
                            instant, text, scope_values, fail, REASONS)
from .living_policy import validate_policy, time_context, quiet_until, local_instant, zone as timezone_info, zone_fingerprint
from .living_repository import state_digest
from .world_sqlite_repository import _SQLiteTransaction


def insert(db, table, **values):
    if table=='living_operations': values['receipt_fingerprint']=fingerprint(json.loads(values['receipt']))
    db.execute(f"INSERT INTO {table} ({','.join(values)}) VALUES ({','.join('?' for _ in values)})",tuple(values.values()))


def one(db, table, root, ident):
    row=db.execute(f'SELECT * FROM {table} WHERE root_id=? AND id=?',(root,ident)).fetchone()
    if row is None: fail('NOT_FOUND')
    return dict(row)


def finish(db, root, at, action, detail):
    db.execute('UPDATE living_roots SET revision=revision+1 WHERE root_id=?',(root,))
    rev=db.execute('SELECT revision FROM living_roots WHERE root_id=?',(root,)).fetchone()[0]
    change=dict(detail=detail,state_digest=state_digest(db,root))
    insert(db,'living_transitions',root_id=root,revision=rev,previous_revision=rev-1,at=at,
           action=action,changes=canonical(change),fingerprint=fingerprint(change))
    return rev


class LivingRuntime:
    def query_operation_recovery(self, context, request):
        """受信只读 durable operation 查询；永不返回 execution qualification。"""
        from .living_recovery import query_operation_recovery
        return query_operation_recovery(self, context, request)

    def __init__(self, repository, *, clock=None, delivery_validator=None, recovery_limit=128):
        if type(recovery_limit) is not int or not 1<=recovery_limit<=128: fail('INVALID_ARGUMENT')
        self.repository=repository
        self.clock=clock or (lambda:datetime.now(timezone.utc))
        self.delivery_validator=delivery_validator
        self.recovery_limit=recovery_limit
        self._snapshot_key=secrets.token_bytes(32)

    def _authorize(self, db, context, *, tick=False):
        if type(context) not in ((LivingContext,LivingTickContext) if tick else (LivingContext,)):
            fail('AUTHORIZATION_DENIED')
        if context.generation!=self.repository.generation: fail('GENERATION_STALE')
        world=_SQLiteTransaction(db); w=world.get_world(context.scope.world_id)
        if w.timeline.scope!=context.scope or w.world.kind is not WorldKind.SOUL or w.world.status is not WorldStatus.ACTIVE:
            fail('SCOPE_MISMATCH')
        if type(context) is LivingContext:
            if context.principal.owner_id!=context.scope.owner_id: fail('SCOPE_MISMATCH')
            if context.session is not None:
                s=context.session; b=world.get_session(s.session_id)
                if (b.principal!=context.principal or b.scope!=context.scope or b.status is not BindingStatus.OPEN
                    or b.writer_epoch!=s.writer_epoch or w.world.writer_epoch!=s.writer_epoch): fail('SESSION_STALE')
                if s.world_revision!=w.world.revision: fail('WORLD_STALE')
        elif context.instance_id!=self.repository.instance_id:
            fail('SCOPE_MISMATCH')
        return w

    def _root(self, db, context, at, *, tick=False):
        self._authorize(db,context,tick=tick)
        r=db.execute('SELECT * FROM living_roots WHERE instance_id=?',(self.repository.instance_id,)).fetchone()
        if not r: fail('LIVING_BINDING_REQUIRED')
        r=dict(r)
        if tuple(r[k] for k in ('owner_id','soul_id','world_id','timeline_id'))!=scope_values(context.scope): fail('SCOPE_MISMATCH')
        if r['generation']!=context.generation: fail('GENERATION_STALE')
        if r['last_evaluated_at'] is not None and at<r['last_evaluated_at']: fail('CLOCK_REGRESSION')
        if type(context) is LivingTickContext and context.policy_revision!=r['policy_revision']: fail('REVISION_CONFLICT')
        return r

    def _policy(self, db, r, *, updating=False):
        result=json.loads(db.execute('SELECT payload FROM living_policies WHERE root_id=? AND revision=?',
                                    (r['root_id'],r['policy_revision'])).fetchone()[0])
        if not updating and result['tzdata_fingerprint']!=zone_fingerprint(result['timezone']): fail('TZDATA_REVALIDATION_REQUIRED')
        return result

    def _command(self, ctx, expected, operation, action, payload, fn, *, tick=False):
        if type(ctx) not in ((LivingContext,LivingTickContext) if tick else (LivingContext,)):
            fail('AUTHORIZATION_DENIED')
        if not tick and (type(expected) is not int or expected<0): fail('REVISION_CONFLICT')
        text(operation); at=instant(self.clock())
        request=[action,payload,scope_values(ctx.scope),str(ctx.principal.principal_id) if type(ctx) is LivingContext else 'tick']
        stamp=fingerprint(request)
        with self.repository.transaction() as db:
            r=self._root(db,ctx,at,tick=tick); rid=r['root_id']
            key=(rid,ctx.generation,ctx.producer,operation)
            previous=db.execute('SELECT * FROM living_operations WHERE root_id=? AND generation=? AND producer=? AND operation_id=?',key).fetchone()
            if previous:
                if previous['fingerprint']!=stamp: fail('IDEMPOTENCY_CONFLICT')
                result=json.loads(previous['receipt'])
                if action=='begin_attempt': result['execute']=False
                return result
            if expected is not None and expected!=r['revision']: fail('REVISION_CONFLICT')
            result=fn(db,r,self._policy(db,r,updating=action=='configure'),at)
            db.execute('UPDATE living_roots SET last_evaluated_at=? WHERE root_id=?',(at,rid))
            rev=finish(db,rid,at,action,payload)
            result={**result,'revision':rev}
            insert(db,'living_operations',root_id=rid,generation=ctx.generation,producer=ctx.producer,
                   operation_id=operation,payload=canonical(request),fingerprint=stamp,receipt=canonical(result),revision=rev)
            return result

    def enroll(self, ctx, policy, target, operation, *, legacy_plan=None, loop_mapping=None):
        """显式 Owner enrollment；legacy 输入须由部署层核对当前配置后提供。"""
        text(operation); text(target); p=validate_policy({**policy,'tzdata_fingerprint':zone_fingerprint(policy['timezone'])}); at=instant(self.clock())
        mapping=loop_mapping or {}
        with self.repository.transaction() as db:
            self._authorize(db,ctx)
            if ctx.session is not None: fail('AUTHORIZATION_DENIED')
            existing=db.execute('SELECT root_id FROM living_roots WHERE instance_id=?',(self.repository.instance_id,)).fetchone()
            request=[scope_values(ctx.scope),p,target,legacy_plan,mapping]
            if existing:
                row=db.execute("SELECT * FROM living_operations WHERE root_id=? AND operation_id=? AND producer=?",
                               (existing[0],operation,ctx.producer)).fetchone()
                if row and row['fingerprint']==fingerprint(request): return json.loads(row['receipt'])
                fail('IDEMPOTENCY_CONFLICT')
            # management 锁覆盖安装内所有实例的唯一 Scope 校验。
            from .durable import registry,state_home
            import sqlite3
            from contextlib import closing
            reg=registry(self.repository.root)
            for key,inst in reg['instances'].items():
                if key==self.repository.instance_id: continue
                path=state_home(self.repository.root,inst)/'agents'/inst['agent_id']/'life.db'
                with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as other:
                    if other.execute('SELECT 1 FROM living_roots WHERE owner_id=? AND soul_id=? AND world_id=? AND timeline_id=?',scope_values(ctx.scope)).fetchone(): fail('SCOPE_ALREADY_ENROLLED')
            rid=uuid4().hex
            insert(db,'living_roots',root_id=rid,instance_id=self.repository.instance_id,
                **dict(zip(('owner_id','soul_id','world_id','timeline_id'),scope_values(ctx.scope))),
                generation=ctx.generation,revision=0,policy_revision=1,timezone_epoch=0,enabled=1,paused=1,
                last_evaluated_at=at,recovery_cursor=None,reconciliation=0,target=target)
            insert(db,'living_policies',root_id=rid,revision=1,payload=canonical(p),fingerprint=fingerprint(p))
            r=dict(db.execute('SELECT * FROM living_roots WHERE root_id=?',(rid,)).fetchone())
            day=self._day(db,r,p,at,legacy_plan=legacy_plan)
            if db.execute('SELECT 1 FROM days LIMIT 1').fetchone():
                from .config import load
                cfg,_=load(self.repository.path.parents[2],self.repository.path.parent.name)
                if cfg['timezone']!=p['timezone']: fail('LEGACY_HANDOFF_REQUIRED')
                if legacy_plan is not None and legacy_plan.get('day')!=day['local_date']: fail('LEGACY_HANDOFF_REQUIRED')
            stored=db.execute('SELECT plan FROM days WHERE day=?',(day['local_date'],)).fetchone()
            if stored and (legacy_plan is None or json.loads(stored[0])!=legacy_plan): fail('LEGACY_HANDOFF_REQUIRED')
            if legacy_plan is not None and (not stored or json.loads(stored[0])!=legacy_plan): fail('LEGACY_HANDOFF_REQUIRED')
            for row in db.execute('SELECT * FROM contacts ORDER BY at,id').fetchall():
                o=self._opportunity(db,r,day,'CONTACT','SOCIAL_IMPULSE','LEGACY',row['id'],row['id'],row['at'],row['at']+1,{})
                did=uuid4().hex
                insert(db,'living_decisions',id=did,root_id=rid,opportunity=o,input_version='LEGACY',policy_revision=1,
                       evaluated_at=row['at'],result='ALLOW',blockers='[]',primary_blocker=None,next_check=None)
                quarantine=row['status'] in ('claimed','prepared','unknown')
                insert(db,'living_intents',id=uuid4().hex,root_id=rid,opportunity=o,decision_id=did,generation=ctx.generation,
                       reserved_at=row['at'],expires=row['at']+1,state='QUARANTINED' if quarantine else 'CANCELLED',
                       target=target,prepared=canonical({'legacy_status':row['status'],'evidence':'UNVERIFIED_LEGACY'}),invalidated=1)
                db.execute("UPDATE living_opportunities SET state='CONSUMED' WHERE id=?",(o,))
                if quarantine: db.execute('UPDATE living_roots SET reconciliation=1 WHERE root_id=?',(rid,))
            for old_id,details in mapping.items():
                row=db.execute("SELECT * FROM loops WHERE id=? AND status='open'",(int(old_id),)).fetchone()
                if not row: fail('LEGACY_HANDOFF_REQUIRED')
                self._followup(db,r,str(old_id),details['due'],details['expires'],row['topic'],'LEGACY_EXPLICIT:'+str(old_id))
            db.execute("INSERT INTO meta VALUES('living_writer',?)",(rid,))
            rev=finish(db,rid,at,'enroll',{'legacy':legacy_plan is not None})
            result=dict(root_id=rid,revision=rev,paused=True)
            insert(db,'living_operations',root_id=rid,generation=ctx.generation,producer=ctx.producer,operation_id=operation,
                   payload=canonical(request),fingerprint=fingerprint(request),receipt=canonical(result),revision=rev)
            return result

    def _choice(self, db, r, p, event, purpose, candidates):
        key=(r['root_id'],event,purpose,p['algorithm'],r['policy_revision'])
        old=db.execute('SELECT * FROM living_choices WHERE root_id=? AND event=? AND purpose=? AND algorithm=? AND policy_revision=?',key).fetchone()
        values=sorted(candidates,key=canonical)
        inp=[list(key),values]; stamp=fingerprint(inp)
        if old:
            if old['input_fingerprint']!=stamp: fail('IDEMPOTENCY_CONFLICT')
            return old['id'],json.loads(old['value'])
        if not values: fail('INVALID_ARGUMENT')
        counter=0; cap=(1<<256)-((1<<256)%len(values))
        while True:
            raw=hmac.new(p['seed'].encode(),canonical([inp,counter]).encode(),hashlib.sha256).digest()
            n=int.from_bytes(raw,'big')
            if n<cap: break
            counter+=1
        value=values[n%len(values)]; ident=fingerprint(list(key))
        insert(db,'living_choices',id=ident,root_id=key[0],event=event,purpose=purpose,algorithm=p['algorithm'],policy_revision=r['policy_revision'],
               input=canonical(inp),input_fingerprint=stamp,value=canonical(value),fingerprint=fingerprint([stamp,value]))
        return ident,value

    def _schedule(self, db, r, subject_type, subject, action, due, expires, priority, local_spec=''):
        if not local_spec:
            resolved=time_context(due,self._policy(db,r),r['timezone_epoch'])
            local_spec=canonical({k:resolved[k] for k in ('timezone','timezone_epoch','local_date','local_time','utc_offset','fold','tzdata_source','tzdata_fingerprint')})
        key=[r['root_id'],subject,action]
        db.execute('INSERT OR IGNORE INTO living_schedule VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (fingerprint(key),r['root_id'],subject_type,subject,'once',action,priority,due,expires,local_spec,r['policy_revision'],'WINDOW', 'PENDING'))

    def _day(self, db, r, p, at, *, legacy_plan=None):
        t=time_context(at,p,r['timezone_epoch']); rid=r['root_id']
        old=db.execute('SELECT * FROM living_days WHERE root_id=? AND epoch=? AND local_date=?',(rid,r['timezone_epoch'],t['local_date'])).fetchone()
        if old: return dict(old)
        ident=fingerprint([rid,r['timezone_epoch'],t['local_date']]); visual={}
        if legacy_plan is not None: visual=legacy_plan['visual']
        elif p['mode']=='companion':
            for k,v in sorted(p['visual'].items()): visual[k]=self._choice(db,r,p,t['local_date'],k,v)[1]
        insert(db,'living_days',id=ident,root_id=rid,epoch=r['timezone_epoch'],local_date=t['local_date'],start=t['start_utc'],end=t['end_utc'],
               policy_revision=r['policy_revision'],revision=1,state='OPEN',updated=at,visual=canonical(visual))
        day=one(db,'living_days',rid,ident)
        self._schedule(db,r,'DAY',ident,'CLOSE',t['end_utc'],t['end_utc'],0)
        localday=datetime.fromisoformat(t['local_date']).date(); zone=timezone_info(p['timezone'])
        routine=p['routine'] if legacy_plan is None else legacy_plan['routine']
        if p['mode']=='companion':
            for i,item in enumerate(routine):
                def minute(x):
                    return int(x[:2])*60+int(x[3:]) if isinstance(x,str) else x
                start=local_instant(localday,minute(item['start']),zone); end=local_instant(localday,minute(item['end']),zone)
                if start>=end: continue
                name=item.get('name',item.get('activity','日常')); loc=item.get('location','未指定')
                self._activity(db,r,day,start,end,name,loc,item.get('category','OTHER'),'LEGACY' if legacy_plan else 'PLAN',at)
        contacts=p['contacts']
        if legacy_plan is not None:
            contacts=[dict(start=int(x['time'][:2])*60+int(x['time'][3:]),end=int(x['time'][:2])*60+int(x['time'][3:])+1,
                           reason='SOCIAL_IMPULSE',photo=x['photo']) for x in legacy_plan['slots']]
        if p['mode']=='companion':
            for i,c in enumerate(contacts):
                ref,minute=self._choice(db,r,p,ident,'contact:'+str(i),list(range(c['start'],c['end'])))
                eligible=local_instant(localday,minute,zone); expires=min(eligible+c.get('grace',3600),t['end_utc'])
                if eligible>=local_instant(localday,c['end'],zone): continue
                if eligible>=expires: continue
                oid=self._opportunity(db,r,day,'CONTACT',c['reason'],'CHOICE',ref,str(i),eligible,expires,{})
                if p['photo'] and c.get('photo',False):
                    activity=db.execute("SELECT id,location_id FROM living_activities WHERE day_id=? AND start<=? AND end>? AND state NOT IN ('CANCELLED','SKIPPED')",(ident,eligible,eligible)).fetchone()
                    self._opportunity(db,r,day,'PHOTO','PHOTO_SHARING','DAY',ident,'photo:'+str(i),eligible,expires,
                                      dict(visual=visual,continuity_identity=ident,contact=oid,theme=c.get('theme','日常'),
                                           activity=activity['id'] if activity else None,location=activity['location_id'] if activity else None))
                if p['voice']:
                    self._opportunity(db,r,day,'VOICE',c['reason'],'DAY',ident,'voice:'+str(i),eligible,expires,dict(contact=oid))
        return day

    def _activity(self, db, r, day, start, end, name, location, category, source, at):
        rid=r['root_id']; text(name); text(location)
        if start>=end or db.execute("SELECT 1 FROM living_activities WHERE root_id=? AND state NOT IN ('CANCELLED','SKIPPED') AND start<? AND end>?",(rid,end,start)).fetchone(): fail('ACTIVITY_OVERLAP')
        loc=fingerprint([location,category])
        revision=r['revision'] if source in ('OWNER','SPONTANEOUS') else 0
        ident=fingerprint([rid,day['id'],start,end,name,location,source,revision])
        db.execute('INSERT OR IGNORE INTO living_locations VALUES(?,?,?,?,?,?)',(loc,rid,1,category,location,'FICTIONAL_ROLE_STATE'))
        insert(db,'living_activities',id=ident,root_id=rid,day_id=day['id'],start=start,end=end,name=name,
               location_id=loc,location_revision=1,source=source,state='PLANNED',activated_at=None,ended_at=None,inferred=0,reason='')
        self._schedule(db,r,'ACTIVITY',ident,'ACTIVATE',start,end,1)
        self._schedule(db,r,'ACTIVITY',ident,'COMPLETE',end,end,0)
        db.execute('UPDATE living_days SET revision=revision+1,updated=? WHERE id=?',(at,day['id']))
        return ident

    def _opportunity(self, db, r, day, kind, reason, source_type, source_ref, occurrence, eligible, expires, payload):
        if reason not in REASONS or eligible>=expires: fail('INVALID_REASON')
        old=db.execute('SELECT id FROM living_opportunities WHERE root_id=? AND kind=? AND source_ref=? AND occurrence=?',
                       (r['root_id'],kind,source_ref,occurrence)).fetchone()
        if old: return old[0]
        ident=fingerprint([r['root_id'],kind,source_ref,occurrence])
        insert(db,'living_opportunities',id=ident,root_id=r['root_id'],day_id=day['id'],kind=kind,reason=reason,
               source_type=source_type,source_ref=source_ref,occurrence=occurrence,eligible=eligible,expires=expires,
               state='OPEN' if kind=='CONTACT' else 'PLANNED',revision=1,target=r['target'],payload=canonical(payload))
        self._schedule(db,r,'OPPORTUNITY',ident,'OFFER',eligible,expires,2 if kind=='CONTACT' else 3)
        self._schedule(db,r,'OPPORTUNITY',ident,'EXPIRE',expires,expires,0)
        return ident

    def _followup(self, db, r, key, due, expires, topic, provenance, reason='REMEMBERED_FOLLOWUP'):
        text(topic); text(provenance)
        if reason not in ('REMEMBERED_FOLLOWUP','USER_PROMISED_FOLLOWUP'): fail('INVALID_REASON')
        if due>=expires: fail('INVALID_ARGUMENT')
        ident=uuid4().hex
        insert(db,'living_followups',id=ident,root_id=r['root_id'],due=due,expires=expires,topic=topic,provenance=provenance,reason=reason,state='OPEN',source_key=key)
        return ident

    def create_followup(self, ctx, expected, operation, *, due, expires, topic, provenance, reason='REMEMBERED_FOLLOWUP'):
        payload=dict(due=instant(due),expires=instant(expires),topic=topic,provenance=provenance,reason=reason)
        return self._command(ctx,expected,operation,'followup',payload,
            lambda db,r,p,at:dict(id=self._followup(db,r,fingerprint([ctx.producer,operation]),**payload)))

    def resolve_followup(self, ctx, expected, operation, ident):
        def apply(db,r,p,at):
            one(db,'living_followups',r['root_id'],ident)
            db.execute("UPDATE living_followups SET state='RESOLVED' WHERE id=?",(ident,))
            return dict(id=ident)
        return self._command(ctx,expected,operation,'resolve',ident,apply)

    def cancel_followup(self, ctx, expected, operation, ident):
        def apply(db,r,p,at):
            one(db,'living_followups',r['root_id'],ident)
            db.execute("UPDATE living_followups SET state='CANCELLED' WHERE id=?",(ident,))
            return dict(id=ident)
        return self._command(ctx,expected,operation,'cancel_followup',ident,apply)

    def cancel_activity(self, ctx, expected, operation, ident):
        def apply(db,r,p,at):
            row=one(db,'living_activities',r['root_id'],ident)
            if row['state'] not in ('PLANNED','ACTIVE'): fail('INVALID_STATE')
            db.execute("UPDATE living_activities SET state='CANCELLED',ended_at=? WHERE id=?",(at,ident))
            db.execute('UPDATE living_days SET revision=revision+1,updated=? WHERE id=?',(at,row['day_id']))
            db.execute("UPDATE living_schedule SET state='CANCELLED' WHERE subject=? AND state='PENDING'",(ident,))
            self._cancel_activity_photos(db,r,ident)
            return dict(id=ident)
        return self._command(ctx,expected,operation,'cancel_activity',ident,apply)

    def _cancel_activity_photos(self, db, r, ident):
        rows=db.execute("SELECT id,payload FROM living_opportunities WHERE root_id=? AND kind='PHOTO' AND state IN ('PLANNED','OFFERED')",(r['root_id'],)).fetchall()
        for row in rows:
            if json.loads(row['payload']).get('activity')==ident:
                db.execute("UPDATE living_opportunities SET state='CANCELLED',revision=revision+1 WHERE id=?",(row['id'],))

    def reconcile(self, ctx, expected, operation, *, evidence_ref, blocked_until):
        """Owner 明确协调后保守暂停至指定水位；不退款、不重发旧 Attempt。"""
        if type(ctx) is not LivingContext or ctx.session is not None: fail('AUTHORIZATION_DENIED')
        text(evidence_ref); boundary=instant(blocked_until)
        def apply(db,r,p,at):
            minimum=max(at+86400,time_context(at,p,r['timezone_epoch'])['end_utc'],at+p['cooldown'],at+p['spacing'],at+p['recent_outbound'])
            if boundary < minimum: fail('INVALID_ARGUMENT')
            db.execute("UPDATE living_intents SET state='CANCELLED',invalidated=1 WHERE root_id=? AND state IN ('DECIDED','PREPARED','QUARANTINED')",(r['root_id'],))
            db.execute("UPDATE living_attempts SET state='UNKNOWN' WHERE root_id=? AND state='CLAIMED'",(r['root_id'],))
            # 明确协调水位保存在根，不使用可退还的预算 counter。
            db.execute('UPDATE living_roots SET reconciliation=0,reconcile_until=?,paused=1 WHERE root_id=?',(boundary,r['root_id']))
            return dict(reconciled=True,blocked_until=boundary)
        return self._command(ctx,expected,operation,'reconcile',[evidence_ref,boundary],apply)

    def configure(self, ctx, expected, operation, *, policy=None, paused=None, target=None):
        if type(ctx) is not LivingContext or ctx.session is not None: fail('AUTHORIZATION_DENIED')
        pnew=validate_policy({**policy,'tzdata_fingerprint':zone_fingerprint(policy['timezone'])}) if policy is not None else None
        def apply(db,r,p,at):
            rid=r['root_id']
            if paused is False and r['reconciliation']: fail('RECONCILIATION_REQUIRED')
            if paused is not None:
                if type(paused) is not bool: fail('INVALID_ARGUMENT')
                db.execute('UPDATE living_roots SET paused=? WHERE root_id=?',(int(paused),rid))
            if target is not None:
                text(target); db.execute('UPDATE living_roots SET target=? WHERE root_id=?',(target,rid))
            if pnew is not None:
                rev=r['policy_revision']+1
                insert(db,'living_policies',root_id=rid,revision=rev,payload=canonical(pnew),fingerprint=fingerprint(pnew))
                db.execute('UPDATE living_roots SET policy_revision=? WHERE root_id=?',(rev,rid))
                if (pnew['timezone'],pnew['tzdata_source'],pnew['tzdata_fingerprint'])!=(p['timezone'],p['tzdata_source'],p['tzdata_fingerprint']):
                    db.execute("UPDATE living_days SET state='PARTIAL' WHERE root_id=? AND state='OPEN'",(rid,))
                    db.execute("UPDATE living_schedule SET state='CANCELLED' WHERE root_id=? AND state='PENDING'",(rid,))
                    db.execute("UPDATE living_activities SET state='CANCELLED',ended_at=? WHERE root_id=? AND state IN ('ACTIVE','PLANNED')",(at,rid))
                    db.execute("UPDATE living_opportunities SET state='CANCELLED',revision=revision+1 WHERE root_id=? AND state IN ('OPEN','PLANNED','OFFERED')",(rid,))
                    db.execute("UPDATE living_intents SET state='CANCELLED' WHERE root_id=? AND state IN ('DECIDED','PREPARED')",(rid,))
                    db.execute('UPDATE living_roots SET timezone_epoch=timezone_epoch+1 WHERE root_id=?',(rid,))
                    r.update(policy_revision=rev,timezone_epoch=r['timezone_epoch']+1)
                    self._day(db,r,pnew,at)
                for kind,key in [('PHOTO','photo'),('VOICE','voice')]:
                    if not pnew[key]: db.execute("UPDATE living_opportunities SET state='CANCELLED' WHERE root_id=? AND kind=? AND state IN ('PLANNED','OFFERED')",(rid,kind))
            return dict(configured=True)
        return self._command(ctx,expected,operation,'configure',dict(policy=pnew,paused=paused,target=target),apply)

    def observe_inbound(self, ctx, expected, operation, *, source, event_id, received_at):
        stamp=instant(received_at); text(source); text(event_id)
        def apply(db,r,p,at):
            if stamp>at: fail('INVALID_CLOCK')
            key=(r['root_id'],source,event_id); digest=fingerprint([source,event_id,stamp])
            old=db.execute('SELECT fingerprint FROM living_inbound WHERE root_id=? AND source=? AND event_id=?',key).fetchone()
            if old and old[0]!=digest: fail('IDEMPOTENCY_CONFLICT')
            db.execute('INSERT OR IGNORE INTO living_inbound VALUES(?,?,?,?,?)',(*key,stamp,digest))
            return dict(observed=True)
        return self._command(ctx,expected,operation,'inbound',[source,event_id,stamp],apply)

    def observe_environment(self, ctx, expected, operation, *, kind, provider, event_id, observed, fetched, expires, summary, region):
        payload=dict(summary=text(summary),region=text(region),version=1)
        observed,fetched,expires=map(instant,(observed,fetched,expires))
        def apply(db,r,p,at):
            if kind not in ('WEATHER','HOLIDAY','SPECIAL_DATE') or not observed<=fetched<=at or expires<=fetched: fail('INVALID_ARGUMENT')
            limit=10800 if kind=='WEATHER' else 604800
            ident=uuid4().hex
            insert(db,'living_observations',id=ident,root_id=r['root_id'],kind=kind,provider=text(provider),event_id=text(event_id),
                   observed=observed,fetched=fetched,expires=min(expires,fetched+limit),payload=canonical(payload),fingerprint=fingerprint(payload))
            return dict(id=ident)
        return self._command(ctx,expected,operation,'environment',[kind,provider,event_id,observed,fetched,expires,payload],apply)

    def reschedule_activity(self, ctx, expected, operation, *, ident, start, end, name, location, category, spontaneous=False):
        start,end=instant(start),instant(end)
        def apply(db,r,p,at):
            if p['mode']!='companion' or start<at: fail('INVALID_ARGUMENT')
            if ident is not None:
                old=one(db,'living_activities',r['root_id'],ident)
                if old['state'] not in ('PLANNED','ACTIVE'): fail('INVALID_STATE')
                db.execute("UPDATE living_activities SET state='CANCELLED',ended_at=? WHERE id=?",(at,ident))
                db.execute('UPDATE living_days SET revision=revision+1,updated=? WHERE id=?',(at,old['day_id']))
                db.execute("UPDATE living_schedule SET state='CANCELLED' WHERE subject=? AND state='PENDING'",(ident,))
                self._cancel_activity_photos(db,r,ident)
            day=self._day(db,r,p,start)
            if spontaneous:
                if not p['spontaneous']: fail('POLICY_DENIED')
                self._choice(db,r,p,operation,'spontaneous',[[start,end,name,location,category]])
            if end>day['end']: fail('INVALID_ARGUMENT')
            return dict(id=self._activity(db,r,day,start,end,name,location,category,'SPONTANEOUS' if spontaneous else 'OWNER',at))
        return self._command(ctx,expected,operation,'activity',[ident,start,end,name,location,category,spontaneous],apply)

    def _reason(self, db,r,p,o,at):
        if o['reason'] not in REASONS: fail('INVALID_REASON')
        if p['mode']=='assistant' and o['reason'] not in ('REMEMBERED_FOLLOWUP','USER_PROMISED_FOLLOWUP'): return False
        if o['reason']=='PHOTO_SHARING':
            photos=db.execute("SELECT payload FROM living_opportunities WHERE root_id=? AND kind='PHOTO' AND state='OFFERED'",(r['root_id'],)).fetchall()
            if not p['photo'] or not any(json.loads(row['payload']).get('contact')==o['id'] for row in photos): return False
        required={'REMEMBERED_FOLLOWUP':'FOLLOWUP','USER_PROMISED_FOLLOWUP':'FOLLOWUP',
                  'WEATHER_EVENT':'OBSERVATION','HOLIDAY':'OBSERVATION','ACTIVITY_TRANSITION':'ACTIVITY'}
        if o['reason'] in required and o['source_type']!=required[o['reason']]: return False
        if o['source_type']=='FOLLOWUP':
            f=one(db,'living_followups',r['root_id'],o['source_ref']); return f['state']=='OPEN' and f['due']<=at<f['expires']
        if o['source_type']=='OBSERVATION':
            obs=one(db,'living_observations',r['root_id'],o['source_ref'])
            return obs['expires']>at and json.loads(obs['payload'])['region']==p['region']
        if o['source_type']=='ACTIVITY': return one(db,'living_activities',r['root_id'],o['source_ref'])['state']=='ACTIVE'
        if o['reason']=='LONG_SILENCE': return db.execute('SELECT 1 FROM living_inbound WHERE root_id=?',(r['root_id'],)).fetchone() is not None
        return o['source_type']!='LEGACY'

    def _blockers(self, db,r,p,o,at, *, execution=False):
        rid=r['root_id']; blocks=[]; until=[]
        def add(code,end=None):
            blocks.append(code)
            if end is not None: until.append(end)
        if r['reconciliation']: fail('RECONCILIATION_REQUIRED')
        if r.get('reconcile_until') is not None and at < r['reconcile_until']:
            add('RECONCILIATION_WATERMARK',r['reconcile_until'])
        if r['paused'] or not r['enabled']: add('PAUSED')
        if o['state'] in ('CANCELLED','EXPIRED') or at>=o['expires']: add('EXPIRED',o['expires'])
        q=quiet_until(at,p)
        if q is not None: add('QUIET_HOURS',q)
        t=time_context(at,p,r['timezone_epoch'])
        reservations=[x[0] for x in db.execute('SELECT reserved_at FROM living_intents WHERE root_id=? ORDER BY reserved_at',(rid,))]
        if not execution:
            day=[x for x in reservations if t['start_utc']<=x<t['end_utc']]
            rolling=[x for x in reservations if at-86400<x<=at]
            if len(day)>=p['daily_cap']: add('DAILY_BUDGET',t['end_utc'])
            if len(rolling)>=p['rolling_cap']:
                release=rolling[len(rolling)-p['rolling_cap']]+86400 if p['rolling_cap'] else o['expires']
                add('ROLLING_BUDGET',release)
            if reservations and at<reservations[-1]+max(p['cooldown'],p['spacing']): add('COOLDOWN',reservations[-1]+max(p['cooldown'],p['spacing']))
        inbound=db.execute('SELECT MAX(received_at) FROM living_inbound WHERE root_id=?',(rid,)).fetchone()[0]
        outbound=db.execute("SELECT MAX(sent_at) FROM living_attempts WHERE root_id=? AND state IN ('SENT','ACKNOWLEDGED')",(rid,)).fetchone()[0]
        if inbound is not None and at<inbound+p['recent_inbound']: add('RECENT_INBOUND',inbound+p['recent_inbound'])
        if outbound is not None and at<outbound+p['recent_outbound']: add('RECENT_OUTBOUND',outbound+p['recent_outbound'])
        if not self._reason(db,r,p,o,at): add('REASON_INVALID')
        if at<o['eligible']: add('NOT_ELIGIBLE',o['eligible'])
        next_check=min(max([o['eligible'],*until]),o['expires']) if blocks else None
        if 'PAUSED' in blocks or 'REASON_INVALID' in blocks: next_check=None
        # 摘要在相关边界之外稳定；跨界时 blockers/日期/水位必定变化。
        inp=[o['revision'],r['policy_revision'],r['paused'],r['enabled'],r['target'],blocks,next_check,
             inbound,outbound,reservations,t['local_date'],r['timezone_epoch']]
        return blocks,next_check,fingerprint(inp)

    def tick(self, ctx, operation=None):
        def apply(db,r,p,at):
            rid=r['root_id']
            # 新进程附着同一 World 代次不会假装接管旧进程的外部调用；恢复需显式新 runtime_id。
            stale=db.execute("SELECT id FROM living_attempts WHERE root_id=? AND state='CLAIMED' AND runtime_id<>?",(rid,self.repository.runtime_id)).fetchall()
            if stale:
                db.execute("UPDATE living_attempts SET state='UNKNOWN' WHERE root_id=? AND state='CLAIMED' AND runtime_id<>?",(rid,self.repository.runtime_id))
                db.execute('UPDATE living_roots SET reconciliation=1 WHERE root_id=?',(rid,)); r['reconciliation']=1
            limit=self.recovery_limit
            rows=db.execute("SELECT * FROM living_schedule WHERE root_id=? AND state='PENDING' AND due<=? ORDER BY due,priority,id LIMIT ?",(rid,at,limit+1)).fetchall()
            for s in rows[:limit]:
                if s['subject_type']=='DAY':
                    db.execute("UPDATE living_days SET state='CLOSED',updated=? WHERE id=? AND state='OPEN'",(at,s['subject']))
                elif s['subject_type']=='ACTIVITY':
                    a=one(db,'living_activities',rid,s['subject'])
                    if a['state']=='PLANNED':
                        if at>=a['end']: db.execute("UPDATE living_activities SET state='SKIPPED',reason='MISSED_WINDOW' WHERE id=?",(a['id'],))
                        elif a['start']<=at:
                            db.execute("UPDATE living_activities SET state='ACTIVE',activated_at=?,inferred=1 WHERE id=?",(at,a['id']))
                            day=one(db,'living_days',rid,a['day_id'])
                            if p['mode']=='companion':
                                self._opportunity(db,r,day,'CONTACT','ACTIVITY_TRANSITION','ACTIVITY',a['id'],'activate',at,min(at+900,a['end']),{})
                    elif a['state']=='ACTIVE' and at>=a['end']:
                        db.execute("UPDATE living_activities SET state='COMPLETED',ended_at=?,inferred=1,reason='INFERRED_ELAPSED' WHERE id=?",(at,a['id']))
                else:
                    o=one(db,'living_opportunities',rid,s['subject'])
                    if o['state']=='CONSUMED' and at>=o['expires']:
                        pending_intent=db.execute("SELECT id FROM living_intents WHERE opportunity=? AND state IN ('DECIDED','PREPARED')",(o['id'],)).fetchone()
                        if pending_intent:
                            db.execute("UPDATE living_intents SET state='EXPIRED' WHERE id=?",(pending_intent[0],))
                            db.execute("UPDATE living_opportunities SET state='EXPIRED',revision=revision+1 WHERE id=?",(o['id'],))
                    if o['state'] not in ('CONSUMED','CANCELLED','EXPIRED'):
                        if at>=o['expires']: db.execute("UPDATE living_opportunities SET state='EXPIRED',revision=revision+1 WHERE id=?",(o['id'],))
                        elif o['kind']!='CONTACT': db.execute("UPDATE living_opportunities SET state='OFFERED' WHERE id=?",(o['id'],))
                db.execute("UPDATE living_schedule SET state=? WHERE id=?",('EXPIRED' if at>s['expires'] else 'CONSUMED',s['id']))
            pending=len(rows)>limit
            db.execute('UPDATE living_roots SET recovery_cursor=? WHERE root_id=?',(rows[limit-1]['id'] if pending else None,rid))
            if pending: return dict(result='RECOVERY_IN_PROGRESS')
            day=self._day(db,r,p,at)
            for f in db.execute("SELECT * FROM living_followups WHERE root_id=? AND state='OPEN' AND due<? AND expires>? ORDER BY due,id",(rid,day['end'],at)).fetchall():
                self._opportunity(db,r,day,'CONTACT',f['reason'],'FOLLOWUP',f['id'],day['id'],max(f['due'],day['start']),min(f['expires'],day['end']),{})
            if p['mode']=='companion':
                for obs in db.execute('SELECT * FROM living_observations WHERE root_id=? AND expires>? ORDER BY observed,id',(rid,at)).fetchall():
                    if json.loads(obs['payload'])['region']!=p['region'] or p['region']=='UNKNOWN': continue
                    reason='WEATHER_EVENT' if obs['kind']=='WEATHER' else 'HOLIDAY'
                    self._opportunity(db,r,day,'CONTACT',reason,'OBSERVATION',obs['id'],day['id'],
                                      max(obs['fetched'],day['start']),min(obs['expires'],day['end']),{})
            if r['reconciliation']: return dict(result='RECONCILIATION_REQUIRED')
            # 新日新建的到期项必须在下一批先收敛，不能跨过 recovery gate。
            if db.execute("SELECT 1 FROM living_schedule WHERE root_id=? AND state='PENDING' AND due<=?",(rid,at)).fetchone(): return dict(result='RECOVERY_IN_PROGRESS')
            candidates=db.execute("SELECT * FROM living_opportunities WHERE root_id=? AND kind='CONTACT' AND state='OPEN' ORDER BY CASE WHEN source_type='FOLLOWUP' THEN 0 ELSE 1 END,expires,reason,id",(rid,)).fetchall()
            candidates=sorted(candidates,key=lambda o:(o['source_type']!='FOLLOWUP',o['expires'],REASONS.index(o['reason']),o['id']))
            for row in candidates:
                o=dict(row); blockers,nxt,inp=self._blockers(db,r,p,o,at)
                old=db.execute('SELECT id FROM living_decisions WHERE opportunity=? AND input_version=? AND policy_revision=?',(o['id'],inp,r['policy_revision'])).fetchone()
                if old: continue
                did=fingerprint([o['id'],inp,r['policy_revision']])
                insert(db,'living_decisions',id=did,root_id=rid,opportunity=o['id'],input_version=inp,policy_revision=r['policy_revision'],evaluated_at=at,
                       result='SUPPRESS' if blockers else 'ALLOW',blockers=canonical(blockers),primary_blocker=blockers[0] if blockers else None,next_check=nxt)
                if blockers:
                    if nxt is not None and nxt>=o['expires']: db.execute("UPDATE living_opportunities SET state='EXPIRED',revision=revision+1 WHERE id=?",(o['id'],))
                    continue
                ident=fingerprint([did,'intent'])
                insert(db,'living_intents',id=ident,root_id=rid,opportunity=o['id'],decision_id=did,generation=r['generation'],reserved_at=at,
                       expires=o['expires'],state='DECIDED',target=o['target'],prepared=None,invalidated=0)
                db.execute("UPDATE living_opportunities SET state='CONSUMED',revision=revision+1 WHERE id=?",(o['id'],))
                return dict(result='RESERVED',intent_id=ident)
            return dict(result='SILENT')
        return self._command(ctx,None,operation or uuid4().hex,'tick',{},apply,tick=True)

    def prepare_intent(self, ctx, expected, operation, ident, material):
        text(material)
        def apply(db,r,p,at):
            i=one(db,'living_intents',r['root_id'],ident)
            if i['state']!='DECIDED': fail('INVALID_STATE')
            db.execute("UPDATE living_intents SET state='PREPARED',prepared=? WHERE id=?",(material,ident))
            return dict(id=ident)
        return self._command(ctx,expected,operation,'prepare',[ident,material],apply)

    def begin_attempt(self, ctx, expected, operation, ident):
        def apply(db,r,p,at):
            i=one(db,'living_intents',r['root_id'],ident)
            prior=db.execute('SELECT id,state FROM living_attempts WHERE intent=?',(ident,)).fetchone()
            if prior: return dict(attempt_id=prior[0],state=prior[1],execute=False)
            if i['generation']!=r['generation']: fail('GENERATION_STALE')
            if r['reconciliation'] or i['invalidated']: fail('RECONCILIATION_REQUIRED')
            if i['state']!='PREPARED': fail('INVALID_STATE')
            o=one(db,'living_opportunities',r['root_id'],i['opportunity'])
            blockers,_,_=self._blockers(db,r,p,o,at,execution=True)
            if i['target']!=r['target'] or o['target']!=r['target']: blockers.append('TARGET_CHANGED')
            if at>=i['expires']: blockers.append('EXPIRED')
            if blockers:
                expired=at>=min(i['expires'],o['expires'])
                db.execute('UPDATE living_intents SET state=? WHERE id=?',('EXPIRED' if expired else 'CANCELLED',ident))
                reopen=not expired and set(blockers)<= {'QUIET_HOURS','RECENT_INBOUND'}
                db.execute('UPDATE living_opportunities SET state=?,revision=revision+1 WHERE id=?',('OPEN' if reopen else 'EXPIRED' if expired else 'CANCELLED',o['id']))
                return dict(execute=False,blockers=blockers)
            aid=fingerprint([ident,'attempt'])
            insert(db,'living_attempts',id=aid,root_id=r['root_id'],intent=ident,state='CLAIMED',claimed_at=at,
                   runtime_id=self.repository.runtime_id,target=i['target'],request_fingerprint=fingerprint([ident,i['prepared'],i['target']]),message_id=None,sent_at=None)
            db.execute("UPDATE living_intents SET state='ATTEMPTED' WHERE id=?",(ident,))
            return dict(attempt_id=aid,state='CLAIMED',execute=True)
        return self._command(ctx,expected,operation,'begin_attempt',ident,apply)

    def record_delivery(self, ctx, expected, operation, ident, evidence):
        if type(ctx) is not LivingContext: fail('AUTHORIZATION_DENIED')
        # 验证器在持锁前执行；生产默认不配置，模型传布尔标记无效。
        if self.delivery_validator is None: fail('RECEIPT_UNVERIFIED')
        result=self.delivery_validator.verify(evidence)
        if not isinstance(result,dict): fail('RECEIPT_UNVERIFIED')
        result=json.loads(canonical(result))
        def apply(db,r,p,at):
            def conflict():
                db.execute('UPDATE living_roots SET reconciliation=1 WHERE root_id=?',(r['root_id'],))
                return dict(state='RECONCILIATION_REQUIRED')
            a=one(db,'living_attempts',r['root_id'],ident)
            if result['attempt_id']!=ident or result['target']!=a['target']: fail('RECEIPT_UNVERIFIED')
            state=result['state']
            if state not in ('SENT','ACKNOWLEDGED','FAILED','UNKNOWN'): fail('RECEIPT_UNVERIFIED')
            old=db.execute('SELECT fingerprint FROM living_delivery_results WHERE attempt=? AND source=? AND event_id=?',(ident,result['source'],result['event_id'])).fetchone()
            if old:
                if old[0]!=fingerprint(result): return conflict()
                return dict(state=a['state'])
            if a['state'] not in ('CLAIMED','UNKNOWN','SENT') or state=='ACKNOWLEDGED' and a['state']!='SENT' or a['state']=='SENT' and state not in ('SENT','ACKNOWLEDGED'): return conflict()
            if state in ('SENT','ACKNOWLEDGED'):
                text(result['message_id'])
                if a['message_id'] is not None and a['message_id']!=result['message_id']: return conflict()
                if a['sent_at'] is not None and a['sent_at']!=result['sent_at']: return conflict()
                if not a['claimed_at']<=result['sent_at']<=at: fail('RECEIPT_UNVERIFIED')
            insert(db,'living_delivery_results',id=uuid4().hex,root_id=r['root_id'],attempt=ident,source=text(result['source']),event_id=text(result['event_id']),payload=canonical(result),fingerprint=fingerprint(result))
            db.execute('UPDATE living_attempts SET state=?,message_id=?,sent_at=? WHERE id=?',(state,result.get('message_id'),result.get('sent_at'),ident))
            if state=='UNKNOWN': db.execute('UPDATE living_roots SET reconciliation=1 WHERE root_id=?',(r['root_id'],))
            return dict(state=state)
        return self._command(ctx,expected,operation,'delivery',[ident,result],apply)

    def status(self, ctx):
        at=instant(self.clock())
        with self.repository.transaction() as db:
            r=self._root(db,ctx,at); p=self._policy(db,r); rid=r['root_id']
            activity=db.execute("SELECT * FROM living_activities WHERE root_id=? AND state='ACTIVE'",(rid,)).fetchone()
            location=None
            if activity: location=dict(db.execute('SELECT * FROM living_locations WHERE root_id=? AND id=? AND revision=?',(rid,activity['location_id'],activity['location_revision'])).fetchone())
            return dict(root=r,time=time_context(at,p,r['timezone_epoch']),activity=dict(activity) if activity else None,location=location,
                days=[dict(x) for x in db.execute('SELECT * FROM living_days WHERE root_id=? ORDER BY start',(rid,))],
                opportunities=[dict(x) for x in db.execute('SELECT * FROM living_opportunities WHERE root_id=? ORDER BY eligible,id',(rid,))],
                intents=[dict(x) for x in db.execute('SELECT * FROM living_intents WHERE root_id=? ORDER BY reserved_at,id',(rid,))],
                next_schedule=[dict(x) for x in db.execute("SELECT * FROM living_schedule WHERE root_id=? AND state='PENDING' ORDER BY due,priority,id LIMIT 3",(rid,))])

    def observation_context(self, ctx):
        at=instant(self.clock())
        with self.repository.transaction() as db:
            r=self._root(db,ctx,at);p=self._policy(db,r);result={}
            for kind in ('WEATHER','HOLIDAY','SPECIAL_DATE'):
                rows=db.execute('SELECT * FROM living_observations WHERE root_id=? AND kind=? ORDER BY observed DESC,id',(r['root_id'],kind))
                latest=next((dict(x) for x in rows if json.loads(x['payload'])['region']==p['region']),None)
                result[kind]={'status':'UNKNOWN'} if latest is None else dict(status='VALID' if latest['expires']>at else 'STALE',
                    id=latest['id'],expires=latest['expires'],summary=json.loads(latest['payload'])['summary'] if latest['expires']>at else None)
            return result
