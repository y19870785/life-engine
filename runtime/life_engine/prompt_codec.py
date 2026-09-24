"""Prompt 内部规范编码；这不是任何模型或宿主的消息格式。"""
from .world_codec import dumps


def item_data(item):
    return {'source_kind': item.source_kind, 'source_id': item.source_id,
            'content': item.content}


def section_data(section):
    return {'kind': section.kind.value, 'authority': section.authority.value,
            'source': section.source, 'priority': section.priority,
            'required': section.required, 'truncation_policy': section.truncation_policy.value,
            'items': [item_data(item) for item in section.items]}


def item_bytes(item):
    return len(dumps(item_data(item)).encode('utf-8'))


def section_bytes(section):
    return len(dumps(section_data(section)).encode('utf-8'))


def render_canonical(sections):
    """供字节预算、指纹和测试使用的内部表示，不是 system prompt。"""
    return dumps([section_data(section) for section in sections])


def total_bytes(sections):
    return len(render_canonical(sections).encode('utf-8'))


def budget_data(budget):
    return {key: getattr(budget, key) for key in (
        'max_total_bytes', 'runtime_control_bytes', 'character_identity_bytes',
        'character_behavior_bytes', 'character_examples_bytes', 'story_bytes',
        'lore_bytes', 'memory_bytes', 'conversation_bytes', 'max_total_tokens')}


def fingerprint_data(snapshot):
    scope = snapshot.scope
    viewer = snapshot.viewer
    return {
        'template_version': snapshot.template_version,
        'scope': [str(scope.owner_id), str(scope.soul_id), str(scope.world_id), str(scope.timeline_id)],
        'principal': [str(snapshot.principal.principal_id), str(snapshot.principal.owner_id)],
        'viewer': [viewer.kind.value, str(viewer.target) if viewer.target else None],
        'purpose': snapshot.purpose.value, 'session_id': str(snapshot.session_id),
        'writer_epoch': snapshot.writer_epoch.value, 'runtime_id': snapshot.runtime_id,
        'generation': snapshot.generation,
        'definition_ref': ([str(snapshot.definition_ref.definition_id), snapshot.definition_ref.version.value]
                           if snapshot.definition_ref else None),
        'character_instance_id': str(snapshot.character_instance_id) if snapshot.character_instance_id else None,
        'world_revision': snapshot.world_revision.value,
        'memory_version': snapshot.memory_version,
        'memory_query_spec': [snapshot.memory_query_spec[0], snapshot.memory_query_spec[1],
                              snapshot.memory_query_spec[2], str(snapshot.memory_query_spec[3]) if snapshot.memory_query_spec[3] else None],
        'lore_binding_revision': snapshot.lore_binding_revision.value,
        'lore_version': snapshot.lore_version,
        'lore_book_versions': [[str(book), version.value] for book, version in snapshot.lore_book_versions],
        'story_revision': snapshot.story_revision.value,
        'story_projection_version': snapshot.story_projection_version,
        'conversation_lane_id': snapshot.conversation_lane_id,
        'conversation_version': snapshot.conversation_version,
        'budget': budget_data(snapshot.budget),
        'sections': [section_data(section) for section in snapshot.sections],
        'diagnostics': [item.value for item in snapshot.diagnostics],
        'budget_exhausted': snapshot.budget_exhausted,
        'requirements': [item.value for item in snapshot.requirements.capabilities],
    }
