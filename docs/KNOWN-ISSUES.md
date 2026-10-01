# v0.3 已知问题与历史记录

本版本用于开发审阅和受控试用。2026-10-01 核对基线为 `f83d36c76fea6de1a31b449535d5df6cea3909b5`；B1 Core 已 DONE，A3 Host 层未完成。历史 Hermes 受控测试与完整真实 Host 验收分开，见 [2026-09-30 脱敏记录](validation/HERMES-COMPREHENSIVE-EVALUATION-2026-09-30.md)。下面 OPEN / BLOCKED / KNOWN LIMITATION / RESOLVED / HISTORICAL 是问题分类，不把阻止功能写成该功能 PASS。


## OPEN — 历史 finding 在 B1 后的代码复核

| 问题 | 等级 / 当前证据 | 后续边界 |
| --- | --- | --- |
| 错误 instance 返回 KeyError | LOW；`durable.run` 直接索引 registry，捕获后输出异常类名，仍未统一为 UNKNOWN_INSTANCE；doctor 的未知实例处理不同。 | B1 未修改该入口；另立修复任务。 |
| 空/错误数据目录的 state_check 返回 FileNotFoundError | LOW；配置 load 仍先读取 agent.json，未统一为 StateSchemaError。 | 与下方已修复的“活动 DB 缺失后静默初始化”是不同问题。 |
| 相同 host_home 的实例 ID 可能相同 | `durable.instance_id(adapter, host)` 仅由 adapter + 规范化 Host 路径摘要产生，不含 permanent root。不同 root / generation 可隔离数据，但 instance_id 不是跨安装全局唯一。 | 记录证据须同时绑定 install/data root、generation、Host profile；operator、plugin/tool naming 与 evidence ambiguity 仍需后续设计评估。 |

以上仅对当前源码作只读核对，没有运行真实 Host 或修改错误处理。

## BLOCKED — A3 完整 legacy routing fence

B1 仅新增 Core recovery API，没有修复 Host 分发层的副作用前 gate。当前代码边界如下：

| legacy 路径 | enrolled 实例上的当前行为 |
| --- | --- |
| status / wake | Engine 在计划/联系业务前调用 legacy_writer，返回 LIVING_HANDOFF_REQUIRED；但 durable wake 的每日备份可能先于该检查。 |
| context | 最终 Engine.status 会拒绝；owner_seen 时 Store.observe 可以先写入，不能宣称整体零副作用。 |
| prepare / loop-add / loop-close | Store 在业务写入前检查 legacy_writer。 |
| observe / pause / resume | Store 对应方法没有统一 enrollment 前置 gate。 |
| ack | 原生工具拒绝 delivered 的未验证回执；管理 CLI / Store acknowledgment 没有统一 enrollment gate。这不是 ACK validator。 |
| photo | 未提供 contact_id 时依赖 Engine.status 的 gate；指定旧 contact_id 可走另一分支，缺少统一的副作用前 fence。 |

不得通过这些缺口绕过 Living handoff，也不得移除 LIVING_HANDOFF_REQUIRED；enrolled 实例不进入旧 Host 业务测试。正式修复属于后续 A3，GOV-DOC3 只记录现状。Schema 8 且未 enrollment 仍可使用 legacy，不能按表存在自动切换 Living。

## KNOWN LIMITATION — 历史 ACK / fresh-process probe

- 无受信 ACK validator：MEDIUM — KNOWN BOUNDARY；一次真实发送保持 SENT / ACK UNKNOWN，message ID、API 回读、rc=0、模型文本和人工 ack 都不是 ACKNOWLEDGED。
- fresh-process probe 缺 live hook 时仍 HOOK_REVALIDATION_REQUIRED，这是 H0 设计边界；B1 查询不会补齐它。
- 独立真实 Gateway restart、当前 generation/revision/ticket 重验仍属 PENDING_REAL_HOST_VALIDATION；H0 plugin_epoch 已存在，但 A3 authority epoch / capability 尚未实现。

## KNOWN LIMITATION — Core 与 Host 边界

A1 已 DONE，提供 Schema 8、显式 enrollment、持久计划/联系状态和独立 projection；B0 / B1 也已 DONE。详见 [Living 操作与迁移](LIVING-RUNTIME.md)。现有 Prompt Template 未接入 Living，原生 Host 工具未切换新 Core；enrolled 实例的 legacy wake/status、prepare、loop 写入受 single-writer gate 拒绝。不要在生产实例 enrollment 后期待旧 Host callback 自动兼容。

生产具名时区必须有真实 IANA tzdata，规则指纹变化要求显式 policy/epoch 更新。UTC 可独立使用；测试的固定 TZif 只验证 2026 DST，不是生产时区库。Core 没有联网天气 provider、真实 transport、渠道 receipt validator、ComfyUI job 或 TTS。UNKNOWN 只协调，不自动重发；rollback/restore 不会证明备份之后没有发生外部发送。


## KNOWN LIMITATION — H0 报告、ACK 与 live probe

新增原生插件诊断与文件化报告只验证本地调用、捕获证据一致性及 reload 代次。历史 Hermes 测试已验证限定 Profile 的 Owner/target 并完成一次真实发送；整体 Hermes/OpenClaw real Host validation 仍为 `PENDING_REAL_HOST_VALIDATION`，不能由单次发送或 Core CI 升级。OpenClaw 现有 agentId/workspace 绑定不能单独证明跨 Gateway/Profile 唯一性；缺少这些实机证据时不签发真实 Sandbox PASS。Host 版本、Session、Gateway 等无法取得的字段必须保留 UNKNOWN。

当前没有受信渠道回执验证器，Hermes/OpenClaw 原生工具拒绝模型发起的 `ack outcome=delivered`。旧管理 CLI 的人工 ack 仍存在，但不属于机械渠道证明，报告不会把其文本转换为 ACKNOWLEDGED。照片 dry-run、文件生成与 media preparation 均不等于已发送。操作步骤与报告字段见[沙箱指南](HOST-SANDBOX-TESTING.md#sp-005h0机械报告与原生插件探测)。Full Private RP、H1/H2 继续 BLOCKED。

当前 canonical main 的 GitHub Actions 在 Ubuntu / Windows、Python 3.11 / 3.12 四矩阵通过。下述 2026-09-13 Windows 结果和缺库复现是历史记录，不代表当前测试状态。

## RESOLVED — 缺失数据库静默初始化

2026-09-13 在 Windows / Python 3.12 临时安装中复现：写入记忆后移走
`life.db`，`doctor` 仍返回 `ok: true`，`status` 返回成功并创建空数据库。
`durable.state_check` 仅检查存在的数据库，后续 `Store` 自动初始化。
已有实例应在缺库时停止并要求恢复，首次安装才允许建库。

SP-004E 已修复此问题：当前 main 的 `state_check` 拒绝缺失活动数据库，健康检查返回失败；
首次安装仍可显式创建完整数据库。相关测试见
[SP-004E 质量门禁](planning/SP-004E-QUALITY-GATES.md)。

## OPEN — 出图期间实例锁阻塞其他调用

代码检查发现 `durable.run` 在整个 photo 命令期间持有实例锁，包括网络等待；
其他命令取得锁的等待上限为 5 秒。长耗时出图可能使上下文注入和入站记录失败。
此并发场景尚未实际复现，应在调整锁范围时同时保护恢复和数据代次切换。

## HISTORICAL — 2026-09-13 Windows 测试结果

2026-09-13 执行 `py -3.12 -m unittest discover -s tests -q`：
50 项测试，5 项错误，1 项跳过。

五项错误均发生于 tearDown 清理临时目录，报 SQLite 文件被占用（WinError 32）。
相关测试的 SQLite 连接需显式关闭；不能据此认定备份、恢复和迁移的业务断言失败。
OpenClaw 契约测试因测试进程 PATH 未发现 Node 而跳过。
历史 Linux 检查记录见 VALIDATION.md，与本轮 Windows 结果分别保留。

SP-004E 已将上述 SQLite 测试改为显式 `contextlib.closing` 释放连接，
保留事务上下文负责 commit/rollback；没有使用 sleep、GC、错误吞掉或新增跳过。
测试复制发布源码时排除 `.git`，避免 Windows 只读 Git 对象触发无关清理错误。
当前 canonical main 的四矩阵结果见 [验证记录](VALIDATION.md)；本节保留当时的故障证据。

## HISTORICAL — Host 审计与实测范围

已对 Hermes / OpenClaw 的 Host 源码和能力做深入审计，并对 Hermes compatibility build 做过隔离的真实 execution-chain 验证；该 fork 验证发现失败，不能外推为 canonical Life Engine 的真实 Host 集成验收。2026-09-30 canonical Hermes 的受控文字发送已取得历史证据，但新的 Living gateway/binding 验证、完整 GPU 出图及可信发送回执闭环尚未完成；World Memory 也尚未自动接入真实宿主对话。
上传代码不代表已安装到本机 Agent，也不代表可宣称稳定发布。

## BLOCKED — Full Private RP / H1 / H2

Hermes 官方 Host 尚缺满足 H0 合同的完整 final-output commit 授权与 session incarnation 围栏。历史审计所引用的上游 [PR #120170](https://github.com/NousResearch/hermes-agent/pull/120170) 曾将 final commit 能力纳入讨论范围；本轮不重审上游最新发布状态，讨论不能当作通过目标版本门禁的证据。实验性的 [compatibility fork PR #1](https://github.com/y19870785/hermes-agent/pull/1) 保持 Draft、未合并；隔离执行链验证曾发现 recovery 先持久化旧候选，以及 A→B→A session incarnation 后旧 writer 可恢复写入，因此 fork 路线已停止，不能生产使用。

OpenClaw 已有 `lifecycleRevision`、writer fence 与多个有用 Hook，但 2026.9.5 的 CAP0/CAP1 审计及 2026.9.6 只读比对未找到插件可用的统一 fail-closed final-output commit boundary。单次授权尚不能机械覆盖首次 assistant 持久化、下一轮重放、最终交付和授权前的模型流式输出。参见 [Host 沙箱测试指南](HOST-SANDBOX-TESTING.md)。

这只阻止 **Full Private RP 的生产 Host 接入**，不否定已完成的 World/Memory/Lore/Story/Bridge/Prompt Core Runtime，也不阻止隔离的 Soul Continuity 沙箱测试。
