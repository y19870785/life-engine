"""Exercise the installed Hermes dispatcher with a synthetic card and temporary home.

No provider calls, credentials, real profiles, gateway or message delivery.
Use Hermes's Python and --host-root pointing to its source checkout.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description='Hermes native card synthetic host probe')
    parser.add_argument('--host-root', required=True)
    args = parser.parse_args()
    host_root = Path(args.host_root).resolve()
    sys.path.insert(0, str(host_root))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
    # New Hermes launchers select a committed dependency tree outside the Python
    # prefix. Read its path without bootstrapping recovery or installing packages.
    try:
        from pm.environments import committed_venv, site_packages
        environment = committed_venv(host_root)
        if environment is not None:
            sys.path.insert(0, str(site_packages(environment)))
    except ImportError:
        pass
    from life_engine import hermes_card_import as ci
    with tempfile.TemporaryDirectory(prefix='hermes-native-probe-') as tmp:
        root = Path(tmp).resolve()
        profile_home = root / 'profiles' / 'synthetic'
        profile_home.mkdir(parents=True)
        os.environ['HERMES_HOME'] = str(profile_home)
        (profile_home / 'config.yaml').write_text('plugins:\n  enabled: [life-engine-character-card]\n', encoding='utf-8')
        (profile_home / 'SOUL.md').write_text('prior identity', encoding='utf-8')
        raw = {'name': '岚', 'description': '灯塔管理员。', 'first_mes': '灯刚亮。',
               'mes_example': '<START>\n{{user}}: 忙吗？\n{{char}}: 正在擦灯。',
               'post_history_instructions': '自然推进虚构日常。',
               'character_book': {'entries': [{'keys': ['灯塔'], 'content': '灯塔在北岸。',
                                              'enabled': True, 'position': 'after_char'}]}}
        source = root / 'source.json'; source.write_bytes(ci.json_bytes(raw))
        plan_path = root / 'plan.json'; ci.preview(source, plan_path, 'native')
        plan = json.loads(plan_path.read_bytes())
        plan['options']['acknowledged'] = [i['id'] for i in plan['issues']]
        plan_path.write_bytes(ci.json_bytes(plan))
        receipt = ci.apply(plan_path, profile_home, ci.digest(plan_path.read_bytes()))['receipt']
        from hermes_constants import get_hermes_home, set_hermes_home_override, reset_hermes_home_override
        from hermes_cli import plugins
        from hermes_cli.middleware import apply_llm_request_middleware
        assert get_hermes_home().resolve() == profile_home
        plugins.discover_plugins()
        manager = plugins.get_plugin_manager()
        assert manager.has_middleware('llm_request')
        ctx = dict(session_id='synthetic', turn_id='one', platform='cli')
        plugins.invoke_hook('pre_llm_call', user_message='灯塔在哪里？', **ctx)
        request = {'messages': [{'role': 'system', 'content': 'host instructions'},
                               {'role': 'user', 'content': '灯塔在哪里？'}],
                   'tools': [{'type': 'function', 'function': {'name': 'terminal'}}]}
        result = apply_llm_request_middleware(request, **ctx)
        assert result.changed and 'tools' not in result.payload
        assert '灯塔在北岸' in result.payload['messages'][1]['content']
        assert result.payload['messages'][-1]['content'] == '自然推进虚构日常。'
        block, _ = plugins._dispatch_pre_tool_call_hooks('terminal', {}, session_id='synthetic', turn_id='one')
        assert block
        retry = apply_llm_request_middleware(result.payload, **ctx)
        assert retry.payload == result.payload
        plugins.invoke_hook('pre_llm_call', **dict(ctx, parent_session_id='parent'))
        child = apply_llm_request_middleware(request, **ctx)
        assert not child.changed
        other = root / 'profiles' / 'other'; other.mkdir()
        token = set_hermes_home_override(other)
        try:
            cross = apply_llm_request_middleware(request, **ctx)
            assert not cross.changed
        finally:
            reset_hermes_home_override(token)
        manager.unload()
        ci.restore(profile_home, receipt)
        assert (profile_home / 'SOUL.md').read_text() == 'prior identity'
        assert ci.apply(plan_path, profile_home, ci.digest(plan_path.read_bytes()))['state'] == 'APPLIED'
        sha = subprocess.run(['git', '-C', str(host_root), 'rev-parse', 'HEAD'],
                             capture_output=True, text=True, check=True).stdout.strip()
        print(json.dumps({'state': 'SYNTHETIC_HOST_MIDDLEWARE_PASS', 'host_sha': sha,
                          'scope': 'real dispatcher; synthetic card/home/request; no model call',
                          'checks': ['discovery', 'composition', 'tool visibility', 'tool guard',
                                     'retry', 'child isolation', 'profile isolation', 'rollback/reinstall']},
                         ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
