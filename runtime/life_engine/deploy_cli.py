"""Guided permanent install and offline lifecycle management."""
import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from .config import defaults, load, validate
from .durable import (absolute, create_install, digest, health, instance_id, locked,
                      read, registry, restore, rollback_code, rollback_schema, snapshot, state_home, upgrade, write)
from .install import inspect_host
from .setup import ask, discover_homes, existing_cfg, guide, merged, yes


def plan_install(package, root, cfg, **options):
    host = absolute(cfg['integration']['host_home'])
    info = inspect_host(host, cfg['integration']['adapter'])
    hashes = dict(info['source_hashes'])
    regpath = root / 'registry.json'
    hashes[str(regpath)] = digest(regpath.read_bytes()) if regpath.exists() else None
    if regpath.exists():
        reg = registry(root)
        key = instance_id(cfg['integration']['adapter'], host)
        if key in reg['instances']:
            instance = reg['instances'][key]
            config_path = state_home(root, instance) / 'agents' / instance['agent_id'] / 'agent.json'
            hashes[str(config_path)] = digest(config_path.read_bytes())
    for path in [options.get('workflow')]:
        if path:
            target = absolute(path)
            hashes[str(target)] = digest(target.read_bytes())
    return {'format': 1, 'root': str(root), 'config': cfg, 'options': options, 'source_hashes': hashes,
            'summary': {'host': str(host), 'adapter': cfg['integration']['adapter'],
                'agent_id': cfg['agent_id'], 'permanent_root': str(root),
                'instance': instance_id(cfg['integration']['adapter'], host),
                'proactive': cfg['social']['enabled'], 'photos': cfg['photos']['enabled'],
                'persona': 'preserve all original SOUL/config files',
                'activation': 'native plugin connect and one persistent host schedule',
                'data_on_reinstall': 'preserve current settings unless reconfigure is explicitly selected'}}


def apply_preview(package, plan):
    if plan.get('format') != 1:
        raise ValueError('Unsupported install preview')
    for name, expected in plan['source_hashes'].items():
        path = absolute(name)
        actual = digest(path.read_bytes()) if path.exists() else None
        if actual != expected:
            raise ValueError('Configuration changed after preview; regenerate it: ' + name)
    return create_install(package, plan['root'], plan['config'], **plan['options'])


def main(package, argv=None, input_fn=input, output=print):
    p = argparse.ArgumentParser(description='Life Engine v0.3 永久安装与维护')
    p.add_argument('action', nargs='?', default='install',
                   choices=['install', 'upgrade', 'doctor', 'list', 'backup', 'restore', 'rollback-code', 'rollback-schema', 'connect', 'repair-python'])
    p.add_argument('--root', type=Path, default=Path.home() / '.life-engine')
    p.add_argument('--home', '--host-home', dest='home', type=Path)
    p.add_argument('--adapter', choices=['hermes', 'openclaw', 'generic'])
    p.add_argument('--host-agent-id', help='OpenClaw 当前配置中的实际 agentId')
    p.add_argument('--host-profile', help='OpenClaw 命名配置；独立于 Agent ID')
    p.add_argument('--instance')
    p.add_argument('--answers', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--apply', action='store_true')
    p.add_argument('--apply-plan', type=Path)
    p.add_argument('--reconfigure', action='store_true')
    p.add_argument('--import-v02', type=Path, help='旧 Agent/life-engine 目录，不是 ZIP 解压目录')
    p.add_argument('--legacy-stopped', action='store_true', help='已暂停旧定时任务并停止旧运行入口')
    p.add_argument('--backup', type=Path)
    p.add_argument('--python', type=Path)
    p.add_argument('--release', help='已安装的代码版本目录名，用于 rollback-code')
    p.add_argument('--checkpoint', type=Path, help='本安装的 Schema 整体回退记录')
    args = p.parse_args(argv)
    root = absolute(args.root)
    try:
        result = None
        if args.action == 'upgrade':
            result = upgrade(root, package)
        elif args.action == 'rollback-schema':
            if not args.checkpoint:
                raise ValueError('rollback-schema 需要 --checkpoint')
            result = rollback_schema(root, args.checkpoint)
        elif args.action == 'rollback-code':
            if not args.release:
                raise ValueError('rollback-code requires --release')
            result = rollback_code(root, args.release)
        elif args.action == 'list':
            reg = registry(root)
            result = {'release': reg['release'], 'instances': list(reg['instances'].values())}
        elif args.action == 'doctor':
            result = health(root, args.instance)
        elif args.action == 'connect':
            if not args.instance:
                raise ValueError('connect requires --instance')
            from .bridges import native_connect
            result = native_connect(root, args.instance, args.host_profile)
        elif args.action == 'backup':
            if not args.instance:
                raise ValueError('backup requires --instance')
            with locked(root, args.instance):
                reg = registry(root)
                saved = snapshot(root, reg, reg['instances'][args.instance], args.out)
                result = {'ok': True, 'backup': str(saved)}
        elif args.action == 'restore':
            if not args.instance or not args.backup:
                raise ValueError('restore requires --instance and --backup')
            result = restore(root, args.instance, args.backup)
        elif args.action == 'repair-python':
            if not args.python:
                raise ValueError('repair-python requires --python /absolute/path/to/python')
            executable = args.python.expanduser().resolve()
            check = subprocess.run([str(executable), '-c',
                'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)'],
                capture_output=True, timeout=10, shell=False)
            if check.returncode:
                raise ValueError('A working Python 3.11+ interpreter is required')
            with locked(root, 'management'):
                reg = registry(root)
                reg['python'] = str(executable)
                write(root / 'registry.json', reg)
            result = {'ok': True, 'python': str(executable)}
        elif args.apply_plan:
            result = apply_preview(package, read(args.apply_plan))
        else:
            if args.answers and (not args.home or not args.adapter):
                raise ValueError('--answers requires --home and --adapter')
            adapter = args.adapter or ask('宿主 hermes / openclaw / generic', 'hermes', input_fn=input_fn, output=output)
            if adapter not in ('hermes', 'openclaw', 'generic'):
                raise ValueError('Unknown adapter')
            if args.home:
                host = absolute(args.home)
            else:
                homes = discover_homes() if adapter == 'hermes' else []
                for h in homes:
                    output('检测到 Hermes Profile：' + h['home'])
                suggestion = homes[0]['home'] if len(homes) == 1 else ''
                host = absolute(ask('当前 Agent 的实际工作目录/Profile', suggestion, input_fn=input_fn, output=output))
            host_agent_id = args.host_agent_id or ''
            if adapter == 'openclaw' and not host_agent_id:
                if args.answers:
                    raise ValueError('OpenClaw requires --host-agent-id')
                host_agent_id = ask('OpenClaw 当前 Agent 的实际 agentId', '', input_fn=input_fn, output=output)
                if not host_agent_id:
                    raise ValueError('Use openclaw agents list to identify the actual Agent')
            key = instance_id(adapter, host)
            old = None
            current = None
            current_home = None
            if (root / 'registry.json').exists():
                reg = registry(root)
                old = reg['instances'].get(key)
                if old:
                    current, current_home = load(state_home(root, old), old['agent_id'])
            source = args.import_v02
            if source and not args.legacy_stopped:
                raise ValueError('Stop the old scheduler and entrypoints, then pass --legacy-stopped for a consistent one-time import')
            if source:
                candidates = list((absolute(source) / 'agents').glob('*/agent.json'))
                if len(candidates) != 1:
                    raise ValueError('Choose a v0.2 installation containing exactly one Agent')
                current = read(candidates[0])
                current_home = candidates[0].parent
            legacy_cfg = existing_cfg(host) if not current else None
            if legacy_cfg and not source:
                raise ValueError('Found v0.2 state. Stop the old entrypoints and use --import-v02 with --legacy-stopped; a new empty life must not replace it')
            workflow = None
            if args.answers:
                patch = read(args.answers)
                cfg = merged(copy.deepcopy(current) if current else defaults(patch.get('agent_id', 'assistant')), patch)
                workflow = patch.get('_workflow_source')
                owner_channel = patch.get('_owner_channel', old.get('owner_channel', '') if old else '')
                owner_sender = patch.get('_owner_sender_id', old.get('owner_sender_id', '') if old else '')
            else:
                cfg, _, workflow = guide(host, adapter, input_fn, output, current=current,
                                          agent_home=current_home, ask_append=False)
                owner_channel = ask('主人的聊天渠道（可留空，之后补齐）', old.get('owner_channel', '') if old else '', input_fn=input_fn, output=output)
                owner_sender = ask('主人的平台 sender ID（可留空，不猜测）', old.get('owner_sender_id', '') if old else '', input_fn=input_fn, output=output)
            cfg['integration'].update(adapter=adapter, host_home=str(host))
            cfg['persona']['soul_path'] = str(host / 'SOUL.md')
            validate(cfg)
            if old and not args.reconfigure:
                output('检测到永久安装：本次保留现有设置；修改设置请显式添加 --reconfigure。')
                cfg = current
            options = {'host_agent_id': host_agent_id, 'source': str(absolute(source)) if source else None,
                       'workflow': str(absolute(workflow)) if workflow else None, 'reconfigure': args.reconfigure,
                       'owner_channel': owner_channel, 'owner_sender_id': owner_sender}
            plan = plan_install(package, root, cfg, **options)
            output(json.dumps(plan['summary'], ensure_ascii=False, indent=2))
            out = absolute(args.out or Path(tempfile.gettempdir()).resolve() /
                           ('life-engine-plan-' + key + '-' + uuid.uuid4().hex[:8] + '.json'))
            if out.is_relative_to(host) or out.is_relative_to(root):
                raise ValueError('Save the preview outside both the host workspace and permanent installation')
            write(out, plan)
            output('安装预览：' + str(out))
            apply = args.apply or (not args.answers and yes('按预览安装到永久目录', True, input_fn, output))
            if apply:
                result = apply_preview(package, plan)
                output('永久安装完成。读取生成的 INSTALL.md，再连接原生插件和宿主持久化定时任务。')
            else:
                result = {'ok': True, 'installed': False, 'preview': str(out)}
        output(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('ok', True) else 1
    except (EOFError, KeyboardInterrupt):
        output('引导已取消。')
        return 2
    except Exception as exc:
        output(json.dumps({'ok': False, 'error': type(exc).__name__, 'message': str(exc)}, ensure_ascii=False))
        return 1
