"""Owner-managed tool permission overlay; never rewrites the installed card."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

from .hermes_card_import import home_path, read, digest, atomic, json_bytes, locked


def configure(profile, tools_file, expected_card_sha):
    home = home_path(profile)
    with locked(home):
        raw = read(home / 'plugins/life-engine-character-card/card.json')
        if digest(raw) != expected_card_sha:
            raise ValueError('CARD_CHANGED')
        tools = json.loads(read(tools_file))
        if not isinstance(tools, list) or any(not isinstance(t, str) or not t for t in tools):
            raise ValueError('TOOL_NAME_LIST_REQUIRED')
        path = home / '.life-engine-character-capabilities.json'
        previous = read(path) if path.exists() else None
        config = {'format': 'life-engine-character-capabilities-v1', 'enabled': True,
                  'profile': str(home), 'card_sha256': expected_card_sha,
                  'allowed_tools': sorted(set(tools))}
        if previous is not None:
            atomic(home / '.life-engine-capability-backups' / (uuid4().hex + '.json'), previous)
        atomic(path, json_bytes(config))
        return {'state': 'CONFIGURED', 'tools': len(config['allowed_tools']),
                'card_unchanged': digest(read(home / 'plugins/life-engine-character-card/card.json')) == expected_card_sha}


def main():
    parser = argparse.ArgumentParser(description='为独立角色Profile配置宿主工具许可；不复制身份或凭据')
    parser.add_argument('--profile-home', required=True)
    parser.add_argument('--tools-file', required=True, help='可信管理者提供的实际Host工具名称JSON数组')
    parser.add_argument('--expected-card-sha', required=True)
    args = parser.parse_args()
    try:
        result = configure(args.profile_home, args.tools_file, args.expected_card_sha)
    except (ValueError, OSError, TypeError) as exc:
        print(json.dumps({'state': 'UNAVAILABLE', 'error': str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
