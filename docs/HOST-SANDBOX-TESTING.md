# Hermes / OpenClaw Host Sandbox 测试指南

## CURRENT CANONICAL STATE — GOV-SOUL-ROADMAP1

[Soul Continuity 主线](architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md)已设为 `ACTIVE_MAINLINE`；Soul Continuity Sandbox 仍可在**单独明确授权**下受控测试，本治理任务不授权任何 Host 操作。A2 retry / HLV4-B 已转入 `DEFERRED Host Integration Track / NOT AUTHORIZED`，不再是默认下一阶段。Full Private RP = `FROZEN_EXTERNAL_BLOCKER / NOT FOR PRODUCTION`；其 Core RP Runtime 保留。

A2-R1 canonical implementation commit = `a552a2d0846ff024b930d0d802228b863a6da74f`；`SP-005A4-HLV4-A2-R1 = DONE` 只确认本地 provider transport 实现。`REAL_HOST_PLUGIN_LOAD / REAL_HOST_DELIVERY_BOUNDARY_PASS / REAL_HOST_SENT / ACKNOWLEDGED = NOT_ACQUIRED`，`ACK_VALIDATOR = HOST_GAP`，`REAL_SEND = NO`。本指南后续旧步骤不构成 Gateway、credential、inbound 或发送授权。

## HISTORICAL — Post-HLV3 / GOV-ARCHGATE1 当前状态快照（2026-10-03）

canonical Base：`9d064d0a90d8d02a5dab04a6baee18bbbf6dcdc2`；PR #39 Squash Merge 与 exact main push CI #37122681930 四矩阵已独立核验。SP-005A4-HLV0 = DONE；SP-005A4-HLV1 = DONE；SP-005A4-HLV2 = DONE；SP-005A4-HLV3 = DONE。REAL_HOST_READONLY_PASS / REAL_HOST_LIFECYCLE_PASS / REAL_HOST_LIFECYCLE_AUTHORITY_PASS / REAL_HOST_DRY_RUN_PASS = CONFIRMED；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED；ACK_VALIDATOR = HOST_GAP。

ARCHITECTURE_REVIEW_GATE = PASS；LOCAL_ORDER = HLV4 → Hermes Living Adapter Stabilization → SP-005A2-P1 → Memory Evolution V1。ARCHITECTURE_CHANGE_REQUIRED = NO；ROADMAP_DIRECTION_CHANGE = NO。完整证据、依赖与授权边界见 [GOV-ARCHGATE1 Gate 记录](architecture/GOV-ARCHGATE1-POST-HLV3-REVIEW.md)。GOV-ARCHGATE1 = DRAFT_REVIEW_PENDING；SP-005A4-HLV4 = NEXT / NOT AUTHORIZED，独立任务与明确授权前 REAL_SEND = FORBIDDEN。Roadmap state != execution authorization。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；SP-005A2-P1 = AFTER_HERMES_ADAPTER_STABILIZATION / NOT AUTHORIZED；Memory Evolution V1 = AFTER_SP-005A2-P1 / PLANNED。OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED_BY_OFFICIAL_HOST_CAPABILITY（H1/H2 blocker 保留）。本轮 NO_REAL_HOST_OPERATION = true、NO_REAL_SEND = true；历史证据只引用，不重跑。

## HISTORICAL — HLV0 治理快照（2026-10-01）

以下原状态与SHA仅指HLV0时点，不覆盖顶部当前状态。

事实基线：`eedc32b719336ba063b99da95eac4e2b6a56c0c5`；[PR #34](https://github.com/y19870785/life-engine/pull/34) 已 Squash Merge，parent 为 `b78b849b1bfac1cbd28359cfb317fd1d4cb84402`；[exact main push CI #36847806554](https://github.com/y19870785/life-engine/actions/runs/36847806554) 为 push / main / exact SHA、completed / success，Ubuntu / Windows × Python 3.11 / 3.12 全部 SUCCESS，并经独立核验。

SP-005A3 = DONE；SP-005A3-B0 = DONE；SP-005A3-B1 Architecture / Implementation = DONE。A3 已实现 Host-neutral Binding Authority、protected metadata、trusted routing、authority/plugin lifecycle、capability vault、recovery-only capability、HostIdentityEnvelope、LivingHostFacade、one-time execution permit、DeliveryEvidence、fake transport、legacy fence 与 crash recovery。B01-B34 = SIMULATED_PASS；B1-08_CORE_PASS / B1-09_CORE_PASS 原样保留，不升级历史证据。

DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1；SP-005A2-P1 = NOT AUTHORIZED；PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES；NO_REAL_SEND = true。Hermes real Host validation = PENDING_REAL_HOST_VALIDATION；OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP = BLOCKED；H1 = BLOCKED；H2 = BLOCKED。

SP-005A4-HLV0 = DONE；当前 canonical main 为 `08bf82e89f7a4572f4931105cc5e6927ae1c5214`，已独立核验。下一任务 SP-005A4-HLV1 须在 GOV-ROADMAP1 正式 DONE 后另行发布与授权。以下“本轮”指 HLV0 历史文档阶段，仅冻结架构、验证计划与治理文档。NO_REAL_HOST_OPERATION = true。本轮没有执行 Hermes、plugin load/reload、Gateway restart、Living mutation、permit consume、fake send、real send 或 cron。H-LV1～H-LV3 是未来分阶段授权的计划，均 NOT_EXECUTED / NOT_AUTHORIZED；H-LV4 = DEFINED_ONLY / NOT_AUTHORIZED。历史 2026-09-30 环境仅为 HISTORICAL_EVIDENCE，不能默认复用。

架构与权限见 [HLV0 architecture](architecture/SP-005A4-HERMES-LIVING-VALIDATION.md)，逐项验证见 [HLV matrix](planning/SP-005A4-HERMES-LIVING-VALIDATION-MATRIX.md)。

## HISTORICAL — GOV-DOC3 / B1 与既有 Host 指南快照

以下原文保留历史状态、计数、finding 和步骤；其中“当前”“本轮”“尚未实现”均指当时，不覆盖顶部 CURRENT CANONICAL STATE，也不是本轮操作授权。原 legacy 入口的 gap 记录保留；A3 新 dispatcher 的受信 routing fence 已 SIMULATED_PASS，但旧 Hermes 插件未接入 A3，不能自动获得此保证。真实验证仍需逐阶段独立授权。

## Living Core 合并后的适用边界

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

当前事实基线 `f83d36c76fea6de1a31b449535d5df6cea3909b5` 已包含 A1、B0、B1 Core，DATA_SCHEMA = 8、Schema Signature = SP-005A-living-runtime-v1、Prompt Template = SP-004K-prompt-v1。[B1](SP-005A3-B1-VALIDATION.md)只新增只读 durable recovery，不提供 Host binding 或发送资格；A3 剩余实现仍 BLOCKED，需新任务授权。下文旧插件流程只适用于未 enrollment 的 legacy 隔离测试；enrolled 实例不得沿用此流程或绕过 LIVING_HANDOFF_REQUIRED。现有 gate 尚未覆盖所有副作用之前的入口，详见 [已知问题](KNOWN-ISSUES.md)。[A3 矩阵](planning/SP-005A3-HOST-BINDING-TEST-MATRIX.md)的 Host 部分仍未完成。

默认 DRY_RUN / NO_REAL_SEND。本次 GOV-DOC3 不安装插件、不调用 Host、不 restart、不启用 cron、不发送。任何新的真实测试需独立授权。Hermes / OpenClaw real Host validation 均保持 PENDING_REAL_HOST_VALIDATION，Living H0-RV R01–R12 = NOT_EXECUTED。

## 2026-09-30 canonical Hermes 综合评测（历史）

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

Hermes 0.21.3 在独立 HERMES_HOME / Profile、独立 canonical permanent root 与 Discord 专用测试渠道上完成历史综合评测；干净源码为 `861734b0c4179e56a3251a775d831cd246278d7f`，release 为 `0.3.0-eefb56b42b6eb8f4`。插件加载、Owner binding 与错误身份拒绝、Soul Continuity context、上一轮一次真实文字发送的证据、当轮静默 gate、持久性及备份/恢复均写入历史报告，生产环境未被污染。完整统计、证据来源与限制见[脱敏历史记录](validation/HERMES-COMPREHENSIVE-EVALUATION-2026-09-30.md)。

报告引用的上一轮发送 external send count = 1，无自动重试；综合评测本轮新发 0 条；边界仍是 SENT / ACK UNKNOWN。真实 wake --preview 返回 silent / recent_conversation，即 ORGANIC_CONTACT_NOT_DUE、send count = 0；未证明自然 eligible 的 organic real-send 闭环。World/Lore/Story/Bridge grant mutation 与 grant revoke 均 NOT_EXECUTED — NO SAFE TEST PATH。B1 没有新增这些 Host mutation 入口，不升级其状态。

## B1 后探测、绑定与回执的含义

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

| 项目 | 当前含义与限制 |
| --- | --- |
| sandbox-probe / live hook | H0 捕获本次插件加载中的 hook 证据；fresh-process probe 无 live hook 仍 HOOK_REVALIDATION_REQUIRED。B1 recovery 查询不生成 hook evidence。 |
| plugin_epoch | 已有 H0 探测代次；尚无 A3 token/ticket/permit 的撤销系统，不能冒充完整 capability 生命周期。 |
| Gateway restart | 两个 Python 进程或模拟 reload 不是真实 Gateway restart；新的隔离 Gateway 与当前 binding 重验仍需独立验证。 |
| binding authority | H0 registry/Host home 绑定与 B1 Core trusted local assertion 均不等于 A3 per-install Host authority。 |
| receipt | B1 durable operation receipt 证明 Core 提交；真实 Discord message ID / API 回读不构成受信 ACK。当前没有渠道 ACK validator。 |

历史受控实测不升级机械报告的 validation_passed，也不完成 A3 Living R01–R12。下文的操作流程保留为另行授权后的测试指南，不表示本轮已执行。

> **当前允许：Soul Continuity / Living Agent / Host Sandbox 受控测试。当前不允许：Full Private RP 生产部署。** 已完成的 World、Memory、Lore、Story、Prompt 和 Bridge Core Runtime 不等于宿主已提供私密 RP 所需的最终输出授权、原始历史隔离和晚到回复围栏。不要通过 prompt 约束来替代 Host 能力。

本指南供用户和本机 Agent 在真实 Hermes / OpenClaw 上建立**隔离测试**。先读 [START-HERE](../START-HERE.md) 和 [Host Integration 合同](architecture/SP-004H-HOST-INTEGRATION.md)。测试以当前实际安装版本和受控身份为准，不预设插件加载即代表功能已送达。

## SP-005H0：机械报告与原生插件探测

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

H0 实施时的历史基线为 `694b45a6f1cd10e28bef96a7e98261c1f85d66f6`。本层复用 durable registry、instance ID、generation 与现有 Profile/Agent 绑定，当时未新增数据库表，保持当时的 `DATA_SCHEMA = 7`、`SP-004F-bridge-runtime-v1` 和 `SP-004K-prompt-v1`。当前 Schema 8 见本文开头；此段不是当前版本声明。H0 不实现 H1/H2 或 Host final-output transaction。

永久 `life.py` 的工具结果新增 `runtime` 身份封套：instance ID、generation、install/data root、release、内部 agent ID、Host kind/home/agent ID 和三项版本常量。封套在实例锁内从 registry 与活动数据目录取得；正常 status 等字段继续保留。它证明所调用的 Life Engine 实例，不证明调用者是可信 Host，也不是远程认证令牌。

两个原生插件新增 `doctor`、`sandbox-probe`。在**独立测试 Host 的工具执行界面**调用实例自己的工具：

```json
{"action": "sandbox-probe"}
```

该 action 不接受 Profile、Agent、版本或 evidence 参数。身份来自 Hermes `get_hermes_home()` 或 OpenClaw 受信工具上下文的 `agentId`/`workspaceDir`，沿用现有拒绝路径。每次插件加载生成新 `plugin_epoch`；本次加载实际运行过 context hook 后才设置 `hook_runtime`。旧进程的 observed.json 时间戳不代替本次 hook 证据。探测依次调用 status、doctor、wake `--preview`、photo `--dry-run`，只保留结果码与身份，不输出记忆、prompt、照片工作流或聊天正文。任何单项失败单独记录。

`wake --preview` 不领取 contact、不发送，但既有 durable 入口可能建立当天备份，status/wake 可能初始化当天计划；这不是数据库字节不变的只读操作。photo dry-run 不访问 ComfyUI 或生成图片；照片关闭时返回 `DISABLED`。如需实际出图，另在独立环境执行正常 photo 并人工检查输出，不拿 dry-run 当成生成成功。

将工具返回的 JSON 对象完整保存为安装目录以外的 `probe.json`，在五分钟内生成报告：

```text
python -X utf8 <永久目录>/manage.py sandbox --instance <实例ID> --probe <证据目录>/probe.json
```

使用终端的 UTF-8 重定向保存输出为 `report-before.json`。如果没有安全隔离的 Host，省略 `--probe` 仍能验证本地实例，但报告会列出 `MISSING_ATTESTATION` 和 `PENDING_REAL_HOST_VALIDATION`。模拟运行显式使用 `--evidence-kind simulated`；默认是 `unverified_capture`，不存在能靠命令行开关签发真实 Host PASS 的选项。

仅在隔离测试 Host reload 后重新执行 hook 和工具，再比较：

```text
python -X utf8 <永久目录>/manage.py sandbox --instance <实例ID> --probe <证据目录>/probe-after.json --previous <证据目录>/report-before.json
```

`NEW_PLUGIN_EPOCH_OBSERVED` 只表示捕获文件中看到了新插件代次，**不证明**真实 Host 服务重启。generation、release 或目录变化返回 `REVALIDATION_REQUIRED`，需要重新核对变化原因、hook 和工具证据；不能沿用旧报告。`PASS_FRESH_PROCESSES` 表示管理器用两个新 Python 子进程分别执行了 status 与 doctor，并再次检查 durable 身份，不能外推为 Gateway restart PASS。

旧安装升级 Runtime 后，现有 `upgrade` 不自动重写插件。要在隔离实例按原参数重新执行安装以刷新受管理 bridge 文件，保留原实例设置，再按测试 Host 自身规则重载。不要为此修改生产配置或重启生产 Gateway；编辑过的受管理文件仍由原安装器拒绝覆盖。

### 报告字段与证据边界

| 字段 | 含义 |
| --- | --- |
| `ok` | 仅管理命令执行成功；生成 FAIL 报告也为 true，不代表验证通过 |
| `report_generated` | 完整报告已生成为 true；命令执行异常、未生成报告为 false |
| `validation_passed` | 当前所有路径固定为 false，模拟或捕获一致性通过不能改变它 |
| `plugin_file_exists` | 仅插件文件存在，不表示已加载 |
| `plugin_load_evidence` | 捕获文件存在时也只标 `UNVERIFIED_CAPTURE` |
| `host_probe_consistency` / `host_probe_errors` | 检查时效、四个工具的 runtime 封套、绑定、版本来源和本代次 hook 一致性；不认证捕获文件真实性 |
| `local_validation` / `local_probes` | 独立子进程调用和安装 doctor 结果，不是 Host PASS |
| `tool_probes` | status、doctor、wake 预览与 photo dry-run 的逐项结果 |
| `reload_comparison` / `life_engine_restart` | 分别记录插件代次比较和新 Python 进程探测 |
| `validation_result` | 本地失败或提供了不一致的捕获文件时为 FAIL；其余仍为 PENDING_REAL_HOST_VALIDATION，等待真实试验与独立审核 |

自动化只能根据 `validation_result` 判断真实验证状态：枚举为 `PASS`、`PENDING_REAL_HOST_VALIDATION`、`FAIL`，并要求 `validation_passed == true` 才能认定完成。当前实现没有产生 `PASS` 或 `validation_passed=true` 的路径。无 probe、模拟或 unverified_capture 一致性通过时，顶层为 `ok=true, report_generated=true, validation_result=PENDING_REAL_HOST_VALIDATION, validation_passed=false`。不一致的 probe 或 generation drift 生成 FAIL 报告时仍为 `ok=true, report_generated=true, validation_passed=false`。这两种已生成报告的情况退出码均为 0；命令执行异常则退出码为 1，返回 `ok=false, report_generated=false, validation_result=FAIL, validation_passed=false`。不得把退出码、ok、local_validation 或 host_probe_consistency 当作真实 Host Sandbox PASS。

Hermes 从实际加载的 `hermes_constants` 路径记录安装来源、Python executable、Profile、Git checkout/origin 和可获得的 distribution version。拿不到的字段为 `UNKNOWN`；非官方 origin 或来源不明不能通过官方 Hermes 一致性核验。origin 字符串并不证明 checkout 未修改，实机审核还须核对官方 checkout 与本地改动。compatibility fork 继续为 `STOPPED / NOT PRODUCTION-SAFE / FORK_ROUTE_TOO_DEEP`。

OpenClaw 从实际解析到的 SDK package 目录读取 package version，记录真实上下文的 agentId/workspace。它不是 `openclaw --version` 的替代：`cli_version`、config/profile、Gateway、Session/target 无可靠 API 证据时明确为 `UNKNOWN`，须在隔离环境另外运行 `openclaw --version` 并保存输出。现有绑定拒绝错误 agentId 或 workspace，但**不证明相同 agentId/workspace 被不同 Gateway/Profile 复用时的唯一性**。因此未取得独立 Gateway/Profile 证据前不得把结果称为真实 Host Sandbox PASS；本实现不虚构受信上下文字段。

### 交付证据

机械证据校验器 `sandbox.delivery_trace` 要求 `GENERATED → PREPARED → SENT → ACKNOWLEDGED`，同一 operation、明确本人 target，发送与 ACK 还须匹配 message ID。默认没有渠道验证器，最多认可 PREPARED；文件生成、media outbox、prepare 和模型提供的 evidence 均不能升级为 SENT/ACKNOWLEDGED。校验器只处理报告，不写业务 contacts，不发送消息。当前管理报告默认交付为 `NOT_EXECUTED`，回执能力为 `LIMITED`。

原生插件现拒绝 `ack outcome=delivered`，返回 `UNVERIFIED_RECEIPT`；模型不能替渠道登记送达。管理 CLI 原有 ack 是操作员记录入口，不是渠道验证器，其历史 delivered 文本不会被沙箱报告转换为 ACKNOWLEDGED。未来接通真实渠道验证器需另行审核；本轮没有实现它。受控真实发送只能使用用户明确指定的本人目标，并另存原始渠道回执供独立审核，不可猜测 last route 或全渠道 fallback。

### 实机记录仍须补齐

真实试验另附 Host 命令输出、独立 Profile/Agent/Session/目标、官方来源检查、错误身份拒绝、测试 Host restart/reload 前后证据、主动联系静默规则以及实际发送/回执。自动报告不接受一份手工 JSON 将这些项目自动升级为 PASS。无隔离环境时记录 `NOT_EXECUTED — production host isolation unavailable`；真实 Hermes 和 OpenClaw 都保持 `PENDING_REAL_HOST_VALIDATION`。没有 ComfyUI 时 photo 为 `DISABLED / NOT CONFIGURED`，不阻塞其它测试。

## 四级测试边界

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

| 级别 | 可做的验证 | 当前门禁 |
| --- | --- | --- |
| Level 0 — Core Runtime | 不接 Host；直接验证 World、Memory、Lore、Story、Bridge、PromptSnapshot、持久化与恢复 | 可进行；是 Runtime 证据，不是 Host 私密 RP 证据 |
| Level 1 — Host Sandbox | 在真实但隔离的 Host 上验证插件加载、身份/Profile/Agent 绑定、status、wake、photo、prompt/context projection 与重启 | 可开始；测试 Profile/Agent、Session、Life Engine 实例和本人目标必须明确 |
| Level 2 — Soul Continuity | 在本人 Soul Agent 的受控会话中验证普通连续生活状态、主动联系、照片、轻量日常记录 | 可受控测试；真实发送和实际回执分别记录，不开启 Full Private RP |
| Level 3 — Full Private RP | Soul / RP 原始 Host 历史结构隔离、最终模型输出 fail-closed 授权和晚到围栏 | **BLOCKED**；Hermes 与 OpenClaw 当前均未取得生产 Host 资格 |

Level 0 中可直接构造 Roleplay World 和 PromptSnapshot；这不把 Level 3 变成可用状态。

## 建立隔离测试环境

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

使用独立 Life Engine instance、独立测试 World、独立 Host Session，以及只由本人控制的测试聊天目标。不要导入真实敏感聊天历史；不要在生产会话试探跨 World 或 DROP 安全性质。不需要修改原 Soul、替换主模型或开放 Full RP。照片是可选项；没有合适 ComfyUI 工作流时保持关闭。宿主插件审查、权限及发送政策继续生效。

先记下 Life Engine 永久目录、实例 ID、`DATA_SCHEMA`、测试 World 和备份位置；通过生成的 `INSTALL.md` 与 `manage.py doctor/status` 核对实际加载，而不是猜目录。插件需要重载时只操作已隔离的测试 Host；任何生产 Gateway 的重启或配置更改应另立明确任务。

### Hermes：官方安装的测试记录

使用**官方 Hermes 安装**和独立测试 Profile / `HERMES_HOME`，不要安装或测试为生产用的 [compatibility fork PR #1](https://github.com/y19870785/hermes-agent/pull/1)。记录下列字段，再执行插件加载与工具调用：

| 字段 | 实测值 |
| --- | --- |
| Hermes version / checkout | 待填写 |
| Profile / `HERMES_HOME` | 待填写；确认与生产目录不同 |
| Agent / 插件加载结果 | 待填写 |
| 测试 conversation / 本人目标 | 待填写 |
| Life Engine instance ID / data root | 待填写 |

在测试 Profile 验证 status、wake 静默规则、本人身份匹配与错误 Profile 拒绝；若启用 photo，验证文件确属本实例并单独确认真实发送。官方 [PR #120170](https://github.com/NousResearch/hermes-agent/pull/120170) 尚不能作为已发布 Full Private RP capability 使用。

### OpenClaw：实际安装的测试记录

记录真实版本、`agentId`、`workspaceDir`、配置/Profile、Gateway 身份、测试 Session 和 Life Engine instance。`workspaceDir` 是绑定证据，不代替受信发送者身份。OpenClaw 2026.9.5 已做 CAP0 审计；2026.9.6 只做相关边界的只读比对。本机以后升级版本，必须重新做 capability probe 和插件重载验证；版本号改变不自动解除 Full RP blocker。

| 字段 | 实测值 |
| --- | --- |
| `openclaw --version` / package path | 待填写 |
| `agentId` / `workspaceDir` | 待填写 |
| Config/Profile / Gateway | 待填写；确认是否测试专用 |
| 测试 Session / 本人目标 | 待填写 |
| Life Engine instance ID / data root | 待填写 |

OpenClaw 有 `before_message_write`、`before_agent_finalize`、`message_sending` 等 Hook 和 `lifecycleRevision`，但不能把这几处拼接成一次 fail-closed final-output commit 决策；不要以 Hook 名称推断 Full Private RP 已安全。

## Level 0：Core Runtime 检查

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

- [ ] 创建 Soul World 和独立测试 RP World；同一 CharacterDefinition 在不同 World 中对应不同 CharacterInstance。
- [ ] 两个 World 的 Memory 默认隔离；有界查询只返回授权 scope/audience。
- [ ] Lore 仅在绑定的 World 和条件下激活。
- [ ] Story 的 accepted event 在重启后可恢复，未接受内容不会成为故事真源。
- [ ] 相同输入与版本生成确定性的 PromptSnapshot。
- [ ] Bridge 无 Grant 时拒绝；有 Grant 时只有授权字段进入有界 BridgeProjection。
- [ ] Grant revoke 后旧 projection / Snapshot 判 stale；F1 不向目标 Memory/Story 自动写入源内容。

这些检查可以通过独立测试数据和 Runtime API 完成，不宣称已通过 Host 私密历史隔离。

## Level 1–2：真实 Host 沙箱检查

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

- [ ] Life Engine `status` 和 `doctor` 正常，实际插件工具能访问**测试实例**。
- [ ] Host Profile/Agent 与实例绑定唯一；错误 Profile/Agent 被拒绝。
- [ ] 使用独立测试 Session 与本人聊天目标；未复制生产私密历史。
- [ ] 重启测试 Host 后，Life Engine 实例状态仍存在，插件重新加载且绑定不漂移。
- [ ] `wake` 在安静时段、无联系理由或限额用尽时保持静默。
- [ ] `photo` 只返回本实例生成文件；未开启照片时不产生媒体发送。
- [ ] 区分内容生成、Host 准备发送、平台实际发送与可验证送达；**无 ACK 不声称送达**。
- [ ] Host 升级或 reload 后重新验证插件加载、身份和实例绑定。
- [ ] Full Private RP 始终关闭；测试报告写明 Host 版本、目标与实际回执。

任一出现 Host 身份不稳定、错误 Profile/Agent 可读取实例、重启后状态丢失、错误 Session 取得历史、未授权 Bridge 字段出现，或生产 conversation 被测试污染，**立即停止测试并保留证据**。

## 本阶段不进行的验证与不得宣称的结果

> HISTORICAL：本节保留当时状态与证据；当前状态以顶部 CURRENT CANONICAL STATE 为准。

暂不在真实 Host 中执行 Soul secret → RP 原始历史、RP secret → Soul 原始历史、RP 切换后晚到模型回复、Full RP delivery fence 或 Host final-output transaction 试验。当前不能宣称：Full Private RP production-safe、Soul/RP raw Host history 已机械隔离、stale model output 不可能出现、Bridge 上下文总能受 Host final commit 保护，或模型输出 DROP 已同时覆盖持久化、下一轮重放、最终交付和流式输出。

Hermes compatibility fork 曾在隔离真实执行链中暴露 recovery durability 和 session incarnation/A→B→A writer 问题，路线已停止；它是审计证据，不是生产安装建议。OpenClaw CAP0/CAP1 也未使 H2 Adapter 解锁。下阶段 [SP-005H0 Host Integration Sandbox](planning/ROADMAP-2026-09.md) 应只验证 Soul Continuity 的真实宿主接线与回执。
