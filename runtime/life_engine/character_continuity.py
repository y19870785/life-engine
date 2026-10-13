"""Profile-bound roleplay continuity pilot over existing World/Memory/Story APIs.

The service is a trusted local CLI owner adapter. It records proven utterances;
generated fiction is never promoted to confirmed player history. The private
recovery journal is outside life.db and does not change the canonical schema.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from . import durable
from .config import defaults
from .domain import (BindingStatus, CanonStatus, CharacterDefinition, DefinitionRef,
    DefinitionVersion, DomainId, IdKind, Principal, Provenance, RealityStatus, Soul,
    SourceType, Values, WorldScope, WorldStatus)
from .hermes_card_import import home_path, read, safe, json_bytes, digest
from .hermes_turn_proof import verify_pair
from .memory import (AudienceKind, IdempotencyIdentity, MemoryAudience, MemoryKind,
                     OwnerMemoryContext, SessionMemoryContext)
from .memory_runtime import MemoryRuntime
from .memory_sqlite_repository import SQLiteMemoryRepository
from .story import (NarrativePayload, OwnerStoryContext, StoryEventKind, StoryEventProposal,
                    StoryIdempotencyIdentity, StoryRevision)
from .story_runtime import StoryRuntime
from .story_sqlite_repository import SQLiteStoryRepository
from .world_runtime import WorldRuntime
from .world_sqlite_repository import SQLiteWorldRepository
from .world_schema import DATA_SCHEMA

FORMAT = 'life-engine-character-continuity-v2'
MAX_TEXT = 12000
HOST_FILES = ('agent/turn_context.py', 'agent/turn_finalizer.py', 'agent/session_persistence.py',
              'agent/message_metadata.py', 'agent/turn_final_response.py', 'hermes_state_common.py')


def init(root, profile, card_path, package):
    root, profile = safe(root), home_path(profile)
    if root.is_relative_to(profile) or profile.is_relative_to(root):
        raise ValueError('SEPARATE_DATA_ROOT_REQUIRED')
    if (root / 'continuity.json').exists():
        return status(root, profile, digest(read(card_path)))
    if root.exists():
        raise ValueError('NEW_CONTINUITY_ROOT_REQUIRED')
    card_raw = read(card_path)
    card = json.loads(card_raw)
    if card.get('format') != 'life-engine-hermes-native-v1':
        raise ValueError('NATIVE_CARD_REQUIRED')
    cfg = defaults('character-continuity')
    cfg['integration'].update(adapter='hermes', host_home=str(profile))
    ready = durable.create_install(package, root, cfg)
    key = ready['instance']
    inst = durable.registry(root)['instances'][key]
    path = durable.state_home(root, inst) / 'agents' / inst['agent_id'] / 'life.db'
    repo = SQLiteWorldRepository(path)
    world = WorldRuntime(repo)
    actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
    soul = Soul(DomainId.new(IdKind.SOUL), actor.owner_id, DomainId.new(IdKind.WORLD))
    now = datetime.now(timezone.utc)
    world.register_soul(actor, soul)
    definition = CharacterDefinition(DefinitionRef(DomainId.new(IdKind.DEFINITION), DefinitionVersion(1)),
        actor.owner_id, card['options'].get('char_name') or card['character']['name'],
        Values((('source_sha256', card['source_sha256']),)),
        Provenance(SourceType.IMPORT, card['source_sha256'], now, actor,
                   RealityStatus.UNKNOWN, CanonStatus.UNREVIEWED))
    world.register_definition(actor, definition)
    created = world.create_roleplay_world(actor, soul.soul_id, now)
    created = world.instantiate(actor, created.world.world_id, created.timeline.scope.timeline_id,
                               definition.reference, created.world.revision, now)
    data = {'format': FORMAT, 'profile': str(profile), 'card_sha256': digest(card_raw),
            'card_source_sha256': card['source_sha256'], 'instance': key, 'runtime_id': repo.runtime_id,
            'principal': str(actor.principal_id), 'owner': str(actor.owner_id),
            'soul': str(soul.soul_id), 'world': str(created.world.world_id),
            'timeline': str(created.timeline.scope.timeline_id),
            'character': str(created.characters[0].character_instance_id),
            'host_session': None, 'core_session': None}
    repo.close()
    with journal(root) as db:
        db.execute('CREATE TABLE turns(source TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, '
            'frame TEXT NOT NULL, lease TEXT NOT NULL, created TEXT NOT NULL, memory_revision INTEGER NOT NULL, '
            'story_revision INTEGER NOT NULL, memory_id TEXT, story_event TEXT, state TEXT NOT NULL)')
    durable.write(root / 'continuity.json', data)
    return status(root, profile, data['card_sha256'])


def load(root, profile, card_sha):
    root, profile = safe(root).resolve(), home_path(profile)
    data = json.loads(read(root / 'continuity.json'))
    if data.get('format') != FORMAT or data['profile'] != str(profile) or data['card_sha256'] != card_sha:
        raise ValueError('CONTINUITY_BINDING_MISMATCH')
    return root, data


def journal(root):
    # Operations hold a separate adapter lock; canonical APIs acquire their normal
    # management/control locks independently. No journal transaction spans Core calls.
    path = safe(root / 'continuity-journal.sqlite')
    return closing(sqlite3.connect(path, timeout=5))


class Core:
    def __init__(self, root, data):
        self.root, self.data = root, data
        inst = durable.registry(root)['instances'][data['instance']]
        db = durable.state_home(root, inst) / 'agents' / inst['agent_id'] / 'life.db'
        self.repo = SQLiteWorldRepository(db, runtime_id=data['runtime_id'])
        self.world = WorldRuntime(self.repo)
        self.actor = Principal(DomainId.parse(data['principal']), DomainId.parse(data['owner']))
        self.scope = WorldScope(*(DomainId.parse(data[k]) for k in ('owner', 'soul', 'world', 'timeline')))
        self.viewer = MemoryAudience(AudienceKind.CHARACTER_INSTANCE, DomainId.parse(data['character']))
        self.memory_repo = SQLiteMemoryRepository(root, data['instance'], runtime_id=self.repo.runtime_id)
        self.story_repo = SQLiteStoryRepository(root, data['instance'], runtime_id=self.repo.runtime_id)
        self.memory, self.story = MemoryRuntime(self.memory_repo), StoryRuntime(self.story_repo)
        self.owner = OwnerMemoryContext(self.actor, self.scope)
        self.story_owner = OwnerStoryContext(self.actor, self.scope)

    def close(self):
        self.memory_repo.close(); self.story_repo.close(); self.repo.close()

    def snapshot(self):
        return self.world.snapshot(self.actor, self.scope.world_id)

    def ensure_session(self, host_session):
        current = self.snapshot()
        opened = next((s for s in current.sessions if s.status is BindingStatus.OPEN), None)
        if opened and self.data['host_session'] == host_session and str(opened.session_id) == self.data['core_session']:
            return self.lease(current, opened)
        if opened:
            current = self.world.exit(self.actor, self.scope.world_id, self.scope.timeline_id,
                opened.session_id, current.world.revision, current.world.writer_epoch)
        operation = self.world.resume if current.world.status is WorldStatus.SUSPENDED else self.world.enter
        current = operation(self.actor, self.scope.world_id, self.scope.timeline_id,
            DomainId.parse(self.data['character']), current.world.revision, current.world.writer_epoch)
        opened = current.sessions[-1]
        self.data.update(host_session=host_session, core_session=str(opened.session_id))
        durable.write(self.root / 'continuity.json', self.data)
        return self.lease(current, opened)

    def lease(self, current, binding):
        return {'session': str(binding.session_id), 'epoch': binding.writer_epoch.value,
                'world_revision': current.world.revision.value, 'host_session': self.data['host_session']}

    def check_lease(self, lease):
        current = self.snapshot()
        opened = next((s for s in current.sessions if s.status is BindingStatus.OPEN), None)
        if (not opened or current.world.status is not WorldStatus.ACTIVE or
                self.lease(current, opened) != lease):
            raise ValueError('CONTINUITY_SESSION_STALE')


def core_call(root, profile, card_sha, action):
    root, _ = load(root, profile, card_sha)
    with durable.locked(root, 'character-continuity', timeout=5):
        root, data = load(root, profile, card_sha)
        core = Core(root, data)
        try:
            return action(core)
        finally:
            core.close()


def stage(core, frame, proof, lease):
    source = proof['source']
    fingerprint = digest(json_bytes([frame['user_text'], frame['assistant_text']]))
    with journal(core.root) as db:
        db.row_factory = sqlite3.Row
        old = db.execute('SELECT * FROM turns WHERE source=?', (source,)).fetchone()
        if old:
            if old['fingerprint'] != fingerprint:
                raise ValueError('CONTINUITY_SOURCE_CONFLICT')
            return dict(old)
        row = (source, fingerprint, json_bytes(frame).decode(), json_bytes(lease).decode(),
               datetime.now(timezone.utc).isoformat(), core.memory.collection_revision(core.owner).value,
               core.story.story_revision(core.story_owner).value, None, None, 'PENDING')
        db.execute('INSERT INTO turns VALUES(?,?,?,?,?,?,?,?,?,?)', row)
        db.commit()
        return dict(db.execute('SELECT * FROM turns WHERE source=?', (source,)).fetchone())


def finish(core, row):
    if row['state'] == 'COMMITTED':
        return row
    frame, lease = json.loads(row['frame']), json.loads(row['lease'])
    core.check_lease(lease)
    now = datetime.fromisoformat(row['created'])
    source = row['source']
    # Confirmed means this utterance was committed, not that its contents are
    # objectively true or that fictional player identities are real identities.
    provenance = Provenance(SourceType.USER_REPORT, source, now, core.actor,
        RealityStatus.USER_CLAIMED, CanonStatus.ACCEPTED,
        core.scope.world_id, core.scope.timeline_id, DomainId.parse(lease['session']))
    if row['memory_id'] is None:
        from .memory import MemoryCollectionRevision
        receipt = core.memory.create_owner_memory(core.owner, MemoryCollectionRevision(row['memory_revision']),
            IdempotencyIdentity(source, 'user-utterance'), content=frame['user_text'],
            kind=MemoryKind.EPISODIC, provenance=provenance, audience=(core.viewer,))
        row['memory_id'] = str(receipt.memory_id)
        with journal(core.root) as db:
            db.execute('UPDATE turns SET memory_id=? WHERE source=?', (row['memory_id'], source)); db.commit()
    if row['story_event'] is None:
        # The Story event accepts the occurrence of this generated narrative. Its
        # model-origin contents stay CANDIDATE; they cannot confirm player promises.
        generated = Provenance(SourceType.MODEL, source, now, core.actor,
            RealityStatus.FICTIONAL, CanonStatus.CANDIDATE,
            core.scope.world_id, core.scope.timeline_id, DomainId.parse(lease['session']))
        proposal = StoryEventProposal(StoryEventKind.NARRATIVE_EVENT,
            NarrativePayload(frame['assistant_text']), generated, character_actor_id=core.viewer.target)
        receipt = core.story.accept_story_event(core.story_owner, StoryRevision(row['story_revision']),
            proposal, StoryIdempotencyIdentity(source, 'generated-narrative'))
        row['story_event'] = str(receipt.event_id)
        with journal(core.root) as db:
            db.execute('UPDATE turns SET story_event=? WHERE source=?', (row['story_event'], source)); db.commit()
    row['state'] = 'COMMITTED'
    with journal(core.root) as db:
        db.execute("UPDATE turns SET state='COMMITTED' WHERE source=?", (source,)); db.commit()
    return row


def commit(root, profile, card_sha, frame, lease):
    # Proof is independently verified in the service, not trusted from plugin JSON.
    load(root, profile, card_sha)  # Bind the target before reading any Host rows.
    proof = verify_pair(home_path(profile), frame)
    if any(len(frame[k].encode('utf-8')) > MAX_TEXT for k in ('user_text', 'assistant_text')):
        raise ValueError('CONTINUITY_TEXT_TOO_LARGE')
    def apply(core):
        core.check_lease(lease)  # Authorization before replay or any journal mutation.
        if lease['host_session'] != frame['session_id']:
            raise ValueError('CONTINUITY_SESSION_STALE')
        row = finish(core, stage(core, frame, proof, lease))
        return {'state': row['state'], 'source': row['source'], 'memory_id': row['memory_id'],
                'story_event': row['story_event'], 'reality': 'user utterance + candidate fictional narrative'}
    return core_call(root, profile, card_sha, apply)


def context(root, profile, card_sha, host_session):
    if not isinstance(host_session, str) or not host_session or len(host_session) > 200:
        raise ValueError('HOST_SESSION_REQUIRED')
    def query(core):
        # Recover only already-proven pending turns for the currently open lease,
        # before switching it. Failures remain visible, never silently superseded.
        with journal(core.root) as db:
            db.row_factory = sqlite3.Row
            pending = [dict(r) for r in db.execute("SELECT * FROM turns WHERE state='PENDING' ORDER BY rowid")]
        for row in pending:
            finish(core, row)
        lease = core.ensure_session(host_session)
        current = core.snapshot(); binding = current.sessions[-1]
        session = SessionMemoryContext(core.actor, core.scope, binding.session_id,
                                       binding.writer_epoch, core.viewer)
        # Fetch accepted Memory through its audience authorization, then only
        # include fully journal-committed turn records; partial Core writes stay out.
        with journal(core.root) as db:
            db.row_factory = sqlite3.Row
            rows = [dict(r) for r in db.execute("SELECT * FROM turns WHERE state='COMMITTED' ORDER BY rowid DESC LIMIT 12")]
        items, used = [], 0
        for row in rows:
            from .memory_repository import MemoryRuntimeError, MemoryFailure
            try:
                user = core.memory.get_memory(session, DomainId.parse(row['memory_id']))
            except MemoryRuntimeError as exc:
                if exc.code is MemoryFailure.NOT_AVAILABLE:
                    continue
                raise
            event = core.story.get_story_event(core.story_owner, DomainId.parse(row['story_event']))
            item = {'source': row['source'], 'recorded_at': row['created'],
                    'user_said': user.content, 'user_reality': user.provenance.reality_status.value,
                    'generated_scene': event.proposal.payload.text, 'scene_canon': 'candidate'}
            cost = len(json_bytes(item))
            if used + cost > 48000:
                continue
            items.append(item); used += cost
        items.reverse()
        return {'state': 'READY', 'world': str(core.scope.world_id), 'lease': lease,
                'has_history': bool(rows), 'records': items,
                'policy': '用户原话只证明曾说过；生成剧情是候选虚构片段，不能确认为玩家过往承诺。'
                          '用户最新明确纠正优先。可以自然续写角色生活，不主动讲解后台或复述全部记忆。'}
    return core_call(root, profile, card_sha, query)


def status(root, profile, card_sha):
    def query(core):
        with journal(core.root) as db:
            states = dict(db.execute('SELECT state,count(*) FROM turns GROUP BY state'))
        return {'state': 'INITIALIZED', 'world': str(core.scope.world_id), 'turns': states,
                'card_sha256': card_sha, 'data_schema': DATA_SCHEMA, 'real_delivery_verified': False}
    return core_call(root, profile, card_sha, query)


def activation(root, profile, card_sha, enabled, host_root=None):
    root, data = load(root, profile, card_sha)
    profile = home_path(profile)
    path = profile / '.life-engine-continuity.json'
    if enabled:
        if host_root is None:
            raise ValueError('HOST_ROOT_REQUIRED')
        host_root = safe(host_root).resolve()
        files = {name: digest(read(host_root / name)) for name in HOST_FILES}
        reg = durable.registry(root)
        config = {'format': FORMAT, 'enabled': True, 'profile': str(profile), 'root': str(root),
                  'python': str(Path(sys.executable).resolve()),
                  'runtime': str(root / 'releases' / reg['release'] / 'runtime'),
                  'host_root': str(host_root), 'host_files': files}
        if path.exists():
            previous = json.loads(read(path))
            if {k: v for k, v in previous.items() if k != 'enabled'} != {k: v for k, v in config.items() if k != 'enabled'}:
                raise ValueError('CONTINUITY_ACTIVATION_CHANGED')
    else:
        config = json.loads(read(path))
        if config.get('root') != str(root) or config.get('profile') != str(profile):
            raise ValueError('CONTINUITY_BINDING_MISMATCH')
        config['enabled'] = False
    # Configuration is owner-managed and separate from author card data. Save the
    # prior toggle before changing it; data and installed card stay intact.
    if path.exists():
        from uuid import uuid4
        durable.write(root / 'activation-backups' / (uuid4().hex + '.json'), json.loads(read(path)))
    durable.write(path, config)
    return {'state': 'ENABLED' if enabled else 'DISABLED', 'profile': str(profile),
            'root': str(root), 'next': '新开CLI会话加载；关闭功能不删除世界和记忆数据。'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='独立角色世界：当前轮可靠记录与跨会话读取（V2试用）')
    parser.add_argument('action', choices=('init', 'context', 'commit', 'status', 'enable', 'disable'))
    parser.add_argument('--root', required=True); parser.add_argument('--profile-home', required=True)
    parser.add_argument('--card', required=True); parser.add_argument('--package')
    parser.add_argument('--host-root')
    args = parser.parse_args(argv)
    try:
        card_sha = digest(read(args.card))
        if args.action == 'init':
            result = init(args.root, args.profile_home, args.card, args.package or str(Path(__file__).resolve().parents[2]))
        elif args.action == 'status':
            result = status(args.root, args.profile_home, card_sha)
        elif args.action in ('enable', 'disable'):
            result = activation(args.root, args.profile_home, card_sha, args.action == 'enable', args.host_root)
        else:
            raw = sys.stdin.buffer.read(65537)
            if len(raw) > 65536:
                raise ValueError('INPUT_TOO_LARGE')
            payload = json.loads(raw)
            result = (context(args.root, args.profile_home, card_sha, payload['session_id'])
                      if args.action == 'context' else commit(args.root, args.profile_home, card_sha,
                                                            payload['frame'], payload['lease']))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'state': 'UNAVAILABLE', 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
