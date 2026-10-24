# C2 PROVIDER-TOOLS 完整相关差异

为避免Markdown空白检查歧义，diff中仅含一个ASCII空格的上下文行以可见符号 `␠` 表示；提取patch时将**整行** `␠` 还原为一个ASCII空格，其余字节不变。该符号不属于源码，台账hash对应还原后的patch。

审查证据，不在本PR安装或执行。Base `baa59729babf9ac56a17e02c682de2e3086e3575`。C2逐文件字节摘要见[证据台账](../../LE-RESET-01-X2-A-REVIEW-EVIDENCE.md)。

本附件含该组全部 8 文件差异；统一换行为LF并移除UTF-8 BOM后做unified diff；原始字节hash另存，因此不能把应用patch后的LF字节冒充原CRLF字节。所有新增文件模式为普通文件；不含真实密钥、Host配置或聊天。

## integrations/hermes_memory/__init__.py

~~~~~~~~diff
--- /dev/null
+++ b/integrations/hermes_memory/__init__.py
@@ -0,0 +1,224 @@
+"""Life Engine 记忆 provider for Hermes.
+
+官方扩展点：``agent.memory_provider.MemoryProvider`` → ``MemoryManager`` 分发，
+每轮调用 ``prefetch(query)`` 把召回内容注入上下文。
+
+行为：
+- ``sync_turn``    每轮把 user/assistant 文本写入 Life Engine 的角色扮演世界
+- ``on_session_end`` 把本轮会话汇总成一条 Soul 回忆录（虚构共同经历）
+- ``prefetch``     读出 Soul 回忆录，带"这是角色扮演"边界后注入
+
+配置失效时禁用，不选择其他目标；生命周期普通异常在包装层隔离。
+本地固定诊断不进入模型上下文，不承诺宿主注册副作用的回滚。
+"""
+from __future__ import annotations
+
+import json
+import os
+import sys
+from pathlib import Path
+from types import MappingProxyType
+
+try:  # Hermes 运行时
+    from agent.memory_provider import MemoryProvider
+except Exception:  # 仓库内单测没有 Hermes
+    class MemoryProvider:  # type: ignore[no-redef]
+        """仓库内测试用的最小替身。"""
+
+try:
+    from .recall_service import RecallService
+except ImportError:  # 被 Hermes 以非包方式加载时
+    sys.path.insert(0, str(Path(__file__).resolve().parent))
+    from recall_service import RecallService
+
+def _settings():
+    """完整文件为权威；仅入口确实不存在才使用三个显式环境目标。"""
+    path = Path(__file__).resolve().parent / 'settings.json'
+    try:
+        path.lstat()
+    except FileNotFoundError:
+        config = {
+            key: os.environ.get(env)
+            for key, env in (
+                ('runtime_path', 'LIFE_ENGINE_RUNTIME'),
+                ('root', 'LIFE_ENGINE_RECALL_ROOT'),
+                ('profile_home', 'HERMES_PROFILE_DIR'))}
+        if any(value is None for value in config.values()):
+            return {}, 'CONFIG_MISSING_TARGET'
+    except Exception:
+        return {}, 'CONFIG_READ_FAILED'
+    else:
+        try:
+            raw = path.read_text(encoding='utf-8')
+        except UnicodeError:
+            return {}, 'CONFIG_INVALID'
+        except Exception:
+            return {}, 'CONFIG_READ_FAILED'
+        try:
+            config = json.loads(raw)
+        except ValueError:
+            return {}, 'CONFIG_INVALID'
+    if type(config) is not dict:
+        return {}, 'CONFIG_INVALID'
+    paths = ('runtime_path', 'root', 'profile_home')
+    if any(key not in config for key in paths):
+        return {}, 'CONFIG_MISSING_TARGET'
+    for key in paths:
+        value = config[key]
+        if type(value) is not str or not value or value != value.strip() or '\0' in value:
+            return {}, 'CONFIG_INVALID'
+        try:
+            value.encode('utf-8')
+        except UnicodeError:
+            return {}, 'CONFIG_INVALID'
+    character = config.get('character_name', '')
+    auto_record = config.get('auto_record', True)
+    if type(character) is not str or type(auto_record) is not bool:
+        return {}, 'CONFIG_INVALID'
+    return {**{key: config[key] for key in paths},
+            'character_name': character, 'auto_record': auto_record}, ''
+
+
+class LifeEngineMemoryProvider(MemoryProvider):
+    """把 Life Engine 的回忆录接进 Hermes 的每轮上下文。"""
+
+    def __init__(self, service=None):
+        self._injected = service is not None
+        config, reason = {}, ''
+        if not self._injected:
+            try:
+                config, reason = _settings()
+            except Exception:
+                reason = 'CONFIG_READ_FAILED'
+        self._config = MappingProxyType(config)
+        self._reason = reason
+        self._configured = self._injected or not reason
+        self._service = service
+        self._session_id = ''
+
+    # --- 必需接口 ---------------------------------------------------------
+
+    def name(self) -> str:
+        return 'life_engine'
+
+    def is_available(self) -> bool:
+        return self._available_service() is not None
+
+    def initialize(self, session_id: str, **kwargs) -> None:
+        try:
+            self._session_id = session_id or ''
+            self._available_service()
+        except Exception:
+            if self._configured:
+                self._reason = 'SERVICE_UNAVAILABLE'
+
+    def get_tool_schemas(self):
+        return []
+
+    # --- 召回 -------------------------------------------------------------
+
+    def prefetch(self, query: str, *, session_id: str = "") -> str:
+        try:
+            service = self._available_service()
+            if service is None:
+                return ''
+            rendered = service.render(service.recall(query))
+            if isinstance(rendered, str):
+                return rendered
+            self._reason = 'SERVICE_UNAVAILABLE'
+            return ''
+        except Exception:  # noqa: BLE001
+            self._reason = 'SERVICE_UNAVAILABLE'
+            return ''
+
+    def recall_status(self):
+        return None
+
+    def system_prompt_block(self) -> str:
+        return ''
+
+    def identity_signature(self):
+        if self._injected or not self._configured:
+            return {}
+        return {'life_engine_root': self._config.get('root', '')}
+
+    def unavailable_reason(self) -> str:
+        """只报告包装层固定码，不读取服务的自由文本诊断。"""
+        return self._reason
+
+    # --- 记录 -------------------------------------------------------------
+
+    def sync_turn(self, user_content: str, assistant_content: str, *,
+                  session_id: str = '', messages=None, turn_author=None) -> None:
+        if not self._config.get('auto_record', True):
+            return
+        try:
+            service = self._available_service()
+            if service is None:
+                return
+            service.remember_turn('user', user_content)
+            service.remember_turn('assistant', assistant_content)
+        except Exception:  # noqa: BLE001
+            self._reason = 'SERVICE_UNAVAILABLE'
+            return
+
+    def on_session_end(self, messages) -> None:
+        if not self._config.get('auto_record', True):
+            return
+        try:
+            service = self._available_service()
+            if service is not None:
+                service.flush_recall()
+        except Exception:  # noqa: BLE001
+            self._reason = 'SERVICE_UNAVAILABLE'
+            return
+
+    def on_session_switch(self, new_session_id: str, *, parent_session_id: str = '',
+                          reset: bool = False, rewound: bool = False, **kwargs) -> None:
+        try:
+            if reset and self._config.get('auto_record', True):
+                service = self._available_service()
+                if service is None:
+                    return
+                service.flush_recall()
+            self._session_id = new_session_id or ''
+        except Exception:  # noqa: BLE001
+            self._reason = 'SERVICE_UNAVAILABLE'
+            return
+
+    # --- 内部 -------------------------------------------------------------
+
+    def _available_service(self):
+        """每次回调只探测一次；后续回调仍使用同一份目标快照。"""
+        if not self._configured:
+            return None
+        try:
+            service = self._recall_service()
+            if service.available() is True:
+                if self._reason == 'SERVICE_UNAVAILABLE':
+                    self._reason = ''
+                return service
+        except Exception:
+            pass
+        self._reason = 'SERVICE_UNAVAILABLE'
+        return None
+
+    def _recall_service(self):
+        if self._service is None:
+            self._service = RecallService(
+                self._config['runtime_path'],
+                self._config['root'],
+                self._config['profile_home'],
+                self._config.get('character_name', ''),
+                auto_record=self._config.get('auto_record', True))
+        return self._service
+
+
+def register(ctx) -> None:
+    provider = None
+    try:
+        provider = LifeEngineMemoryProvider()
+        ctx.register_memory_provider(provider)
+    except Exception:
+        if provider is not None and provider._reason in ('', 'SERVICE_UNAVAILABLE'):
+            provider._reason = 'PROVIDER_REGISTRATION_FAILED'
~~~~~~~~

## integrations/hermes_memory/plugin.yaml

~~~~~~~~diff
--- /dev/null
+++ b/integrations/hermes_memory/plugin.yaml
@@ -0,0 +1,3 @@
+name: life_engine
+version: 1.0.0
+description: "Life Engine 角色扮演回忆录：把每轮对话记进独立 World，并在退出后让 Soul 记得、且知道那是扮演。"
~~~~~~~~

## integrations/hermes_memory/recall_service.py

~~~~~~~~diff
--- /dev/null
+++ b/integrations/hermes_memory/recall_service.py
@@ -0,0 +1,634 @@
+"""Life Engine 记忆服务：给 Hermes MemoryProvider 用的 Core 封装。
+
+不依赖 Hermes，可单独测试。服务显式报告扫描与游标失败，调用方负责
+宿主回合的失败隔离，不能把损坏数据解释成没有待处理轮次。
+
+一个 store = 一个 Soul；每个角色卡 Profile 一个角色扮演世界：
+
+    ~/.life-engine-hermes/
+      install/                 一个 Life Engine 实例
+      state.json               Soul 作用域 + characters[key] → 该角色的 RP 作用域
+      flush.json               characters[key] → 已登记轮次游标
+      host/                    合成的 Host 目录（不随 Profile 变化）
+
+因此退出任何角色后，Soul 都记得自己扮演过哪些角色。
+"""
+import hashlib
+import json
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+import unicodedata
+
+MAX_TURN_BYTES = 1200
+MAX_HIGHLIGHT_BYTES = 180
+MAX_HIGHLIGHTS = 6
+MAX_RECALL_ITEMS = 6
+BOUNDARY = '（以下是角色扮演经历，不是真实发生过的事实）'
+STATE_VERSION = 2
+
+
+def _utcnow():
+    return datetime.now(timezone.utc)
+
+
+class RecallCursorError(Exception):
+    """当前布局的 flush 游标损坏；不携带正文或路径。"""
+
+    code = 'CURSOR_INVALID'
+
+    def __init__(self):
+        super().__init__(self.code)
+
+
+class RecallService:
+    """把 Hermes 的对话轮次写成角色扮演记忆，并从中生成 Soul 回忆录。"""
+
+    def __init__(self, runtime_path, root, profile_home, character_name='', *,
+                 auto_record=True, clock=None, character_key=None):
+        self.runtime_path = Path(runtime_path)
+        self.root = Path(root).expanduser()
+        self.profile_home = Path(profile_home).expanduser()
+        self.character_name = (character_name or '').strip()[:120]
+        self.auto_record = bool(auto_record)
+        self.clock = clock or _utcnow
+        self.character_key = (character_key or self.profile_home.name or 'default')[:64]
+        self._ready = False
+        self._error = ''
+        self._state = None
+
+    # --- 生命周期 ---------------------------------------------------------
+
+    def available(self):
+        try:
+            self.ensure()
+            return True
+        except Exception as exc:  # noqa: BLE001 - 记忆层不得让宿主失败
+            self._error = f'{type(exc).__name__}: {exc}'[:300]
+            return False
+
+    def unavailable_reason(self):
+        return self._error
+
+    def characters(self):
+        """已登记的角色键（用于诊断）。"""
+        self.ensure()
+        return tuple(sorted(self._state['characters']))
+
+    def ensure(self):
+        if self._ready:
+            return self
+        if str(self.runtime_path) not in sys.path:
+            sys.path.insert(0, str(self.runtime_path))
+        from life_engine import durable
+        from life_engine.memory_runtime import MemoryRuntime
+        from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
+        from life_engine.world_runtime import WorldRuntime
+        from life_engine.world_sqlite_repository import SQLiteWorldRepository
+
+        self.root.mkdir(parents=True, exist_ok=True)
+        state_path = self.root / 'state.json'
+        if not state_path.exists():
+            from life_engine.domain import DomainId, IdKind
+            self._create_install(durable)
+            self._save({'version': STATE_VERSION,
+                        'principal': str(DomainId.new(IdKind.PRINCIPAL)),
+                        'owner': str(DomainId.new(IdKind.OWNER)),
+                        'soul': str(DomainId.new(IdKind.SOUL)),
+                        'characters': {}})
+        state = self._migrate(json.loads(state_path.read_text(encoding='utf-8')))
+
+        install = self.root / 'install'
+        registry = durable.registry(install)
+        key = _single(registry['instances'])
+        db = durable.state_home(install, registry['instances'][key]) / 'agents/synthetic/life.db'
+        self._world = WorldRuntime(SQLiteWorldRepository(db))
+        self._memory = MemoryRuntime(SQLiteMemoryRepository(
+            install, key, runtime_id=self._world.repository.runtime_id))
+        self._actor = _principal(state)
+
+        changed = False
+        if not state.get('soul_world'):
+            self._create_soul_world(state)
+            changed = True
+        if self.character_key not in state['characters']:
+            self._create_character(state)
+            changed = True
+        self._state = state
+        if changed:
+            self._save(state)
+
+        self._soul_owner = _owner_ctx(self._actor, state, 'soul')
+        self._rp_owner = _owner_ctx(self._actor, state['characters'][self.character_key], 'rp')
+        self._ready = True
+        return self
+
+    def _create_install(self, durable):
+        from life_engine.config import defaults
+        host = self.root / 'host'
+        host.mkdir(parents=True, exist_ok=True)
+        cfg = defaults('synthetic')
+        cfg['integration'].update(adapter='hermes', host_home=str(host))
+        durable.create_install(_package_root(self.runtime_path), self.root / 'install', cfg)
+
+    def _save(self, state):
+        (self.root / 'state.json').write_text(
+            json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
+
+    # --- 迁移与建世界 -----------------------------------------------------
+
+    def _migrate(self, state):
+        """旧版扁平结构（单个 rp_*）→ 多角色结构，保留已有回忆录。"""
+        if state.get('version') == STATE_VERSION:
+            state.setdefault('characters', {})
+            return state
+        migrated = {'version': STATE_VERSION, 'characters': {}}
+        for field in ('principal', 'owner', 'soul'):
+            if field in state:
+                migrated[field] = state[field]
+        if state.get('soul_world'):
+            for field in ('owner', 'soul', 'world', 'timeline'):
+                migrated[f'soul_{field}'] = state[f'soul_{field}']
+        if state.get('rp_world'):
+            entry = {f'rp_{f}': state[f'rp_{f}'] for f in ('owner', 'soul', 'world', 'timeline')}
+            entry['name'] = state.get('character') or self.character_name
+            migrated['characters'][self.character_key] = entry
+        self._save(migrated)
+        self._migrate_cursor()
+        return migrated
+
+    def _migrate_cursor(self):
+        path = self.root / 'flush.json'
+        if not path.exists():
+            return
+        try:
+            cursor = json.loads(path.read_text(encoding='utf-8'))
+        except ValueError:
+            return
+        if 'characters' in cursor:
+            return
+        path.write_text(json.dumps({'characters': {
+            self.character_key: {'flushed': int(cursor.get('flushed', 0))}}}), encoding='utf-8')
+
+    def _create_soul_world(self, state):
+        from life_engine.domain import (CanonStatus, DomainId, IdKind, Provenance, RealityStatus,
+                                        SourceType, Soul, World, WorldKind, WorldScope,
+                                        WorldStatus, WorldTimeline)
+        from life_engine.world_repository import WorldSnapshot
+
+        now = self.clock()
+        actor = _principal(state)
+        soul = Soul(DomainId.parse(state['soul']), actor.owner_id, DomainId.new(IdKind.WORLD))
+        self._world.register_soul(actor, soul)
+        scope = WorldScope(actor.owner_id, soul.soul_id, soul.soul_world_id,
+                           DomainId.new(IdKind.TIMELINE))
+        prov = Provenance(SourceType.OWNER_COMMAND, 'Hermes 记忆 provider', now, actor,
+                          RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
+        with self._world.repository.transaction() as tx:
+            tx.add_world(WorldSnapshot(
+                World(scope.world_id, scope.owner_id, scope.soul_id, WorldKind.SOUL, prov,
+                      WorldStatus.ACTIVE),
+                WorldTimeline(scope, prov)))
+        for field in ('owner', 'soul', 'world', 'timeline'):
+            state[f'soul_{field}'] = str(getattr(scope, f'{field}_id'))
+
+    def _create_character(self, state):
+        from life_engine.domain import (CanonStatus, DefinitionRef, DefinitionVersion, DomainId,
+                                        IdKind, Provenance, RealityStatus, SourceType, Values,
+                                        CharacterDefinition)
+
+        now = self.clock()
+        actor = _principal(state)
+        soul_id = DomainId.parse(state['soul'])
+        label = self.character_name or self.character_key
+        definition = CharacterDefinition(
+            DefinitionRef(DomainId.new(IdKind.DEFINITION), DefinitionVersion(1)),
+            actor.owner_id, label, Values(),
+            Provenance(SourceType.IMPORT, f'hermes-profile:{self.character_key}', now, actor,
+                       RealityStatus.UNKNOWN, CanonStatus.UNREVIEWED))
+        self._world.register_definition(actor, definition)
+        rp = self._world.create_roleplay_world(actor, soul_id, now)
+        rp = self._world.instantiate(actor, rp.world.world_id, rp.timeline.scope.timeline_id,
+                                     definition.reference, rp.world.revision, now)
+        entry = {f'rp_{field}': str(getattr(rp.timeline.scope, f'{field}_id'))
+                 for field in ('owner', 'soul', 'world', 'timeline')}
+        entry['name'] = self.character_name or self.character_key
+        state['characters'][self.character_key] = entry
+
+    # --- 写入：记录一轮 ---------------------------------------------------
+
+    def remember_turn(self, role, text, *, at=None):
+        if not self.auto_record:
+            return None
+        self.ensure()
+        text = _excerpt(text or '', MAX_TURN_BYTES)
+        if not text or role not in ('user', 'assistant'):
+            return None
+        from life_engine.domain import CanonStatus, Provenance, RealityStatus, SourceType
+        from life_engine.memory import (AudienceKind, IdempotencyIdentity, MemoryAudience,
+                                        MemoryKind)
+        moment = at or self.clock()
+        user_side = role == 'user'
+        provenance = Provenance(
+            SourceType.USER_REPORT if user_side else SourceType.MODEL,
+            f'hermes:{self.character_key}:{role}', moment, self._actor,
+            RealityStatus.USER_CLAIMED if user_side else RealityStatus.FICTIONAL,
+            CanonStatus.ACCEPTED,
+            source_world_id=self._rp_owner.scope.world_id,
+            source_timeline_id=self._rp_owner.scope.timeline_id)
+        slot = hashlib.sha256(
+            f'{self.character_key}|{role}|{moment.isoformat()}|{text}'.encode('utf-8')).hexdigest()[:32]
+        return self._memory.create_owner_memory(
+            self._rp_owner, self._memory.collection_revision(self._rp_owner),
+            IdempotencyIdentity('hermes-memory', slot), content=text,
+            kind=MemoryKind.EPISODIC, provenance=provenance,
+            audience=(MemoryAudience(AudienceKind.WORLD),))
+
+    # --- 写入：把本轮扮演登记成回忆录 -------------------------------------
+
+    def _flush_cursor(self, path):
+        """只缺文件或缺当前角色才从零开始；已有损坏值不自动修复。"""
+        try:
+            raw = path.read_text(encoding='utf-8')
+        except FileNotFoundError:
+            cursor = {'characters': {}}
+        except UnicodeError:
+            raise RecallCursorError() from None
+        else:
+            try:
+                cursor = json.loads(raw)
+            except ValueError:
+                raise RecallCursorError() from None
+        if not isinstance(cursor, dict) or not isinstance(cursor.get('characters'), dict):
+            raise RecallCursorError()
+        entries = cursor['characters']
+        if self.character_key not in entries:
+            entries[self.character_key] = {'flushed': 0}
+        mine = entries[self.character_key]
+        if (not isinstance(mine, dict) or type(mine.get('flushed')) is not int
+                or mine['flushed'] < 0):
+            raise RecallCursorError()
+        return cursor, mine
+
+    def flush_recall(self, *, accept=True):
+        """把本角色世界里尚未登记的轮次汇总成一条 Soul 回忆录。"""
+        self.ensure()
+        path = self.root / 'flush.json'
+        cursor, mine = self._flush_cursor(path)
+        # count 只对应已证明纯追加历史中的前 N 次创建，不依赖墙钟或随机 ID 排序。
+        records = self._memory.scan_owner_memory(self._rp_owner, append_only=True).records
+        seen = mine['flushed']
+        if seen > len(records):
+            raise RecallCursorError()
+        pending = records[seen:]
+        if not pending:
+            return None
+        from life_engine import roleplay_recall as recall_lib
+        from life_engine.domain import SourceType
+        user_turns = [r for r in pending if r.provenance.source_type is SourceType.USER_REPORT]
+        highlights = _select_highlights(pending)
+        moments = [r.created_at for r in pending]
+        source = recall_lib.RecallSource(
+            source_scope=self._rp_owner.scope,
+            character_name=self.character_name or self.character_key,
+            card_fingerprint=f'hermes-profile:{self.character_key}',
+            turn_count=len(user_turns) or len(pending),
+            started_at=min(moments), ended_at=max(moments),
+            highlights=highlights)
+        receipt = recall_lib.record_recall(
+            self._memory, self._soul_owner, source,
+            identity=_identity('hermes-recall', f'{self.character_key}-{seen}'),
+            accept=accept)
+        mine['flushed'] = len(records)
+        path.write_text(json.dumps(cursor), encoding='utf-8')
+        return receipt
+
+    # --- 读取：给 Prompt 用（跨角色共享） ---------------------------------
+
+    def recall(self, query='', limit=MAX_RECALL_ITEMS):
+        query = validate_query(query, limit, MAX_RECALL_ITEMS)
+        if limit == 0:
+            return []
+        self.ensure()
+        from life_engine import roleplay_recall as recall_lib
+        records = [r for r in self._memory.scan_owner_memory(self._soul_owner).records
+                   if recall_lib.is_recall(r)]
+        if not records:
+            return []
+        return select_recall(records, query, limit)
+
+    def render(self, records):
+        if not records:
+            return ''
+        lines = [BOUNDARY]
+        for record in records:
+            for line in record.content.splitlines():
+                if line.startswith('[') or line.startswith('这是一次'):
+                    continue
+                lines.append(line)
+            lines.append('')
+        return '\n'.join(lines).strip()
+
+
+# --- 小工具 ---------------------------------------------------------------
+
+def _single(mapping):
+    keys = list(mapping)
+    if len(keys) != 1:
+        raise ValueError('expected exactly one Life Engine instance in this store')
+    return keys[0]
+
+
+def _package_root(runtime_path):
+    return Path(runtime_path).resolve().parent
+
+
+def _excerpt(text, maximum=MAX_HIGHLIGHT_BYTES):
+    flat = ' '.join(text.split())
+    return flat.encode('utf-8')[:maximum].decode('utf-8', 'ignore')
+
+
+def _select_highlights(records):
+    """按追加序位选原文摘录：三个结构锚点，再以最远位置补齐。"""
+    from life_engine.domain import SourceType
+    first, latest, candidates, extent = None, {}, {}, 0
+    for index, record in enumerate(records):
+        extent = index + 1
+        text = _excerpt(record.content)
+        if not text:
+            continue
+        candidates.setdefault(text, index)
+        if first is None:
+            first = (text, index)
+        source = record.provenance.source_type
+        if source in (SourceType.USER_REPORT, SourceType.MODEL):
+            latest[source] = (text, index)
+    if first is None:
+        return ()
+    selected = {}
+    for anchor in (first, latest.get(SourceType.USER_REPORT), latest.get(SourceType.MODEL)):
+        if anchor is not None:
+            text, position = anchor
+            selected.setdefault(text, position)
+    remaining = {text: (index, extent)
+                 for text, index in candidates.items() if text not in selected}
+
+    def update_distances(position):
+        for text, (index, distance) in remaining.items():
+            remaining[text] = (index, min(distance, abs(index - position)))
+
+    for position in selected.values():
+        update_distances(position)
+    while remaining and len(selected) < MAX_HIGHLIGHTS:
+        text = max(remaining, key=lambda item: (remaining[item][1], -remaining[item][0]))
+        position, _ = remaining.pop(text)
+        selected[text] = position
+        update_distances(position)
+    return tuple(sorted(selected, key=selected.get))
+
+
+def _identity(source, slot):
+    from life_engine.memory import IdempotencyIdentity
+    return IdempotencyIdentity(source, slot)
+
+
+def _principal(state):
+    from life_engine.domain import DomainId, Principal
+    return Principal(DomainId.parse(state['principal']), DomainId.parse(state['owner']))
+
+
+def _owner_ctx(actor, values, prefix):
+    from life_engine.domain import DomainId, WorldScope
+    from life_engine.memory import OwnerMemoryContext
+    scope = WorldScope(*(DomainId.parse(values[f'{prefix}_{key}'])
+                         for key in ('owner', 'soul', 'world', 'timeline')))
+    return OwnerMemoryContext(actor, scope)
+
+
+# --- 纯词面召回选择 ------------------------------------------------------
+
+MAX_QUERY_BYTES = 4096
+QUOTE_PAIRS = {'「': '」', '『': '』', '“': '”', '"': '"'}
+QUOTE_CHARS = frozenset(QUOTE_PAIRS) | frozenset(QUOTE_PAIRS.values())
+# 实施前设计中固定的英文问题/功能/请求框架词；不是主题或同义词表。
+FRAMEWORK_WORDS = frozenset('''a an the and or but if then else of to in on at by for from with into onto as
+is am are was were be been being do does did can could may might must shall should will would have has had
+i me my mine we us our ours you your yours he him his she her hers it its they them their theirs
+this that these those what which who whom whose when where why how please tell explain describe
+recall remember about again ever still'''.split())
+
+
+class RecallQueryError(Exception):
+    """输入无效；固定代码不回显原始查询。"""
+    code = 'QUERY_INVALID'
+
+    def __init__(self):
+        super().__init__(self.code)
+
+
+def validate_query(query, limit, maximum):
+    """即使 limit=0 也完整校验，不截断非法输入。"""
+    if type(limit) is not int or not 0 <= limit <= maximum:
+        raise RecallQueryError()
+    if query is None:
+        query = ''
+    if type(query) is not str:
+        raise RecallQueryError()
+    try:
+        if len(query.encode('utf-8')) > MAX_QUERY_BYTES:
+            raise RecallQueryError()
+        normalized = unicodedata.normalize('NFKC', query).casefold()
+        if len(normalized.encode('utf-8')) > MAX_QUERY_BYTES:
+            raise RecallQueryError()
+    except UnicodeError:
+        raise RecallQueryError() from None
+    return normalized
+
+
+def _cjk_range(char):
+    point = ord(char)
+    return (0x3400 <= point <= 0x9fff or 0x20000 <= point <= 0x323af
+            or 0x3040 <= point <= 0x30ff or 0xac00 <= point <= 0xd7af
+            or 0xf900 <= point <= 0xfaff)
+
+
+def _cjk(char):
+    return _cjk_range(char) and unicodedata.category(char)[0] not in 'PSC'
+
+
+def _join_cjk(text, predicate=_cjk):
+    result, index = [], 0
+    while index < len(text):
+        if text[index].isspace() and text[index] not in '\r\n':
+            end = index + 1
+            while end < len(text) and text[end].isspace() and text[end] not in '\r\n':
+                end += 1
+            if result and predicate(result[-1]) and end < len(text) and predicate(text[end]):
+                index = end
+                continue
+        result.append(text[index])
+        index += 1
+    return ''.join(result)
+
+
+def _runs(text):
+    """每个标点、换行、引号及文字类别边界均终止 run。"""
+    current, kind = [], None
+    for char in _join_cjk(text):
+        next_kind = 'cjk' if _cjk(char) else ('word' if char.isalnum() or char == '_' else None)
+        if next_kind != kind or next_kind is None:
+            if current:
+                yield kind, ''.join(current)
+            current, kind = [], next_kind
+        if next_kind is not None:
+            current.append(char)
+    if current:
+        yield kind, ''.join(current)
+
+
+def _latin(word):
+    return all(char.isalpha() and unicodedata.name(char, '').startswith('LATIN') for char in word)
+
+
+def _features(text, *, short=False, framework=False):
+    features = set()
+    for kind, word in _runs(text):
+        if kind == 'cjk':
+            # 短锚点是完整2/3字 run，不从长问句内部提取短 n-gram。
+            if short and len(word) in (2, 3):
+                features.add((kind, word))
+            for size in range(4, min(8, len(word)) + 1):
+                features.update((kind, word[index:index + size]) for index in range(len(word) - size + 1))
+        elif (_latin(word) and len(word) >= (2 if short else 4)
+              and (not framework or word not in FRAMEWORK_WORDS)):
+            features.add((kind, word))
+    return features
+
+
+def _quoted(text):
+    """只给闭合且非嵌套的固定成对引号生成 anchor；分隔符仍留给 run 边界。"""
+    anchors, stack, start, valid = [], [], 0, True
+    for index, char in enumerate(text):
+        if char not in QUOTE_CHARS:
+            continue
+        if stack and char == stack[-1]:
+            stack.pop()
+            if not stack and valid:
+                anchors.append(text[start:index])
+        elif char in QUOTE_PAIRS:
+            if not stack:
+                start, valid = index + 1, True
+            else:
+                valid = False
+            stack.append(QUOTE_PAIRS[char])
+        elif stack:
+            valid = False
+    return anchors
+
+
+def _outer_punctuation(text):
+    start, end = 0, len(text)
+    while start < end and (text[start].isspace() or unicodedata.category(text[start]).startswith('P')):
+        start += 1
+    while end > start and (text[end - 1].isspace() or unicodedata.category(text[end - 1]).startswith('P')):
+        end -= 1
+    return text[start:end]
+
+
+def _label(text):
+    # 标签保留旧范围的空白兼容；普通事件用带类别过滤的_cjk。
+    return ' '.join(_join_cjk(unicodedata.normalize('NFKC', text).casefold(), _cjk_range).split())
+
+
+def _identifier(text):
+    """明确独立/引用的连续 Han+ASCII 数字标识；不跨空白组装。"""
+    text = text.strip()
+    index = len(text)
+    while index and '0' <= text[index - 1] <= '9':
+        index -= 1
+    if index < 4 or index == len(text):
+        return None
+    if all(0x3400 <= ord(char) <= 0x9fff or 0x20000 <= ord(char) <= 0x323af
+           or 0xf900 <= ord(char) <= 0xfaff for char in text[:index]):
+        return text
+    return None
+
+
+def _identifier_match(identifier, text):
+    start = text.find(identifier)
+    while start >= 0:
+        end = start + len(identifier)
+        if end == len(text) or not '0' <= text[end] <= '9':
+            return True
+        start = text.find(identifier, start + 1)
+    return False
+
+
+def _bullets(content):
+    lines = content.splitlines()
+    if (not lines or lines[0] != '[角色扮演回忆]'
+            or lines[-1] != '这是一次角色扮演经历，不是真实发生过的事实。'
+            or lines.count('期间记得的事：') != 1):
+        return ()
+    result = []
+    for line in lines[lines.index('期间记得的事：') + 1:]:
+        if not line.startswith('- '):
+            break
+        result.append(unicodedata.normalize('NFKC', line[2:]).casefold())
+    return result
+
+
+def select_recall(records, query, limit):
+    """query 已校验/归一化；返回原对象，全部强证据候选按证据长度再时间排序。"""
+    order = lambda record: (record.created_at, str(record.memory_id))
+    if not query.strip():
+        return sorted(records, key=order, reverse=True)[:limit]
+    anchors = _quoted(query)
+    independent = _outer_punctuation(query) if not (set(query) & QUOTE_CHARS) else ''
+    independent_id = _identifier(independent)
+    identifiers = {_identifier(anchor) for anchor in anchors}
+    identifiers.discard(None)
+    if independent_id:
+        identifiers.add(independent_id)
+    # 明确编号是完整锚点；不能再用它的共同中文前缀召回其他编号。
+    strong_text = '' if independent_id else query
+    for anchor in anchors:
+        if _identifier(anchor):
+            strong_text = strong_text.replace(anchor, ' ')
+    runs = list(_runs(independent))
+    single = (len(runs) == 1 and runs[0][1] == _join_cjk(independent))
+    wanted = _features(strong_text, framework=not single)
+    if single:
+        wanted |= _features(independent, short=True)
+    for anchor in anchors:
+        if not _identifier(anchor):
+            wanted |= _features(anchor, short=True)
+    event_matches = []
+    for record in records:
+        evidence = set()
+        for bullet in _bullets(record.content):
+            evidence.update(('identifier', value) for value in identifiers if _identifier_match(value, bullet))
+            # 正文可供完整短词寻找，但每个 bullet 独立，不拼成跨边界词。
+            for kind, word in _runs(bullet):
+                if kind == 'cjk':
+                    for size in range(2, min(8, len(word)) + 1):
+                        evidence.update((kind, word[index:index + size]) for index in range(len(word) - size + 1))
+                elif _latin(word) and len(word) >= 2:
+                    evidence.add((kind, word))
+        common = (wanted | {('identifier', value) for value in identifiers}) & evidence
+        if common:
+            event_matches.append((max(min(8, len(word)) for _, word in common), record))
+    if event_matches:
+        event_matches.sort(key=lambda item: (item[0], *order(item[1])), reverse=True)
+        return [record for _, record in event_matches[:limit]]
+    explicit_labels = {_label(anchor) for anchor in anchors}
+    if independent:
+        explicit_labels.add(_label(independent))
+    character_matches = []
+    for record in records:
+        labels = {_label(subject.text) for subject in record.subjects if subject.kind.value == 'text'}
+        labels.discard('角色扮演')
+        labels.discard('')
+        if labels & explicit_labels:
+            character_matches.append(record)
+    return sorted(character_matches, key=order, reverse=True)[:limit]
~~~~~~~~

## tools/hermes_memory_flush.py

~~~~~~~~diff
--- /dev/null
+++ b/tools/hermes_memory_flush.py
@@ -0,0 +1,96 @@
+"""手动汇总已登记角色的待处理轮次；不启动 Hermes，也不创建 store。"""
+import argparse
+import json
+from pathlib import Path
+import sys
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'integrations' / 'hermes_memory'))
+sys.path.insert(0, str(ROOT / 'runtime'))
+
+from recall_service import RecallCursorError, RecallService, STATE_VERSION  # noqa: E402
+from life_engine.memory_repository import MemoryFailure, MemoryRuntimeError  # noqa: E402
+
+
+class FlushError(Exception):
+    def __init__(self, code):
+        self.code = code
+        super().__init__(code)
+
+
+class FlushArgumentParser(argparse.ArgumentParser):
+    def error(self, message):
+        # argparse 的 message 可能包含路径/正文；只由 main 输出固定失败码。
+        raise FlushError('ARGUMENT_INVALID')
+
+
+def existing_service(root, profile):
+    """只打开现有布局；缺失或旧版布局不由此命令初始化、迁移。"""
+    state_path = root / 'state.json'
+    if not state_path.is_file() or not (root / 'install').is_dir():
+        raise FlushError('STORE_NOT_INITIALIZED')
+    if not profile.is_dir():
+        raise FlushError('PROFILE_NOT_FOUND')
+    if not profile.name or len(profile.name) > 64:
+        raise FlushError('CHARACTER_KEY_INVALID')
+    try:
+        state = json.loads(state_path.read_text(encoding='utf-8'))
+    except (OSError, ValueError):
+        raise FlushError('STORE_STATE_INVALID') from None
+    if not isinstance(state, dict) or state.get('version') != STATE_VERSION:
+        raise FlushError('STORE_VERSION_UNSUPPORTED')
+    characters = state.get('characters')
+    if not isinstance(characters, dict) or profile.name not in characters:
+        raise FlushError('CHARACTER_NOT_REGISTERED')
+    character = characters[profile.name]
+    if (not isinstance(character, dict)
+            or not all(state.get(key) for key in
+                       ('principal', 'owner', 'soul', 'soul_owner', 'soul_soul',
+                        'soul_world', 'soul_timeline'))
+            or not all(character.get('rp_' + key) for key in
+                       ('owner', 'soul', 'world', 'timeline'))):
+        raise FlushError('STORE_STATE_INVALID')
+    return RecallService(ROOT / 'runtime', root, profile,
+                         character.get('name', ''), character_key=profile.name)
+
+
+def main(argv=None):
+    parser = FlushArgumentParser(description=__doc__, allow_abbrev=False)
+    parser.add_argument('--root', required=True, help='已有回忆数据根；不自动创建')
+    parser.add_argument('--profile-home', required=True, help='已登记角色的 Profile 目录')
+    parser.add_argument('--accept', action='store_true',
+                        help='显式接受新回忆录；不指定时只登记候选，不进入正常召回')
+    try:
+        args = parser.parse_args(argv)
+        if not args.root.strip() or not args.profile_home.strip():
+            raise FlushError('ARGUMENT_INVALID')
+        service = existing_service(Path(args.root).expanduser(),
+                                   Path(args.profile_home).expanduser())
+        receipt = service.flush_recall(accept=args.accept)
+        result = {'ok': True, 'status': 'FLUSHED' if receipt else 'NO_PENDING_TURNS',
+                  'character_key': service.character_key,
+                  'memory_id': str(receipt.memory_id) if receipt else None,
+                  'requested_canon_status': ('accepted' if args.accept else 'candidate') if receipt else None,
+                  'reality_status': 'fictional_shared_experience' if receipt else None}
+    except FlushError as exc:
+        code = exc.code
+        result = {'ok': False, 'failure_code': (code if type(code) is str and code in (
+            'ARGUMENT_INVALID', 'STORE_NOT_INITIALIZED', 'PROFILE_NOT_FOUND',
+            'CHARACTER_KEY_INVALID', 'STORE_STATE_INVALID', 'STORE_VERSION_UNSUPPORTED',
+            'CHARACTER_NOT_REGISTERED') else 'FLUSH_FAILED')}
+    except RecallCursorError:
+        result = {'ok': False, 'failure_code': 'CURSOR_INVALID'}
+    except MemoryRuntimeError as exc:
+        code = getattr(exc, 'code', None)
+        result = {'ok': False, 'failure_code': (code.value if type(code) is MemoryFailure and code in (
+                                               MemoryFailure.QUERY_INCOMPLETE, MemoryFailure.HISTORY_NOT_APPEND_ONLY,
+                                               MemoryFailure.IDEMPOTENCY_CONFLICT)
+                                               else 'FLUSH_FAILED')}
+    except Exception:  # 不把数据正文、路径或底层异常回显到终端。
+        result = {'ok': False, 'failure_code': 'FLUSH_FAILED'}
+    print(json.dumps(result, ensure_ascii=False))
+    return 0 if result['ok'] else 1
+
+
+if __name__ == '__main__':
+    sys.exit(main())
~~~~~~~~

## tools/hermes_memory_install.py

~~~~~~~~diff
--- /dev/null
+++ b/tools/hermes_memory_install.py
@@ -0,0 +1,248 @@
+"""把一个 Hermes Profile 接上 Life Engine 记忆 provider（标准流程第 5 步）。
+
+确定性、可重复、可回滚：
+
+1. 把 provider 源码冻结到 ``<root>/provider/<hash8>/``（不指向开发目录）
+2. 复制进 ``<profile>/plugins/life_engine/``，写 settings.json
+3. 备份并在 config.yaml 追加 ``memory: provider: life_engine``（已有则不动）
+4. 就地验证 provider 可用并打印已登记角色
+
+失败时抛出明确错误，绝不半途改配置而不留备份。
+"""
+import argparse
+import hashlib
+import json
+import shutil
+import stat
+import sys
+import tempfile
+from datetime import datetime
+from pathlib import Path
+
+FILES = ('__init__.py', 'recall_service.py', 'plugin.yaml')
+
+
+def source_dir():
+    return Path(__file__).resolve().parent.parent / 'integrations' / 'hermes_memory'
+
+
+# 默认用同一份 package 里的 runtime；冻结包因此自包含，不依赖开发目录。
+DEFAULT_RUNTIME = str(source_dir().parent.parent / 'runtime')
+DEFAULT_ROOT = '~/.life-engine-hermes'
+
+
+def digest(directory):
+    h = hashlib.sha256()
+    for name in FILES:
+        h.update(name.encode('ascii'))
+        h.update((directory / name).read_bytes())
+    return h.hexdigest()
+
+
+class ProviderCacheError(Exception):
+    """缓存不能证明完整时，调用方只输出固定失败码。"""
+
+
+def _cache_entry(path, *, directory=False):
+    """lstat拒绝静态链接及Windows reparse，不认证整个祖先路径。"""
+    entry = path.lstat()
+    if (stat.S_ISLNK(entry.st_mode)
+            or getattr(entry, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
+            or not (stat.S_ISDIR(entry.st_mode) if directory else stat.S_ISREG(entry.st_mode))):
+        raise ProviderCacheError()
+    return entry
+
+
+def _verify_cache(path, expected):
+    _cache_entry(path, directory=True)
+    for name in FILES:
+        _cache_entry(path / name)
+    if digest(path) != expected:
+        raise ProviderCacheError()
+
+
+def _cleanup_stage(stage, identity):
+    """只清理身份未变的独占stage；不递归，不触碰target或未知文件。"""
+    try:
+        entry = _cache_entry(stage, directory=True)
+        if not identity or not identity[1] or (entry.st_dev, entry.st_ino) != identity:
+            return
+        known = []
+        for name in FILES:
+            path = stage / name
+            try:
+                _cache_entry(path)
+            except FileNotFoundError:
+                continue
+            known.append(path)
+        for path in known:
+            path.unlink()
+        stage.rmdir()
+    except Exception:
+        # 清理不能掩盖主失败；不改用递归删除或转删其他目录。
+        return
+
+
+def freeze(src, root):
+    """完整核验才复用；认领目录和xb写入均不覆盖竞争者。"""
+    stage, identity = None, None
+    try:
+        expected = digest(src)
+        version = expected[:8]
+        branch = root / 'provider'
+        try:
+            branch.lstat()
+        except FileNotFoundError:
+            branch.mkdir(parents=True, exist_ok=False)
+        _cache_entry(branch, directory=True)
+        target = branch / version
+        try:
+            target.lstat()
+        except FileNotFoundError:
+            pass
+        else:
+            _verify_cache(target, expected)
+            return target, version
+        stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=branch))
+        entry = _cache_entry(stage, directory=True)
+        identity = (entry.st_dev, entry.st_ino)
+        for name in FILES:
+            shutil.copy2(src / name, stage / name)
+        _verify_cache(stage, expected)
+        _cache_entry(branch, directory=True)
+        target.mkdir(exist_ok=False)
+        for name in FILES:
+            with (stage / name).open('rb') as source, (target / name).open('xb') as destination:
+                shutil.copyfileobj(source, destination)
+        _verify_cache(target, expected)
+        return target, version
+    except Exception:
+        raise ProviderCacheError() from None
+    finally:
+        if stage is not None:
+            _cleanup_stage(stage, identity)
+
+
+def has_memory_block(text):
+    return any(line.startswith('memory:') for line in text.splitlines())
+
+
+class InstallArgumentParser(argparse.ArgumentParser):
+    def error(self, message):
+        # message可含用户输入；解析失败只允许main输出固定码。
+        raise ValueError('ARGUMENT_INVALID')
+
+
+def main():
+    parser = InstallArgumentParser(description='给一个 Hermes Profile 接入 Life Engine 记忆 provider',
+                                   allow_abbrev=False)
+    parser.add_argument('--profile-home', required=True,
+                        help='目标 Profile 目录，例如 ~/.hermes/profiles/suyao')
+    parser.add_argument('--character-name', required=True, help='该 Profile 的角色显示名')
+    parser.add_argument('--runtime', default=DEFAULT_RUNTIME, help='Life Engine runtime 目录')
+    parser.add_argument('--root', default=DEFAULT_ROOT, help='回忆数据根（所有角色共用）')
+    parser.add_argument('--dry-run', action='store_true', help='只检查不修改')
+    parser.add_argument('--skip-verify', action='store_true', help='跳过就地可用性验证')
+    try:
+        args = parser.parse_args()
+        if any(type(value) is not str or not value.strip()
+               for value in (args.root, args.runtime, args.profile_home)):
+            return fail('ARGUMENT_INVALID')
+    except Exception:
+        return fail('ARGUMENT_INVALID')
+
+    profile = Path(args.profile_home).expanduser()
+    config = profile / 'config.yaml'
+    if not profile.is_dir():
+        return fail(f'PROFILE_NOT_FOUND: {profile}')
+    if not config.is_file():
+        return fail(f'PROFILE_CONFIG_MISSING: {config}')
+    if not Path(args.runtime).is_dir():
+        return fail(f'RUNTIME_NOT_FOUND: {args.runtime}')
+
+    root = Path(args.root).expanduser()
+    src = source_dir()
+    if not (src / 'recall_service.py').is_file():
+        return fail(f'PROVIDER_SOURCE_MISSING: {src}')
+
+    text = config.read_text(encoding='utf-8')
+    already = has_memory_block(text)
+    destination = profile / 'plugins' / 'life_engine'
+
+    try:
+        source_hash = digest(src)
+    except Exception:
+        return fail('PROVIDER_CACHE_INVALID')
+    plan = {
+        'profile': str(profile),
+        'character': args.character_name,
+        'provider_source_sha256': source_hash[:16],
+        'freeze_to': str(root / 'provider' / source_hash[:8]),
+        'install_to': str(destination),
+        'config_already_has_memory': already,
+        'dry_run': bool(args.dry_run),
+    }
+    if args.dry_run:
+        print(json.dumps(plan, ensure_ascii=False, indent=2))
+        return 0
+
+    try:
+        frozen, version = freeze(src, root)
+        # plan与freeze各自取摘要；Profile写入前仍须绑定本次计划的完整内容。
+        _verify_cache(frozen, source_hash)
+    except Exception:
+        return fail('PROVIDER_CACHE_INVALID')
+    destination.mkdir(parents=True, exist_ok=True)
+    for name in FILES:
+        shutil.copy2(frozen / name, destination / name)
+    (destination / 'settings.json').write_text(json.dumps({
+        'runtime_path': args.runtime,
+        'root': str(root),
+        'profile_home': str(profile),
+        'character_name': args.character_name,
+        'auto_record': True,
+    }, ensure_ascii=False, indent=2), encoding='utf-8')
+    (destination / 'installed.json').write_text(json.dumps({
+        'provider_version': version,
+        'provider_sha256': digest(frozen),
+        'character_name': args.character_name,
+        'installed_at': datetime.now().astimezone().isoformat(timespec='seconds'),
+    }, ensure_ascii=False, indent=2), encoding='utf-8')
+
+    if already:
+        plan['config_backup'] = None
+        plan['config_note'] = 'memory 段已存在，未改动'
+    else:
+        backup = config.with_name(config.name + '.bak-life-engine-' +
+                                  datetime.now().strftime('%Y%m%d_%H%M%S'))
+        shutil.copy2(config, backup)
+        config.write_text(text.rstrip('\n') + '\n\nmemory:\n  provider: life_engine\n',
+                          encoding='utf-8')
+        plan['config_backup'] = str(backup)
+
+    if not args.skip_verify:
+        plan['verify'] = verify(args.runtime, root, profile, args.character_name)
+    print(json.dumps(plan, ensure_ascii=False, indent=2))
+    return 0 if plan.get('verify', {}).get('available', True) else 2
+
+
+def verify(runtime, root, profile, character):
+    sys.path.insert(0, str(runtime))
+    sys.path.insert(0, str(profile / 'plugins' / 'life_engine'))
+    try:
+        from recall_service import RecallService
+        service = RecallService(runtime, root, profile, character)
+        if not service.available():
+            return {'available': False, 'reason': service.unavailable_reason()}
+        return {'available': True, 'characters': list(service.characters())}
+    except Exception as exc:  # noqa: BLE001
+        return {'available': False, 'reason': f'{type(exc).__name__}: {exc}'[:200]}
+
+
+def fail(message):
+    print(json.dumps({'status': 'FAILED', 'error': message}, ensure_ascii=False))
+    return 1
+
+
+if __name__ == '__main__':
+    raise SystemExit(main())
~~~~~~~~

## tools/hermes_memory_manage.py

~~~~~~~~diff
--- /dev/null
+++ b/tools/hermes_memory_manage.py
@@ -0,0 +1,132 @@
+"""按显式目标查看/接受已登记角色的 Soul 回忆候选；本地可信管理入口。"""
+import argparse
+import json
+from pathlib import Path
+import sys
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'runtime'))
+
+from hermes_memory_flush import existing_service, FlushError  # noqa: E402
+from life_engine.domain import CanonStatus, DomainId, IdKind, RealityStatus, SourceType  # noqa: E402
+from life_engine.memory import (AudienceKind, IdempotencyIdentity, MemoryAudience, MemoryCollectionRevision,
+                                MemoryKind, MemoryLifecycle)  # noqa: E402
+from life_engine.memory_repository import MemoryFailure, MemoryRuntimeError  # noqa: E402
+
+FLUSH_CODES = frozenset({'STORE_NOT_INITIALIZED', 'PROFILE_NOT_FOUND', 'CHARACTER_KEY_INVALID',
+                         'STORE_STATE_INVALID', 'STORE_VERSION_UNSUPPORTED', 'CHARACTER_NOT_REGISTERED'})
+
+
+class ManagementError(Exception):
+    """只携带本工具固定失败码。"""
+    def __init__(self, code):
+        self.code = code
+        super().__init__(code)
+
+
+class _Parser(argparse.ArgumentParser):
+    def __init__(self, *args, **kwargs):
+        kwargs.setdefault('allow_abbrev', False)
+        super().__init__(*args, **kwargs)
+
+    def error(self, message):
+        raise ManagementError('ARGUMENT_INVALID')
+
+
+def _arguments(argv):
+    parser = _Parser(prog='hermes_memory_manage', description=__doc__)
+    commands = parser.add_subparsers(dest='command', required=True)
+    for name in ('inspect', 'accept'):
+        command = commands.add_parser(name)
+        command.add_argument('--root', required=True, help='已有 store；不初始化或迁移')
+        command.add_argument('--profile-home', required=True, help='已有角色目录；按 basename 登记')
+        command.add_argument('--memory-id', required=True, help='明确的规范 Memory UUID4')
+        if name == 'accept':
+            command.add_argument('--expected-revision', required=True, help='首次写入的 Soul 集合修订')
+    args = parser.parse_args(argv)
+    try:
+        if not args.root.strip() or not args.profile_home.strip():
+            raise ValueError()
+        args.target = DomainId.parse(args.memory_id)
+        if args.target.kind is not IdKind.MEMORY:
+            raise ValueError()
+        if args.command == 'accept':
+            raw = args.expected_revision
+            if not raw or not all('0' <= char <= '9' for char in raw):
+                raise ValueError()
+            significant = raw.lstrip('0') or '0'
+            if len(significant) > 19 or int(significant) > (1 << 63) - 1:
+                raise ValueError()
+            args.revision = MemoryCollectionRevision(int(significant))
+    except ValueError:
+        raise ManagementError('ARGUMENT_INVALID') from None
+    return args
+
+
+def _bound_target(record, service):
+    """只绑定已授权 Soul 与指定角色来源；不查源 World 当前存在性。"""
+    provenance = record.provenance
+    if (record.scope != service._soul_owner.scope
+            or provenance.source_type is not SourceType.ROLEPLAY_RECALL
+            or provenance.reality_status is not RealityStatus.FICTIONAL_SHARED_EXPERIENCE
+            or record.kind is not MemoryKind.SHARED_EXPERIENCE
+            or record.audience != (MemoryAudience(AudienceKind.SOUL, service._soul_owner.scope.soul_id),)
+            or provenance.source_world_id != service._rp_owner.scope.world_id
+            or provenance.source_timeline_id != service._rp_owner.scope.timeline_id):
+        raise ManagementError('TARGET_NOT_AVAILABLE')
+
+
+def _execute(args):
+    service = existing_service(Path(args.root).expanduser(), Path(args.profile_home).expanduser())
+    service.ensure()
+    memory, owner = service._memory, service._soul_owner
+    target = memory.get_memory(owner, args.target, history=True)
+    _bound_target(target, service)
+    if args.command == 'inspect':
+        return {'ok': True, 'memory_id': str(target.memory_id), 'character_key': service.character_key,
+                'canon_status': target.provenance.canon_status.value, 'lifecycle': target.lifecycle.value,
+                'source_type': target.provenance.source_type.value,
+                'reality_status': target.provenance.reality_status.value,
+                'collection_revision': memory.collection_revision(owner).value,
+                'superseded_by': str(target.superseded_by) if target.superseded_by else None}
+    if (target.provenance.canon_status is not CanonStatus.CANDIDATE
+            or target.lifecycle not in (MemoryLifecycle.LIVE, MemoryLifecycle.SUPERSEDED)):
+        raise ManagementError('TARGET_NOT_AVAILABLE')
+    receipt = memory.accept_memory(owner, args.target, args.revision,
+                                   IdempotencyIdentity('hermes-recall-management', 'accept:' + str(args.target)))
+    result = memory.get_memory(owner, receipt.memory_id)
+    _bound_target(result, service)
+    if (result.provenance.canon_status is not CanonStatus.ACCEPTED
+            or result.lifecycle is not MemoryLifecycle.LIVE or result.predecessor != args.target):
+        raise ManagementError('TARGET_NOT_AVAILABLE')
+    return {'ok': True, 'requested_memory_id': str(args.target), 'resulting_memory_id': str(result.memory_id),
+            'revision': receipt.revision.value, 'canon_status': 'accepted',
+            'reality_status': 'fictional_shared_experience'}
+
+
+def main(argv=None):
+    try:
+        result = _execute(_arguments(argv))
+    except ManagementError as exc:
+        code = exc.code if type(exc.code) is str and exc.code in {'ARGUMENT_INVALID', 'TARGET_NOT_AVAILABLE'} else 'MANAGEMENT_FAILED'
+        result = {'ok': False, 'failure_code': code}
+    except FlushError as exc:
+        code = exc.code if type(exc.code) is str and exc.code in FLUSH_CODES else 'MANAGEMENT_FAILED'
+        result = {'ok': False, 'failure_code': code}
+    except MemoryRuntimeError as exc:
+        code = getattr(exc, 'code', None)
+        failure = 'MANAGEMENT_FAILED'
+        if type(code) is MemoryFailure:
+            if code in (MemoryFailure.REVISION_CONFLICT, MemoryFailure.IDEMPOTENCY_CONFLICT):
+                failure = code.value
+            elif code is MemoryFailure.NOT_AVAILABLE:
+                failure = 'TARGET_NOT_AVAILABLE'
+        result = {'ok': False, 'failure_code': failure}
+    except Exception:
+        result = {'ok': False, 'failure_code': 'MANAGEMENT_FAILED'}
+    print(json.dumps(result, ensure_ascii=False))
+    return 0 if result['ok'] else 1
+
+
+if __name__ == '__main__':
+    sys.exit(main())
~~~~~~~~

## tools/roleplay_recall_eval.py

~~~~~~~~diff
--- /dev/null
+++ b/tools/roleplay_recall_eval.py
@@ -0,0 +1,401 @@
+"""固定合成语料的召回质量基线；只创建临时 store，无真实数据根入口。"""
+import argparse
+from dataclasses import replace
+from datetime import datetime, timedelta
+import hashlib
+import json
+from pathlib import Path
+import re
+import sys
+import tempfile
+from types import SimpleNamespace
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'runtime'))
+sys.path.insert(0, str(ROOT / 'integrations' / 'hermes_memory'))
+
+from recall_service import BOUNDARY, RecallService  # noqa: E402
+from life_engine import roleplay_recall as recall_lib  # noqa: E402
+from life_engine.domain import (CanonStatus, DomainId, IdKind, Provenance, RealityStatus,
+                                Soul, SourceType)  # noqa: E402
+from life_engine.memory import (AudienceKind, IdempotencyIdentity, MemoryAudience,
+                                MemoryKind, MemorySubject, SubjectKind)  # noqa: E402
+from life_engine.memory_repository import MemoryFailure, MemoryRuntimeError  # noqa: E402
+
+CORPUS = ROOT / 'tests' / 'fixtures' / 'roleplay_recall_eval' / 'v1.json'
+CORPUS_SHA256 = '82859adddc510cf350dcf963f8456cd43f1f135b8de9de2784faab2a959eebc0'
+UUID_PATTERN = re.compile(r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}')
+PHASES = ('retrieval', 'summary', 'characters', 'boundaries', 'retry', 'generic_mutations')
+REQUIRED_PROBES = frozenset({
+    'fictional_source', 'render_boundary', 'synthetic_unknown_fact_absent',
+    'characters_share_soul', 'distinct_character_origins', 'source_character_attribution',
+    'candidate_exists_as_candidate', 'candidate_not_recalled',
+    'repeat_flush_does_not_accept_candidate', 'forgotten_not_recalled',
+    'forgotten_not_revived_by_repeat_flush', 'same_soul_source_positive_control',
+    'foreign_source_is_different_soul', 'foreign_soul_source_denied',
+    'owner_write_positive_control', 'bridge_write_denied',
+    'injected_cursor_failure_observed', 'retry_does_not_duplicate', 'repeat_flush_is_noop',
+    'generic_valid_recall_positive', 'generic_missing_source_denied', 'generic_wrong_kind_denied',
+    'generic_world_audience_denied', 'generic_entity_subject_denied',
+    'recall_audience_expansion_denied', 'supersede_forged_recall_denied',
+    'recall_source_replacement_denied', 'recall_source_identity_preserved'})
+
+
+class EvaluationError(Exception):
+    """只公开固定代码，避免在失败报告里泄露原始异常。"""
+
+    def __init__(self, code):
+        self.code = code
+        super().__init__(code)
+
+
+def canonical_bytes(value):
+    return json.dumps(value, ensure_ascii=False, sort_keys=True,
+                      separators=(',', ':')).encode('utf-8')
+
+
+def source_hashes():
+    """绑定被测 Core、服务和评测入口；不读取任何 Host 文件。"""
+    paths = sorted((ROOT / 'runtime' / 'life_engine').rglob('*.py'))
+    paths += sorted((ROOT / 'integrations' / 'hermes_memory').glob('*.py'))
+    paths.append(Path(__file__).resolve())
+    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
+            for path in paths}
+
+
+def load_corpus():
+    raw = CORPUS.read_bytes()
+    if hashlib.sha256(raw).hexdigest() != CORPUS_SHA256:
+        raise EvaluationError('CORPUS_HASH_MISMATCH')
+    corpus = json.loads(raw)
+    if corpus['version'] != 'RR-EVAL-01/v1' or corpus['scope'] != 'LOCAL_SYNTHETIC':
+        raise EvaluationError('CORPUS_VERSION_UNSUPPORTED')
+    return corpus
+
+
+class SyntheticRun:
+    """路径来自本次 TemporaryDirectory，不暴露外部 store 参数。"""
+
+    def __init__(self, base, corpus, report):
+        self.base = base
+        self.corpus = corpus
+        self.report = report
+        self.origin = datetime.fromisoformat(corpus['time_origin'])
+        self.tick = 0
+
+    def now(self):
+        self.tick += 1
+        return self.origin + timedelta(seconds=self.tick)
+
+    def service(self, store, key='character', name='合成角色'):
+        profile = self.base / 'profiles' / key
+        profile.mkdir(parents=True, exist_ok=True)
+        service = RecallService(ROOT / 'runtime', self.base / store, profile, name,
+                                clock=self.now, character_key=key)
+        service.ensure()
+        return service
+
+    def batch(self, service, turns, *, accept=True):
+        for role, text in turns:
+            service.remember_turn(role, text)
+        return service.flush_recall(accept=accept)
+
+    def check(self, label, passed):
+        self.report['safety']['checks'].append({'id': label, 'passed': bool(passed)})
+
+    def check_records(self, service, records):
+        for record in records:
+            provenance = record.provenance
+            self.check('fictional_source', provenance.source_type.value == 'roleplay_recall'
+                       and provenance.reality_status.value == 'fictional_shared_experience'
+                       and provenance.canon_status.value == 'accepted')
+        self.check('render_boundary', not records or service.render(records).startswith(BOUNDARY))
+
+    def retrieval(self):
+        fixture = self.corpus['retrieval']
+        service = self.service('retrieval', name=fixture['character'])
+        labels = {}
+        for batch in fixture['batches']:
+            receipt = self.batch(service, batch['turns'])
+            labels[str(receipt.memory_id)] = batch['label']
+        for case in fixture['queries']:
+            records = service.recall(case['query'])
+            actual = [labels[str(record.memory_id)] for record in records]
+            desired = case['desired']
+            missing = [label for label in desired if label not in actual]
+            extra = [label for label in actual if label not in desired]
+            self.report['quality']['retrieval'].append({
+                'id': case['id'], 'query': case['query'], 'reason': case['reason'],
+                'desired_labels': desired, 'actual_labels': actual,
+                'missing_labels': missing, 'off_topic_labels': extra,
+                'target_coverage': (len(desired) - len(missing)) / len(desired) if desired else None,
+                'returned_count': len(actual), 'off_topic_count': len(extra),
+                'prompt_bytes': len(service.render(records).encode('utf-8')),
+                'status': 'MET' if not missing and not extra else 'GAP'})
+            self.check_records(service, records)
+
+    def summary(self):
+        fixture = self.corpus['summary']
+        service = self.service('summary', name=fixture['character'])
+        self.batch(service, fixture['turns'])
+        records = service.recall()
+        text = '\n'.join(record.content for record in records)
+        retained = [{'fragment': fragment, 'retained': fragment in text}
+                    for fragment in fixture['desired_fragments']]
+        self.report['quality']['summary'] = {
+            'desired_fragments': retained,
+            'desired_fragment_retention': sum(item['retained'] for item in retained) / len(retained),
+            'normalized_content': UUID_PATTERN.sub('<uuid>', text),
+            'prompt_bytes': len(service.render(records).encode('utf-8')),
+            'status': 'MET' if all(item['retained'] for item in retained) else 'GAP'}
+        self.check('synthetic_unknown_fact_absent', fixture['absent_fragment'] not in text)
+        self.check_records(service, records)
+
+    def characters(self):
+        labels, scopes, origins = {}, [], {}
+        for fixture in self.corpus['multi_character']:
+            service = self.service('shared', fixture['key'], fixture['name'])
+            scopes.append(service._soul_owner.scope)
+            receipt = self.batch(service, [('user', fixture['text'])])
+            labels[str(receipt.memory_id)] = fixture['label']
+            origins[fixture['label']] = (service._rp_owner.scope.world_id, fixture['name'])
+            # 服务顺序生命周期；不在旧 WorldRuntime 上继续操作。
+        records = service.recall()
+        actual = [labels[str(record.memory_id)] for record in records]
+        self.check('characters_share_soul', scopes[0] == scopes[1])
+        self.check('distinct_character_origins', len({item[0] for item in origins.values()}) == 2)
+        for record in records:
+            world, name = origins[labels[str(record.memory_id)]]
+            self.check('source_character_attribution', record.provenance.source_world_id == world
+                       and name in record.content)
+        self.check_records(service, records)
+        self.report['quality']['multi_character'] = {
+            'desired_labels': sorted(origins), 'actual_labels': sorted(actual),
+            'status': 'MET' if set(actual) == set(origins) else 'GAP'}
+
+    def boundaries(self):
+        fixture = self.corpus['boundaries']
+        service = self.service('candidate')
+        receipt = self.batch(service, [('user', fixture['candidate_text'])], accept=False)
+        stored = service._memory.get_memory(service._soul_owner, receipt.memory_id, history=True)
+        self.check('candidate_exists_as_candidate', stored.provenance.canon_status.value == 'candidate')
+        self.check('candidate_not_recalled', service.recall(fixture['candidate_text']) == [])
+        self.check('repeat_flush_does_not_accept_candidate', service.flush_recall(accept=True) is None
+                   and service.recall() == [])
+        service = self.service('forgotten')
+        receipt = self.batch(service, [('user', fixture['forgotten_text'])])
+        service._memory.delete_memory(service._soul_owner, receipt.memory_id,
+                                      service._memory.collection_revision(service._soul_owner),
+                                      IdempotencyIdentity('eval', 'forget'))
+        self.check('forgotten_not_recalled', service.recall() == [] and service.recall() == [])
+        self.check('forgotten_not_revived_by_repeat_flush', service.flush_recall() is None
+                   and service.recall() == [])
+        self.permissions(service)
+
+    def permissions(self, service):
+        source = recall_lib.RecallSource(service._rp_owner.scope, ended_at=self.now(),
+                                        highlights=('合成权限检查',))
+        positive = recall_lib.record_recall(
+            service._memory, service._soul_owner, source,
+            identity=IdempotencyIdentity('eval', 'same-soul-control'), accept=True)
+        self.check('same_soul_source_positive_control', any(
+            record.memory_id == positive.memory_id for record in service.recall()))
+        foreign_soul = Soul(DomainId.new(IdKind.SOUL), service._actor.owner_id,
+                            DomainId.new(IdKind.WORLD))
+        service._world.register_soul(service._actor, foreign_soul)
+        foreign_world = service._world.create_roleplay_world(service._actor, foreign_soul.soul_id,
+                                                             self.now())
+        foreign_scope = foreign_world.timeline.scope
+        self.check('foreign_source_is_different_soul', foreign_scope.soul_id != service._soul_owner.scope.soul_id
+                   and foreign_scope.owner_id == service._soul_owner.scope.owner_id)
+        try:
+            recall_lib.record_recall(
+                service._memory, service._soul_owner, replace(source, source_scope=foreign_scope),
+                identity=IdempotencyIdentity('eval', 'foreign-soul'), accept=True)
+        except MemoryRuntimeError as exc:
+            denied = exc.code in (MemoryFailure.INVALID_SOURCE, MemoryFailure.AUTHORIZATION_DENIED)
+        else:
+            denied = False
+        self.check('foreign_soul_source_denied', denied)
+        provenance = Provenance(SourceType.OWNER_COMMAND, '合成权限正控', self.now(), service._actor,
+                                RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
+        control = service._memory.create_owner_memory(
+            service._soul_owner, service._memory.collection_revision(service._soul_owner),
+            IdempotencyIdentity('eval', 'owner-control'), content='合成写入正控',
+            kind=MemoryKind.EPISODIC, provenance=provenance,
+            audience=recall_lib.recall_audience(service._soul_owner.scope.soul_id))
+        self.check('owner_write_positive_control', service._memory.get_memory(
+            service._soul_owner, control.memory_id).content == '合成写入正控')
+        provenance = replace(provenance, source_type=SourceType.BRIDGE)
+        try:
+            service._memory.create_owner_memory(
+                service._soul_owner, service._memory.collection_revision(service._soul_owner),
+                IdempotencyIdentity('eval', 'bridge'), content='合成 Bridge 不能写入',
+                kind=MemoryKind.EPISODIC, provenance=provenance,
+                audience=recall_lib.recall_audience(service._soul_owner.scope.soul_id))
+        except MemoryRuntimeError as exc:
+            denied = exc.code in (MemoryFailure.INVALID_SOURCE, MemoryFailure.AUTHORIZATION_DENIED)
+        else:
+            denied = False
+        self.check('bridge_write_denied', denied)
+
+    def retry(self):
+        service = self.service('retry')
+        service.remember_turn('user', self.corpus['boundaries']['retry_text'])
+        original = Path.write_text
+
+        def fail_cursor(path, *args, **kwargs):
+            if path == service.root / 'flush.json':
+                raise OSError('SYNTHETIC_CURSOR_WRITE_FAILURE')
+            return original(path, *args, **kwargs)
+
+        failed = False
+        with patch.object(Path, 'write_text', fail_cursor):
+            try:
+                service.flush_recall()
+            except OSError:
+                failed = True
+        before = service.recall()
+        service.flush_recall()
+        after = service.recall()
+        repeated = service.flush_recall()
+        self.check('injected_cursor_failure_observed', failed)
+        self.check('retry_does_not_duplicate', len(before) == len(after) == 1
+                   and before[0].memory_id == after[0].memory_id)
+        self.check('repeat_flush_is_noop', repeated is None)
+        self.report['quality']['retry'] = {
+            'injected_failure_observed': failed, 'records_before_retry': len(before),
+            'records_after_retry': len(after), 'repeat_flush_noop': repeated is None}
+
+    def generic_mutations(self):
+        """直接打泛写入口，不能只验证专用 API 的正向闭环。"""
+        service = self.service('generic-mutations')
+        provenance = recall_lib.build_provenance(recall_lib.RecallSource(
+            service._rp_owner.scope, ended_at=self.now(), highlights=('合成安全正控',)),
+            service._actor, canon=CanonStatus.ACCEPTED)
+        owner = service._soul_owner
+        memory = service._memory
+
+        def create(slot, **changes):
+            params = dict(content='合成安全回忆', kind=MemoryKind.SHARED_EXPERIENCE,
+                          provenance=provenance, audience=recall_lib.recall_audience(owner.scope.soul_id))
+            params.update(changes)
+            return memory.create_owner_memory(owner, memory.collection_revision(owner),
+                                              IdempotencyIdentity('eval-generic', slot), **params)
+
+        def reject_unchanged(label, operation):
+            before = memory.collection_revision(owner)
+            try:
+                operation()
+            except MemoryRuntimeError:
+                passed = memory.collection_revision(owner) == before
+            else:
+                passed = False
+            self.check(label, passed)
+
+        positive = create('positive')
+        self.check('generic_valid_recall_positive', any(
+            record.memory_id == positive.memory_id for record in service.recall()))
+        forged = replace(provenance, source_world_id=DomainId.new(IdKind.WORLD),
+                         source_timeline_id=DomainId.new(IdKind.TIMELINE))
+        reject_unchanged('generic_missing_source_denied', lambda: create('missing', provenance=forged))
+        reject_unchanged('generic_wrong_kind_denied', lambda: create('kind', kind=MemoryKind.EPISODIC))
+        reject_unchanged('generic_world_audience_denied', lambda: create(
+            'audience', audience=(MemoryAudience(AudienceKind.WORLD),)))
+        reject_unchanged('generic_entity_subject_denied', lambda: create(
+            'subject', subjects=(MemorySubject(SubjectKind.SOUL, owner.scope.soul_id),)))
+        reject_unchanged('recall_audience_expansion_denied', lambda: memory.change_audience(
+            owner, positive.memory_id, memory.collection_revision(owner),
+            IdempotencyIdentity('eval-generic', 'expand'), audience=(MemoryAudience(AudienceKind.WORLD),)))
+        ordinary_provenance = Provenance(SourceType.OWNER_COMMAND, '合成普通来源', self.now(),
+                                         service._actor, RealityStatus.USER_CLAIMED, CanonStatus.ACCEPTED)
+        ordinary = create('ordinary', provenance=ordinary_provenance)
+        reject_unchanged('supersede_forged_recall_denied', lambda: memory.supersede_memory(
+            owner, ordinary.memory_id, memory.collection_revision(owner),
+            IdempotencyIdentity('eval-generic', 'introduce'), content='合成伪造回忆', provenance=forged))
+        source_control = create('source-control')
+        reject_unchanged('recall_source_replacement_denied', lambda: memory.supersede_memory(
+            owner, source_control.memory_id, memory.collection_revision(owner),
+            IdempotencyIdentity('eval-generic', 'replace-source'), content='替换来源', provenance=forged))
+        identity_control = create('identity-control')
+        reject_unchanged('recall_source_identity_preserved', lambda: memory.supersede_memory(
+            owner, identity_control.memory_id, memory.collection_revision(owner),
+            IdempotencyIdentity('eval-generic', 'shed-source'), content='扮演不能脱壳变成事实',
+            provenance=ordinary_provenance))
+
+
+def validate_completion(report, corpus):
+    """缺少探针或整个阶段不能被空集 all() 变成安全通过。"""
+    present = {item['id'] for item in report['safety']['checks']}
+    quality = report['quality']
+    completed = (
+        report['execution'].get('completed_phases') == list(PHASES)
+        and REQUIRED_PROBES <= present
+        and [item['id'] for item in quality['retrieval']] == [
+            item['id'] for item in corpus['retrieval']['queries']]
+        and len(quality.get('summary', {}).get('desired_fragments', [])) == len(
+            corpus['summary']['desired_fragments'])
+        and quality.get('multi_character', {}).get('desired_labels') == sorted(
+            item['label'] for item in corpus['multi_character'])
+        and {'injected_failure_observed', 'records_before_retry', 'records_after_retry',
+             'repeat_flush_noop'} <= quality.get('retry', {}).keys())
+    if not completed:
+        raise EvaluationError('EVALUATION_INCOMPLETE')
+
+
+def evaluate():
+    """每次全新合成环境；执行成功与安全、质量分别呈现。"""
+    report = {
+        'version': 'RR-EVAL-01/v1', 'scope': 'LOCAL_SYNTHETIC',
+        'bindings': {'corpus_sha256': CORPUS_SHA256},
+        'execution': {'status': 'NOT_EXECUTED', 'completed_phases': []},
+        'safety': {'status': 'NOT_EXECUTED', 'checks': [], 'required_probe_ids': sorted(REQUIRED_PROBES)},
+        'quality': {'status': 'NOT_EXECUTED', 'retrieval': [],
+                    'off_topic_definition': '返回标签不在该查询冻结desired集合中的记录数；不是自然度评分',
+                    'not_measured': ['自然度', '真实模型理解', '真实Host跨会话', '真实发送']}}
+    try:
+        report['bindings']['sources'] = source_hashes()
+        report['bindings']['sources_sha256'] = hashlib.sha256(
+            canonical_bytes(report['bindings']['sources'])).hexdigest()
+        corpus = load_corpus()
+        with tempfile.TemporaryDirectory(prefix='le-rr-eval-synthetic-') as temporary:
+            run = SyntheticRun(Path(temporary).resolve(), corpus, report)
+            # Core 记录落盘时间也固定；不只固定 provider 的来源时间。
+            with patch('life_engine.memory_runtime.datetime',
+                       SimpleNamespace(now=lambda tz: run.now())):
+                for phase in PHASES:
+                    getattr(run, phase)()
+                    report['execution']['completed_phases'].append(phase)
+        validate_completion(report, corpus)
+        report['execution']['status'] = 'COMPLETED'
+        report['safety']['status'] = 'PASS' if all(
+            item['passed'] for item in report['safety']['checks']) else 'FAIL'
+        cases = report['quality']['retrieval'] + [report['quality']['summary'],
+                                                 report['quality']['multi_character']]
+        report['quality']['status'] = 'GAPS_OBSERVED' if any(
+            item['status'] == 'GAP' for item in cases) else 'FIXTURE_EXPECTATIONS_MET'
+    except Exception as exc:  # 固定错误码；不回显原始异常、数据或临时路径。
+        report['execution'] = {'status': 'ERROR', 'failure_code': (
+            exc.code if isinstance(exc, EvaluationError) else 'EVALUATION_EXECUTION_FAILED')}
+        report['safety']['status'] = 'INCOMPLETE'
+        report['quality']['status'] = 'INCOMPLETE'
+    report['semantic_sha256'] = hashlib.sha256(canonical_bytes(report)).hexdigest()
+    return report
+
+
+def exit_code(report):
+    return 0 if (report['execution']['status'] == 'COMPLETED'
+                 and report['safety']['status'] == 'PASS') else 1
+
+
+def main(argv=None):
+    parser = argparse.ArgumentParser(description=__doc__)
+    parser.parse_args(argv)  # 故意没有 root/profile/corpus 参数。
+    report = evaluate()
+    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
+    return exit_code(report)
+
+
+if __name__ == '__main__':
+    sys.exit(main())
~~~~~~~~

## examples/cosplay_recall_trial.py

~~~~~~~~diff
--- /dev/null
+++ b/examples/cosplay_recall_trial.py
@@ -0,0 +1,337 @@
+"""角色扮演回忆录本地试用：扮演 → 退出 → Soul 记得，且知道那是扮演。
+
+全部在系统临时目录里的新建合成实例中进行；不读取现有聊天或角色卡，
+不连接模型、宿主或网络。输出固定标记 MODEL_NOT_CONNECTED。
+"""
+import argparse
+from datetime import datetime, timezone, timedelta
+import json
+from pathlib import Path
+import shutil
+import sys
+import tempfile
+from uuid import uuid4
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
+
+from life_engine import durable
+from life_engine import roleplay_recall as recall_lib
+from life_engine.config import defaults
+from life_engine.domain import (CanonStatus, DefinitionRef, DefinitionVersion, DomainId, IdKind,
+                                Principal, Provenance, RealityStatus, Soul, SourceType, Values,
+                                World, WorldKind, WorldScope, WorldStatus, WorldTimeline,
+                                CharacterDefinition)
+from life_engine.memory import (AudienceKind, IdempotencyIdentity, MemoryAudience, MemoryKind,
+                                OwnerMemoryContext, SessionMemoryContext)
+from life_engine.memory_runtime import MemoryRuntime
+from life_engine.memory_sqlite_repository import SQLiteMemoryRepository
+from life_engine.world_repository import WorldSnapshot
+from life_engine.world_runtime import WorldRuntime
+from life_engine.world_sqlite_repository import SQLiteWorldRepository
+
+DAY0 = datetime(2026, 10, 12, 21, 0, tzinfo=timezone.utc)
+MARKER = 'LIFE_ENGINE_COSPLAY_RECALL_TRIAL_V1'
+LINES = ('我刚进门，外面风很大。',
+         '你说的那个旧书铺，我今天路过看了。',
+         '明天我要早起，先睡了。')
+
+
+def output(value):
+    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))
+
+
+def safe_sandbox(path):
+    root = Path(tempfile.gettempdir()).resolve()
+    target = Path(path).absolute()
+
+    def linked(part):
+        try:
+            return part.is_symlink() or bool(getattr(part.lstat(), 'st_file_attributes', 0) & 0x400)
+        except FileNotFoundError:
+            return False
+
+    if any(linked(p) for p in (target, *target.parents)):
+        raise ValueError('SANDBOX_PATH_REQUIRED: 路径必须是系统临时目录下的非链接子目录')
+    target = target.resolve()
+    if target == root or root not in target.parents:
+        raise ValueError('SANDBOX_PATH_REQUIRED: 路径必须是系统临时目录下的非链接子目录')
+    return target
+
+
+def load(path):
+    base = safe_sandbox(path)
+    data = json.loads((base / 'trial.json').read_text(encoding='utf-8'))
+    if data.get('marker') != MARKER:
+        raise ValueError('NOT_COSPLAY_RECALL_SANDBOX')
+    return base, data
+
+
+def save(base, data):
+    (base / 'trial.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
+
+
+def db_path(base, data):
+    root = base / 'install'
+    inst = durable.registry(root)['instances'][data['instance']]
+    return root, durable.state_home(root, inst) / 'agents/synthetic/life.db'
+
+
+def core(base, data):
+    root, db = db_path(base, data)
+    world_repo = SQLiteWorldRepository(db)
+    actor = Principal(DomainId.parse(data['principal']), DomainId.parse(data['owner']))
+    world = WorldRuntime(world_repo)
+    memory = MemoryRuntime(SQLiteMemoryRepository(root, data['instance'], runtime_id=world_repo.runtime_id))
+    return world, memory, actor, db
+
+
+def scope_of(data, prefix):
+    return WorldScope(*(DomainId.parse(data[f'{prefix}_{k}'])
+                        for k in ('owner', 'soul', 'world', 'timeline')))
+
+
+def open_session(world, actor, scope, *, soul_viewer):
+    snapshot = world.snapshot(actor, scope.world_id)
+    current = next((s for s in snapshot.sessions if s.status.value == 'open'), None)
+    if current:
+        snapshot = world.exit(actor, scope.world_id, scope.timeline_id, current.session_id,
+                              snapshot.world.revision, snapshot.world.writer_epoch)
+    opened = world.enter(actor, scope.world_id, scope.timeline_id, None,
+                         snapshot.world.revision, snapshot.world.writer_epoch)
+    binding = opened.sessions[-1]
+    viewer = (MemoryAudience(AudienceKind.SOUL, scope.soul_id) if soul_viewer
+              else MemoryAudience(AudienceKind.CHARACTER_INSTANCE, binding.character_instance_id))
+    return SessionMemoryContext(actor, scope, binding.session_id, binding.writer_epoch, viewer)
+
+
+def describe(records):
+    return [{'id': str(r.memory_id), 'content': r.content, 'kind': r.kind.value,
+             'reality': r.provenance.reality_status.value,
+             'source_type': r.provenance.source_type.value,
+             'from_world': str(r.provenance.source_world_id) if r.provenance.source_world_id else None}
+            for r in records]
+
+
+def ensure_rp_session(world, actor, rp_scope):
+    """返回 RP 会话绑定；没有就进入或继续 cosplay。
+
+    跨进程后旧的 OPEN 会话会被既有 session fence 关闭并把世界置为 SUSPENDED，
+    因此这里必须按当前状态选 enter（CREATED）或 resume（SUSPENDED）。
+    """
+    snapshot = world.snapshot(actor, rp_scope.world_id)
+    current = next((s for s in snapshot.sessions if s.status.value == 'open'), None)
+    if current:
+        return current
+    if not snapshot.characters:
+        raise ValueError('RP_WORLD_NOT_INSTANTIATED')
+    character_id = snapshot.characters[0].character_instance_id
+    status = snapshot.world.status.value
+    if status not in ('created', 'suspended'):
+        raise ValueError(f'RP_WORLD_NOT_JOINABLE: {status}')
+    command = world.resume if status == 'suspended' else world.enter
+    opened = command(actor, rp_scope.world_id, rp_scope.timeline_id, character_id,
+                     snapshot.world.revision, snapshot.world.writer_epoch)
+    return opened.sessions[-1]
+
+
+def command_init(args):
+    base = safe_sandbox(args.sandbox) if args.sandbox else Path(tempfile.mkdtemp(prefix='life-engine-cosplay-')).resolve()
+    if args.sandbox:
+        base.mkdir(parents=False, exist_ok=False)
+    host = base / 'synthetic-host'
+    host.mkdir()
+    cfg = defaults('synthetic')
+    cfg['integration'].update(adapter='hermes', host_home=str(host))
+    result = durable.create_install(Path(__file__).resolve().parents[1], base / 'install', cfg)
+    data = {'marker': MARKER, 'instance': result['instance'], 'character': args.character,
+            'played': False, 'recall_id': None, 'accepted': False}
+    actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
+    soul = Soul(DomainId.new(IdKind.SOUL), actor.owner_id, DomainId.new(IdKind.WORLD))
+    data.update(principal=str(actor.principal_id), owner=str(actor.owner_id), soul=str(soul.soul_id))
+    world, memory, actor, db = core(base, data)
+    world.register_soul(actor, soul)
+    # Soul World：回忆录的归属地。
+    soul_scope = WorldScope(actor.owner_id, soul.soul_id, soul.soul_world_id, DomainId.new(IdKind.TIMELINE))
+    prov = Provenance(SourceType.OWNER_COMMAND, '试用：Soul 世界', DAY0, actor,
+                      RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
+    with world.repository.transaction() as tx:
+        tx.add_world(WorldSnapshot(
+            World(soul_scope.world_id, soul_scope.owner_id, soul_scope.soul_id,
+                  WorldKind.SOUL, prov, WorldStatus.ACTIVE),
+            WorldTimeline(soul_scope, prov)))
+    # 角色扮演世界：一次 cosplay。
+    rp = world.create_roleplay_world(actor, soul.soul_id, DAY0)
+    definition = CharacterDefinition(
+        DefinitionRef(DomainId.new(IdKind.DEFINITION), DefinitionVersion(1)), actor.owner_id,
+        args.character, Values(),
+        Provenance(SourceType.IMPORT, '试用：合成角色卡', DAY0, actor,
+                   RealityStatus.UNKNOWN, CanonStatus.UNREVIEWED))
+    world.register_definition(actor, definition)
+    rp = world.instantiate(actor, rp.world.world_id, rp.timeline.scope.timeline_id,
+                          definition.reference, rp.world.revision, DAY0)
+    for prefix, scope in (('soul', soul_scope), ('rp', rp.timeline.scope)):
+        for key in ('owner', 'soul', 'world', 'timeline'):
+            data[f'{prefix}_{key}'] = str(getattr(scope, f'{key}_id'))
+    save(base, data)
+    ensure_rp_session(world, actor, scope_of(data, 'rp'))
+    output({'status': 'SYNTHETIC_READY', 'sandbox': str(base), 'character': args.character,
+            'next': f'py -3.12 -X utf8 examples/cosplay_recall_trial.py play --sandbox "{base}"'})
+
+
+def command_play(args):
+    base, data = load(args.sandbox)
+    world, memory, actor, db = core(base, data)
+    if data['played']:
+        raise ValueError('ALREADY_PLAYED: 请先 exit-cosplay，或 init 新实例')
+    rp_scope = scope_of(data, 'rp')
+    rp_open = ensure_rp_session(world, actor, rp_scope)
+    viewer = MemoryAudience(AudienceKind.CHARACTER_INSTANCE, rp_open.character_instance_id)
+    owner = OwnerMemoryContext(actor, rp_scope)
+    for index, line in enumerate(LINES):
+        memory.create_owner_memory(
+            owner, memory.collection_revision(owner),
+            IdempotencyIdentity('cosplay', f'line-{index}'), content=line,
+            kind=MemoryKind.EPISODIC,
+            provenance=Provenance(SourceType.USER_REPORT, f'cosplay:用户原话 {index+1}',
+                                  DAY0 + timedelta(minutes=10 * index), actor,
+                                  RealityStatus.USER_CLAIMED, CanonStatus.ACCEPTED,
+                                  source_world_id=rp_scope.world_id,
+                                  source_timeline_id=rp_scope.timeline_id,
+                                  source_session_id=rp_open.session_id),
+            audience=(viewer,))
+    data['played'] = True
+    save(base, data)
+    output({'status': 'COSPLAY_PLAYED', 'character': data['character'],
+            'rp_world': data['rp_world'], 'lines': list(LINES),
+            'note': '这些是角色扮演世界里的对话，尚未进入 Soul'})
+
+
+def command_exit(args):
+    base, data = load(args.sandbox)
+    world, memory, actor, db = core(base, data)
+    rp_scope = scope_of(data, 'rp')
+    soul_scope = scope_of(data, 'soul')
+    snapshot = world.snapshot(actor, rp_scope.world_id)
+    session = next((s for s in snapshot.sessions if s.status.value == 'open'), None)
+    rp_owner = OwnerMemoryContext(actor, rp_scope)
+    played = memory.query(rp_owner).records
+    if session is not None:
+        world.exit(actor, rp_scope.world_id, rp_scope.timeline_id, session.session_id,
+                   snapshot.world.revision, snapshot.world.writer_epoch)
+    highlights = tuple(r.content[:60] for r in played[:6])
+    times = [r.created_at for r in played] or [DAY0]
+    source = recall_lib.RecallSource(
+        source_scope=rp_scope, character_name=data['character'],
+        card_fingerprint='synthetic-' + data['instance'][:12],
+        turn_count=len(played), started_at=min(times), ended_at=max(times),
+        highlights=highlights)
+    soul_owner = OwnerMemoryContext(actor, soul_scope)
+    # 幂等槽由"这次扮演的规模与起点"派生：重复 exit 复用同一批数据，
+    # 因此不会生成重复回忆录；真的又演了一轮则会得到新槽。
+    slot = f'turn-{len(played)}-{min(times).isoformat(timespec="minutes")}'
+    receipt = recall_lib.record_recall(
+        memory, soul_owner, source,
+        identity=IdempotencyIdentity('cosplay-recall', slot), accept=args.accept)
+    data['recall_id'] = str(receipt.memory_id)
+    data['accepted'] = bool(args.accept)
+    save(base, data)
+    output({'status': 'COSPLAY_EXITED',
+            'recall_memory_id': str(receipt.memory_id),
+            'accepted': bool(args.accept),
+            'note': ('已接受：现在会进入正常检索' if args.accept
+                     else '仍是候选：需要 accept 才进入正常检索'),
+            'next': f'py -3.12 -X utf8 examples/cosplay_recall_trial.py recall --sandbox "{base}"'})
+
+
+def command_accept(args):
+    base, data = load(args.sandbox)
+    world, memory, actor, db = core(base, data)
+    if not data.get('recall_id'):
+        raise ValueError('NO_RECALL: 请先 exit-cosplay')
+    if data.get('accepted'):
+        return output({'status': 'ALREADY_ACCEPTED', 'recall_memory_id': data['recall_id']})
+    soul_owner = OwnerMemoryContext(actor, scope_of(data, 'soul'))
+    receipt = memory.accept_memory(
+        soul_owner, DomainId.parse(data['recall_id']),
+        memory.collection_revision(soul_owner),
+        IdempotencyIdentity('cosplay-accept', uuid4().hex))
+    data['recall_id'] = str(receipt.memory_id)
+    data['accepted'] = True
+    save(base, data)
+    output({'status': 'ACCEPTED', 'recall_memory_id': str(receipt.memory_id)})
+
+
+def command_recall(args):
+    base, data = load(args.sandbox)
+    world, memory, actor, db = core(base, data)
+    soul_scope = scope_of(data, 'soul')
+    view = open_session(world, actor, soul_scope, soul_viewer=True)
+    records = memory.query(view).records
+    output({'status': 'SOUL_RECALL', 'sandbox': str(base),
+            'new_session': str(view.session_id),
+            'user_message': args.message,
+            'soul_memories': describe(records),
+            'roleplay_boundary': recall_lib.BOUNDARY,
+            'model': 'MODEL_NOT_CONNECTED',
+            'note': ('Soul 会话里能看到这段扮演经历，且标记为虚构共同经历；'
+                     '它不会被当成真实发生过的事。')})
+
+
+def command_forget(args):
+    base, data = load(args.sandbox)
+    world, memory, actor, db = core(base, data)
+    soul_owner = OwnerMemoryContext(actor, scope_of(data, 'soul'))
+    removed = []
+    for record in memory.query(soul_owner).records:
+        if recall_lib.is_recall(record):
+            memory.delete_memory(soul_owner, record.memory_id,
+                                 memory.collection_revision(soul_owner),
+                                 IdempotencyIdentity('cosplay-forget', uuid4().hex))
+            removed.append(str(record.memory_id))
+    data['recall_id'] = None
+    data['accepted'] = False
+    save(base, data)
+    output({'status': 'FORGOTTEN', 'removed': removed,
+            'normal_query': describe(memory.query(soul_owner).records)})
+
+
+def command_status(args):
+    base, data = load(args.sandbox)
+    world, memory, actor, db = core(base, data)
+    rp_owner = OwnerMemoryContext(actor, scope_of(data, 'rp'))
+    soul_owner = OwnerMemoryContext(actor, scope_of(data, 'soul'))
+    output({'status': 'STATUS', 'character': data['character'],
+            'played': data['played'], 'accepted': data.get('accepted', False),
+            'rp_world_memories': describe(memory.query(rp_owner).records),
+            'soul_world_memories': describe(memory.query(soul_owner).records),
+            'model': 'MODEL_NOT_CONNECTED'})
+
+
+def command_reset(args):
+    base, data = load(args.sandbox)
+    shutil.rmtree(base)
+    output({'status': 'SYNTHETIC_SANDBOX_REMOVED', 'sandbox': str(base)})
+
+
+def main():
+    parser = argparse.ArgumentParser(description='角色扮演回忆录本地试用')
+    parser.add_argument('command', choices=['init', 'play', 'exit-cosplay', 'accept', 'recall',
+                                            'forget', 'status', 'reset'])
+    parser.add_argument('--sandbox', help='系统临时目录下的试用实例路径')
+    parser.add_argument('--character', default='合成角色', help='合成的角色显示名')
+    parser.add_argument('--message', default='你还记得上次扮的那个人吗？')
+    parser.add_argument('--accept', action='store_true', help='退出时直接接受回忆录')
+    args = parser.parse_args()
+    if args.command != 'init' and not args.sandbox:
+        parser.error('此命令需要 --sandbox')
+    table = {'init': command_init, 'play': command_play, 'exit-cosplay': command_exit,
+             'accept': command_accept, 'recall': command_recall, 'forget': command_forget,
+             'status': command_status, 'reset': command_reset}
+    try:
+        table[args.command](args)
+    except (OSError, ValueError, KeyError) as exc:
+        parser.exit(1, f'{type(exc).__name__}: {exc}\n')
+
+
+if __name__ == '__main__':
+    main()
~~~~~~~~
