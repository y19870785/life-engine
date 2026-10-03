# SP-005A4-HLV1-E0-R3-R1：Gateway lifecycle 阻塞静态修复与补证方案

## Scope / Current R3 Blockers

Roadmap Stage：Real Host Integration → SP-005A4-HLV1 → Environment Gate Remediation → E0-R3-R1。本轮沿用固定 Base `f52042188fa960b0d66b99644334454d08995420`、`validation/sp-005a4-hlv1-e0-test-env` 和 Draft PR #37。只做当前 Hermes 源码、Test Home 配置及进程/服务的静态审计；仅为关闭 command sync 修改 Dedicated Test Home 的 `.env`。**没有再次启动、停止或重启任何 Gateway**，没有真实 inbound、Living operation、消息发送或 Life Engine Core 修改。

R3 原结论保持 `BLOCKED`；三项阻塞是：B1 exact Server + Channel route 缺直接运行时证据；B2 第一次 Discord slash-command sync attempt 的远端结果未知；B3 裸 SIGTERM 后 Test Home 持久状态仍为 `gateway_state=running`。本轮目标是清楚定义下一次补测的安全边界，不把静态推导冒充新的 lifecycle PASS。

## Route Runtime Observability Analysis（B1）

当前 Hermes 源码 checkout 仍为 `01382698fc32ec7740b6a204d9b7a6abeac74d33`。受信加载路径：`gateway/config_loader.py::_TOPLEVEL_BRIDGE` 将 `gateway.profile_routes` 搬入 Gateway config data（约 93、129 行）；`gateway/config.py::GatewayConfig.from_dict` 调用 `parse_profile_routes`（约 720–742 行）；`gateway/run.py::load_gateway_config_for_runner` 在启动时重新加载 config，`GatewayRunner.__init__` 把结果保存在 `runner.config`（约 1745–1771、3397–3407 行）；`GatewayRunner._profile_name_for_source` 经 `match_profile_route` 使用该内存对象（约 4285–4332 行）；主 adapter 的 `_stamp_routed_profile` 在接收来源时调用它（`gateway/run_adapters.py` 约 1437 行）。

逐级检索当前 Host 暴露面，结果如下：

| 观测等级 | 当前能力 | 结论 |
| --- | --- | --- |
| A. runtime state projection | `gateway_state.json` 只有 `served_profiles` 等运行信息，没有 route 数量、约束或目标 | ABSENT |
| B. startup structured log | 首次 R3 日志确认 `life-engine-hlv-test` 被服务，但无 exact route 装载摘要 | ABSENT |
| C. internal loaded config object | `runner.config.profile_routes` 在进程内存在；没有公开的只读导出 | INTERNAL_ONLY |
| D. diagnostic/status command | `gateway/control_socket.py` 的 `identify` / `status` 投影与 web status 暴露 served profiles，不暴露 profile_routes；其他 verb 可能修改 Host | ABSENT |
| E. deterministic startup parser evidence | 当前 Test Home 配置经官方桥接和 parser 可确定为单条 exact Server + Channel → Test profile | AVAILABLE_STATIC_ONLY |

因此 `ROUTE_OBSERVATION_METHOD = HOST_GAP`：**无需真实 inbound 的现有 read-only Host surface 无法直接证明运行中 `runner.config.profile_routes` 的 exact 约束。** 下一次启动可安全组合“启动前官方 parser 的脱敏断言 + live control-socket 身份与 served-profile 投影 + 配置文件签名未漂移”，但这仍是确定性间接证据，不得写成 direct runtime route projection 或 `EXPLICIT_ROUTE_LOAD = PASS`。若未来需要直接证据，应先单独审核 Host-owned、只读、脱敏的 startup route summary/status projection；本任务不改 Hermes 源码，不制造 inbound。报告格式应限于 `LOADED_ROUTE_COUNT`、`TARGET_PROFILE = VERIFIED`、`EXACT_SERVER_CONSTRAINT = PRESENT`、`EXACT_CHANNEL_CONSTRAINT = PRESENT`，绝不输出 ID。

## Discord Command Sync Analysis / Effective Disable（B2）

`plugins/platforms/discord/adapter.py` 中 `_DISCORD_COMMAND_SYNC_POLICIES = {safe, bulk, off}`（约 82 行）；`_get_discord_command_sync_policy` 通过 profile-scoped `DISCORD_COMMAND_SYNC_POLICY` 读取，缺省为 `safe`（约 2658–2667 行）。`_run_post_connect_initialization` 在 `off` 时先记录 skip 并返回；`bulk` 使用 `tree.sync()`；`safe` 先记录 attempt，再调用 `_safe_sync_slash_commands`（约 2067–2117 行）。safe 路径可调用 Discord global-command delete/upsert/edit（约 2751–2810 行），不是纯只读身份查询。

本轮只向 **Dedicated Test Home `.env`** 追加 `DISCORD_COMMAND_SYNC_POLICY=off`；修改前复核 Home 与 Default Home 的真实路径和 install ID 不同、Test Gateway 不运行、`.env` 为 Test 用户拥有的非 symlink 普通文件且 mode `0600`，并确认该 key 原先不存在。通过 `O_NOFOLLOW | O_APPEND` 单次写入并 `fsync`，未打印、复制、轮换或更改 Bot credential/Owner allowlist。修改后 `.env` 仍为 `0600`。使用 Hermes `build_profile_secret_scope(Test Home)`、multiplex secret scope、真实 `DiscordAdapter._get_discord_command_sync_policy` 在 fresh Python 中取得 **`off`**；源码顺序确认 `off` 分支在 attempt 记录及远端 sync 调用之前返回。`NEXT_START_COMMAND_SYNC = DISABLED_VERIFIED`。未启动 Gateway 验证，下一次获授权启动仍须检查运行日志明确出现 `policy=off` 的 skip 证据。

第一次 R3 留下的 `discord_command_sync_state.json` 只有 attempt，没有 success/summary；没有远端 command registry 的事前快照。当前 GET 也无法单独重建第一次 attempt 是否改变过远端命令。因此 `PREVIOUS_COMMAND_SYNC_OUTCOME = UNKNOWN`，本轮未调用 Discord API，也未删除或改写该状态文件。

## Gateway Shutdown State Machine / Planned Stop（B3）

首次 R3 用裸 SIGTERM：`gateway/run.py` 的 signal handler 未找到 planned-stop marker，于是设置 `_signal_initiated_shutdown = True`（约 4992–5013 行）。`gateway/run_shutdown.py` 在完成 adapter/session 清理后对此类意外 signal 保留 `gateway_state=running`，使未来 container boot 能恢复（约 1928–1945 行）；因此 `graceful_shutdown` 和退出码 1 不等于持久 `stopped`。这是 Hermes 有意的生命周期语义，不应直接编辑 `gateway_state.json`。

Hermes 的计划停止机制已找到：`gateway/status.py::write_planned_stop_marker(target_pid)` 写入目标 PID、进程起始时间及时间戳（约 1561–1576 行）；`hermes_cli/gateway.py::stop_profile_gateway` 在发出 SIGTERM 前调用该 marker（约 1818–1855 行）；Gateway watcher/handler 只接受属于自身的有效 marker 并走 planned-stop 分支（`gateway/run.py` 约 4398–4443、4992–5013 行）。planned-stop 不设置 unexpected-signal flag，`gateway/run_shutdown.py` 随后持久化 `gateway_state=stopped`，预期以 clean exit 结束。

下一次受控补测应避免泛用 `hermes gateway stop`：当前 WSL 用户有正在运行的 Default `hermes-gateway.service`，泛用 CLI 可能先选择同名 service。更窄的官方内部路径是：先从 Test Home control socket / PID record 与 `/proc` 双重确认 exact Test PID、起始时间及 `HERMES_HOME`；在 **Test Home scope** 调用 Hermes `write_planned_stop_marker(exact_test_pid)`，核对 marker 位于 Test Home 且包含同一进程身份；然后只对该 Test PID 发 SIGTERM，等待退出，并只读确认 `gateway_state=stopped`、Test PID 消失、Default PID/起始时间不变。该步骤属于未来 **R3-R2 单独授权的运行操作**，本轮仅冻结方案；绝不手工修改、删除或伪造状态文件。

## Auto-Restart Risk / Runtime Artifacts

本轮 `/proc` 只发现 Default Gateway，先前 Test PID 已不存在，Test Home 无 gateway PID 文件。当前 WSL PID 1 为 systemd，非 container；用户级 systemd unit 只有 Default Hermes Gateway 和 dashboard，没有 Test Home unit/timer，Default unit 不引用 Test Home；没有活动的 Test Home auto-restart worker。因此 **`AUTO_RESTART_RISK = NO`（当前进程与 supervisor 快照）**。Test Home 的持久 `gateway_state=running` 仍是未来显式 Test Home launcher/container boot 的潜在恢复信号；任何下一次启动前都必须重新检查进程和 supervisor，不能把此快照当永久保证。

R3 生成的默认 Test profile `SOUL.md`、state/cron/log、SQLite sidecar、command-sync state 等均作为 Host lifecycle 证据保留；本轮未清理、未编辑 Test Agent SOUL、未打开 `executions.db`。没有发现需要改变 Life Engine Core、Schema、Prompt、Attempt、Recovery 或 Binding Authority 语义的证据，`ARCHITECTURE_CHANGE_REQUIRED = NO`。

## Next Startup Preconditions / Remaining Gaps

R3-R2 仍需单独授权。届时先重新核对固定 Git 对象、Test/Default Home 与 install 隔离、Owner/Bot/Server/Channel 身份、Test Gateway 无进程、Default Gateway 基线、cron snapshot、Test `.env` mode `0600` 与 effective command-sync `off`。启动后只读确认 `policy=off` skip、Bot connection、Test profile、无 inbound/Living/send，并按 planned-stop marker + exact PID 路径停机。对 exact route，只能报告已有的间接证据或先取得经独立审核的新 Host 只读 projection；不得因本轮静态链推导而升级为 direct runtime PASS。历史 sync outcome 保持 UNKNOWN。

## Final Result

`SP-005A4-HLV1-E0-R3-R1 = PASS`：安全 route 观测缺口已明确，下一次 command sync 已由官方配置机制静态关闭并 parser-verified，planned-stop 路径与当前无活动自动重启风险已明确。**R3 仍 BLOCKED；E0 仍 BLOCKED / IN_PROGRESS；HLV1 仍 BLOCKED。** 本轮没有第二次 Test Gateway 启动，也没有将首次 R3 证据升级。

| 项目 | 结论 |
| --- | --- |
| ROUTE_OBSERVATION_METHOD | HOST_GAP（可做间接一致性核验，不等于直接 runtime route projection） |
| NEXT_START_COMMAND_SYNC | DISABLED_VERIFIED |
| PREVIOUS_COMMAND_SYNC_OUTCOME | UNKNOWN |
| PLANNED_STOP | DEFINED（待 R3-R2 lifecycle 实证） |
| AUTO_RESTART_RISK | NO（当前活动 supervisor 快照；未来启动前重查） |
| TEST_GATEWAY_RUNNING / DEFAULT_GATEWAY_MUTATED | NO / NO |
| REAL_SEND / REAL_INBOUND / LIVING_OPERATION | NO / NO / NO |
| RUNTIME_CODE_CHANGED / SCHEMA_CHANGED / PROMPT_CHANGED | NO / NO / NO |

执行过的操作：固定 Base、PR Head、clean worktree 验证；Test Gateway/Default Gateway 与 systemd/timer 的只读检查；Hermes 当前源码、状态投影与 Test Home 文件 metadata 的只读审计；仅追加 Test Home command-sync 禁用配置；fresh Python 读取 Hermes effective policy；新增本脱敏文档。未输出或提交 token、Owner/Bot/Server/Channel ID、session ID 或私有路径。
