# SP-005A4-HLV1-E0-R3：Hermes Test Gateway 首次受控启动验证

## Scope / Authorization

Roadmap Stage：Real Host Integration → SP-005A4-HLV1 → Environment Gate Remediation → E0-R3 First Controlled Test Gateway Startup。固定 Base 为 `f52042188fa960b0d66b99644334454d08995420`，沿用 Draft PR #37。本轮仅获授权启动、观察并停止 **Dedicated Test Home** Gateway；未授权 Living operation、真实 inbound、手工消息发送、Default Gateway 操作或配置修改。

**最终结果：SP-005A4-HLV1-E0-R3 = BLOCKED。** 启停和隔离进程证据已取得，但精确路由缺少直接的运行时装载证据；Discord 启动路径还记录了一次 slash-command sync attempt，不能从现有记录证明它仅做了只读查询。`ARCHITECTURE_CHANGE_REQUIRED = NO`。`SP-005A4-HLV1-E0 = BLOCKED / IN_PROGRESS`，`SP-005A4-HLV1 = BLOCKED`；不得据此开始 HLV1 retry。

## Pre-start Gates / Default Gateway Protection

启动前重新确认：`origin/main` 与 PR #37 Base 为固定 SHA，PR Head 为 `e63d1e1dfa5dce1c9dd2e1f161597ec2178a8d5e`，工作区 clean。Test / Default Home 的 realpath 与 install ID 不同；Test `.env` 是预期 owner 的普通非 symlink 文件，mode `0600`。Test cron 目录仍有 R1 的五个原始**文件**及原有 `output` 目录，无 `executions.db-wal`、`executions.db-shm`、`jobs.json` 或待投递队列；没有打开 SQLite 账本。`CRON_STARTUP_GATE = PASS_STATIC_SNAPSHOT`，不等于生命周期 PASS。

R2 的 Test profile marker 和本地 `0600` 身份比较记录仍匹配 Test install；Test Home 配置只有一条 `Discord + exact Server + exact Channel → life-engine-hlv-test` 路由，`discord.allowed_channels` 经 Hermes CSV gate 解析后恰为一个精确 Channel，没有 wildcard 或环境变量覆盖。Test credential 存在且未读取输出；Test `.env` 的单一 Owner allowlist 与 Life Engine canonical test registry Owner 本地逐值一致，registry 仍指向 Test Home。R2 已取得的 Bot/Server/Channel 当前身份 GET 证据未发现配置漂移，因此本轮未重新访问 Discord 身份 API。

启动前进程表只有 Default Gateway；记录了其 PID 与进程起始时间作为不公开的本地比较值。Test Gateway 未运行。启动命令显式设置 `HERMES_HOME` 为 Dedicated Test Home，并用 Hermes `--profile default` 固定该 Test Home 的 launch root；未依赖隐式默认 Home，未使用 service start/restart 或 `--replace`。Hermes 源码 SHA 仍为 R1 已审计的 `01382698fc32ec7740b6a204d9b7a6abeac74d33`。

## Test Gateway Start / Process Identity

在 Test Home 下以受保护的 `0600` 本地日志启动一次 Gateway，观察约 **90 秒**。新进程 PID 与 Default Gateway 不同；运行中的 `/proc/<test-pid>/environ` 精确显示 `HERMES_HOME` 为 Test Home。Test Home 的 `gateway_state.json` 记录的 PID、Home 与本次进程一致；没有把精确私有路径或身份 ID 写入仓库。

Gateway 日志显示 Discord adapter 开始连接、连接成功，随后报告 `1 platform`。Test Home 的 credential 与 R2 已认证 Bot identity 的本地比较记录保持不变；日志中的 Bot 显示名仅作连接旁证，**不作为身份 authority**。`DISCORD_CONNECTION = PASS`，不代表消息已发出。

## Test Agent / Owner / Explicit Route Load

Gateway 日志明确报告 multiplex cron 将服务 `default` 与 `life-engine-hlv-test` 两个 profile；Test Home 的运行状态文件也记录了这两个 `served_profiles`。因此 Test Agent 的 Host 运行时识别为 **PASS**。Test profile 首次运行还由 Hermes 自动生成默认 `SOUL.md` 和本地 state/cron 文件；这是实际 Host 启动副产物，未由本任务编辑 persona、Memory 或 Life Engine Core。该事实应在后续 Test Agent 审核中保留。

Owner allowlist 与精确 Channel gate 在启动前按 Test Home 受信配置及 Hermes 解析规则复核；没有制造 inbound 去触发 Owner 校验。实际 Gateway 日志与运行状态**没有单独暴露** exact Server + Channel route 的装载结果，也没有执行被禁止的 inbound 来观察路由匹配。因此 `EXPLICIT_ROUTE_LOAD = BLOCKED`，不能把 R2 静态 parser PASS 或 `served_profiles` 自动提升为精确路由运行时 PASS。后续应先设计只读、无 inbound 的运行时配置观测办法，再决定是否补测；本轮未改 Host 配置或再次启动。

## Cron / Housekeeping / Unexpected Side Effect

启动日志显示内置 cron ticker 服务两个 profile、housekeeping 与 kanban dispatcher 启动；停止时 drain 报告 active agent、cron、API、deferred work 均为零。没有观察到 job 执行、deferred Bot Chat drain、delivery queue drain、Living operation 或消息发送尝试。Test Gateway 的 stdout 与 Test Home gateway/agent/error 日志在本次观察窗口内未出现明确的 send/message-create 记录。**对外用户可见发送仅能报告 `NO_SEND_OBSERVED`；没有 transport 级完整审计，不能宣称绝对发送计数已证明为零。**

另有一项与消息发送不同的 Host 行为：Test Home 的 `discord_command_sync_state.json` 在本次窗口内更新，记录了 slash-command sync `last_attempt_at`，但没有 success/summary。Hermes 当前默认 sync policy 为 `safe`；源码 `plugins/platforms/discord/adapter.py::_run_post_connect_initialization` 在该路径可能执行 Discord command reconciliation。现有本地证据无法确认是否发生远端 command mutation，故记为 **EXTERNAL_COMMAND_SYNC_OUTCOME = UNKNOWN**，不能把“Bot connected”扩大解释为“只做连接”。这不是消息发送或 ACK 证据，也不是 Life Engine 架构冲突。需独立审查该启动副作用后再解除 R3 阻塞；本轮未改 sync policy、未访问 Discord command API。实时监测只覆盖启动进程 stdout；Test Home 的其他 Host 日志在停止后复核，因此未形成能够在任意消息尝试前立即截断的完整 transport 监控。

## Controlled Shutdown / Post-run Drift

观察窗口结束后只向 Test Gateway 的独立进程组发送 SIGTERM。日志显示 Discord adapter 断开、所有 adapter 关闭、SessionDB close 完成，生命周期文件记录 `exit_reason = graceful_shutdown`；Test PID 已消失，Default Gateway 的 PID 与起始时间保持不变。Hermes 对 signal-initiated shutdown 按源码以退出码 `1` 结束，并在 Test Home `gateway_state.json` 保留 `gateway_state=running`，用于其未来 container boot 自动恢复逻辑；这与**当前进程已停止**是不同事实。没有修改或清理该运行时状态，后续启动前必须重新确认 Test Gateway 未被自动拉起。

Test Home 产生或更新了 gateway/agent/error/shutdown 日志、状态与 heartbeat、cache、`state.db`、kanban SQLite sidecar、Discord command-sync attempt 记录，以及 Test profile 的默认 `SOUL.md`、state/cron/log 文件。均留在 Test Home，未擅自删除。原始 cron 五文件仍在；cron `executions.db` sidecar 仍为零。未主动修改 Default Home；Default Gateway 的 PID 与进程起始时间未变。

解除阻塞需要独立评审三件事：怎样在不制造 inbound 的前提下观察运行时 exact route；Test Home 的 Discord command sync 是否应在后续启动前关闭或另行授权；怎样使用 Hermes 的 planned-stop 路径，避免仅凭 SIGTERM 留下 `gateway_state=running`。本轮不自行编辑配置、重写运行状态或再次启动 Gateway。

## Evidence Level / Final Declaration

Gateway 启停、Test Home 进程归属、Test Agent 识别、Discord adapter 连接取得 **REAL_HOST_LIFECYCLE_PASS（局部）**。精确路由装载、外部 command-sync 副作用和绝对零发送均未获得足够证据，不授予 R3 / E0 整体 PASS；不升级为 REAL_HOST_DRY_RUN_PASS、REAL_HOST_SENT 或 ACKNOWLEDGED。

| 项目 | 结果 |
| --- | --- |
| SP-005A4-HLV1-E0-R3 | BLOCKED |
| SP-005A4-HLV1-E0 / HLV1 | BLOCKED / IN_PROGRESS；BLOCKED |
| TEST_GATEWAY_STARTED / TEST_GATEWAY_STOPPED | YES / YES（进程已退出；signal 退出码 1） |
| DEFAULT_GATEWAY_MUTATED | NO |
| TEST_AGENT_RUNTIME_LOAD | PASS |
| DISCORD_ADAPTER_LOAD / DISCORD_CONNECTION | PASS / PASS |
| EXPLICIT_ROUTE_LOAD | BLOCKED |
| UNEXPECTED_SEND_ATTEMPT | UNKNOWN（Host 日志中 NO_SEND_OBSERVED；缺 transport 级审计） |
| REAL_SEND / REAL_INBOUND_TEST / LIVING_OPERATION | NO / NO / NO（本任务没有发起） |
| RUNTIME_CODE_CHANGED / SCHEMA_CHANGED / PROMPT_CHANGED | NO / NO / NO |
| HLV1_RETRY_STARTED / H_LV2_STARTED / H_LV3_STARTED / H_LV4_STARTED | NO / NO / NO / NO |

执行过的操作：Git 与 Test Home 启动前只读检查；一次显式 Test Home Gateway 启动、约 90 秒观察、Test 进程 SIGTERM；Test Home 日志与文件 metadata、Hermes 源码只读复核。未重新打开 `executions.db`，未执行 Discord/Telegram/微信消息发送或真实 inbound，未启动 Living。所有 credential、Authorization header、Owner/Server/Channel/Bot ID、Discord session ID 与私有路径均未写入本文档。
