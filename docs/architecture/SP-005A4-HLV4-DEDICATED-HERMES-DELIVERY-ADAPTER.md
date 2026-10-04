# SP-005A4-HLV4-A0 — Hermes 专用 Living Delivery Adapter 边界合同

## CURRENT — HLV4-A2-R0 Provider Transport 精化（2026-10-05）

A0 / A1 = DONE；A2 在真实 Host 操作前因 `REAL_TRANSPORT_IMPLEMENTATION_REQUIRED` 停止。A0 下文的 `channel.send(content=exact_payload)` 是当时待 HLV4-A 锁定的 SDK 调用占位；[A2-R0 source audit 与架构候选](SP-005A4-HLV4-DEDICATED-DISCORD-PROVIDER-TRANSPORT.md)发现 discord.py 2.7.1 在 `HTTPClient.request()` 内自动重试，因此该占位不能直接成为 one-permit/one-attempt 边界。A0 的 exact target、final guard、consume、无重试和 generic fail-closed 原则不变。A2-R0 仅文档，A2-R1 / A2 retry / HLV4-B 均未授权；`REAL_SEND = NO`。以下 A1 CURRENT 为历史阶段快照。

## CURRENT — HLV4-A1 本地实施（2026-10-04）

A0 = DONE（canonical main `337f5f95d47929c0a63c86cf9e2f70a14b9f6ddb`）；A1 = IMPLEMENTED / DRAFT_REVIEW_PENDING，见 [A1 本地验证报告](../validation/SP-005A4-HLV4-A1-DEDICATED-ADAPTER.md)。独立 `life_engine_discord` 插件源码与 R1 consumer 的固定 Host-neutral port 已实现；标准 generic `send()` 和其他发送面 fail closed，默认 factory 不提供 transport。本地 inert 测试不是 Host 加载或真实边界证据。A2 = NOT AUTHORIZED；HLV4-B = NOT AUTHORIZED；REAL_SEND = NO；REAL_HOST_SENT / ACKNOWLEDGED = NOT ACQUIRED。下文为 A0 原始架构冻结记录。

## HISTORICAL — A0 状态与证据边界

本合同以 canonical main `0b733908ffdef059a43428af42f3b3cb83a9850e` 为 Base，冻结待独立审核的 HLV4-A 修复路径；A0 仅修改文档，没有安装插件、启动 Gateway、执行 Living 或发送消息。R0 / R1 = DONE；HLV4-A built-in Discord path = REJECTED；dedicated plugin route = ARCHITECTURE_FREEZE_PENDING；HLV4-B = NOT AUTHORIZED；REAL_SEND = NO。本文描述后续实现必须满足的条件，不构成实现或运行验证证据。

Hermes 0.21.3、源码 `01382698fc32ec7740b6a204d9b7a6abeac74d33` 的 built-in `DiscordAdapter.send()` 具有 `metadata.thread_id` 目标覆盖、forum auto-create、message splitting、reply-reference fallback、多处 `channel.send()`、retryable delivery 和 generic ledger 交互。因此 `BUILTIN_DISCORD_ADAPTER_FOR_REAL_CONTACT = FORBIDDEN`。不得 monkeypatch、subclass/wrap/replace 该方法，也不得以配置关闭部分行为来声明安全。坚持 built-in 路径需要 Host patch：`HOST_PATCH_REQUIRED_FOR_BUILTIN_PATH = YES`。

源码中的 `PluginContext.register_platform()`、`PlatformEntry.adapter_factory`、`platform_registry` 以及 Gateway 的 plugin adapter 构造路径提供独立平台扩展点；注册按 `HERMES_HOME` scope 管理，Gateway 在 profile runtime scope 中创建 named-profile adapter，已注册平台构造失败不会退回 built-in。由此可冻结不修改 Hermes upstream 的候选路径：`HOST_PATCH_REQUIRED_FOR_DEDICATED_PLUGIN_ROUTE = NO`，但它的隔离、实例独占和实际执行安全仍须在 HLV4-A 验证；若任一条件无法成立，按下文 STOP。项目级 `HOST_PATCH_REQUIRED_FOR_HLV4 = NO` 是该条件性架构结论，不是插件已运行的证明。

## 平台身份、安装与生命周期

专用平台名固定为 `life_engine_discord`。插件只向官方 registry 注册此名称，使用独立 `BasePlatformAdapter` 实现，不重新注册 `discord`、不继承或复用 built-in `DiscordAdapter.send()`。注册前必须检查名称归属；若有同名他方注册或 scope 歧义，拒绝启动，不利用 registry 的覆盖语义。插件只可安装在隔离 HLV Test `HERMES_HOME` 的 `plugins/life-engine-discord/`，不得进入 default/production Home、system-wide 环境或 Hermes 源码树。

可信 binding 必须从 Gateway process、profile、plugin registration、adapter instance、credential identity、受保护 target registry 和 Life Engine Core generation 投影当前身份。Gateway restart、plugin reload、adapter recreation、target/credential identity 变化或 Core generation 变化均撤销旧 authority、grant、permit。持久 session、route 或 target 元数据不能恢复执行权。未来实现须确认 isolated profile 中只有一个实际持有相应 bot credential 的 adapter 实例；若 duplicate-credential/listener claim 或 profile scope 不能安全成立，HLV4-A 停止，不能在 default Gateway 寻找替代路径。

## Generic 路由硬拒绝

标准 `LifeEngineDiscordAdapter.send(chat_id, content, reply_to, metadata)` 必须对任何参数固定 fail closed，返回明确 `REAL_CONTACT_AUTHORITY_REQUIRED` 或等价拒绝，且调用 provider transport 次数为零。所有从 `BasePlatformAdapter` 继承而可能产生 provider side effect 的额外方法，也必须经审计并拒绝 generic 调用。不得注册 `send_message_handler`、`standalone_sender_fn`、`cron_deliver_env_var`、model-callable send tool、slash-command send、webhook sender 或 fallback sender。不得让 `hermes send`、cron、webhook、default/last route 或 generic delivery ledger 重放获得专用入口。

唯一执行入口是 adapter 内部的 trusted `deliver_authorized_real_contact(...)`（具体符号由实施阶段确定）。它只能由 Life Engine trusted Host Binding 与 `RealDeliveryConsumer` 调用；不能暴露给 model、generic Hermes send、cron、webhook 或公共 fallback。插件 factory 与 registry 只提供实例/lifecycle，不授予 REAL_CONTACT 权限。普通插件对象引用亦不构成 execution capability。

## Authority 与最终不可逆边界

唯一合法顺序：Core `begin_attempt` → durable `CLAIMED` → transaction ends → `execute=true` → `OneShotRealDeliveryGrant` → `RealDeliveryPolicy.ALLOW` → `REAL_CONTACT` `ExecutionPermit` → `RealDeliveryConsumer` → 当前 Host lifecycle projection → final delivery guard → atomic permit consume → 专用 adapter 的唯一 provider call。R0/R1 [Real Delivery Authority 合同](SP-005A4-HLV4-REAL-DELIVERY-AUTHORITY.md)继续管理 Core、grant、permit 与 consumer；Hermes 仅提供受信 Host projection 和 transport，不成为业务 authority。`SIMULATED_CONTACT` permit 永远不能调用此入口；recovery 永不签发 permit。

进入 final guard 前，`TrustedDeliveryTarget` 必须精确冻结 provider/platform、bot/application identity、server/guild、channel、owner、profile、Agent 与 binding identity；所有字段来自受保护 Host 配置/registry，不来自 model、prompt、display name、last/default route、`reply_to`、`metadata.thread_id`。缺失、歧义、变化均拒绝。单条固定 text payload 以 canonical digest 贯穿 grant、permit、guard、call；禁止 attachment/image/audio/embed/mention/command/reply/thread/forum/chunk，超过 provider 单消息安全长度即拒绝，不 split。

最终边界只允许 `final_guard()` → `consume_once()` → **恰好一次** `channel.send(content=exact_payload)`（具体 SDK call site 由 HLV4-A 锁定）。consume 与该调用之间不得排队、任意 await、重新解析目标、改 payload、创建 thread、split、retry、fallback、fan-out 或写入 generic ledger。provider 结果不确定时标为 UNKNOWN / reconciliation，不自动 resend，不创建第二 permit 或 Attempt。异常同样 fail closed。

HLV4-A 必须把唯一不可逆 call site 结构性替换为 `HARD_PRE_SEND_INTERCEPT`，在 guard 与 consume 后截断，真实 provider call **不得进入**；要求代码路径证据与独立 runtime hard trap / instrumentation 两类证据。其成功上限为 `REAL_HOST_DELIVERY_BOUNDARY_PASS`，`REAL_TRANSPORT_INVOCATION_COUNT = 0`、`REAL_NETWORK_SEND_COUNT = 0`、`PROVIDER_MESSAGE_CREATED = NO`。HLV4-B 需另行授权才能移除截断，届时最多一次 invocation；A0 不授权此事。

## Credential、evidence 与独立边界

credential 只由隔离 Hermes Host/plugin secret scope 持有。Core、World、Memory、Story、Prompt、grant、permit、receipt、journal、Git 和 PR 只能看到 credential identity/presence projection，不得包含 raw secret。`CLAIMED != SENT != ACKNOWLEDGED`；permit、consume、intercept、transport return 本身都不是 ACK。未来独立受信 provider-result validator 才可建立 `DeliveryEvidence(SENT)`；`ACK_VALIDATOR = HOST_GAP`。本平台只处理 Living REAL_CONTACT，不解决 Full Private RP final-output commit / H1 / H2；其 blocker 保持 `BLOCKED_BY_OFFICIAL_HOST_CAPABILITY`。

## HLV4-A 必须验证的门槛

实施时至少证明：`adapter.send()` 与 generic Hermes send 均 DENY；metadata target override、`reply_to`、`thread_id`、forum target、oversized payload 均 DENY；cron route UNAVAILABLE/DENY，standalone sender NOT REGISTERED，webhook generic delivery DENY；replay、recovery、stale adapter DENY / NO PERMIT。须同时证明真实隔离 Gateway → 官方 plugin registry → `life_engine_discord` 实例 → REAL_CONTACT authority → final guard → consume → hard intercept，且 default Gateway 未变。provider SDK 和 plugin lifecycle 均只在 Host adapter/integration 层，不能进入 Living Core 或 RealDeliveryPolicy。

## STOP 条件

若 Hermes 此确切版本无法创建独立 adapter、限定 isolated profile、硬拒绝 generic send、持有准确 lifecycle 或提供 Life Engine-only 入口：`HOST_CAPABILITY_INSUFFICIENT`，停止。若必须 patch Hermes Core、monkeypatch Host 或替换 built-in：`HOST_PATCH_REQUIRED`，停止。若需要改变 R0/R1 authority、Attempt、permit、recovery 或 evidence 合同：`ARCHITECTURE_CHANGE_REQUIRED`，停止。A0 本身不实施插件、Host 操作或真实发送；`ARCHITECTURE_CHANGE_REQUIRED = NO`、`ROADMAP_DIRECTION_CHANGE = NO`。
