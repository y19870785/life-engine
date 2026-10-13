"""Profile-bound Hermes Chat Completions adapter for the native card compiler."""
import hashlib
import json
import logging
import os
from pathlib import Path
import tempfile
import threading

from .hermes_card_runtime import assemble, validate

PLUGIN = 'life-engine-character-card'
_turns = {}
_lock = threading.RLock()


def bound_home():
    from hermes_constants import get_hermes_home
    folder = Path(__file__).resolve().parent
    binding = json.loads((folder / 'binding.json').read_text(encoding='utf-8'))
    home = Path(binding['profile_home']).resolve()
    if home != Path(get_hermes_home()).resolve() or folder != home / 'plugins' / PLUGIN:
        return None
    return home


def before(**kwargs):
    if bound_home() is None:
        return None
    key = (kwargs.get('session_id'), kwargs.get('turn_id'))
    with _lock:
        if len(_turns) >= 128:
            _turns.pop(next(iter(_turns)))
        _turns[key] = not kwargs.get('parent_session_id') and kwargs.get('platform') in ('cli', '')
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
        return None
    try:
        path = home / 'plugins' / PLUGIN / 'card.json'
        if path.is_symlink() or path.stat().st_size > 1024 * 1024:
            raise ValueError('INVALID_CARD_FILE')
        raw = path.read_bytes()
        plan = json.loads(raw)
        result, trace = assemble(plan, request)
        trace.update(card_sha256=hashlib.sha256(raw).hexdigest(), state='COMPOSED',
                     session_id=kwargs.get('session_id'), turn_id=kwargs.get('turn_id'))
    except Exception as exc:
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
        plan = validate(json.loads(path.read_bytes()))
    except Exception:
        return {'action': 'block', 'message': '角色工具配置暂不可用，本次工具调用已阻止。'}
    if kwargs.get('tool_name') not in plan['options']['allowed_tools']:
        return {'action': 'block', 'message': '当前角色会话未启用此工具，请在管理会话执行。'}
    return None


def register(ctx):
    if bound_home() is not None:
        ctx.register_hook('pre_llm_call', before)
        ctx.register_hook('pre_tool_call', guard_tool)
        ctx.register_middleware('llm_request', rewrite)
