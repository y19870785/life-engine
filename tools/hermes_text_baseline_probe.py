"""T1: real Hermes dispatcher, synthetic lifecycle/rows; no model or delivery.

Run only after review, using the Host interpreter. --root must not exist.
Raw synthetic evidence is preserved under that root, including on failure.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

RUNNER = ('import sys,runpy; sys.path.insert(0,sys.argv[1]); '
          'sys.argv=sys.argv[2:]; runpy.run_module("life_engine.character_continuity",run_name="__main__")')
CHILD_GUARD = ('import sys; sys.dont_write_bytecode=True; sys.addaudithook(lambda e,a: '
               '(_ for _ in ()).throw(RuntimeError("T1_EXTERNAL_ACTION_DENIED")) '
               'if e.startswith("socket.") or e in '
               '("subprocess.Popen","os.system","os.posix_spawn","os.exec","os.fork") else None); ')


def tree_digest(folder):
    digest = hashlib.sha256()
    for path in sorted(folder.rglob('*.py')):
        digest.update(path.relative_to(folder).as_posix().encode() + b'\0')
        digest.update(path.read_bytes())
    return digest.hexdigest()


def new_root(value):
    path = Path(value).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('LINKED_ROOT_REFUSED')
    if path.exists() or not path.parent.is_dir():
        raise ValueError('NEW_ROOT_REQUIRED')
    return path


def restrict_processes(config, profile):
    original = subprocess.Popen
    allowed = []
    def audit(event, args):
        if event.startswith('socket.') or event in ('os.system', 'os.posix_spawn', 'os.exec', 'os.fork'):
            raise RuntimeError('T1_EXTERNAL_ACTION_DENIED')
        if event == 'subprocess.Popen' and (not allowed or args[1] not in (allowed[0], subprocess.list2cmdline(allowed[0]))):
            raise RuntimeError('T1_CHILD_DENIED')
    sys.addaudithook(audit)
    def spawn(command, *args, **kwargs):
        expected_prefix = [config['python'], '-I', '-X', 'utf8', '-c', RUNNER,
                           config['runtime'], 'character-continuity']
        expected_suffix = ['--root', config['root'], '--profile-home', str(profile),
                           '--card', str(profile / 'plugins/life-engine-character-card/card.json')]
        if (not isinstance(command, list) or len(command) != 15 or command[:8] != expected_prefix
                or command[8] not in ('context', 'commit') or command[9:] != expected_suffix
                or kwargs.get('shell') or args):
            raise RuntimeError('T1_CHILD_DENIED')
        command = list(command); command[5] = CHILD_GUARD + RUNNER
        kwargs['env'] = dict(os.environ)
        allowed[:] = [command]
        try:
            return original(command, **kwargs)
        finally:
            allowed.clear()
    subprocess.Popen = spawn


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-root', required=True)
    parser.add_argument('--root', required=True)
    parser.add_argument('--expected-runtime-sha256', required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parents[1]
    runtime = package / 'runtime'
    if tree_digest(runtime) != args.expected_runtime_sha256:
        raise ValueError('RUNTIME_HASH_MISMATCH')
    root = new_root(args.root)
    root.mkdir()
    profile = root / 'profiles/synthetic'; profile.mkdir(parents=True)
    # Do not inherit provider keys, credential selectors, proxy or production HOME.
    keep = {key: value for key, value in os.environ.items()
            if key in ('PATH', 'SYSTEMROOT', 'WINDIR', 'LANG', 'LC_ALL')}
    os.environ.clear(); os.environ.update(keep)
    os.environ.update(HOME=str(root), USERPROFILE=str(root), HERMES_HOME=str(profile),
                      PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    host = Path(args.host_root).resolve()
    sys.path.insert(0, str(host)); sys.path.insert(0, str(runtime))
    # Block network/processes during Host imports and plugin discovery too.
    config = {'python': sys.executable, 'runtime': '', 'root': str(root / 'world')}
    restrict_processes(config, profile)
    from pm.environments import committed_venv, site_packages
    environment = committed_venv(host)
    if environment is not None:
        sys.path.insert(0, str(site_packages(environment)))
    from life_engine import hermes_card_import as ci, character_continuity as cc
    (profile / 'config.yaml').write_text('plugins:\n  enabled: [life-engine-character-card]\n', encoding='utf-8')
    source = root / 'source.json'
    source.write_bytes(ci.json_bytes({'name': '岚', 'description': '灯塔管理员。', 'first_mes': '灯刚亮。'}))
    plan_path = root / 'plan.json'; ci.preview(source, plan_path, 'native')
    plan = json.loads(plan_path.read_bytes())
    plan['options']['acknowledged'] = [issue['id'] for issue in plan['issues']]
    plan_path.write_bytes(ci.json_bytes(plan))
    receipt = ci.apply(plan_path, profile, ci.digest(plan_path.read_bytes()))['receipt']
    card = profile / 'plugins/life-engine-character-card/card.json'
    sha = cc.digest(card.read_bytes())
    cc.init(root / 'world', profile, card, package)
    cc.activation(root / 'world', profile, sha, True, host)
    config.update(json.loads((profile / '.life-engine-continuity.json').read_bytes()))
    if tree_digest(Path(config['runtime'])) != args.expected_runtime_sha256:
        raise ValueError('FROZEN_RUNTIME_HASH_MISMATCH')
    from hermes_state import SessionDB
    from agent.message_metadata import stamp_message_uid
    from hermes_constants import get_hermes_home
    from hermes_cli import plugins
    from hermes_cli.middleware import apply_llm_request_middleware
    if get_hermes_home().resolve() != profile:
        raise ValueError('HOST_HOME_MISMATCH')
    report = {'state': 'PENDING', 'scope': 'T1 real dispatcher; synthetic lifecycle and rows; no model/CLI turn',
              'runtime_sha256': args.expected_runtime_sha256, 'host_files': config['host_files'],
              'model_requests': 0, 'real_send': False, 'events': []}
    db = SessionDB(db_path=profile / 'state.db')
    manager = None
    try:
        plugins.discover_plugins(); manager = plugins.get_plugin_manager()
        if not manager.has_middleware('llm_request'):
            raise ValueError('MIDDLEWARE_MISSING')
        def dispatch(event, **kwargs):
            plugins.invoke_hook(event, **kwargs)
            report['events'].append({'hook': event, 'session_id': kwargs['session_id']})
        first = dict(session_id='t1-first', turn_id='t1-one', platform='cli')
        db.create_session(first['session_id'], source='cli')
        user = {'role': 'user', 'content': '我明天下午去面试。'}
        dispatch('pre_llm_call', user_message=user['content'], conversation_history=[user], **first)
        request = apply_llm_request_middleware({'messages': [user], 'tools': []}, **first).payload
        if '灯刚亮。' not in json.dumps(request, ensure_ascii=False) or request.get('tools'):
            raise ValueError('OPENING_OR_TOOL_FAILURE')
        final = {'role': 'assistant', 'content': '岚准备傍晚去码头散步。'}
        for message in (user, final):
            stamp_message_uid(message)
            db.append_message(first['session_id'], message['role'], message['content'],
                              message_uid=message['message_uid'])
        dispatch('post_llm_call', assistant_response=final['content'], conversation_history=[user, final], **first)
        dispatch('on_session_end', completed=True, failed=False, interrupted=False,
                 turn_exit_reason='text_response(finish_reason=stop)', **first)
        trace = json.loads((profile / '.life-engine-continuity-last-turn.json').read_bytes())
        if trace['state'] != 'COMMITTED':
            raise ValueError('HOOK_COMMIT_FAILED')
        before = cc.status(root / 'world', profile, sha)
        future = dict(session_id='t1-next', turn_id='t1-two', platform='cli')
        db.create_session(future['session_id'], source='cli')
        follow = {'role': 'user', 'content': '我们继续。'}
        dispatch('pre_llm_call', user_message=follow['content'], conversation_history=[follow], **future)
        result = apply_llm_request_middleware({'messages': [follow], 'tools': []}, **future).payload
        text = json.dumps(result, ensure_ascii=False)
        if any(value not in text for value in (user['content'], final['content'], 'user_claimed_fact', 'candidate')):
            raise ValueError('CONTINUITY_PROJECTION_MISSING')
        if '灯刚亮。' in text or result.get('tools'):
            raise ValueError('REPLAYED_OPENING_OR_TOOLS')
        after = cc.status(root / 'world', profile, sha)
        if before['world'] != after['world'] or after['turns'] != {'COMMITTED': 1}:
            raise ValueError('WORLD_OR_COUNT_MISMATCH')
        report.update(state='T1_SYNTHETIC_CONTINUITY_PASS', world=after['world'], commit_trace=trace,
                      checks=['real UID API', 'real SessionDB', 'dispatcher commit', 'new session projection',
                              'source separation', 'opening not replayed', 'empty tools'])
    except Exception as exc:
        report.update(state='T1_FAILED', error_type=type(exc).__name__)
        raise
    finally:
        cleanup_errors = []
        for name, action in (
            ('db_close', db.close),
            ('plugin_unload', lambda: manager.unload() if manager is not None else None),
            ('disable_v2', lambda: cc.activation(root / 'world', profile, sha, False)),
            ('restore_plugin', lambda: ci.restore(profile, receipt)),
        ):
            try:
                action()
            except Exception as exc:
                cleanup_errors.append({'step': name, 'error_type': type(exc).__name__})
        report['cleanup'] = {'errors': cleanup_errors, 'synthetic_evidence_retained': True}
        if cleanup_errors:
            report['state'] = 'T1_CLEANUP_INCOMPLETE'
        (root / 'report.json').write_bytes(ci.json_bytes(report))
        if cleanup_errors and sys.exc_info()[0] is None:
            raise RuntimeError('T1_CLEANUP_INCOMPLETE')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
