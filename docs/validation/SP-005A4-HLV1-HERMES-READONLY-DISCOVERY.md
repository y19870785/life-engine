# SP-005A4-HLV1-R1：Hermes 真实 Host 只读发现与 Binding Validation 重试

## Scope / Safety / Git

Roadmap Stage：Real Host Integration → SP-005A4-HLV1 → Read-only Discovery / Binding Validation Retry。Why Now：E0 的 R1/R2/R3 已取得隔离环境与真实 Gateway lifecycle 证据，`ENVIRONMENT_GATE_READY = YES`；本轮在**不运行 Gateway**的条件下重新执行 HLV1 Phase 0，并映射当前 Hermes 的可信能力来源。原 HLV1 Phase 0 因隔离环境证据不足而 `BLOCKED` 是历史事实；本文件是 E0 remediation 后的重新发现，不回写成当时已 PASS。

固定 Base `f52042188fa960b0d66b99644334454d08995420`；本轮开始时 PR #37 为 OPEN / Draft，Head `704a0d758f2a941f1d5fc9f2d63d228512453bfc`，工作区 clean。本轮只读检查当前 Test Home/registry/source、已有 Host 状态与日志，以及三个 Discord identity **GET**；没有 Gateway 启停/reload、真实 inbound、Living mutation、消息发送或 Default Home 操作。仓库仅修改脱敏文档与验证矩阵。

## Phase 0 — Current Environment Gate

本轮重新逐值比较，而非仅转述 E0：Test Home 与 Default Home 的 realpath、`install_id` 均不同；Test Home 的持久 named profile `life-engine-hlv-test` 仍存在；`.env` 是预期用户所有、非 symlink、mode `0600`，Bot credential 仅在内存中验证存在。Test Home 单一 `DISCORD_ALLOWED_USERS` 与 Life Engine 受保护 registry 的 Owner 值相等，registry `host_home` 指向 Test Home、`owner_channel=discord`。Hermes 官方 `parse_profile_routes` 解析恰好一条 Discord + exact Server + exact Channel → Test profile；`discord.allowed_channels` 恰好为该 Channel，无 wildcard。Bot/Server/Channel 的本地受保护 ID fixture 仍与 Test Home 配置一致；该 fixture 明确 `authority=false`，不被当作身份来源。

使用 Test Home credential 仅执行 Discord API v10 `GET /users/@me`、`GET /channels/{id}`、`GET /guilds/{id}`：当前认证 Bot ID、Channel ID、Channel 所属 Guild ID 和 Guild ID 均与受保护 fixture 一致。没有输出 credential、Authorization header、响应正文或任何真实 ID；没有 POST/PUT/PATCH/DELETE、interaction 或 send。Test Gateway 当前无进程，Test Home 持久 `gateway_state=stopped`；Default Gateway 仍为同一受保护运行上下文。`ENVIRONMENT_GATE = PASS`。这些 GET 证明当前身份可识别，不证明 Bot 能发送消息。

历史 2026-09-30 Telegram → Discord guidance 拓扑仍为 `HISTORICAL_ONLY`；当前 Gate 使用独立 Test Home/Agent/Bot/Server/Channel。微信与 OpenClaw 不在本轮发现范围。E0 的 Gateway 启停属于独立 `REAL_HOST_LIFECYCLE_PASS` 前置证据，本轮最高证据等级仅 `REAL_HOST_READONLY_PASS`。

## Hermes Identity / Home / Profile / Binding Authority

当前 Hermes Test Gateway 上次运行状态报告版本 `0.21.3`、源码 SHA `01382698fc32ec7740b6a204d9b7a6abeac74d33`；本轮重新核对同一源码 checkout SHA、该 venv 的 `hermes-agent` package metadata 版本 `0.21.3`，以及 `hermes_cli`、Discord adapter 的实际 Python module path 均解析到该 checkout。**这证明本轮选用的 venv 与审计源码一致；没有假定其他系统 PATH 上的 Hermes 命令也一致。**

`hermes_cli/install_identity.py::read_or_create_install_id` 使用 Home 内持久 `install_id`，`hermes_cli/profiles.py` 将 named profile 映射为 Home 下持久目录；`gateway/session.py::_session_key_namespace` 以 profile 隔离 session key。`gateway/run.py::_profile_name_for_source` 使用 `profile_routes`；`run_adapters.py::_stamp_routed_profile` 将匹配结果写入受信 `SessionSource.profile`。Test Home 的 exact route 经官方 parser 当前复核；E0 live `served_profiles` 是独立 lifecycle 证据。Hermes 没有名为 A3 Binding Authority 的原生对象；A3 Authority 应绑定这些 Host-owned Home/install/profile/process 与 Life Engine registry identity，不能让 model/tool JSON 决定。A3 authority/plugin epoch、Core generation 仍由各自可信边界管理，Hermes PID 或 session ID 不替代它们。

## Trusted Inbound / HostIdentityEnvelope / Session

`plugins/platforms/discord/adapter.py::_discord_message_admission` 从 Discord `message.id`、`message.author.id`、`message.channel.id`、`message.guild.id` 等 provider event 字段进入准入路径，随后 `_dispatch_discord_message` 调用 `_handle_message`。`_is_allowed_user` 读取 profile-scoped allowed users/roles，也可能接受 pairing grant；因此 Test `.env` 的单一 Owner allowlist **不能单独证明 Hermes 所有授权路径只剩一人**。未来 Living binding 必须再次按 exact Owner / platform / Server / Channel 独立拒绝，且不能把 display name、message text、prompt 或模型输出升格为 authority。当前 Test Home 未配置角色与开放式用户开关；本轮未制造 inbound 验证实际拒绝路径。

`gateway/platforms/base.py::build_source` 组装 `SessionSource`，含 platform、chat/user、guild/scope、thread、message、profile 等；`gateway/session.py::build_session_key` 生成 profile namespaced key，`SessionEntry` 持有独立 `session_id`、origin 与持久会话元数据。它们可作为 `HostIdentityEnvelope` 的**候选受信输入**；Life Engine 的 `WriterEpoch`、`WorldRevision` 与 Core generation 必须从 Core 当前授权状态取得，不能由 Hermes session key 推断。当前 `gateway_platform_event` hook 的 `run_adapters.py::_handle_gateway_platform_event` 虽先检查授权，却只 `invoke_hook(**event)`，未向插件传递完整 `SessionSource`/session ID；该 hook **单独不足以构造完整可信 envelope**。H-LV2/adapter 设计需找到可保持来源与生命周期身份的受信入口；不能从 hook payload 猜缺失字段。

## Trusted Outbound Target / Execution Consumer

`gateway/delivery.py::DeliveryTarget.parse` 支持显式 `discord:<chat_id>`，也支持 `origin`、platform home channel；`DeliveryRouter._deliver_to_platform` 通过 `DeliveryTransport.send` 调用 Discord adapter。`plugins/platforms/discord/adapter.py::send(chat_id, content, metadata)` 可接受明确 `chat_id`，先 `_resolve_channel` 再 `channel.send()`，返回 `SendResult` 和 provider message ID；这提供 **post-Core / pre-network 候选位置**。但它不是现成的 Life Engine execution-permit consumer，也不自动继承 A3 target fence。

Living 专用执行组件未来必须只接受 Binding Authority 复核的 exact platform/server/channel/Attempt/invocation/purpose，并在最后 side effect 前 consume one-time permit；不得走 `origin`、home channel、last/recent route、模型指定 target。`send` 的 `metadata.thread_id` 优先于 `chat_id`，forum channel 可自动创建 thread，长消息可拆多条，reply reference 被拒时可再尝试一次；这些都是**当前通用 Host 路径不满足“一 permit / 一 exact target / 一 side effect”**的具体缺口。H-LV2/H-LV3 需先验证可由专用 adapter/binding 层限缩这些路径，不能直接接入通用 `DeliveryRouter` 就宣称安全。`_profile_name_for_source` 在部分匹配异常路径会回退默认 profile；Living 的 trusted routing fence 必须独立 fail closed。没有发现需要改变 Life Engine Core/Attempt/permit 合同的证据，因此本轮 `ARCHITECTURE_CHANGE_REQUIRED = NO`。

## Plugin / Gateway Lifecycle / Capability Vault

`hermes_cli/plugins.py::PluginManager.discover_and_load(force=True)` 可卸载后重发现，注册项有 ownership ledger；`gateway/run_adapters.py` 管理 adapter connect/disconnect/reconnect，`gateway/run_shutdown.py` 管理 drain/stop。E0 已实证 Test Gateway planned stop 与 Default Gateway 隔离。本轮不触发任何 load/reload/restart。Hermes 没有直接提供 A3 的 `plugin_epoch`/`binding_runtime_epoch`；未来 Binding Authority 必须将真实 loader/adapter 生命周期与自身 epoch 绑定，并在旧实例失效时撤销 capability/permit。仅凭 `gateway_platform_event` observer 不能作为同步 lifecycle barrier。

Credential 由 Test Home mode `0600` `.env` 与 Hermes profile-scoped secret/config loader 提供；Discord adapter connect 时读取 scoped Bot token 并建立 transport lock。A3 `CredentialVault` 是 Life Engine 的独立内存能力保管，不等同于 Hermes `.env` 或普通插件 hook。未来运行组件不得把 raw capability/token 交给模型、prompt、普通日志或 transcript；本轮没有读取或输出 credential 内容。

## Delivery Evidence / ACK / Recovery / Auto Retry

`DiscordAdapter.send` 的 `channel.send()` 返回 provider message object 与 ID，`gateway/platforms/base.py::SendResult` 含 `success`、`message_id`、`raw_response`、`retryable`。这是受信 SENT evidence 的**候选来源**，需未来 validator 绑定 exact target、Attempt、invocation、provider identity；一次函数调用、local log 或 success boolean 不直接证明 SENT。没有找到可证明用户/平台最终接收的独立 ACK validator：`ACK_VALIDATOR = HOST_GAP`，Discord message ID 最多作为 remote acceptance / SENT 候选，不能升为 ACKNOWLEDGED。

`gateway/delivery_ledger.py` 对普通 final response 持久记录 `pending/attempting/failed/delivered`，`sweep_recoverable` 可在 dead owner 后 claim，`gateway/run_startup.py::_redeliver_claimed_obligations` **会重新调用 adapter.send**；`attempting` 也可能重送并加可见 duplicate marker。另有 reconnect/flood timer 的 runtime retry、`BasePlatformAdapter._send_with_retry`、Discord `send` 内 reply-reference fallback；Discord missed-message backfill 默认关闭，但源码提供重放入口。上述是 Hermes **普通消息**的 at-least-once/recovery 策略，不能用于 A3 Living CLAIMED 的自动 resend。Living recovery 必须由独立受信 caller 持 exact operation identity/digest 调用 `LivingHostFacade.recover_operation`，只取得 B1 projection/Attempt association，进入 reconciliation；无 execution permit、无自动发送。通用 delivery ledger 及 queue replay 若无法在 Living 路径前排除，应作为 H-LV2/H-LV3 的 Host gap 阻断执行。本轮只读分类，没有打开 SQLite ledger、制造 crash/retry 或查询用户消息。

`CLAIMED != SENT != ACKNOWLEDGED`，`DB transaction != network transaction`，`recovery != authorization`。Living permit 边界与 Full Private RP `llm_final_output_commit` 是不同问题；H1 继续 `BLOCKED_BY_OFFICIAL_HERMES_HOST_CAPABILITY`，本轮不调查或实现最终输出 commit。

## A3 → Current Hermes Capability Mapping

标签是**当前只读发现状态**，不等于已集成或可发送。`KNOWN` 表示已定位到当前 Host-owned 来源；`DISCOVERABLE` 表示已有候选但须后续受控验证；`HOST_GAP` 表示现成接口不能直接满足冻结合同。

| A3 abstraction | Hermes current source / evidence | Status | Remaining boundary |
| --- | --- | --- | --- |
| Host identity / Binding Authority | Test Home `install_id`、profile marker、E0 process identity、Life Engine registry | KNOWN | A3 Authority 与 Host 的 trusted wiring 未实现 |
| Authority / plugin epoch | Gateway PID/start identity、plugin manager ownership / force reload | DISCOVERABLE | Hermes 无原生 A3 epoch；H-LV2 验证撤销排序 |
| Core generation | Life Engine protected registry/Core | KNOWN | 不能用 Hermes process/session 代替 |
| Owner identity / trusted inbound | Discord provider `author.id`、`message.id`、guild/channel；adapter admission | KNOWN | pairing 等授权路径需独立 Owner fence；不制造 inbound |
| HostIdentityEnvelope / session | `SessionSource`、profile namespaced key、`SessionEntry.session_id` | DISCOVERABLE | plugin event hook 未传完整 source；Core revision/epoch 独立取得 |
| Explicit outbound target | `DeliveryTarget` explicit chat_id、Discord `send(chat_id)` | KNOWN | 禁止 origin/home/thread override/forum/split 路径替代 exact target |
| Plugin / Gateway lifecycle | `PluginManager`、GatewayRunner、adapter connect/disconnect | KNOWN | reload/restart 的 epoch 关联留 H-LV2 |
| Execution permit consumer | `DeliveryTransport.send` → `DiscordAdapter.send` → `channel.send()` | DISCOVERABLE | 无现成 permit hook；专用组件需最后 fence 与一次性消费 |
| DeliveryEvidence SENT candidate | provider message ID、`SendResult` | DISCOVERABLE | 独立 validator 未实现；不能直接宣称 SENT |
| ACK validator | 无受信最终交付 ACK 合同 | HOST_GAP | 不把 API success/message ID 当 ACK |
| Recovery caller / association | A3 B1 recovery projection；Hermes session origin、普通 delivery ledger | DISCOVERABLE | 普通 ledger 会重送；Living 必须绕开并只读协调 |
| Auto retry | ledger restart/reconnect/flood、base retry、Discord reference fallback | KNOWN | Living 路径必须显式排除这些重送行为 |
| Capability Vault | A3 in-memory vault；Hermes Test Home scoped credential | DISCOVERABLE | 不向 model/prompt/log 暴露 raw capability |

## Host Gaps / Deferred / Historical Drift

已确认的 Host gap：完整 `SessionSource` 未在现有 `gateway_platform_event` hook 中传递；没有原生 one-time permit consumer；通用 delivery 路径支持 target override、拆分和若干重送；没有可信 ACK validator；exact profile route 缺直接只读 runtime projection（E0 已以间接一致性证据接受）。这些是**现成 Host surface**的缺口，不宣称 Hermes 永远无法由专用 Adapter 安全吸收。H-LV2 应检查 loader/adapter 生命周期、Owner/Session 来源与旧能力撤销；H-LV3 才能验证 Living fake/local side effect 与 recovery；H-LV4 仍 `DEFINED_ONLY / NOT_AUTHORIZED`，没有网络发送资格。

与 2026-09-30 历史环境相比：Test Server ID 及 Test Home directory 中的 Channel ID 经当前 GET 复核为 `UNCHANGED`；历史 Bot ID 无独立对照，记 `UNKNOWN`，当前 credential 的 Bot identity 已重新认证；Telegram guidance 为 `HISTORICAL_ONLY`，不作为当前 topology。Default Home、Bot 在线/发送能力、真实 Owner inbound、ACK 均未被历史报告替代。

## Evidence Correction for E0-R3-R2

HLV1-R1 只读复核发现：E0-R3-R2 脚本比较了 Test Home 根目录下不存在的 `discord_command_sync_state.json`，而真实文件位于 `gateway/discord_command_sync_state.json`。原报告“真实状态文件启动前后摘要未变”的表述不成立，已在同一 PR 的 E0-R3-R2 文档中更正。真实文件当前的修改时间与嵌套 `last_attempt_at` 均早于第二次启动，且当次新增日志明确 `policy=off` skip；这些证据支持 `NEW_COMMAND_SYNC_ATTEMPT = NO`，但不能重写成当时已做正确路径的摘要比较。该纠错不影响 planned-stop、Test process 或 config fingerprint 的独立证据。

## Final Result / Commands and Redaction

`SP-005A4-HLV1-R1 = PASS`；`SP-005A4-HLV1 = PASS` 的范围仅为 **REAL_HOST_READONLY_PASS**：Phase 0 当前环境通过，Host/version、identity、inbound/outbound、session、plugin lifecycle、execution candidate、delivery、ACK gap、recovery/auto-retry 与 capability storage 均已按真实当前源码/配置分类。PASS 不等于 Hermes Living Integration、Living execution、真实发送或 Full Private RP 可用。`ARCHITECTURE_CHANGE_REQUIRED = NO`；后续阶段需独立审核和授权。

只读证据操作：固定 Git Base/Head/worktree 与 PR 查询；Test/Default Home 文件 metadata、install/profile/config/registry 本地比对；当前 Hermes source checkout SHA、venv package metadata/module path；`rg`/源码定位；当前 Discord 三个身份 GET；Test Gateway 进程与持久停止状态只读检查。未执行 Gateway 生命周期动作、插件 reload、SQLite connection、真实 inbound、Living 方法或消息发送。所有 token、Owner/Bot/Server/Channel ID、私有 Home 路径、真实 PID/session ID 均未进入本文档、PR 描述或终端报告正文。
