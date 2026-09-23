"""仅从已接受事件生成 StoryState 的纯确定性 reducer。"""
from dataclasses import replace

from .domain import DomainError, require
from .story import (CharacterPayload, FactPayload, NarrativePayload, RelationshipPayload,
                    StoryEvent, StoryEventKind as K, StoryState, StoryThread,
                    StoryThreadStatus, ThreadPayload)


def _ordered(mapping):
    """领域 ID 按规范字符串排序，避免 Python 对象比较。"""
    return tuple((*key, value) for key, value in sorted(mapping.items(), key=lambda pair:
        tuple(str(part).encode('utf-8') for part in pair[0])))


def reduce_story(previous_state, accepted_event):
    """不读取外部状态；不存在的移除及非法线索状态一律拒绝。"""
    require(previous_state, StoryState)
    require(accepted_event, StoryEvent)
    if (previous_state.scope != accepted_event.scope or
            accepted_event.sequence != previous_state.last_event_sequence + 1):
        raise DomainError('Story 事件与投影不连续')
    kind, payload = accepted_event.proposal.kind, accepted_event.proposal.payload
    facts = {(a, b): c for a, b, c in previous_state.world_facts}
    characters = {(a, b): c for a, b, c in previous_state.character_states}
    relationships = {(a, b, c): d for a, b, c, d in previous_state.relationships}
    threads = {item.thread_id: item for item in previous_state.threads}
    if isinstance(payload, FactPayload):
        key = (payload.namespace, payload.key)
        if kind is K.WORLD_FACT_SET:
            facts[key] = payload.value
        elif key in facts:
            del facts[key]
        else:
            raise DomainError('Story 事实不存在')
    elif isinstance(payload, CharacterPayload):
        key = (payload.character_id, payload.key)
        if kind is K.CHARACTER_STATE_SET:
            characters[key] = payload.value
        elif key in characters:
            del characters[key]
        else:
            raise DomainError('Story 角色状态不存在')
    elif isinstance(payload, RelationshipPayload):
        key = (payload.source_id, payload.target_id, payload.key)
        if kind is K.RELATIONSHIP_SET:
            relationships[key] = payload.value
        elif key in relationships:
            del relationships[key]
        else:
            raise DomainError('Story 关系不存在')
    elif isinstance(payload, ThreadPayload):
        old = threads.get(payload.thread_id)
        if kind is K.THREAD_OPENED:
            if old is not None:
                raise DomainError('Story 线索身份已存在')
            threads[payload.thread_id] = StoryThread(payload.thread_id, payload.title, payload.summary,
                StoryThreadStatus.OPEN, accepted_event.event_id, accepted_event.event_id)
        else:
            if old is None or old.status is not StoryThreadStatus.OPEN:
                raise DomainError('Story 线索不处于开放状态')
            if kind is K.THREAD_UPDATED:
                threads[payload.thread_id] = replace(old, summary=payload.summary,
                    last_updated_event=accepted_event.event_id)
            else:
                threads[payload.thread_id] = replace(old,
                    status=StoryThreadStatus.RESOLVED if kind is K.THREAD_RESOLVED else StoryThreadStatus.CANCELLED,
                    last_updated_event=accepted_event.event_id, resolved_by_event=accepted_event.event_id)
    elif not isinstance(payload, NarrativePayload):
        raise DomainError('Story 载荷不受支持')
    return StoryState(previous_state.scope, accepted_event.revision, accepted_event.clock,
        accepted_event.sequence, previous_state.projection_version,
        _ordered(facts), _ordered(characters), _ordered(relationships),
        tuple(threads[key] for key in sorted(threads, key=lambda value: value.value.bytes)))


def replay_story(scope, events):
    """按事件接收顺序重建投影；不跳过被前向修正的旧事件。"""
    state = StoryState(scope)
    for event in events:
        state = reduce_story(state, event)
    return state
