# LE-RESET-01：固定基线、执行记录与索引

当前裁定与权限见 [STATUS](../STATUS.md)。这是审计快照，不是持续状态表；记录时间按 Asia/Shanghai，采证日期 2026-10-23。后续 PR 的精确 Head/CI 由 GitHub 页面绑定，不用修改源码反复追写 CI 状态。

## 固定对象与安全边界

| 对象 | 本轮固定内容 |
| --- | --- |
| R：远端 main / 本地初始 HEAD | `baa59729babf9ac56a17e02c682de2e3086e3575`，`git ls-remote origin refs/heads/main` 与本地一致 |
| R Git tree | `0e85214e157da4974d94b532297233eb499bc707`；306 tracked 文件，77 runtime Python 模块；所有本报告 main 代码行号固定此对象 |
| A：审计分支 | 独立 managed worktree，`docs/le-reset-01-audit`；从 R 创建，无生产或 dirty 代码覆盖 |
| L：本机候选 | 原目录 `D:\xiangmu\life-engine` 的未提交文件；初查64个 modified/untracked条目。不是干净main，不通过本PR发布代码 |
| L 冻结方式 | 复制白名单源码/测试/文档/fixture到全新系统临时目录；357文件，逐文件SHA256；不复制.env、用户库、凭据或聊天记录 |
| Host/生产 | 未读取Host Home、密钥、生产DB；未安装/加载Host、调用真实模型、连接ComfyUI、建定时任务、重启Gateway或发送 |
| PR权限 | 仅文档Draft；不Ready、不merge、不Auto Merge、不关闭Issue |

读到的 main 旧主线与本机 ROLEPLAY-RECALL 状态不同，能够由版本归属解释。没有用本机状态覆盖远端，也没有为“统一”而丢弃本机代码。#62 的并行文档提案单独审计，未 cherry-pick。

## 验证命令与实际结果

### Q1：干净 main 全量

环境：Windows-11-10.0.26200-SP0，Python 3.12.10，SQLite 3.49.1，Node v22.23.2。CI 使用Node24，环境差异保留。本轮不用Python3.10判定损坏，也不声称本地跑过3.11/Linux。

```powershell
$env:PYTHONUTF8='1'
py -3.12 -B -m unittest discover -s tests -q
```

<!-- Q1_RESULT -->
本轮实际终态：退出码 `0`，`Ran 684 tests in 818.466s`，`OK (skipped=3)`。
完整日志 `le-reset-01-main-tests.log` 的 SHA256 为
`c6dcbc92748f7cf7fef200c982e458f3abe5cd1b45145716b63b3d15488cbcda`。
quiet 输出不列逐项 skip 原因，本轮不猜测三项名单；与历史CI Windows跳过2项不同，结果按本次原样保留。
<!-- /Q1_RESULT -->

测试仅在新 worktree 的临时合成 fixture 运行；期间有既有 TemporaryDirectory ResourceWarning，保留而不屏蔽。全量结果不能代表本机 dirty 候选或真实 Host。

### Q2：本轮 X1 实际 CLI 闭环

每条命令以独立Python进程执行，`py -3.12 -B -X utf8 examples/experience_x1.py` 后依次传入：

| 顺序 | 参数（后七步追加同一 `--sandbox`） | 实际结果 / 退出码 |
| --- | --- | --- |
| 1 | `init` | SYNTHETIC_READY，系统临时新实例 / 0 |
| 2 | `day0` | NOT_ACCEPTED、accepted_memory空 / 0 |
| 3 | `day0 --accept` | ACCEPTED，一条合成原话 / 0 |
| 4 | `day1` | 新Session读回同一Memory，current_activity=UNKNOWN / 0 |
| 5 | `status` | 同一World和虚拟活动状态 / 0 |
| 6 | `isolation-check` | ISOLATED / 0 |
| 7 | `forget` | FORGOTTEN、normal_query=[] / 0 |
| 8 | `day1` | 新Session memory=[] / 0 |

各model字段为MODEL_NOT_CONNECTED；计划活动是合成时钟推断，不是角色自主生活。原始JSON只含合成数据，留存在本机临时证据中；可执行复验步骤见[X2方案A段](../planning/LE-RESET-01-X2-EXPERIENCE-PLAN.md#三十分钟试用脚本)。

### Q3：本机冻结候选离线评测

在L冻结目录运行 `py -3.12 -B -X utf8 tools/roleplay_recall_eval.py`，不是在漂移工作树直接引用模块，不接Host/模型。退出0；execution=COMPLETED，完成retrieval/summary/characters/boundaries/retry/generic_mutations六阶段；safety=PASS，65次实际检查；quality=GAPS_OBSERVED。

| 项目 | 实际结果 | 不能推导 |
| --- | --- | --- |
| 固定检索10项 | 9 MET，paraphrase GAP，期望harbor而实际空 | 不代表自然语言总体90%准确率 |
| 无关查询 | actual=[] | 不代表所有无关主题永不误召回 |
| 摘要 | 3个冻结目标片段全部保留 | 不代表任意对话摘要完整/自然 |
| 多角色 | 两个合成角色标签均找回 | 共用Soul不证明不同Soul隔离 |
| 重试 | 注入失败实际发生；重试前后各1条，重复flush noop | 不证明任意崩溃/并发/生产恢复 |

本轮没有执行L全量，也没有重跑其历史全量回执；L状态文档记载的独立审核、私有验收原件未在本轮逐一核验。只把Q3作为绑定该冻结候选的一次合成评测。

### Q4：文档与源码静态检查

<!-- Q4_RESULT -->
本轮作者静态核对通过：R的151个Python文件AST解析、9份变更文档中的64个本地链接/锚点及116个固定main代码链接/行号均有效；变更清单仅9份Markdown，Runtime/tests/tools/integrations/examples/workflow零差异。`git diff --check`通过。
L冻结357文件在Q3后逐文件摘要未变；原目录同一白名单357文件与采样时也无差异。此为本轮保护核对，不声称其他任务或未采样文件永远不变。
静态核对原件 `le-reset-01-static-check.json` SHA256为
`a9eae54cbc79e4ce010d0f4c75bf189fac73f8c6dad4d4952fe53e50d2ab7ab0`。
本轮只有作者自检，独立复核待进行；不把静态检查或自我审阅标成独立审核PASS。
<!-- /Q4_RESULT -->

## 远端 PR 与 CI 证据

使用GitHub连接器读取Issue #63及评论（当时0条）；PR批量查询参数不可用，改用gh只读查询，无凭据输出。以下命令可复查，结果会随未来远端变化；本表保留本轮观察。

```powershell
gh pr list --repo y19870785/life-engine --state all --limit 100 --json number,title,state,isDraft,headRefOid,baseRefName,mergedAt,url
gh run list --repo y19870785/life-engine --limit 100 --json databaseId,event,headSha,headBranch,status,conclusion,url
gh run view 39138679747 --repo y19870785/life-engine --json headSha,event,status,conclusion,jobs
gh run view 39138679747 --repo y19870785/life-engine --log
gh run view 39107386322 --repo y19870785/life-engine --log-failed
gh pr view 62 --repo y19870785/life-engine --json body,files,reviews,statusCheckRollup
```

PR共62条：60 MERGED、#62 OPEN/Draft、#3 CLOSED/unmerged。#60 base是codex/character-onboarding，先合入#59，不能当作独立main提交。#62 Head=f8393fa4698b55d75bfa891df1629266de8e2fe9，25份文档，reviews列表为空；其描述记载的独立文档审核不等于GitHub已提交review。

main精确push CI [39138679747](https://github.com/y19870785/life-engine/actions/runs/39138679747) 的event=push、headSha=R、status=completed、conclusion=success。逐job核验与日志：

| job | 实际结果 | 日志耗时 |
| --- | --- | --- |
| Ubuntu / Python3.11 | 684 tests，OK(skipped=3) | 257.888秒 |
| Ubuntu / Python3.12 | 684 tests，OK(skipped=3) | 285.627秒 |
| Windows / Python3.11 | 684 tests，OK(skipped=2) | 1378.199秒 |
| Windows / Python3.12 | 684 tests，OK(skipped=2) | 1740.109秒 |

这些是历史固定SHA的实际CI，不是当前文档PR的CI，也不证明Host/模型/用户体验。Windows单job约23–29分钟，与仓库本地8–10分钟提示不同；本轮不推断CPU或SQLite根因，不改workflow/同步/断言。

最近100个run抽样为94 success、5 failure、1 cancelled；不是完整项目通过率，也不是开发人时。非成功记录如下，旧失败保留不改写：

| run | event / SHA | conclusion / 核查范围 |
| --- | --- | --- |
| [39107386322](https://github.com/y19870785/life-engine/actions/runs/39107386322) | push / `b1fbfc2694c45882c848b8dc1e978301615eb375` | failure；读日志：Windows3.11 ready JSON半写，JSONDecodeError；#61原子发布修复已入后续main |
| [38768822634](https://github.com/y19870785/life-engine/actions/runs/38768822634) | pull_request / `f99963bdad61d100486dff9670923815370ebcbb` | failure；W1原件记录：路径/子进程准入测试失败，不是Host功能通过 |
| [38241948240](https://github.com/y19870785/life-engine/actions/runs/38241948240) | pull_request / `3e95f6c4e15734634a665f66e5fd564ee2a592ed` | cancelled；#55描述记录Windows3.12达到25分钟时限；不是完整通过，未据此判产品断言失败 |
| [38154006264](https://github.com/y19870785/life-engine/actions/runs/38154006264) | pull_request / `2741d807731e1d3debbf1c4eb0827fa3796d9efc` | failure；读日志：X1 Windows临时路径别名拒绝，test_reopen_forget_and_world_isolation失败 |
| [38153323133](https://github.com/y19870785/life-engine/actions/runs/38153323133) | pull_request / `da6a1f8abc8aa0355d50860837fff9c81bc186a0` | failure；读日志：同类X1路径拒绝；不由后续通过抹除 |
| [38132715723](https://github.com/y19870785/life-engine/actions/runs/38132715723) | pull_request / `e439bc043d712b76c5443d4bec598bd36a5a1156` | failure；M1-A原件记录：Windows短路径检查阻断，后来修复；不等于原语准入 |

PR #62 的“先依赖闭包→纯合成OS fixture→无模型T1→小预算T2”建议及CI成本分析已读取；本提案不重复把下一周期出口设为又一份Host任务书，而提供不依赖W1的隔离消费链。#62未合并，不作为本PR Base。

另用连接器读取#55/#57/#58/#59/#60的正文与固定Base/Head/merge对象：#55明确无模型及超时修复；#57保留历史Profile两轮COMMITTED与后续W1失败的分层；#58保留工具可见性而非媒体成功；#59包含#60的最终诊断，且本次main代码树与远端对象一致。PR正文的“独立审核”是历史作者记录，本报告没有替代其私有审查原件重新签发审核结论。

## 本机候选证据

以下是L冻结源码的审计摘录和逐文件绑定，不是随PR发布的Runtime，也不是完整候选代码独审。远端review者可据摘录审核本报告的归因；若要批准该代码复用，仍须提供完整固定候选diff/包与独立审核。没有远端源码链接的L文件不可伪装成main已有文件。

冻结UTC时间 `2026-10-23T15:01:43.618079+00:00`；357文件清单SHA256 `3ec7e7d47d2f39fc60476934996416be11367ba62ae4963f8da70ba669938863`。Q3报告semantic_sha256 `8903897d667f1a6715e07861605b6ea4378c9058be92b6e25bfa983b468268ac`。

| ID | 冻结文件（L相对路径） | SHA256 |
| --- | --- | --- |
| L1 | `runtime/life_engine/roleplay_recall.py` | `04052e70cc0c5ce5e288815acbe21fc72022bfb21845e8592b918b61139c2cf0` |
| L2 | `integrations/hermes_memory/__init__.py` | `2af24885dcb799df2ecbbafec294214476db266a3076807357c2feddc7d4d406` |
| L3 | `integrations/hermes_memory/recall_service.py` | `d12178359b8917980b32a9cdf234491888dada5df2f498779d7f01f14a245d2f` |
| L4 | `docs/planning/RR-FORGET-SOURCE-DESIGN.md` | `f36a8fcc51660a57742b80ce25accab56f17d072330e68c027de7b162186fbae` |
| L5 | `docs/HERMES-MEMORY-PROVIDER.md` | `f7981365dd55c652827517b75a51adb43113b465a891b162aaf14934701263ab` |
| L6 | `docs/STATUS.md` | `dd2f497ec6228608219126a37687f00bc096696292d98d01df7fb95d896ee3a7` |
| L7 | `tools/hermes_memory_install.py` | `25705308886891f1428646209d093ac3ab8c4f01faf5cb47d31b730a801450bd` |
| L8 | `tools/hermes_memory_manage.py` | `563bf65f308072b3cae245e5707a249544be34fa23be2d6bd6cf83969a8d2e79` |
| L9 | `tools/hermes_memory_flush.py` | `629ae569f0dbf9805b1b912758ca67cc43c61fa479d901cda0cb0c4679c39e78` |
| L10 | `tools/roleplay_recall_eval.py` | `c23c09e422e575b7c5306ec31a03541ee26fd71808b75ab88f1f5a5231ffc29d` |
| L11 | `tests/fixtures/roleplay_recall_eval/v1.json` | `82859adddc510cf350dcf963f8456cd43f1f135b8de9de2784faab2a959eebc0` |
| L12 | `runtime/life_engine/memory_runtime.py` | `78ec9462d90b39f95dcdca9a7a253a63569c927f96a7e022bb07c671c6fb26dc` |
| L13 | `runtime/life_engine/domain.py` | `aabb98655fb9351fb9ad0e14fb0b015d2362b1e4379fea528b8dd5c5a2f7b606` |
| L14 | `runtime/life_engine/memory_repository.py` | `926478609f3da991cfd646f7d32ec81b00b5ff13211efca540e7e5e85b05174d` |
| L15 | `tests/test_hermes_memory_provider.py` | `c355e60ddfa4a07916660f680960be104f31e6a3bf1f85d2af3c80a2f330cbf5` |
| L16 | `tests/test_hermes_memory_retrieval_quality.py` | `a5aa7f19eb3fd5d4ca3f9a1a2247f12f97d5f4d54b0a69182031aa437dfe7476` |
| L17 | `tests/test_hermes_memory_summary_quality.py` | `ca2f6a23b314ed559720a740c094220c1f0a0d718a07a516bf190d8bae98d6dd` |
| L18 | `tests/test_roleplay_recall.py` | `f782184dcd470b65a1216938d9d5ae9fd84736749d305cc84312158dae7fe0f8` |
| L19 | `docs/planning/RR-RETRIEVAL-UNICODE-01.md` | `74960476837d7c7a7f5451473389fa38c2a80926e082eccb08a863974a250682` |
| L20 | `docs/planning/RR-INSTALL-CACHE-01.md` | `6edb8d0c247581f3dff87091c3476d7b69602a64f4af584e93b611af76562aa7` |

### L2：无命中与不可用都表现为空上下文，状态行为空

`integrations/hermes_memory/__init__.py:120–135`，内容如下：

```python
    def prefetch(self, query: str, *, session_id: str = "") -> str:
        try:
            service = self._available_service()
            if service is None:
                return ''
            rendered = service.render(service.recall(query))
            if isinstance(rendered, str):
                return rendered
            self._reason = 'SERVICE_UNAVAILABLE'
            return ''
        except Exception:  # noqa: BLE001
            self._reason = 'SERVICE_UNAVAILABLE'
            return ''

    def recall_status(self):
        return None
```

### L2：sync_turn与会话结束边界

`integrations/hermes_memory/__init__.py:151–185`，内容如下：

```python
    def sync_turn(self, user_content: str, assistant_content: str, *,
                  session_id: str = '', messages=None, turn_author=None) -> None:
        if not self._config.get('auto_record', True):
            return
        try:
            service = self._available_service()
            if service is None:
                return
            service.remember_turn('user', user_content)
            service.remember_turn('assistant', assistant_content)
        except Exception:  # noqa: BLE001
            self._reason = 'SERVICE_UNAVAILABLE'
            return

    def on_session_end(self, messages) -> None:
        if not self._config.get('auto_record', True):
            return
        try:
            service = self._available_service()
            if service is not None:
                service.flush_recall()
        except Exception:  # noqa: BLE001
            self._reason = 'SERVICE_UNAVAILABLE'
            return

    def on_session_switch(self, new_session_id: str, *, parent_session_id: str = '',
                          reset: bool = False, rewound: bool = False, **kwargs) -> None:
        try:
            if reset and self._config.get('auto_record', True):
                service = self._available_service()
                if service is None:
                    return
                service.flush_recall()
            self._session_id = new_session_id or ''
        except Exception:  # noqa: BLE001
```

### L3：追加扫描、批次来源与flush游标

`integrations/hermes_memory/recall_service.py:273–304`，内容如下：

```python
    def flush_recall(self, *, accept=True):
        """把本角色世界里尚未登记的轮次汇总成一条 Soul 回忆录。"""
        self.ensure()
        path = self.root / 'flush.json'
        cursor, mine = self._flush_cursor(path)
        # count 只对应已证明纯追加历史中的前 N 次创建，不依赖墙钟或随机 ID 排序。
        records = self._memory.scan_owner_memory(self._rp_owner, append_only=True).records
        seen = mine['flushed']
        if seen > len(records):
            raise RecallCursorError()
        pending = records[seen:]
        if not pending:
            return None
        from life_engine import roleplay_recall as recall_lib
        from life_engine.domain import SourceType
        user_turns = [r for r in pending if r.provenance.source_type is SourceType.USER_REPORT]
        highlights = _select_highlights(pending)
        moments = [r.created_at for r in pending]
        source = recall_lib.RecallSource(
            source_scope=self._rp_owner.scope,
            character_name=self.character_name or self.character_key,
            card_fingerprint=f'hermes-profile:{self.character_key}',
            turn_count=len(user_turns) or len(pending),
            started_at=min(moments), ended_at=max(moments),
            highlights=highlights)
        receipt = recall_lib.record_recall(
            self._memory, self._soul_owner, source,
            identity=_identity('hermes-recall', f'{self.character_key}-{seen}'),
            accept=accept)
        mine['flushed'] = len(records)
        path.write_text(json.dumps(cursor), encoding='utf-8')
        return receipt
```

### L3：词面召回与带边界render

`integrations/hermes_memory/recall_service.py:308–332`，内容如下：

```python
    def recall(self, query='', limit=MAX_RECALL_ITEMS):
        query = validate_query(query, limit, MAX_RECALL_ITEMS)
        if limit == 0:
            return []
        self.ensure()
        from life_engine import roleplay_recall as recall_lib
        records = [r for r in self._memory.scan_owner_memory(self._soul_owner).records
                   if recall_lib.is_recall(r)]
        if not records:
            return []
        return select_recall(records, query, limit)

    def render(self, records):
        if not records:
            return ''
        lines = [BOUNDARY]
        for record in records:
            for line in record.content.splitlines():
                if line.startswith('[') or line.startswith('这是一次'):
                    continue
                lines.append(line)
            lines.append('')
        return '\n'.join(lines).strip()


```

### L1：来源的虚构边界

`runtime/life_engine/roleplay_recall.py:96–114`，内容如下：

```python
def build_provenance(source, actor, *, canon=CanonStatus.CANDIDATE, created_at=None):
    """回忆录的来源断言：来源语义固定在 FICTIONAL_SHARED_EXPERIENCE。

    ``created_at`` 缺省取这段经历结束（或开始）的时间，而不是写入时间：
    回忆录记录的是**事情何时发生**，同一段经历重复登记也因而是确定的。
    """
    require(actor, Principal)
    moment = created_at or source.ended_at or source.started_at or datetime.now(timezone.utc)
    return Provenance(
        SourceType.ROLEPLAY_RECALL,
        source_reference(source),
        moment,
        actor,
        RealityStatus.FICTIONAL_SHARED_EXPERIENCE,
        canon,
        source_world_id=source.source_scope.world_id,
        source_timeline_id=source.source_scope.timeline_id,
    )

```

L5历史观察摘要：文档标日期2026-10-19，准备合成“明天下午面试”轮次；两个新CLI会话分别明确追问/回顾，记载来源边界与未补岗位/地点；记录rp_turns=4、recall_count=2。历史包示例69c76569标WORKING_TREE_UNCOMMITTED，明确不含后续补丁。本轮只核文档/源码，不接触其私有原件与安装副本，证据维度是HOST_RECORD，不是本轮HOST_PASS或小雪USER_PASS。

L4/L19/L20记载的反例（本轮未独立重现）：来源级删除会阻断未来同角色来源写入；Unicode范围包含部分符号可组成强词面匹配；freeze复用既有目录未核内容摘要。L3/L7有相应路径，故列为候选准入风险，不宣称生产已出事故或本轮已修好。缺私有反例原件时保持待复核。

## 全仓源码调用面索引

下面覆盖R所有runtime Python模块，列顶层类/函数的实际行号（自动AST读取，不执行import）。支持codec/schema/repository并不等于单独可体验能力；“完整枚举”不等于逐行安全审计。入口与消费方的人工核查见[主审计](../reviews/LE-RESET-01-REPOSITORY-AUDIT.md#3-实际调用路径)。

<details>
<summary>77个Runtime模块</summary>

| 模块 | 顶层符号 / 代码行 |
| --- | --- |
| [runtime/life_engine/__init__.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/__init__.py#L1) | 包入口/常量 |
| [runtime/life_engine/bridge.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/bridge.py#L1) | BridgeFailure:22；BridgeRuntimeError:49；deny:55；bounded:59；BridgeDataClass:64；BridgePurpose:69；BridgeGrantStatus:75；BridgeGrantRevision:81；checked_fields:85；checked_audience:94；OwnerBridgeContext:101；SessionBridgeContext:115；BridgeGrantProposal:135；BridgeGrant:154；BridgeIdempotencyIdentity:181；BridgeBudget:193；BridgePreview:208；BridgeReceipt:219；BridgeLineage:226；BridgeItem:239；BridgeProjection:247；BridgeMemorySource:277；BridgeStorySource:314；BridgeProjectionRequest:336 |
| [runtime/life_engine/bridge_codec.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/bridge_codec.py#L1) | scope_data:7；audience_data:11；proposal_data:15；digest:22；preview_data:26；lineage_data:33；item_data:41；projection_data:46 |
| [runtime/life_engine/bridge_control.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/bridge_control.py#L1) | control_structure:25；initialize_control:36；control:70；append_intent:125 |
| [runtime/life_engine/bridge_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/bridge_repository.py#L1) | BridgeTransaction:9；BridgeRepository:17 |
| [runtime/life_engine/bridge_runtime.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/bridge_runtime.py#L1) | BridgeRuntime:30 |
| [runtime/life_engine/bridge_schema.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/bridge_schema.py#L1) | create_bridge_schema:68 |
| [runtime/life_engine/bridge_sqlite_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/bridge_sqlite_repository.py#L1) | _grant:21；validate_bridge_data:44；reconcile_db:109；BridgeTransaction:163；SQLiteBridgeRepository:224 |
| [runtime/life_engine/bridges.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/bridges.py#L1) | install_bridges:308；installation_guide:354；native_connect:433 |
| [runtime/life_engine/character_continuity.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/character_continuity.py#L1) | init:41；load:90；journal:98；Core:105；core_call:155；stage:166；finish:184；commit:223；context:239；status:284；activation:293；main:326 |
| [runtime/life_engine/character_onboarding.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/character_onboarding.py#L1) | inspect:14；prepare:37；install:63；_install:74；main:133 |
| [runtime/life_engine/cli.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/cli.py#L1) | emit:13；parser:17；simulate:62；main:78 |
| [runtime/life_engine/compat_scan.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/compat_scan.py#L1) | inventory:17；diagnostic:38；scan:43；main:108 |
| [runtime/life_engine/config.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/config.py#L1) | tz:12；now_in:21；minutes:27；valid_id:34；defaults:40；validate:68；load:133；json_bytes:147 |
| [runtime/life_engine/deploy_cli.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/deploy_cli.py#L1) | plan_install:19；apply_preview:46；main:57 |
| [runtime/life_engine/domain.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/domain.py#L1) | DomainError:8；require:12；IdKind:17；DomainId:35；check_id:64；Revision:71；WriterEpoch:83；DefinitionVersion:88；WorldKind:95；WorldStatus:100；RealityStatus:108；CanonStatus:119；SourceType:126；Owner:138；Principal:146；aware:156；Provenance:163；Soul:198；World:210；WorldScope:236；WorldTimeline:254；Values:271；WorldState:287；DefinitionRef:303；CharacterDefinition:313；CharacterInstance:332；BindingStatus:356；SessionBinding:362 |
| [runtime/life_engine/domain_lifecycle.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/domain_lifecycle.py#L1) | WorldCommand:10；WorldEvent:21；Transition:33；create_world:38；validate_fence:52；transition_world:76；bind_session:92；_validate_binding:109；validate_write:119；CloseReason:133；close_session:138 |
| [runtime/life_engine/domain_policy.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/domain_policy.py#L1) | Capability:9；Support:19；HostCapabilities:29；labels:60；BridgeRequest:67；BridgePolicy:92；BridgeDecision:114；evaluate_bridge:122 |
| [runtime/life_engine/durable.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/durable.py#L1) | absolute:30；read:36；write:41；sync_dir:46；sync_tree:55；safe_name:65；relative:71；locked:79；registry:114；state_home:125；instance_id:133；files_under:137；db_check:148；copy_state:174；rebase_photos:195；state_check:212；snapshot:227；verify_backup:284；reconcile_memory_generation:300；reconcile_bridge_generation:321；restore:339；release_files:368；release_install:373；probe_release:401；rollback_code:427；create_install:469；migrate_generation:575；upgrade:592；rollback_schema:638；rollback_living:671；health:700；context_text:762；publish_photo:798；run:815 |
| [runtime/life_engine/engine.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/engine.py#L1) | quiet:10；Engine:18 |
| [runtime/life_engine/hermes_capabilities.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/hermes_capabilities.py#L1) | configure:11；main:35 |
| [runtime/life_engine/hermes_card_hook.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/hermes_card_hook.py#L1) | validate_card:16；text_input:53；matches:62；project:70；before:89；register:113 |
| [runtime/life_engine/hermes_card_import.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/hermes_card_import.py#L1) | digest:23；safe:27；home_path:34；read:41；json_bytes:48；signed:52；atomic:61；locked:77；preview:88；current:137；receipt_at:142；verify:157；restore:166；apply:199；main:269 |
| [runtime/life_engine/hermes_card_native_hook.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/hermes_card_native_hook.py#L1) | host_capabilities:20；continuity_config:40；continuity_call:66；continuity_trace:80；bound_home:91；before:101；rewrite:138；guard_tool:234；after:262；ended:284；register:314 |
| [runtime/life_engine/hermes_card_runtime.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/hermes_card_runtime.py#L1) | integer:29；text:37；expand:43；text_issues:52；compile_plan:61；validate:170；opening:214；example_messages:220；message_text:248；select_lore:258；restrict_tools:291；assemble:309 |
| [runtime/life_engine/hermes_profile_setup.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/hermes_profile_setup.py#L1) | configure_host:23；_yaml:56；_mapping:66；_names:72；_config:81；_fresh:88；prepare:104；apply:157；restore:200 |
| [runtime/life_engine/hermes_turn_proof.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/hermes_turn_proof.py#L1) | digest:12；safe_db:16；watermark:25；verify_pair:31 |
| [runtime/life_engine/import_cards.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/import_cards.py#L1) | is_link:24；read_card:29；png_payload:43；validate_metadata:109；normalize_lore:129；parse_bytes:163；normalize_card:185；parse_card:265 |
| [runtime/life_engine/import_ir.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/import_ir.py#L1) | Classification:18；ImportFailure:27；canonical:34；load_json:38；JsonValue:84；LoreIR:101；CharacterImportIR:120；project_definition:204 |
| [runtime/life_engine/install.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/install.py#L1) | digest:16；file_hash:20；no_symlinks:31；atomic_write:38；inspect_host:55；discover_homes:99；soul_block:116；build_plan:140；plan_view:218；guard_plan:228；apply_plan:256；rollback:295 |
| [runtime/life_engine/integration.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/integration.py#L1) | command:10；integration_text:14；skill_text:62；schedule_recipe:73 |
| [runtime/life_engine/living_domain.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_domain.py#L1) | LivingError:15；fail:21；canonical:25；fingerprint:29；text:33；instant:39；scope_values:45；LivingContext:52；LivingTickContext:69 |
| [runtime/life_engine/living_host_binding.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_host_binding.py#L1) | HostIdentityEnvelope:31；BindingAuthority:63；RealDeliveryBindingFactory:522 |
| [runtime/life_engine/living_host_capability.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_host_capability.py#L1) | Capability:11；ExecutionPermit:19；CredentialVault:29 |
| [runtime/life_engine/living_host_evidence.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_host_evidence.py#L1) | DeliveryEvidence:14；FakeEvidenceValidator:35；DeterministicFakeTransport:82 |
| [runtime/life_engine/living_host_facade.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_host_facade.py#L1) | bounded:13；payload:19；ClaimOutcome:27；LivingHostFacade:36 |
| [runtime/life_engine/living_host_metadata.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_host_metadata.py#L1) | current_sid:20；protect:26；BindingMetadata:39 |
| [runtime/life_engine/living_migration.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_migration.py#L1) | fence_generation:10 |
| [runtime/life_engine/living_policy.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_policy.py#L1) | zone:13；zone_fingerprint:18；tz_source:32；policy:39；validate_policy:52；local_instant:100；time_context:112；quiet_until:127 |
| [runtime/life_engine/living_projection.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_projection.py#L1) | LivingContextSnapshot:15；query:20；revalidate:90 |
| [runtime/life_engine/living_real_delivery.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_real_delivery.py#L1) | BindingMode:8；ExecutionPurpose:13；PolicyDecision:18；TrustedDeliveryTarget:24；DeliveryContext:46；RealDeliveryPolicy:61；OneShotRealDeliveryGrant:67；validation_text:112；SimulationConsumer:120；RealDeliveryConsumer:131 |
| [runtime/life_engine/living_recovery.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_recovery.py#L1) | _identity:17；RecoveryDelegation:27；LivingRecoveryContext:44；OperationRecoveryRequest:51；PrepareRecoveryReceipt:62；ClaimRecoveryReceipt:68；RecoveryAttempt:76；OperationRecoveryProjection:82；_request:102；_context:121；_json:167；_stored_text:182；_project:190；_root_integrity:265；query_operation_recovery:275 |
| [runtime/life_engine/living_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_repository.py#L1) | state_digest:18；validate_living_data:23；LivingRepository:80 |
| [runtime/life_engine/living_runtime.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_runtime.py#L1) | insert:18；one:23；finish:29；LivingRuntime:38 |
| [runtime/life_engine/living_schema.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/living_schema.py#L1) | create_living_schema:99 |
| [runtime/life_engine/lore.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/lore.py#L1) | byte_size:32；metadata:42；bounded_int:48；LoreBookVersion:54；LoreBindingRevision:65；LoreDiagnostic:72；LoreActivationReason:86；LoreBookDefinition:94；LoreBookVersionRecord:118；LoreEntryDefinition:150；LoreBinding:193；LoreBudget:212；LoreRegistrationIdentity:227；OwnerLoreContext:239；SessionLoreContext:253；LoreMemoryProjection:274；LoreActivationRequest:311；ActivatedLoreEntry:339；LoreActivationResult:354；LoreReceipt:371 |
| [runtime/life_engine/lore_normalize.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/lore_normalize.py#L1) | NormalizedEntry:12；NormalizedBook:28；normalize_lore_ir:36；registration_fingerprint:140 |
| [runtime/life_engine/lore_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/lore_repository.py#L1) | LoreFailure:6；LoreRuntimeError:23；fail:29；LoreRepository:33；LoreTransaction:40 |
| [runtime/life_engine/lore_runtime.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/lore_runtime.py#L1) | checked:21；_fingerprint:38；_activation_order:42；_owner:48；_scope_world:54；LoreRuntime:64 |
| [runtime/life_engine/lore_schema.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/lore_schema.py#L1) | create_lore_schema:84 |
| [runtime/life_engine/lore_sqlite_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/lore_sqlite_repository.py#L1) | _id:22；_json:28；decoded:35；_book:48；_version:56；_entry:67；_binding:91；validate_lore_data:99；LoreTransaction:185；SQLiteLoreRepository:314 |
| [runtime/life_engine/memory.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/memory.py#L1) | bounded_text:17；MemoryKind:23；MemoryLifecycle:33；MemoryCollectionRevision:41；AudienceKind:45；MemoryAudience:54；audiences:69；SubjectKind:83；MemorySubject:91；MemoryRecord:111；IdempotencyIdentity:159；OwnerMemoryContext:169；SessionMemoryContext:182；MemoryReceipt:201；MemoryQueryResult:207 |
| [runtime/life_engine/memory_control.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/memory_control.py#L1) | control_structure:25；fingerprint:36；initialize_control:40；control:75；append_intent:121；scope_values:136 |
| [runtime/life_engine/memory_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/memory_repository.py#L1) | MemoryFailure:8；MemoryRuntimeError:18；deny:25；MemoryRepository:29 |
| [runtime/life_engine/memory_runtime.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/memory_runtime.py#L1) | checked:20；authorize:32；validate_record:54；available:101；MemoryRuntime:120 |
| [runtime/life_engine/memory_schema.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/memory_schema.py#L1) | create_memory_schema:62 |
| [runtime/life_engine/memory_sqlite_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/memory_sqlite_repository.py#L1) | load_record:22；MemoryTransaction:47；reconcile_db:123；SQLiteMemoryRepository:159；validate_memory_data:285 |
| [runtime/life_engine/migrate.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/migrate.py#L1) | migrate_v01:7 |
| [runtime/life_engine/photos.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/photos.py#L1) | media_directive:13；inspect_workflow:18；replace_tokens:34；render_prompt:47；ComfyUI:62；photo:108 |
| [runtime/life_engine/prompt.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/prompt.py#L1) | PromptPurpose:25；PromptAuthority:30；PromptSectionKind:36；TruncationPolicy:48；PromptDiagnostic:54；PromptFailure:64；PromptRuntimeError:82；fail:88；_text:92；PromptItem:105；PromptSection:123；PromptBudget:154；PromptTokenEstimator:184；ConversationVersionValidator:188；ConversationTurn:194；ConversationProjection:207；PromptMemoryProjection:239；PromptStoryProjection:284；PromptLoreProjection:309；PromptBridgeProjection:336；PromptSessionContext:358；PromptAssemblyRequest:383；PromptRequirements:396；PromptSnapshot:403 |
| [runtime/life_engine/prompt_codec.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/prompt_codec.py#L1) | item_data:5；section_data:10；item_bytes:17；section_bytes:21；render_canonical:25；total_bytes:30；budget_data:34；fingerprint_data:44 |
| [runtime/life_engine/prompt_runtime.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/prompt_runtime.py#L1) | PromptRuntime:31 |
| [runtime/life_engine/sandbox.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/sandbox.py#L1) | identity:16；delivery_trace:26；validate_probe:59；report:114 |
| [runtime/life_engine/setup.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/setup.py#L1) | ask:24；yes:35；merged:45；choose_home:59；existing_cfg:78；guide:86；preview:176；main:201 |
| [runtime/life_engine/store.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/store.py#L1) | Store:28；legacy_writer:127 |
| [runtime/life_engine/story.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/story.py#L1) | bounded:25；StoryRevision:32；StoryClock:37；StoryEventKind:48；StoryThreadStatus:62；SourceReferenceKind:68；StoryEventSourceReference:76；FactPayload:94；CharacterPayload:107；RelationshipPayload:120；ThreadPayload:137；NarrativePayload:151；payload_data:173；payload_load:204；StoryIdempotencyIdentity:234；OwnerStoryContext:244；SessionStoryContext:256；StoryEventProposal:276；StoryEvent:301；StoryThread:326；StoryState:349；StoryReceipt:374；StoryProjection:381 |
| [runtime/life_engine/story_codec.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/story_codec.py#L1) | scope_values:11；scope_load:15；state_data:20；state_dump:33；state_load:37；refs_dump:61；refs_load:65；payload_dump:75；payload_decode:79 |
| [runtime/life_engine/story_reducer.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/story_reducer.py#L1) | _ordered:10；reduce_story:16；replay_story:77 |
| [runtime/life_engine/story_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/story_repository.py#L1) | StoryFailure:6；StoryRuntimeError:23；fail:30；StoryRepository:34；StoryTransaction:39 |
| [runtime/life_engine/story_runtime.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/story_runtime.py#L1) | checked:21；_owner:38；_world:42；_session:51；_fingerprint:74；StoryRuntime:84 |
| [runtime/life_engine/story_schema.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/story_schema.py#L1) | create_story_schema:76 |
| [runtime/life_engine/story_sqlite_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/story_sqlite_repository.py#L1) | _id:23；decoded:29；_state:42；_event:50；validate_story_data:73；_character_ids:141；StoryTransaction:153；SQLiteStoryRepository:220 |
| [runtime/life_engine/world_codec.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/world_codec.py#L1) | dumps:9；values_dump:13；values_load:17；provenance_dump:24；provenance_load:35 |
| [runtime/life_engine/world_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/world_repository.py#L1) | FailureCode:13；WorldRuntimeError:39；fail:46；WorldSnapshot:51；WorldTransaction:92；WorldRepository:105；_MemoryTransaction:110；validate_update:220；InMemoryWorldRepository:243 |
| [runtime/life_engine/world_runtime.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/world_runtime.py#L1) | checked:18；SwitchResult:32；WorldRuntime:38 |
| [runtime/life_engine/world_schema.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/world_schema.py#L1) | structure:65；expected_structure:72；validate_schema:102；create_world_schema:123；migrate_2_to_3:144；migrate_3_to_4:162；migrate_4_to_5:174；migrate_5_to_6:194；migrate_6_to_7:217；migrate_copy:243；migrate_7_to_8:275 |
| [runtime/life_engine/world_sqlite_repository.py:1](https://github.com/y19870785/life-engine/blob/baa59729babf9ac56a17e02c682de2e3086e3575/runtime/life_engine/world_sqlite_repository.py#L1) | storage_errors:19；decoded:32；_SQLiteTransaction:52；validate_world_data:254；SQLiteWorldRepository:275 |

</details>

部署/工具/Host的配套入口：setup.py、setup_legacy.py、life.py；tools/hermes_character.py、hermes_card.py、hermes_continuity.py、hermes_capabilities.py、hermes_native_host_probe.py、hermes_text_baseline_probe.py；integrations/hermes_living/{adapter,provider_ownership,provider_transport,__init__}.py；examples/experience_x1.py。均纳入AST/调用面核查。

## PR全量观察清单

以下状态为本轮采样时点；本审计PR创建后远端条数会增加，不自动改写本快照。标题仅是GitHub原始数据，不作为能力验收依据。

| PR | 标题 | 观察状态 | Base | Head |
| --- | --- | --- | --- | --- |
| [#1](https://github.com/y19870785/life-engine/pull/1) | 导入 Life Engine v0.3 开发预览 | MERGED | main | `ffcacb41790fef64335fbd29a6fdac7998865fa7` |
| [#2](https://github.com/y19870785/life-engine/pull/2) | 用实际场景和简明步骤重写 README | MERGED | main | `b79d2fe53a54df8ca394b1dff7ce5359ea54a102` |
| [#3](https://github.com/y19870785/life-engine/pull/3) | 新增双层身份角色扮演、世界书与隔离记忆 | CLOSED / Draft | main | `ab227f2179eeaa7ded662d612508a98ad5cdf04a` |
| [#4](https://github.com/y19870785/life-engine/pull/4) | docs(architecture): define persistent world runtime baseline | MERGED | main | `ec253dfb37cea6cb792c77ec364f28b16b7bad15` |
| [#5](https://github.com/y19870785/life-engine/pull/5) | feat(domain): establish world domain model | MERGED | main | `63e3c49ee72ff3414dd7874add60662389fbb7ad` |
| [#6](https://github.com/y19870785/life-engine/pull/6) | feat(import): establish character card compatibility IR | MERGED | main | `c03bb3dd0972b626f7829890f0539ad51c7d10e6` |
| [#7](https://github.com/y19870785/life-engine/pull/7) | feat(world): 建立角色实例与世界会话运行基线 | MERGED | main | `fad902fe3cbaa90023affd18136092cba0b8362d` |
| [#8](https://github.com/y19870785/life-engine/pull/8) | feat(storage): 建立世界运行时持久化与 Schema 3 迁移 | MERGED | main | `0022547731378f682a842be4eb39e4ef3df99293` |
| [#9](https://github.com/y19870785/life-engine/pull/9) | docs: 完成 PR #3 拆分吸收与路线图校准 | MERGED | main | `9286406faad5245dfbea2a82415e2f449952862f` |
| [#10](https://github.com/y19870785/life-engine/pull/10) | ci: 建立最小跨平台测试基线 | MERGED | main | `c98778fff7ee734a14b6cdb0ca6a1184362368fc` |
| [#11](https://github.com/y19870785/life-engine/pull/11) | docs(memory): 冻结 World Memory 架构与 Schema 4 合同 | MERGED | main | `8848b5ea05f49526bb7fb4a56a85acc105998b48` |
| [#12](https://github.com/y19870785/life-engine/pull/12) | feat(memory): 实现 World Memory Runtime 与 Schema 4 | MERGED | main | `39931e6cc5f2f7a69b15cab2bc295ec390a5e400` |
| [#13](https://github.com/y19870785/life-engine/pull/13) | docs: 校准 README 与当前 World Memory 状态 | MERGED | main | `545e21045fd1d71909b9c802a4f8ede802b0be25` |
| [#14](https://github.com/y19870785/life-engine/pull/14) | docs(lore): 冻结 Lore / World Book Runtime 架构 | MERGED | main | `5f1dca8760f8ade37495f54735b09c61dcf35902` |
| [#15](https://github.com/y19870785/life-engine/pull/15) | feat(lore): 实现 Lore / World Book Runtime 与 Schema 5 | MERGED | main | `56a569e05221e80f753c0924dee0a4cb3b442c36` |
| [#16](https://github.com/y19870785/life-engine/pull/16) | docs(story): 冻结 Story Runtime 架构 | MERGED | main | `b2ddbce517b6c02ff3dcb90dcdcb94a5fb16ae07` |
| [#17](https://github.com/y19870785/life-engine/pull/17) | feat(story): 实现 Story Runtime 与 Schema 6 | MERGED | main | `657e638f6b276e2fd7201d6a4541ae891831d6b2` |
| [#18](https://github.com/y19870785/life-engine/pull/18) | docs(prompt): 冻结 Prompt Runtime 架构 | MERGED | main | `9bdd88ced441050dcfa67d8836d348852dbde08b` |
| [#19](https://github.com/y19870785/life-engine/pull/19) | feat(prompt): 实现 Prompt Runtime | MERGED | main | `0dde68dc51570835b31906a075b9711fef923785` |
| [#20](https://github.com/y19870785/life-engine/pull/20) | docs(bridge): 冻结 Controlled World Bridge 架构 | MERGED | main | `adb27f7d50136baceb5042bf7fbd96cb4d6bc22e` |
| [#21](https://github.com/y19870785/life-engine/pull/21) | feat(bridge): 实现 Controlled World Bridge Runtime | MERGED | main | `eb488259faf11c0ac78a264d19a47ad8fca5c028` |
| [#22](https://github.com/y19870785/life-engine/pull/22) | docs(host): 冻结 Host Integration Contract | MERGED | main | `20c4a4bb7a6e2c1b3d99d953ba3a57081465ac00` |
| [#23](https://github.com/y19870785/life-engine/pull/23) | GOV-DOC2: 校准当前状态、Host 沙箱测试与后续路线 | MERGED | main | `77700fa3f0c023630072381fff0e5dc4f7ad0606` |
| [#24](https://github.com/y19870785/life-engine/pull/24) | SP-005H0: Host Integration Sandbox | MERGED | main | `e800352196107e2450cc5d000d1ad257bbc800b0` |
| [#25](https://github.com/y19870785/life-engine/pull/25) | SP-005A0: 冻结 Living Runtime 架构 | MERGED | main | `65dfe9e876743ec60516536deeb9cd004c526bd9` |
| [#26](https://github.com/y19870785/life-engine/pull/26) | SP-005A0-R1: 明确 Intent 预留与 Attempt 重验语义 | MERGED | main | `1e274507ef184095f966712fc10dbad051fd495d` |
| [#27](https://github.com/y19870785/life-engine/pull/27) | SP-005A1: 实现 Living Runtime 与 Schema 8 | MERGED | main | `953aa8fec2cea39e2c68307c23473b3da1d7bb56` |
| [#28](https://github.com/y19870785/life-engine/pull/28) | SP-005A2: 冻结 Living Runtime Host Binding 架构 | MERGED | main | `e22ad30169e6081166afdf2f6dd856bedff908a4` |
| [#29](https://github.com/y19870785/life-engine/pull/29) | SP-005A2-R1: 明确 Session World Revision Fence | MERGED | main | `0212bb89aa6b78f1cf6efccefb6c51adf6a9aa16` |
| [#30](https://github.com/y19870785/life-engine/pull/30) | SP-005A3-B0: 修复 Session World Revision Fence | MERGED | main | `f2ab8b03c2e70f4da567595f5c3fb7f217dcef87` |
| [#31](https://github.com/y19870785/life-engine/pull/31) | SP-005A3-B1: 冻结 Durable Operation Recovery Projection | MERGED | main | `4e85cd41f423c3ff3ee0d2563514a33256507fbe` |
| [#32](https://github.com/y19870785/life-engine/pull/32) | SP-005A3-B1: 实现 Durable Operation Recovery Projection | MERGED | main | `724cbf350c2e8a40232c3ca4c6de58f335730fbd` |
| [#33](https://github.com/y19870785/life-engine/pull/33) | docs: 校准 B1 后 Hermes 综合验收与后续路线 | MERGED | main | `877e3fc4e021a18ea4fb9aa7afe9dfaa3e4deef4` |
| [#34](https://github.com/y19870785/life-engine/pull/34) | SP-005A3: 实现 Living Runtime Host Binding | MERGED | main | `f2135db635233629e13ae9ff5d87549189ffcbea` |
| [#35](https://github.com/y19870785/life-engine/pull/35) | SP-005A4-HLV0: 冻结 Hermes Living Sandbox Validation 架构与测试计划 | MERGED | main | `7fda11c52d71b935812985e480ba397f284e331a` |
| [#36](https://github.com/y19870785/life-engine/pull/36) | GOV-ROADMAP1: 冻结 Life Engine 长期开发路线与阶段治理 | MERGED | main | `0b683a406866578ccfc3c8c3d4313f52e8e5a3fc` |
| [#37](https://github.com/y19870785/life-engine/pull/37) | SP-005A4-HLV1-E0: 记录 Test Home 安全修复与 cron Gate 阻塞 | MERGED | main | `60e4a1bd378c9c80b1f032581d5a6de567c1457d` |
| [#38](https://github.com/y19870785/life-engine/pull/38) | SP-005A4-HLV2: 验证 Hermes Host 生命周期与 Authority 边界 | MERGED | main | `1a52251195c604a0082d620b628855b4a3bba50c` |
| [#39](https://github.com/y19870785/life-engine/pull/39) | SP-005A4-HLV3: 验证 Hermes Living Dry-Run 与 Crash Recovery | MERGED | main | `76c0f69ddcf698060facc1cfdb0e54b1e3b6cb8c` |
| [#40](https://github.com/y19870785/life-engine/pull/40) | GOV-ARCHGATE1: 冻结 HLV3 后架构评审与局部路线 | MERGED | main | `19813571f982b43b3b3503da6d078268d2266753` |
| [#41](https://github.com/y19870785/life-engine/pull/41) | SP-005A4-HLV4-R0: 冻结 Real Delivery Authority 架构 | MERGED | main | `0e40d34071922d1de04d78cacab09ae06e2749ad` |
| [#42](https://github.com/y19870785/life-engine/pull/42) | SP-005A4-HLV4-R1: 实现 Real Delivery Authority | MERGED | main | `becd49749b153de1311c5264f788ae032649a761` |
| [#43](https://github.com/y19870785/life-engine/pull/43) | SP-005A4-HLV4-A0: 冻结 Hermes Dedicated Delivery Adapter 边界 | MERGED | main | `6d7c09a845898d6832dc3bd048713a2b2143257a` |
| [#44](https://github.com/y19870785/life-engine/pull/44) | SP-005A4-HLV4-A1: 实现 Dedicated Hermes Delivery Adapter | MERGED | main | `a843aece99f3a2c51c208a047a69f46cdf69623f` |
| [#45](https://github.com/y19870785/life-engine/pull/45) | SP-005A4-HLV4-A2-R0: 冻结 Dedicated Discord Provider Transport 架构 | MERGED | main | `7080f691c5998679982ae283131aaf85c04d06f3` |
| [#46](https://github.com/y19870785/life-engine/pull/46) | SP-005A4-HLV4-A2-R1: 实现 Dedicated Discord Provider Transport | MERGED | main | `9845abb157c02c8c7b478689922d591f9f0cbf41` |
| [#47](https://github.com/y19870785/life-engine/pull/47) | GOV-SOUL-ROADMAP1: 冻结 Soul Continuity 主线与三轨治理 | MERGED | main | `d4274969e34c146915ad920c9b0f7f2fc7a2c7bb` |
| [#48](https://github.com/y19870785/life-engine/pull/48) | docs: 收敛 Soul Continuity 后续规划与连续性证明门禁 | MERGED | main | `70289ea65669294feccd26e678ba8199e7c066ae` |
| [#49](https://github.com/y19870785/life-engine/pull/49) | docs: 冻结 Soul Continuity 核心架构与验证门禁 | MERGED | main | `977baa362a891828e15a5642661a8dca7ae36f01` |
| [#50](https://github.com/y19870785/life-engine/pull/50) | docs: 冻结 M1-P0 Continuity Persistence Protocol | MERGED | main | `d25f765984f12b51d5193ed13ebddf97d6e37948` |
| [#51](https://github.com/y19870785/life-engine/pull/51) | docs: 提出阶段内自主开发治理与 M1-A 设计任务 | MERGED | main | `96b3b2a536733ca99f9df9510b4e9b1094d34c10` |
| [#52](https://github.com/y19870785/life-engine/pull/52) | docs: 校准 M1-P0 Genesis 首代编号与 SP-006S0 | MERGED | main | `4fcf0eb3c61867a65a6a1c668fce3c47bc3c8e2c` |
| [#53](https://github.com/y19870785/life-engine/pull/53) | docs: M1-A continuity 存储与准入设计 | MERGED | main | `707ff2d393568e0a35894ad690ff3028a3692671` |
| [#54](https://github.com/y19870785/life-engine/pull/54) | test: M1-A 隔离原语探针与 E0 证据 | MERGED | main | `b7cc22184cdb5f62eef6aa1b420cf5b69eba553d` |
| [#55](https://github.com/y19870785/life-engine/pull/55) | X1：隔离试用跨会话记忆与 Agent 虚拟日常 | MERGED | main | `3dc04fcfe665e0ba3eb353ff2afd42205a42cb75` |
| [#56](https://github.com/y19870785/life-engine/pull/56) | 角色卡：新增 Hermes 原生提示与世界书接入 V1 | MERGED | main | `5bcc4c484178d712e59cf3fb9032aa6473b48cfe` |
| [#57](https://github.com/y19870785/life-engine/pull/57) | feat: Hermes 角色跨会话连续性 V2 试用 | MERGED | main | `cf7aae8f9dcbef3bba91ce36bb404924b5a8285e` |
| [#58](https://github.com/y19870785/life-engine/pull/58) | feat: 角色继承宿主工具能力并保持剧情表达 | MERGED | main | `15a9e38fa25b40539c319e20aa65e6e330f8561d` |
| [#59](https://github.com/y19870785/life-engine/pull/59) | feat: 通用角色故事介绍、开场选择与 Hermes 自助导入 | MERGED | main | `c0901db727911488f6a1ad52a608126b49800d8f` |
| [#60](https://github.com/y19870785/life-engine/pull/60) | W0/W1：修复验证路径并定位 Hermes 依赖准备阻断 | MERGED | codex/character-onboarding | `fa66fb484e8e4b636ec40c376bdbc000d1c2c7f5` |
| [#61](https://github.com/y19870785/life-engine/pull/61) | test: 原子发布多进程探针 ready JSON | MERGED | main | `847df109eed8cf0e437172363e635e4fd282eeab` |
| [#62](https://github.com/y19870785/life-engine/pull/62) | docs: 近一周开发复盘、流程改进与项目文档校准 | OPEN / Draft | main | `f8393fa4698b55d75bfa891df1629266de8e2fe9` |

## 本轮原件摘要

临时目录只是本机复核辅助；远端独立复核应优先使用固定Git对象、可点击CI原件和本文命令重跑，不假设可访问本机私有路径。

| 原件 | SHA256 |
| --- | --- |
| `le-reset-01-prs.json` | `6c87d40594e06866595368e45509e2f484740d3c73a1b7f87b310bd715d8d25a` |
| `le-reset-01-runs.json` | `9d9b9a319be741d264c842d367302fac3b6bc57baa2c95981d09207523269b52` |
| `le-reset-01-x1.json` | `7e4b24581a5eef49e6f0b725aab7e58a974813fb674c0a2dac3f861d0fca45af` |
| `le-reset-01-local-eval.json` | `0926e3723569036f1975cc9dc9d87aaa8d7d97c2fae0dbcfa01d1893c03197b4` |

全量日志/终态与文档检查结果见Q1/Q4；本轮不创建或引用不存在的独立审核结论。新增文档不改产品行为，因此没有新增同构测试；既有全量及实际CLI/eval结果分别记录，不互相替代。
