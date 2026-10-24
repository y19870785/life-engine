"""X2 离线薄控制器。只有受管合成 fixture，没有 Host 或模型适配器。"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone

from life_engine import durable as d, roleplay_recall as recall
from life_engine.config import defaults
from life_engine.domain import (DomainId, IdKind, Principal, Soul, DefinitionRef,
    DefinitionVersion, CharacterDefinition, Values, Provenance, SourceType,
    RealityStatus, CanonStatus, WorldScope, World, WorldKind, WorldStatus, WorldTimeline)
from life_engine.memory import (OwnerMemoryContext, SessionMemoryContext, MemoryAudience,
    AudienceKind, MemoryKind, IdempotencyIdentity, MemoryCollectionRevision, MemoryLifecycle)
from life_engine.memory_runtime import MemoryRuntime
from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
from life_engine.world_repository import WorldSnapshot
from life_engine.world_runtime import WorldRuntime
from life_engine.world_sqlite_repository import SQLiteWorldRepository
from x2_selection import _select_highlights, select_recall, validate_query

PACKAGE = Path(__file__).resolve().parents[1]
VERSION = 'X2-A-L1.1'
MANAGED = Path(tempfile.gettempdir()).absolute() / 'life-engine-x2-l1'
PROBE_SHA = 'bd53cf99bcec4b24c80284df4a63371ccf4d245e9d72c16dda38a004a24ef705'


class X2Error(Exception):
    def __init__(self, code, stage='controller'):
        self.code, self.stage = code, stage
        super().__init__(code)


def checked_path(path):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise X2Error('PATH_LINK_DENIED', 'isolation')
    return path


def package_hash():
    paths = sorted((PACKAGE / 'runtime/life_engine').glob('*.py'))
    paths += sorted((PACKAGE / 'tools').glob('*x2*.py'))
    paths += sorted((PACKAGE / 'examples/x2').glob('*'))
    h = hashlib.sha256()
    for path in paths:
        checked_path(path)
        h.update(str(path.relative_to(PACKAGE)).replace('\\', '/').encode())
        h.update(b'\0' + path.read_bytes())
    return h.hexdigest()


def fixture_path(identifier):
    if type(identifier) is not str or not re.fullmatch('[0-9a-f]{32}', identifier):
        raise X2Error('FIXTURE_ID_INVALID', 'isolation')
    base = checked_path(MANAGED)
    path = checked_path(base / identifier)
    if path.parent != base:
        raise X2Error('FIXTURE_PATH_DENIED', 'isolation')
    return path


def text(value, maximum=1200, empty=False):
    if type(value) is not str:
        raise X2Error('TEXT_INVALID')
    try:
        valid = len(value.encode('utf-8')) <= maximum and (empty or bool(value.strip()))
    except UnicodeError:
        valid = False
    if not valid:
        raise X2Error('TEXT_INVALID')
    return value


def scope(values):
    return WorldScope(*(DomainId.parse(v) for v in values))


def scope_values(value):
    return [str(getattr(value, k + '_id')) for k in ('owner', 'soul', 'world', 'timeline')]


def stamp():
    return datetime.now(timezone.utc).isoformat()


def validate_control(value):
    """控制元数据不是可扩展导入格式；未知字段/损坏拒绝，尤其不原样导出对象。"""
    try:
        if type(value) is not dict or set(value) != {'version', 'package', 'instance', 'probe', 'sessions',
                'pending', 'feedback', 'completed', 'principal', 'soul_scope', 'definition'}:
            raise ValueError()
        if value['probe'] != dict(isolated=True, no_site=True, module_inside_release=True):
            raise ValueError()
        if type(value['sessions']) is not list or len(value['sessions']) > 7:
            raise ValueError()
        for session in value['sessions']:
            if set(session) != {'scope', 'character', 'binding', 'started', 'phase', 'turns', 'candidate', 'accepted'}:
                raise ValueError()
            if session['phase'] not in ('roleplay', 'interrupted', 'candidate', 'accepted', 'ended'):
                raise ValueError()
            if type(session['turns']) is not list or len(session['turns']) > 4:
                raise ValueError()
            scope(session['scope'])
            for turn in session['turns']:
                if set(turn) != {'request', 'user', 'model'} or not re.fullmatch('[0-9a-f]{32}', turn['request']):
                    raise ValueError()
                DomainId.parse(turn['user'])
                DomainId.parse(turn['model'])
        if type(value['completed']) is not dict or len(value['completed']) > 42:
            raise ValueError()
        for key, digest in value['completed'].items():
            if not re.fullmatch('[0-9a-f]{32}', key) or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError()
        if type(value['feedback']) is not list or len(value['feedback']) > 100:
            raise ValueError()
        for item in value['feedback']:
            if (set(item) != {'rating', 'reason'} or item['rating'] not in ('useful', 'miss', 'confusing')
                    or item['reason'] not in ('none', 'retrieval', 'source', 'recovery', 'ui')):
                raise ValueError()
        pending = value['pending']
        if pending is not None:
            action = pending['action']
            expected = {'action', 'payload', 'time'} if action in ('new', 'end') else {'action', 'payload', 'fingerprint', 'time', 'stage'}
            if action == 'turn':
                expected.add('revision')
            if action not in ('new', 'end', 'turn', 'finish', 'accept') or set(pending) != expected:
                raise ValueError()
            if datetime.fromisoformat(pending['time']).tzinfo is None:
                raise ValueError()
            fields = {'new': set(), 'end': set(), 'turn': {'request', 'text'},
                      'finish': {'request'}, 'accept': {'request', 'revision'}}[action]
            if set(pending['payload']) != fields:
                raise ValueError()
        scope(value['soul_scope'])
        DomainId.parse(value['principal'])
    except (ValueError, TypeError, KeyError, AttributeError):
        raise X2Error('RECOVERY_REQUIRED', 'control_invalid') from None


def initialize(root):
    """只允许 durable 的固定导入探针；不允许任意子进程或 Host 初始化。"""
    host, install = root / 'synthetic-host', root / 'install'
    host.mkdir()
    cfg = defaults('synthetic')
    cfg['integration'].update(adapter='hermes', host_home=str(host))
    original = subprocess.run
    script = next(s for s in d.probe_release.__code__.co_consts
                  if type(s) is str and 'SchemaMismatch' in s)
    python = Path(getattr(sys, '_base_executable', sys.executable)).resolve()
    if hashlib.sha256(script.encode()).hexdigest() != PROBE_SHA:
        raise X2Error('INITIALIZER_SCRIPT_CHANGED', 'initializer')
    observations = []

    def guard(argv, **kw):
        options = dict(capture_output=True, text=True, encoding='utf-8', timeout=20, shell=False)
        if (type(argv) is not list or len(argv) != 5 or argv[:3] != [str(python), '-c', script]
                or argv[4] != '8' or kw != options):
            raise X2Error('INITIALIZER_PROBE_DENIED', 'initializer')
        runtime = checked_path(argv[3])
        if runtime.parent.parent != install / 'releases' or runtime.name != 'runtime':
            raise X2Error('INITIALIZER_TARGET_DENIED', 'initializer')
        manifest = d.read(runtime.parent / 'release.json')
        expected = {name: d.digest(data) for name, data in d.release_files(PACKAGE).items()}
        if manifest['files'] != expected or manifest['data_schema'] != 8:
            raise X2Error('INITIALIZER_PACKAGE_CHANGED', 'initializer')
        for name, digest in expected.items():
            if d.digest(checked_path(runtime.parent / d.relative(name)).read_bytes()) != digest:
                raise X2Error('INITIALIZER_PACKAGE_CHANGED', 'initializer')
        audit = ('import sys\ndef deny(event,args):\n'
                 ' if event.startswith("socket.") or event in ("subprocess.Popen","os.system",'
                 '"os.posix_spawn","os.exec","os.fork"): raise RuntimeError("PROBE_EXTERNAL_DENIED")\n'
                 'sys.addaudithook(deny)\n')
        verify = ('\nimport json,os,life_engine.memory_runtime\n'
                  'print(json.dumps({"isolated":sys.flags.isolated,"no_site":sys.flags.no_site,'
                  '"module":life_engine.memory_runtime.__file__,"home":'
                  'any(k in os.environ for k in ("HOME","USERPROFILE","PYTHONPATH"))}))')
        env = {k: os.environ[k] for k in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP') if k in os.environ}
        result = original([str(python), '-I', '-S', '-B', '-X', 'utf8', '-c',
                           audit + script + verify, str(runtime), '8'], env=env, **kw)
        if result.returncode:
            raise X2Error('INITIALIZER_PROBE_FAILED', 'initializer')
        observed = json.loads(result.stdout)
        if (observed['isolated'] != 1 or observed['no_site'] != 1 or observed['home']
                or not Path(observed['module']).is_relative_to(runtime)):
            raise X2Error('INITIALIZER_ISOLATION_GAP', 'initializer')
        observations.append({'isolated': True, 'no_site': True, 'module_inside_release': True})
        return result

    # 初始化发生在线程/HTTP 启动前；恢复全局函数，不保留通用代理。
    subprocess.run = guard
    try:
        result = d.create_install(PACKAGE, install, cfg)
    finally:
        subprocess.run = original
    if len(observations) != 1:
        raise X2Error('INITIALIZER_ISOLATION_GAP', 'initializer')
    return result, observations[0]


class Controller:
    def __init__(self, identifier=None, *, fault=None):
        self.mutex = threading.RLock()
        self.fault = fault or (lambda stage: None)
        self.stack = contextlib.ExitStack()
        self.identifier = identifier or os.urandom(16).hex()
        self.root = fixture_path(self.identifier)
        try:
            if identifier is None:
                checked_path(MANAGED).mkdir(parents=True, exist_ok=True, mode=0o700)
                self.root.mkdir(mode=0o700)
            elif not self.root.is_dir():
                raise X2Error('FIXTURE_NOT_FOUND', 'open')
            self.stack.enter_context(d.locked(self.root, 'x2-ui', timeout=.3))
            if identifier is None:
                created, probe = initialize(self.root)
                self.state = dict(version=VERSION, package=package_hash(), instance=created['instance'],
                                  probe=probe, sessions=[], pending=None, feedback=[], completed={})
                self._open_repositories()
                self._seed()
                self.save()
            else:
                for path in self.root.rglob('*'):
                    checked_path(path)
                self.state = d.read(self.root / 'x2.json')
                if self.state['version'] != VERSION or self.state['package'] != package_hash():
                    raise X2Error('FIXTURE_VERSION_MISMATCH', 'open')
                validate_control(self.state)
                self._open_repositories()
                self.actor = Principal(DomainId.parse(self.state['principal']),
                                       DomainId.parse(self.state['soul_scope'][0]))
                self.soul_scope = scope(self.state['soul_scope'])
                self.recover()
                if self.state['sessions'] and self.current()['phase'] == 'roleplay':
                    self.current()['phase'] = 'interrupted'
                    self.save()
            self.soul_owner = OwnerMemoryContext(self.actor, self.soul_scope)
            self.soul_session = self._session(self.soul_scope, None, renew=True)
        except BaseException:
            self.close()
            raise

    def _open_repositories(self):
        install = self.root / 'install'
        reg = d.registry(install)
        self.registry_snapshot = reg
        if set(reg['instances']) != {self.state['instance']} or reg['data_schema'] != 8:
            raise X2Error('REGISTRY_INVALID', 'isolation')
        inst = reg['instances'][self.state['instance']]
        if (inst['host_home'] != str(self.root / 'synthetic-host') or inst['agent_id'] != 'synthetic'
                or inst['adapter'] != 'hermes' or inst['owner_channel'] or inst['owner_sender_id']):
            raise X2Error('REGISTRY_TARGET_DENIED', 'isolation')
        manifest = d.read(install / 'releases' / d.safe_name(reg['release']) / 'release.json')
        expected = {name: d.digest(data) for name, data in d.release_files(PACKAGE).items()}
        if manifest['files'] != expected or manifest['data_schema'] != 8:
            raise X2Error('PACKAGE_MISMATCH', 'isolation')
        for name, digest in expected.items():
            if d.digest(checked_path(install / 'releases' / reg['release'] / d.relative(name)).read_bytes()) != digest:
                raise X2Error('PACKAGE_MISMATCH', 'isolation')
        data = d.state_home(install, inst)
        path = checked_path(data / 'agents/synthetic/life.db')
        if not path.is_file():
            raise X2Error('FIXTURE_DATABASE_MISSING', 'isolation')
        self.world_repo = SQLiteWorldRepository(path)
        self.stack.callback(self.world_repo.close)
        self.world = WorldRuntime(self.world_repo)
        self.repo = SQLiteMemoryRepository(install, inst['id'], runtime_id=self.world_repo.runtime_id)
        self.stack.callback(self.repo.close)
        self.memory = MemoryRuntime(self.repo)

    def _seed(self):
        now = datetime.now(timezone.utc)
        self.actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
        soul = Soul(DomainId.new(IdKind.SOUL), self.actor.owner_id, DomainId.new(IdKind.WORLD))
        self.world.register_soul(self.actor, soul)
        prov = Provenance(SourceType.IMPORT, 'X2 原创合成种子', now, self.actor,
                          RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
        definition = CharacterDefinition(DefinitionRef(DomainId.new(IdKind.DEFINITION), DefinitionVersion(1)),
                                         self.actor.owner_id, '灯塔守望者', Values(), prov)
        self.world.register_definition(self.actor, definition)
        self.soul_scope = WorldScope(self.actor.owner_id, soul.soul_id, soul.soul_world_id,
                                     DomainId.new(IdKind.TIMELINE))
        with self.world.repository.transaction() as tx:
            tx.add_world(WorldSnapshot(World(soul.soul_world_id, soul.owner_id, soul.soul_id,
                         WorldKind.SOUL, prov, WorldStatus.ACTIVE), WorldTimeline(self.soul_scope, prov)))
        self.state.update(principal=str(self.actor.principal_id), soul_scope=scope_values(self.soul_scope),
                          definition=[str(definition.reference.definition_id), definition.reference.version.value])

    def save(self):
        checked_path(self.root / 'x2.json')
        d.write(self.root / 'x2.json', self.state)

    def close(self):
        self.stack.close()

    def _session(self, target, character, renew=False):
        current = self.world.snapshot(self.actor, target.world_id)
        opened = next((s for s in current.sessions if s.status.value == 'open'), None)
        if opened and renew:
            current = self.world.exit(self.actor, target.world_id, target.timeline_id, opened.session_id,
                                      current.world.revision, current.world.writer_epoch)
            opened = None
        if opened is None:
            call = self.world.resume if current.world.status is WorldStatus.SUSPENDED else self.world.enter
            current = call(self.actor, target.world_id, target.timeline_id, character,
                           current.world.revision, current.world.writer_epoch)
            opened = current.sessions[-1]
        viewer = MemoryAudience(AudienceKind.CHARACTER_INSTANCE, character) if character else MemoryAudience(AudienceKind.SOUL, target.soul_id)
        return SessionMemoryContext(self.actor, target, opened.session_id, opened.writer_epoch, viewer)

    def current(self):
        if not self.state['sessions']:
            raise X2Error('START_ROLEPLAY_FIRST')
        return self.state['sessions'][-1]

    def rp_context(self, session):
        target = scope(session['scope'])
        w = self.world.snapshot(self.actor, target.world_id)
        binding = next((b for b in w.sessions if str(b.session_id) == session['binding']), None)
        if binding is None or binding.status.value != 'open':
            raise X2Error('SESSION_CHANGED', 'recovery')
        ctx = SessionMemoryContext(self.actor, target, binding.session_id, binding.writer_epoch,
            MemoryAudience(AudienceKind.CHARACTER_INSTANCE, DomainId.parse(session['character'])))
        return OwnerMemoryContext(self.actor, target), ctx

    def new_roleplay(self):
        if self.state['pending']:
            raise X2Error('RECOVERY_REQUIRED', 'recovery')
        if self.state['sessions'] and self.current()['phase'] != 'ended':
            raise X2Error('END_ROLEPLAY_FIRST')
        if len(self.state['sessions']) >= 7:
            raise X2Error('FIXTURE_LIMIT_REACHED')
        # World 多步建立没有跨 API 原子事务。先持久标记，未知结果一律保全停写。
        self.state['pending'] = dict(action='new', payload={}, time=stamp())
        self.save()
        ref = DefinitionRef(DomainId.parse(self.state['definition'][0]), DefinitionVersion(self.state['definition'][1]))
        w = self.world.create_roleplay_world(self.actor, self.soul_scope.soul_id, datetime.now(timezone.utc))
        self.fault('after_world')
        w = self.world.instantiate(self.actor, w.world.world_id, w.timeline.scope.timeline_id,
                                   ref, w.world.revision, datetime.now(timezone.utc))
        ctx = self._session(w.timeline.scope, w.characters[0].character_instance_id)
        self.state['sessions'].append(dict(scope=scope_values(ctx.scope), character=str(ctx.viewer.target),
            binding=str(ctx.session_id), started=stamp(), phase='roleplay', turns=[], candidate=None, accepted=None))
        self.state['pending'] = None
        self.save()

    def begin(self, action, payload):
        request = payload['request']
        if type(request) is not str or not re.fullmatch('[0-9a-f]{32}', request):
            raise X2Error('REQUEST_INVALID')
        fingerprint = hashlib.sha256(json.dumps([action, payload], sort_keys=True).encode()).hexdigest()
        old = self.state['completed'].get(request)
        if old:
            if old != fingerprint:
                raise X2Error('REQUEST_REPLAY_MISMATCH')
            return False
        if self.state['pending']:
            raise X2Error('RECOVERY_REQUIRED', 'recovery')
        self.state['pending'] = dict(action=action, payload=payload, fingerprint=fingerprint,
                                     time=stamp(), stage='prepared')
        self.save()
        return True

    def recover(self):
        pending = self.state['pending']
        self.soul_owner = OwnerMemoryContext(self.actor, self.soul_scope)
        if pending:
            # 新运行代次已围住旧 lease；只查 Core 已提交的唯一操作回执，不补写半轮。
            try:
                if pending['action'] in ('new', 'end'):
                    raise X2Error('RECOVERY_REQUIRED', 'world_lifecycle')
                s = self.current()
                key = pending['payload']['request']
                action = pending['action']
                if action == 'turn':
                    target = scope(s['scope'])
                    user = self.receipt(target, 'x2-turn', key + ':user')
                    model = self.receipt(target, 'x2-turn', key + ':model')
                    if user and not model:
                        raise X2Error('INCOMPLETE_TURN', 'recovery')
                    if not user or not model:
                        raise X2Error('RECOVERY_REQUIRED', 'recovery')
                    if (user.content != pending['payload']['text'] or user.provenance.source_type is not SourceType.USER_REPORT
                            or model.provenance.source_type is not SourceType.MODEL
                            or str(model.provenance.source_session_id) != s['binding']):
                        raise X2Error('RECOVERY_REQUIRED', 'recovery')
                    if not any(t['request'] == key for t in s['turns']):
                        s['turns'].append(dict(request=key, user=str(user.memory_id), model=str(model.memory_id)))
                elif action == 'finish':
                    candidate = self.receipt(self.soul_scope, 'x2-finish', key)
                    if (candidate is None or candidate.provenance.source_type is not SourceType.ROLEPLAY_RECALL
                            or candidate.provenance.canon_status is not CanonStatus.CANDIDATE
                            or candidate.provenance.source_world_id != scope(s['scope']).world_id):
                        raise X2Error('RECOVERY_REQUIRED', 'recovery')
                    s.update(candidate=str(candidate.memory_id), phase='candidate')
                elif action == 'accept':
                    accepted = self.receipt(self.soul_scope, 'x2-accept', key)
                    if (accepted is None or str(accepted.predecessor) != s['candidate']
                            or accepted.provenance.canon_status is not CanonStatus.ACCEPTED
                            or accepted.provenance.reality_status is not RealityStatus.FICTIONAL_SHARED_EXPERIENCE):
                        raise X2Error('RECOVERY_REQUIRED', 'recovery')
                    s.update(accepted=str(accepted.memory_id), phase='accepted')
                else:
                    raise X2Error('RECOVERY_REQUIRED', 'recovery')
                self.state['completed'][key] = pending['fingerprint']
                self.state['pending'] = None
                self.save()
            except X2Error:
                raise
            except Exception:
                raise X2Error('RECOVERY_REQUIRED', 'recovery') from None

    def receipt(self, target, source, slot):
        """固定 SQL 只读 Core 幂等回执；不扫描全集，不新增存储写原语。"""
        from life_engine.memory_sqlite_repository import SCOPE_SQL
        with self.repo.transaction() as tx:
            row = tx.db.execute('SELECT memory_id FROM memory_idempotency WHERE ' + SCOPE_SQL +
                ' AND producer=? AND source=? AND slot=?',
                (*scope_values(target), str(self.actor.principal_id), source, slot)).fetchone()
        if row is None:
            return None
        record = self.memory.get_memory(OwnerMemoryContext(self.actor, target), DomainId.parse(row[0]), history=True)
        if record.lifecycle is not MemoryLifecycle.LIVE:
            raise X2Error('RECOVERY_REQUIRED', 'recovery')
        return record

    def execute_pending(self):
        p = self.state['pending']
        session = self.current()
        action, data, key = p['action'], p['payload'], p['payload']['request']
        if action == 'turn':
            owner, ctx = self.rp_context(session)
            moment = datetime.fromisoformat(p['time'])
            user = self.memory.create_owner_memory(owner, MemoryCollectionRevision(p['revision']),
                IdempotencyIdentity('x2-turn', key + ':user'), content=data['text'], kind=MemoryKind.EPISODIC,
                provenance=Provenance(SourceType.USER_REPORT, key, moment, self.actor,
                                      RealityStatus.USER_CLAIMED, CanonStatus.ACCEPTED), audience=(ctx.viewer,))
            self.fault('after_user')
            replay = 'OFFLINE_REPLAY：已记录合成情节；请继续描述灯塔探险。'
            model = self.memory.create_session_candidate(ctx, self.memory.collection_revision(owner),
                IdempotencyIdentity('x2-turn', key + ':model'), content=replay, kind=MemoryKind.EPISODIC,
                provenance=Provenance(SourceType.MODEL, key, moment, self.actor, RealityStatus.FICTIONAL,
                    CanonStatus.CANDIDATE, ctx.scope.world_id, ctx.scope.timeline_id, ctx.session_id))
            self.fault('after_pair')
            if not any(t['request'] == key for t in session['turns']):
                session['turns'].append(dict(request=key, user=str(user.memory_id), model=str(model.memory_id)))
        elif action == 'finish':
            target = scope(session['scope'])
            owner = OwnerMemoryContext(self.actor, target)
            viewer = MemoryAudience(AudienceKind.CHARACTER_INSTANCE, DomainId.parse(session['character']))
            records = []
            for turn in session['turns']:
                for label, source in (('user', SourceType.USER_REPORT), ('model', SourceType.MODEL)):
                    r = self.memory.get_memory(owner, DomainId.parse(turn[label]), history=True)
                    if (r.lifecycle is not MemoryLifecycle.LIVE or r.scope != target
                            or r.provenance.source_type is not source or r.provenance.actor != self.actor
                            or r.provenance.source_id != turn['request']
                            or r.audience != (viewer,)
                            or (label == 'user' and (r.provenance.canon_status is not CanonStatus.ACCEPTED
                                or r.provenance.reality_status is not RealityStatus.USER_CLAIMED))
                            or (label == 'model' and (str(r.provenance.source_session_id) != session['binding']
                                or r.provenance.source_world_id != target.world_id
                                or r.provenance.source_timeline_id != target.timeline_id
                                or r.provenance.reality_status is not RealityStatus.FICTIONAL
                                or r.provenance.canon_status is not CanonStatus.CANDIDATE))):
                        raise X2Error('SOURCE_MEMBERSHIP_DENIED', 'finish')
                    records.append(r)
            source = recall.RecallSource(target, '灯塔守望者', 'x2-synthetic-v1', len(session['turns']),
                datetime.fromisoformat(session['started']), datetime.fromisoformat(p['time']), _select_highlights(records))
            candidate = recall.record_recall(self.memory, self.soul_owner, source,
                                             identity=IdempotencyIdentity('x2-finish', key))
            self.fault('after_candidate')
            session.update(candidate=str(candidate.memory_id), phase='candidate')
        elif action == 'accept':
            candidate = DomainId.parse(session['candidate'])
            accepted = self.memory.accept_memory(self.soul_owner, candidate, MemoryCollectionRevision(data['revision']),
                                                 IdempotencyIdentity('x2-accept', key))
            result = self.memory.get_memory(self.soul_owner, accepted.memory_id)
            if (result.predecessor != candidate or result.provenance.source_type is not SourceType.ROLEPLAY_RECALL
                    or result.provenance.source_world_id != scope(session['scope']).world_id
                    or result.provenance.reality_status is not RealityStatus.FICTIONAL_SHARED_EXPERIENCE):
                raise X2Error('ACCEPT_RECEIPT_INVALID', 'accept')
            self.fault('after_accept')
            session.update(accepted=str(accepted.memory_id), phase='accepted')
        self.state['completed'][key] = p['fingerprint']
        self.state['pending'] = None
        self.fault('before_index')
        self.save()

    def mutate(self, action, payload):
        with self.mutex:
            self.check_integrity()
            if self.state['pending']:
                raise X2Error('RECOVERY_REQUIRED', 'recovery')
            fields = {'new': set(), 'turn': {'request', 'text'}, 'finish': {'request'},
                      'accept': {'request', 'revision'}, 'end': set(), 'feedback': {'rating', 'reason'}}
            if action not in fields or set(payload) != fields[action]:
                raise X2Error('FIELDS_INVALID', 'http')
            if action == 'new':
                self.new_roleplay()
            elif action == 'feedback':
                if payload['rating'] not in ('useful', 'miss', 'confusing') or payload['reason'] not in ('none', 'retrieval', 'source', 'recovery', 'ui'):
                    raise X2Error('FEEDBACK_INVALID')
                if len(self.state['feedback']) >= 100:
                    raise X2Error('FEEDBACK_LIMIT_REACHED')
                self.state['feedback'].append(dict(payload))
                self.save()
            elif action == 'end':
                if self.state['pending']:
                    raise X2Error('RECOVERY_REQUIRED')
                s = self.current()
                if s['phase'] not in ('candidate', 'accepted', 'ended'):
                    raise X2Error('CREATE_CANDIDATE_FIRST')
                if s['phase'] != 'ended':
                    self.state['pending'] = dict(action='end', payload={}, time=stamp())
                    self.save()
                    target = scope(s['scope'])
                    w = self.world.snapshot(self.actor, target.world_id)
                    opened = next((b for b in w.sessions if b.status.value == 'open'), None)
                    if opened:
                        self.world.exit(self.actor, target.world_id, target.timeline_id, opened.session_id,
                                        w.world.revision, w.world.writer_epoch)
                    s['phase'] = 'ended'
                    self.state['pending'] = None
                    self.save()
            else:
                s = self.current()
                key = payload.get('request')
                if key not in self.state['completed']:
                    required = {'turn': 'roleplay', 'finish': 'roleplay', 'accept': 'candidate'}[action]
                    if s['phase'] != required and not (action == 'finish' and s['phase'] == 'interrupted'):
                        raise X2Error('PHASE_INVALID')
                    if action == 'turn':
                        text(payload['text'])
                        if len(s['turns']) >= 4:
                            raise X2Error('SESSION_LIMIT_REACHED')
                    if action == 'finish' and not s['turns']:
                        raise X2Error('NO_COMPLETE_TURN')
                    if action == 'accept' and (type(payload['revision']) is not int or payload['revision'] != self.memory.collection_revision(self.soul_owner).value):
                        raise X2Error('REVISION_CONFLICT', 'accept')
                if self.begin(action, payload):
                    if action == 'turn':
                        self.state['pending']['revision'] = self.memory.collection_revision(self.rp_context(s)[0]).value
                        self.save()
                    try:
                        self.execute_pending()
                    except Exception:
                        # 未能唯一确认提交结果，留 journal 给下次受控重开。
                        raise X2Error('RECOVERY_REQUIRED', 'mutation') from None
            return self.view()

    def check_integrity(self):
        for path in self.root.rglob('*'):
            checked_path(path)
        if d.read(self.root / 'x2.json') != self.state:
            raise X2Error('CONTROL_CHANGED', 'isolation')
        if self.state['package'] != package_hash():
            raise X2Error('PACKAGE_CHANGED', 'isolation')
        if d.registry(self.root / 'install') != self.registry_snapshot:
            raise X2Error('REGISTRY_CHANGED', 'isolation')

    def record_view(self, record):
        p = record.provenance
        return dict(id=str(record.memory_id), content=record.content, source=p.source_type.value,
                    reality=p.reality_status.value, canon=p.canon_status.value,
                    source_world=str(p.source_world_id), source_timeline=str(p.source_timeline_id),
                    source_reference=p.source_id, predecessor=str(record.predecessor))

    def view(self, query=''):
        with self.mutex:
            self.check_integrity()
            normalized = validate_query(query, 6, 6)
            visible = [r for r in self.memory.query(self.soul_session, limit=100).records if recall.is_recall(r)]
            selected = select_recall(visible, normalized, 6)
            s = self.state['sessions'][-1] if self.state['sessions'] else None
            candidate = None
            if s and s['candidate']:
                candidate = self.record_view(self.memory.get_memory(self.soul_owner, DomainId.parse(s['accepted'] or s['candidate']), history=True))
            turns = []
            if s:
                owner = OwnerMemoryContext(self.actor, scope(s['scope']))
                for turn in s['turns']:
                    turns.append({k: self.memory.get_memory(owner, DomainId.parse(turn[k]), history=True).content for k in ('user', 'model')})
            return dict(version=VERSION, fixture=self.identifier, mode='OFFLINE_REPLAY / MODEL_NOT_CONNECTED',
                        phase=s['phase'] if s else 'empty', turns=turns, candidate=candidate,
                        revision=self.memory.collection_revision(self.soul_owner).value,
                        recalls=[self.record_view(r) for r in selected],
                        diagnostic='RECOVERY_REQUIRED' if self.state['pending'] else ('RECALL_MATCH' if selected else
                            ('NO_LEXICAL_MATCH' if visible else 'NO_ACCEPTED_RECALL')),
                        sessions=len(self.state['sessions']), feedback_count=len(self.state['feedback']))

    def export(self):
        with self.mutex:
            self.check_integrity()
            return diagnostic_report(self.state)


def diagnostic_report(state):
    validate_control(state)
    return dict(version=VERSION, python=sys.version.split()[0], data_schema=8,
        mode='OFFLINE_REPLAY', sessions=len(state['sessions']),
        turns=sum(len(s['turns']) for s in state['sessions']),
        accepted=sum(bool(s['accepted']) for s in state['sessions']),
        diagnostic='RECOVERY_REQUIRED' if state['pending'] else 'CONTROL_READABLE',
        pending=bool(state['pending']), feedback=[dict(rating=f['rating'], reason=f['reason']) for f in state['feedback']],
        initializer=state['probe'], real_model_calls=0, real_send=False)


def offline_report(identifier):
    """停止后查元数据不打开业务 DB，不推进 World 运行代次。"""
    root = fixture_path(identifier)
    if not root.is_dir():
        raise X2Error('FIXTURE_NOT_FOUND', 'open')
    for path in root.rglob('*'):
        checked_path(path)
    with d.locked(root, 'x2-ui', timeout=.3):
        state = d.read(root / 'x2.json')
        if state['version'] != VERSION or state['package'] != package_hash():
            raise X2Error('FIXTURE_VERSION_MISMATCH', 'open')
        return diagnostic_report(state)
