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

# Exact offline import probe emitted by durable.probe_release in this snapshot.
IMPORT_PROBE = ('import sys; sys.path.insert(0, sys.argv[1]); from life_engine import cli, deploy_cli, durable\n'
                'if durable.DATA_SCHEMA != int(sys.argv[2]): raise ValueError("SchemaMismatch")\n'
                'if int(sys.argv[2]) >= 3: from life_engine.world_sqlite_repository import SQLiteWorldRepository\n'
                'if int(sys.argv[2]) >= 4: from life_engine.memory_runtime import MemoryRuntime\n'
                'if int(sys.argv[2]) >= 5: from life_engine.lore_runtime import LoreRuntime\n'
                'if int(sys.argv[2]) >= 6: from life_engine.story_runtime import StoryRuntime\n'
                'if int(sys.argv[2]) >= 7: from life_engine.bridge_runtime import BridgeRuntime\n')

# No git process is allowed. These optional version probes can use the Host's
# native OSError fallback; unknown commands still fail the admission boundary.
VERSION_QUERIES = (
    ('git', 'rev-parse', 'HEAD'), ('git', 'branch', '--show-current'),
    ('git', 'log', '-1', '--format=%ct', 'HEAD'),
    ('git', '--no-optional-locks', 'status', '--porcelain', '-uno'),
    ('git', 'tag', '--merged', 'HEAD', '--list', 'v[0-9]*'),
    ('git', 'describe', '--tags', '--long', '--match', 'v2[0-9][0-9][0-9].*', 'HEAD'),
    ('git', 'rev-parse', '--short=7', 'HEAD'),
)


def unlinked_identity(value):
    """Canonical existing path; short Windows names are aliases, links are not."""
    path = Path(value).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('LINKED_IDENTITY_REFUSED')
    return path.resolve(strict=True)


def optional_version_query(command, kwargs, config):
    host = config.get('host_root')
    if not host or tuple(command) not in VERSION_QUERIES or kwargs.get('executable') is not None:
        return False
    try:
        expected = unlinked_identity(Path(host) / 'hermes_cli/version_info.py')
        if unlinked_identity(kwargs.get('cwd', '')) != unlinked_identity(host):
            return False
        # Only the real optional version module may consume this recoverable denial.
        frame = sys._getframe(1)
        while frame is not None:
            if (frame.f_code.co_name in ('_run_git', '_git_version_info')
                    and unlinked_identity(frame.f_code.co_filename) == expected
                    and unlinked_identity(frame.f_globals.get('__file__', '')) == expected):
                return True
            frame = frame.f_back
    except (OSError, ValueError, TypeError):
        return False
    return False


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
    return path.resolve()


def restrict_processes(config, profile):
    original = subprocess.Popen
    interpreter = Path(config['python']).resolve(strict=True)
    allowed = []
    def audit(event, args):
        if event.startswith('socket.') or event in ('os.system', 'os.posix_spawn', 'os.exec', 'os.fork'):
            raise RuntimeError('T1_EXTERNAL_ACTION_DENIED')
        if event == 'subprocess.Popen' and (not allowed or args[1] not in (allowed[0], subprocess.list2cmdline(allowed[0]))):
            raise RuntimeError('T1_CHILD_DENIED')
    sys.addaudithook(audit)
    def spawn(command, *args, **kwargs):
        expected_prefix = [str(interpreter), '-I', '-X', 'utf8', '-c', RUNNER,
                           config['runtime'], 'character-continuity']
        expected_suffix = ['--root', config['root'], '--profile-home', str(profile),
                           '--card', str(profile / 'plugins/life-engine-character-card/card.json')]
        if not isinstance(command, list) or kwargs.get('shell') or args:
            raise RuntimeError('T1_CHILD_DENIED')
        command = list(command)
        if optional_version_query(command, kwargs, config):
            config.setdefault('version_query_denials', []).append(command)
            raise PermissionError('T1_OPTIONAL_VERSION_QUERY_DENIED')
        # durable and activation resolve the interpreter; accept only aliases of
        # the same existing file, then launch the pinned canonical path.
        try:
            if not Path(command[0]).is_absolute() or not Path(command[0]).samefile(interpreter):
                raise RuntimeError('T1_CHILD_DENIED')
        except (OSError, IndexError, TypeError):
            raise RuntimeError('T1_CHILD_DENIED') from None
        if kwargs.get('executable') is not None:
            raise RuntimeError('T1_CHILD_DENIED')
        command[0] = str(interpreter)
        if (len(command) == 15 and command[:8] == expected_prefix
                and command[8] in ('context', 'commit') and command[9:] == expected_suffix):
            command[5] = CHILD_GUARD + RUNNER
        elif (len(command) == 5 and command[:3] == [str(interpreter), '-c', IMPORT_PROBE]
              and command[4] == '8'):
            runtime = Path(command[3])
            releases = Path(config['root']) / 'releases'
            if (runtime.name != 'runtime' or runtime.parent.parent != releases
                    or runtime.resolve() != runtime.absolute()
                    or tree_digest(runtime) != config.get('runtime_sha256')):
                raise RuntimeError('T1_CHILD_DENIED')
            command[2] = CHILD_GUARD + IMPORT_PROBE
        else:
            raise RuntimeError('T1_CHILD_DENIED')
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
    parser.add_argument('--dependency-site', required=True)
    parser.add_argument('--expected-dependency-sha256', required=True)
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
    config = {'python': sys.executable, 'runtime': '', 'root': str(root / 'world'),
              'runtime_sha256': args.expected_runtime_sha256, 'host_root': str(host)}
    restrict_processes(config, profile)
    dependency = Path(args.dependency_site).absolute()
    report = {'state': 'PENDING', 'scope': 'T1 real dispatcher; synthetic lifecycle and rows; no model/CLI turn',
              'runtime_sha256': args.expected_runtime_sha256, 'model_requests': 0,
              'real_send': False, 'events': []}
    db = manager = receipt = None
    ci = cc = None
    try:
        marker = dependency / 'ruamel/yaml/__init__.py'
        for part in (marker, *marker.parents):
            if part.is_symlink() or (part.exists() and getattr(part.lstat(), 'st_file_attributes', 0) & 0x400):
                raise ValueError('LINKED_DEPENDENCY_REFUSED')
        if hashlib.sha256(marker.read_bytes()).hexdigest() != args.expected_dependency_sha256:
            raise ValueError('DEPENDENCY_HASH_MISMATCH')
        if dependency.parent.name != 'python' + str(sys.version_info.major) + '.' + str(sys.version_info.minor):
            raise ValueError('DEPENDENCY_PYTHON_VERSION_MISMATCH')
        sys.path.insert(0, str(dependency))
        import ruamel.yaml
        if Path(ruamel.yaml.__file__).resolve() != marker.resolve():
            raise ValueError('DEPENDENCY_IMPORT_PATH_MISMATCH')
        from hermes_state import SessionDB
        from agent.message_metadata import stamp_message_uid
        from hermes_constants import get_hermes_home
        from hermes_cli import plugins
        from hermes_cli.middleware import apply_llm_request_middleware
        if get_hermes_home().resolve() != profile:
            raise ValueError('HOST_HOME_MISMATCH')
        report.update(dependency_site=str(dependency), dependency_marker_sha256=args.expected_dependency_sha256,
                      loaded_modules={name: str(Path(sys.modules[name].__file__).resolve())
                                      for name in ('ruamel.yaml', 'hermes_state', 'agent.message_metadata',
                                                   'hermes_cli.plugins', 'hermes_cli.middleware')})
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
        report['host_files'] = config['host_files']
        db = SessionDB(db_path=profile / 'state.db')
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
            ('db_close', lambda: db.close() if db is not None else None),
            ('plugin_unload', lambda: manager.unload() if manager is not None else None),
            ('disable_v2', lambda: cc.activation(root / 'world', profile, sha, False)
             if cc is not None and (profile / '.life-engine-continuity.json').exists() else None),
            ('restore_plugin', lambda: ci.restore(profile, receipt) if receipt is not None else None),
        ):
            try:
                action()
            except Exception as exc:
                cleanup_errors.append({'step': name, 'error_type': type(exc).__name__})
        report['version_metadata'] = {
            'optional_queries_denied': config.get('version_query_denials', []),
            'state': 'UNAVAILABLE_QUERIES_DENIED' if config.get('version_query_denials') else 'NOT_OBSERVED',
            'identity_source': 'external Host file and Git verification; not this optional API',
        }
        if config.get('version_query_denials'):
            report['version_metadata']['expected_native_fallback'] = 'source=git; version=unknown; commit/branch=None'
        report['cleanup'] = {'errors': cleanup_errors, 'synthetic_evidence_retained': True}
        if cleanup_errors:
            report['state'] = 'T1_CLEANUP_INCOMPLETE'
        (root / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        if cleanup_errors and sys.exc_info()[0] is None:
            raise RuntimeError('T1_CLEANUP_INCOMPLETE')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
