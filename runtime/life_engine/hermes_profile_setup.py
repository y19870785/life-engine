"""Reviewed configuration inheritance for a fresh, Host-created named Profile.

YAML belongs to the Hermes adapter environment. This module does not create a
Profile, install dependencies, clone credentials, or bootstrap a missing Host.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

from .hermes_card_import import atomic, digest, home_path, json_bytes, locked, read, safe

FORMAT = 'life-engine-hermes-profile-setup-v1'
DEFAULT_DISABLED_SKILLS = (
    'life-engine-shuyao', 'shuyao-character-profile', 'shuyao-daily-life',
    'shuyao-voice', 'shuyao-memory', 'life-engine-companion',
    'life-engine-companion-profile', 'comfyui_z_image_turbo', 'pollinations-image-gen',
)
MARKER = '.life-engine-profile-setup.json'


def configure_host(host_root):
    """Attach the existing Host source/committed dependencies; never install them."""
    root = safe(host_root).resolve()
    if not root.is_dir() or not (root / 'hermes_yaml.py').is_file() or not (root / 'pm/environments.py').is_file():
        raise ValueError('HOST_UNAVAILABLE')
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from pm.environments import committed_venv, owning_home_root, install_key, site_packages
        venv = committed_venv(root)
        if venv is None:
            owner = owning_home_root(root)
            if owner is None:
                raise ValueError('HOST_DEPENDENCIES_UNAVAILABLE')
            state = safe(owner / 'installs' / install_key(root)).resolve()
            facts = json.loads(read(state / 'facts.json'))
            venv = safe(facts['packages']['venv']['environment']).resolve()
            if not venv.is_relative_to(state / 'environments') or not (venv / 'pyvenv.cfg').is_file():
                raise ValueError('HOST_DEPENDENCIES_UNAVAILABLE')
        dependencies = safe(site_packages(venv)).resolve()
        if not dependencies.is_dir():
            raise ValueError('HOST_DEPENDENCIES_UNAVAILABLE')
        if str(dependencies) not in sys.path:
            sys.path.insert(0, str(dependencies))
        yaml = _yaml()
        module_file = getattr(yaml, '__file__', None)
        if module_file is None or Path(module_file).resolve() != (root / 'hermes_yaml.py').resolve():
            raise ValueError('HOST_YAML_BINDING_MISMATCH')
    except (ImportError, KeyError, AttributeError, TypeError, OSError) as exc:
        raise ValueError('HOST_DEPENDENCIES_UNAVAILABLE') from exc
    return {'host_root': str(root), 'dependency_path': str(dependencies), 'yaml_ready': True}


def _yaml():
    try:
        import hermes_yaml
        if not callable(hermes_yaml.safe_load) or not callable(hermes_yaml.safe_dump):
            raise ImportError('invalid Hermes YAML adapter')
        return hermes_yaml
    except (ImportError, AttributeError) as exc:
        raise ValueError('HOST_YAML_UNAVAILABLE') from exc


def _mapping(value, name):
    if not isinstance(value, dict):
        raise ValueError('INVALID_CONFIG_' + name)
    return value


def _names(value, name):
    if not isinstance(value, (list, tuple)) or any(
        not isinstance(item, str) or not item.strip() or len(item) > 1024
        for item in value
    ):
        raise ValueError('INVALID_CONFIG_' + name)
    return list(dict.fromkeys(value))


def _config(home, yaml):
    path = safe(home / 'config.yaml')
    raw = read(path)
    config = yaml.safe_load(raw.decode('utf-8-sig'))
    return raw, _mapping(config, 'ROOT')


def _fresh(home, config):
    # No private history is opened to guess whether an existing agent is unused.
    for name in ('state.db', 'history.json', 'history.jsonl', 'MEMORY.md', 'USER.md',
                 '.life-engine-continuity.json', '.life-engine-character-capabilities.json',
                 MARKER, 'life-engine'):
        if (home / name).exists():
            raise ValueError('TARGET_NOT_FRESH')
    for name in ('plugins', 'cron', 'sessions', 'memories'):
        path = safe(home / name)
        if path.exists() and (not path.is_dir() or next(path.iterdir(), None) is not None):
            raise ValueError('TARGET_NOT_FRESH')
    plugins = _mapping(config.get('plugins') or {}, 'PLUGINS')
    if plugins.get('enabled') or config.get('mcp_servers'):
        raise ValueError('TARGET_NOT_FRESH')


def prepare(source_home, target_home, *, disabled_skills=None):
    """Return a reviewable plan with both config hashes; no filesystem writes."""
    yaml = _yaml()
    source, target = safe(source_home).resolve(), home_path(target_home)
    if not source.is_dir() or source == target:
        raise ValueError('DISTINCT_SOURCE_PROFILE_REQUIRED')
    source_raw, source_config = _config(source, yaml)
    target_raw, target_config = _config(target, yaml)
    _fresh(target, target_config)
    disabled = _names(DEFAULT_DISABLED_SKILLS if disabled_skills is None else disabled_skills, 'DISABLED_SKILLS')
    source_platforms = _mapping(source_config.get('platform_toolsets') or {}, 'PLATFORM_TOOLSETS')
    cli = _names(source_platforms.get('cli', source_config.get('toolsets', ['hermes-cli'])), 'CLI_TOOLSETS')
    source_skills = _mapping(source_config.get('skills') or {}, 'SKILLS')
    # Share paths, not skill copies, role identity, secrets, or tool outputs.
    external = []
    source_external = source_skills.get('external_dirs', [])
    if isinstance(source_external, str):
        source_external = [source_external]
    paths = [str(source / 'skills'), *_names(source_external, 'EXTERNAL_DIRS')]
    if source_skills.get('create_dir'):
        paths.extend(_names([source_skills['create_dir']], 'CREATE_DIR'))
    for path in paths:
        candidate = Path(os.path.expandvars(path)).expanduser()
        if not candidate.is_absolute():
            candidate = source / candidate
        candidate = safe(candidate).resolve()
        if candidate.is_dir() and str(candidate) not in external:
            external.append(str(candidate))
    before = deepcopy(target_config)
    after = deepcopy(target_config)
    _mapping(after.setdefault('platform_toolsets', {}), 'PLATFORM_TOOLSETS')['cli'] = cli
    skills = _mapping(after.setdefault('skills', {}), 'SKILLS')
    skills['external_dirs'] = _names([*_names(skills.get('external_dirs', []), 'EXTERNAL_DIRS'), *external], 'EXTERNAL_DIRS')
    skills['disabled'] = sorted(set(_names(skills.get('disabled', []), 'DISABLED_SKILLS') +
                                   _names(source_skills.get('disabled', []), 'DISABLED_SKILLS') + disabled))
    tools = _mapping(after.setdefault('tools', {}), 'TOOLS')
    _mapping(tools.setdefault('tool_search', {}), 'TOOL_SEARCH')['enabled'] = 'off'
    _mapping(after.setdefault('plugins', {}), 'PLUGINS')['enabled'] = ['life-engine-character-card']
    changes = {key: after[key] for key in ('platform_toolsets', 'skills', 'tools', 'plugins')
               if before.get(key) != after[key]}
    # Restrict review output to selected capability fields: do not expose unrelated
    # source/target provider settings or credential-bearing config sections.
    review = {'cli_toolsets': cli, 'external_skill_dirs': skills['external_dirs'],
              'disabled_skills': skills['disabled'], 'tool_search': 'off',
              'enabled_plugins': ['life-engine-character-card']}
    rendered = yaml.safe_dump(after, allow_unicode=True, sort_keys=False).encode('utf-8')
    return {'format': FORMAT, 'source_home': str(source), 'target_home': str(target),
            'source_config_sha256': digest(source_raw), 'target_config_sha256': digest(target_raw),
            'after_config_sha256': digest(rendered), 'disabled_skills': disabled,
            'changes': review, 'changed_sections': sorted(changes),
            'scope': 'fresh named Profile capability settings only; no credentials/MCP/identity/history clone'}


def apply(setup):
    """Recheck both hashes and the reviewed plan, then update only target config."""
    if not isinstance(setup, dict) or setup.get('format') != FORMAT:
        raise ValueError('INVALID_PROFILE_SETUP')
    target = home_path(setup['target_home'])
    with locked(target):
        if digest(read(safe(setup['source_home']) / 'config.yaml')) != setup.get('source_config_sha256'):
            raise ValueError('SOURCE_CONFIG_CHANGED')
        if digest(read(target / 'config.yaml')) != setup.get('target_config_sha256'):
            raise ValueError('TARGET_CONFIG_CHANGED')
        current = prepare(setup['source_home'], target, disabled_skills=setup['disabled_skills'])
        if current['source_config_sha256'] != setup.get('source_config_sha256'):
            raise ValueError('SOURCE_CONFIG_CHANGED')
        if current['target_config_sha256'] != setup.get('target_config_sha256'):
            raise ValueError('TARGET_CONFIG_CHANGED')
        if current != setup:
            raise ValueError('SETUP_PLAN_CHANGED')
        yaml = _yaml()
        before_raw, config = _config(target, yaml)
        review = setup['changes']
        _mapping(config.setdefault('platform_toolsets', {}), 'PLATFORM_TOOLSETS')['cli'] = review['cli_toolsets']
        skills = _mapping(config.setdefault('skills', {}), 'SKILLS')
        skills['external_dirs'], skills['disabled'] = review['external_skill_dirs'], review['disabled_skills']
        tools = _mapping(config.setdefault('tools', {}), 'TOOLS')
        _mapping(tools.setdefault('tool_search', {}), 'TOOL_SEARCH')['enabled'] = 'off'
        _mapping(config.setdefault('plugins', {}), 'PLUGINS')['enabled'] = review['enabled_plugins']
        after_raw = yaml.safe_dump(config, allow_unicode=True, sort_keys=False).encode('utf-8')
        if digest(after_raw) != setup['after_config_sha256']:
            raise ValueError('SETUP_RENDER_CHANGED')
        if (digest(read(target / 'config.yaml')) != setup['target_config_sha256'] or
                digest(read(safe(setup['source_home']) / 'config.yaml')) != setup['source_config_sha256']):
            raise ValueError('SETUP_CONFIG_CHANGED')
        from uuid import uuid4
        backup = safe(target / '.life-engine-profile-setup-backups' / (uuid4().hex + '.yaml'))
        atomic(backup, before_raw)
        receipt = {**setup, 'state': 'PREPARED', 'backup': str(backup)}
        atomic(target / MARKER, json_bytes(receipt))
        atomic(target / 'config.yaml', after_raw)
        receipt['state'] = 'APPLIED'
        atomic(target / MARKER, json_bytes(receipt))
        return receipt


def restore(receipt):
    """Restore only the original target config when its installed hash matches."""
    if not isinstance(receipt, dict) or receipt.get('format') != FORMAT:
        raise ValueError('INVALID_PROFILE_SETUP')
    target = home_path(receipt['target_home'])
    with locked(target):
        marker = json.loads(read(target / MARKER))
        if marker != receipt or receipt.get('state') != 'APPLIED':
            raise ValueError('SETUP_RECEIPT_CHANGED')
        if digest(read(target / 'config.yaml')) != receipt['after_config_sha256']:
            raise ValueError('TARGET_CONFIG_CHANGED')
        backup = safe(receipt['backup'])
        if backup.parent != target / '.life-engine-profile-setup-backups':
            raise ValueError('INVALID_SETUP_BACKUP')
        raw = read(backup)
        if digest(raw) != receipt['target_config_sha256']:
            raise ValueError('SETUP_BACKUP_CHANGED')
        atomic(target / 'config.yaml', raw)
        result = {**receipt, 'state': 'ROLLED_BACK'}
        atomic(target / MARKER, json_bytes(result))
        return result
