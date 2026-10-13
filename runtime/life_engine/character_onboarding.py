"""Private card inspection and selected-opening plans for named Hermes Profiles."""
import argparse
import json
import importlib
import os
from pathlib import Path

from . import hermes_card_import as ci, hermes_card_runtime as native
from .import_cards import parse_card
from . import character_continuity as continuity
from .hermes_capabilities import configure


def inspect(card_path, *, details=False, user_name='用户'):
    ir = parse_card(card_path)
    plan = native.compile_plan(ir.preserved_source.value(), ir.source_fingerprint)
    plan['options']['user_name'] = user_name
    character = plan['character']
    openings = []
    for index, value in enumerate([character['first_mes'], *character['alternate_greetings']]):
        openings.append({'index': index, 'kind': 'default' if index == 0 else 'alternate',
                         'text': native.expand(value, character, plan['options'])})
    result = {'format': 'life-engine-character-story-view-v1', 'source_sha256': ir.source_fingerprint,
              'name': character['name'], 'scenario': native.expand(character['scenario'], character, plan['options']),
              'player': '按原卡正文与开场中的默认 {{user}} 身份互动；未提供独立用户 Persona 时不自行补定身份。',
              'openings': openings, 'compatibility': plan['issues'],
              'worldbook': {'entries': len(plan['entries']),
                            'enabled': sum(row['enabled'] for row in plan['entries'])},
              'private': True, 'notice': '作者场景和开场可能含剧透；不展示世界书全文，不声称已自动识别秘密。'}
    if details:
        result['author_character_description'] = character['description']
        result['author_personality'] = character['personality']
        result['notice'] += ' 完整角色说明也可能含作者秘密。'
    return result


def prepare(card_path, output, opening_index, *, acknowledged=(), user_name='用户', user_persona='',
            disabled_entries=(), lore_budget=None):
    ir = parse_card(card_path)
    plan = native.compile_plan(ir.preserved_source.value(), ir.source_fingerprint)
    plan['options'].update(greeting_index=opening_index, user_name=user_name, user_persona=user_persona,
                           acknowledged=list(acknowledged))
    for identifier in disabled_entries:
        row = next((row for row in plan['entries'] if row['id'] == identifier), None)
        if row is None:
            raise ValueError('UNKNOWN_WORLDBOOK_ENTRY')
        row['enabled'] = False
    if lore_budget is not None:
        plan['options']['lore_budget'] = lore_budget
    # Review remains explicit; selecting an opening is not blanket acceptance of
    # missing scripts/worldbook behavior. Raw author content is never rewritten.
    native.validate(plan)
    native.assemble(plan, {'messages': []})
    path = ci.safe(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = ci.json_bytes(plan)
    with path.open('xb') as stream:
        stream.write(raw)
    return {'state': 'PREPARED', 'plan': str(path), 'sha256': ci.digest(raw),
            'opening_index': opening_index, 'opening': native.opening(plan), 'private': True}


def install(plan_path, expected_sha, profile, source_home, root, host_root, tools_file, package):
    home = ci.home_path(profile)
    lock = ci.safe(home / '.life-engine-onboarding.lock')
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        return _install(plan_path, expected_sha, home, source_home, root, host_root, tools_file, package)
    finally:
        lock.unlink()


def _install(plan_path, expected_sha, profile, source_home, root, host_root, tools_file, package):
    setup = importlib.import_module('.hermes_profile_setup', __package__)
    home, root = ci.home_path(profile), ci.safe(root)
    if root.exists() or root.is_relative_to(home) or home.is_relative_to(root):
        raise ValueError('NEW_SEPARATE_WORLD_ROOT_REQUIRED')
    progress = home / '.life-engine-onboarding.json'
    if progress.exists():
        raise ValueError('ONBOARDING_ALREADY_STARTED')
    raw = ci.read(plan_path)
    if ci.digest(raw) != expected_sha:
        raise ValueError('PLAN_CHANGED')
    plan = native.validate(json.loads(raw))
    native.assemble(plan, {'messages': []})
    tool_bytes = ci.read(tools_file)
    names = json.loads(tool_bytes)
    if not isinstance(names, list) or any(not isinstance(t, str) or not t for t in names):
        raise ValueError('TOOL_NAME_LIST_REQUIRED')
    # Validate actual lifecycle files before any Profile change.
    for name in continuity.HOST_FILES:
        ci.read(Path(host_root) / name)
    setup.configure_host(host_root)
    prepared = setup.prepare(source_home, home)
    record = {'format': 'life-engine-character-onboarding-v1', 'state': 'STARTED',
              'profile': str(home), 'root': str(root), 'plan_sha256': expected_sha,
              'opening_index': plan['options']['greeting_index'], 'stage': 'CONFIG',
              'scope': 'local CLI installation; no model, media or channel execution'}
    def checkpoint(stage):
        record['stage'] = stage
        ci.atomic(progress, ci.json_bytes(record))
    try:
        checkpoint('CONFIG')
        record['config_receipt'] = setup.apply(prepared)
        checkpoint('CARD')
        record['card_receipt'] = ci.apply(plan_path, home, expected_sha)['receipt']
        card = home / 'plugins/life-engine-character-card/card.json'
        card_sha = ci.digest(ci.read(card))
        record['card_sha256'] = card_sha
        checkpoint('WORLD')
        record['world'] = continuity.init(root, home, card, package)['world']
        checkpoint('CONTINUITY')
        continuity.activation(root, home, card_sha, True, host_root)
        checkpoint('CAPABILITIES')
        if ci.digest(ci.read(tools_file)) != ci.digest(tool_bytes):
            raise ValueError('TOOLS_CHANGED')
        configure(home, tools_file, card_sha)
        record['state'] = 'INSTALLED'
        checkpoint('DONE')
        return {'state': 'INSTALLED', 'profile': str(home), 'world': record['world'],
                'opening_index': record['opening_index'], 'receipt': str(progress),
                'next': '新开该Profile的CLI；选其他开场应建立新的Profile/World，不能重置已有故事。',
                'host_verified': False}
    except Exception as exc:
        # No destructive cleanup or implicit reinstallation of a partially created
        # world. Receipts identify exact stages for owner-managed recovery.
        record.update(state='FAILED_PARTIAL', error_type=type(exc).__name__)
        ci.atomic(progress, ci.json_bytes(record))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description='查看角色故事与全部开场，并生成选定开场的独立安装计划')
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('inspect'); p.add_argument('--card', required=True)
    p.add_argument('--details', action='store_true'); p.add_argument('--user-name', default='用户')
    p = sub.add_parser('prepare'); p.add_argument('--card', required=True); p.add_argument('--out', required=True)
    p.add_argument('--opening', required=True, type=int); p.add_argument('--ack', action='append', default=[])
    p.add_argument('--user-name', default='用户'); p.add_argument('--user-persona', default='')
    p.add_argument('--disable-entry', type=int, action='append', default=[])
    p.add_argument('--lore-budget', type=int)
    p = sub.add_parser('install')
    for name in ('plan', 'expect-sha', 'profile-home', 'source-home', 'root', 'host-root', 'tools-file'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--package', default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args(argv)
    try:
        if args.action == 'inspect':
            result = inspect(args.card, details=args.details, user_name=args.user_name)
        elif args.action == 'prepare':
            result = prepare(args.card, args.out, args.opening, acknowledged=args.ack,
                             user_name=args.user_name, user_persona=args.user_persona,
                             disabled_entries=args.disable_entry, lore_budget=args.lore_budget)
        else:
            result = install(args.plan, args.expect_sha, args.profile_home, args.source_home, args.root,
                             args.host_root, args.tools_file, args.package)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'state': 'UNAVAILABLE', 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
