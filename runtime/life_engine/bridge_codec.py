"""Bridge 的规范 UTF-8 JSON 数据；不编码 Python 对象身份或 HMAC 密钥。"""
import hashlib

from .world_codec import dumps


def scope_data(scope):
    return [str(scope.owner_id), str(scope.soul_id), str(scope.world_id), str(scope.timeline_id)]


def audience_data(audience):
    return [audience.kind.value, str(audience.target)]


def proposal_data(proposal):
    return {'source': scope_data(proposal.source_scope), 'target': scope_data(proposal.target_scope),
            'data_class': proposal.data_class.value, 'fields': list(proposal.allowed_fields),
            'purpose': proposal.purpose.value, 'audience': audience_data(proposal.target_audience),
            'expires_at': proposal.expires_at.isoformat()}


def digest(value):
    return hashlib.sha256(dumps(value).encode('utf-8')).hexdigest()


def preview_data(preview):
    return {'mode': 'grant', 'grant_id': str(preview.grant_id),
            'principal': [str(preview.principal.principal_id), str(preview.principal.owner_id)],
            'proposal': proposal_data(preview.proposal), 'runtime_id': preview.runtime_id,
            'generation': preview.generation}


def lineage_data(lineage):
    return {'scope': scope_data(lineage.source_scope), 'subsystem': lineage.source_subsystem.value,
            'object_id': lineage.source_object_id, 'version': lineage.source_version,
            'audience': [audience_data(a) for a in lineage.source_audience],
            'reality': lineage.reality_status.value, 'canon': lineage.canon_status.value,
            'grant_id': str(lineage.grant_id), 'grant_revision': lineage.grant_revision.value}


def item_data(item):
    return {'item_id': item.item_id, 'fields': list(map(list, item.fields)),
            'lineage': lineage_data(item.lineage), 'byte_size': item.byte_size}


def projection_data(projection):
    target = projection.target_session
    return {'grant_id': str(projection.grant_id), 'grant_revision': projection.grant_revision.value,
            'source': scope_data(projection.source_scope), 'target': scope_data(projection.target_scope),
            'data_class': projection.data_class.value, 'purpose': projection.purpose.value,
            'fields': list(projection.fields), 'audience': audience_data(projection.target_audience),
            'source_version': projection.source_version,
            'source_session': [str(projection.source_principal.principal_id),
                               audience_data(projection.source_viewer), str(projection.source_session_id),
                               projection.source_writer_epoch.value, projection.source_runtime_id,
                               projection.source_generation],
            'target_session': [str(target.principal.principal_id), str(target.session_id),
                               target.writer_epoch.value, target.runtime_id, target.generation,
                               audience_data(target.viewer)],
            'items': [item_data(item) for item in projection.items],
            'budget': [projection.budget.max_items, projection.budget.max_item_bytes,
                       projection.budget.max_total_bytes], 'budget_used': projection.budget_used}
