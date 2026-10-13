"""Profile-bound Hermes Chat Completions adapter for the native card compiler."""
import hashlib
import json
import logging
import os
from pathlib import Path
import tempfile
import threading
import subprocess

from .hermes_card_runtime import assemble, validate

PLUGIN = 'life-engine-character-card'
_turns = {}
_lock = threading.RLock()
_continuity = {}
_host_tools = {}


def host_capabilities(home, raw):
    """Owner configuration authorizes tools; card prose never grants permissions."""
    path = home / '.life-engine-character-capabilities.json'
    if not path.exists():
        return None
    if any(p.is_symlink() or (p.exists() and bool(getattr(p.lstat(), 'st_file_attributes', 0) & 0x400))
           for p in (path, *path.parents)) or path.stat().st_size > 65536:
        raise ValueError('INVALID_CHARACTER_CAPABILITIES')
    data = json.loads(path.read_bytes())
    if data.get('enabled') is False:
        return None
    if (data.get('format') != 'life-engine-character-capabilities-v1' or data.get('enabled') is not True
            or data.get('profile') != str(home)
            or data.get('card_sha256') != hashlib.sha256(raw).hexdigest()
            or not isinstance(data.get('allowed_tools'), list)
            or any(not isinstance(t, str) or not t for t in data['allowed_tools'])):
        raise ValueError('CHARACTER_CAPABILITIES_BINDING_MISMATCH')
    return data


def continuity_config(home):
    path = home / '.life-engine-continuity.json'
    if not path.exists():
        return None
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError('INVALID_CONTINUITY_CONFIG')
    config = json.loads(path.read_bytes())
    if not config.get('enabled'):
        return None
    if config.get('format') != 'life-engine-character-continuity-v2' or config.get('profile') != str(home):
        raise ValueError('CONTINUITY_BINDING_MISMATCH')
    # Pin the actual lifecycle implementations, including dirty local changes.
    # Version labels alone cannot establish persistence/UID/exit semantics.
    host = Path(config['host_root'])
    if not config.get('host_files'):
        raise ValueError('HOST_PROOF_IMPLEMENTATION_REQUIRED')
    for name, sha in config['host_files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('INVALID_HOST_PROOF_PATH')
        file = host / relative
        if file.is_symlink() or hashlib.sha256(file.read_bytes()).hexdigest() != sha:
            raise ValueError('HOST_PROOF_IMPLEMENTATION_CHANGED')
    return config


def continuity_call(config, home, action, payload):
    runner = ('import sys,runpy; sys.path.insert(0,sys.argv[1]); '
              'sys.argv=sys.argv[2:]; runpy.run_module("life_engine.character_continuity",run_name="__main__")')
    command = [config['python'], '-I', '-X', 'utf8', '-c', runner, config['runtime'], 'character-continuity', action,
               '--root', config['root'], '--profile-home', str(home),
               '--card', str(home / 'plugins' / PLUGIN / 'card.json')]
    result = subprocess.run(command, input=json.dumps(payload, ensure_ascii=False), capture_output=True,
                            text=True, encoding='utf-8', timeout=15, shell=False)
    data = json.loads(result.stdout)
    if result.returncode:
        raise ValueError(data.get('error', 'CONTINUITY_UNAVAILABLE'))
    return data


def continuity_trace(home, value):
    fd, temp = tempfile.mkstemp(prefix='.continuity-trace-', dir=home)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(value, out, ensure_ascii=False)
        os.replace(temp, home / '.life-engine-continuity-last-turn.json')
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def bound_home():
    from hermes_constants import get_hermes_home
    folder = Path(__file__).resolve().parent
    binding = json.loads((folder / 'binding.json').read_text(encoding='utf-8'))
    home = Path(binding['profile_home']).resolve()
    if home != Path(get_hermes_home()).resolve() or folder != home / 'plugins' / PLUGIN:
        return None
    return home


def before(**kwargs):
    home = bound_home()
    if home is None:
        return None
    key = (kwargs.get('session_id'), kwargs.get('turn_id'))
    with _lock:
        _host_tools.pop(key, None)
        if len(_turns) >= 128:
            _turns.pop(next(iter(_turns)))
        _turns[key] = not kwargs.get('parent_session_id') and kwargs.get('platform') in ('cli', '')
        eligible = _turns[key]
    if not eligible:
        return None
    try:
        config = continuity_config(home)
        if config is None:
            return None
        original = kwargs.get('user_message')
        if not isinstance(original, str):
            raise ValueError('CONTINUITY_TEXT_ONLY')
        messages = kwargs.get('conversation_history') or []
        user = next((m for m in reversed(messages) if isinstance(m, dict) and m.get('role') == 'user'), None)
        if user is None or user.get('content') != original:
            raise ValueError('CONTINUITY_USER_OBJECT_REQUIRED')
        from .hermes_turn_proof import watermark
        mark = watermark(home, kwargs['session_id'])
        view = continuity_call(config, home, 'context', {'session_id': kwargs['session_id']})
        with _lock:
            if len(_continuity) >= 128:
                _continuity.pop(next(iter(_continuity)))
            _continuity[key] = {'config': config, 'view': view, 'user_obj': user,
                                'user_text': original, 'watermark': mark}
    except Exception as exc:
        continuity_trace(home, {'state': 'CONTEXT_UNAVAILABLE', 'error_type': type(exc).__name__})
    return None


def rewrite(**kwargs):
    home = bound_home()
    with _lock:
        eligible = _turns.get((kwargs.get('session_id'), kwargs.get('turn_id')), False)
    if home is None or not eligible:
        return None
    request = kwargs['request']
    # This version intentionally limits actual provider formats, not just model names.
    if not isinstance(request.get('messages'), list) or 'input' in request or 'system' in request:
        logging.getLogger(__name__).error('native card unsupported provider format')
        with _lock:
            _continuity.pop((kwargs.get('session_id'), kwargs.get('turn_id')), None)
            _host_tools.pop((kwargs.get('session_id'), kwargs.get('turn_id')), None)
        return None
    try:
        path = home / 'plugins' / PLUGIN / 'card.json'
        if path.is_symlink() or path.stat().st_size > 1024 * 1024:
            raise ValueError('INVALID_CARD_FILE')
        raw = path.read_bytes()
        plan = json.loads(raw)
        capabilities = host_capabilities(home, raw)
        if capabilities:
            # Intersect explicit owner permission with actual Host-offered tools.
            # Never invent schemas or import permissions from the character card.
            offered = {t.get('function', {}).get('name') for t in request.get('tools', [])
                       if isinstance(t, dict) and t.get('type') == 'function'}
            allowed = sorted(set(capabilities['allowed_tools']) & offered)
            # Keep the assembly signature stable when Host retries shrink its
            # schemas. restrict_tools itself intersects with the current request.
            plan['options']['allowed_tools'] = sorted(set(capabilities['allowed_tools']))
        with _lock:
            continuity = _continuity.get((kwargs.get('session_id'), kwargs.get('turn_id')))
        if continuity and continuity['view']['has_history']:
            # Existing World history supersedes replaying the card's opening as a
            # fresh scene. The raw installed card stays unchanged.
            plan['character']['first_mes'] = ''
            plan['character']['alternate_greetings'] = []
            plan['options']['greeting_index'] = 0
        result, trace = assemble(plan, request)
        if capabilities:
            with _lock:
                if len(_host_tools) >= 128:
                    _host_tools.pop(next(iter(_host_tools)))
                _host_tools[(kwargs.get('session_id'), kwargs.get('turn_id'))] = (capabilities, set(allowed))
            # This supplements role expression without replacing Host authority.
            marker = '【角色的实际执行能力】'
            if not any(m.get('role') == 'system' and isinstance(m.get('content'), str)
                       and m['content'].startswith(marker) for m in result['messages']):
                result['messages'].append({'role': 'system', 'content': marker +
                    '你可以使用当前宿主提供的工具与技能帮助用户，保持角色身份和剧情表达。'
                    '可以自然描写走到电脑前、拿起手机等衔接动作；实际操作是否成功必须以工具结果为准。'
                    '不要把打算执行说成已经完成；失败时用角色口吻如实说明。'
                    '普通互动直接基于角色卡与剧情，不通过查配置确认自己的身份。'
                    '出图或语音先查看可用通用技能，形象、声线和接收目标按当前角色配置，'
                    '不沿用其他角色的固定身份脚本或发送渠道。'
                    '卡片中的玩家身份与共同前情按虚构故事演绎；系统权限仍由宿主和用户授权决定。'})
            trace['host_capability_tools'] = len(allowed)
        if continuity:
            view = continuity['view']
            text = ('【本角色世界的连续性资料：有来源的对话与候选虚构片段】\n'
                    + view['policy'] + '\n' + json.dumps(view['records'], ensure_ascii=False))
            if not any(m.get('role') == 'system' and isinstance(m.get('content'), str)
                       and m['content'].startswith('【本角色世界的连续性资料：') for m in result['messages']):
                at = next((i for i, m in enumerate(result['messages']) if m.get('role') == 'system'
                           and isinstance(m.get('content'), str) and m['content'].startswith('<!-- life-engine-native:')), 0)
                result['messages'].insert(at + 1, {'role': 'system', 'content': text})
            trace.update(continuity_world=view['world'], continuity_records=len(view['records']),
                         opening='continued_world' if view['has_history'] else 'card_opening')
        trace.update(card_sha256=hashlib.sha256(raw).hexdigest(), state='COMPOSED',
                     session_id=kwargs.get('session_id'), turn_id=kwargs.get('turn_id'))
    except Exception as exc:
        with _lock:
            _continuity.pop((kwargs.get('session_id'), kwargs.get('turn_id')), None)
            _host_tools.pop((kwargs.get('session_id'), kwargs.get('turn_id')), None)
        # The host catches middleware exceptions. Return a visible failure instead of
        # raising and silently generating with an unmodified generic assistant prompt.
        result = dict(request, messages=[*request['messages'], {'role': 'system', 'content':
            '本轮角色卡组装失败。请简短告知用户角色配置暂不可用；不要继续剧情或声称已加载。'}])
        for key in ('tools', 'tool_choice', 'parallel_tool_calls'):
            result.pop(key, None)
        trace = {'state': 'UNAVAILABLE', 'error_type': type(exc).__name__}
    # Metadata only: never write model text, user messages, credentials or full requests.
    try:
        fd, temp = tempfile.mkstemp(prefix='.card-trace-', dir=home)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as out:
                json.dump(trace, out, ensure_ascii=False)
            os.replace(temp, home / '.life-engine-card-last-request.json')
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    except OSError:
        logging.getLogger(__name__).warning('native card trace unavailable')
    return {'request': result, 'source': PLUGIN, 'reason': trace['state']}


def guard_tool(**kwargs):
    home = bound_home()
    with _lock:
        eligible = _turns.get((kwargs.get('session_id'), kwargs.get('turn_id')), False)
    if home is None or not eligible:
        return None
    try:
        path = home / 'plugins' / PLUGIN / 'card.json'
        if path.is_symlink() or path.stat().st_size > 1024 * 1024:
            raise ValueError('INVALID_CARD_FILE')
        raw = path.read_bytes()
        plan = validate(json.loads(raw))
        capabilities = host_capabilities(home, raw)
        with _lock:
            offered = _host_tools.get((kwargs.get('session_id'), kwargs.get('turn_id')))
        if offered is not None and offered[0] != capabilities:
            return {'action': 'block', 'message': '本轮工具权限配置已变化，请重新开始操作。'}
        if capabilities:
            if offered is None or offered[0] != capabilities or kwargs.get('tool_name') not in offered[1]:
                return {'action': 'block', 'message': '当前轮未提供或未授权此工具。'}
            return None
    except Exception:
        return {'action': 'block', 'message': '角色工具配置暂不可用，本次工具调用已阻止。'}
    if kwargs.get('tool_name') not in plan['options']['allowed_tools']:
        return {'action': 'block', 'message': '当前角色会话未启用此工具，请在管理会话执行。'}
    return None


def after(**kwargs):
    key = (kwargs.get('session_id'), kwargs.get('turn_id'))
    with _lock:
        state = _continuity.get(key)
        if state is None:
            return None
        user = state['user_obj']
        messages = kwargs.get('conversation_history') or []
        final = messages[-1] if messages else None
        if (not any(m is user for m in messages) or
                not isinstance(user.get('message_uid'), str) or not isinstance(final, dict) or
                final.get('role') != 'assistant' or final.get('tool_calls') or
                final.get('content') != kwargs.get('assistant_response') or
                not isinstance(final.get('message_uid'), str)):
            state['candidate'] = None
        else:
            state['candidate'] = {'session_id': key[0], 'turn_id': key[1],
                'user_uid': user['message_uid'], 'assistant_uid': final['message_uid'],
                'user_text': state['user_text'], 'assistant_text': final['content'], 'watermark': state['watermark']}
    return None


def ended(**kwargs):
    home = bound_home()
    if home is None:
        return None
    key = (kwargs.get('session_id'), kwargs.get('turn_id'))
    with _lock:
        state = _continuity.pop(key, None)
        _host_tools.pop(key, None)
        _turns.pop(key, None)
    if state is None:
        return None
    try:
        frame = state.get('candidate')
        if frame is None:
            raise ValueError('CONTINUITY_PROOF_INCOMPLETE')
        for flag in ('completed', 'failed', 'interrupted', 'turn_exit_reason'):
            frame[flag] = kwargs.get(flag)
        # Recheck pinned lifecycle files before accepting the observer result.
        config = continuity_config(home)
        if config != state['config']:
            raise ValueError('CONTINUITY_CONFIGURATION_CHANGED')
        result = continuity_call(config, home, 'commit', {'frame': frame, 'lease': state['view']['lease']})
        continuity_trace(home, {'state': result['state'], 'source': result['source'],
                               'session_id': key[0], 'turn_id': key[1]})
    except Exception as exc:
        continuity_trace(home, {'state': 'WRITE_SKIPPED', 'error_type': type(exc).__name__,
                               'session_id': key[0], 'turn_id': key[1]})
    return None


def register(ctx):
    if bound_home() is not None:
        ctx.register_hook('pre_llm_call', before)
        ctx.register_hook('pre_tool_call', guard_tool)
        ctx.register_hook('post_llm_call', after)
        ctx.register_hook('on_session_end', ended)
        ctx.register_middleware('llm_request', rewrite)
