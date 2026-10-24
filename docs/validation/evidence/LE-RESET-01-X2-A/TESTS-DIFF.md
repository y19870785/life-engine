# C2 TESTS 完整相关差异

为避免Markdown空白检查歧义，diff中仅含一个ASCII空格的上下文行以可见符号 `␠` 表示；提取patch时将**整行** `␠` 还原为一个ASCII空格，其余字节不变。该符号不属于源码，台账hash对应还原后的patch。

审查证据，不在本PR安装或执行。Base `baa59729babf9ac56a17e02c682de2e3086e3575`。C2逐文件字节摘要见[证据台账](../../LE-RESET-01-X2-A-REVIEW-EVIDENCE.md)。

本附件含该组全部 24 文件差异；统一换行为LF并移除UTF-8 BOM后做unified diff；原始字节hash另存，因此不能把应用patch后的LF字节冒充原CRLF字节。所有新增文件模式为普通文件；不含真实密钥、Host配置或聊天。

## tests/fixtures/roleplay_recall_eval/v1.json

~~~~~~~~diff
--- /dev/null
+++ b/tests/fixtures/roleplay_recall_eval/v1.json
@@ -0,0 +1,59 @@
+{
+  "version": "RR-EVAL-01/v1",
+  "scope": "LOCAL_SYNTHETIC",
+  "time_origin": "2026-01-01T00:00:00+00:00",
+  "retrieval": {
+    "character": "合成领航员",
+    "batches": [
+      {"label": "harbor", "turns": [["user", "共同线索：我们在星港灯塔修好了导航仪。"], ["assistant", "星港灯塔的导航仪已经恢复。"]]},
+      {"label": "garden", "turns": [["user", "共同线索：我们种下月光花。"]]},
+      {"label": "library", "turns": [["user", "共同线索：我们整理旧图书馆。"]]},
+      {"label": "valley", "turns": [["user", "共同线索：我们穿过安静山谷。"]]},
+      {"label": "island", "turns": [["user", "共同线索：我们给海岛画地图。"]]},
+      {"label": "forest", "turns": [["user", "共同线索：我们在森林捡到红叶。"]]},
+      {"label": "river", "turns": [["user", "共同线索：我们修补河边木桥。"]]},
+      {"label": "snow", "turns": [["user", "共同线索：我们在雪原搭建营地。"]]}
+    ],
+    "queries": [
+      {"id": "exact", "query": "星港灯塔", "desired": ["harbor"], "reason": "明确关键词应找回旧批次，减少无关注入"},
+      {"id": "full_question", "query": "你还记得我们在星港灯塔修导航仪的那次经历吗？", "desired": ["harbor"], "reason": "完整问句应找回对应经历"},
+      {"id": "paraphrase", "query": "那回海边信标站的指路设备是怎么修好的？", "desired": ["harbor"], "reason": "同义表达期望命中，规则检索未必支持"},
+      {"id": "unrelated", "query": "请解释矩阵特征值的计算方法", "desired": [], "reason": "无关问题期望不注入扮演回忆"},
+      {"id": "empty_context", "query": "", "desired": ["snow", "river", "forest", "island", "valley", "library"], "reason": "空查询作为启动上下文，期望最近六批次"},
+      {"id": "unicode_whitespace", "query": "　星　港　灯　塔　", "desired": ["harbor"], "reason": "中文空白归一化后仍能找回明确词项"},
+      {"id": "whitespace_only", "query": "　 \t\n　", "desired": ["snow", "river", "forest", "island", "valley", "library"], "reason": "纯空白按无查询启动上下文观察"},
+      {"id": "long_question", "query": "你还记得我们在星港灯塔修导航仪吗？请详细回忆那一次经过，并说明我们先做什么后做什么，不要把别的扮演经历混到这段回忆里面。", "desired": ["harbor"], "reason": "超过四十字符的问句不应因截断丢失目标"},
+      {"id": "late_target", "query": "我想请你回忆我们此前一起做过的一件事情，这段话先交代背景并且没有提到任何具体地点，直到这里才问：星港灯塔发生过什么？", "desired": ["harbor"], "reason": "唯一目标词项位于前四十字符之外，截断不应令它丢失"},
+      {"id": "competition", "query": "共同线索", "desired": ["snow", "river", "forest", "island", "valley", "library"], "reason": "八个相关批次竞争默认六个位置，期望最近六个"}
+    ]
+  },
+  "summary": {
+    "character": "合成修理师",
+    "turns": [
+      ["user", "重要早事件：我们找回了失踪的蓝色航海日志。"],
+      ["assistant", "我把蓝色航海日志交还给你。"],
+      ["user", "随后检查码头的木箱。"],
+      ["assistant", "木箱里只有备用绳索。"],
+      ["user", "接着擦拭驾驶舱的窗户。"],
+      ["assistant", "驾驶舱的窗户擦干净了。"],
+      ["user", "最近用户动作：我递给你一张损坏的海图。"],
+      ["assistant", "最近助手结果：我修复海图并把成品交回给你。"]
+    ],
+    "desired_fragments": ["找回了失踪的蓝色航海日志", "我递给你一张损坏的海图", "我修复海图并把成品交回给你"],
+    "absent_fragment": "我们实际登上了火星"
+  },
+  "multi_character": [
+    {"key": "pilot", "name": "合成领航员", "label": "pilot_memory", "text": "领航员独有经历：绘制了北方星图。"},
+    {"key": "gardener", "name": "合成园丁", "label": "gardener_memory", "text": "园丁独有经历：培育了银色兰花。"}
+  ],
+  "boundaries": {
+    "candidate_text": "候选秘密：琥珀城的地下门。",
+    "forgotten_text": "遗忘秘密：琉璃山的钟楼。",
+    "retry_text": "重试经历：一起修复虚构的纸船。"
+  },
+  "metrics": {
+    "retrieval": ["target_coverage", "off_topic_count", "prompt_bytes"],
+    "summary": ["desired_fragment_retention", "source_and_fictional_boundary"],
+    "not_measured": ["自然度", "真实模型理解", "真实Host跨会话", "真实发送"]
+  }
+}
~~~~~~~~

## tests/test_hermes_memory_complete_scan.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_complete_scan.py
@@ -0,0 +1,102 @@
+"""Provider 完整扫描：完整轮次、末尾回忆与预算失败无副作用。"""
+import contextlib
+import io
+import json
+from pathlib import Path
+import sys
+import tempfile
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'runtime'))
+sys.path.insert(0, str(ROOT / 'integrations' / 'hermes_memory'))
+sys.path.insert(0, str(ROOT / 'tools'))
+from recall_service import RecallService  # noqa: E402
+import hermes_memory_flush as cli  # noqa: E402
+from life_engine.memory_repository import MemoryFailure as MC, MemoryRuntimeError  # noqa: E402
+
+
+class CompleteProviderScanTests(unittest.TestCase):
+    def setUp(self):
+        directory = tempfile.TemporaryDirectory(prefix='le-provider-complete-synthetic-')
+        self.addCleanup(directory.cleanup)
+        self.base = Path(directory.name)
+        self.profile = self.base / 'synthetic-profile'
+        self.profile.mkdir()
+        self.service = RecallService(ROOT / 'runtime', self.base / 'store', self.profile, '合成角色')
+        self.service.ensure()
+
+    def test_25_then_26_turns_and_more_than_100_are_all_flushed(self):
+        for index in range(25):
+            self.service.remember_turn('user', f'合成轮次{index:03d}')
+        self.service.flush_recall()
+        cursor = self.service.root / 'flush.json'
+        self.assertEqual(json.loads(cursor.read_text())['characters'][self.profile.name]['flushed'], 25)
+        self.assertIn('交互轮次：25', self.service.recall()[0].content)
+        self.service.remember_turn('user', '第26条新经历')
+        self.assertIsNotNone(self.service.flush_recall())
+        self.assertEqual(json.loads(cursor.read_text())['characters'][self.profile.name]['flushed'], 26)
+        for index in range(26, 102):
+            self.service.remember_turn('user', f'合成轮次{index:03d}')
+        self.assertIsNotNone(self.service.flush_recall())
+        self.assertEqual(json.loads(cursor.read_text())['characters'][self.profile.name]['flushed'], 102)
+        self.assertIsNone(self.service.flush_recall())
+        self.assertEqual(len(self.service.recall()), 3)
+
+    def test_recall_reads_record_after_first_20_and_100_random_ids(self):
+        from life_engine import roleplay_recall as recall
+        from life_engine.domain import CanonStatus
+        from life_engine.memory import IdempotencyIdentity, MemoryKind
+        for index in range(102):
+            source = recall.RecallSource(self.service._rp_owner.scope, character_name='合成角色',
+                                         ended_at=self.service.clock(), highlights=(f'唯一标记{index:03d}',))
+            self.service._memory.create_owner_memory(
+                self.service._soul_owner,
+                self.service._memory.collection_revision(self.service._soul_owner),
+                IdempotencyIdentity('complete-recall', str(index)),
+                content=recall.digest(source), kind=MemoryKind.SHARED_EXPERIENCE,
+                provenance=recall.build_provenance(source, self.service._actor, canon=CanonStatus.ACCEPTED),
+                audience=recall.recall_audience(self.service._soul_owner.scope.soul_id))
+        all_records = self.service._memory.scan_owner_memory(self.service._soul_owner).records
+        target = all_records[-1]
+        marker = next(line[2:] for line in target.content.splitlines() if line.startswith('- 唯一标记'))
+        self.assertNotIn(target.memory_id, {record.memory_id for record in self.service._memory.query(
+            self.service._soul_owner, limit=100).records})
+        self.assertEqual(self.service.recall(marker)[0].memory_id, target.memory_id)
+
+    def test_each_budget_failure_preserves_soul_and_cursor_and_cli_reports_error(self):
+        self.service.remember_turn('user', '第一批合成经历')
+        self.service.flush_recall()
+        self.service.remember_turn('user', '第二批合成经历')
+        cursor = self.service.root / 'flush.json'
+        old_cursor = cursor.read_bytes()
+        old_soul = self.service._memory.scan_owner_memory(self.service._soul_owner).records
+        original = self.service._memory.scan_owner_memory
+        for options in ({'max_rows': 1}, {'max_bytes': 1}, {'max_seconds': 1}):
+            def limited(context, **kwargs):
+                if 'max_seconds' in options:
+                    # 实际扫描入口在开始检查时已截止，不能写入部分摘要。
+                    from life_engine import memory_runtime
+                    with patch.object(memory_runtime.time, 'monotonic', side_effect=[0, 2]):
+                        return original(context, **kwargs, **options)
+                return original(context, **kwargs, **options)
+            with self.subTest(options=options), patch.object(self.service._memory, 'scan_owner_memory', limited):
+                with self.assertRaises(MemoryRuntimeError) as caught:
+                    self.service.flush_recall()
+                self.assertIs(caught.exception.code, MC.QUERY_INCOMPLETE)
+            self.assertEqual(cursor.read_bytes(), old_cursor)
+            self.assertEqual(original(self.service._soul_owner).records, old_soul)
+        output = io.StringIO()
+        with patch.object(cli, 'existing_service', return_value=self.service), patch.object(
+                self.service._memory, 'scan_owner_memory', side_effect=MemoryRuntimeError(MC.QUERY_INCOMPLETE)), contextlib.redirect_stdout(output):
+            code = cli.main(['--root', str(self.service.root), '--profile-home', str(self.profile), '--accept'])
+        self.assertEqual(code, 1)
+        self.assertEqual(json.loads(output.getvalue()), {'ok': False, 'failure_code': MC.QUERY_INCOMPLETE.value})
+        self.assertNotIn('NO_PENDING_TURNS', output.getvalue())
+        self.assertEqual(cursor.read_bytes(), old_cursor)
+        self.assertEqual(original(self.service._soul_owner).records, old_soul)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_flush.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_flush.py
@@ -0,0 +1,164 @@
+"""手动 flush 只操作临时合成 store，不接 Hermes、模型或渠道。"""
+import contextlib
+import io
+import json
+from pathlib import Path
+import sys
+import subprocess
+import tempfile
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'tools'))
+sys.path.insert(0, str(ROOT / 'integrations' / 'hermes_memory'))
+
+import hermes_memory_flush as cli  # noqa: E402
+from recall_service import RecallService  # noqa: E402
+
+
+class ManualFlushTests(unittest.TestCase):
+    def setUp(self):
+        directory = tempfile.TemporaryDirectory(prefix='lew-manual-flush-')
+        self.addCleanup(directory.cleanup)
+        self.base = Path(directory.name).resolve()
+        self.profile = self.base / 'character-one'
+        self.profile.mkdir()
+        self.store = self.base / 'store'
+
+    def service(self, profile=None):
+        service = RecallService(ROOT / 'runtime', self.store,
+                                profile or self.profile, '合成角色')
+        service.ensure()
+        return service
+
+    def run_cli(self, *extra, profile=None):
+        output = io.StringIO()
+        with contextlib.redirect_stdout(output):
+            code = cli.main(['--root', str(self.store), '--profile-home',
+                             str(profile or self.profile), *extra])
+        return code, json.loads(output.getvalue())
+
+    def test_accept_flushes_once_and_keeps_fictional_boundary(self):
+        service = self.service()
+        service.remember_turn('user', '一起找到了虚构世界里的旧书店')
+        self.assertEqual(service.recall(), [])
+        code, report = self.run_cli('--accept')
+        self.assertEqual(code, 0)
+        self.assertEqual(report['status'], 'FLUSHED')
+        record = self.service().recall()[0]
+        self.assertEqual(str(record.memory_id), report['memory_id'])
+        self.assertEqual(record.provenance.reality_status.value, 'fictional_shared_experience')
+        self.assertEqual(record.provenance.source_type.value, 'roleplay_recall')
+        self.assertIn('这是一次角色扮演经历，不是真实发生过的事实。', record.content)
+        code, report = self.run_cli('--accept')
+        self.assertEqual((code, report['status']), (0, 'NO_PENDING_TURNS'))
+        self.assertEqual(len(self.service().recall()), 1)
+
+    def test_default_candidate_is_not_recalled_or_upgraded_by_replay(self):
+        service = self.service()
+        service.remember_turn('assistant', '虚构角色的一段经历')
+        code, report = self.run_cli()
+        self.assertEqual((code, report['requested_canon_status']), (0, 'candidate'))
+        self.assertEqual(self.service().recall(), [])
+        code, report = self.run_cli('--accept')
+        self.assertEqual((code, report['status']), (0, 'NO_PENDING_TURNS'))
+        self.assertEqual(self.service().recall(), [])
+
+    def test_missing_store_is_not_bootstrapped(self):
+        code, report = self.run_cli('--accept')
+        self.assertEqual((code, report['failure_code']), (1, 'STORE_NOT_INITIALIZED'))
+        self.assertFalse(self.store.exists())
+
+    def test_unknown_profile_is_not_registered(self):
+        self.service()
+        before = (self.store / 'state.json').read_bytes()
+        unknown = self.base / 'unknown'
+        unknown.mkdir()
+        code, report = self.run_cli('--accept', profile=unknown)
+        self.assertEqual((code, report['failure_code']), (1, 'CHARACTER_NOT_REGISTERED'))
+        self.assertEqual((self.store / 'state.json').read_bytes(), before)
+
+    def test_legacy_state_is_not_migrated(self):
+        self.service()
+        path = self.store / 'state.json'
+        state = json.loads(path.read_text(encoding='utf-8'))
+        state.pop('version')
+        path.write_text(json.dumps(state), encoding='utf-8')
+        before = path.read_bytes()
+        code, report = self.run_cli()
+        self.assertEqual((code, report['failure_code']), (1, 'STORE_VERSION_UNSUPPORTED'))
+        self.assertEqual(path.read_bytes(), before)
+
+    def test_only_selected_character_pending_turns_are_flushed(self):
+        first = self.service()
+        first.remember_turn('user', '第一角色独有的山谷')
+        second_profile = self.base / 'character-two'
+        second_profile.mkdir()
+        second = self.service(second_profile)
+        second.remember_turn('user', '第二角色独有的海岛')
+        code, report = self.run_cli('--accept')
+        self.assertEqual((code, report['character_key']), (0, self.profile.name))
+        content = self.service().recall()[0].content
+        self.assertIn('山谷', content)
+        self.assertNotIn('海岛', content)
+        self.assertIsNotNone(self.service(second_profile).flush_recall())
+
+    def test_real_cli_process_outputs_receipt_without_conversation(self):
+        service = self.service()
+        service.remember_turn('user', 'PRIVATE_SYNTHETIC_TURN_DO_NOT_PRINT')
+        command = [sys.executable, '-X', 'utf8', '-B',
+                   str(ROOT / 'tools' / 'hermes_memory_flush.py'),
+                   '--root', str(self.store), '--profile-home', str(self.profile), '--accept']
+        process = subprocess.run(command, capture_output=True, text=True,
+                                 encoding='utf-8', timeout=30)
+        self.assertEqual(process.returncode, 0, process.stderr)
+        self.assertEqual(json.loads(process.stdout)['status'], 'FLUSHED')
+        self.assertNotIn('PRIVATE_SYNTHETIC', process.stdout + process.stderr)
+        self.assertEqual(len(self.service().recall()), 1)
+
+    def test_service_error_is_nonzero_without_raw_exception(self):
+        self.service()
+        with patch.object(RecallService, 'flush_recall',
+                          side_effect=RuntimeError('PRIVATE_BODY_AND_PATH')):
+            code, report = self.run_cli('--accept')
+        self.assertEqual((code, report['failure_code']), (1, 'FLUSH_FAILED'))
+        self.assertNotIn('PRIVATE', json.dumps(report))
+
+    def test_overlong_character_key_cannot_create_truncated_character(self):
+        self.service()
+        profile = self.base / ('x' * 65)
+        profile.mkdir()
+        path = self.store / 'state.json'
+        state = json.loads(path.read_text(encoding='utf-8'))
+        state['characters'][profile.name] = state['characters'][self.profile.name]
+        path.write_text(json.dumps(state), encoding='utf-8')
+        before = {p: p.read_bytes() for p in self.store.rglob('*') if p.is_file()}
+        code, report = self.run_cli(profile=profile)
+        self.assertEqual((code, report['failure_code']), (1, 'CHARACTER_KEY_INVALID'))
+        self.assertEqual({p: p.read_bytes() for p in self.store.rglob('*') if p.is_file()}, before)
+
+    def test_cursor_write_failure_retry_does_not_duplicate_committed_recall(self):
+        service = self.service()
+        service.remember_turn('user', '合成重试场景')
+        original = Path.write_text
+
+        def fail_cursor(path, *args, **kwargs):
+            if path == self.store / 'flush.json':
+                raise OSError('SYNTHETIC_CURSOR_WRITE_FAILURE')
+            return original(path, *args, **kwargs)
+
+        with patch.object(Path, 'write_text', fail_cursor):
+            code, report = self.run_cli('--accept')
+        self.assertEqual((code, report['failure_code']), (1, 'FLUSH_FAILED'))
+        committed = self.service().recall()
+        self.assertEqual(len(committed), 1)
+        code, report = self.run_cli('--accept')
+        self.assertEqual((code, report['status']), (0, 'FLUSHED'))
+        records = self.service().recall()
+        self.assertEqual(len(records), 1)
+        self.assertEqual(records[0].memory_id, committed[0].memory_id)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_flush_append.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_flush_append.py
@@ -0,0 +1,103 @@
+"""角色轮次按 Core 审计追加顺序汇总；历史编辑明确拒绝。"""
+import contextlib
+from datetime import datetime, timezone
+import io
+import json
+from pathlib import Path
+import sys
+import tempfile
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path[:0] = [str(ROOT / 'runtime'), str(ROOT / 'integrations' / 'hermes_memory'), str(ROOT / 'tools')]
+from recall_service import RecallService  # noqa: E402
+from life_engine.domain import DomainId, IdKind  # noqa: E402
+from life_engine.memory import IdempotencyIdentity  # noqa: E402
+from life_engine.memory_repository import MemoryFailure as MC, MemoryRuntimeError  # noqa: E402
+from life_engine import memory_runtime as runtime  # noqa: E402
+import hermes_memory_flush as cli  # noqa: E402
+
+
+class FlushAppendTests(unittest.TestCase):
+    def setUp(self):
+        directory = tempfile.TemporaryDirectory(prefix='le-append-synthetic-')
+        self.addCleanup(directory.cleanup)
+        self.base = Path(directory.name)
+        profile = self.base / 'profile'
+        profile.mkdir()
+        self.service = RecallService(ROOT / 'runtime', self.base / 'store', profile, '合成角色')
+        self.service.ensure()
+
+    def turn(self, text, identifier, year=2026):
+        original = DomainId.new
+        class FixedDate(datetime):
+            @classmethod
+            def now(cls, tz=None):
+                return datetime(year, 10, 22, tzinfo=timezone.utc)
+        with patch.object(runtime, 'datetime', FixedDate), patch.object(
+                DomainId, 'new', side_effect=lambda kind: DomainId.parse(identifier) if kind is IdKind.MEMORY else original(kind)):
+            return self.service.remember_turn('assistant', text)
+
+    def test_same_created_at_reverse_random_id_keeps_new_turn_and_retry(self):
+        self.turn('OLD_HIGH', 'memory:ffffffff-ffff-4fff-bfff-ffffffffffff')
+        self.service.flush_recall()
+        self.turn('NEW_LOW', 'memory:00000000-0000-4000-8000-000000000001')
+        self.assertIsNotNone(self.service.flush_recall())
+        contents = [r.content for r in self.service.recall()]
+        self.assertEqual(sum('OLD_HIGH' in c for c in contents), 1)
+        self.assertEqual(sum('NEW_LOW' in c for c in contents), 1)
+        self.assertIsNone(self.service.flush_recall())
+
+    def test_core_creation_clock_rollback_keeps_new_turn(self):
+        self.turn('FIRST_2026', 'memory:ffffffff-ffff-4fff-bfff-ffffffffffff', 2026)
+        self.service.flush_recall()
+        self.turn('LATER_CREATED_2025', 'memory:00000000-0000-4000-8000-000000000001', 2025)
+        self.service.flush_recall()
+        contents = [r.content for r in self.service.recall()]
+        self.assertEqual(sum('FIRST_2026' in c for c in contents), 1)
+        self.assertEqual(sum('LATER_CREATED_2025' in c for c in contents), 1)
+
+    def test_delete_then_append_explicit_failure_soul_cursor_unchanged(self):
+        first = self.service.remember_turn('user', '已处理后删除')
+        self.service.flush_recall()
+        self.service._memory.delete_memory(self.service._rp_owner, first.memory_id,
+                                           self.service._memory.collection_revision(self.service._rp_owner),
+                                           IdempotencyIdentity('append', 'delete'))
+        self.service.remember_turn('assistant', '新增轮不能被静默忽略')
+        path = self.service.root / 'flush.json'
+        raw = path.read_bytes()
+        records = self.service.recall()
+        revision = self.service._memory.collection_revision(self.service._soul_owner)
+        with self.assertRaises(MemoryRuntimeError) as caught:
+            self.service.flush_recall()
+        self.assertIs(caught.exception.code, MC.HISTORY_NOT_APPEND_ONLY)
+        self.assertEqual(path.read_bytes(), raw)
+        self.assertEqual(self.service.recall(), records)
+        self.assertEqual(self.service._memory.collection_revision(self.service._soul_owner), revision)
+        output = io.StringIO()
+        with patch.object(cli, 'existing_service', return_value=self.service), contextlib.redirect_stdout(output):
+            code = cli.main(['--root', str(self.service.root), '--profile-home', str(self.service.profile_home)])
+        self.assertEqual(code, 1)
+        self.assertEqual(json.loads(output.getvalue()), {'ok': False, 'failure_code': MC.HISTORY_NOT_APPEND_ONLY.value})
+
+    def test_append_budget_failure_cannot_flush_or_advance(self):
+        self.service.remember_turn('user', '第一批')
+        self.service.flush_recall()
+        self.service.remember_turn('assistant', '下一批')
+        path = self.service.root / 'flush.json'
+        raw = path.read_bytes()
+        before = self.service._memory.collection_revision(self.service._soul_owner)
+        original = self.service._memory.scan_owner_memory
+        def bounded(context, **options):
+            return original(context, max_rows=2, **options)
+        with patch.object(self.service._memory, 'scan_owner_memory', bounded):
+            with self.assertRaises(MemoryRuntimeError) as caught:
+                self.service.flush_recall()
+        self.assertIs(caught.exception.code, MC.QUERY_INCOMPLETE)
+        self.assertEqual(path.read_bytes(), raw)
+        self.assertEqual(self.service._memory.collection_revision(self.service._soul_owner), before)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_flush_arguments.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_flush_arguments.py
@@ -0,0 +1,169 @@
+"""手动汇总的参数拒绝不打开业务；所有实际数据均为临时合成 store。"""
+import contextlib
+import io
+import json
+from pathlib import Path
+import sqlite3
+import subprocess
+import sys
+import tempfile
+from types import SimpleNamespace
+import unittest
+from unittest.mock import Mock, patch
+
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'integrations/hermes_memory'), str(ROOT / 'runtime')]
+import hermes_memory_flush as cli  # noqa: E402
+from recall_service import RecallService  # noqa: E402
+from life_engine.memory_repository import MemoryFailure, MemoryRuntimeError  # noqa: E402
+
+PRIVATE = 'PRIVATE_ARGUMENT_BODY_AND_PATH'
+INVALID = {'ok': False, 'failure_code': 'ARGUMENT_INVALID'}
+LAYOUT_CODES = ('STORE_NOT_INITIALIZED', 'PROFILE_NOT_FOUND', 'CHARACTER_KEY_INVALID',
+                'STORE_STATE_INVALID', 'STORE_VERSION_UNSUPPORTED', 'CHARACTER_NOT_REGISTERED')
+
+
+class FlushArgumentTests(unittest.TestCase):
+    def invoke(self, args, *, error=None):
+        output, diagnostic = io.StringIO(), io.StringIO()
+        service = SimpleNamespace(character_key='synthetic', flush_recall=Mock(return_value=None))
+        with (patch.object(cli, 'existing_service', return_value=service, side_effect=error) as opened,
+              contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostic)):
+            code = cli.main(args)
+        self.assertEqual(diagnostic.getvalue(), '')
+        self.assertEqual(len(output.getvalue().splitlines()), 1)
+        self.assertNotIn(PRIVATE, output.getvalue())
+        return code, json.loads(output.getvalue()), opened, service
+
+    def test_parse_errors_are_single_safe_json_and_never_open_store(self):
+        for args in ([], ['--root', PRIVATE], ['--profile-home', PRIVATE],
+                     ['--root', PRIVATE, '--profile-home'],
+                     ['--root', 'r', '--profile-home', 'p', '--unknown=' + PRIVATE],
+                     ['--root', 'r', '--profile-home', 'p', PRIVATE],
+                     ['--roo', PRIVATE, '--profile-home', 'p'],
+                     ['--root', 'r', '--profile-h', PRIVATE],
+                     ['--root', 'r', '--profile-home', 'p', '--acc']):
+            with self.subTest(args=args):
+                code, report, opened, _ = self.invoke(args)
+                self.assertEqual((code, report), (1, INVALID))
+                opened.assert_not_called()
+
+    def test_empty_targets_rejected_before_path_expansion_or_open(self):
+        for target in ('--root', '--profile-home'):
+            for value in ('', ' ', '\t\n'):
+                args = ['--root', 'explicit-root', '--profile-home', 'explicit-profile']
+                args[args.index(target) + 1] = value
+                with self.subTest(target=target, value=repr(value)), \
+                        patch.object(cli, 'Path', side_effect=AssertionError(PRIVATE)):
+                    code, report, opened, _ = self.invoke(args)
+                    self.assertEqual((code, report), (1, INVALID))
+                    opened.assert_not_called()
+
+    def test_valid_explicit_relative_paths_and_accept_flag_preserve_behavior(self):
+        for root, profile, accept in (('.', './profile', False), ('store space', 'profile space', True)):
+            args = ['--root', root, '--profile-home', profile] + (['--accept'] if accept else [])
+            code, report, opened, service = self.invoke(args)
+            self.assertEqual((code, report['status']), (0, 'NO_PENDING_TURNS'))
+            opened.assert_called_once_with(Path(root), Path(profile))
+            service.flush_recall.assert_called_once_with(accept=accept)
+
+    def test_help_remains_static_and_zero_without_opening_store(self):
+        output, diagnostic = io.StringIO(), io.StringIO()
+        with (patch.object(cli, 'existing_service') as opened,
+              contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostic)):
+            with self.assertRaises(SystemExit) as stopped:
+                cli.main(['--help'])
+        self.assertEqual(stopped.exception.code, 0)
+        self.assertIn('--profile-home', output.getvalue())
+        self.assertEqual(diagnostic.getvalue(), '')
+        opened.assert_not_called()
+
+    def test_flush_error_only_exact_fixed_strings_are_public(self):
+        class StringSubclass(str):
+            pass
+        class Spoof:
+            def __eq__(self, other):
+                raise AssertionError(PRIVATE)
+            def __str__(self):
+                return PRIVATE
+        for value in (*LAYOUT_CODES, 'ARGUMENT_INVALID', PRIVATE, None, False, 1,
+                      ['STORE_NOT_INITIALIZED'], {'private': PRIVATE},
+                      StringSubclass('STORE_NOT_INITIALIZED'), Spoof()):
+            with self.subTest(kind=type(value).__name__, code=repr(value)):
+                code, report, _, _ = self.invoke(['--root', 'r', '--profile-home', 'p'],
+                                                error=cli.FlushError(value))
+                allowed = type(value) is str and value in (*LAYOUT_CODES, 'ARGUMENT_INVALID')
+                self.assertEqual((code, report), (1, {'ok': False, 'failure_code': value if allowed else 'FLUSH_FAILED'}))
+
+    def test_memory_failure_allowlist_remains_exact_enum(self):
+        for value in (MemoryFailure.QUERY_INCOMPLETE, MemoryFailure.HISTORY_NOT_APPEND_ONLY,
+                      MemoryFailure.IDEMPOTENCY_CONFLICT, MemoryFailure.INVALID_ARGUMENT):
+            code, report, _, _ = self.invoke(['--root', 'r', '--profile-home', 'p'],
+                                            error=MemoryRuntimeError(value))
+            self.assertEqual((code, report['failure_code']),
+                             (1, value.value if value is not MemoryFailure.INVALID_ARGUMENT else 'FLUSH_FAILED'))
+
+
+class FlushArgumentProcessTests(unittest.TestCase):
+    def setUp(self):
+        temporary = tempfile.TemporaryDirectory(prefix='le-flush-argument-')
+        self.addCleanup(temporary.cleanup)
+        self.base = Path(temporary.name)
+        self.store = self.base / 'synthetic store'
+        self.profile = self.base / 'synthetic profile'
+        self.profile.mkdir()
+        self.service = RecallService(ROOT / 'runtime', self.store, self.profile, '合成角色')
+        self.service.remember_turn('user', PRIVATE + ' 待处理虚构经历')
+
+    def snapshot(self):
+        with contextlib.closing(sqlite3.connect(self.service._memory.repository.path)) as db:
+            business = tuple(db.iterdump())
+        return {'business': business, 'state': (self.store / 'state.json').read_bytes(),
+                'cursor': (self.store / 'flush.json').read_bytes() if (self.store / 'flush.json').exists() else None}
+
+    def process(self, args, *, cwd=None):
+        return subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT / 'tools/hermes_memory_flush.py'), *args],
+                              cwd=cwd or self.base, capture_output=True, text=True, encoding='utf-8', timeout=30)
+
+    def test_actual_cwd_store_empty_root_and_bad_args_never_change_business(self):
+        for args in (['--root', '', '--profile-home', str(self.profile), '--accept'],
+                     ['--root', ' ', '--profile-home', str(self.profile), '--accept'],
+                     ['--root', str(self.store), '--profile-home', ''],
+                     ['--root', str(self.store), '--profile-home', '\t'],
+                     ['--root', str(self.store), '--profile-home', str(self.profile), '--unknown=' + PRIVATE],
+                     ['--root', str(self.store), '--profile-home', str(self.profile), '--acc'], []):
+            with self.subTest(args=args):
+                before = self.snapshot()
+                result = self.process(args, cwd=self.store)
+                self.assertEqual(self.snapshot(), before)
+                self.assertEqual(result.returncode, 1)
+                self.assertEqual(result.stderr, '')
+                self.assertEqual(len(result.stdout.splitlines()), 1)
+                self.assertEqual(json.loads(result.stdout), INVALID)
+                self.assertNotIn(PRIVATE, result.stdout + result.stderr)
+                self.assertNotIn(str(self.base), result.stdout + result.stderr)
+
+    def test_actual_absolute_candidate_then_relative_accept_keep_success_semantics(self):
+        result = self.process(['--root', str(self.store), '--profile-home', str(self.profile)])
+        self.assertEqual(result.returncode, 0, result.stderr)
+        report = json.loads(result.stdout)
+        self.assertEqual((report['status'], report['requested_canon_status']), ('FLUSHED', 'candidate'))
+        # CLI 重开已有 store 后，按既有恢复契约重开父进程服务，不复用旧句柄。
+        self.service = RecallService(ROOT / 'runtime', self.store, self.profile, '合成角色')
+        self.assertEqual(self.service.recall(), [])
+        self.service.remember_turn('assistant', '第二批相对路径虚构经历')
+        result = self.process(['--root', self.store.name, '--profile-home', self.profile.name, '--accept'])
+        self.assertEqual(result.returncode, 0, result.stderr)
+        self.assertEqual(json.loads(result.stdout)['requested_canon_status'], 'accepted')
+        self.service = RecallService(ROOT / 'runtime', self.store, self.profile, '合成角色')
+        records = self.service.recall()
+        self.assertEqual(len(records), 1)
+        self.assertIn('第二批相对路径', records[0].content)
+        result = self.process(['--root', '.', '--profile-home', str(self.profile), '--accept'], cwd=self.store)
+        self.assertEqual(result.returncode, 0, result.stderr)
+        self.assertEqual(json.loads(result.stdout)['status'], 'NO_PENDING_TURNS')
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_flush_cursor.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_flush_cursor.py
@@ -0,0 +1,173 @@
+"""损坏游标只在临时合成 store 复现；拒绝不能写 Soul 或改原始游标。"""
+import contextlib
+import io
+import json
+from pathlib import Path
+import sys
+import subprocess
+import tempfile
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'runtime'))
+sys.path.insert(0, str(ROOT / 'integrations' / 'hermes_memory'))
+sys.path.insert(0, str(ROOT / 'tools'))
+from recall_service import RecallCursorError, RecallService  # noqa: E402
+import hermes_memory_flush as cli  # noqa: E402
+
+
+class FlushCursorTests(unittest.TestCase):
+    @contextlib.contextmanager
+    def store(self):
+        with tempfile.TemporaryDirectory(prefix='le-cursor-synthetic-') as directory:
+            base = Path(directory)
+            profile = base / 'synthetic-profile'
+            profile.mkdir()
+            service = RecallService(ROOT / 'runtime', base / 'store', profile, '合成角色')
+            service.remember_turn('user', '第一批已登记的合成经历')
+            service.flush_recall()
+            service.remember_turn('assistant', '第二批待登记的合成经历')
+            yield service
+
+    def invalid_documents(self, key):
+        yield 'bad-json', b'{PRIVATE_SYNTHETIC'
+        yield 'bad-utf8', b'\xff'
+        for value in (None, [], 1, 'PRIVATE_SYNTHETIC', {},
+                      {'flushed': 1}, {'characters': None}, {'characters': []},
+                      {'characters': {key: None}}, {'characters': {key: []}},
+                      {'characters': {key: {}}}):
+            yield repr(value), json.dumps(value).encode('utf-8')
+        for value in (-1, True, False, '1', 1.0, None, 3, 10**80):
+            yield f'flushed={value!r}', json.dumps(
+                {'characters': {key: {'flushed': value}}}).encode('utf-8')
+
+    def snapshot(self, service):
+        result = service._memory.scan_owner_memory(service._soul_owner)
+        # query version 绑定 runtime generation；跨进程验证使用持久集合 revision。
+        return result.records, service._memory.collection_revision(service._soul_owner)
+
+    def test_invalid_cursor_service_rejects_without_any_write(self):
+        with self.store() as service:
+            path = service.root / 'flush.json'
+            before = self.snapshot(service)
+            for label, raw in self.invalid_documents(service.character_key):
+                with self.subTest(label=label):
+                    path.write_bytes(raw)
+                    with self.assertRaises(RecallCursorError) as raised:
+                        service.flush_recall()
+                    self.assertEqual(getattr(raised.exception, 'code', None), 'CURSOR_INVALID')
+                    self.assertEqual(path.read_bytes(), raw)
+                    self.assertEqual(self.snapshot(service), before)
+
+    def test_invalid_cursor_cli_is_explicit_and_private(self):
+        with self.store() as service:
+            path = service.root / 'flush.json'
+            before = self.snapshot(service)
+            for label, raw in self.invalid_documents(service.character_key):
+                with self.subTest(label=label):
+                    path.write_bytes(raw)
+                    output = io.StringIO()
+                    with patch.object(cli, 'existing_service', return_value=service), contextlib.redirect_stdout(output):
+                        code = cli.main(['--root', str(service.root), '--profile-home', str(service.profile_home)])
+                    self.assertEqual(code, 1)
+                    self.assertEqual(json.loads(output.getvalue()),
+                                     {'ok': False, 'failure_code': 'CURSOR_INVALID'})
+                    self.assertNotIn('PRIVATE_SYNTHETIC', output.getvalue())
+                    self.assertEqual(path.read_bytes(), raw)
+                    self.assertEqual(self.snapshot(service), before)
+
+    def test_missing_file_with_new_character_starts_normally(self):
+        with tempfile.TemporaryDirectory(prefix='le-new-cursor-synthetic-') as directory:
+            base = Path(directory)
+            service = RecallService(ROOT / 'runtime', base / 'store', base / 'profile', '新角色')
+            service.remember_turn('user', '首次经历')
+            self.assertFalse((service.root / 'flush.json').exists())
+            self.assertIsNotNone(service.flush_recall())
+            self.assertIsNone(service.flush_recall())
+
+    def test_empty_world_without_cursor_returns_none_without_file(self):
+        with tempfile.TemporaryDirectory(prefix='le-empty-cursor-synthetic-') as directory:
+            base = Path(directory)
+            service = RecallService(ROOT / 'runtime', base / 'store', base / 'profile', '新角色')
+            service.ensure()
+            self.assertIsNone(service.flush_recall())
+            self.assertFalse((service.root / 'flush.json').exists())
+
+    def test_real_cli_process_rejects_corruption_without_soul_or_cursor_write(self):
+        for raw in (b'\xff', b'{PRIVATE_SYNTHETIC',
+                    b'{"characters":{"synthetic-profile":{"flushed":3}}}'):
+            with self.subTest(raw=raw), self.store() as service:
+                path = service.root / 'flush.json'
+                path.write_bytes(raw)
+                before = self.snapshot(service)
+                process = subprocess.run(
+                    [sys.executable, '-X', 'utf8', '-B', str(ROOT / 'tools/hermes_memory_flush.py'),
+                     '--root', str(service.root), '--profile-home', str(service.profile_home), '--accept'],
+                    capture_output=True, text=True, encoding='utf-8', timeout=30)
+                self.assertEqual(process.returncode, 1, process.stderr)
+                self.assertEqual(json.loads(process.stdout), {'ok': False, 'failure_code': 'CURSOR_INVALID'})
+                self.assertEqual(process.stderr, '')
+                self.assertEqual(path.read_bytes(), raw)
+                reopened = RecallService(ROOT / 'runtime', service.root, service.profile_home, '合成角色')
+                reopened.ensure()
+                self.assertEqual(self.snapshot(reopened), before)
+
+    def test_missing_character_starts_and_preserves_other_entries(self):
+        with self.store() as service:
+            path = service.root / 'flush.json'
+            other = {'flushed': '未解释的其他角色字段', 'extra': [1, None]}
+            document = {'characters': {'other': other}, 'extra': {'preserve': True}}
+            path.write_text(json.dumps(document), encoding='utf-8')
+            # 此场景模拟新角色无游标；独立身份空间避免与旧登记身份重放冲突。
+            new = RecallService(ROOT / 'runtime', service.root, service.profile_home,
+                                '新角色', character_key='new-character')
+            new.remember_turn('user', '新角色首次经历')
+            self.assertIsNotNone(new.flush_recall())
+            after = json.loads(path.read_text(encoding='utf-8'))
+            self.assertEqual(after['characters']['other'], other)
+            self.assertEqual(after['extra'], document['extra'])
+            self.assertEqual(after['characters']['new-character']['flushed'], 1)
+
+    def test_exact_length_returns_none_and_preserves_bytes(self):
+        with self.store() as service:
+            path = service.root / 'flush.json'
+            raw = json.dumps({'characters': {service.character_key: {'flushed': 2}}}, indent=4).encode()
+            path.write_bytes(raw)
+            before = self.snapshot(service)
+            self.assertIsNone(service.flush_recall())
+            self.assertEqual(path.read_bytes(), raw)
+            self.assertEqual(self.snapshot(service), before)
+
+    def test_zero_is_valid_and_current_extra_fields_preserved(self):
+        with tempfile.TemporaryDirectory(prefix='le-zero-cursor-synthetic-') as directory:
+            base = Path(directory)
+            service = RecallService(ROOT / 'runtime', base / 'store', base / 'profile', '合成')
+            service.remember_turn('user', '首次经历')
+            path = service.root / 'flush.json'
+            path.write_text(json.dumps({'characters': {service.character_key: {'flushed': 0, 'extra': 7}}}), encoding='utf-8')
+            self.assertIsNotNone(service.flush_recall())
+            self.assertEqual(json.loads(path.read_text())['characters'][service.character_key],
+                             {'flushed': 1, 'extra': 7})
+
+    def test_cursor_read_io_failure_is_not_a_missing_file(self):
+        with self.store() as service:
+            path = service.root / 'flush.json'
+            raw = path.read_bytes()
+            before = self.snapshot(service)
+            original = Path.read_text
+
+            def fail_read(target, *args, **kwargs):
+                if target == path:
+                    raise PermissionError('PRIVATE_SYNTHETIC_IO')
+                return original(target, *args, **kwargs)
+
+            with patch.object(Path, 'read_text', fail_read):
+                with self.assertRaises(PermissionError):
+                    service.flush_recall()
+            self.assertEqual(path.read_bytes(), raw)
+            self.assertEqual(self.snapshot(service), before)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_flush_errors.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_flush_errors.py
@@ -0,0 +1,146 @@
+"""手动 flush 只公开固定冲突码；真实 CLI 重开合成 store 验证业务数据不变。"""
+import contextlib
+import io
+import json
+from pathlib import Path
+import sqlite3
+import subprocess
+import sys
+import tempfile
+from types import SimpleNamespace
+import unittest
+from unittest.mock import Mock, patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path[:0] = [str(ROOT / 'runtime'), str(ROOT / 'integrations' / 'hermes_memory'), str(ROOT / 'tools')]
+import hermes_memory_flush as cli  # noqa: E402
+import recall_service as service_module  # noqa: E402
+from life_engine.memory_repository import MemoryFailure as MC, MemoryRuntimeError  # noqa: E402
+from life_engine.world_repository import FailureCode, WorldRuntimeError  # noqa: E402
+
+PRIVATE = 'PRIVATE_SYNTHETIC_BODY_AND_PATH_DO_NOT_PRINT'
+
+
+class FlushFailureMappingTests(unittest.TestCase):
+    def invoke(self, error):
+        error.args = (PRIVATE,)
+        service = SimpleNamespace(flush_recall=Mock(side_effect=error))
+        output, diagnostic = io.StringIO(), io.StringIO()
+        with (patch.object(cli, 'existing_service', return_value=service),
+              contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostic)):
+            code = cli.main(['--root', '/synthetic-unused', '--profile-home', '/synthetic-unused-profile'])
+        self.assertEqual(code, 1)
+        self.assertEqual(diagnostic.getvalue(), '')
+        self.assertNotIn(PRIVATE, output.getvalue())
+        report = json.loads(output.getvalue())
+        self.assertEqual(set(report), {'ok', 'failure_code'})
+        self.assertIs(report['ok'], False)
+        return report['failure_code']
+
+    def test_only_three_exact_memory_enum_values_are_public(self):
+        allowed = {MC.QUERY_INCOMPLETE, MC.HISTORY_NOT_APPEND_ONLY, MC.IDEMPOTENCY_CONFLICT}
+        for code in MC:
+            with self.subTest(code=code):
+                self.assertEqual(self.invoke(MemoryRuntimeError(code)), code.value if code in allowed else 'FLUSH_FAILED')
+
+    def test_polluted_or_missing_codes_cannot_serialize_arbitrary_value(self):
+        class Spoof:
+            value = PRIVATE
+            def __eq__(self, other):
+                return True
+        class Explosive:
+            @property
+            def value(self):
+                raise AssertionError(PRIVATE)
+            def __eq__(self, other):
+                raise AssertionError(PRIVATE)
+        for code in (None, True, 'MemoryQueryIncomplete', 'MemoryIdempotencyConflict',
+                     SimpleNamespace(value=PRIVATE), Spoof(), Explosive()):
+            with self.subTest(kind=type(code).__name__):
+                error = MemoryRuntimeError(MC.INVALID_ARGUMENT)
+                error.code = code
+                self.assertEqual(self.invoke(error), 'FLUSH_FAILED')
+        error = MemoryRuntimeError(MC.INVALID_ARGUMENT)
+        del error.code
+        self.assertEqual(self.invoke(error), 'FLUSH_FAILED')
+
+    def test_world_io_and_unknown_failures_remain_generic_without_detail(self):
+        for error in (WorldRuntimeError(FailureCode.STORAGE_CORRUPT), OSError(PRIVATE), RuntimeError(PRIVATE)):
+            with self.subTest(kind=type(error).__name__):
+                self.assertEqual(self.invoke(error), 'FLUSH_FAILED')
+
+
+class FlushConflictProcessTests(unittest.TestCase):
+    def setUp(self):
+        directory = tempfile.TemporaryDirectory(prefix='le-flush-error-synthetic-')
+        self.addCleanup(directory.cleanup)
+        self.base = Path(directory.name)
+        self.profile = self.base / 'synthetic-profile'
+        self.profile.mkdir()
+        self.service = service_module.RecallService(ROOT / 'runtime', self.base / 'store', self.profile, '合成角色')
+        self.service.remember_turn('user', '已完成的首批')
+        self.service.flush_recall()
+        self.original_cursor = (self.service.root / 'flush.json').read_bytes()
+        for index in range(20):
+            self.service.remember_turn('user' if index % 2 == 0 else 'assistant', f'{PRIVATE} 待处理原文{index:03d}')
+
+    def snapshot(self):
+        scope = self.service._soul_owner.scope
+        values = [str(getattr(scope, field + '_id')) for field in ('owner', 'soul', 'world', 'timeline')]
+        where = ' AND '.join('m.' + field + '=?' for field in ('owner_id', 'soul_id', 'world_id', 'timeline_id'))
+        with contextlib.closing(sqlite3.connect(self.service._memory.repository.path)) as db:
+            result = {'records': tuple(db.execute('SELECT m.* FROM world_memories m WHERE ' + where + ' ORDER BY memory_id', values)),
+                      'revision': tuple(db.execute('SELECT m.* FROM memory_collection_state m WHERE ' + where, values)),
+                      'operations': tuple(db.execute('SELECT * FROM memory_operations ORDER BY sequence'))}
+            for table in ('memory_audiences', 'memory_subjects', 'memory_lineage'):
+                result[table] = tuple(db.execute(f'SELECT a.* FROM {table} a JOIN world_memories m ON m.memory_id=a.memory_id WHERE ' + where + ' ORDER BY a.memory_id,2', values))
+        result['state'] = (self.service.root / 'state.json').read_bytes()
+        result['cursor'] = (self.service.root / 'flush.json').read_bytes()
+        return result
+
+    def commit_without_cursor(self, *, old_strategy):
+        original = Path.write_text
+        def fail_cursor(path, *args, **kwargs):
+            if path == self.service.root / 'flush.json':
+                raise OSError(PRIVATE)
+            return original(path, *args, **kwargs)
+        old = lambda records: tuple(service_module._excerpt(record.content) for record in records[-6:])
+        strategy = patch.object(service_module, '_select_highlights', old) if old_strategy else contextlib.nullcontext()
+        with strategy, patch.object(Path, 'write_text', fail_cursor):
+            with self.assertRaises(OSError):
+                self.service.flush_recall()
+        self.assertEqual((self.service.root / 'flush.json').read_bytes(), self.original_cursor)
+
+    def process(self):
+        result = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(ROOT / 'tools/hermes_memory_flush.py'),
+                                 '--root', str(self.service.root), '--profile-home', str(self.profile), '--accept'],
+                                capture_output=True, text=True, encoding='utf-8', timeout=30)
+        self.assertEqual(result.stderr, '')
+        self.assertNotIn(PRIVATE, result.stdout + result.stderr)
+        self.assertNotIn(str(self.base), result.stdout + result.stderr)
+        return result.returncode, json.loads(result.stdout)
+
+    def test_old_strategy_committed_with_existing_cursor_reports_conflict_without_business_writes(self):
+        self.commit_without_cursor(old_strategy=True)
+        before = self.snapshot()
+        code, report = self.process()
+        self.assertEqual((code, report), (1, {'ok': False, 'failure_code': 'MemoryIdempotencyConflict'}))
+        self.assertEqual(self.snapshot(), before)
+
+    def test_same_strategy_real_process_retry_reuses_record_and_advances_existing_cursor(self):
+        self.commit_without_cursor(old_strategy=False)
+        before = self.snapshot()
+        code, report = self.process()
+        self.assertEqual((code, report['status']), (0, 'FLUSHED'))
+        after = self.snapshot()
+        self.assertEqual({key: value for key, value in after.items() if key != 'cursor'},
+                         {key: value for key, value in before.items() if key != 'cursor'})
+        self.assertIn(report['memory_id'], {row[0] for row in before['records']})
+        self.assertEqual(json.loads(after['cursor'])['characters'][self.profile.name]['flushed'], 21)
+        code, report = self.process()
+        self.assertEqual((code, report['status']), (0, 'NO_PENDING_TURNS'))
+        self.assertEqual(self.snapshot(), after)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_install.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_install.py
@@ -0,0 +1,100 @@
+"""记忆 provider 安装器：冻结、配置追加、幂等与留痕。"""
+import contextlib
+import io
+import json
+import sys
+import tempfile
+import unittest
+import unittest.mock
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'runtime'))
+sys.path.insert(0, str(ROOT / 'tools'))
+
+import hermes_memory_install as installer  # noqa: E402
+
+CONFIG = 'model:\n  provider: deepseek\n  default: deepseek-v4-flash\n'
+
+
+class InstallerTests(unittest.TestCase):
+    def setUp(self):
+        directory = tempfile.TemporaryDirectory(prefix='lew-mem-install-')
+        self.addCleanup(directory.cleanup)
+        base = Path(directory.name).resolve()
+        self.profile = base / 'profile'
+        self.profile.mkdir()
+        self.config = self.profile / 'config.yaml'
+        self.config.write_text(CONFIG, encoding='utf-8')
+        self.root = base / 'store'
+
+    def run_tool(self, *extra):
+        argv = ['hermes_memory_install.py',
+                '--profile-home', str(self.profile),
+                '--character-name', '测试角色',
+                '--runtime', str(ROOT / 'runtime'),
+                '--root', str(self.root), *extra]
+        out = io.StringIO()
+        with contextlib.redirect_stdout(out), \
+                unittest.mock.patch.object(sys, 'argv', argv):
+            code = installer.main()
+        return code, out.getvalue()
+
+    def test_dry_run_changes_nothing(self):
+        code, out = self.run_tool('--dry-run')
+        self.assertEqual(code, 0)
+        plan = json.loads(out)
+        self.assertTrue(plan['dry_run'])
+        self.assertFalse(plan['config_already_has_memory'])
+        self.assertEqual(self.config.read_text(encoding='utf-8'), CONFIG)
+        self.assertFalse((self.profile / 'plugins' / 'life_engine').exists())
+
+    def test_install_appends_memory_and_backs_up_config(self):
+        code, out = self.run_tool('--skip-verify')
+        self.assertEqual(code, 0)
+        report = json.loads(out)
+        self.assertIn('memory:', self.config.read_text(encoding='utf-8'))
+        self.assertIn('provider: life_engine', self.config.read_text(encoding='utf-8'))
+        backup = Path(report['config_backup'])
+        self.assertTrue(backup.is_file())
+        self.assertEqual(backup.read_text(encoding='utf-8'), CONFIG)
+        plugin = self.profile / 'plugins' / 'life_engine'
+        self.assertTrue((plugin / 'recall_service.py').is_file())
+        self.assertTrue((plugin / 'settings.json').is_file())
+        installed = json.loads((plugin / 'installed.json').read_text(encoding='utf-8'))
+        self.assertEqual(installed['character_name'], '测试角色')
+        settings = json.loads((plugin / 'settings.json').read_text(encoding='utf-8'))
+        self.assertEqual(settings['profile_home'], str(self.profile),
+                         '必须写入 profile_home，provider 不能靠环境变量猜')
+
+    def test_second_run_does_not_duplicate_memory_block(self):
+        self.run_tool('--skip-verify')
+        after_first = self.config.read_text(encoding='utf-8')
+        code, out = self.run_tool('--skip-verify')
+        self.assertEqual(code, 0)
+        self.assertTrue(json.loads(out)['config_already_has_memory'])
+        self.assertEqual(self.config.read_text(encoding='utf-8'), after_first)
+
+    def test_provider_is_frozen_by_content_hash(self):
+        code, out = self.run_tool('--skip-verify')
+        self.assertEqual(code, 0)
+        report = json.loads(out)
+        frozen = Path(report['freeze_to'])
+        self.assertTrue(frozen.is_dir())
+        self.assertEqual(frozen.name, report['provider_source_sha256'][:8])
+        self.assertEqual(installer.digest(frozen), installer.digest(installer.source_dir()))
+
+    def test_missing_profile_fails_cleanly(self):
+        argv = ['hermes_memory_install.py', '--profile-home', str(self.profile / 'nope'),
+                '--character-name', 'x', '--runtime', str(ROOT / 'runtime'),
+                '--root', str(self.root)]
+        out = io.StringIO()
+        with contextlib.redirect_stdout(out), \
+                unittest.mock.patch.object(sys, 'argv', argv):
+            code = installer.main()
+        self.assertEqual(code, 1)
+        self.assertIn('PROFILE_NOT_FOUND', out.getvalue())
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_install_arguments.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_install_arguments.py
@@ -0,0 +1,154 @@
+"""安装器参数测试只使用临时合成目录，不访问默认 Home 或真实 Host。"""
+import contextlib
+import io
+import json
+from pathlib import Path
+import subprocess
+import sys
+import tempfile
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'tools'))
+import hermes_memory_install as installer  # noqa: E402
+
+PRIVATE = 'PRIVATE_INSTALL_ARGUMENT_AND_BODY'
+INVALID = {'status': 'FAILED', 'error': 'ARGUMENT_INVALID'}
+
+
+class InstallArgumentTests(unittest.TestCase):
+    def setUp(self):
+        temporary = tempfile.TemporaryDirectory(prefix='le-install-argument-')
+        self.addCleanup(temporary.cleanup)
+        self.base = Path(temporary.name)
+        self.profile = self.base / 'profile space'
+        self.profile.mkdir()
+        (self.profile / 'config.yaml').write_text('model: synthetic\n', encoding='utf-8')
+        self.runtime = self.base / 'runtime space'
+        self.runtime.mkdir()
+        self.store = self.base / 'store space'
+
+    def args(self):
+        return ['--root', str(self.store), '--runtime', str(self.runtime),
+                '--profile-home', str(self.profile), '--character-name', '合成角色', '--skip-verify']
+
+    def main(self, args):
+        out, err = io.StringIO(), io.StringIO()
+        with patch.object(sys, 'argv', ['installer', *args]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
+            code = installer.main()
+        self.assertEqual(err.getvalue(), '')
+        return code, out.getvalue()
+
+    def tree(self):
+        return {str(p.relative_to(self.base)): p.read_bytes() if p.is_file() else None
+                for p in self.base.rglob('*')}
+
+    def test_empty_or_blank_targets_and_parser_errors_do_not_access_business(self):
+        requests = []
+        for key in ('--root', '--runtime', '--profile-home'):
+            for value in ('', ' ', '\t\n'):
+                args = self.args()
+                args[args.index(key) + 1] = value
+                requests.append(args)
+        requests.extend(([], ['--profile-home', PRIVATE],
+                         ['--character-name', PRIVATE], ['--profile-home'],
+                         [*self.args(), '--unknown=' + PRIVATE], [*self.args(), PRIVATE],
+                         ['--profile-h', PRIVATE, '--character-name', 'x'],
+                         [*self.args(), '--dry'], [*self.args(), '--skip-v']))
+        for args in requests:
+            with self.subTest(args=args), contextlib.ExitStack() as stack:
+                spies = [stack.enter_context(patch.object(installer, name, side_effect=AssertionError(PRIVATE)))
+                         for name in ('Path', 'source_dir', 'digest', 'freeze', 'verify')]
+                code, raw = self.main(args)
+                self.assertEqual((code, json.loads(raw)), (1, INVALID))
+                self.assertEqual(len(raw.splitlines()), 1)
+                self.assertNotIn(PRIVATE, raw)
+                for spy in spies:
+                    spy.assert_not_called()
+
+    def test_help_obeys_argparse_action_order_and_opens_nothing(self):
+        for args in (['--help'], ['--help', '--profile-home']):
+            out, err = io.StringIO(), io.StringIO()
+            with (patch.object(sys, 'argv', ['installer', *args]),
+                  patch.object(installer, 'Path') as paths,
+                  patch.object(installer, 'source_dir') as source,
+                  contextlib.redirect_stdout(out), contextlib.redirect_stderr(err)):
+                with self.assertRaises(SystemExit) as stopped:
+                    installer.main()
+            self.assertEqual(stopped.exception.code, 0)
+            self.assertIn('--profile-home', out.getvalue())
+            self.assertEqual(err.getvalue(), '')
+            paths.assert_not_called()
+            source.assert_not_called()
+        code, raw = self.main(['--profile-home', '--help'])
+        self.assertEqual((code, json.loads(raw)), (1, INVALID))
+
+    def test_omitted_root_and_runtime_use_explicitly_patched_temporary_defaults(self):
+        with (patch.object(installer, 'DEFAULT_ROOT', str(self.store)),
+              patch.object(installer, 'DEFAULT_RUNTIME', str(self.runtime)),
+              patch.object(installer, 'verify', return_value={'available': True}) as verified):
+            code, raw = self.main(['--profile-home', str(self.profile), '--character-name', '合成角色'])
+        self.assertEqual(code, 0)
+        self.assertEqual(json.loads(raw)['profile'], str(self.profile))
+        verified.assert_called_once_with(str(self.runtime), self.store, self.profile, '合成角色')
+        settings = json.loads((self.profile / 'plugins/life_engine/settings.json').read_text(encoding='utf-8'))
+        self.assertEqual(settings['root'], str(self.store))
+        self.assertEqual(settings['runtime_path'], str(self.runtime))
+
+    def test_nonempty_surrounding_space_is_not_trimmed_by_guard(self):
+        args = self.args()
+        args[args.index('--profile-home') + 1] = ' profile with outer spaces '
+        with patch.object(installer, 'Path', side_effect=RuntimeError('synthetic stop')) as paths:
+            with self.assertRaises(RuntimeError):
+                self.main(args)
+        paths.assert_called_once_with(' profile with outer spaces ')
+
+    def process(self, args):
+        return subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT / 'tools/hermes_memory_install.py'), *args],
+                              cwd=self.base, capture_output=True, text=True, encoding='utf-8', timeout=30)
+
+    def test_actual_cli_invalid_paths_keep_cwd_profile_cache_and_backups_unchanged(self):
+        # 诱饵cwd同时是合法Profile与runtime目录，仍须先拒绝显式空目标。
+        (self.base / 'config.yaml').write_text('model: bait\n', encoding='utf-8')
+        for key in ('--root', '--runtime', '--profile-home'):
+            for value in ('', ' \t'):
+                args = ['--root', str(self.store), '--runtime', str(self.base),
+                        '--profile-home', str(self.base), '--character-name', '合成角色', '--skip-verify']
+                args[args.index(key) + 1] = value
+                with self.subTest(key=key, value=repr(value)):
+                    before = self.tree()
+                    result = self.process(args)
+                    self.assertEqual(self.tree(), before)
+                    self.assertEqual(result.returncode, 1)
+                    self.assertEqual(result.stderr, '')
+                    self.assertEqual(json.loads(result.stdout), INVALID)
+                    self.assertEqual(len(result.stdout.splitlines()), 1)
+                    self.assertNotIn(str(self.base), result.stdout)
+        for args in ([], [*self.args(), '--unknown=' + PRIVATE], [*self.args(), '--runt', PRIVATE]):
+            result = self.process(args)
+            self.assertEqual(result.returncode, 1)
+            self.assertEqual(result.stderr, '')
+            self.assertEqual(json.loads(result.stdout), INVALID)
+            self.assertNotIn(PRIVATE, result.stdout)
+
+    def test_actual_absolute_relative_and_dot_paths_install_and_dry_run_stays_clean(self):
+        before = self.tree()
+        result = self.process([*self.args(), '--dry-run'])
+        self.assertEqual(result.returncode, 0, result.stderr)
+        self.assertTrue(json.loads(result.stdout)['dry_run'])
+        self.assertEqual(self.tree(), before)
+        result = self.process(self.args())
+        self.assertEqual(result.returncode, 0, result.stderr)
+        args = ['--root', self.store.name, '--runtime', '.', '--profile-home', self.profile.name,
+                '--character-name', '', '--skip-verify']
+        result = self.process(args)
+        self.assertEqual(result.returncode, 0, result.stderr)
+        settings = json.loads((self.profile / 'plugins/life_engine/settings.json').read_text(encoding='utf-8'))
+        self.assertEqual(settings['runtime_path'], '.')
+        self.assertEqual(settings['character_name'], '')
+        self.assertEqual(len(list(self.profile.glob('config.yaml.bak-*'))), 1)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_install_cache.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_install_cache.py
@@ -0,0 +1,272 @@
+"""冻结缓存仅在临时三文件源/配置上验收，不接真实 Host。"""
+import contextlib
+import io
+import json
+from pathlib import Path
+import shutil
+import stat
+import sys
+import tempfile
+from types import SimpleNamespace
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'tools'))
+import hermes_memory_install as installer  # noqa: E402
+
+
+class InstallCacheTests(unittest.TestCase):
+    def setUp(self):
+        temporary = tempfile.TemporaryDirectory(prefix='le-cache-synthetic-')
+        self.addCleanup(temporary.cleanup)
+        self.base = Path(temporary.name)
+        self.source = self.base / 'source'
+        self.source.mkdir()
+        for name in installer.FILES:
+            (self.source / name).write_text('synthetic ' + name, encoding='utf-8')
+        self.root = self.base / 'store'
+        self.expected = installer.digest(self.source)
+        self.target = self.root / 'provider' / self.expected[:8]
+        self.profile = self.base / 'profile'
+        self.profile.mkdir()
+        (self.profile / 'config.yaml').write_text('model: synthetic\n', encoding='utf-8')
+        self.runtime = self.base / 'runtime'
+        self.runtime.mkdir()
+
+    def tree(self, path):
+        if not path.exists():
+            return None
+        return {str(p.relative_to(path)): p.read_bytes() if p.is_file() else None
+                for p in path.rglob('*')}
+
+    def main(self, *extra):
+        out, err = io.StringIO(), io.StringIO()
+        args = ['installer', '--root', str(self.root), '--profile-home', str(self.profile),
+                '--runtime', str(self.runtime), '--character-name', '合成角色', '--skip-verify', *extra]
+        with (patch.object(installer, 'source_dir', return_value=self.source),
+              patch.object(sys, 'argv', args), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err)):
+            code = installer.main()
+        self.assertEqual(err.getvalue(), '')
+        return code, json.loads(out.getvalue())
+
+    def assert_rejected(self):
+        before = self.tree(self.profile), self.tree(self.root)
+        code, report = self.main()
+        self.assertEqual((code, report), (1, {'status': 'FAILED', 'error': 'PROVIDER_CACHE_INVALID'}))
+        self.assertEqual((self.tree(self.profile), self.tree(self.root)), before)
+        self.assertNotIn(str(self.base), json.dumps(report))
+
+    def test_correct_cache_reuse_and_repeat_install_keep_complete_digest(self):
+        first, version = installer.freeze(self.source, self.root)
+        before = self.tree(first)
+        self.assertEqual(installer.freeze(self.source, self.root), (first, version))
+        self.assertEqual(self.tree(first), before)
+        self.assertEqual(installer.digest(first), self.expected)
+        self.assertEqual(version, self.expected[:8])
+        self.assertEqual(self.main()[0], 0)
+        self.assertEqual(self.main()[0], 0)
+        destination = self.profile / 'plugins/life_engine'
+        self.assertEqual(installer.digest(destination), self.expected)
+        self.assertEqual(len(list(self.profile.glob('config.yaml.bak-*'))), 1)
+
+    def test_mutated_missing_and_wrong_type_cache_reject_before_profile_writes(self):
+        installer.freeze(self.source, self.root)
+        file = self.target / installer.FILES[0]
+        for fault in ('changed', 'missing', 'directory'):
+            with self.subTest(fault=fault):
+                if fault == 'changed':
+                    file.write_bytes(b'PRIVATE_CACHE_BODY')
+                elif fault == 'missing':
+                    file.unlink()
+                else:
+                    file.unlink()
+                    file.mkdir()
+                self.assert_rejected()
+                if file.is_dir():
+                    file.rmdir()
+                shutil.copy2(self.source / file.name, file)
+
+    def test_wrong_type_branch_and_target_are_preserved(self):
+        self.root.mkdir()
+        branch = self.root / 'provider'
+        branch.write_bytes(b'branch sentinel')
+        self.assert_rejected()
+        branch.unlink()
+        branch.mkdir()
+        self.target.write_bytes(b'target sentinel')
+        self.assert_rejected()
+
+    def test_same_hash8_prefix_requires_full_digest_and_unreadable_cache_rejects(self):
+        installer.freeze(self.source, self.root)
+        original = installer.digest
+        with patch.object(installer, 'digest', side_effect=lambda p: self.expected[:8] + 'f' * 56 if p == self.target else original(p)):
+            self.assert_rejected()
+        read = Path.read_bytes
+        def unreadable(path):
+            if path == self.target / installer.FILES[0]:
+                raise PermissionError('PRIVATE_IO_PATH')
+            return read(path)
+        # 快照在注入外获取，避免测试本身读不可读替身。
+        before = self.tree(self.profile), self.tree(self.root)
+        with patch.object(Path, 'read_bytes', unreadable):
+            code, report = self.main()
+        self.assertEqual((code, report), (1, {'status': 'FAILED', 'error': 'PROVIDER_CACHE_INVALID'}))
+        self.assertEqual((self.tree(self.profile), self.tree(self.root)), before)
+
+    def test_stage_copy_failure_and_source_drift_never_claim_target(self):
+        original = shutil.copy2
+        def fail_copy(src, dst, *args, **kwargs):
+            original(src, dst, *args, **kwargs)
+            raise OSError('PRIVATE_COPY_PATH')
+        with patch.object(shutil, 'copy2', fail_copy):
+            code, report = self.main()
+        self.assertEqual((code, report['error']), (1, 'PROVIDER_CACHE_INVALID'))
+        self.assertFalse(self.target.exists())
+        def drift_copy(src, dst, *args, **kwargs):
+            result = original(src, dst, *args, **kwargs)
+            Path(dst).write_bytes(b'drift')
+            return result
+        with patch.object(shutil, 'copy2', drift_copy):
+            code, report = self.main()
+        self.assertEqual((code, report['error']), (1, 'PROVIDER_CACHE_INVALID'))
+        self.assertFalse(self.target.exists())
+        self.assertFalse((self.profile / 'plugins').exists())
+
+    def test_target_claim_conflict_never_overwrites_existing_empty_directory(self):
+        original = Path.mkdir
+        raced = []
+        def mkdir(path, *args, **kwargs):
+            if path == self.target and not raced:
+                raced.append(True)
+                original(path)
+            return original(path, *args, **kwargs)
+        with patch.object(Path, 'mkdir', mkdir):
+            code, report = self.main()
+        self.assertEqual((code, report['error']), (1, 'PROVIDER_CACHE_INVALID'))
+        self.assertTrue(self.target.is_dir())
+        self.assertEqual(list(self.target.iterdir()), [])
+        self.assert_rejected()
+
+    def test_exclusive_file_conflict_partial_failure_and_complete_residual(self):
+        original = Path.open
+        conflict = self.target / installer.FILES[0]
+        def opened(path, mode='r', *args, **kwargs):
+            if path == conflict and mode == 'xb':
+                with original(path, 'wb') as stream:
+                    stream.write(b'competing sentinel')
+            return original(path, mode, *args, **kwargs)
+        with patch.object(Path, 'open', opened):
+            code, report = self.main()
+        self.assertEqual((code, report['error']), (1, 'PROVIDER_CACHE_INVALID'))
+        self.assertEqual(conflict.read_bytes(), b'competing sentinel')
+        self.assert_rejected()
+        # 合成完整残留，不通过freeze修补失败目录；测试夹具手动提供完整内容。
+        for name in installer.FILES:
+            shutil.copy2(self.source / name, self.target / name)
+        self.assertEqual(installer.freeze(self.source, self.root)[0], self.target)
+
+    def test_stage_cleanup_identity_change_retains_replacement_and_original(self):
+        created = []
+        original_stage = tempfile.mkdtemp
+        def mkdtemp(*args, **kwargs):
+            path = original_stage(*args, **kwargs)
+            created.append(Path(path))
+            return path
+        def replace_stage(src, dst, *args, **kwargs):
+            stage = Path(dst).parent
+            stage.rename(stage.with_name(stage.name + '-original'))
+            stage.mkdir()
+            (stage / 'sentinel').write_bytes(b'not owned')
+            raise OSError('PRIVATE_COPY')
+        with patch.object(tempfile, 'mkdtemp', mkdtemp), patch.object(shutil, 'copy2', replace_stage):
+            code, report = self.main()
+        self.assertEqual((code, report['error']), (1, 'PROVIDER_CACHE_INVALID'))
+        self.assertEqual(len(created), 1)
+        self.assertEqual((created[0] / 'sentinel').read_bytes(), b'not owned')
+        self.assertTrue(created[0].with_name(created[0].name + '-original').is_dir())
+        self.assertFalse(self.target.exists())
+
+    def test_final_digest_failure_keeps_partial_target_and_cleanup_failure_does_not_mask(self):
+        original = shutil.copyfileobj
+        def corrupted(source, destination, *args, **kwargs):
+            original(source, destination, *args, **kwargs)
+            destination.write(b'corrupt after copy')
+        with patch.object(shutil, 'copyfileobj', corrupted):
+            code, report = self.main()
+        self.assertEqual((code, report['error']), (1, 'PROVIDER_CACHE_INVALID'))
+        self.assertTrue(self.target.is_dir())
+        self.assert_rejected()
+        other_root = self.base / 'cleanup failure store'
+        original_copy = shutil.copy2
+        def copied(src, dst, *args, **kwargs):
+            original_copy(src, dst, *args, **kwargs)
+            raise OSError('PRIVATE_PRIMARY')
+        with patch.object(shutil, 'copy2', copied), patch.object(Path, 'unlink', side_effect=PermissionError('PRIVATE_CLEANUP')):
+            with self.assertRaises(installer.ProviderCacheError) as rejected:
+                installer.freeze(self.source, other_root)
+        self.assertEqual(str(rejected.exception), '')
+        self.assertEqual(len(list((other_root / 'provider').glob('.stage-*'))), 1)
+
+    def test_reparse_and_dangling_entries_simulated_without_host_access(self):
+        installer.freeze(self.source, self.root)
+        original = Path.lstat
+        for chosen in (self.root / 'provider', self.target, self.target / installer.FILES[0]):
+            def lstat(path, *args, **kwargs):
+                result = original(path, *args, **kwargs)
+                if path == chosen:
+                    return SimpleNamespace(st_mode=result.st_mode, st_file_attributes=0x400,
+                                           st_dev=result.st_dev, st_ino=result.st_ino)
+                return result
+            with self.subTest(chosen=chosen), patch.object(Path, 'lstat', lstat):
+                code, report = self.main()
+                self.assertEqual((code, report['error']), (1, 'PROVIDER_CACHE_INVALID'))
+        for chosen in (self.root / 'provider', self.target, self.target / installer.FILES[0]):
+            def dangling(path, *args, **kwargs):
+                if path == chosen:
+                    return SimpleNamespace(st_mode=stat.S_IFLNK | 0o777)
+                return original(path, *args, **kwargs)
+            with self.subTest(chosen=chosen), patch.object(Path, 'lstat', dangling):
+                code, report = self.main()
+                self.assertEqual((code, report['error']), (1, 'PROVIDER_CACHE_INVALID'))
+
+    def test_actual_symlink_cache_file_is_rejected_when_platform_allows(self):
+        installer.freeze(self.source, self.root)
+        chosen = self.target / installer.FILES[0]
+        chosen.unlink()
+        try:
+            chosen.symlink_to(self.source / chosen.name)
+        except OSError as exc:
+            self.skipTest('实际symlink权限不可用：' + type(exc).__name__)
+        self.assert_rejected()
+
+    def test_dry_run_creates_no_cache_plugin_or_backup(self):
+        before = self.tree(self.profile)
+        code, report = self.main('--dry-run')
+        self.assertEqual(code, 0)
+        self.assertTrue(report['dry_run'])
+        self.assertFalse(self.root.exists())
+        self.assertEqual(self.tree(self.profile), before)
+
+    def test_source_drift_between_plan_and_freeze_rejects_before_any_profile_write(self):
+        before = self.tree(self.profile)
+        original = installer.freeze
+        def changed_source(src, root):
+            (src / installer.FILES[0]).write_bytes(b'changed after plan digest')
+            return original(src, root)
+        with patch.object(installer, 'freeze', changed_source):
+            code, report = self.main()
+        self.assertEqual((code, report), (1, {'status': 'FAILED', 'error': 'PROVIDER_CACHE_INVALID'}))
+        self.assertEqual(self.tree(self.profile), before)
+        self.assertFalse((self.profile / 'plugins').exists())
+        self.assertEqual(list(self.profile.glob('config.yaml.bak-*')), [])
+        current = installer.digest(self.source)
+        with (patch.object(installer, 'freeze', return_value=(self.root / 'provider' / current[:8], current[:8])),
+              patch.object(installer, '_verify_cache', side_effect=OSError('PRIVATE_FINAL_CHECK'))):
+            code, report = self.main()
+        self.assertEqual((code, report), (1, {'status': 'FAILED', 'error': 'PROVIDER_CACHE_INVALID'}))
+        self.assertEqual(self.tree(self.profile), before)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_manage.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_manage.py
@@ -0,0 +1,278 @@
+"""候选管理仅操作临时合成 store；实际 CLI 验证目标绑定、CAS 与幂等。"""
+import contextlib
+from dataclasses import replace
+import io
+import json
+from pathlib import Path
+import sqlite3
+import subprocess
+import sys
+import tempfile
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path[:0] = [str(ROOT / 'runtime'), str(ROOT / 'integrations/hermes_memory'), str(ROOT / 'tools')]
+import hermes_memory_manage as manage  # noqa: E402
+from recall_service import RecallService  # noqa: E402
+from life_engine.domain import CanonStatus, DomainId, IdKind, RealityStatus, SourceType  # noqa: E402
+from life_engine.memory import AudienceKind, IdempotencyIdentity, MemoryAudience, MemoryKind  # noqa: E402
+from life_engine.memory_repository import MemoryFailure as MC, MemoryRuntimeError  # noqa: E402
+
+PRIVATE = 'PRIVATE_SYNTHETIC_BODY_DO_NOT_PRINT'
+
+
+class ManageArgumentTests(unittest.TestCase):
+    def test_invalid_arguments_do_not_open_store_or_echo_input(self):
+        mid = str(DomainId.new(IdKind.MEMORY))
+        base = ['accept', '--root', '/PRIVATE_PATH', '--profile-home', '/PRIVATE_PROFILE', '--memory-id', mid]
+        cases = [[], ['unknown', PRIVATE], ['inspect'], base,
+                 base + ['--expected-revision', '0', '--unknown', PRIVATE]]
+        for revision in ('-1', 'True', '１', '١', '9223372036854775808', '1.0', PRIVATE):
+            cases.append(base + ['--expected-revision', revision])
+        for index in (2, 4):
+            for value in ('', ' \t\n'):
+                arguments = base + ['--expected-revision', '0']
+                arguments[index] = value
+                cases.append(arguments)
+        for identifier in ('memory:not-a-uuid', str(DomainId.new(IdKind.WORLD)), mid.upper(), PRIVATE):
+            cases.append(['inspect', '--root', '/PRIVATE_PATH', '--profile-home', '/PRIVATE_PROFILE', '--memory-id', identifier])
+        for arguments in cases:
+            with self.subTest(arguments=arguments):
+                output, errors = io.StringIO(), io.StringIO()
+                with (patch.object(manage, 'existing_service') as opener,
+                      contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors)):
+                    code = manage.main(arguments)
+                opener.assert_not_called()
+                self.assertEqual(code, 1)
+                self.assertEqual(json.loads(output.getvalue()), {'ok': False, 'failure_code': 'ARGUMENT_INVALID'})
+                self.assertEqual(errors.getvalue(), '')
+                self.assertNotIn('PRIVATE', output.getvalue())
+
+
+class ManageProcessTests(unittest.TestCase):
+    def setUp(self):
+        directory = tempfile.TemporaryDirectory(prefix='le-manage-synthetic-')
+        self.addCleanup(directory.cleanup)
+        self.base = Path(directory.name)
+        self.store = self.base / 'store'
+        self.profile = self.base / 'profile'
+        self.profile.mkdir()
+        service = self.open()
+        service.remember_turn('user', PRIVATE)
+        receipt = service.flush_recall(accept=False)
+        self.mid = receipt.memory_id
+        self.revision = receipt.revision.value
+        self.dbpath = service._memory.repository.path
+        self.assertEqual(service.recall(), [])
+
+    def open(self, profile=None, store=None):
+        service = RecallService(ROOT / 'runtime', store or self.store, profile or self.profile, '同名合成角色')
+        service.ensure()
+        return service
+
+    def snapshot(self):
+        with contextlib.closing(sqlite3.connect(self.dbpath)) as db:
+            result = {table: tuple(db.execute(f'SELECT * FROM {table} ORDER BY 1,2')) for table in
+                      ('world_memories', 'memory_audiences', 'memory_subjects', 'memory_lineage',
+                       'memory_collection_state', 'memory_operations', 'memory_idempotency')}
+        result['state'] = (self.store / 'state.json').read_bytes()
+        result['cursor'] = (self.store / 'flush.json').read_bytes()
+        return result
+
+    def command(self, verb='inspect', *, mid=None, revision=None, profile=None, store=None):
+        arguments = [sys.executable, '-X', 'utf8', '-B', str(ROOT / 'tools/hermes_memory_manage.py'), verb,
+                     '--root', str(store or self.store), '--profile-home', str(profile or self.profile),
+                     '--memory-id', str(mid or self.mid)]
+        if verb == 'accept':
+            arguments += ['--expected-revision', str(self.revision if revision is None else revision)]
+        process = subprocess.run(arguments, capture_output=True, text=True, encoding='utf-8', timeout=30)
+        self.assertEqual(process.stderr, '')
+        self.assertNotIn(PRIVATE, process.stdout)
+        self.assertNotIn(str(self.base), process.stdout)
+        self.assertEqual(len(process.stdout.splitlines()), 1)
+        return process.returncode, json.loads(process.stdout)
+
+    def assert_target_failure(self, **options):
+        before = self.snapshot()
+        code, report = self.command(**options)
+        self.assertEqual((code, report), (1, {'ok': False, 'failure_code': 'TARGET_NOT_AVAILABLE'}))
+        self.assertEqual(self.snapshot(), before)
+
+    def test_default_candidate_inspect_accept_real_successor_and_cross_process_replays(self):
+        before = self.snapshot()
+        code, report = self.command()
+        self.assertEqual(code, 0)
+        self.assertEqual(report['canon_status'], 'candidate')
+        self.assertEqual(report['lifecycle'], 'live')
+        self.assertEqual(report['collection_revision'], self.revision)
+        self.assertNotIn('content', report)
+        self.assertEqual(self.snapshot(), before)
+        code, accepted = self.command('accept')
+        self.assertEqual(code, 0)
+        self.assertEqual(accepted['requested_memory_id'], str(self.mid))
+        self.assertNotEqual(accepted['resulting_memory_id'], str(self.mid))
+        service = self.open()
+        result = service.recall()
+        self.assertEqual(len(result), 1)
+        self.assertEqual(str(result[0].memory_id), accepted['resulting_memory_id'])
+        self.assertEqual(result[0].predecessor, self.mid)
+        self.assertEqual(result[0].provenance.canon_status, CanonStatus.ACCEPTED)
+        self.assertEqual(accepted['revision'], self.revision + 1)
+        after = self.snapshot()
+        self.assertEqual(after['cursor'], before['cursor'])
+        self.assertEqual(after['state'], before['state'])
+        self.assertEqual(len(after['world_memories']), len(before['world_memories']) + 1)
+        for revision in (self.revision, 0, 9223372036854775807):
+            code, replay = self.command('accept', revision=revision)
+            self.assertEqual((code, replay), (0, accepted))
+            self.assertEqual(self.snapshot(), after)
+        code, original = self.command()
+        self.assertEqual((code, original['lifecycle']), (0, 'superseded'))
+        self.assertEqual(original['superseded_by'], accepted['resulting_memory_id'])
+        self.assert_target_failure(verb='accept', mid=DomainId.parse(accepted['resulting_memory_id']))
+
+    def test_first_write_preserves_cas_and_does_not_refresh_revision(self):
+        self.command()
+        service = self.open()
+        service._memory.create_owner_memory(service._soul_owner, service._memory.collection_revision(service._soul_owner),
+                                            IdempotencyIdentity('management-test', 'unrelated'), content='其他合法记录',
+                                            kind=MemoryKind.EPISODIC,
+                                            audience=(MemoryAudience(AudienceKind.SOUL, service._soul_owner.scope.soul_id),),
+                                            provenance=replace(service._memory.get_memory(service._soul_owner, self.mid, history=True).provenance,
+                                                               source_type=SourceType.USER_REPORT, canon_status=CanonStatus.ACCEPTED,
+                                                               reality_status=RealityStatus.USER_CLAIMED,
+                                                               source_world_id=None, source_timeline_id=None))
+        before = self.snapshot()
+        code, report = self.command('accept')
+        self.assertEqual((code, report), (1, {'ok': False, 'failure_code': 'MemoryRevisionConflict'}))
+        self.assertEqual(self.snapshot(), before)
+
+    def test_wrong_character_same_display_name_and_cross_soul_and_unknown(self):
+        other = self.base / 'other-character'
+        other.mkdir()
+        self.open(other)
+        self.assert_target_failure(profile=other)
+        foreign_store = self.base / 'foreign-store'
+        self.open(store=foreign_store)
+        self.assert_target_failure(store=foreign_store)
+        self.assert_target_failure(mid=DomainId.new(IdKind.MEMORY))
+
+    def test_hidden_candidate_inspect_allowed_but_accept_cannot_resurrect(self):
+        service = self.open()
+        service._memory.hide_memory(service._soul_owner, self.mid,
+                                    service._memory.collection_revision(service._soul_owner), IdempotencyIdentity('manage-test', 'hide'))
+        before = self.snapshot()
+        code, report = self.command()
+        self.assertEqual((code, report['lifecycle']), (0, 'hidden'))
+        self.assertEqual(self.snapshot(), before)
+        self.assert_target_failure(verb='accept', revision=self.revision + 1)
+
+    def test_rejected_or_other_superseded_original_is_not_tool_replay(self):
+        service = self.open()
+        receipt = service._memory.reject_memory(service._soul_owner, self.mid,
+                                               service._memory.collection_revision(service._soul_owner), IdempotencyIdentity('manage-test', 'reject'))
+        self.assert_target_failure(verb='accept')
+        self.assert_target_failure(verb='accept', mid=receipt.memory_id)
+
+    def test_forgotten_original_and_success_receipt_result_cannot_fake_success(self):
+        code, report = self.command('accept')
+        self.assertEqual(code, 0)
+        result = DomainId.parse(report['resulting_memory_id'])
+        service = self.open()
+        service._memory.hide_memory(service._soul_owner, result,
+                                    service._memory.collection_revision(service._soul_owner), IdempotencyIdentity('manage-test', 'hide-result'))
+        self.assert_target_failure(verb='accept')
+        service = self.open()
+        service._memory.unhide_memory(service._soul_owner, result,
+                                      service._memory.collection_revision(service._soul_owner), IdempotencyIdentity('manage-test', 'unhide-result'))
+        service._memory.delete_memory(service._soul_owner, result,
+                                      service._memory.collection_revision(service._soul_owner), IdempotencyIdentity('manage-test', 'forget-result'))
+        self.assert_target_failure(verb='accept')
+        service = self.open()
+        service._memory.delete_memory(service._soul_owner, self.mid,
+                                      service._memory.collection_revision(service._soul_owner), IdempotencyIdentity('manage-test', 'forget-original'))
+        self.assert_target_failure()
+        self.assert_target_failure(verb='accept')
+
+    def test_source_archived_or_tombstoned_does_not_add_dependency(self):
+        service = self.open()
+        source = str(service._rp_owner.scope.world_id)
+        for status in ('archived', 'tombstoned'):
+            with contextlib.closing(sqlite3.connect(self.dbpath)) as db:
+                db.execute('UPDATE worlds SET status=? WHERE world_id=?', (status, source))
+                db.commit()
+            before = self.snapshot()
+            self.assertEqual(self.command()[0], 0)
+            self.assertEqual(self.snapshot(), before)
+        self.assertEqual(self.command('accept')[0], 0)
+
+    def test_unregistered_profile_and_legacy_layout_do_not_initialize_or_migrate(self):
+        unknown = self.base / 'unknown'
+        unknown.mkdir()
+        before = self.snapshot()
+        code, report = self.command(profile=unknown)
+        self.assertEqual((code, report), (1, {'ok': False, 'failure_code': 'CHARACTER_NOT_REGISTERED'}))
+        self.assertEqual(self.snapshot(), before)
+        path = self.store / 'state.json'
+        state = json.loads(path.read_text(encoding='utf-8'))
+        state.pop('version')
+        path.write_text(json.dumps(state), encoding='utf-8')
+        before = self.snapshot()
+        code, report = self.command()
+        self.assertEqual((code, report), (1, {'ok': False, 'failure_code': 'STORE_VERSION_UNSUPPORTED'}))
+        self.assertEqual(self.snapshot(), before)
+
+    def test_same_basename_alias_is_only_local_character_key_not_path_authentication(self):
+        alias = self.base / 'alias-parent' / self.profile.name
+        alias.mkdir(parents=True)
+        before = self.snapshot()
+        code, report = self.command(profile=alias)
+        self.assertEqual((code, report['character_key']), (0, self.profile.name))
+        self.assertEqual(self.snapshot(), before)
+
+    def test_nonrecall_target_and_other_supersede_cannot_be_accepted(self):
+        service = self.open()
+        original = service._memory.get_memory(service._soul_owner, self.mid, history=True)
+        ordinary = service._memory.create_owner_memory(
+            service._soul_owner, service._memory.collection_revision(service._soul_owner),
+            IdempotencyIdentity('manage-test', 'ordinary'), content=PRIVATE, kind=MemoryKind.EPISODIC,
+            audience=original.audience, provenance=replace(original.provenance, source_type=SourceType.USER_REPORT,
+                                                         reality_status=RealityStatus.USER_CLAIMED,
+                                                         source_world_id=None, source_timeline_id=None))
+        self.assert_target_failure(mid=ordinary.memory_id)
+        service = self.open()
+        original = service._memory.get_memory(service._soul_owner, self.mid, history=True)
+        service._memory.supersede_memory(service._soul_owner, self.mid,
+                                         service._memory.collection_revision(service._soul_owner),
+                                         IdempotencyIdentity('manage-test', 'other-supersede'),
+                                         content='其他明确候选修订', provenance=original.provenance)
+        self.assert_target_failure(verb='accept')
+
+    def test_semantic_binding_and_receipt_predecessor_are_checked(self):
+        service = self.open()
+        original = service._memory.get_memory(service._soul_owner, self.mid, history=True)
+        for record in (replace(original, kind=MemoryKind.EPISODIC),
+                       replace(original, audience=(MemoryAudience(AudienceKind.WORLD),)),
+                       replace(original, provenance=replace(original.provenance, source_timeline_id=DomainId.new(IdKind.TIMELINE)))):
+            with self.assertRaises(manage.ManagementError) as caught:
+                manage._bound_target(record, service)
+            self.assertEqual(caught.exception.code, 'TARGET_NOT_AVAILABLE')
+        args = ['accept', '--root', str(self.store), '--profile-home', str(self.profile),
+                '--memory-id', str(self.mid), '--expected-revision', str(self.revision)]
+        accepted = service._memory.accept_memory(service._soul_owner, self.mid,
+                                                 service._memory.collection_revision(service._soul_owner),
+                                                 IdempotencyIdentity('manage-test', 'fixture-accept'))
+        result = service._memory.get_memory(service._soul_owner, accepted.memory_id)
+        with (patch.object(manage, 'existing_service', return_value=service),
+              patch.object(service._memory, 'get_memory', side_effect=[original, replace(result, predecessor=None)]),
+              patch.object(service._memory, 'accept_memory', return_value=accepted)):
+            output = io.StringIO()
+            with contextlib.redirect_stdout(output):
+                code = manage.main(args)
+        self.assertEqual((code, json.loads(output.getvalue())),
+                         (1, {'ok': False, 'failure_code': 'TARGET_NOT_AVAILABLE'}))
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_provider.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_provider.py
@@ -0,0 +1,217 @@
+"""Hermes 记忆 provider 的核心服务：写入、汇总、召回与失败隔离。"""
+import json
+import sys
+import tempfile
+import unittest
+from datetime import datetime, timezone
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'runtime'))
+sys.path.insert(0, str(ROOT / 'integrations' / 'hermes_memory'))
+
+from recall_service import BOUNDARY, RecallService  # noqa: E402
+
+NOW = datetime(2026, 10, 20, 9, 0, tzinfo=timezone.utc)
+
+
+class RecallServiceTests(unittest.TestCase):
+    def setUp(self):
+        directory = tempfile.TemporaryDirectory(prefix='lew-hermes-memory-')
+        self.addCleanup(directory.cleanup)
+        self.base = Path(directory.name).resolve()
+        self.rootdir = self.base / 'recall'
+        self.profile = self.base / 'profile'
+        self.profile.mkdir()
+        self.service = RecallService(
+            ROOT / 'runtime', self.rootdir, self.profile, '仙姑',
+            clock=lambda: NOW)
+
+    # --- 初始化 -----------------------------------------------------------
+
+    def test_bootstrap_creates_isolated_store(self):
+        self.assertTrue(self.service.available())
+        self.assertTrue((self.service.root / 'state.json').exists())
+        self.assertTrue((self.service.root / 'install').is_dir())
+        self.assertEqual(self.service.unavailable_reason(), '')
+
+    def test_second_service_reuses_same_store(self):
+        self.service.ensure()
+        before = (self.service.root / 'state.json').read_text(encoding='utf-8')
+        again = RecallService(ROOT / 'runtime', self.service.root, self.profile, '仙姑',
+                              clock=lambda: NOW)
+        self.assertTrue(again.available())
+        after = (again.root / 'state.json').read_text(encoding='utf-8')
+        self.assertEqual(before, after, '重复初始化不应重建实例或丢作用域')
+
+    # --- 写入与汇总 -------------------------------------------------------
+
+    def test_turns_do_not_become_soul_recall_until_flush(self):
+        self.service.ensure()
+        self.service.remember_turn('user', '明天下午面试，我有点紧张')
+        self.service.remember_turn('assistant', '我记着，别太累')
+        self.assertEqual(self.service.recall('面试'), [],
+                         '轮次本身不应立刻变成 Soul 回忆录')
+        receipt = self.service.flush_recall()
+        self.assertIsNotNone(receipt)
+        records = self.service.recall('面试')
+        self.assertEqual(len(records), 1)
+        self.assertIn('仙姑', records[0].content)
+        self.assertIn(BOUNDARY.strip('（）'), self.service.render(records))
+
+    def test_flush_is_idempotent_without_new_turns(self):
+        self.service.ensure()
+        self.service.remember_turn('user', '第一轮')
+        self.assertIsNotNone(self.service.flush_recall())
+        self.assertIsNone(self.service.flush_recall(), '没有新轮次时不应再写回忆录')
+        self.assertEqual(len(self.service.recall()), 1)
+
+    def test_second_batch_creates_second_recall(self):
+        self.service.ensure()
+        self.service.remember_turn('user', '第一轮')
+        self.service.flush_recall()
+        self.service.remember_turn('user', '第二轮')
+        self.service.flush_recall()
+        self.assertEqual(len(self.service.recall()), 2)
+
+    def test_action_result_survives_in_long_batch(self):
+        """出图/动作结果在 assistant 一侧；长批次里不能被"用户优先"挤掉。"""
+        self.service.ensure()
+        for i in range(4):
+            self.service.remember_turn('user', f'第{i}轮的要求')
+            self.service.remember_turn('assistant', f'第{i}轮的回应')
+        self.service.remember_turn('assistant', '这次手动出图已经跑通了，图在这里。')
+        self.service.flush_recall()
+        content = self.service.recall()[0].content
+        self.assertIn('图在这里', content, '最近的动作结果必须出现在回忆录里')
+        highlights = [line[2:] for line in content.splitlines() if line.startswith('- ')]
+        self.assertEqual(highlights, ['第0轮的要求', '第0轮的回应', '第1轮的要求',
+                                      '第1轮的回应', '第3轮的要求',
+                                      '这次手动出图已经跑通了，图在这里。'])
+        self.assertIn('第3轮的要求', highlights)
+        self.assertEqual(len(highlights), 6)
+        self.assertEqual(len(highlights), len(set(highlights)))
+
+    def test_second_recall_contains_only_the_new_batch(self):
+        """游标切片必须按时间重排，不能把旧批次混进新回忆录。"""
+        self.service.ensure()
+        self.service.remember_turn('user', '第一批：面试')
+        self.service.flush_recall()
+        self.service.remember_turn('user', '第二批：写稿子')
+        self.service.flush_recall()
+        recalls = sorted(self.service.recall(), key=lambda r: r.created_at)
+        self.assertEqual(len(recalls), 2)
+        self.assertIn('写稿子', recalls[1].content)
+        self.assertNotIn('面试', recalls[1].content,
+                         '第二批回忆录不得包含第一批的内容')
+        self.assertEqual(len(recalls[1].content.splitlines()), len(set(recalls[1].content.splitlines())))
+
+    def test_auto_record_off_skips_writes(self):
+        service = RecallService(ROOT / 'runtime', self.service.root, self.profile, '仙姑',
+                                auto_record=False, clock=lambda: NOW)
+        service.ensure()
+        service.remember_turn('user', '不该被记录')
+        self.assertIsNone(service.flush_recall())
+
+    # --- 失败隔离 ---------------------------------------------------------
+
+    def test_missing_runtime_is_reported_not_raised(self):
+        service = RecallService(Path('/nonexistent-runtime'), self.service.root,
+                                self.profile, '仙姑', clock=lambda: NOW)
+        self.assertFalse(service.available())
+        self.assertNotEqual(service.unavailable_reason(), '')
+
+    def test_render_empty_is_empty_string(self):
+        self.service.ensure()
+        self.assertEqual(self.service.render([]), '')
+
+    # --- 多角色共享同一个 Soul -------------------------------------------
+    # 真实环境里每个 Profile 是独立进程，同一进程并存两个 WorldRuntime 会触发
+    # 既有 generation fence，所以这里按"顺序生命周期"验证。
+
+    def open_as(self, name, key):
+        profile = self.base / key
+        profile.mkdir(exist_ok=True)
+        return RecallService(ROOT / 'runtime', self.rootdir, profile, name, clock=lambda: NOW)
+
+    def test_second_character_shares_one_soul_world(self):
+        first = self.open_as('殷冬雪', 'dongxue')
+        first.ensure()
+        soul_scope, rp_scope = first._soul_owner.scope, first._rp_owner.scope
+        del first
+
+        second = self.open_as('苏瑶', 'suyao')
+        second.ensure()
+        self.assertEqual(second._soul_owner.scope, soul_scope,
+                         '两个角色必须共用同一个 Soul 作用域')
+        self.assertNotEqual(second._rp_owner.scope, rp_scope,
+                            '每个角色必须有独立的角色扮演世界')
+        self.assertEqual(set(second.characters()), {'dongxue', 'suyao'})
+
+    def test_soul_remembers_other_characters_after_switching(self):
+        first = self.open_as('殷冬雪', 'dongxue')
+        first.ensure()
+        first.remember_turn('user', '我明天下午有个面试')
+        first.flush_recall()
+        del first
+
+        second = self.open_as('苏瑶', 'suyao')
+        second.ensure()
+        second.remember_turn('user', '今天写稿写到很晚')
+        second.flush_recall()
+
+        # 站在第二个角色上，Soul 已经记得另一段扮演
+        joined = '\n'.join(r.content for r in second.recall())
+        self.assertIn('面试', joined)
+        self.assertIn('写稿', joined)
+        self.assertIn('苏瑶', joined)
+        self.assertIn('殷冬雪', joined)
+
+    def test_flush_cursors_are_per_character(self):
+        first = self.open_as('殷冬雪', 'dongxue')
+        first.ensure()
+        first.remember_turn('user', '角色一的一句话')
+        first.flush_recall()
+        del first
+
+        second = self.open_as('苏瑶', 'suyao')
+        second.ensure()
+        second.remember_turn('user', '角色二的一句话')
+        second.flush_recall()
+        del second
+
+        again = self.open_as('殷冬雪', 'dongxue')
+        again.ensure()
+        self.assertIsNone(again.flush_recall(), '角色一没有新轮次，不应再写回忆录')
+        self.assertEqual(len(again.recall()), 2)
+
+    def test_legacy_flat_state_is_migrated(self):
+        self.service.ensure()
+        self.service.remember_turn('user', '迁移前的一句话')
+        self.service.flush_recall()
+        recalls_before = len(self.service.recall())
+
+        # 手工降级成旧的扁平结构
+        state_path = self.service.root / 'state.json'
+        state = json.loads(state_path.read_text(encoding='utf-8'))
+        entry = state['characters']['profile']
+        flat = {'principal': state['principal'], 'owner': state['owner'], 'soul': state['soul'],
+                'character': '殷冬雪'}
+        for key, value in state.items():
+            if key.startswith('soul_'):
+                flat[key] = value
+        for field in ('owner', 'soul', 'world', 'timeline'):
+            flat[f'rp_{field}'] = entry[f'rp_{field}']
+        state_path.write_text(json.dumps(flat), encoding='utf-8')
+        (self.service.root / 'flush.json').unlink()
+
+        migrated = RecallService(ROOT / 'runtime', self.service.root, self.profile, '殷冬雪',
+                                 clock=lambda: NOW)
+        self.assertTrue(migrated.available())
+        self.assertEqual(migrated.characters(), ('profile',))
+        self.assertEqual(len(migrated.recall()), recalls_before,
+                         '迁移不得丢失已有回忆录')
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_provider_config.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_provider_config.py
@@ -0,0 +1,419 @@
+"""包装层只使用复制插件、临时配置和替身，不读取真实 Hermes Home。"""
+import importlib.util
+import json
+import os
+from pathlib import Path
+import shutil
+import subprocess
+import sys
+import tempfile
+import types
+import unittest
+from unittest import mock
+
+
+ROOT = Path(__file__).resolve().parents[1]
+FILES = ('__init__.py', 'recall_service.py', 'plugin.yaml')
+TARGET = dict(runtime_path='runtime space', root='store space', profile_home='profile space')
+ENV = dict(LIFE_ENGINE_RUNTIME='bait-runtime', LIFE_ENGINE_RECALL_ROOT='bait-root',
+           HERMES_PROFILE_DIR='bait-profile')
+
+
+class StubService:
+    def __init__(self):
+        self.calls = []
+        self.ready = True
+        self.fail = ''
+        self.rendered = '安全的合成回忆'
+
+    def _call(self, name, *args):
+        self.calls.append((name, args))
+        if self.fail == name:
+            raise RuntimeError('SECRET-PATH-AND-BODY')
+
+    def available(self):
+        self._call('available')
+        return self.ready
+
+    def recall(self, query):
+        self._call('recall', query)
+        return ['synthetic']
+
+    def render(self, records):
+        self._call('render', records)
+        return self.rendered
+
+    def remember_turn(self, *args):
+        self._call('remember', *args)
+
+    def flush_recall(self):
+        self._call('flush')
+
+    def unavailable_reason(self):
+        raise AssertionError('不得读取自由文本诊断')
+
+
+class ProviderConfigTests(unittest.TestCase):
+    def setUp(self):
+        temporary = tempfile.TemporaryDirectory(prefix='le-provider-config-')
+        self.addCleanup(temporary.cleanup)
+        self.base = Path(temporary.name)
+        self.package = self.base / 'copied_provider'
+        self.package.mkdir()
+        for name in FILES:
+            shutil.copy2(ROOT / 'integrations/hermes_memory' / name, self.package / name)
+        name = '_rr_provider_config_' + self.base.name.replace('-', '_')
+        spec = importlib.util.spec_from_file_location(
+            name, self.package / '__init__.py', submodule_search_locations=[str(self.package)])
+        module = importlib.util.module_from_spec(spec)
+        sys.modules[name] = module
+        self.addCleanup(lambda: [sys.modules.pop(k, None) for k in list(sys.modules)
+                                 if k == name or k.startswith(name + '.')])
+        sdk = types.ModuleType('agent.memory_provider')
+        sdk.MemoryProvider = type('MemoryProvider', (), {})
+        with mock.patch.dict(sys.modules, {'agent': types.ModuleType('agent'),
+                                          'agent.memory_provider': sdk}):
+            spec.loader.exec_module(module)
+            self.assertEqual(Path(sys.modules[module.RecallService.__module__].__file__).resolve(),
+                             self.package / 'recall_service.py')
+        self.module = module
+        self.settings = self.package / 'settings.json'
+        self.service = StubService()
+        self.factory = mock.Mock(return_value=self.service)
+        module.RecallService = self.factory
+        # 所有配置环境均为合成值；任何默认 Home 展开立即失败。
+        self.environment = mock.patch.dict(os.environ, ENV, clear=True)
+        self.environment.start()
+        self.addCleanup(self.environment.stop)
+        self.home_guard = mock.patch.object(module.os.path, 'expanduser',
+                                           side_effect=AssertionError('DEFAULT HOME ACCESS'))
+        self.home_guard.start()
+        self.addCleanup(self.home_guard.stop)
+
+    def configure(self, value=None):
+        self.settings.write_text(json.dumps(TARGET if value is None else value), encoding='utf-8')
+
+    def disabled(self, reason):
+        provider = self.module.LifeEngineMemoryProvider()
+        self.assertFalse(provider.is_available())
+        self.assertIsNone(provider.initialize('session'))
+        self.assertEqual(provider.prefetch('SECRET-QUERY'), '')
+        self.assertIsNone(provider.sync_turn('SECRET-USER', 'SECRET-ASSISTANT'))
+        self.assertIsNone(provider.on_session_end([]))
+        self.assertIsNone(provider.on_session_switch('next', reset=True))
+        self.assertEqual(provider.get_tool_schemas(), [])
+        self.assertEqual(provider.system_prompt_block(), '')
+        self.assertIsNone(provider.recall_status())
+        self.assertEqual(provider.identity_signature(), {})
+        self.assertEqual(provider.unavailable_reason(), reason)
+        self.factory.assert_not_called()
+        self.assertEqual(self.service.calls, [])
+        return provider
+
+    def test_complete_settings_authoritative_snapshot_and_lazy_creation(self):
+        self.configure(dict(TARGET, character_name='角色', extra='ignored'))
+        provider = self.module.LifeEngineMemoryProvider()
+        self.factory.assert_not_called()
+        os.environ.update({k: 'changed' for k in ENV})
+        self.configure(dict(TARGET, root='changed-file'))
+        self.assertTrue(provider.is_available())
+        self.factory.assert_called_once_with(*TARGET.values(), '角色', auto_record=True)
+        self.assertEqual(provider.identity_signature(), {'life_engine_root': TARGET['root']})
+        self.assertEqual(provider.unavailable_reason(), '')
+
+    def test_missing_settings_requires_all_three_explicit_environment_targets(self):
+        provider = self.module.LifeEngineMemoryProvider()
+        self.assertTrue(provider.is_available())
+        self.factory.assert_called_once_with(*ENV.values(), '', auto_record=True)
+        for missing in ENV:
+            with self.subTest(missing=missing), mock.patch.dict(os.environ, ENV, clear=True):
+                os.environ.pop(missing)
+                self.factory.reset_mock()
+                self.service.calls.clear()
+                self.disabled('CONFIG_MISSING_TARGET')
+
+    def test_invalid_json_utf8_and_non_object_do_not_fall_back(self):
+        for raw in (b'{bad', b'\xff', b'[]', b'null', b'9', b'"text"', b'true'):
+            with self.subTest(raw=raw):
+                self.settings.write_bytes(raw)
+                self.disabled('CONFIG_INVALID')
+
+    def test_incomplete_settings_never_use_bait_environment(self):
+        for key in TARGET:
+            config = dict(TARGET)
+            config.pop(key)
+            with self.subTest(key=key):
+                self.configure(config)
+                self.disabled('CONFIG_MISSING_TARGET')
+
+    def test_invalid_paths_and_optional_fields(self):
+        bad = ('', ' ', ' leading', 'trailing ', 'nul\0path', '\ud800', 1, False, [], None)
+        for key in TARGET:
+            for value in bad:
+                with self.subTest(key=key, value=repr(value)):
+                    self.configure(dict(TARGET, **{key: value}))
+                    self.disabled('CONFIG_INVALID')
+        for key, values in (('auto_record', ('false', 0, 1, None, [])),
+                            ('character_name', (None, 0, False, []))):
+            for value in values:
+                with self.subTest(key=key, value=value):
+                    self.configure(dict(TARGET, **{key: value}))
+                    self.disabled('CONFIG_INVALID')
+
+    def test_settings_read_failure_directory_and_dangling_entry_fail_closed(self):
+        self.configure()
+        with mock.patch.object(Path, 'read_text', side_effect=PermissionError('SECRET')):
+            self.disabled('CONFIG_READ_FAILED')
+        self.settings.unlink()
+        self.settings.mkdir()
+        self.disabled('CONFIG_READ_FAILED')
+        self.settings.rmdir()
+        # Windows 无符号链接权限时，显式模拟 lstat 成功/read 缺失；不能当入口缺失。
+        with mock.patch.object(Path, 'lstat', return_value=object()), \
+                mock.patch.object(Path, 'read_text', side_effect=FileNotFoundError('dangling')):
+            self.disabled('CONFIG_READ_FAILED')
+
+    def test_relative_and_tilde_paths_are_not_probed_or_expanded(self):
+        self.configure(dict(runtime_path='./runtime', root='~/explicit', profile_home='../profile'))
+        with mock.patch.object(Path, 'exists', side_effect=AssertionError('target probe')):
+            provider = self.module.LifeEngineMemoryProvider()
+        self.factory.assert_not_called()
+        self.assertTrue(provider.is_available())
+        self.factory.assert_called_once_with('./runtime', '~/explicit', '../profile', '', auto_record=True)
+
+    def test_configuration_only_probes_settings_entry_and_lstat_failure_is_not_absence(self):
+        self.configure()
+        original_lstat, original_read = Path.lstat, Path.read_text
+        touched = []
+        def lstat(path, *args, **kwargs):
+            touched.append(('lstat', path))
+            self.assertEqual(path, self.settings)
+            return original_lstat(path, *args, **kwargs)
+        def read(path, *args, **kwargs):
+            touched.append(('read', path))
+            self.assertEqual(path, self.settings)
+            return original_read(path, *args, **kwargs)
+        with mock.patch.object(Path, 'lstat', lstat), mock.patch.object(Path, 'read_text', read):
+            provider = self.module.LifeEngineMemoryProvider()
+        self.assertEqual(touched, [('lstat', self.settings), ('read', self.settings)])
+        self.factory.assert_not_called()
+        self.assertEqual(provider.unavailable_reason(), '')
+        with mock.patch.object(Path, 'lstat', side_effect=OSError('SECRET-ENTRY')):
+            self.disabled('CONFIG_READ_FAILED')
+
+    def test_false_auto_record_keeps_reads_but_never_remembers_or_flushes(self):
+        self.configure(dict(TARGET, auto_record=False))
+        provider = self.module.LifeEngineMemoryProvider()
+        self.assertEqual(provider.prefetch('query'), self.service.rendered)
+        provider.sync_turn('user', 'assistant')
+        provider.on_session_end([])
+        provider.on_session_switch('next', reset=True)
+        self.assertFalse(any(name in ('remember', 'flush') for name, _ in self.service.calls))
+        self.factory.assert_called_once_with(*TARGET.values(), '', auto_record=False)
+
+    def test_true_records_and_only_reset_switch_flushes(self):
+        self.configure()
+        provider = self.module.LifeEngineMemoryProvider()
+        provider.initialize('initial')
+        provider.sync_turn('user', 'assistant')
+        provider.on_session_switch('next')
+        self.assertEqual(sum(name == 'flush' for name, _ in self.service.calls), 0)
+        provider.on_session_switch('reset', reset=True)
+        provider.on_session_end([])
+        self.assertEqual(sum(name == 'flush' for name, _ in self.service.calls), 2)
+        self.assertEqual([args for name, args in self.service.calls if name == 'remember'],
+                         [('user', 'user'), ('assistant', 'assistant')])
+
+    def test_nonreset_and_recording_disabled_switch_do_not_probe_service(self):
+        for auto_record, reset in ((True, False), (False, False), (False, True)):
+            with self.subTest(auto_record=auto_record, reset=reset):
+                self.configure(dict(TARGET, auto_record=auto_record))
+                provider = self.module.LifeEngineMemoryProvider()
+                provider.on_session_switch('next', reset=reset)
+                self.assertEqual(provider._session_id, 'next')
+                self.factory.assert_not_called()
+                self.assertEqual(self.service.calls, [])
+
+    def test_service_constructor_failure_each_callback_once_then_later_recovery(self):
+        self.configure()
+        provider = self.module.LifeEngineMemoryProvider()
+        self.factory.side_effect = OSError('SECRET-PATH')
+        callbacks = ((lambda: provider.is_available(), False),
+                     (lambda: provider.initialize('a'), None),
+                     (lambda: provider.prefetch('q'), ''),
+                     (lambda: provider.sync_turn('u', 'a'), None),
+                     (lambda: provider.on_session_end([]), None),
+                     (lambda: provider.on_session_switch('b', reset=True), None))
+        for callback, expected in callbacks:
+            before = self.factory.call_count
+            self.assertEqual(callback(), expected)
+            self.assertEqual(self.factory.call_count, before + 1)
+            self.assertEqual(provider.unavailable_reason(), 'SERVICE_UNAVAILABLE')
+        self.factory.side_effect = None
+        self.assertTrue(provider.is_available())
+        self.assertEqual(provider.unavailable_reason(), '')
+        self.assertEqual(self.factory.call_args.args[:3], tuple(TARGET.values()))
+
+    def test_available_exception_and_nonbool_never_reach_memory_actions(self):
+        self.configure()
+        for value in (1, 'yes', [], None, False, object()):
+            with self.subTest(value=repr(value)):
+                self.service.calls.clear()
+                self.service.ready = value
+                provider = self.module.LifeEngineMemoryProvider()
+                self.assertFalse(provider.is_available())
+                provider.initialize('a')
+                self.assertEqual(provider.prefetch('q'), '')
+                provider.sync_turn('u', 'a')
+                provider.on_session_end([])
+                provider.on_session_switch('b', reset=True)
+                self.assertTrue(all(name == 'available' for name, _ in self.service.calls))
+                self.assertEqual(provider.unavailable_reason(), 'SERVICE_UNAVAILABLE')
+        self.service.fail = 'available'
+        provider = self.module.LifeEngineMemoryProvider()
+        self.assertFalse(provider.is_available())
+        self.assertIsNone(provider.initialize('a'))
+
+    def test_callback_action_exceptions_and_render_type_are_isolated(self):
+        self.configure()
+        provider = self.module.LifeEngineMemoryProvider()
+        for fail, callback, expected in (
+                ('recall', lambda: provider.prefetch('q'), ''),
+                ('render', lambda: provider.prefetch('q'), ''),
+                ('remember', lambda: provider.sync_turn('u', 'a'), None),
+                ('flush', lambda: provider.on_session_end([]), None),
+                ('flush', lambda: provider.on_session_switch('x', reset=True), None)):
+            with self.subTest(fail=fail):
+                self.service.fail = fail
+                self.service.calls.clear()
+                self.assertEqual(callback(), expected)
+                self.assertEqual(provider.unavailable_reason(), 'SERVICE_UNAVAILABLE')
+                self.assertEqual(sum(name == 'available' for name, _ in self.service.calls), 1)
+                self.assertEqual(sum(name == fail for name, _ in self.service.calls), 1)
+        self.service.fail = ''
+        for rendered in (None, 1, [], b'bytes'):
+            self.service.rendered = rendered
+            self.assertEqual(provider.prefetch('q'), '')
+
+    def test_dependency_injection_does_not_read_any_config_or_environment(self):
+        self.settings.write_bytes(b'{bad')
+        with mock.patch.object(self.module, '_settings', side_effect=AssertionError('config read')), \
+                mock.patch.object(self.module.os, 'environ', None):
+            provider = self.module.LifeEngineMemoryProvider(service=self.service)
+        self.assertTrue(provider.is_available())
+        self.assertEqual(provider.identity_signature(), {})
+        self.assertEqual(provider.prefetch('q'), self.service.rendered)
+        provider.sync_turn('u', 'a')
+        self.assertEqual(sum(name == 'remember' for name, _ in self.service.calls), 2)
+        self.factory.assert_not_called()
+        self.service.fail = 'available'
+        self.assertFalse(provider.is_available())
+
+    def test_injected_available_failure_isolated_for_every_lifecycle(self):
+        provider = self.module.LifeEngineMemoryProvider(service=self.service)
+        self.service.fail = 'available'
+        for callback, expected in (
+                (lambda: provider.is_available(), False),
+                (lambda: provider.initialize('a'), None),
+                (lambda: provider.prefetch('q'), ''),
+                (lambda: provider.sync_turn('u', 'a'), None),
+                (lambda: provider.on_session_end([]), None),
+                (lambda: provider.on_session_switch('b', reset=True), None)):
+            self.service.calls.clear()
+            self.assertEqual(callback(), expected)
+            self.assertEqual(self.service.calls, [('available', ())])
+            self.assertEqual(provider.unavailable_reason(), 'SERVICE_UNAVAILABLE')
+        self.factory.assert_not_called()
+
+    def test_invalid_snapshot_cannot_recover_by_changed_file_or_environment(self):
+        self.settings.write_bytes(b'[]')
+        provider = self.disabled('CONFIG_INVALID')
+        self.configure()
+        self.assertFalse(provider.is_available())
+        self.assertEqual(provider.unavailable_reason(), 'CONFIG_INVALID')
+        self.factory.assert_not_called()
+
+    def test_register_disabled_instance_and_registration_failure_are_safe(self):
+        self.settings.write_bytes(b'[]')
+        ctx = mock.Mock()
+        self.assertIsNone(self.module.register(ctx))
+        provider = ctx.register_memory_provider.call_args.args[0]
+        self.assertFalse(provider.is_available())
+        self.configure()
+        captured = []
+        def reject(provider):
+            captured.append(provider)
+            raise RuntimeError('SECRET-REGISTRATION')
+        ctx.register_memory_provider.side_effect = reject
+        self.assertIsNone(self.module.register(ctx))
+        self.assertEqual(captured[0].unavailable_reason(), 'PROVIDER_REGISTRATION_FAILED')
+        self.factory.assert_not_called()
+        with mock.patch.object(self.module, 'LifeEngineMemoryProvider', side_effect=ValueError('SECRET')):
+            self.assertIsNone(self.module.register(ctx))
+
+    def test_process_control_exceptions_are_not_swallowed(self):
+        self.configure()
+        for error in (KeyboardInterrupt, SystemExit):
+            with self.subTest(error=error):
+                self.factory.side_effect = error()
+                provider = self.module.LifeEngineMemoryProvider()
+                with self.assertRaises(error):
+                    provider.is_available()
+                ctx = mock.Mock()
+                ctx.register_memory_provider.side_effect = error()
+                with self.assertRaises(error):
+                    self.module.register(ctx)
+
+    def test_installer_configuration_and_isolated_three_file_import_modes(self):
+        profile = self.base / 'install profile'
+        profile.mkdir()
+        (profile / 'config.yaml').write_text('model: synthetic\n', encoding='utf-8')
+        runtime = self.base / 'runtime'
+        runtime.mkdir()
+        store = self.base / 'install store'
+        result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'tools/hermes_memory_install.py'),
+                                 '--profile-home', str(profile), '--root', str(store),
+                                 '--runtime', str(runtime), '--character-name', '合成角色', '--skip-verify'],
+                                cwd=self.base, capture_output=True, text=True, encoding='utf-8')
+        self.assertEqual(result.returncode, 0, result.stderr)
+        copied = profile / 'plugins/life_engine'
+        script = r'''
+import importlib.util,json,os,pathlib,sys
+directory=pathlib.Path(sys.argv[1]).resolve()
+mode=sys.argv[2]
+assert not any('xiangmu' in p.lower() for p in sys.path)
+# 明确阻断真实 Host SDK；加载成功必须依赖插件自己的无 Host 替身。
+sys.modules['agent']=None
+name='isolated_package' if mode=='package' else 'isolated_standalone'
+kwargs={'submodule_search_locations':[str(directory)]} if mode=='package' else {}
+spec=importlib.util.spec_from_file_location(name,directory/'__init__.py',**kwargs)
+module=importlib.util.module_from_spec(spec)
+sys.modules[name]=module
+spec.loader.exec_module(module)
+service_module=sys.modules[module.RecallService.__module__]
+assert pathlib.Path(service_module.__file__).resolve()==directory/'recall_service.py'
+class Stub:
+ def available(self):return True
+ def recall(self,q):return []
+ def render(self,r):return 'copied-package-only'
+calls=[]
+module.RecallService=lambda *a,**kw:(calls.append((a,kw)) or Stub())
+provider=module.LifeEngineMemoryProvider()
+assert not calls
+assert provider.is_available() is True
+assert provider.prefetch('q')=='copied-package-only'
+settings=json.loads((directory/'settings.json').read_text(encoding='utf-8'))
+assert list(calls[0][0])==[settings[k] for k in ('runtime_path','root','profile_home','character_name')]
+assert provider.identity_signature()=={'life_engine_root':settings['root']}
+print(json.dumps({'mode':mode,'imported_from_copy':True,'settings_used':True}))
+'''
+        for mode in ('package', 'standalone'):
+            result = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', '-c', script,
+                                     str(copied), mode], cwd=self.base, capture_output=True,
+                                    text=True, encoding='utf-8', env=dict(ENV))
+            self.assertEqual(result.returncode, 0, result.stderr)
+            self.assertTrue(json.loads(result.stdout)['imported_from_copy'])
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_retrieval.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_retrieval.py
@@ -0,0 +1,184 @@
+"""预先固定的词面召回门槛；不修改 v1 语料或既有安全断言。"""
+from datetime import datetime, timedelta, timezone
+from pathlib import Path
+from types import SimpleNamespace
+from unittest.mock import Mock
+import sys
+import shutil
+import subprocess
+import tempfile
+import unittest
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path[:0] = [str(ROOT / 'runtime'), str(ROOT / 'integrations' / 'hermes_memory')]
+from recall_service import RecallService  # noqa: E402
+from life_engine.domain import SourceType  # noqa: E402
+
+
+class RetrievalSelectionTests(unittest.TestCase):
+    def record(self, key, *bullets, name='合成角色', day=0, content=None):
+        text = '\n'.join(['[角色扮演回忆]', '扮演世界：world:PRIVATE_METADATA',
+                          '时间：2026-01-01', '交互轮次：2'] +
+                         (['期间记得的事：'] + ['- ' + text for text in bullets] if bullets else []) +
+                         ['这是一次角色扮演经历，不是真实发生过的事实。'])
+        return SimpleNamespace(memory_id=key, content=text if content is None else content,
+                               created_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=day),
+                               provenance=SimpleNamespace(source_type=SourceType.ROLEPLAY_RECALL),
+                               subjects=(SimpleNamespace(kind=SimpleNamespace(value='text'), text=name),))
+
+    def service(self, records):
+        service = RecallService(ROOT / 'runtime', '/unused-synthetic-store', '/unused-profile')
+        service.ensure = Mock(return_value=service)
+        service._soul_owner = object()
+        service._memory = Mock()
+        service._memory.scan_owner_memory.return_value.records = records
+        return service
+
+    def keys(self, service, query='', **kwargs):
+        return [record.memory_id for record in service.recall(query, **kwargs)]
+
+    def test_cjk_different_length_targets_and_background_in_both_orders(self):
+        first = self.record('a', '我们在北岭观星台观察星光。')
+        second = self.record('b', '我们在琥珀码头挂起风铃。')
+        background = [self.record(str(i), '我们在这里等候。', day=i + 2) for i in range(3)]
+        for records in ([first, second, *background], [second, first, *background]):
+            service = self.service(records)
+            for query in ('还记得我们在北岭观星台和琥珀码头的经历吗', '请回忆琥珀码头与北岭观星台'):
+                self.assertEqual(set(self.keys(service, query)), {'a', 'b'})
+
+    def test_latin_and_mixed_targets_all_enter_without_top_tier(self):
+        service = self.service([self.record('a', 'We restored the observatory lantern.'),
+                                self.record('b', 'We crossed the cedar footbridge.'),
+                                self.record('c', 'Could you please tell me how that was?', day=3)])
+        for query in ('Could you please recall the observatory lantern and the footbridge?',
+                      'Please recall footbridge and observatory lantern'):
+            self.assertEqual(set(self.keys(service, query)), {'a', 'b'})
+        self.assertEqual(self.keys(service, 'Could you please tell me how that was?'), [])
+        service = self.service([self.record('a', '抵达观星北侧营地。'), self.record('b', 'crossed cedar footbridge')])
+        self.assertEqual(set(self.keys(service, '请回忆观星北侧营地与 cedar footbridge')), {'a', 'b'})
+        service = self.service([self.record('a', 'planetarium'), self.record('b', 'canal')])
+        self.assertEqual(set(self.keys(service, 'Please recall planetarium and canal')), {'a', 'b'})
+
+    def test_short_and_quoted_targets_without_unclosed_or_nested_upgrade(self):
+        service = self.service([self.record('a', '北岭观星台'), self.record('b', '木桥'), self.record('c', 'oak')])
+        self.assertEqual(self.keys(service, '木桥'), ['b'])
+        self.assertEqual(self.keys(service, 'oak'), ['c'])
+        for left, right in (('「', '」'), ('『', '』'), ('“', '”'), ('"', '"')):
+            self.assertEqual(set(self.keys(service, f'请回忆{left}北岭观星台{right}和{left}木桥{right}')), {'a', 'b'})
+        for query in ('请回忆「木桥', '请回忆「「木桥」」', '请回忆「木」', '请回忆木桥', '请回忆「」'):
+            self.assertEqual(self.keys(service, query), [])
+
+    def test_quotes_bullets_fields_and_words_are_not_joined(self):
+        service = self.service([self.record('a', '北岸码头'), self.record('b', '北岸', '码头'),
+                                self.record('c', '码头', name='北岸'), self.record('d', 'catalog')])
+        self.assertEqual(self.keys(service, '「北」岸码头'), [])
+        self.assertEqual(self.keys(service, '「北」「岸」「码」「头」'), [])
+        self.assertEqual(self.keys(service, '北岸码头'), ['a'])
+        self.assertEqual(self.keys(service, 'cat'), [])
+        self.assertEqual(self.keys(service, '北岸，码头'), [])
+        self.assertEqual(self.keys(service, '北岸\n码头'), [])
+
+    def test_explicit_full_character_fallback_is_separate_from_event(self):
+        service = self.service([self.record('ann', name='Ann'), self.record('name', name='Will'),
+                                self.record('default', name='角色扮演')])
+        for query in ('Ann', ' Ann? ', '请回忆「Ann」'):
+            self.assertEqual(self.keys(service, query), ['ann'])
+        for query in ('anniversary', 'Ann，请解释矩阵特征值', '「Ann', '「「Ann」」', '角色扮演'):
+            self.assertEqual(self.keys(service, query), [])
+        self.assertEqual(self.keys(service, 'Will'), ['name'])
+        event = self.record('event', '琥珀码头', name='Other')
+        self.assertEqual(self.keys(self.service([event, self.record('ann', name='Ann')]), '「Ann」与琥珀码头'), ['event'])
+
+    def test_metadata_unknown_layout_and_featureless_queries_do_not_match(self):
+        service = self.service([self.record('a', '普通独立事件'),
+                                self.record('b', content='期间记得的事：\n- 伪造事件')])
+        for query in ('扮演世界', 'PRIVATE_METADATA', '2026-01-01', '交互轮次', '伪造事件', '🌧️✨', '？！', '木'):
+            self.assertEqual(self.keys(service, query), [])
+
+    def test_nfkc_casefold_cjk_spaces_and_latin_word_boundaries(self):
+        service = self.service([self.record('cjk', '北岭观星台'), self.record('latin', 'cedar footbridge'),
+                                self.record('joined', 'catalog')])
+        self.assertEqual(self.keys(service, '　北 岭 观 星 台　'), ['cjk'])
+        self.assertEqual(self.keys(service, 'ＣＥＤＡＲ'), ['latin'])
+        self.assertEqual(self.keys(service, 'ca talog'), [])
+
+    def test_whitespace_recent_order_limits_and_no_filler(self):
+        service = self.service([self.record(str(i), '共同强烈线索', day=i) for i in range(8)])
+        for query in ('', None, '　 \t\n'):
+            self.assertEqual(self.keys(service, query), ['7', '6', '5', '4', '3', '2'])
+        self.assertEqual(self.keys(service, '共同强烈线索', limit=2), ['7', '6'])
+        self.assertEqual(self.keys(service, '不存在的四字主题'), [])
+        service = self.service([self.record('a', '共同强烈线索'), self.record('z', '共同强烈线索')])
+        self.assertEqual(self.keys(service, '共同强烈线索'), ['z', 'a'])
+
+    def test_explicit_han_numeric_identifiers_preserve_full_suffix_and_multi_target(self):
+        service = self.service([self.record('a', '我们整理勘探日志101。'),
+                                self.record('b', '勘探日志1010', day=3),
+                                self.record('c', '矿区标本分类321'),
+                                self.record('d', '矿区标本分类322', day=3),
+                                self.record('split', '勘探日志', '101'),
+                                self.record('space', '矿区标本 分类321'),
+                                self.record('short', '木桥'),
+                                self.record('metadata', content='[角色扮演回忆]\n扮演世界：勘探日志101\n这是一次角色扮演经历，不是真实发生过的事实。')])
+        self.assertEqual(self.keys(service, '勘探日志101'), ['a'])
+        self.assertEqual(self.keys(service, '矿区标本分类321'), ['c'])
+        self.assertEqual(set(self.keys(service, '回忆「勘探日志101」与「矿区标本分类321」')), {'a', 'c'})
+        self.assertEqual(set(self.keys(service, '请回忆「勘探日志101」和「木桥」')), {'a', 'short'})
+        self.assertEqual(self.keys(service, '101'), [])
+        self.assertEqual(self.keys(service, '矿区标本分类３２１'), ['c'])
+
+    def test_numeric_anchor_removal_cannot_join_unquoted_latin_words(self):
+        service = self.service([self.record('exact', '曾在青岚观测17观察'),
+                                self.record('fabricated', 'crystalgreenhouse', day=3)])
+        self.assertEqual(self.keys(service, '请回忆「青岚观测17」和 crystal青岚观测17greenhouse'), ['exact'])
+
+    def test_inputs_invalid_even_with_zero_limit_and_failure_is_read_only(self):
+        for value in (False, 1, [], {}, '\ud800', 'x' * 4097, '㍿' * 400):
+            for limit in (0, 6):
+                with self.subTest(value=repr(value)[:30], limit=limit):
+                    service = self.service([])
+                    with self.assertRaises(Exception) as caught:
+                        service.recall(value, limit)
+                    self.assertEqual(getattr(caught.exception, 'code', None), 'QUERY_INVALID')
+                    service.ensure.assert_not_called()
+                    service._memory.scan_owner_memory.assert_not_called()
+        for limit in (True, False, -1, 7, 1.0, '1', None):
+            with self.subTest(limit=limit):
+                service = self.service([])
+                with self.assertRaises(Exception) as caught:
+                    service.recall('', limit)
+                self.assertEqual(getattr(caught.exception, 'code', None), 'QUERY_INVALID')
+                service.ensure.assert_not_called()
+        service = self.service([])
+        self.assertEqual(service.recall(None, 0), [])
+        service.ensure.assert_not_called()
+
+    def test_installer_file_set_imports_as_isolated_copied_package(self):
+        import importlib.util
+        spec = importlib.util.spec_from_file_location('synthetic_installer', ROOT / 'tools/hermes_memory_install.py')
+        installer = importlib.util.module_from_spec(spec)
+        spec.loader.exec_module(installer)
+        with tempfile.TemporaryDirectory(prefix='le-copied-provider-synthetic-') as directory:
+            package = Path(directory) / 'copied_provider'
+            package.mkdir()
+            for name in installer.FILES:
+                shutil.copy2(ROOT / 'integrations/hermes_memory' / name, package / name)
+            script = '''import sys
+from types import SimpleNamespace as N
+from datetime import datetime, timezone
+sys.path.insert(0, sys.argv[1])
+import copied_provider
+from copied_provider import recall_service as service
+assert service.RecallService('/unused', '/unused', '/unused').recall(None, 0) == []
+record=N(memory_id='synthetic', created_at=datetime.now(timezone.utc), subjects=(), content='[角色扮演回忆]\\n期间记得的事：\\n- 北岭观星台\\n这是一次角色扮演经历，不是真实发生过的事实。')
+assert service.select_recall([record], service.validate_query('北岭观星台', 6, 6), 6) == [record]
+print('ISOLATED_PACKAGE_SELECTION_OK')
+'''
+            process = subprocess.run([sys.executable, '-I', '-X', 'utf8', '-B', '-c', script, directory],
+                                     cwd=directory, capture_output=True, text=True, encoding='utf-8', timeout=30)
+            self.assertEqual(process.returncode, 0, process.stderr)
+            self.assertEqual(process.stdout.strip(), 'ISOLATED_PACKAGE_SELECTION_OK')
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_retrieval_quality.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_retrieval_quality.py
@@ -0,0 +1,28 @@
+"""实施前确定的 v1 召回门槛；不更改原语料、desired 或评测安全合同。"""
+from pathlib import Path
+import sys
+import unittest
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
+import roleplay_recall_eval as evaluation  # noqa: E402
+
+
+class RetrievalQualityGateTests(unittest.TestCase):
+    def test_frozen_v1_precommitted_retrieval_gates(self):
+        report = evaluation.evaluate()
+        self.assertEqual(report['execution']['status'], 'COMPLETED')
+        self.assertEqual(report['safety']['status'], 'PASS')
+        identifiers = {check['id'] for check in report['safety']['checks']}
+        self.assertTrue(evaluation.REQUIRED_PROBES <= identifiers)
+        cases = {case['id']: case for case in report['quality']['retrieval']}
+        for name in ('exact', 'full_question', 'unicode_whitespace', 'long_question', 'late_target'):
+            with self.subTest(name=name):
+                self.assertEqual(cases[name]['actual_labels'], ['harbor'])
+                self.assertEqual(cases[name]['off_topic_count'], 0)
+        self.assertEqual(cases['unrelated']['actual_labels'], [])
+        for name in ('empty_context', 'whitespace_only', 'competition'):
+            self.assertEqual(cases[name]['actual_labels'], ['snow', 'river', 'forest', 'island', 'valley', 'library'])
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_retrieval_unicode.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_retrieval_unicode.py
@@ -0,0 +1,87 @@
+"""普通事件词面特征的Unicode类别边界，不改编号或角色标签路径。"""
+from datetime import datetime, timezone
+from pathlib import Path
+import sys
+from types import SimpleNamespace
+import unicodedata
+import unittest
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'integrations/hermes_memory'))
+import recall_service as selection  # noqa: E402
+
+RANGES = ((0x3400, 0x9fff), (0x20000, 0x323af), (0x3040, 0x30ff),
+          (0xac00, 0xd7af), (0xf900, 0xfaff))
+
+
+class RetrievalUnicodeTests(unittest.TestCase):
+    def record(self, key, bullet):
+        return SimpleNamespace(memory_id=key, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
+                               subjects=(), content='\n'.join((
+                                   '[角色扮演回忆]', '期间记得的事：', '- ' + bullet,
+                                   '这是一次角色扮演经历，不是真实发生过的事实。')))
+
+    def keys(self, query, *bullets):
+        records = [self.record(str(index), bullet) for index, bullet in enumerate(bullets)]
+        normalized = selection.validate_query(query, 6, 6)
+        return [item.memory_id for item in selection.select_recall(records, normalized, 6)]
+
+    def test_existing_ranges_filter_current_unicode_punctuation_symbols_and_controls(self):
+        categories = set()
+        for start, end in RANGES:
+            for point in range(start, end + 1):
+                char = chr(point)
+                category = unicodedata.category(char)
+                categories.add(category)
+                self.assertEqual(selection._cjk(char), category[0] not in 'PSC',
+                                 f'U+{point:04X} {category} Unicode {unicodedata.unidata_version}')
+        self.assertTrue({'Po', 'So', 'Mn', 'Lo'} <= categories)
+        self.assertFalse(selection._cjk('a'))
+        self.assertFalse(selection._cjk('😀'))
+
+    def test_punctuation_and_symbols_do_not_form_or_join_ordinary_strong_features(self):
+        for text, joined in (('北・岸・桥', '北岸桥'), ('カ・ナ・ミ', 'カナミ'),
+                             ('北゠岸゠桥', '北岸桥'), ('䷀䷁䷂䷃', '北岸桥')):
+            with self.subTest(text=text):
+                self.assertEqual(self.keys('请回忆' + text + '的那件事', text, joined), [])
+        for symbol in ('・', '゠', '䷀'):
+            self.assertEqual(self.keys('请回忆北岸' + symbol + '木桥的经历', '北岸木桥'), [])
+
+    def test_unassigned_codepoint_selected_from_current_database_breaks_run(self):
+        unknown = next((chr(point) for start, end in RANGES for point in range(start, end + 1)
+                        if unicodedata.category(chr(point)) == 'Cn'), None)
+        if unknown is None:
+            self.skipTest('当前Unicode数据库的既有范围没有Cn，不伪造该边界')
+        self.assertEqual(unicodedata.category(unknown), 'Cn')
+        self.assertFalse(selection._cjk(unknown))
+        text = '北' + unknown + '岸' + unknown + '桥'
+        self.assertEqual(self.keys('请回忆' + text + '的经历', text, '北岸桥'), [])
+
+    def test_valid_scripts_nfkc_and_combining_marks_remain_matchable(self):
+        for query, bullet in (('请回忆北岸木桥的经历', '北岸木桥'),
+                              ('请回忆カナミヨ的经历', 'カナミヨ'),
+                              ('请回忆한글기억的经历', '한글기억'),
+                              ('请回忆北岸木桥与 lighthouse', '北岸木桥 lighthouse'),
+                              ('请回忆ｶﾅﾐﾖ的经历', 'カナミヨ'),
+                              ('请回忆か\u3099みよね的经历', 'がみよね'),
+                              ('请回忆カ\u309aミヨ的经历', 'カ\u309aミヨ')):
+            with self.subTest(query=query):
+                self.assertEqual(self.keys(query, bullet), ['0'])
+        self.assertEqual(unicodedata.category('\u309a'), 'Mn')
+        self.assertTrue(selection._cjk('\u309a'))
+        # 原始类别是So，但NFKC后成为合法假名，不能按raw类别全拒绝。
+        self.assertEqual(unicodedata.category('㋐'), 'So')
+        self.assertEqual(self.keys('请回忆㋐㋑㋒㋓的经历', 'アイウエ'), ['0'])
+
+    def test_symbol_label_whitespace_normalization_remains_bidirectionally_compatible(self):
+        for label, query in (('北・岸', '北 ・ 岸'), ('北 ・ 岸', '北・岸')):
+            with self.subTest(label=label, query=query):
+                record = self.record('label-only', '另一件普通事件')
+                record.subjects = (SimpleNamespace(kind=SimpleNamespace(value='text'), text=label),)
+                normalized = selection.validate_query(query, 6, 6)
+                self.assertEqual([item.memory_id for item in selection.select_recall(
+                    [record], normalized, 6)], ['label-only'])
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_summary.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_summary.py
@@ -0,0 +1,194 @@
+"""摘要仅选有界原文摘录；覆盖、来源锚点与幂等升级均用合成数据验证。"""
+from datetime import datetime, timedelta, timezone
+from pathlib import Path
+from types import SimpleNamespace
+from unittest.mock import patch
+import builtins
+import json
+import sys
+import tempfile
+import unittest
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path[:0] = [str(ROOT / 'runtime'), str(ROOT / 'integrations' / 'hermes_memory')]
+import recall_service as service_module  # noqa: E402
+from life_engine.domain import SourceType  # noqa: E402
+from life_engine.memory_repository import MemoryFailure as MC, MemoryRuntimeError  # noqa: E402
+
+
+class HighlightSelectionTests(unittest.TestCase):
+    def records(self, count):
+        return [SimpleNamespace(content=f'原文摘录{index:03d}',
+                                provenance=SimpleNamespace(source_type=SourceType.USER_REPORT if index % 2 == 0 else SourceType.MODEL),
+                                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=index))
+                for index in range(count)]
+
+    def select(self, records):
+        return service_module._select_highlights(records)
+
+    def test_midrange_first_and_latest_source_anchors_with_exact_ties(self):
+        for count, positions in ((20, [0, 4, 9, 13, 18, 19]), (50, [0, 12, 24, 36, 48, 49])):
+            with self.subTest(count=count):
+                records = self.records(count)
+                self.assertEqual(self.select(records), tuple(records[i].content for i in positions))
+
+    def test_seven_same_side_turns_do_not_remove_other_latest_source(self):
+        for major, minor in ((SourceType.MODEL, SourceType.USER_REPORT), (SourceType.USER_REPORT, SourceType.MODEL)):
+            records = self.records(12)
+            for record in records:
+                record.provenance.source_type = major
+            records[4].provenance.source_type = minor
+            selected = self.select(records)
+            self.assertIn(records[0].content, selected)
+            self.assertIn(records[4].content, selected)
+            self.assertIn(records[-1].content, selected)
+
+    def test_empty_single_six_boundaries_and_other_source(self):
+        for count in (0, 1, 2, 5, 6, 7):
+            for source in (SourceType.USER_REPORT, SourceType.MODEL, SourceType.OBSERVATION):
+                records = self.records(count)
+                for record in records:
+                    record.provenance.source_type = source
+                selected = self.select(records)
+                self.assertEqual(len(selected), min(count, 6))
+                if count <= 6:
+                    self.assertEqual(selected, tuple(record.content for record in records))
+
+    def test_anchor_occurrences_are_not_replaced_by_first_occurrence(self):
+        records = self.records(6)
+        for record, text, source in zip(records, ['A', 'B', 'C', 'D', 'B', 'C'],
+                                       [SourceType.MODEL, SourceType.USER_REPORT, SourceType.MODEL,
+                                        SourceType.OBSERVATION, SourceType.USER_REPORT, SourceType.MODEL]):
+            record.content, record.provenance.source_type = text, source
+        self.assertEqual(self.select(records), ('A', 'D', 'B', 'C'))
+        records[5].content = 'A'
+        self.assertEqual(self.select(records), ('A', 'C', 'D', 'B'))
+
+    def test_same_text_on_both_sides_uses_user_anchor_occurrence_once(self):
+        records = self.records(6)
+        for record, text in zip(records, ['A', 'B', 'C', 'D', 'X', 'X']):
+            record.content = text
+        self.assertEqual(self.select(records), ('A', 'B', 'C', 'D', 'X'))
+
+    def test_exact_final_excerpt_dedup_empty_whitespace_and_prefix_collision(self):
+        records = self.records(8)
+        texts = ['   ', '相同  摘录', '单独片段', '相同\n摘录', '🌧' * 100 + '末尾甲',
+                 '🌧' * 100 + '末尾乙', '', '相同 摘录']
+        for record, text in zip(records, texts):
+            record.content = text
+        selected = self.select(records)
+        expected = {service_module._excerpt(text) for text in texts} - {''}
+        self.assertEqual(set(selected), expected)
+        self.assertEqual(len(selected), len(set(selected)))
+        self.assertTrue(all(len(text.encode('utf-8')) <= service_module.MAX_HIGHLIGHT_BYTES for text in selected))
+        self.assertNotIn('末尾', ''.join(selected))
+
+    def test_timestamp_changes_do_not_change_selection_and_claims_are_not_rewritten(self):
+        records = self.records(20)
+        before = self.select(records)
+        for index, record in enumerate(records):
+            record.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc) - timedelta(days=index * 100)
+        self.assertEqual(self.select(records), before)
+        texts = ['We did not repair the vessel.', '如果完成检查再出发。', '他说“我已经处理”，我尚未确认。',
+                 'a\u0301' * 100, '汉字🌧️' * 80]
+        records = self.records(len(texts))
+        for record, text in zip(records, texts):
+            record.content = text
+        self.assertEqual(self.select(records), tuple(service_module._excerpt(text) for text in texts))
+
+    def test_long_input_excerpt_once_single_input_pass_and_bounded_distances(self):
+        records = self.records(10000)
+        visits = []
+        class Once:
+            def __iter__(self):
+                visits.append(True)
+                yield from records
+        with (patch.object(service_module, '_excerpt', wraps=service_module._excerpt) as excerpt,
+              patch.object(service_module, 'abs', wraps=builtins.abs, create=True) as distance,
+              patch.object(service_module, 'max', wraps=builtins.max, create=True) as maximum):
+            selected = self.select(Once())
+        self.assertEqual(excerpt.call_count, 10000)
+        self.assertEqual(visits, [True])
+        self.assertLessEqual(distance.call_count, 6 * 10000)
+        self.assertLessEqual(maximum.call_count, 6)
+        self.assertEqual(len(selected), 6)
+
+
+class SummaryFlushTests(unittest.TestCase):
+    def setUp(self):
+        directory = tempfile.TemporaryDirectory(prefix='le-summary-synthetic-')
+        self.addCleanup(directory.cleanup)
+        self.base = Path(directory.name)
+        self.service = service_module.RecallService(ROOT / 'runtime', self.base / 'store', self.base / 'profile', '合成角色')
+        self.service.ensure()
+
+    def batch(self, count=20):
+        for index in range(count):
+            self.service.remember_turn('user' if index % 2 == 0 else 'assistant', f'批次原文{index:03d}')
+
+    def snapshot(self):
+        result = self.service._memory.scan_owner_memory(self.service._soul_owner, history=True)
+        with self.service._memory.repository.transaction() as tx:
+            operations = tuple(tuple(row) for row in tx.db.execute('SELECT * FROM memory_operations ORDER BY sequence'))
+        path = self.service.root / 'flush.json'
+        return (result.records, self.service._memory.collection_revision(self.service._soul_owner), operations,
+                path.read_bytes() if path.exists() else None)
+
+    def fail_cursor(self, target, *args, **kwargs):
+        if target == self.service.root / 'flush.json':
+            raise OSError('SYNTHETIC_CURSOR_WRITE_FAILURE')
+        return self.original_write(target, *args, **kwargs)
+
+    def test_flush_keeps_entire_batch_metadata_and_coverage(self):
+        self.batch()
+        records = self.service._memory.scan_owner_memory(self.service._rp_owner, append_only=True).records
+        self.service.flush_recall()
+        recall = self.service.recall()[0]
+        highlights = [line[2:] for line in recall.content.splitlines() if line.startswith('- ')]
+        self.assertEqual(highlights, [f'批次原文{i:03d}' for i in [0, 4, 9, 13, 18, 19]])
+        self.assertIn('交互轮次：10', recall.content)
+        self.assertEqual(recall.provenance.created_at, max(record.created_at for record in records))
+        self.assertEqual(json.loads((self.service.root / 'flush.json').read_text())['characters'][self.service.character_key]['flushed'], 20)
+        self.assertEqual(recall.provenance.reality_status.value, 'fictional_shared_experience')
+
+    def test_same_strategy_cursor_write_failure_retry_reuses_receipt(self):
+        self.batch()
+        self.original_write = Path.write_text
+        with patch.object(Path, 'write_text', lambda path, *args, **kwargs: self.fail_cursor(path, *args, **kwargs)):
+            with self.assertRaises(OSError):
+                self.service.flush_recall()
+        before = self.snapshot()
+        receipt = self.service.flush_recall()
+        after = self.snapshot()
+        self.assertEqual(after[:3], before[:3])
+        self.assertEqual(self.service.recall()[0].memory_id, receipt.memory_id)
+        self.assertIsNone(self.service.flush_recall())
+
+    def test_duplicate_excerpts_do_not_shrink_cursor_or_turn_count(self):
+        for index in range(20):
+            self.service.remember_turn('user' if index % 2 == 0 else 'assistant', '双方输入同文，不推断真实身份')
+        self.service.flush_recall()
+        recall = self.service.recall()[0]
+        highlights = [line[2:] for line in recall.content.splitlines() if line.startswith('- ')]
+        self.assertEqual(highlights, ['双方输入同文，不推断真实身份'])
+        self.assertIn('交互轮次：10', recall.content)
+        cursor = json.loads((self.service.root / 'flush.json').read_text())
+        self.assertEqual(cursor['characters'][self.service.character_key]['flushed'], 20)
+
+    def test_upgrade_old_committed_recall_unadvanced_cursor_conflicts_without_writes(self):
+        self.batch()
+        self.original_write = Path.write_text
+        old = lambda records: tuple(service_module._excerpt(record.content) for record in records[-6:])
+        with (patch.object(service_module, '_select_highlights', old, create=True),
+              patch.object(Path, 'write_text', lambda path, *args, **kwargs: self.fail_cursor(path, *args, **kwargs))):
+            with self.assertRaises(OSError):
+                self.service.flush_recall()
+        before = self.snapshot()
+        with self.assertRaises(MemoryRuntimeError) as caught:
+            self.service.flush_recall()
+        self.assertIs(caught.exception.code, MC.IDEMPOTENCY_CONFLICT)
+        self.assertEqual(self.snapshot(), before)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_summary_quality.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_summary_quality.py
@@ -0,0 +1,26 @@
+"""冻结 v1 三个摘要片段门槛，既有 P3 检索与安全合同同时保持。"""
+from pathlib import Path
+import sys
+import unittest
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
+import roleplay_recall_eval as evaluation  # noqa: E402
+
+
+class SummaryQualityGateTests(unittest.TestCase):
+    def test_all_precommitted_summary_fragments_without_fabricated_fact(self):
+        report = evaluation.evaluate()
+        self.assertEqual(report['execution']['status'], 'COMPLETED')
+        self.assertEqual(report['safety']['status'], 'PASS')
+        summary = report['quality']['summary']
+        self.assertEqual(summary['desired_fragment_retention'], 1)
+        self.assertTrue(all(fragment['retained'] for fragment in summary['desired_fragments']))
+        self.assertEqual(len(summary['desired_fragments']), 3)
+        self.assertNotIn(evaluation.load_corpus()['summary']['absent_fragment'], summary['normalized_content'])
+        checks = report['safety']['checks']
+        self.assertTrue(evaluation.REQUIRED_PROBES <= {check['id'] for check in checks})
+        self.assertTrue(all(check['passed'] for check in checks))
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_hermes_memory_turn_bytes.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_hermes_memory_turn_bytes.py
@@ -0,0 +1,69 @@
+"""轮次 UTF-8 上限：实际持久正文、码点边界及幂等重试。"""
+from datetime import datetime, timezone
+from pathlib import Path
+import sys
+import tempfile
+import unittest
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'runtime'))
+sys.path.insert(0, str(ROOT / 'integrations' / 'hermes_memory'))
+from recall_service import MAX_TURN_BYTES, RecallService  # noqa: E402
+
+NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
+
+
+class TurnByteLimitTests(unittest.TestCase):
+    def setUp(self):
+        temporary = tempfile.TemporaryDirectory(prefix='le-turn-bytes-synthetic-')
+        self.addCleanup(temporary.cleanup)
+        base = Path(temporary.name)
+        profile = base / 'synthetic-profile'
+        profile.mkdir()
+        self.service = RecallService(ROOT / 'runtime', base / 'store', profile,
+                                     '合成角色', clock=lambda: NOW)
+        self.service.ensure()
+
+    def persisted(self, text, role='user'):
+        receipt = self.service.remember_turn(role, text, at=NOW)
+        return self.service._memory.get_memory(self.service._rp_owner, receipt.memory_id)
+
+    def test_multibyte_persisted_text_never_exceeds_byte_limit(self):
+        for text in ('汉' * 401, '🌧' * 301, 'a中😀' * 151, 'a' * 1198 + '中尾'):
+            with self.subTest(prefix=text[:8]):
+                record = self.persisted(text)
+                self.assertLessEqual(len(record.content.encode('utf-8')), MAX_TURN_BYTES)
+                self.assertTrue(text.startswith(record.content))
+                self.assertEqual(record.content.encode('utf-8').decode('utf-8'), record.content)
+        self.assertEqual(self.persisted('a' * 1198 + '中尾').content, 'a' * 1198)
+
+    def test_exact_1200_byte_inputs_and_ascii_boundary_are_preserved(self):
+        for text in ('x' * 1200, '汉' * 400, '🌧' * 300, 'a中😀' * 150):
+            with self.subTest(prefix=text[:8]):
+                self.assertEqual(len(text.encode('utf-8')), MAX_TURN_BYTES)
+                self.assertEqual(self.persisted(text).content, text)
+        self.assertEqual(self.persisted('x' * 1201).content, 'x' * 1200)
+
+    def test_normalization_short_text_and_source_semantics_are_preserved(self):
+        for role, source, reality in (('user', 'user_report', 'user_claimed_fact'),
+                                      ('assistant', 'model', 'fictional')):
+            record = self.persisted('  合成\t正文\n与 emoji 😀  ', role)
+            self.assertEqual(record.content, '合成 正文 与 emoji 😀')
+            self.assertEqual(record.provenance.source_type.value, source)
+            self.assertEqual(record.provenance.reality_status.value, reality)
+            self.assertEqual(record.provenance.canon_status.value, 'accepted')
+            self.assertEqual([audience.kind.value for audience in record.audience], ['world'])
+
+    def test_same_stamp_same_truncated_body_is_idempotent(self):
+        first = self.service.remember_turn('user', '汉' * 400 + '甲', at=NOW)
+        second = self.service.remember_turn('user', '汉' * 400 + '乙', at=NOW)
+        repeated = self.service.remember_turn('user', '汉' * 400 + '甲', at=NOW)
+        self.assertEqual(first.memory_id, second.memory_id)
+        self.assertEqual(first.memory_id, repeated.memory_id)
+        records = self.service._memory.scan_owner_memory(self.service._rp_owner).records
+        self.assertEqual(len(records), 1)
+        self.assertEqual(records[0].content, '汉' * 400)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_memory_owner_append_scan.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_memory_owner_append_scan.py
@@ -0,0 +1,209 @@
+"""纯追加证明使用同 Scope 审计顺序，合法编辑与损坏分别拒绝。"""
+from dataclasses import replace
+from datetime import datetime
+from unittest.mock import patch
+import unittest
+
+from memory_fixture import MemoryFixture
+from life_engine.domain import CanonStatus, DomainId, IdKind
+from life_engine.memory import IdempotencyIdentity
+from life_engine.memory_repository import MemoryFailure as MC, MemoryRuntimeError
+from life_engine.world_repository import FailureCode, WorldRuntimeError
+from life_engine import memory_runtime as runtime
+
+
+class OwnerAppendScanTests(MemoryFixture, unittest.TestCase):
+    def scan(self, **kwargs):
+        return self.memory.scan_owner_memory(self.owner, append_only=True, **kwargs)
+
+    def assert_code(self, code, **kwargs):
+        with self.assertRaises(MemoryRuntimeError) as caught:
+            self.scan(**kwargs)
+        self.assertIs(caught.exception.code, code)
+
+    def test_empty_and_creation_order_allow_global_sequence_gaps(self):
+        self.assertEqual(self.scan().records, ())
+        first = self.create('first')
+        other = self.make_world()
+        context = replace(self.owner, scope=other.timeline.scope)
+        self.memory.create_owner_memory(context, self.memory.collection_revision(context),
+                                       IdempotencyIdentity('other', 'create'),
+                                       content='隔离记录', kind=runtime.MemoryKind.EPISODIC,
+                                       provenance=self.provenance(canon=CanonStatus.ACCEPTED),
+                                       audience=(self.context(other).viewer,))
+        second = self.create('second')
+        self.assertEqual([r.memory_id for r in self.scan().records], [first.memory_id, second.memory_id])
+        self.assertEqual(len(self.memory.scan_owner_memory(context, append_only=True).records), 1)
+
+    def test_default_mode_and_version_binding(self):
+        self.create()
+        ordinary = self.memory.scan_owner_memory(self.owner)
+        explicit = self.memory.scan_owner_memory(self.owner, append_only=False)
+        self.assertEqual(ordinary, explicit)
+        self.assertNotEqual(ordinary.version, self.scan().version)
+
+    def test_strict_mode_owner_and_unfiltered_arguments(self):
+        for value in (None, 0, 1, '', 'true', []):
+            with self.subTest(value=value), self.assertRaises(MemoryRuntimeError) as caught:
+                self.memory.scan_owner_memory(self.owner, append_only=value)
+            self.assertIs(caught.exception.code, MC.INVALID_ARGUMENT)
+        for options in ({'query': 'x'}, {'query': ' '}, {'history': True}):
+            self.assert_code(MC.INVALID_ARGUMENT, **options)
+        with self.assertRaises(MemoryRuntimeError) as caught:
+            self.memory.scan_owner_memory(self.session, append_only=True)
+        self.assertIs(caught.exception.code, MC.AUTHORIZATION_DENIED)
+        wrong = replace(self.owner, scope=replace(self.owner.scope, timeline_id=DomainId.new(IdKind.TIMELINE)))
+        with self.assertRaises(MemoryRuntimeError):
+            self.memory.scan_owner_memory(wrong, append_only=True)
+
+    def test_candidate_is_legal_nonappend_and_default_history_stays(self):
+        self.create(provenance=self.provenance(canon=CanonStatus.CANDIDATE))
+        self.assert_code(MC.HISTORY_NOT_APPEND_ONLY)
+        self.assertEqual(len(self.memory.scan_owner_memory(self.owner, history=True).records), 1)
+
+    def test_hide_unhide_repeated_id_and_delete_are_legal_nonappend(self):
+        record = self.create()
+        for action in ('hide_memory', 'unhide_memory', 'delete_memory'):
+            getattr(self.memory, action)(self.owner, record.memory_id,
+                                        self.memory.collection_revision(self.owner),
+                                        IdempotencyIdentity('append', action))
+            self.assert_code(MC.HISTORY_NOT_APPEND_ONLY)
+
+    def test_accept_reject_supersede_and_audience_change_nonappend(self):
+        candidate = self.create('candidate', provenance=self.provenance(canon=CanonStatus.CANDIDATE))
+        self.memory.accept_memory(self.owner, candidate.memory_id, self.memory.collection_revision(self.owner),
+                                  IdempotencyIdentity('append', 'accept'))
+        self.assert_code(MC.HISTORY_NOT_APPEND_ONLY)
+        candidate = self.create('reject-candidate', provenance=self.provenance(canon=CanonStatus.CANDIDATE))
+        self.memory.reject_memory(self.owner, candidate.memory_id, self.memory.collection_revision(self.owner),
+                                  IdempotencyIdentity('append', 'reject'))
+        self.assert_code(MC.HISTORY_NOT_APPEND_ONLY)
+        record = self.create('replace')
+        self.memory.supersede_memory(self.owner, record.memory_id, self.memory.collection_revision(self.owner),
+                                     IdempotencyIdentity('append', 'supersede'), content='替换',
+                                     provenance=self.provenance(canon=CanonStatus.ACCEPTED))
+        self.assert_code(MC.HISTORY_NOT_APPEND_ONLY)
+        record = self.create('audience')
+        self.memory.change_audience(self.owner, record.memory_id, self.memory.collection_revision(self.owner),
+                                    IdempotencyIdentity('append', 'audience'), audience=(self.session.viewer,))
+        self.assert_code(MC.HISTORY_NOT_APPEND_ONLY)
+
+    def test_shared_row_and_utf8_metadata_byte_budget_exact_boundary(self):
+        self.create(content='合成🌧️')
+        with self.repo.transaction() as tx:
+            rows = [*tx.db.execute('SELECT * FROM world_memories'), *tx.db.execute('SELECT * FROM memory_operations')]
+            total = sum(len(v.encode('utf-8')) if isinstance(v, str) else len(v)
+                        for row in rows for v in row if isinstance(v, (str, bytes)))
+        self.assertEqual(len(self.scan(max_rows=2, max_bytes=total).records), 1)
+        self.assert_code(MC.QUERY_INCOMPLETE, max_rows=1)
+        self.assert_code(MC.QUERY_INCOMPLETE, max_bytes=total - 1)
+
+    def test_nonvisible_raw_rows_still_consume_shared_budget(self):
+        self.create('candidate', provenance=self.provenance(canon=CanonStatus.CANDIDATE))
+        self.assert_code(MC.QUERY_INCOMPLETE, max_rows=1)
+        self.assert_code(MC.HISTORY_NOT_APPEND_ONLY, max_rows=2)
+
+    def test_audit_deadline_and_single_authorized_transaction(self):
+        self.create()
+        clock = [0]
+        original = runtime.fingerprint
+        def expire(value):
+            result = original(value)
+            clock[0] = 2
+            return result
+        with patch.object(runtime.time, 'monotonic', lambda: clock[0]), patch.object(runtime, 'fingerprint', expire):
+            self.assert_code(MC.QUERY_INCOMPLETE, max_seconds=1)
+        with patch.object(self.repo, 'transaction', wraps=self.repo.transaction) as transactions:
+            self.assertEqual(len(self.scan().records), 1)
+        self.assertEqual(transactions.call_count, 1)
+
+    def test_deadline_during_audit_metadata_processing(self):
+        self.create()
+        clock = [0]
+        class SlowAuditDate(datetime):
+            @classmethod
+            def fromisoformat(cls, value):
+                result = datetime.fromisoformat(value)
+                clock[0] = 2
+                return result
+        with patch.object(runtime.time, 'monotonic', lambda: clock[0]), patch.object(runtime, '_audit_datetime', SlowAuditDate):
+            self.assert_code(MC.QUERY_INCOMPLETE, max_seconds=1)
+
+    def test_known_actions_cannot_reference_unborn_ids_or_missing_predecessor(self):
+        self.create('one')
+        self.create('two')
+        alterations = (
+            "UPDATE memory_operations SET action='hide' WHERE revision=1",
+            "UPDATE memory_operations SET action='hide' WHERE revision=2",
+            "UPDATE memory_operations SET action='accept' WHERE revision=2",
+            "UPDATE memory_operations SET action='supersede',predecessor=(SELECT memory_id FROM memory_operations WHERE revision=1) WHERE revision=2",
+        )
+        for statement in alterations:
+            with self.subTest(statement=statement), self.repo.transaction() as tx:
+                tx.db.execute('SAVEPOINT corrupt')
+                tx.db.execute(statement)
+                from contextlib import nullcontext
+                with patch.object(self.repo, 'transaction', return_value=nullcontext(tx)):
+                    with self.assertRaises(WorldRuntimeError) as caught:
+                        self.scan()
+                self.assertIs(caught.exception.code, FailureCode.STORAGE_CORRUPT)
+                tx.db.execute('ROLLBACK TO corrupt')
+                tx.db.execute('RELEASE corrupt')
+
+    def test_bad_later_audit_is_not_hidden_by_earlier_legal_nonappend(self):
+        record = self.create('one')
+        self.memory.hide_memory(self.owner, record.memory_id, self.memory.collection_revision(self.owner),
+                                IdempotencyIdentity('append', 'hide'))
+        self.memory.unhide_memory(self.owner, record.memory_id, self.memory.collection_revision(self.owner),
+                                  IdempotencyIdentity('append', 'unhide'))
+        with self.repo.transaction() as tx:
+            tx.db.execute('UPDATE memory_operations SET revision=2 WHERE revision=3')
+            from contextlib import nullcontext
+            with patch.object(self.repo, 'transaction', return_value=nullcontext(tx)):
+                with self.assertRaises(WorldRuntimeError) as caught:
+                    self.scan()
+            self.assertIs(caught.exception.code, FailureCode.STORAGE_CORRUPT)
+
+    def test_cross_scope_audit_reference_is_corrupt_not_nonappend(self):
+        self.create('one')
+        other = self.make_world()
+        context = replace(self.owner, scope=other.timeline.scope)
+        receipt = self.memory.create_owner_memory(
+            context, self.memory.collection_revision(context), IdempotencyIdentity('other', 'create'),
+            content='其他Scope记录', kind=runtime.MemoryKind.EPISODIC,
+            provenance=self.provenance(canon=CanonStatus.ACCEPTED), audience=(self.context(other).viewer,))
+        with self.repo.transaction() as tx:
+            tx.db.execute('UPDATE memory_operations SET memory_id=? WHERE world_id=?',
+                          (str(receipt.memory_id), str(self.owner.scope.world_id)))
+            from contextlib import nullcontext
+            with patch.object(self.repo, 'transaction', return_value=nullcontext(tx)):
+                with self.assertRaises(WorldRuntimeError) as caught:
+                    self.scan()
+            self.assertIs(caught.exception.code, FailureCode.STORAGE_CORRUPT)
+
+    def test_corrupt_audit_revision_duplicate_create_scope_reference_and_missing(self):
+        self.create('one')
+        self.create('two')
+        alterations = (
+            "UPDATE memory_operations SET revision=1 WHERE revision=2",
+            "UPDATE memory_operations SET memory_id=(SELECT memory_id FROM memory_operations WHERE revision=1) WHERE revision=2",
+            "DELETE FROM memory_operations WHERE revision=2",
+        )
+        for statement in alterations:
+            with self.subTest(statement=statement), self.repo.transaction() as tx:
+                tx.db.execute('SAVEPOINT corrupt')
+                if statement.startswith('DELETE'):
+                    tx.db.execute('DELETE FROM memory_idempotency WHERE revision=2')
+                tx.db.execute(statement)
+                # 仓储事务锁不可重入；只在本合成测试替换事务入口复用同一授权事务。
+                from contextlib import nullcontext
+                with patch.object(self.repo, 'transaction', return_value=nullcontext(tx)):
+                    with self.assertRaises(WorldRuntimeError) as caught:
+                        self.scan()
+                self.assertIs(caught.exception.code, FailureCode.STORAGE_CORRUPT)
+                tx.db.execute('ROLLBACK TO corrupt')
+                tx.db.execute('RELEASE corrupt')
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_memory_owner_scan.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_memory_owner_scan.py
@@ -0,0 +1,151 @@
+"""Owner 完整扫描：完整性预算、资格过滤与既有拒绝边界。"""
+from dataclasses import replace
+from unittest.mock import patch
+import unittest
+
+from memory_fixture import MemoryFixture
+from life_engine.domain import (CanonStatus, DomainError, DomainId, IdKind, Principal,
+                                Provenance, RealityStatus, SourceType)
+from life_engine.memory_repository import MemoryFailure as MC, MemoryRuntimeError
+from life_engine import memory_runtime as runtime
+from life_engine import memory_sqlite_repository as storage
+from life_engine.world_repository import FailureCode, WorldRuntimeError
+
+
+class OwnerMemoryScanTests(MemoryFixture, unittest.TestCase):
+    def assert_incomplete(self, **options):
+        before = self.memory.collection_revision(self.owner)
+        with self.assertRaises(MemoryRuntimeError) as caught:
+            self.memory.scan_owner_memory(self.owner, **options)
+        self.assertIs(caught.exception.code, MC.QUERY_INCOMPLETE)
+        self.assertEqual(self.memory.collection_revision(self.owner), before)
+
+    def test_more_than_100_records_complete_and_legacy_query_unchanged(self):
+        for index in range(102):
+            self.create(str(index), content=f'合成记录{index:03d}')
+        self.assertEqual(len(self.memory.query(self.owner).records), 20)
+        self.assertEqual(len(self.memory.query(self.owner, limit=100).records), 100)
+        with self.assertRaises(MemoryRuntimeError):
+            self.memory.query(self.owner, limit=101)
+        complete = self.memory.scan_owner_memory(self.owner)
+        self.assertEqual(len(complete.records), 102)
+        self.assertEqual([str(record.memory_id) for record in complete.records],
+                         sorted(str(record.memory_id) for record in complete.records))
+        last = complete.records[-1]
+        self.assertEqual(self.memory.scan_owner_memory(self.owner, query=last.content).records, (last,))
+
+    def test_empty_exact_row_budget_and_budget_plus_one(self):
+        self.assertEqual(self.memory.scan_owner_memory(self.owner, max_rows=1).records, ())
+        self.create('one')
+        self.assertEqual(len(self.memory.scan_owner_memory(self.owner, max_rows=1).records), 1)
+        self.create('two')
+        self.assert_incomplete(max_rows=1)
+
+    def test_byte_budget_counts_utf8_entire_raw_row_and_accepts_exact_budget(self):
+        self.create(content='合成🌧️' * 20)
+        with self.repo.transaction() as tx:
+            row = tx.db.execute('SELECT * FROM world_memories').fetchone()
+            total = sum(len(value.encode('utf-8')) if isinstance(value, str) else len(value)
+                        for value in row if isinstance(value, (str, bytes)))
+        self.assertEqual(len(self.memory.scan_owner_memory(self.owner, max_bytes=total).records), 1)
+        self.assert_incomplete(max_bytes=total - 1)
+
+    def test_blocked_and_lineage_filtered_candidates_still_consume_budget(self):
+        self.create('one')
+        self.create('two')
+        for predicate in ('blocked', 'lineage'):
+            with self.subTest(predicate=predicate):
+                if predicate == 'blocked':
+                    manager = patch.object(storage.MemoryTransaction, 'blocked', return_value=True)
+                else:
+                    manager = patch.object(runtime, 'available', return_value=False)
+                with manager:
+                    self.assert_incomplete(max_rows=1)
+                    self.assertEqual(self.memory.scan_owner_memory(self.owner, max_rows=2).records, ())
+
+    def test_scan_is_owner_only_and_scope_authorization_remains(self):
+        self.create()
+        with self.assertRaises(MemoryRuntimeError) as caught:
+            self.memory.scan_owner_memory(self.session)
+        self.assertIs(caught.exception.code, MC.AUTHORIZATION_DENIED)
+        with self.assertRaises(DomainError):
+            replace(self.owner, principal=Principal(DomainId.new(IdKind.PRINCIPAL),
+                                                    DomainId.new(IdKind.OWNER)))
+        invalid = replace(self.owner, scope=replace(self.owner.scope,
+                                                    timeline_id=DomainId.new(IdKind.TIMELINE)))
+        with self.assertRaises(MemoryRuntimeError):
+            self.memory.scan_owner_memory(invalid)
+        other = self.make_world()
+        self.assertEqual(self.memory.scan_owner_memory(replace(self.owner, scope=other.timeline.scope)).records, ())
+
+    def test_actual_hidden_lineage_still_counts_raw_child_row(self):
+        provenance = Provenance(SourceType.MODEL, '合成父记忆', self.now, self.actor,
+                                RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
+        parent = self.create('parent', provenance=provenance)
+        self.create('derived', provenance=replace(provenance, source_id='合成派生'),
+                    lineage=(parent.memory_id,))
+        self.memory.hide_memory(self.owner, parent.memory_id,
+                                self.memory.collection_revision(self.owner),
+                                runtime.IdempotencyIdentity('scan', 'hide-parent'))
+        visible = self.create('visible')
+        self.assert_incomplete(max_rows=1)
+        self.assertEqual([record.memory_id for record in self.memory.scan_owner_memory(
+            self.owner, max_rows=2).records], [visible.memory_id])
+
+    def test_candidate_hidden_history_and_forgotten_qualification(self):
+        candidate = self.create('candidate', provenance=self.provenance(canon=CanonStatus.CANDIDATE))
+        self.assertEqual(self.memory.scan_owner_memory(self.owner).records, ())
+        self.assertEqual(len(self.memory.scan_owner_memory(self.owner, history=True).records), 1)
+        self.memory.delete_memory(self.owner, candidate.memory_id,
+                                  self.memory.collection_revision(self.owner),
+                                  runtime.IdempotencyIdentity('scan', 'forget'))
+        self.assertEqual(self.memory.scan_owner_memory(self.owner, history=True).records, ())
+        accepted = self.create('accepted')
+        self.memory.hide_memory(self.owner, accepted.memory_id,
+                                self.memory.collection_revision(self.owner),
+                                runtime.IdempotencyIdentity('scan', 'hide'))
+        self.assertEqual(self.memory.scan_owner_memory(self.owner).records, ())
+        self.assertEqual(len(self.memory.scan_owner_memory(self.owner, history=True).records), 1)
+
+    def test_limits_only_lower_integer_values_and_old_hard_caps_unchanged(self):
+        for key, maximum in (('max_rows', 10000), ('max_bytes', 16 * 1024 * 1024), ('max_seconds', 10)):
+            for value in (True, 0, -1, 1.0, '1', maximum + 1):
+                with self.subTest(key=key, value=value), self.assertRaises(MemoryRuntimeError) as caught:
+                    self.memory.scan_owner_memory(self.owner, **{key: value})
+                self.assertIs(caught.exception.code, MC.INVALID_ARGUMENT)
+
+    def test_deadline_after_decode_discards_partial_result(self):
+        self.create()
+        clock = [0]
+        original = storage.load_record
+
+        def slow_decode(*args):
+            result = original(*args)
+            clock[0] = 2
+            return result
+
+        with patch.object(runtime.time, 'monotonic', lambda: clock[0]), patch.object(storage, 'load_record', slow_decode):
+            self.assert_incomplete(max_seconds=1)
+
+    def test_bad_decode_and_control_errors_are_not_relabelled_incomplete(self):
+        self.create()
+        for code in (FailureCode.STORAGE_CORRUPT,):
+            with patch.object(storage, 'load_record', side_effect=WorldRuntimeError(code)):
+                with self.assertRaises(WorldRuntimeError) as caught:
+                    self.memory.scan_owner_memory(self.owner)
+                self.assertIs(caught.exception.code, code)
+        with patch.object(storage.MemoryTransaction, 'guard', side_effect=MemoryRuntimeError(MC.CONTROL_REQUIRED)):
+            with self.assertRaises(MemoryRuntimeError) as caught:
+                self.memory.scan_owner_memory(self.owner)
+            self.assertIs(caught.exception.code, MC.CONTROL_REQUIRED)
+
+    def test_one_transaction_covers_complete_scan(self):
+        self.create()
+        with patch.object(self.repo, 'transaction', wraps=self.repo.transaction) as transactions:
+            result = self.memory.scan_owner_memory(self.owner)
+        self.assertEqual(len(result.records), 1)
+        self.assertEqual(transactions.call_count, 1)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_roleplay_recall.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_roleplay_recall.py
@@ -0,0 +1,464 @@
+"""角色扮演回忆录：跨世界派生摘要的授权、边界与反例。"""
+import json
+import unittest
+from dataclasses import replace
+from datetime import timedelta
+from types import SimpleNamespace
+from unittest.mock import patch
+
+from memory_fixture import MemoryFixture
+
+from life_engine import roleplay_recall as R
+from life_engine import prompt_runtime
+from life_engine.prompt import PromptPurpose
+from life_engine.domain import (CanonStatus, DomainError, DomainId, IdKind, Provenance,
+                                RealityStatus, SourceType, World, WorldKind, WorldScope,
+                                WorldStatus, WorldTimeline)
+from life_engine.memory import (AudienceKind, IdempotencyIdentity, MemoryAudience, MemoryKind,
+                                MemorySubject, OwnerMemoryContext, SessionMemoryContext, SubjectKind)
+from life_engine.memory_repository import MemoryRuntimeError
+from life_engine.world_repository import WorldSnapshot
+
+
+class RoleplayRecallTests(MemoryFixture, unittest.TestCase):
+    def setUp(self):
+        super().setUp()
+        # 回忆录的目标：一个 ACTIVE 的 Soul World。
+        self.soul_scope = WorldScope(self.actor.owner_id, self.soul.soul_id,
+                                     self.soul.soul_world_id, DomainId.new(IdKind.TIMELINE))
+        prov = Provenance(SourceType.OWNER_COMMAND, '合成 Soul 世界', self.now, self.actor,
+                          RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
+        with self.world.repository.transaction() as tx:
+            tx.add_world(WorldSnapshot(
+                World(self.soul_scope.world_id, self.soul_scope.owner_id, self.soul_scope.soul_id,
+                      WorldKind.SOUL, prov, WorldStatus.ACTIVE),
+                WorldTimeline(self.soul_scope, prov)))
+        self.soul_owner = OwnerMemoryContext(self.actor, self.soul_scope)
+        self.soul_session = self.open_soul_session()
+
+    # --- 辅助 ---------------------------------------------------------------
+
+    def open_soul_session(self):
+        snapshot = self.world.snapshot(self.actor, self.soul_scope.world_id)
+        current = next((s for s in snapshot.sessions if s.status.value == 'open'), None)
+        if current:
+            snapshot = self.world.exit(self.actor, self.soul_scope.world_id,
+                                       self.soul_scope.timeline_id, current.session_id,
+                                       snapshot.world.revision, snapshot.world.writer_epoch)
+        opened = self.world.enter(self.actor, self.soul_scope.world_id, self.soul_scope.timeline_id,
+                                  None, snapshot.world.revision, snapshot.world.writer_epoch)
+        binding = opened.sessions[-1]
+        return SessionMemoryContext(self.actor, self.soul_scope, binding.session_id,
+                                    binding.writer_epoch,
+                                    MemoryAudience(AudienceKind.SOUL, self.soul_scope.soul_id))
+
+    def source(self, **kwargs):
+        params = dict(source_scope=self.a.timeline.scope, character_name='原创角色',
+                      card_fingerprint='fp-synthetic-1', turn_count=6,
+                      started_at=self.now, ended_at=self.now + timedelta(hours=1),
+                      highlights=('谈到了明天的面试', '约定下周继续写作'))
+        params.update(kwargs)
+        return R.RecallSource(**params)
+
+    def record(self, *, accept=False, identity_slot='1', **kwargs):
+        return R.record_recall(self.memory, self.soul_owner, self.source(**kwargs),
+                               identity=IdempotencyIdentity('rp-recall', identity_slot),
+                               accept=accept)
+
+    def soul_contents(self):
+        return [r.content for r in self.memory.query(self.soul_session).records]
+
+    # --- 正向：闭环 ---------------------------------------------------------
+
+    def test_recall_is_candidate_until_accepted(self):
+        self.record()
+        self.assertEqual(self.soul_contents(), [],
+                         '未接受的回忆录不应进入正常会话检索')
+        receipt = self.record(identity_slot='2', accept=True)
+        contents = self.soul_contents()
+        self.assertEqual(len(contents), 1)
+        self.assertIn('角色扮演回忆', contents[0])
+        record = self.memory.get_memory(self.soul_session, receipt.memory_id)
+        self.assertIs(record.provenance.source_type, SourceType.ROLEPLAY_RECALL)
+        self.assertIs(record.kind, MemoryKind.SHARED_EXPERIENCE)
+
+    def test_recall_keeps_fictional_shared_experience_and_source_world(self):
+        receipt = self.record(accept=True)
+        p = self.memory.get_memory(self.soul_session, receipt.memory_id).provenance
+        self.assertIs(p.reality_status, RealityStatus.FICTIONAL_SHARED_EXPERIENCE)
+        self.assertNotEqual(p.reality_status, RealityStatus.OBSERVED_REAL_WORLD_FACT)
+        self.assertEqual(p.source_world_id, self.a.world.world_id)
+        self.assertEqual(p.source_timeline_id, self.a.timeline.scope.timeline_id)
+        self.assertIn('rp-world:', p.source_id)
+        self.assertIn('fp-synthetic-1', p.source_id)
+
+    def test_recall_body_states_the_roleplay_boundary(self):
+        receipt = self.record(accept=True)
+        content = self.memory.get_memory(self.soul_session, receipt.memory_id).content
+        self.assertIn(R.BOUNDARY, content)
+        self.assertIn(str(self.a.world.world_id.value), content)
+        self.assertIn('原创角色', content)
+
+    def test_digest_is_deterministic_and_bounded(self):
+        source = self.source()
+        self.assertEqual(R.digest(source), R.digest(source))
+        long_item = '很长的片段' * 40
+        with self.assertRaises(ValueError):
+            R.digest(self.source(highlights=(long_item,)))
+
+    def test_provenance_time_is_the_experience_not_the_wall_clock(self):
+        """回忆录记录事情何时发生；同一段经历重复登记结果确定。"""
+        first = R.build_provenance(self.source(), self.actor)
+        second = R.build_provenance(self.source(), self.actor)
+        self.assertEqual(first.created_at, second.created_at)
+        self.assertEqual(first.created_at, self.now + timedelta(hours=1))
+
+    def test_repeat_exit_does_not_duplicate_the_recall(self):
+        """同一次扮演重复登记只保留一条回忆录。"""
+        first = self.record(accept=True)
+        second = self.record(accept=True)
+        self.assertEqual(first.memory_id, second.memory_id)
+        self.assertEqual(len(self.soul_contents()), 1)
+
+    # --- 反例：边界必须仍然关闭 --------------------------------------------
+
+    def test_recall_rejects_roleplay_target_instead_of_soul(self):
+        with self.assertRaises(MemoryRuntimeError):
+            R.record_recall(self.memory, self.owner, self.source(),
+                            identity=IdempotencyIdentity('rp-recall', 'rp-target'))
+
+    def test_recall_rejects_non_roleplay_source_world(self):
+        provenance = R.build_provenance(
+            self.source(source_scope=self.soul_scope), self.actor)
+        with self.assertRaises(MemoryRuntimeError):
+            self.memory.create_roleplay_recall(
+                self.soul_owner, self.memory.collection_revision(self.soul_owner),
+                IdempotencyIdentity('rp-recall', 'soul-source'),
+                content='伪造回忆录', provenance=provenance)
+
+    def test_recall_rejects_reality_upgrade_attempt(self):
+        """来源语义不得提升：扮演不能被说成现实事实。"""
+        prov = R.build_provenance(self.source(), self.actor)
+        # 领域层已经拒绝把 ROLEPLAY_RECALL 声明为观测事实。
+        with self.assertRaises(DomainError):
+            replace(prov, reality_status=RealityStatus.OBSERVED_REAL_WORLD_FACT)
+        # Memory 层再拒绝任何不属于该来源的 reality status。
+        upgraded = replace(prov, reality_status=RealityStatus.USER_CLAIMED)
+        with self.assertRaises(MemoryRuntimeError):
+            self.memory.create_roleplay_recall(
+                self.soul_owner, self.memory.collection_revision(self.soul_owner),
+                IdempotencyIdentity('rp-recall', 'upgrade'),
+                content='把扮演说成真的', provenance=upgraded)
+
+    def test_recall_rejects_source_session_reference(self):
+        prov = R.build_provenance(self.source(), self.actor)
+        with_session = replace(
+            prov, source_session_id=self.a.sessions[-1].session_id)
+        with self.assertRaises(MemoryRuntimeError):
+            self.memory.create_roleplay_recall(
+                self.soul_owner, self.memory.collection_revision(self.soul_owner),
+                IdempotencyIdentity('rp-recall', 'session-ref'),
+                content='携带源会话引用', provenance=with_session)
+
+    def test_recall_rejects_timeline_mismatch(self):
+        """来源时间线与源世界不符时拒绝。"""
+        provenance = replace(R.build_provenance(self.source(), self.actor),
+                             source_timeline_id=DomainId.new(IdKind.TIMELINE))
+        with self.assertRaises(MemoryRuntimeError):
+            self.memory.create_roleplay_recall(
+                self.soul_owner, self.memory.collection_revision(self.soul_owner),
+                IdempotencyIdentity('rp-recall', 'timeline-mismatch'),
+                content='时间线不符的回忆录', provenance=provenance)
+
+    # --- 隔离与遗忘 ---------------------------------------------------------
+
+    def test_rp_memory_text_is_not_copied_into_soul(self):
+        secret = 'RP_ONLY_SECRET'
+        self.memory.create_owner_memory(
+            self.owner, self.memory.collection_revision(self.owner),
+            IdempotencyIdentity('rp','secret'), content=secret, kind=MemoryKind.EPISODIC,
+            provenance=self.provenance('RP 密语'), audience=(self.session.viewer,))
+        self.record(accept=True)
+        joined = '\n'.join(self.soul_contents())
+        self.assertNotIn(secret, joined, 'RP 原文不得复制进 Soul World')
+
+    def test_forgotten_recall_stays_forgotten(self):
+        receipt = self.record(accept=True)
+        self.assertEqual(len(self.soul_contents()), 1)
+        self.memory.delete_memory(self.soul_owner, receipt.memory_id,
+                                  self.memory.collection_revision(self.soul_owner),
+                                  IdempotencyIdentity('rp-recall', 'forget'))
+        self.assertEqual(self.soul_contents(), [])
+        self.assertEqual(self.soul_contents(), [], '遗忘后不得因重查复活')
+
+    def test_recall_readable_after_leaving_cosplay(self):
+        receipt = self.record(accept=True)
+        snapshot = self.world.snapshot(self.actor, self.a.world.world_id)
+        session = next(s for s in snapshot.sessions if s.status.value == 'open')
+        self.world.exit(self.actor, self.a.world.world_id, self.a.timeline.scope.timeline_id,
+                        session.session_id, snapshot.world.revision, snapshot.world.writer_epoch)
+        record = self.memory.get_memory(self.soul_session, receipt.memory_id)
+        self.assertIs(record.provenance.reality_status,
+                      RealityStatus.FICTIONAL_SHARED_EXPERIENCE)
+        self.assertIn(R.BOUNDARY, record.content)
+
+    def test_bridge_source_still_denied(self):
+        """既有安全边界不变：Bridge 仍然不能写目标 Memory。"""
+        prov = replace(
+            R.build_provenance(self.source(), self.actor), source_type=SourceType.BRIDGE)
+        with self.assertRaises(MemoryRuntimeError):
+            self.memory.create_owner_memory(
+                self.soul_owner, self.memory.collection_revision(self.soul_owner),
+                IdempotencyIdentity('rp-recall', 'bridge'),
+                content='bridge 写入', kind=MemoryKind.EPISODIC, provenance=prov,
+                audience=(MemoryAudience(AudienceKind.SOUL, self.soul_scope.soul_id),))
+
+    # 泛入口也必须守住回忆录契约；以下只新增拒绝断言，不修改原安全测试。
+    def generic_recall(self, slot='generic', **kwargs):
+        params = dict(content='合成回忆录', kind=MemoryKind.SHARED_EXPERIENCE,
+                      provenance=R.build_provenance(self.source(), self.actor,
+                                                    canon=CanonStatus.ACCEPTED),
+                      audience=R.recall_audience(self.soul_scope.soul_id))
+        params.update(kwargs)
+        return self.memory.create_owner_memory(
+            self.soul_owner, self.memory.collection_revision(self.soul_owner),
+            IdempotencyIdentity('generic-recall', slot), **params)
+
+    def memory_state(self):
+        with self.repo.transaction() as tx:
+            return (tx.revision(self.soul_scope),
+                    tuple(tuple(row) for row in tx.db.execute('SELECT * FROM world_memories ORDER BY memory_id')),
+                    tuple(tuple(row) for row in tx.db.execute('SELECT * FROM memory_operations ORDER BY sequence')))
+
+    def denied_unchanged(self, operation):
+        before = self.memory_state()
+        with self.assertRaises(MemoryRuntimeError):
+            operation()
+        self.assertEqual(self.memory_state(), before, '拒绝不能推进修订、改旧记录或新增审计')
+
+    def test_generic_recall_rejects_missing_source(self):
+        source = self.source(source_scope=WorldScope(
+            self.actor.owner_id, self.soul.soul_id, DomainId.new(IdKind.WORLD),
+            DomainId.new(IdKind.TIMELINE)))
+        self.denied_unchanged(lambda: self.generic_recall(
+            provenance=R.build_provenance(source, self.actor, canon=CanonStatus.ACCEPTED)))
+
+    def test_generic_recall_rejects_bad_timeline(self):
+        provenance = replace(R.build_provenance(self.source(), self.actor),
+                             source_timeline_id=DomainId.new(IdKind.TIMELINE))
+        self.denied_unchanged(lambda: self.generic_recall(provenance=provenance))
+
+    def test_generic_recall_rejects_other_soul_source(self):
+        from life_engine.domain import Soul
+        other = Soul(DomainId.new(IdKind.SOUL), self.actor.owner_id, DomainId.new(IdKind.WORLD))
+        self.world.register_soul(self.actor, other)
+        world = self.world.create_roleplay_world(self.actor, other.soul_id, self.now)
+        source = self.source(source_scope=world.timeline.scope)
+        self.denied_unchanged(lambda: self.generic_recall(
+            provenance=R.build_provenance(source, self.actor)))
+
+    def test_generic_recall_rejects_other_owner_source(self):
+        from life_engine.domain import Principal, Soul
+        actor = Principal(DomainId.new(IdKind.PRINCIPAL), DomainId.new(IdKind.OWNER))
+        soul = Soul(DomainId.new(IdKind.SOUL), actor.owner_id, DomainId.new(IdKind.WORLD))
+        self.world.register_soul(actor, soul)
+        world = self.world.create_roleplay_world(actor, soul.soul_id, self.now)
+        source = self.source(source_scope=world.timeline.scope)
+        self.denied_unchanged(lambda: self.generic_recall(
+            provenance=R.build_provenance(source, self.actor)))
+
+    def test_generic_recall_rejects_wrong_kind_audience_and_subject(self):
+        changes = ({'kind': MemoryKind.EPISODIC},
+                   {'audience': (MemoryAudience(AudienceKind.WORLD),)},
+                   {'subjects': (MemorySubject(SubjectKind.SOUL, self.soul_scope.soul_id),)})
+        for index, change in enumerate(changes):
+            with self.subTest(change=change):
+                self.denied_unchanged(lambda: self.generic_recall(str(index), **change))
+
+    def test_generic_recall_rejects_roleplay_target(self):
+        other = self.make_world()
+        provenance = R.build_provenance(self.source(source_scope=other.timeline.scope), self.actor)
+        self.denied_unchanged(lambda: self.memory.create_owner_memory(
+            self.owner, self.memory.collection_revision(self.owner), IdempotencyIdentity('bad-target', '1'),
+            content='合成回忆录', kind=MemoryKind.SHARED_EXPERIENCE, provenance=provenance,
+            audience=(MemoryAudience(AudienceKind.WORLD),)))
+
+    def test_recall_audience_cannot_expand_through_generic_change(self):
+        receipt = self.record(accept=True)
+        self.denied_unchanged(lambda: self.memory.change_audience(
+            self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
+            IdempotencyIdentity('recall-expand', '1'), audience=(MemoryAudience(AudienceKind.WORLD),)))
+
+    def test_supersede_generic_memory_cannot_introduce_forged_recall(self):
+        ordinary = self.memory.create_owner_memory(
+            self.soul_owner, self.memory.collection_revision(self.soul_owner),
+            IdempotencyIdentity('ordinary', '1'), content='普通合成记忆', kind=MemoryKind.SHARED_EXPERIENCE,
+            provenance=Provenance(SourceType.OWNER_COMMAND, '合成正控', self.now, self.actor,
+                                  RealityStatus.FICTIONAL, CanonStatus.ACCEPTED),
+            audience=R.recall_audience(self.soul_scope.soul_id))
+        provenance = replace(R.build_provenance(self.source(), self.actor),
+                             source_world_id=DomainId.new(IdKind.WORLD),
+                             source_timeline_id=DomainId.new(IdKind.TIMELINE))
+        self.denied_unchanged(lambda: self.memory.supersede_memory(
+            self.soul_owner, ordinary.memory_id, self.memory.collection_revision(self.soul_owner),
+            IdempotencyIdentity('forge-supersede', '1'), content='伪造回忆', provenance=provenance))
+
+    def test_supersede_generic_memory_cannot_introduce_wrong_recall_shape(self):
+        provenance = Provenance(SourceType.OWNER_COMMAND, '普通合成来源', self.now, self.actor,
+                                RealityStatus.FICTIONAL, CanonStatus.ACCEPTED)
+        for index, (kind, audience) in enumerate((
+                (MemoryKind.EPISODIC, R.recall_audience(self.soul_scope.soul_id)),
+                (MemoryKind.SHARED_EXPERIENCE, (MemoryAudience(AudienceKind.WORLD),)))):
+            with self.subTest(kind=kind, audience=audience):
+                ordinary = self.memory.create_owner_memory(
+                    self.soul_owner, self.memory.collection_revision(self.soul_owner),
+                    IdempotencyIdentity('ordinary-shape', str(index)), content='普通合成记忆',
+                    kind=kind, provenance=provenance, audience=audience)
+                self.denied_unchanged(lambda: self.memory.supersede_memory(
+                    self.soul_owner, ordinary.memory_id, self.memory.collection_revision(self.soul_owner),
+                    IdempotencyIdentity('shape-supersede', str(index)), content='非法回忆录布局',
+                    provenance=R.build_provenance(self.source(), self.actor)))
+
+    def test_supersede_can_introduce_or_change_to_verified_roleplay_source(self):
+        ordinary = self.memory.create_owner_memory(
+            self.soul_owner, self.memory.collection_revision(self.soul_owner),
+            IdempotencyIdentity('valid-supersede', 'ordinary'), content='普通合成记忆',
+            kind=MemoryKind.SHARED_EXPERIENCE,
+            provenance=Provenance(SourceType.OWNER_COMMAND, '合成正控', self.now, self.actor,
+                                  RealityStatus.FICTIONAL, CanonStatus.ACCEPTED),
+            audience=R.recall_audience(self.soul_scope.soul_id))
+        receipt = self.memory.supersede_memory(
+            self.soul_owner, ordinary.memory_id, self.memory.collection_revision(self.soul_owner),
+            IdempotencyIdentity('valid-supersede', 'introduce'), content='合法回忆录',
+            provenance=R.build_provenance(self.source(), self.actor, canon=CanonStatus.ACCEPTED))
+        other = self.make_world()
+        provenance = R.build_provenance(self.source(source_scope=other.timeline.scope), self.actor,
+                                        canon=CanonStatus.ACCEPTED)
+        receipt = self.memory.supersede_memory(
+            self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
+            IdempotencyIdentity('valid-supersede', 'change-source'), content='合法换源回忆录',
+            provenance=provenance)
+        self.assertEqual(self.memory.get_memory(self.soul_owner, receipt.memory_id).provenance, provenance)
+
+    def test_supersede_recall_cannot_replace_with_missing_source_or_wrong_timeline(self):
+        receipt = self.record(accept=True)
+        provenance = self.memory.get_memory(self.soul_owner, receipt.memory_id).provenance
+        changes = ({'source_world_id': DomainId.new(IdKind.WORLD)},
+                   {'source_timeline_id': DomainId.new(IdKind.TIMELINE)})
+        for index, change in enumerate(changes):
+            with self.subTest(change=change):
+                self.denied_unchanged(lambda: self.memory.supersede_memory(
+                    self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
+                    IdempotencyIdentity('change-source', str(index)), content='修改回忆',
+                    provenance=replace(provenance, **change)))
+
+    def test_supersede_recall_cannot_shed_fictional_source_identity(self):
+        receipt = self.record(accept=True)
+        ordinary = Provenance(SourceType.OWNER_COMMAND, '来源脱壳', self.now, self.actor,
+                              RealityStatus.USER_CLAIMED, CanonStatus.ACCEPTED)
+        self.denied_unchanged(lambda: self.memory.supersede_memory(
+            self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
+            IdempotencyIdentity('shed-source', '1'), content='声称真实经历', provenance=ordinary))
+
+    def test_dedicated_create_validates_source_in_the_write_transaction(self):
+        revision = self.memory.collection_revision(self.soul_owner)
+        with patch.object(self.repo, 'transaction', wraps=self.repo.transaction) as transactions:
+            self.memory.create_roleplay_recall(
+                self.soul_owner, revision, IdempotencyIdentity('single-transaction', '1'),
+                content='合法合成回忆', provenance=R.build_provenance(self.source(), self.actor))
+        self.assertEqual(transactions.call_count, 1, '验源与写入不能分为两个事务')
+
+    def test_source_unavailable_does_not_break_existing_recall_lifecycle(self):
+        receipt = self.record()
+        with self.repo.transaction() as tx:
+            world_tx_class = type(tx.world)
+        original = world_tx_class.get_world
+
+        def unavailable_source(tx, world_id):
+            if world_id == self.a.world.world_id:
+                from life_engine.world_repository import FailureCode, WorldRuntimeError
+                raise WorldRuntimeError(FailureCode.WORLD_NOT_FOUND)
+            return original(tx, world_id)
+
+        with patch.object(world_tx_class, 'get_world', unavailable_source):
+            self.denied_unchanged(lambda: self.generic_recall('source-gone-new'))
+            receipt = self.memory.accept_memory(
+                self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
+                IdempotencyIdentity('unavailable-source', 'accept'))
+            self.assertEqual(len(self.soul_contents()), 1)
+            self.memory.hide_memory(self.soul_owner, receipt.memory_id,
+                                    self.memory.collection_revision(self.soul_owner),
+                                    IdempotencyIdentity('unavailable-source', 'hide'))
+            self.memory.unhide_memory(self.soul_owner, receipt.memory_id,
+                                      self.memory.collection_revision(self.soul_owner),
+                                      IdempotencyIdentity('unavailable-source', 'unhide'))
+            receipt = self.memory.change_audience(
+                self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
+                IdempotencyIdentity('unavailable-source', 'same-audience'),
+                audience=R.recall_audience(self.soul_scope.soul_id))
+            old = self.memory.get_memory(self.soul_owner, receipt.memory_id)
+            self.denied_unchanged(lambda: self.memory.supersede_memory(
+                self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
+                IdempotencyIdentity('unavailable-source', 'changed-source'), content='更改来源引用',
+                provenance=replace(old.provenance, source_id='新来源引用')))
+            receipt = self.memory.supersede_memory(
+                self.soul_owner, receipt.memory_id, self.memory.collection_revision(self.soul_owner),
+                IdempotencyIdentity('unavailable-source', 'same-source-text'),
+                content='同来源的摘要修订', provenance=old.provenance)
+            self.assertEqual(self.soul_contents(), ['同来源的摘要修订'])
+            self.memory.delete_memory(self.soul_owner, receipt.memory_id,
+                                      self.memory.collection_revision(self.soul_owner),
+                                      IdempotencyIdentity('unavailable-source', 'forget'))
+            self.assertEqual(self.soul_contents(), [])
+
+    def test_archived_or_tombstoned_source_does_not_break_recall_reads(self):
+        self.record(accept=True)
+        for status in (WorldStatus.ARCHIVED, WorldStatus.TOMBSTONED):
+            with self.world.repository.transaction() as tx:
+                tx.db.execute('UPDATE worlds SET status=? WHERE world_id=?',
+                              (status.value, str(self.a.world.world_id)))
+            self.assertEqual(len(self.soul_contents()), 1)
+
+
+class PromptRecallBoundaryTests(unittest.TestCase):
+    """Prompt 必须让模型看见"这是扮演"，不能只说正文。"""
+
+    def scope(self):
+        return WorldScope(*(DomainId.new(k) for k in
+                            (IdKind.OWNER, IdKind.SOUL, IdKind.WORLD, IdKind.TIMELINE)))
+
+    def session(self):
+        scope = self.scope()
+        return SimpleNamespace(purpose=PromptPurpose.SOUL_RESPONSE, scope=scope,
+                               viewer=MemoryAudience(AudienceKind.SOUL, scope.soul_id))
+
+    def record(self, source_type, content='回忆正文'):
+        return SimpleNamespace(memory_id=DomainId.new(IdKind.MEMORY), content=content,
+                               provenance=SimpleNamespace(source_type=source_type))
+
+    def test_control_marks_roleplay_recall(self):
+        plain = json.loads(prompt_runtime.control_payload(
+            self.session(), [self.record(SourceType.USER_REPORT)]))
+        self.assertNotIn('roleplay_recall', plain)
+        marked = json.loads(prompt_runtime.control_payload(
+            self.session(), [self.record(SourceType.ROLEPLAY_RECALL)]))
+        block = marked['roleplay_recall']
+        self.assertEqual(block['count'], 1)
+        self.assertEqual(block['reality'], 'fictional_shared_experience')
+        self.assertIn('played character', block['rule'])
+
+    def test_recall_item_uses_its_own_kind(self):
+        self.assertEqual(prompt_runtime.memory_item(
+            self.record(SourceType.ROLEPLAY_RECALL)).source_kind, 'memory_roleplay_recall')
+        self.assertEqual(prompt_runtime.memory_item(
+            self.record(SourceType.USER_REPORT)).source_kind, 'memory')
+
+    def test_recall_records_filter(self):
+        records = (self.record(SourceType.USER_REPORT), self.record(SourceType.ROLEPLAY_RECALL))
+        selected = prompt_runtime.roleplay_recall_records(records)
+        self.assertEqual(len(selected), 1)
+        self.assertIs(selected[0].provenance.source_type, SourceType.ROLEPLAY_RECALL)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_roleplay_recall_eval.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_roleplay_recall_eval.py
@@ -0,0 +1,187 @@
+"""合成评测的可重复性、指标语义与失败分层；不要求产品保持当前缺口。"""
+import contextlib
+import copy
+import hashlib
+import io
+import json
+from pathlib import Path
+import sys
+import tempfile
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(ROOT / 'tools'))
+
+import roleplay_recall_eval as evaluation  # noqa: E402
+
+
+class RecallEvaluationTests(unittest.TestCase):
+    @classmethod
+    def setUpClass(cls):
+        cls.temporary_paths = []
+        original = tempfile.TemporaryDirectory
+
+        def temporary(*args, **kwargs):
+            directory = original(*args, **kwargs)
+            cls.temporary_paths.append(Path(directory.name))
+            return directory
+
+        with patch.object(evaluation.tempfile, 'TemporaryDirectory', temporary):
+            cls.first = evaluation.evaluate()
+            cls.second = evaluation.evaluate()
+
+    def test_two_actual_runs_have_identical_semantic_results(self):
+        self.assertEqual(self.first['execution']['status'], 'COMPLETED')
+        self.assertEqual(self.first, self.second)
+        unhashed = copy.deepcopy(self.first)
+        semantic_hash = unhashed.pop('semantic_sha256')
+        self.assertEqual(hashlib.sha256(evaluation.canonical_bytes(unhashed)).hexdigest(),
+                         semantic_hash)
+
+    def test_each_run_uses_and_cleans_a_distinct_temporary_store(self):
+        self.assertEqual(len(self.temporary_paths), 2)
+        self.assertNotEqual(self.temporary_paths[0], self.temporary_paths[1])
+        self.assertTrue(all(not path.exists() for path in self.temporary_paths))
+        serialized = json.dumps(self.first, ensure_ascii=False)
+        self.assertNotIn('le-rr-eval-synthetic-', serialized)
+        self.assertNotIn(str(ROOT), serialized)
+
+    def test_frozen_corpus_covers_real_whitespace_and_late_anchor(self):
+        corpus = evaluation.load_corpus()
+        self.assertEqual(hashlib.sha256(evaluation.CORPUS.read_bytes()).hexdigest(),
+                         evaluation.CORPUS_SHA256)
+        cases = {item['id']: item for item in corpus['retrieval']['queries']}
+        self.assertEqual(cases['whitespace_only']['query'].strip(), '')
+        self.assertIn('\t', cases['whitespace_only']['query'])
+        self.assertGreater(cases['late_target']['query'].index('星港灯塔'), 40)
+        self.assertEqual(cases['unrelated']['desired'], [])
+        self.assertEqual(len(corpus['retrieval']['batches']), 8)
+
+    def test_report_binds_actual_sources_and_corpus(self):
+        bindings = self.first['bindings']
+        self.assertEqual(bindings['corpus_sha256'], evaluation.CORPUS_SHA256)
+        for path in ('integrations/hermes_memory/recall_service.py',
+                     'runtime/life_engine/memory_runtime.py',
+                     'runtime/life_engine/roleplay_recall.py',
+                     'tools/roleplay_recall_eval.py'):
+            self.assertEqual(bindings['sources'][path],
+                             hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
+        self.assertEqual(bindings['sources_sha256'], hashlib.sha256(
+            evaluation.canonical_bytes(bindings['sources'])).hexdigest())
+
+    def test_metrics_are_interpretable_without_assuming_old_failures(self):
+        corpus_cases = {item['id']: item for item in evaluation.load_corpus()['retrieval']['queries']}
+        cases = self.first['quality']['retrieval']
+        self.assertEqual({case['id'] for case in cases}, set(corpus_cases))
+        for case in cases:
+            desired = corpus_cases[case['id']]['desired']
+            self.assertEqual(case['desired_labels'], desired)
+            self.assertEqual(case['returned_count'], len(case['actual_labels']))
+            self.assertEqual(case['off_topic_count'],
+                             len(set(case['actual_labels']) - set(desired)))
+            if desired:
+                self.assertEqual(case['target_coverage'],
+                                 len(set(desired) & set(case['actual_labels'])) / len(desired))
+            else:
+                self.assertIsNone(case['target_coverage'])
+                self.assertEqual(case['off_topic_count'], case['returned_count'])
+            self.assertGreaterEqual(case['prompt_bytes'], 0)
+        self.assertIn('自然度', self.first['quality']['not_measured'])
+
+    def test_actual_safety_boundaries_remain_closed(self):
+        self.assertEqual(self.first['safety']['status'], 'PASS')
+        checks = self.first['safety']['checks']
+        self.assertTrue(all(check['passed'] for check in checks))
+        required = {'candidate_exists_as_candidate', 'candidate_not_recalled',
+                    'repeat_flush_does_not_accept_candidate', 'forgotten_not_recalled',
+                    'forgotten_not_revived_by_repeat_flush', 'fictional_source',
+                    'foreign_soul_source_denied', 'bridge_write_denied',
+                    'source_character_attribution', 'distinct_character_origins',
+                    'render_boundary', 'injected_cursor_failure_observed',
+                    'retry_does_not_duplicate', 'repeat_flush_is_noop',
+                    'generic_valid_recall_positive', 'generic_missing_source_denied',
+                    'generic_wrong_kind_denied', 'generic_world_audience_denied',
+                    'generic_entity_subject_denied', 'recall_audience_expansion_denied',
+                    'supersede_forged_recall_denied', 'recall_source_replacement_denied',
+                    'recall_source_identity_preserved'}
+        self.assertLessEqual(required, {check['id'] for check in checks})
+
+    def test_summary_is_normalized_and_fragment_observations_are_not_naturalness(self):
+        summary = self.first['quality']['summary']
+        self.assertIn('<uuid>', summary['normalized_content'])
+        self.assertIsNone(evaluation.UUID_PATTERN.search(summary['normalized_content']))
+        expected = evaluation.load_corpus()['summary']['desired_fragments']
+        self.assertEqual([item['fragment'] for item in summary['desired_fragments']], expected)
+        self.assertEqual(summary['desired_fragment_retention'], sum(
+            item['retained'] for item in summary['desired_fragments']) / len(expected))
+
+    def test_quality_gaps_do_not_turn_successful_execution_into_failure(self):
+        report = copy.deepcopy(self.first)
+        report['quality']['status'] = 'GAPS_OBSERVED'
+        self.assertEqual(evaluation.exit_code(report), 0)
+        report['safety']['status'] = 'FAIL'
+        self.assertEqual(evaluation.exit_code(report), 1)
+        report['safety']['status'] = 'PASS'
+        report['execution']['status'] = 'ERROR'
+        self.assertEqual(evaluation.exit_code(report), 1)
+
+    def test_empty_checks_and_missing_phase_cannot_be_vacuously_safe(self):
+        corpus = evaluation.load_corpus()
+        for mutation in ('empty_checks', 'missing_phase', 'missing_boundary', 'missing_query',
+                         'missing_summary', 'missing_generic_probe'):
+            with self.subTest(mutation=mutation):
+                report = copy.deepcopy(self.first)
+                if mutation == 'empty_checks':
+                    report['safety']['checks'] = []
+                elif mutation == 'missing_phase':
+                    report['execution']['completed_phases'].remove('boundaries')
+                elif mutation == 'missing_boundary':
+                    report['safety']['checks'] = [check for check in report['safety']['checks']
+                                                 if check['id'] != 'candidate_not_recalled']
+                elif mutation == 'missing_query':
+                    report['quality']['retrieval'].pop()
+                elif mutation == 'missing_summary':
+                    report['quality'].pop('summary')
+                else:
+                    report['safety']['checks'] = [check for check in report['safety']['checks']
+                                                 if check['id'] != 'recall_source_identity_preserved']
+                with self.assertRaises(evaluation.EvaluationError) as raised:
+                    evaluation.validate_completion(report, corpus)
+                self.assertEqual(raised.exception.code, 'EVALUATION_INCOMPLETE')
+
+    def test_cli_refuses_external_data_root_before_evaluation(self):
+        with patch.object(evaluation, 'evaluate') as run, contextlib.redirect_stderr(io.StringIO()):
+            with self.assertRaises(SystemExit) as raised:
+                evaluation.main(['--root', 'DO_NOT_OPEN_REAL_STORE'])
+        self.assertEqual(raised.exception.code, 2)
+        run.assert_not_called()
+
+    def test_unexpected_failure_is_nonzero_without_raw_exception_or_false_pass(self):
+        with patch.object(evaluation, 'load_corpus', side_effect=OSError('PRIVATE_BODY_AND_PATH')):
+            report = evaluation.evaluate()
+        self.assertEqual(report['execution'], {'status': 'ERROR',
+                                               'failure_code': 'EVALUATION_EXECUTION_FAILED'})
+        self.assertEqual(report['safety']['status'], 'INCOMPLETE')
+        self.assertEqual(report['quality']['status'], 'INCOMPLETE')
+        self.assertEqual(evaluation.exit_code(report), 1)
+        self.assertNotIn('PRIVATE', json.dumps(report))
+
+    def test_changed_corpus_is_rejected_with_explicit_code(self):
+        with patch.object(Path, 'read_bytes', return_value=b'{}'):
+            with self.assertRaises(evaluation.EvaluationError) as raised:
+                evaluation.load_corpus()
+        self.assertEqual(raised.exception.code, 'CORPUS_HASH_MISMATCH')
+
+    def test_cli_outputs_json_and_propagates_failure_status(self):
+        report = copy.deepcopy(self.first)
+        report['safety']['status'] = 'FAIL'
+        output = io.StringIO()
+        with patch.object(evaluation, 'evaluate', return_value=report), contextlib.redirect_stdout(output):
+            code = evaluation.main([])
+        self.assertEqual(code, 1)
+        self.assertEqual(json.loads(output.getvalue()), report)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~

## tests/test_roleplay_recall_lifecycle.py

~~~~~~~~diff
--- /dev/null
+++ b/tests/test_roleplay_recall_lifecycle.py
@@ -0,0 +1,172 @@
+"""汇总重试不恢复隐藏/不可见目标；Core Owner 接受能力本身不改变。"""
+import contextlib
+from dataclasses import replace
+from pathlib import Path
+import sqlite3
+import sys
+import tempfile
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[1]
+sys.path[:0] = [str(ROOT / 'runtime'), str(ROOT / 'integrations' / 'hermes_memory')]
+from recall_service import RecallService  # noqa: E402
+from life_engine import roleplay_recall as recall  # noqa: E402
+from life_engine.domain import CanonStatus, DomainId, IdKind, RealityStatus, SourceType  # noqa: E402
+from life_engine.memory import AudienceKind, IdempotencyIdentity, MemoryAudience, MemoryKind  # noqa: E402
+from life_engine.memory_repository import MemoryFailure as MC, MemoryRuntimeError  # noqa: E402
+from life_engine.world_repository import FailureCode, WorldRuntimeError  # noqa: E402
+
+
+class RecallLifecycleTests(unittest.TestCase):
+    def setUp(self):
+        directory = tempfile.TemporaryDirectory(prefix='le-recall-lifecycle-synthetic-')
+        self.addCleanup(directory.cleanup)
+        self.base = Path(directory.name)
+        self.sequence = 0
+
+    def service(self):
+        self.sequence += 1
+        service = RecallService(ROOT / 'runtime', self.base / f'store-{self.sequence}',
+                                self.base / f'profile-{self.sequence}', '合成生命周期角色')
+        service.remember_turn('user', '合成待处理原文')
+        service.remember_turn('assistant', '合成待处理回应')
+        return service
+
+    def snapshot(self, service):
+        with contextlib.closing(sqlite3.connect(service._memory.repository.path)) as db:
+            result = {table: tuple(db.execute(f'SELECT * FROM {table} ORDER BY 1,2')) for table in
+                      ('world_memories', 'memory_audiences', 'memory_subjects', 'memory_lineage',
+                       'memory_collection_state', 'memory_operations', 'memory_idempotency')}
+        cursor = service.root / 'flush.json'
+        result['cursor'] = cursor.read_bytes() if cursor.exists() else None
+        result['state'] = (service.root / 'state.json').read_bytes()
+        return result
+
+    def commit_without_cursor(self, service, *, accept):
+        original = Path.write_text
+        def fail(path, *args, **kwargs):
+            if path == service.root / 'flush.json':
+                raise OSError('SYNTHETIC_CURSOR_FAILURE')
+            return original(path, *args, **kwargs)
+        with patch.object(recall, 'record_recall', wraps=recall.record_recall) as recorder:
+            with patch.object(Path, 'write_text', fail):
+                with self.assertRaises(OSError):
+                    service.flush_recall(accept=accept)
+        records = service._memory.scan_owner_memory(service._soul_owner, history=True).records
+        candidate = next(record for record in records if record.provenance.canon_status is CanonStatus.CANDIDATE)
+        accepted = next((record for record in records if record.provenance.canon_status is CanonStatus.ACCEPTED), None)
+        return candidate, accepted, recorder.call_args
+
+    def mutate(self, service, method, target, **extra):
+        return getattr(service._memory, method)(service._soul_owner, target,
+                service._memory.collection_revision(service._soul_owner),
+                IdempotencyIdentity('lifecycle-owner', method), **extra)
+
+    def refused_unchanged(self, service, *, accept):
+        before = self.snapshot(service)
+        with self.assertRaises(MemoryRuntimeError) as raised:
+            service.flush_recall(accept=accept)
+        self.assertIs(raised.exception.code, MC.NOT_AVAILABLE)
+        self.assertEqual(self.snapshot(service), before)
+        self.assertEqual(len(service._memory.scan_owner_memory(service._rp_owner, append_only=True).records), 2)
+
+    def test_hidden_candidate_is_refused_before_accept_core_call(self):
+        service = self.service()
+        candidate, _, _ = self.commit_without_cursor(service, accept=False)
+        self.mutate(service, 'hide_memory', candidate.memory_id)
+        with patch.object(service._memory, 'accept_memory', wraps=service._memory.accept_memory) as acceptance:
+            self.refused_unchanged(service, accept=True)
+        acceptance.assert_not_called()
+        self.assertEqual(service.recall(), [])
+
+    def test_candidate_mode_hidden_or_superseded_cannot_claim_live_candidate(self):
+        for action in ('hide_memory', 'accept_memory', 'reject_memory'):
+            with self.subTest(action=action):
+                service = self.service()
+                candidate, _, _ = self.commit_without_cursor(service, accept=False)
+                self.mutate(service, action, candidate.memory_id)
+                self.refused_unchanged(service, accept=False)
+
+    def test_accepted_result_hidden_deleted_or_superseded_cannot_replay_success(self):
+        for action in ('hide_memory', 'delete_memory', 'supersede_memory'):
+            with self.subTest(action=action):
+                service = self.service()
+                _, accepted, _ = self.commit_without_cursor(service, accept=True)
+                extra = {'content': '其他Owner的新正文', 'provenance': accepted.provenance} if action == 'supersede_memory' else {}
+                self.mutate(service, action, accepted.memory_id, **extra)
+                self.refused_unchanged(service, accept=True)
+
+    def test_other_accept_reject_supersede_cannot_be_borrowed_by_flush_identity(self):
+        for action in ('accept_memory', 'reject_memory', 'supersede_memory'):
+            with self.subTest(action=action):
+                service = self.service()
+                candidate, _, _ = self.commit_without_cursor(service, accept=False)
+                extra = {'content': '其他候选正文', 'provenance': candidate.provenance} if action == 'supersede_memory' else {}
+                self.mutate(service, action, candidate.memory_id, **extra)
+                self.refused_unchanged(service, accept=True)
+
+    def test_current_candidate_and_accepted_write_failure_retries_keep_receipts(self):
+        for accept in (False, True):
+            with self.subTest(accept=accept):
+                service = self.service()
+                candidate, accepted, _ = self.commit_without_cursor(service, accept=accept)
+                before = self.snapshot(service)
+                receipt = service.flush_recall(accept=accept)
+                after = self.snapshot(service)
+                self.assertEqual(receipt.memory_id, accepted.memory_id if accept else candidate.memory_id)
+                self.assertEqual({key: value for key, value in before.items() if key != 'cursor'},
+                                 {key: value for key, value in after.items() if key != 'cursor'})
+                self.assertIsNotNone(after['cursor'])
+                self.assertIsNone(service.flush_recall(accept=accept))
+
+    def test_requesting_candidate_after_own_accept_is_not_live_candidate_success(self):
+        service = self.service()
+        self.commit_without_cursor(service, accept=True)
+        self.refused_unchanged(service, accept=False)
+
+    def test_forgotten_original_stays_unavailable(self):
+        service = self.service()
+        candidate, _, _ = self.commit_without_cursor(service, accept=False)
+        self.mutate(service, 'delete_memory', candidate.memory_id)
+        self.refused_unchanged(service, accept=False)
+        self.refused_unchanged(service, accept=True)
+
+    def test_existing_receipt_source_unavailable_does_not_bypass_new_create_checks(self):
+        service = self.service()
+        _, _, call = self.commit_without_cursor(service, accept=False)
+        with service._memory.repository.transaction() as tx:
+            world_class = type(tx.world)
+        original = world_class.get_world
+        def unavailable(tx, world_id):
+            if world_id == service._rp_owner.scope.world_id:
+                raise WorldRuntimeError(FailureCode.WORLD_NOT_FOUND)
+            return original(tx, world_id)
+        with patch.object(world_class, 'get_world', unavailable):
+            receipt = recall.record_recall(*call.args, identity=call.kwargs['identity'], accept=True)
+            result = service._memory.get_memory(service._soul_owner, receipt.memory_id)
+            self.assertIs(result.provenance.canon_status, CanonStatus.ACCEPTED)
+            before = self.snapshot(service)
+            with self.assertRaises(MemoryRuntimeError) as raised:
+                recall.record_recall(*call.args, identity=IdempotencyIdentity('new-source-required', 'fresh'), accept=True)
+            self.assertIs(raised.exception.code, MC.INVALID_SOURCE)
+            self.assertEqual(self.snapshot(service), before)
+
+    def test_result_shape_predecessor_and_source_must_match(self):
+        service = self.service()
+        candidate, accepted, call = self.commit_without_cursor(service, accept=True)
+        mutations = [replace(accepted, predecessor=None), replace(accepted, kind=MemoryKind.EPISODIC),
+                     replace(accepted, audience=(MemoryAudience(AudienceKind.WORLD),)),
+                     replace(accepted, provenance=replace(accepted.provenance, reality_status=RealityStatus.USER_CLAIMED)),
+                     replace(accepted, provenance=replace(accepted.provenance, source_id='不同来源')),
+                     replace(accepted, scope=replace(accepted.scope, world_id=DomainId.new(IdKind.WORLD)))]
+        for invalid in mutations:
+            with self.subTest(invalid=invalid.memory_id):
+                with patch.object(service._memory, 'get_memory', side_effect=[candidate, invalid]):
+                    with self.assertRaises(MemoryRuntimeError) as raised:
+                        recall.record_recall(*call.args, identity=call.kwargs['identity'], accept=True)
+                self.assertIs(raised.exception.code, MC.NOT_AVAILABLE)
+
+
+if __name__ == '__main__':
+    unittest.main()
~~~~~~~~
