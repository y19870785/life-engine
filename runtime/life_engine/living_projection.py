"""独立只读投影；不修改现有 Prompt 模板或权限。"""
from dataclasses import dataclass
import hashlib
import hmac
import json

from .living_domain import LivingContext, canonical, fail, instant, scope_values
from .living_policy import time_context
from .memory import AudienceKind
from .prompt import PromptSessionContext, PromptPurpose
from .world_sqlite_repository import _SQLiteTransaction


@dataclass(frozen=True)
class LivingContextSnapshot:
    payload: str
    seal: str


def query(runtime, session, *, maximum_bytes=8192):
    if type(session) is not PromptSessionContext or session.purpose is not PromptPurpose.SOUL_RESPONSE:
        fail('UNSUPPORTED_PURPOSE')
    if session.viewer.kind is not AudienceKind.SOUL or session.viewer.target != session.scope.soul_id:
        fail('VIEWER_MISMATCH')
    if session.runtime_id != runtime.repository.runtime_id:
        fail('SESSION_STALE')
    if type(maximum_bytes) is not int or not 0 < maximum_bytes <= 8192:
        fail('BUDGET_INPUT')
    ctx = LivingContext(session.principal, session.scope, session.generation, 'projection', session)
    at = instant(runtime.clock())
    with runtime.repository.transaction() as db:
        root = runtime._root(db, ctx, at)
        world = _SQLiteTransaction(db).get_world(session.scope.world_id)
        if world.world.revision != session.world_revision:
            fail('WORLD_STALE')
        rid = root['root_id']
        policy = runtime._policy(db, root)
        activity = db.execute("SELECT id,name,location_id,location_revision,start,end,state,activated_at,inferred FROM living_activities WHERE root_id=? AND state='ACTIVE'", (rid,)).fetchone()
        location = None
        if activity:
            location = dict(db.execute('SELECT id,name,category,origin FROM living_locations WHERE root_id=? AND id=? AND revision=?', (rid, activity['location_id'], activity['location_revision'])).fetchone())
        bounds = [((at // 60) + 1) * 60]
        for table, column, condition in [('living_schedule', 'due', "state='PENDING'"),
                                          ('living_observations', 'expires', '1=1'),
                                          ('living_opportunities', 'expires', "state IN ('OPEN','OFFERED','CONSUMED')")]:
            suffix = '' if table == 'living_schedule' else f' AND {column}>?'
            params = (rid,) if not suffix else (rid,at)
            value = db.execute(f'SELECT MIN({column}) FROM {table} WHERE root_id=? AND {condition}'+suffix, params).fetchone()[0]
            if value is not None:
                bounds.append(value)
        if min(bounds) <= at:
            fail('REVALIDATION_REQUIRED')
        payload = dict(scope=scope_values(session.scope), principal=str(session.principal.principal_id),
                       session=str(session.session_id), viewer=str(session.viewer.target),
                       writer_epoch=session.writer_epoch.value, world_revision=session.world_revision.value,
                       runtime_id=session.runtime_id, generation=session.generation,
                       living_revision=root['revision'], policy_revision=root['policy_revision'],
                       time=time_context(at, policy, root['timezone_epoch']), valid_until=min(bounds),
                       activity=dict(activity) if activity else None, location=location,
                       origin='FICTIONAL_ROLE_STATE', text_authority='UNTRUSTED_CONTENT_DATA',
                       structure_authority='TRUSTED_STRUCTURED_STATE', diagnostics=[])
        if len(canonical(payload).encode()) > maximum_bytes:
            fail('BUDGET_INPUT')
        optional = [
            ('days', 'SELECT id,revision,local_date FROM living_days WHERE root_id=? ORDER BY start DESC LIMIT 2'),
            ('recent_transitions', 'SELECT revision,at,action FROM living_transitions WHERE root_id=? ORDER BY revision DESC LIMIT 5'),
            ('next_schedule', "SELECT id,subject,action,due FROM living_schedule WHERE root_id=? AND state='PENDING' ORDER BY due,priority,id LIMIT 3"),
            ('contact', 'SELECT id,result,primary_blocker,next_check FROM living_decisions WHERE root_id=? ORDER BY evaluated_at DESC,id LIMIT 1'),
            ('photo', "SELECT id,payload,expires FROM living_opportunities WHERE root_id=? AND kind='PHOTO' AND state='OFFERED' ORDER BY eligible DESC,id LIMIT 1"),
            ('voice', "SELECT id,payload,expires FROM living_opportunities WHERE root_id=? AND kind='VOICE' AND state='OFFERED' ORDER BY eligible DESC,id LIMIT 1"),
        ]
        for name, sql in optional:
            payload[name] = []
            for row in db.execute(sql, (rid,)):
                item = dict(row)
                if name in ('photo','voice'):
                    item['payload']=json.loads(item['payload'])
                payload[name].append(item)
                if len(canonical(payload).encode()) + 64 > maximum_bytes:
                    payload[name].pop()
                    if 'OPTIONAL_TRUNCATED' not in payload['diagnostics']:
                        payload['diagnostics'].append('OPTIONAL_TRUNCATED')
                    break
        encoded = canonical(payload)
        if len(encoded.encode()) > maximum_bytes:
            fail('BUDGET_INPUT')
        return LivingContextSnapshot(encoded, hmac.new(runtime._snapshot_key, encoded.encode(), hashlib.sha256).hexdigest())


def revalidate(runtime, session, snapshot):
    if type(snapshot) is not LivingContextSnapshot:
        fail('SNAPSHOT_UNTRUSTED')
    seal = hmac.new(runtime._snapshot_key, snapshot.payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(seal, snapshot.seal):
        fail('SNAPSHOT_UNTRUSTED')
    old = json.loads(snapshot.payload)
    current = json.loads(query(runtime, session).payload)
    if not old['time']['as_of_utc'] <= instant(runtime.clock()) < old['valid_until']:
        fail('SNAPSHOT_STALE')
    for key in ('scope','principal','session','viewer','writer_epoch','world_revision','runtime_id',
                'generation','living_revision','policy_revision'):
        if old[key] != current[key]:
            fail('SNAPSHOT_STALE')
    return True
