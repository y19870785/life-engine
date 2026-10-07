# v0.3 验证记录

## CURRENT CANONICAL STATE — GOV-SOUL-ROADMAP1

A2-R1 canonical implementation commit = `a552a2d0846ff024b930d0d802228b863a6da74f`。[PR #46](https://github.com/y19870785/life-engine/pull/46) Squash Merge 后，[exact main push CI #37297156541](https://github.com/y19870785/life-engine/actions/runs/37297156541) 的有效 attempt 3 为 `push / main / exact SHA / completed / success`，Ubuntu、Windows × Python 3.11、3.12 全部 SUCCESS；`SP-005A4-HLV4-A2-R1 = DONE`。attempt 1、2 均 CANCELLED；attempt 2 后继续执行 attempt 3 构成 `CI_RECOVERY_GOVERNANCE_DEVIATION = YES`，详见[治理记录](architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md)。技术证据未失效，但该偏差不抹去。

Soul Continuity = `ACTIVE_MAINLINE`；Host Integration = `DEFERRED`；Full Private RP = `FROZEN_EXTERNAL_BLOCKER`。下一阶段 `SP-006S0 Soul Continuity Architecture Freeze = NEXT / NOT AUTHORIZED`。A2 retry、HLV4-B 与真实发送均未授权；`REAL_HOST_PLUGIN_LOAD / REAL_HOST_DELIVERY_BOUNDARY_PASS / REAL_HOST_SENT / ACKNOWLEDGED = NOT_ACQUIRED`，`ACK_VALIDATOR = HOST_GAP`，`REAL_SEND = NO`。

`DATA_SCHEMA = 8`；`Schema Signature = SP-005A-living-runtime-v1`；`Prompt Template = SP-004K-prompt-v1`；`PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES`。下列 HLV/GOV-DOC3/B1 记录为当时证据，不改写历史测试结论。

## HISTORICAL — Post-HLV3 / GOV-ARCHGATE1 当前状态快照（2026-10-03）

canonical Base：`9d064d0a90d8d02a5dab04a6baee18bbbf6dcdc2`；PR #39 Squash Merge 与 exact main push CI #37122681930 四矩阵已独立核验。SP-005A4-HLV0 = DONE；SP-005A4-HLV1 = DONE；SP-005A4-HLV2 = DONE；SP-005A4-HLV3 = DONE。REAL_HOST_READONLY_PASS / REAL_HOST_LIFECYCLE_PASS / REAL_HOST_LIFECYCLE_AUTHORITY_PASS / REAL_HOST_DRY_RUN_PASS = CONFIRMED；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。

ARCHITECTURE_REVIEW_GATE = PASS；LOCAL_ORDER = HLV4 → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。ARCHITECTURE_CHANGE_REQUIRED = NO；ROADMAP_DIRECTION_CHANGE = NO。完整证据、依赖与授权边界见 [GOV-ARCHGATE1 Gate 记录](architecture/GOV-ARCHGATE1-POST-HLV3-REVIEW.md)。GOV-ARCHGATE1 = DRAFT_REVIEW_PENDING；SP-005A4-HLV4 = NEXT / NOT AUTHORIZED，独立任务与明确授权前 REAL_SEND = FORBIDDEN。Roadmap state != execution authorization。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = AFTER_HERMES_ADAPTER_STABILIZATION / NOT AUTHORIZED；Memory Evolution V1 = AFTER_SP-005A2-P1 / PLANNED。OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED_BY_OFFICIAL_HOST_CAPABILITY（H1/H2 blocker 保留）。本轮 NO_REAL_HOST_OPERATION = true、NO_REAL_SEND = true；历史证据只引用，不重跑。

## GOV-ARCHGATE1 文档校准检查

本轮仅修改13份Markdown：Gate记录、两份Roadmap、README/VALIDATION/KNOWN-ISSUES、Host指南与HLV0架构，以及主入口所引用的A2/A3状态页、HLV matrix和HLV3报告治理状态。额外页面只更新顶部引用/历史标签，避免仍把HLV1～3写成未来任务；执行代码、case语义、Schema、Prompt、workflow均zero diff。

146个相关本地链接/锚点（含20个入站引用）检查PASS；状态、canonical SHA、局部顺序与git diff --check均PASS。HLV1/HLV2报告和E0未改，既有GOV-DOC3/B1历史正文逐项保持不变；HLV3只校准DONE治理状态，不更改执行结果、计数或manifest。不重跑Host、Living、permit、fake/real transport；Draft exact Head四矩阵由既有CI workflow执行并在交付报告独立核验，不使用旧main/PR CI替代。

## HISTORICAL — HLV0 治理快照（2026-10-01）

以下原状态与SHA仅指HLV0时点，不覆盖顶部当前状态。

事实基线：`eedc32b719336ba063b99da95eac4e2b6a56c0c5`；[PR #34](https://github.com/y19870785/life-engine/pull/34) 已 Squash Merge，parent 为 `b78b849b1bfac1cbd28359cfb317fd1d4cb84402`；[exact main push CI #36847806554](https://github.com/y19870785/life-engine/actions/runs/36847806554) 为 push / main / exact SHA、completed / success，Ubuntu / Windows × Python 3.11 / 3.12 全部 SUCCESS，并经独立核验。

SP-005A3 = DONE；SP-005A3-B0 = DONE；SP-005A3-B1 Architecture / Implementation = DONE。A3 已实现 Host-neutral Binding Authority、protected metadata、trusted routing、authority/plugin lifecycle、capability vault、recovery-only capability、HostIdentityEnvelope、LivingHostFacade、one-time execution permit、DeliveryEvidence、fake transport、legacy fence 与 crash recovery。B01-B34 = SIMULATED_PASS；B1-08_CORE_PASS / B1-09_CORE_PASS 原样保留，不升级历史证据。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；SP-005A2-P1 = NOT AUTHORIZED；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；NO_REAL_SEND = true。Hermes real Host validation = PENDING_REAL_HOST_VALIDATION；OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED；H1 = BLOCKED；H2 = BLOCKED。

SP-005A4-HLV0 = DONE；当前 canonical main 为 `08bf82e89f7a4572f4931105cc5e6927ae1c5214`，已独立核验。下一任务 SP-005A4-HLV1 须在 GOV-ROADMAP1 正式 DONE 后另行发布与授权。以下“本轮”指 HLV0 历史文档阶段，仅冻结架构、验证计划与治理文档。NO_REAL_HOST_OPERATION = true。本轮没有执行 Hermes、plugin load/reload、Gateway restart、Living mutation、permit consume、fake send、real send 或 cron。H-LV1～H-LV3 是未来分阶段授权的计划，均 NOT_EXECUTED / NOT_AUTHORIZED；H-LV4 = DEFINED_ONLY / NOT_AUTHORIZED。历史 2026-09-30 环境仅为 HISTORICAL_EVIDENCE，不能默认复用。

架构与权限见 [HLV0 architecture](architecture/SP-005A4-HERMES-LIVING-VALIDATION.md)，逐项验证见 [HLV matrix](planning/SP-005A4-HERMES-LIVING-VALIDATION-MATRIX.md)。

## HISTORICAL — HLV0 文档校准与验证范围

本地完整回归：Windows / Python 3.12.10 / Node 22.23.2，`py -3.12 -X utf8 -m unittest discover -s tests -q`，443 total / 442 passed / 1 existing platform skip / 0 failed / 0 errors，366.740秒。Runtime/tests未改；沿用canonical完整套件。Draft exact Head四矩阵需另行核验，不能用Base main CI替代。

本轮仅修改10份Markdown：6份指定现有文档、2份新增HLV0架构/矩阵，另校准A2架构与A3验证页顶部状态，原因是它们作为主入口链接目标仍显示A3 Draft旧状态；旧正文与技术合同保留为HISTORICAL。Runtime/tests/Schema/Prompt/workflow diff均为空，NO_REAL_HOST_OPERATION = true、NO_REAL_SEND = true。

本轮校验覆盖8份current-state文档的14个关键状态；RV-01～RV-12、CR-01～CR-10共22场景各12字段；本地链接/锚点与git diff --check；原Hermes历史报告zero diff，VALIDATION/HOST-SANDBOX/KNOWN-ISSUES原记录非空行逐行按原顺序保留。没有升级A3模拟证据、B1 Core标签或历史真实发送。

## HISTORICAL — GOV-DOC3 / B1 与既有 Host 指南快照

以下原文保留历史状态、计数、finding 和步骤；其中“当前”“本轮”“尚未实现”均指当时，不覆盖顶部 CURRENT CANONICAL STATE，也不是本轮操作授权。原 legacy 入口的 gap 记录保留；A3 新 dispatcher 的受信 routing fence 已 SIMULATED_PASS，但旧 Hermes 插件未接入 A3，不能自动获得此保证。真实验证仍需逐阶段独立授权。

## GOV-DOC3 文档校准验证（2026-10-01）

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

本次只修改 Markdown 文档，重新读取 B1 后 canonical 文档并只读核对 legacy 分发、实例标识、state_check、H0 probe 与 receipt 边界，没有修改 Runtime、tests、Schema、Prompt 或执行真实 Host 操作。

Windows / Python 3.12.10 / Node 22.23.2：执行 `py -3.12 -X utf8 -m unittest discover -s tests -q`，397 total / 396 passed / 1 skipped / 0 failed / 0 errors，294.749 秒。平台跳过沿用既有 Unix symlink 用例。仓库唯一 CI workflow 为 `.github/workflows/tests.yml`，运行完整 unittest 四矩阵；没有独立的可执行文档/link/status 检查脚本，本轮另做相对链接/锚点、状态用词、历史统计和 docs-only diff 检查。Draft PR 的 exact Head CI 需独立核对，不能用下方 B1 main CI 替代。

本轮 14 份 Markdown 变更的 106 个相对链接/锚点检查通过，`git diff --check` 通过；历史 JSON 的 59 个 rows 与统计一致，两份源报告的 SHA-256 与 Owner 提供的清单一致。检查未把私人 sender/channel/message ID、实际 Host 路径或实例/代次标识写入变更文档；原始证据清单中的其他文件没有冒充已复核。Runtime / tests / workflow diff 均为空。

## HISTORICAL — B1 后 canonical 当前状态（2026-10-01）

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

事实基线：`f83d36c76fea6de1a31b449535d5df6cea3909b5`。[PR #32](https://github.com/y19870785/life-engine/pull/32) 经独立审核、Ready 后轻量终审与 Squash Merge，唯一 parent 为 `a27caf372a263932346d5b193ca35c92fea6f5dd`。GOV-DOC3 开工复核远端 main exact 指向该 SHA，工作树 clean；[main push CI #36795009694](https://github.com/y19870785/life-engine/actions/runs/36795009694) 为 push / main / exact SHA，completed / success，Ubuntu / Windows × Python 3.11 / 3.12 四矩阵均 PASS，无待处理的 B1 范围 blocker。

SP-005A3-B1 Architecture / Implementation = DONE。B1 专项 16 PASS；A1 48 个合同编号 / 52 个映射测试 PASS；B0 R1 回归 10 PASS；B1 实施时本地 full unittest 为 397 total / 396 passed / 1 skipped / 0 failed / 0 errors。具体测试映射见 [B1 验证](SP-005A3-B1-VALIDATION.md)，这些计数属于 B1 实施记录，不是历史 Hermes 59 项统计，也不代表真实 Host 验收。

B1-08_CORE_PASS、B1-09_CORE_PASS 仅证明 Core 子集。Host authority/epoch/token、context handle、prepare/claim ticket、execution permit、transport、完整 legacy routing fence 仍未实现；对应 Host 部分 DEFERRED_TO_A3 / NOT_EXECUTED。A3 整体 BLOCKED，须另行授权剩余实施；B06/B28/B14 不升级完整 PASS。B1 不提供新的真实 World/Lore/Story/Bridge mutation 测试入口。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。SP-005A2-P1 = NOT AUTHORIZED；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES。Hermes / OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Living R01–R12 = NOT_EXECUTED；Full Private RP / H1 / H2 = BLOCKED。任何 blocker enforcement verified 都不等于对应功能 PASS。

## Hermes canonical comprehensive evaluation — 2026-09-30

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

本节只保存当日 canonical snapshot 的历史结果，不是 B1 后最新自动测试或 Host 验收状态。脱敏环境、证据来源与 finding 见[完整历史摘要](validation/HERMES-COMPREHENSIVE-EVALUATION-2026-09-30.md)。

| 历史统计 | 数量 |
| --- | ---: |
| total | 59 |
| PASS | 42 |
| PASS_WITH_LIMITATION | 8 |
| PENDING（历史评测枚举，保留原值） | 1 |
| BLOCKED | 1 |
| NOT_EXECUTED | 7 |
| FAIL | 0 |
| critical_findings | 0 |

历史总体结论：CURRENT IMPLEMENTED SCOPE ACCEPTABLE FOR CONTROLLED LOCAL TESTING。报告引用的上一轮一次受控 Discord 文字发送保持 SENT / ACK UNKNOWN；综合评测本轮新发 0 条；Organic Contact 为 ORGANIC_CONTACT_NOT_DUE / silent / recent_conversation，external send count = 0。没有将单次 Soul Continuity send 当成 organic eligible real-send 链路通过，没有把 API 回读当作 ACK。World/Lore/Story/Bridge grant mutation 与 grant revoke 的真实 Host 状态仍 NOT_EXECUTED — NO SAFE TEST PATH。

以下按阶段保留历史测试环境、数量与限制；其中“本轮”均指对应历史阶段，不覆盖本文顶部当前事实。

## SP-005A3-B0 实施验证（历史测试记录；阶段 DONE）

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

固定 Base：`3367a8906060af129d7ee29ef4da7959926b5d0b`。Runtime 仅增加 session World revision 的事务内 fence；R1-01～R1-06 与补充回归的具体测试见 [B0 实施映射](SP-005A3-B0-VALIDATION.md)。新增 10 项测试，包含独立进程 World 更新、提交后 os._exit 响应丢失及原 operation receipt recovery。原 A1 的 [48 项合同映射](SP-005A1-VALIDATION.md)继续保留。

本地完整测试：Windows、Python 3.12.10、Node 22.23.2；`py -3.12 -m unittest discover -s tests -v`，381 项，380 passed、1 skipped（既有 Unix symlink 平台跳过）、0 failed、0 errors，282.666 秒。新增 10 项 B0 测试全部通过；按日志核验 A1 48 个合同编号映射的 52 个具体测试全部通过。32 个相对链接及锚点检查、`git diff --check` 通过。exact Head 四矩阵 CI 结果在 Draft PR 和交付报告中关联。B06/B28/B14 仅 Core 子集验收，不代表 A3 Host 层 PASS。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。SP-005A3-B0 = DONE；SP-005A3 = BLOCKED（Host 层未完成，恢复实施须另行授权）；SP-005A2-P1 = NOT AUTHORIZED；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES。没有真实 Host 操作或发送，H1/H2、Full Private RP 保持 BLOCKED。

## SP-005A1 实施验证（历史测试记录；阶段 DONE）

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

固定 Base：`9159c493ad435cf947ed8c0fef278e1f5fb9dc83`。本次实现 `DATA_SCHEMA = 8`、`SP-005A-living-runtime-v1`；Prompt Template 仍为 `SP-004K-prompt-v1`。原始 A0/R1 判据与具体测试的 48 项对应关系见 [实施映射](SP-005A1-VALIDATION.md)，部署边界与 copy migration/rollback 见 [操作说明](LIVING-RUNTIME.md)。

自动证据来自独立临时安装、Schema 7 canonical 原版发行包、进程 crash、两进程 tick/Scope 竞争、固定 DST fixture 和 fake delivery validator。未调用生产 Host、渠道、ComfyUI 或 TTS。Hermes/OpenClaw real Host validation 均保持 PENDING_REAL_HOST_VALIDATION；Full Private RP/H1/H2 继续 BLOCKED。

最终本地完整测试：Windows、Python 3.12.10、Node 22.23.2；`python -m unittest discover -s tests -v`，371 项，370 通过、1 项既有 Unix symlink 平台跳过，0 失败/错误，245.458 秒。新增 48 项 Living 测试及 3 项 Schema 8 migration/rollback 测试；48 项架构矩阵逐项映射，测试数量不等于矩阵编号数量。其后仅清理四个模块 EOF 空行，并核对 AST 未变。100 个相对链接检查通过，`git diff --check` 通过。远端 Ubuntu / Windows × Python 3.11 / 3.12 以本 PR exact Head 的 CI 记录为准；PR 描述和实施报告提供 run 关联。下方 H0 和 2026-09-26 数据是历史基线，不代表 A1 的 schema 或测试数量。


## SP-005H0 实施验证（2026-09-27 历史记录；实现 DONE）

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

固定 Base：`694b45a6f1cd10e28bef96a7e98261c1f85d66f6`。本阶段新增原生插件 `doctor`/`sandbox-probe`、durable 调用身份封套、文件化沙箱报告与交付证据链校验。报告不会签发真实 Host PASS，也不改变 Full Private RP 能力门禁。

审核修订后的顶层语义：`ok` 仅表示命令执行成功，`report_generated` 表示完整报告已生成；真实验证只看 `validation_result` 与 `validation_passed`，当前所有路径的 `validation_passed` 固定为 false。无 probe、模拟/unverified_capture 一致性通过、新进程本地探测通过，都仍为 PENDING_REAL_HOST_VALIDATION；probe 不一致或 generation drift 为 FAIL。生成 FAIL 报告不是命令异常，因此 ok=true、退出码 0；执行异常时 ok=false、report_generated=false、validation_result=FAIL、validation_passed=false，退出码 1。自动消费者不得使用 ok 或退出码判断 Sandbox 完成。

最终本地完整测试：Windows、Python 3.12.10、Node 22.23.2；执行 `python -m unittest discover -s tests -v`，320 项，319 通过、1 项既有 Unix symlink 测试平台跳过，0 失败/错误，耗时 198.235 秒。新增 12 项测试，并扩展既有两个原生插件合同测试。`git diff --check` 与三份更新文档相对链接检查通过。本机 Python 3.11 launcher 指向失效路径，未宣称本地 3.11 通过；其结果由 Draft PR 的独立 CI 矩阵提供。自动通过不等于真实 Host 或独立审核通过。

| 验证项 | 自动证据与边界 |
| --- | --- |
| Hermes | 模拟 PluginContext/get_hermes_home，实际加载生成的 Python 插件并调用独立 Python 引擎；错误 Profile 拒绝，status/doctor 身份一致，reload 更换插件代次且清空 hook 证据 |
| OpenClaw | Node 加载生成的 JS 插件，最小 SDK 替身；错误 agentId、缺少 workspace、调用后身份变更均拒绝；status/doctor、photo disabled、reload 重新验证 |
| stable instance / generation | 真实临时安装、新 Python 子进程读取同一 instance/data root；配置重建 generation 后旧 attestation 被拒绝，要求重验 |
| wake | 复用现有 contact opportunity、quiet hours、无联系理由和并发领取测试；补充 cooldown/daily budget 静默测试；插件 probe 仅 preview |
| photo | 自动验证关闭时为 DISABLED；既有假 ComfyUI 和本实例 media outbox 测试继续保留，未使用真实 GPU |
| delivery / receipt | 检查不能跳级、operation/target/message ID 必须一致；模型 evidence 不能登记 delivered；没有验证器时不能升级 SENT/ACKNOWLEDGED |
| Full Private RP | 一致性验证通过后，既有 require_private_context_isolation 仍拒绝缺失 capability；HISTORY_ISOLATION/final-output 门禁未弱化 |

真实 Hermes / OpenClaw Sandbox 均为 **PENDING_REAL_HOST_VALIDATION**。本轮只检查 Windows PATH 中的可执行命令位置，未发现 Hermes/OpenClaw；这不代表 WSL 或其它环境没有安装。没有选定独立测试 Profile/Agent、Session 或本人聊天目标，故未安装或更改生产插件、重启 Gateway、执行真实聊天/发送、读取生产聊天历史，也未探测 compatibility fork。实际 Host version、profile/config/Gateway/target evidence 为 **UNKNOWN**。测试中的版本和身份是模拟数据，不能当作实机记录。

真实 Host restart/upgrade：`NOT_EXECUTED — production host isolation unavailable`。新 Life Engine 子进程与模拟插件 reload 的通过结果只证明自动合同。OpenClaw 跨 Gateway/Profile 的唯一性尚未证明；当前没有渠道 receipt 验证器。操作方法、结构化输出与剩余实机检查见[沙箱指南](HOST-SANDBOX-TESTING.md)。

H0 当时数据版本为 `DATA_SCHEMA = 7`，Schema Signature 为 `SP-004F-bridge-runtime-v1`，Prompt Template 为 `SP-004K-prompt-v1`；没有 Schema 迁移、Host Core patch 或 H1/H2 实现。最终阶段结论由 ChatGPT / 小雪审核 Draft PR 与真实证据后决定。

## 历史 canonical validation（2026-09-26）

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

固定 canonical main：`8e2db9ae50b1ac3c46bb1953851d14442c58f085`。合并 H0 后的 [main push CI #36088249987](https://github.com/y19870785/life-engine/actions/runs/36088249987) 在 Ubuntu / Windows × Python 3.11 / 3.12 四矩阵全绿。此处不推断本次 CI 的测试数量；下方 217 项是 SP-004B1 时点的**历史**记录。

该历史基线 `DATA_SCHEMA = 7`，World Schema Signature 为 `SP-004F-bridge-runtime-v1`，Prompt template 为 `SP-004K-prompt-v1`。World、Memory、Lore、Story、Bridge、Prompt Core Runtime 与 H0 Host Integration Contract 已进入 main；真实 Host Private RP 尚未通过能力门禁。自动 CI 和模拟宿主测试不等于真实渠道送达。

### Hermes Host Capability Audit

官方 final-output commit 能力仍阻塞 H1。CAP1 已判定需要 upstream，CAP2 提案已完成，CAP3 在 [PR #120170](https://github.com/NousResearch/hermes-agent/pull/120170) 获得 in-scope 方向反馈，官方实现仍待完成。独立的 compatibility fork 实机验证：attempt #1 因 recovery durability **FAIL**；R2 修复 recovery 后 rerun 又因 stale session incarnation / A→B→A writer fence **FAIL**，fork 路线已停止。以上是 **Hermes fork** 的 Host 能力实验，绝非 Life Engine main CI 结果，也不构成生产安全认证。

### OpenClaw Host Capability Audit

本机 2026.9.5 的 CAP0 结果：`HOST_CAPABILITY_INSUFFICIENT`。对 2026.9.6 做了相关边界的只读比对；CAP1 结果：`UPSTREAM_CHANGE_TOO_DEEP`。已有结构化身份、run/session ID、`lifecycleRevision`、transcript writer fencing 与多个 Hook，但缺统一的 fail-closed final-output commit / replay / delivery / stream 授权。宿主源码审计与正式 Life Engine Host 沙箱验收须分开记录。

## SP-004B1 时点自动验证（历史）

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

基线：`d89b362701e614415354c38302a102f593a0a0a7`（SP-004B1 合并提交）。[GitHub Actions 运行记录](https://github.com/y19870785/life-engine/actions/runs/35748952847) 已完成且通过：Ubuntu / Python 3.11、Ubuntu / Python 3.12、Windows / Python 3.11、Windows / Python 3.12。当时完整 `unittest` 共 217 项；Windows 为 216 项通过、1 项既有平台跳过。

这些自动测试覆盖代码合同与模拟宿主，不等于真实 Hermes / OpenClaw Gateway、聊天渠道、GPU 出图或发送回执闭环验收；也不表示新的 World Memory 已自动接入宿主每轮聊天。

## 2026-09-13 历史验证

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

测试环境：Linux，Python 3.12.14，Node.js 24.19.0。验证日期：2026-09-13。

执行：python -m unittest discover -s tests -q。

50 项测试通过。原有 31 项覆盖角色状态/联系策略、SQLite 并发领取、模拟隔离、ComfyUI 假 HTTP 服务流程、照片复用/未知失败不重排、旧安装保护和 v0.1 迁移。新增 19 项覆盖永久入口、升级备份、恢复原子切换、代码回退与原生适配器。

永久安装验证使用真实临时文件系统与独立 Python 子进程：安装后删除解压目录，改变 HERMES_HOME，重新运行状态与维护入口仍可读取已保存记忆。重复安装保留手工修改过的 agent.json 与数据库字节；不同宿主即使内部角色名相同，也使用不同实例与数据库。

升级验证将有变化的新代码复制为独立版本；确认切换版本后配置与数据库内容不变。构造语法损坏的新代码，导入检查拒绝激活；回退到原代码后，保留新代码运行期间写入的记忆。

备份验证包含保持 WAL 连接打开时已提交的新记录与实际图片文件。恢复验证保留原数据代次、重写所复制照片的有效路径并暂停主动联系；损坏备份与模拟注册指针写入失败都不会先删除当前可用数据。未知数据库 schema 会阻止升级。

Hermes 原生桥接器使用模拟 PluginContext 与当前 Profile 上下文，实际调用独立 Python 引擎，验证状态补入、主人匹配和跨 Profile 拒绝。OpenClaw 桥接器由 Node 实际加载，使用最小 SDK/宿主接口替身调用真实 Python 引擎，验证 agentId/workspace 双重匹配、工具调用和主人入站标记。它们是适配器契约测试，不等价于在真实 Hermes/OpenClaw Gateway 中测试。

OpenClaw 图片暂存验证只接受本实例生成目录中的图片，复制到当前 workspace 后内容一致；其他文件和冲突文件被拒绝。没有为此扩大宿主全局文件访问权限。

另执行安装 CLI 的非交互预览/应用/维护入口检查。未访问用户的本地宿主、未启用其定时任务、未发送真实微信消息、未调用真实 GPU。没有实测 Windows/macOS 系统服务、容器重建、真实断电或磁盘硬件故障；这些需要在最终运行环境验证，持续保存仍依赖持久磁盘/卷和可用备份。
