"""版本化策略和当地时间解析；时间比较始终使用 UTC instant。"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, TZPATH
from importlib.metadata import version, PackageNotFoundError
import json
import hashlib
from pathlib import Path
from importlib.resources import files

from .living_domain import canonical, fail, text, REASONS, LOCATIONS


def zone(name):
    """UTC 不依赖外部数据库；具名时区必须使用实际安装的 IANA 数据。"""
    return timezone.utc if name == 'UTC' else ZoneInfo.no_cache(name)


def zone_fingerprint(name):
    """固定实际规则数据指纹，避免同名 tzdata 更新静默改变未决定的时间。"""
    if name=='UTC': return 'UTC-fixed-offset-zero'
    if name.startswith('/') or '..' in name.split('/'): fail('INVALID_POLICY')
    for folder in TZPATH:
        path=Path(folder).joinpath(*name.split('/'))
        if path.is_file(): return hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        data=files('tzdata.zoneinfo').joinpath(*name.split('/')).read_bytes()
    except (ImportError,FileNotFoundError):
        fail('TZDATA_REQUIRED')
    return hashlib.sha256(data).hexdigest()


def tz_source():
    try:
        return 'tzdata:' + version('tzdata')
    except PackageNotFoundError:
        return 'system:' + '|'.join(map(str, TZPATH))


def policy(**changes):
    result = dict(timezone='UTC', tzdata_source=tz_source(), mode='companion',
        quiet=[1380, 480], daily_cap=3, rolling_cap=3, cooldown=9000, spacing=0,
        recent_inbound=4500, recent_outbound=0, workdays=[0, 1, 2, 3, 4],
        dayparts=[[0,360,'夜间'],[360,660,'早晨'],[660,840,'午间'],[840,1080,'下午'],
                  [1080,1320,'晚间'],[1320,1440,'夜间']],
        routine=[], contacts=[], visual={}, photo=False, voice=False, special_dates=[],
        spontaneous=False, region='UNKNOWN', seed='living-v1', algorithm='HMAC-SHA256-rejection-v1')
    result.update(changes)
    result['tzdata_fingerprint']=zone_fingerprint(result['timezone'])
    return validate_policy(result)


def validate_policy(p):
    p = json.loads(canonical(p))
    try:
        zone(p['timezone'])
        for key in ('daily_cap','rolling_cap','cooldown','spacing','recent_inbound','recent_outbound'):
            if type(p[key]) is not int or not 0 <= p[key] <= 31536000:
                fail('INVALID_POLICY')
        if p['mode'] not in ('assistant','companion') or p['algorithm'] != 'HMAC-SHA256-rejection-v1':
            fail('INVALID_POLICY')
        if len(p['quiet']) != 2 or any(type(n) is not int or not 0 <= n < 1440 for n in p['quiet']):
            fail('INVALID_POLICY')
        if any(type(p[k]) is not bool for k in ('photo','voice','spontaneous')):
            fail('INVALID_POLICY')
        end = 0
        for a,b,name in p['dayparts']:
            if a != end or not a < b <= 1440:
                fail('INVALID_POLICY')
            text(name); end = b
        if end != 1440 or any(type(n) is not int or n not in range(7) for n in p['workdays']):
            fail('INVALID_POLICY')
        text(p['seed']); text(p['tzdata_source']); text(p['region'])
        text(p['tzdata_fingerprint'])
        if len(p['routine']) > 512 or len(p['contacts']) > 512:
            fail('INVALID_POLICY')
        prior = 0
        for r in sorted(p['routine'], key=lambda x:x['start']):
            if not prior <= r['start'] < r['end'] <= 1440 or r['category'] not in LOCATIONS:
                fail('INVALID_POLICY')
            text(r['name']); text(r['location']); prior = r['end']
        for c in p['contacts']:
            text(c.get('theme','日常'))
            if type(c.get('photo',False)) is not bool: fail('INVALID_POLICY')
            if c['reason'] not in REASONS or not 0 <= c['start'] < c['end'] <= 1440:
                fail('INVALID_POLICY')
            if not 1 <= c.get('grace',3600) <= 86400:
                fail('INVALID_POLICY')
        for key,candidates in p['visual'].items():
            text(key,128)
            if not candidates or len(candidates)>256:
                fail('INVALID_POLICY')
            for item in candidates: text(item)
        for day in p['special_dates']:
            datetime.strptime('2000-'+day, '%Y-%m-%d')
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        fail('INVALID_POLICY')
    return p


def local_instant(day, minute, zone):
    """fold 固定为 0；gap 逐分钟移动到首个有效墙钟分钟。"""
    naive = datetime.combine(day, datetime.min.time()) + timedelta(minutes=minute)
    for _ in range(2881):
        candidate = naive.replace(tzinfo=zone, fold=0)
        utc = candidate.astimezone(timezone.utc)
        if utc.astimezone(zone).replace(tzinfo=None) == naive:
            return utc.timestamp()
        naive += timedelta(minutes=1)
    fail('INVALID_LOCAL_TIME')


def time_context(at, p, epoch):
    local_zone = zone(p['timezone'])
    local = datetime.fromtimestamp(at, timezone.utc).astimezone(local_zone)
    minute = local.hour*60+local.minute
    start = local_instant(local.date(),0,local_zone)
    end = local_instant(local.date()+timedelta(days=1),0,local_zone)
    return dict(as_of_utc=at,timezone=p['timezone'],timezone_epoch=epoch,
        tzdata_source=p['tzdata_source'],tzdata_fingerprint=p['tzdata_fingerprint'],utc_offset=int(local.utcoffset().total_seconds()),
        fold=local.fold,local_date=local.date().isoformat(),local_time=local.time().isoformat(),
        weekday=local.weekday(),daypart=next(n for a,b,n in p['dayparts'] if a<=minute<b),
        calendar_status='WORKDAY' if local.weekday() in p['workdays'] else 'WEEKEND',
        holiday='UNKNOWN',special_date=local.strftime('%m-%d') in p['special_dates'],
        start_utc=start,end_utc=end)


def quiet_until(at, p):
    start,end = p['quiet']
    local = datetime.fromtimestamp(at,timezone.utc).astimezone(zone(p['timezone']))
    m=local.hour*60+local.minute
    inside = start != end and (start<=m<end if start<end else m>=start or m<end)
    if not inside: return None
    day=local.date()+timedelta(days=1 if start>end and m>=start else 0)
    return local_instant(day,end,zone(p['timezone']))
