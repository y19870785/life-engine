"""Living 值、身份与序列化；不依赖宿主或模型。"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from .domain import Principal, WorldScope

REASONS = ('MORNING_GREETING', 'LUNCH_CHECKIN', 'AFTER_WORK', 'REMEMBERED_FOLLOWUP',
           'LONG_SILENCE', 'ACTIVITY_TRANSITION', 'WEATHER_EVENT', 'HOLIDAY',
           'PHOTO_SHARING', 'USER_PROMISED_FOLLOWUP', 'SOCIAL_IMPULSE')
LOCATIONS = ('HOME', 'WORK', 'EXERCISE', 'CAFE', 'TRANSIT', 'SHOP', 'PARK', 'OTHER')


class LivingError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def fail(code):
    raise LivingError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def text(value, limit=512):
    if type(value) is not str or not value or len(value.encode('utf-8')) > limit:
        fail('INVALID_ARGUMENT')
    return value


def instant(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        fail('INVALID_CLOCK')
    return value.astimezone(timezone.utc).timestamp()


def scope_values(scope):
    if type(scope) is not WorldScope:
        fail('SCOPE_MISMATCH')
    return tuple(str(getattr(scope, k)) for k in ('owner_id', 'soul_id', 'world_id', 'timeline_id'))


@dataclass(frozen=True)
class LivingContext:
    """仅由受信本地调用方构造；不暴露给 Host 参数/模型正文。"""
    principal: Principal
    scope: WorldScope
    generation: str
    producer: str
    session: object = None

    def __post_init__(self):
        if type(self.principal) is not Principal or self.principal.owner_id != self.scope.owner_id:
            fail('SCOPE_MISMATCH')
        scope_values(self.scope)
        text(self.generation)
        text(self.producer)


@dataclass(frozen=True)
class LivingTickContext:
    """部署层授予的窄 tick 能力；不能用于 Owner 命令或发送。"""
    scope: WorldScope
    instance_id: str
    generation: str
    policy_revision: int
    producer: str = 'scheduler'
