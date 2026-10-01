# Hermes canonical 综合评测 — 2026-09-30 历史摘要

本文保留 B1 完成前的历史验收事实；当前工程状态以 [B1 后验证记录](../VALIDATION.md)为准。历史评测不是 A3 Living Host Binding、正式 Prompt 接入或生产验收。

## 来源与核验范围

Owner 提供 `LIFE-ENGINE-HERMES-COMPREHENSIVE-EVALUATION.md`、`evaluation-summary.json` 和 `SHA256SUMS`。GOV-DOC3 已读取两份报告，逐字节计算 SHA-256 并与清单对应项核对一致；JSON 的 59 个 rows 与汇总数量一致。

| 材料 | SHA-256 |
| --- | --- |
| LIFE-ENGINE-HERMES-COMPREHENSIVE-EVALUATION.md | `18d77ca4ab131cffb94a9d268f2c71f94b0f23c9186e97b72dc057b667ee1328` |
| evaluation-summary.json | `aba5dcc1b2c99cbc73d7dc6e3a088b304b609098a8a4f4879729128da9a1b071` |

清单还引用环境、数据库、探针、发送及隔离等原始证据文件，这些文件未随本次三份材料提供，未在 GOV-DOC3 中逐项重新读取或复跑。校验和一致证明收到的报告与清单对应，不代替独立验证每条原始 Host 证据。本文仅提交脱敏摘要，不复制原报告中的 sender/channel/message ID、私有路径、实例/代次标识、生产进程信息或原始日志；未提交 token、密钥、配置或聊天正文。报告中的修复建议不构成本轮 Runtime 修改授权。

## 历史环境与隔离

| 项目 | 历史记录 |
| --- | --- |
| 时间 | 2026-09-30 20:47–20:58，UTC+8 |
| canonical clean source | `861734b0c4179e56a3251a775d831cd246278d7f`；报告记录源码工作树 clean |
| release | `0.3.0-eefb56b42b6eb8f4`；报告记录发行 runtime 与源码一致 |
| 版本 | DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1 |
| Host | 官方 Hermes 0.21.3；独立 HERMES_HOME / 测试 Profile |
| 数据与目标 | 独立 canonical permanent root、显式 Owner/Discord 专用测试渠道；durability 变更另在独立 scratch root 执行 |
| 生产隔离 | 报告记录未修改生产配置、既有 cron 或生产 Gateway，未触碰旧 permanent root；测试环境未建立长期 cron |

以上是报告记录的历史隔离证据；GOV-DOC3 不访问生产环境、不运行 Host 探针、不发送消息，不将旧绑定直接沿用为当前授权。

## 历史统计（保持原值）

| 分类 | 数量 |
| --- | ---: |
| tests_total | 59 |
| PASS | 42 |
| PASS_WITH_LIMITATION | 8 |
| PENDING | 1 |
| BLOCKED | 1 |
| NOT_EXECUTED | 7 |
| FAIL | 0 |
| critical_findings | 0 |

PENDING 是原汇总字段；对应 row 为 host.real_host_binding_validation，状态 PENDING_REAL_HOST_VALIDATION。七个 NOT_EXECUTED 分别为 World、Lore、Story、Bridge、grant revoke、真实 Gateway restart、旧 generation/stale identity 的 Host 验证。汇总 FAIL = 0 不掩盖单独 probe 的 host_probe_consistency=FAIL / HOOK_REVALIDATION_REQUIRED；该 probe 在历史评测中归为 PASS_WITH_LIMITATION，不能转成真实 Host PASS。

历史总体结论：**CURRENT IMPLEMENTED SCOPE ACCEPTABLE FOR CONTROLLED LOCAL TESTING**。这限定于当时已实现和实际执行的范围，不是 B1 后新状态，也不是生产放行。

## 已取得的历史证据与不能外推的结论

| 范围 | 报告支持的事实 | 验收边界 |
| --- | --- | --- |
| 插件与绑定 | scoped register、legacy context/status 的 runtime 与 registry 一致；错误 Profile / HERMES_HOME 拒绝 | 不是 A3 Binding Authority / capability 验证 |
| Owner | 正确 owner + platform 时 owner_recorded=true；错误 sender 或正确 sender + 错误 platform 时 false | 不从 last-route、默认目标、模型文本或猜测取得身份 |
| Soul Continuity context | legacy context 生成、归一化后两次输出一致 | 原报告的 PromptSnapshot 标签不能据此证明正式 PromptSnapshot 或 Living P1 注入；Memory 记录用例同样不能外推全部 World Memory Host 行为 |
| 持久性 | 跨进程读取；scratch backup / verify / restore / reconfigure 改变 generation；restore 后 paused | 旧代保留，未知外部发送仍需协调；同版本 rollback 是 no-op，不证明任意版本回退 |
| Photo | disabled 配置下 photo --dry-run 返回 DISABLED | 未调用 ComfyUI、无真实出图或媒体发送 |
| World / Lore / Story / Bridge grant / revoke | schema/doctor/db_check 及已有 Core 测试证据 | 真实 Host mutation 为 NOT_EXECUTED — NO SAFE TEST PATH，不能写实机 PASS |

### 发送：上一轮 1 条，综合评测本轮 0 条

综合报告引用**上一轮**一次受控 Soul Continuity 真实 Discord 文字发送：Hermes 实际 send、原生 message ID、明确渠道匹配、external send count = 1，无自动重试或第二条。该 ID 仅用于本地阅读核对，不在仓库发布。综合评测本轮 `real_send_count = 0`，未消耗新的发送配额；GOV-DOC3 同样没有发送。

历史描述继续保持 **SENT / ACK UNKNOWN**。没有受信渠道 ACK validator；CLI rc=0、message ID、Discord API 回读、模型输出或人工布尔值不能升级为 ACKNOWLEDGED。报告还记录无 validator 时机械 receipt 路径返回 UNVERIFIED_RECEIPT、停在 PREPARED；外部发送事实与 Core/机械 receipt 状态不能混为一谈。

### Organic Contact：真实静默 gate，不是 eligible 发送闭环

实际 wake --preview 返回 silent，reason=recent_conversation，结果 **ORGANIC_CONTACT_NOT_DUE**，external send count = 0。未修改时间、quota、cooldown、recent conversation 或伪造 follow-up 来制造可发送条件。

这证明当次静默 gate 阻止了不合时机的联系。未证明自然 eligible → organic contact → real send；当次没有历史 contact 触发 cooldown，没有实际 follow-up。quiet hours / daily cap 的配置与当前值检查也不等于已实测所有边界转换。

### Host 生命周期与 Private RP

两次独立 Python 进程产生不同 H0 plugin_epoch，runtime/generation/release 一致；不能把它等同于真实 Gateway restart 或 A3 token 撤销。fresh-process probe 缺 live hook，报告保持 HOOK_REVALIDATION_REQUIRED、validation_passed=false；真实 Gateway restart 与正式 reload comparison 未执行。Hermes real Host validation 继续 PENDING_REAL_HOST_VALIDATION。

Full Private RP、H1/H2 均 **BLOCKED**。原报告将 blocker enforcement 与功能结果混写的标签不沿用；只记录 **blocker enforcement verified**，不将阻止功能视为功能通过。历史 A3 也为 BLOCKED，当前原因另见下节。

## Findings 与 B1 后复核

| Finding | 历史等级 | B1 后代码复核 |
| --- | --- | --- |
| 未知 instance 输出 KeyError，未统一 UNKNOWN_INSTANCE | LOW | 仍存在于 durable.run 的 registry 索引路径 |
| 缺少受信 ACK validator | MEDIUM — KNOWN BOUNDARY | 仍存在；B1 的 operation receipt 不是渠道 receipt |
| 空/错误目录 state_check 抛 FileNotFoundError | LOW | 配置读取路径仍存在；与已修复的缺 DB 静默初始化不同 |
| 无 live hook 的 fresh-process probe 返回 HOOK_REVALIDATION_REQUIRED | MEDIUM — BY DESIGN | H0 设计边界未被 B1 改变 |

GOV-DOC3 任务书另记录的 same host_home / different permanent root 实例 ID 歧义，经当前 `durable.instance_id` 源码确认：ID 不包含 permanent root。此项不是原 JSON 的第五条 finding，不改动历史四条 finding 或 critical_findings 计数。详见 [已知问题](../KNOWN-ISSUES.md)。

## B1 后当前事实与下一步

当前基线 `f83d36c76fea6de1a31b449535d5df6cea3909b5` 的 B1 Architecture / Implementation = DONE，新增 trusted read-only operation recovery；授权先于 receipt lookup，不返回 execute，不签 permit，不重试/发送。具体合并与四矩阵 CI 见 [B1 验证映射](../SP-005A3-B1-VALIDATION.md)。

完整 A3 Host Binding 仍 BLOCKED，待剩余实现的新授权。H0 的旧 binding / plugin_epoch 和 B1 Core 的 principal / Scope / generation / Session / WorldRevision 授权，均不能替代尚未实现的 A3 authority、ticket、capability 与 execution permit。历史实测不使 Living R01–R12 升级，仍 NOT_EXECUTED；Hermes / OpenClaw real Host validation 均 PENDING_REAL_HOST_VALIDATION。

后续依赖、长期沙箱前置条件及独立 Full Private RP gate 见[路线](../planning/ROADMAP-2026-09.md)。本摘要不授权真实 cron、自动发送、ACK validator、A3、P1、Media、Voice 或新的 Memory 功能。
