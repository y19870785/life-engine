# SP-005A2 — CURRENT_HOST_BINDING_AUDIT

审计基线：`84493be98d7ed675de6b859cafdb014a900325ca`。本文只描述该提交的源码及仓库内契约测试，不断言当前上游最新版本或本机真实 Host 已通过验证。没有启动 Host、访问生产配置或发送消息。

版本：DATA_SCHEMA = 8；Schema Signature = SP-005A-living-runtime-v1；Prompt Template = SP-004K-prompt-v1。

## 现有执行路径

| 路径及源码锚点 | 当前行为 | A2 判断 |
| --- | --- | --- |
| [durable.run / context_text](../../runtime/life_engine/durable.py) | permanent entrypoint 读取 registry、锁定 instance、验证数据并附 runtime identity；context 调用 legacy Engine.status，owner_seen 先写 Store.observe；wake 还可能创建每日备份，再进入 CLI | 不能直接路由 enrolled Living；context 并非只读，失败前可能已写 legacy observation，wake 失败前可能已备份 |
| [Engine.status / wake](../../runtime/life_engine/engine.py) | status 会创建日计划；wake 决定并领取 legacy contact；两者在事务内检查 living_writer | enrollment 后返回 LIVING_HANDOFF_REQUIRED，不能用 preview 绕过 |
| [Store.prepare / acknowledge / observe / loops](../../runtime/life_engine/store.py) | prepare 为 claimed→prepared；ack 记录 delivered/failed/unknown 文本；prepare、loop 写入有 single-writer gate；observe、ack 并非完整 Living facade | legacy ack 不等于受信 receipt；legacy observe 不更新 living_inbound；A3 必须在 Host 分发前整体选路，不能仅依赖几个 Core gate |
| [Hermes bridge](../../runtime/life_engine/bridges.py) 的 _scoped/_handle/_before | get_hermes_home 与 registry host_home 比较；tool 调 permanent CLI；pre_llm_call 调 context；sender/platform 匹配且非 parent_session 时传 owner_seen，turn_id 用作 event key | Profile 绑定可复用；不等于 principal/World Session 授权。现有工具可见参数不能用来生成 LivingContext |
| 同文件 OpenClaw scoped/registerTool/before_prompt_build | 每次比较 agentId 与真实 workspace 路径；hook 可检查 toolAuthority 和 hookInvocation.assertActive；external_user + sender/channel 匹配后记录 owner_seen | 有 Agent/workspace 契约；同一 pair 在另一 Gateway/profile 的复用尚无唯一性证明；可选 hook 检查不是完整 late-result fence |
| [integration.schedule_recipe](../../runtime/life_engine/integration.py) / bridges.installation_guide | 生成周期 wake 的操作说明；安装器不创建业务计划或自动创建 cron；Host 负责调度、最终回复路由 | 旧 wake recipe 不适用于 enrolled instance；不能继续让模型根据 action=contact 自行发送 |
| [sandbox.identity / report / delivery_trace](../../runtime/life_engine/sandbox.py) | instance/generation/release/data root 封套；fresh-process status/doctor；捕获一致性和 epoch 比较；交付链报告验证 | 可复用身份字段、doctor 和证据格式思路，但不是 binding credential；报告固定 validation_passed=false，不能授予 capability |
| bridges 的 sandbox-probe | 运行 status、doctor、wake preview、photo dry-run；本次 hook 后记录 hook_runtime；模块加载生成 plugin_epoch | enrolled status/wake 会遭 handoff gate，旧 probe 不是 Living 验收器；epoch UUID 仅证据，无旧 token 撤销机制 |
| [LivingRuntime](../../runtime/life_engine/living_runtime.py) | enroll/configure/tick/prepare_intent/begin_attempt/record_delivery/observe_inbound 等受信 Python API | 无 Host facade、无真实 transport；不可把内部 API 原样暴露为模型 tool |
| [LivingRepository](../../runtime/life_engine/living_repository.py) | management lock→instance lock→同一 SQLite 事务；校验 generation、World runtime_id、Scope 与数据完整性 | 可复用完整原子性；不能在外层重复持同一非重入锁后调用 Core；网络不得进入锁内 |
| [LivingContextSnapshot](../../runtime/life_engine/living_projection.py) | SOUL_RESPONSE、Soul viewer、Session/WriterEpoch、world/living/policy revision、runtime_id/generation；最多 8192 bytes；进程 HMAC seal，valid_until | 独立 Core projection，可 query/revalidate；没有进入 PromptSnapshot，不能跨进程复用 seal |
| [PromptRuntime._sections / assemble / revalidate](../../runtime/life_engine/prompt_runtime.py) | 固定版本 section、预算、投影重验；没有 Living section | 正式 Living 拼装需要单独模板升级，不能塞进 Memory/Story/Lore 或 legacy context 字符串冒充已支持 |

## Core 接口可复用与缺口

`LivingTickContext` 是窄调度权限：instance/Scope/generation/policy revision；无 chat session，不能 Owner 命令或发送。`LivingContext` 由受信调用方构造，带 principal/Scope/generation/producer，可带 session。Core 类型检查并不证明调用方已经认证真实 Owner；该责任属于未来 binding layer。

tick 的当前结果已有 SILENT、RECOVERY_IN_PROGRESS、RECONCILIATION_REQUIRED、RESERVED；异常另抛。它会写 Day、恢复状态和 reservation，不是只读预览。prepare_intent 当前把 DECIDED 改为 PREPARED，material 使用有界 text（默认 512 UTF-8 bytes），不发消息。begin_attempt 首次持久 CLAIMED 并返回 execute=true；相同 operation 重放或已有 Attempt 均返回 execute=false。取消不退款，R1 自我 quota/cooldown 规则已实现。A3 复用这些公开方法，不复制业务算法。

record_delivery 默认无 validator，返回 RECEIPT_UNVERIFIED。validator 在锁外执行，Core 在事务内验证 Attempt/target/message/sent_at、source/event 去重；冲突进入协调门禁。SENT 后才接受 ACKNOWLEDGED。测试 fake 不提供真实渠道证明。status 的 Core 返回包含历史集合，未来 Host status 需要有界、脱敏投影，不应原样交给模型。

World SQLite repository 默认构造会创建新的 runtime incarnation 并恢复旧会话；同 incarnation 的工作连接必须显式传 runtime_id。不能每个 Host tool subprocess 都默认创建新 World runtime。Living snapshot 的 seal 又是每个 LivingRuntime 对象独有：插件 epoch、Core incarnation、generation 是三个不同生命周期。

## 当前能力证据及禁止外推

契约测试见 [test_durable.py](../../tests/test_durable.py)、[test_sandbox.py](../../tests/test_sandbox.py)、[test_living_runtime.py](../../tests/test_living_runtime.py)、[test_prompt_runtime.py](../../tests/test_prompt_runtime.py)。它们证明本仓库合同和模拟宿主，不证明真实插件已加载、Gateway 身份、Session continuity 或发送回执。

Hermes 已知接入点为仓库生成的 register_tool/pre_llm_call/Profile API；OpenClaw 为 registerTool/before_prompt_build/agentId/workspace API。官方 Host 的准确版本、能力可用性与 receipt 都必须在未来隔离环境重新 attestation；未知项记 UNKNOWN 并拒绝需要该项的能力。A2 不做上游 capability 更新裁定。

现有源码没有可信 Living principal/session 映射注册表、受信调用 token、binding revision、统一发送执行器、真实 receipt validator。H0 中的完整历史隔离、final-output authorization、late-response fencing 与 RP lane 不在 A2 补齐范围。Hermes compatibility fork 保持 STOPPED / NOT PRODUCTION-SAFE / FORK_ROUTE_TOO_DEEP，官方 upstream 只作 watcher，H1/H2 不自动解锁。

Hermes real Host validation = PENDING_REAL_HOST_VALIDATION；OpenClaw real Host validation = PENDING_REAL_HOST_VALIDATION；Full Private RP / H1 / H2 = BLOCKED。后续合同见 [A2 架构](SP-005A2-LIVING-HOST-BINDING.md)。
