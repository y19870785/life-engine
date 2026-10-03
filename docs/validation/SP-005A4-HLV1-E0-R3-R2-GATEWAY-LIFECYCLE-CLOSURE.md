# SP-005A4-HLV1-E0-R3-R2：Hermes Test Gateway 第二次受控生命周期闭环

## Authorization / Scope

Roadmap Stage：Real Host Integration → SP-005A4-HLV1 → Environment Gate Remediation → E0-R3-R2。固定 Base 为 `f52042188fa960b0d66b99644334454d08995420`，继续使用 Draft PR #37。本轮仅获授权启动、观察和计划停止 Dedicated Test Home Gateway；真实 inbound、消息发送、Living operation、Default Gateway 操作均未授权，也未执行。

本次是第一次 R3 阻塞后的**第二次、单次**受控生命周期验证。第一次 R3 的观察和 R3-R1 的静态修复仍保留在各自文档中；本文件只报告本次新取得的证据。没有修改 Life Engine Runtime、测试、Schema 或 Prompt，也没有执行 HLV1 retry。

## Preflight / Isolation

启动前核对 `origin/main` 为固定 Base、PR #37 Head 为已审核的 `00162cae701dbec50a625c978af794b5925c2c66`、工作区 clean。Dedicated Test Home 与 Default Home 的 realpath、install ID 均不相同；Test Gateway 进程不存在。记录 Default Gateway 的 PID 和 `/proc` process-start identity，仅在本地比较。当前没有 Test Home systemd service、timer、container restart policy、活动 supervisor 或 auto-restart worker。

Test Home `.env` 为预期用户拥有的普通非 symlink 文件，mode `0600`；未输出内容。R1 原始 cron 五文件仍在，启动前没有额外 SQLite sidecar 或 jobs 配置；本轮没有打开 `executions.db`。R1 `CRON_STARTUP_GATE = PASS_STATIC_SNAPSHOT`，不冒充 Gateway lifecycle 证据。

R2 身份 fixture、Test Agent 持久 profile marker、Bot / Server / Channel fixture、单一 Owner allowlist 与 Life Engine test registry 指向 Test Home 的本地逐值比对均通过；没有再次访问 Discord identity API。通过 Hermes 官方 config bridge 与 `parse_profile_routes` 复核：恰好一条 Discord route，目标 profile 为 `life-engine-hlv-test`，exact Server 与 exact Channel 约束均存在，`discord.allowed_channels` 仅含该 exact Channel，无 wildcard 或 last-route fallback。真实 ID 不进入仓库。

## Effective Command Sync Policy / Config Fingerprint

启动前经 Hermes profile-scoped secret/config 路径与 `DiscordAdapter._get_discord_command_sync_policy` 确认 Test Home effective `DISCORD_COMMAND_SYNC_POLICY = off`。对 Test Home 路由配置和 Test Agent profile 配置计算本地 SHA-256，仅比较启动前、观察期间及停止后的值；credential 文件不进入 fingerprint material，摘要值也不写入仓库。三次比较一致：`CONFIG_FINGERPRINT_MATCH = YES`。

第一次 R3 的 `discord_command_sync_state.json` 作为历史证据保留。本次启动前、观察期间和停止后对其文件摘要作本地比较，均未变化；结合本次新增日志中的 `Skipping Discord slash command sync (policy=off)`，判定 `NEW_COMMAND_SYNC_ATTEMPT = NO`。第一次 attempt 是否改变过远端命令仍为 `UNKNOWN`，本轮没有调用远端 command API。

## Gateway Start / Process Identity / Agent / Discord

启动命令显式设置 `HERMES_HOME = Dedicated Test Home`，在当前 Hermes checkout 使用 `--profile default gateway run --no-supervise`，将输出写入 Test Home 内 mode `0600` 的受保护本地日志。没有使用隐式默认 Home、service start 或 `--replace`。

新 Test PID 与 Default PID 不同；其 `/proc/<pid>/environ` 中 `HERMES_HOME` 精确对应 Test Home，process-start identity 在整个操作期间保持一致。Test Home `gateway_state.json` 在运行中指向该 PID/Home，并报告 `life-engine-hlv-test` 出现在 `served_profiles`。Discord platform runtime state 为 `connected`；本次新增 Host 日志确认 Discord adapter 连接及 Test profile 识别。Bot 连接只证明 transport connection，**不代表 SENT**。

## Exact Route Observability

当前 Hermes 没有暴露运行中 `runner.config.profile_routes` exact 约束的只读 projection。按照 R3-R1 已冻结的裁决，本轮组合官方 parser 的单条精确路由结果、未漂移的配置 fingerprint、运行时 `served_profiles` 与 Test Home 进程身份，作为**间接一致性证据**。`EXACT_ROUTE_RUNTIME_PROJECTION = HOST_GAP_ACCEPTED`；本轮没有制造 inbound，也不宣称 `DIRECT_RUNTIME_PASS`。

## Observation / Side Effects

观察窗口为约 90 秒。监测启动进程输出及 Test Home gateway、agent、error 日志的本次新增部分；随后核对停止时日志。没有观察到 cron job 执行、deferred Bot Chat / delivery queue drain、slash-command sync attempt 或消息创建/发送尝试。日志记录了 `policy=off` 跳过 command sync。没有执行真实 inbound、Living tick / prepare / claim / permit / delivery submission，未调用手工 Discord、Telegram 或微信发送。

`SEND_EVIDENCE = NO_SEND_OBSERVED`。这是可观察 Host 日志范围内的结论；没有 transport 级完整审计，不写成 `ABSOLUTE_ZERO_SEND_PROVEN`。Discord connection 与 user-visible send 继续严格区分。

## Planned Stop / Persisted Lifecycle State

停止前重新核对 exact Test PID、`/proc` process-start identity 与 `HERMES_HOME`。在 Test Home scope 调用 Hermes 官方 `gateway.status.write_planned_stop_marker(exact_test_pid)`；立即核对 marker 位于 Test Home，记录的 target PID 和 target process-start identity 均与本次 Test 进程一致。随后仅向该 exact PID 发 SIGTERM，没有调用泛用 Gateway stop、`pkill` 或进程组信号。

Hermes 接受 planned stop，Discord adapter 与 session store 完成关闭，Test 进程以退出码 `0` 消失；Test Home 持久 `gateway_state = stopped`。Default Gateway 的 PID 与 process-start identity 前后相同。停止后再次确认 Test Gateway 无进程，路由配置 fingerprint 未变，command-sync state 未变。保留全部 Gateway runtime artifact、日志、state、SOUL、cron 与 SQLite sidecar；未清理或直接改写 Host 状态文件。

## Evidence Level / Final Result

`SP-005A4-HLV1-E0-R3-R2 = PASS`。首次 R3 的三个阻塞在本次授权范围内关闭：exact route 直接 projection 缺口按已审核的 `HOST_GAP_ACCEPTED` 处理；command sync 在运行时跳过且没有新增 attempt；官方 planned stop 使进程与持久状态均停止。结合 R1、R2 已为 PASS，且没有新环境 blocker，`SP-005A4-HLV1-E0-R3 = PASS`、`SP-005A4-HLV1-E0 = PASS`、`ENVIRONMENT_GATE_READY = YES`。证据等级仅为 **REAL_HOST_LIFECYCLE_PASS（E0 lifecycle closure）**，不是 REAL_HOST_DRY_RUN_PASS、REAL_HOST_SENT 或 ACKNOWLEDGED。

`SP-005A4-HLV1 = READY_FOR_READONLY_RETRY`，**尚未重试，更不是 PASS**。Draft PR #37 保持 Draft；后续 HLV1 Phase 0 必须重新执行并接受独立审核。本轮不涉及 Life Engine 冻结 Core contract，`ARCHITECTURE_CHANGE_REQUIRED = NO`。

| 项目 | 结果 |
| --- | --- |
| TEST_GATEWAY_STARTED / TEST_GATEWAY_STOPPED | YES / YES |
| TEST_AGENT_RUNTIME_LOAD / DISCORD_CONNECTION | PASS / PASS |
| COMMAND_SYNC_RUNTIME / NEW_COMMAND_SYNC_ATTEMPT | OFF_CONFIRMED / NO |
| ROUTE_STATIC_PARSE / CONFIG_FINGERPRINT_MATCH | PASS / YES |
| EXACT_ROUTE_RUNTIME_PROJECTION | HOST_GAP_ACCEPTED |
| SEND_EVIDENCE | NO_SEND_OBSERVED |
| PLANNED_STOP_RUNTIME / FINAL_GATEWAY_STATE | PASS / STOPPED |
| DEFAULT_GATEWAY_MUTATED | NO |
| REAL_INBOUND / LIVING_OPERATION / REAL_SEND | NO / NO / NO |
| RUNTIME_CODE_CHANGED / SCHEMA_CHANGED / PROMPT_CHANGED | NO / NO / NO |
| HLV1_RETRY_STARTED | NO |

所有本地证据中的 credential、Owner / Bot / Server / Channel ID、精确 PID、私有路径及 Discord session 信息均未提交。本文仅使用脱敏状态与可审计的 Host-owned 证据类型。
