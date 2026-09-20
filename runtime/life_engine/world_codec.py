"""数据库附属值的确定性 JSON 编码；身份与引用仍由独立 SQL 列保存。"""
from dataclasses import fields
from datetime import datetime, timezone
import json

from .domain import (CanonStatus, DomainId, Principal, Provenance, RealityStatus, SourceType, Values)


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def values_dump(value):
    return dumps(value.items)


def values_load(text):
    value = json.loads(text)
    if type(value) is not list or any(type(pair) is not list for pair in value):
        raise ValueError('Values 必须为成对数组')
    return Values(tuple(tuple(pair) for pair in value))


def provenance_dump(value):
    result = {f.name: getattr(value, f.name) for f in fields(Provenance)}
    result.update(source_type=value.source_type.value, reality_status=value.reality_status.value,
                  canon_status=value.canon_status.value,
                  created_at=value.created_at.astimezone(timezone.utc).isoformat(),
                  actor={'principal_id': str(value.actor.principal_id), 'owner_id': str(value.actor.owner_id)})
    for key in ('source_world_id', 'source_timeline_id', 'source_session_id', 'source_event_id'):
        result[key] = str(result[key]) if result[key] is not None else None
    return dumps(result)


def provenance_load(text):
    result = json.loads(text)
    if type(result) is not dict or set(result) != {f.name for f in fields(Provenance)}:
        raise ValueError('Provenance 字段不完整')
    actor = result['actor']
    if type(actor) is not dict or set(actor) != {'principal_id', 'owner_id'}:
        raise ValueError('Principal 字段不完整')
    result.update(source_type=SourceType(result['source_type']), reality_status=RealityStatus(result['reality_status']),
                  canon_status=CanonStatus(result['canon_status']), created_at=datetime.fromisoformat(result['created_at']),
                  actor=Principal(DomainId.parse(actor['principal_id']), DomainId.parse(actor['owner_id'])))
    for key in ('source_world_id', 'source_timeline_id', 'source_session_id', 'source_event_id'):
        if result[key] is not None:
            result[key] = DomainId.parse(result[key])
    return Provenance(**result)
