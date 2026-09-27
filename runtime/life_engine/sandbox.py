"""Soul Continuity 沙箱证据；不授予 Host capability，也不保存业务 Schema。"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .durable import absolute, health, locked, registry, state_check, state_home
from .prompt import TEMPLATE_VERSION
from .world_schema import DATA_SCHEMA, SIGNATURE

FORMAT = 'SP-005H0-sandbox-v1'


def identity(root, reg, instance):
    """调用时从 durable 真源取身份，不接受模型提供的实例声明。"""
    return {'instance_id': instance['id'], 'generation': instance['generation'],
            'data_root': str(state_home(root, instance)), 'install_root': str(root),
            'release': reg['release'], 'agent_id': instance['agent_id'],
            'host_kind': instance['adapter'], 'host_home': instance['host_home'],
            'host_agent_id': instance['host_agent_id'], 'data_schema': DATA_SCHEMA,
            'schema_signature': SIGNATURE, 'prompt_template': TEMPLATE_VERSION}


def delivery_trace(events, *, verify_receipt=None):
    """只校验报告证据链，不发送、不写 contacts、不把 ack 文本当回执。

    当前原生桥接器没有渠道回执验证器；因此默认最多到 PREPARED。
    验证器须由受信渠道代码提供，不能来自 JSON 或模型参数。
    """
    order = ('GENERATED', 'PREPARED', 'SENT', 'ACKNOWLEDGED')
    state = 'NOT_EXECUTED'
    correlation = None
    message_id = None
    for index, event in enumerate(events):
        if index >= len(order) or event.get('state') != order[index]:
            raise ValueError('交付证据不能跳级或倒退')
        key = (event.get('operation_id'), event.get('target'))
        if not all(isinstance(v, str) and v.strip() for v in key):
            raise ValueError('交付证据需要明确 operation_id 与本人测试目标')
        if correlation is not None and key != correlation:
            raise ValueError('交付证据不属于同一操作和目标')
        correlation = key
        if index >= 2:
            if not isinstance(event.get('message_id'), str) or not event['message_id'].strip():
                raise ValueError('发送与回执需要真实 message_id')
            if message_id is not None and event['message_id'] != message_id:
                raise ValueError('回执不属于已发送消息')
            if not event.get('receipt') or verify_receipt is None or verify_receipt(event) is not True:
                return {'state': state, 'unverified_claim': event['state'],
                        'receipt_capability': 'LIMITED', 'result': 'UNVERIFIED_RECEIPT'}
            message_id = event['message_id']
        state = event['state']
    return {'state': state, 'receipt_capability': 'LIMITED' if verify_receipt is None else 'VERIFIED',
            'result': 'PASS'}


def validate_probe(probe, expected, *, now=None):
    """验证捕获文件的一致性和时效；文件不是签名认证或真实 Host 证明。"""
    errors = []
    if not isinstance(probe, dict) or probe.get('format') != FORMAT:
        return ['INVALID_ATTESTATION']
    now = now or datetime.now(timezone.utc)
    try:
        at = datetime.fromisoformat(probe['at'])
        age = (now - at).total_seconds()
        if not 0 <= age <= 300:
            errors.append('ATTESTATION_EXPIRED')
    except (KeyError, TypeError, ValueError):
        errors.append('INVALID_TIMESTAMP')
    host = probe.get('host', {})
    if not isinstance(host, dict):
        return errors + ['INVALID_HOST']
    if host.get('kind') != expected['host_kind']:
        errors.append('HOST_KIND_MISMATCH')
    for name in ('installation', 'executable'):
        if not isinstance(host.get(name), str) or host[name] in ('', 'UNKNOWN'):
            errors.append('MISSING_' + name.upper())
    if expected['host_kind'] == 'hermes':
        official = ('https://github.com/NousResearch/hermes-agent.git',
                    'https://github.com/NousResearch/hermes-agent', 'git@github.com:NousResearch/hermes-agent.git')
        if host.get('origin') not in official:
            errors.append('OFFICIAL_HERMES_NOT_ATTESTED')
        version_known = isinstance(host.get('version'), str) and host['version'] not in ('', 'UNKNOWN')
        checkout_known = isinstance(host.get('checkout'), str) and host['checkout'] not in ('', 'UNKNOWN')
        if not version_known and not checkout_known:
            errors.append('HOST_VERSION_UNKNOWN')
    elif not isinstance(host.get('version'), str) or host['version'] in ('', 'UNKNOWN'):
        errors.append('HOST_VERSION_UNKNOWN')
    field = 'profile' if expected['host_kind'] == 'hermes' else 'workspace'
    try:
        if not host.get(field) or Path(host[field]).resolve() != Path(expected['host_home']).resolve():
            errors.append('HOST_BINDING_MISMATCH')
    except (TypeError, ValueError, OSError):
        errors.append('INVALID_HOST_PATH')
    if expected['host_kind'] == 'openclaw' and host.get('agent_id') != expected['host_agent_id']:
        errors.append('HOST_AGENT_MISMATCH')
    epoch = probe.get('plugin_epoch')
    if not isinstance(epoch, str) or not epoch.strip():
        errors.append('MISSING_PLUGIN_EPOCH')
    probes = probe.get('probes', {})
    if not isinstance(probes, dict):
        return errors + ['INVALID_PROBES']
    for action in ('status', 'doctor', 'wake', 'photo'):
        result = probes.get(action, {})
        if not isinstance(result, dict) or result.get('ok') is not True or result.get('runtime') != expected:
            errors.append(action.upper() + '_PROBE_FAILED')
    if probe.get('hook_runtime') != expected:
        errors.append('HOOK_REVALIDATION_REQUIRED')
    return errors


def report(root, key, *, probe=None, previous=None, evidence_kind='unverified_capture'):
    """新进程探测目标实例；真实重启、聊天和渠道回执仍需独立实测。"""
    if evidence_kind not in ('simulated', 'unverified_capture'):
        raise ValueError('证据类型只允许 simulated 或 unverified_capture')
    root = absolute(root)
    with locked(root, key):
        reg = registry(root)
        instance = reg['instances'][key]
        cfg = state_check(state_home(root, instance), instance)
        expected = identity(root, reg, instance)
    local = {}
    for action in ('status', 'doctor'):
        done = subprocess.run([reg['python'], '-X', 'utf8', str(root / 'life.py'), '--instance', key, action],
                              capture_output=True, text=True, encoding='utf-8', timeout=30)
        result = json.loads(done.stdout)
        local[action] = {'ok': done.returncode == 0 and result.get('ok', True) is True,
                         'runtime': result.get('runtime')}
    errors = []
    if any(not v['ok'] or v['runtime'] != expected for v in local.values()):
        errors.append('LOCAL_PROBE_FAILED')
    doctor = health(root, key)
    if not doctor['ok']:
        errors.append('INSTALLATION_DOCTOR_FAILED')
    with locked(root, key):
        current = registry(root)
        if identity(root, current, current['instances'][key]) != expected:
            errors.append('INSTANCE_CHANGED_DURING_VALIDATION')
    probe_errors = validate_probe(probe, expected) if probe is not None else ['MISSING_ATTESTATION']
    recovery = 'NOT_EXECUTED'
    if previous is not None:
        if not isinstance(previous, dict) or previous.get('format') != FORMAT:
            errors.append('INVALID_PREVIOUS_REPORT')
        elif previous.get('runtime') != expected:
            recovery = 'REVALIDATION_REQUIRED'
        elif not probe_errors and previous.get('plugin_epoch') and previous['plugin_epoch'] != probe['plugin_epoch']:
            recovery = 'NEW_PLUGIN_EPOCH_OBSERVED'
        else:
            recovery = 'RELOAD_NOT_PROVEN'
    bridge = root / 'bridges' / key / instance['adapter']
    entry = bridge / ('__init__.py' if instance['adapter'] == 'hermes' else 'index.mjs')
    return {'format': FORMAT, 'at': datetime.now(timezone.utc).isoformat(),
            'report_generated': True, 'validation_passed': False,
            'scope': 'SOUL_CONTINUITY_ONLY', 'full_private_rp': 'BLOCKED', 'h1_h2': 'BLOCKED',
            'runtime': expected, 'evidence_kind': evidence_kind,
            'host': probe.get('host', {}) if isinstance(probe, dict) else {'version': 'UNKNOWN'},
            'plugin_file': str(entry), 'plugin_file_exists': entry.is_file(),
            'plugin_load_evidence': 'UNVERIFIED_CAPTURE' if probe is not None else 'UNKNOWN',
            'binding_basis': 'Hermes get_hermes_home' if instance['adapter'] == 'hermes' else 'OpenClaw agentId + workspaceDir；跨 Gateway/Profile 唯一性未证明',
            'plugin_epoch': probe.get('plugin_epoch') if isinstance(probe, dict) else None,
            'host_probe_consistency': 'PASS' if not probe_errors else 'FAIL',
            'host_probe_errors': probe_errors, 'local_probes': local,
            'local_validation': 'PASS' if not errors else 'FAIL', 'errors': errors,
            'life_engine_restart': 'PASS_FRESH_PROCESSES' if not errors else 'FAIL',
            'last_successful_tool_probe': probe.get('at') if probe is not None and not probe_errors else None,
            'reload_comparison': recovery,
            'restart': 'NOT_EXECUTED — production host isolation unavailable',
            'host_upgrade': 'NOT_EXECUTED', 'wrong_identity_real_host': 'NOT_EXECUTED',
            'test_conversation': 'UNKNOWN', 'test_target': 'UNKNOWN',
            'photo': 'DISABLED' if not cfg['photos']['enabled'] else 'NOT_EXECUTED — dry_run only',
            'tool_probes': probe.get('probes', {}) if isinstance(probe, dict) else {},
            'delivery': delivery_trace([]),
            'validation_result': 'FAIL' if errors or probe is not None and probe_errors else 'PENDING_REAL_HOST_VALIDATION',
            'note': '本地探测和捕获文件一致性不能证明真实 Host、重启、本人聊天或送达；不得解锁 Full Private RP。'}
