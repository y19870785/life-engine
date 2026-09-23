"""Story 事件与投影的严格规范 JSON 往返。"""
import json

from .domain import DomainError, DomainId, IdKind, WorldScope, check_id
from .story import (PROJECTION_VERSION, StoryClock, StoryEventKind, StoryEventSourceReference,
                    StoryRevision, StoryState, StoryThread, StoryThreadStatus,
                    SourceReferenceKind, payload_data, payload_load)
from .world_codec import dumps


def scope_values(scope):
    return (str(scope.owner_id), str(scope.soul_id), str(scope.world_id), str(scope.timeline_id))


def scope_load(row):
    result = WorldScope(*(DomainId.parse(row[k]) for k in ('owner_id','soul_id','world_id','timeline_id')))
    return result


def state_data(state):
    return {
        'world_facts': [list(row) for row in state.world_facts],
        'character_states': [[str(a),b,c] for a,b,c in state.character_states],
        'relationships': [[str(a),str(b),c,d] for a,b,c,d in state.relationships],
        'threads': [{'thread_id':str(t.thread_id),'title':t.title,'summary':t.summary,
            'status':t.status.value,'opened_by_event':str(t.opened_by_event),
            'last_updated_event':str(t.last_updated_event),
            'resolved_by_event':str(t.resolved_by_event) if t.resolved_by_event else None}
            for t in state.threads],
    }


def state_dump(state):
    return dumps(state_data(state))


def state_load(scope, revision, tick, sequence, version, text):
    if type(text) is not str or version != PROJECTION_VERSION:
        raise DomainError('Story 投影版本或编码无效')
    data = json.loads(text)
    if type(data) is not dict or set(data) != {'world_facts','character_states','relationships','threads'}:
        raise DomainError('Story 投影字段无效')
    if any(type(data[k]) is not list for k in data):
        raise DomainError('Story 投影列表无效')
    facts = tuple(tuple(row) for row in data['world_facts'])
    characters = tuple((DomainId.parse(row[0]),row[1],row[2]) for row in data['character_states'])
    relationships = tuple((DomainId.parse(row[0]),DomainId.parse(row[1]),row[2],row[3])
                          for row in data['relationships'])
    threads = tuple(StoryThread(DomainId.parse(t['thread_id']), t['title'], t['summary'],
        StoryThreadStatus(t['status']), DomainId.parse(t['opened_by_event']),
        DomainId.parse(t['last_updated_event']),
        DomainId.parse(t['resolved_by_event']) if t['resolved_by_event'] else None)
        for t in data['threads'])
    state = StoryState(scope, StoryRevision(revision), StoryClock(tick), sequence, version,
        facts, characters, relationships, threads)
    if state_dump(state) != text:
        raise DomainError('Story 投影不是规范或排序编码')
    return state


def refs_dump(refs):
    return dumps([[ref.kind.value,ref.identity] for ref in refs])


def refs_load(text):
    data = json.loads(text)
    if type(data) is not list:
        raise DomainError('Story 来源列表无效')
    result = tuple(StoryEventSourceReference(SourceReferenceKind(k), v) for k,v in data)
    if refs_dump(result) != text:
        raise DomainError('Story 来源编码不规范')
    return result


def payload_dump(kind, payload):
    return dumps(payload_data(kind,payload))


def payload_decode(kind, text):
    data = json.loads(text)
    payload = payload_load(kind,data)
    if payload_dump(kind,payload) != text:
        raise DomainError('Story 载荷编码不规范')
    return payload
