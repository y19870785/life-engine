# SP-005A4-HLV2：Hermes Host 生命周期与 Authority 验证

## 范围与结果

Roadmap Stage：Real Host Integration → SP-005A4 → HLV1 DONE → HLV2。开工 canonical Base：`991a988c9f8c2a80eda834697af81957fbe8688d`；独立分支 `validation/sp-005a4-hlv2-host-lifecycle`，不继续 PR #37 分支。当前远端复核 PR #37 已合并，其 merge commit 正是该 Base；[HLV1](SP-005A4-HLV1-HERMES-READONLY-DISCOVERY.md) 与 [E0 lifecycle closure](SP-005A4-HLV1-E0-R3-R2-GATEWAY-LIFECYCLE-CLOSURE.md) 保留 canonical historical evidence，未修改。

2026-10-03 的两轮隔离真实 Gateway 生命周期及本地 inert comparison 取得 `SP-005A4-HLV2 = PASS`，证据等级仅 `REAL_HOST_LIFECYCLE_AUTHORITY_PASS`，待独立 Draft Review。真实部分是 Test Gateway 启停、进程身份、profile load、adapter connection/disconnection 与持久状态；旧 authority/capability 拒绝部分是 **Host binding projection candidate 的本地非网络 probe**，不是已部署 BindingAuthority、真实 capability 或 permit 的验证。

未制造真实 inbound、未调用 send、未执行 Living mutation / claim / permit issue / permit consume / delivery submission。没有修改 Hermes source、Test config、Life Engine Runtime、Schema 或 Prompt；没有执行 plugin/config/profile reload。`REAL_HOST_DRY_RUN_PASS` 尚未取得，`SENT / ACKNOWLEDGED = NOT TESTED`。H-LV3 未授权、未开始；H-LV4 保持 DEFINED_ONLY / NOT_AUTHORIZED；Full Private RP 保持 BLOCKED_BY_OFFICIAL_HERMES_HOST_CAPABILITY。

## Phase A：启动前隔离与 outbound 安全门

每轮启动前及最终停止后重新核对：Dedicated Test Home 与 Default Home 的 realpath、install ID 不同；Test Agent 的持久 profile marker 与 exact Discord Server/Channel route 均指向 `life-engine-hlv-test`；Owner allowlist 与受保护 Life Engine registry 的 Owner 一致，registry `host_home` 精确指向 Test Home。`host_agent_id` 为空是 E0 已记载的 Hermes 部署事实，该字段没有被补写或当作 named profile 的来源。Test `.env` 为 expected owner 所有的普通非 symlink 文件、mode `0600`。

Bot/Server/Channel/install/profile fixture 在本轮前后逐值一致；Bot token 的编码身份部分在内存中与既有 Bot fixture 比较相等，credential 本轮前后本地比较相等。这是静态连续性比较，**没有重新执行 Discord identity GET，也不冒充本轮远端 Bot identity 重新认证**。fixture 继续 `authority=false`；runtime adapter connection 是独立事实。

Test 初始进程 absent、`gateway_state=stopped`。记录并逐阶段比较 Default PID、`/proc` process-start identity 与 Home，最终三者均未变。检查当前用户进程、systemd system/user unit 文件、crontab 以及容器工具可用性，未发现指向 Test Home/profile 的 service、timer、container、supervisor 或 auto-restart worker；启动显式 `--no-supervise`。

在 Host 停止状态只读检查 launch Home 和 named Test profile：无待执行 cron jobs、无 pending_messages、restart/update notification marker、deferred/queue/watcher artifact，无 resume_pending / active_turn_token；kanban task/run/event 等表为空。SQLite 仅在确认 WAL 为空后以 URI `immutable=1` + `PRAGMA query_only=ON` 查询，未调用 Host ledger opener、sweep、claim 或 replay。launch Home 有一条历史 `delivered` obligation，没有 pending/attempting/failed obligation；named Test profile 无待执行 obligation。该历史 delivered 记录不属于本阶段 send evidence。

每次启动前 dotenv/config 源与官方 `DiscordAdapter._get_discord_command_sync_policy` 确认为 `off`；official profile-route parser 复核单条 exact Server/Channel route，allowed_channels 只含该 Channel。config/profile/registry fingerprint 不含 credential 文件；credential 只做独立受保护比较，不进入公开 fingerprint material。启动前、两轮之间及最终比较均一致。

## Phase B/C/E/F/G：真实生命周期与身份对比

显式设置 `HERMES_HOME = Dedicated Test Home`，使用已核对 venv 的 Hermes entrypoint、`--profile default gateway run --no-supervise`；第二轮用同一 venv Python 执行该 entrypoint。没有 `--replace`、generic service start/stop 或 Default Gateway mutation。源码 checkout 仍为 `01382698fc32ec7740b6a204d9b7a6abeac74d33`；沿用 HLV1 对该 venv/module 来源的核验边界。

| 本轮受信比较 | 第一轮 | 第二轮 / restart |
| --- | --- | --- |
| Test PID 与 Default PID | 不同 | 不同 |
| `/proc/<test-pid>/environ` 的 exact Home | MATCH | MATCH |
| Test process-start identity | 取得并在运行/停止前复核 | 与第一轮不同，取得并复核 |
| install / profile / explicit route / registry | MATCH | 前后 MATCH |
| Test profile runtime load | 本轮 profile 初始化日志 + 本轮 process-owned state 的 served_profiles | 同类证据 + 独立 running snapshot |
| Discord adapter | 本轮 connected 日志 | 新进程 connected 日志 |
| connected → disconnected 日志窗口 | 约 83 秒 | 约 84 秒 |
| command sync | 本轮新增 `Skipping Discord slash command sync (policy=off)` | 同样 skip |
| 官方 planned stop / exit code | PASS / `0` | PASS / `0` |
| adapter disconnect / SessionDB close | 新增日志均观察到 | 新增日志均观察到 |
| 持久 gateway_state / Test PID | stopped / absent | stopped / absent |
| Default PID/start/Home | MATCH | MATCH |

每次停止前核对 exact PID、process-start identity 与 Test Home，调用 Hermes 官方 `gateway.status.write_planned_stop_marker(exact_test_pid)`，核对官方 marker 的 target PID/start stamp，再仅向 exact Test PID 发 SIGTERM。没有 pkill、killall、generic Gateway stop 或进程组信号。停止后 state 的 PID/start stamp 与本轮实际进程一致，日志确认 `all adapters disconnected`、`SessionDB close done`，进程退出码为 `0`。不把停止后 `session_store.status=ok` 单独当作 close 证明。

**观察器限制与纠正：** 首轮启动输出不含 Host INFO 日志，本地脚本因此初判缺少 sync skip/teardown evidence；补查预先记录 offset 后捕获的本轮 Host 日志，确认 skip/disconnect/close。另一次第二轮启动前的 launcher 环境采样发生在 exec 完成前，身份检查拒绝继续；随后 exact target 已不存在、持久 Test state 仍 stopped、capture 为空，没有新增 Gateway runtime 日志。该 pre-runtime launcher 拒绝没有被计为成功 Gateway 生命周期；修正本地采样及 entrypoint 调用后完成第二轮。

初始 polling 还可能读到上轮 stopped state 中保留的 connected/served_profiles，故初始 polling snapshot **不作为本轮 load/connection 或观察时长的证明**。上述结论使用本轮新增日志、停止后的本轮 process-owned state，以及第二轮独立取得的 running PID/start/Home snapshot；窗口按本轮真实 connected/disconnected 日志计算。原始脚本结果与纠正后的独立比较均保留，未删除不利或缺证记录。

真实 command-sync state 位于 `gateway/discord_command_sync_state.json`：本轮开始、第一轮后、第二轮后摘要一致；结合每轮新增 skip 日志，`NEW_COMMAND_SYNC_ATTEMPT = NO`。没有调用远端 command API。本轮 Host 输出及 launch/profile gateway/agent/error 增量日志未观察到 send、真实 inbound、cron execution、resume 或 obligation redelivery 指标；metadata 数量也未显示新会话。`SEND_EVIDENCE = NO_SEND_OBSERVED`，不具备 transport-level complete audit，不宣称 ABSOLUTE_ZERO_SEND_PROVEN。

## Phase D：SessionSource / 持久 session / Envelope candidate

当前源码仍由 Discord provider event 的 author/channel/guild/message identity 进入 admission 与 `_handle_message`，`BasePlatformAdapter.build_source` 构造 `SessionSource`，Host routing 写入 profile。`SessionSource.to_dict` / `SessionEntry.origin`、gateway_routing 与持久 session metadata 保存来源；profile-aware store/runner 显式把 resolved profile 传给 `build_session_key(..., profile=...)`。仅设置 `source.profile` 后裸调用 helper **不会自动选择 namespace**；本地 probe 按真实 caller 的显式参数规则核验。display/user name 变化不改变 key，不同 explicit profile 产生不同 namespace。

可信边界来自 authenticated provider admission、Host routing 与可信 store caller，**不是仅凭 Python 类型或字典字段**。`SessionSource.from_dict` 是反序列化工具，不能把模型/prompt/tool JSON 转成可信身份。message content、display name、model、prompt 和 tool payload 不能替代 provider ID、Host route 或 store-owned session ID；未来 binding 必须只从该受信路径取值，不接受 caller 自报字段。session key 未完整编码 Discord Server，不能用 key 代替独立 Server fence。

当前 Test launch Home 有历史 default namespace 的 gateway routing/session metadata 和历史 SessionDB rows；named `life-engine-hlv-test` 没有既有会话。restart 后历史 session ID 在本地只读比较中保留；origin 含 platform、user/chat、scope/guild、message 等字段。**没有制造 named Test profile session，也没有宣称 named-profile 实际 inbound/session 创建验证。** 持久数据只提供连续性 metadata，不携带新的执行授权。

`run_adapters.py::_handle_gateway_platform_event` 仍在授权检查后仅 `invoke_hook("gateway_platform_event", **event)`，没有把完整可信 `SessionSource` 与 session association 传给 hook。完整 source 的源码路径可发现，但该 hook 单独仍 `SESSION_SOURCE = HOST_GAP`。

下表是 Host binding projection 的 candidate，**不是改写现有 Core `HostIdentityEnvelope` contract**：

| candidate 字段 | 分类 | 可信来源 / 限制 |
| --- | --- | --- |
| host Home / install | TRUSTED | Host-owned Home、install_id；私有精确值不公开 |
| profile / agent | TRUSTED | 持久 marker、exact route、当前 lifecycle load evidence |
| process lifecycle | TRUSTED | 本轮 exact process 的 PID + `/proc` start identity + Home；PID alone 不足 |
| platform | TRUSTED | 当前 Discord adapter；session source 另从 provider path 取得 |
| owner | TRUSTED | registry/allowlist 与 future provider author 的独立 exact fence；本轮无 inbound |
| server / channel | TRUSTED | 固定 route/fixture，未来 provider source 必须再匹配；不从 session key 猜测 |
| session | DERIVED | store-owned session_id / profile namespace / origin candidate；本轮仅历史 metadata + source/local probe |
| 当前 named Test session | MISSING | 无既有记录，未制造 inbound |
| 单一 hook 的完整 source/envelope | MISSING | gateway_platform_event 缺完整 source/session association |
| adapter incarnation | DERIVED / MISSING | restart replacement 由新进程连接及旧进程退出分类；同进程 replacement 缺现成可信 incarnation projection |
| ACK / permit authority | NOT_APPLICABLE | 本阶段没有 delivery 或 permit consumption |

组合 candidate `HOST_IDENTITY_ENVELOPE = DISCOVERABLE`，不升级为 KNOWN_SAFE；完整 hook 为 HOST_GAP 可以与本阶段 PASS 并存。

## Authority model 与 inert fail-closed probe

**Persistent Identity + Process Lifecycle Identity + Life Engine Binding Generation = Current Binding Authority Candidate。**

Persistent Identity 包含 install/Home/profile/Owner/platform/Server/Channel；Process Lifecycle Identity 必须包含可信 birth/start identity，未来 binding 还需可信 adapter incarnation 和自己的 lifecycle generation。Hermes 没有原生 `authority_epoch` / `plugin_epoch`。Life Engine registry generation 是 Core-owned 只读输入；probe 的 `binding_generation` 与 adapter incarnation 是 **synthetic inert fixture**，不把它们称为已经在 Hermes 部署的 A3 epoch。Core generation、WriterEpoch、WorldRevision 保持独立，不由 Hermes process/session/restart 推导，也未调用 Core mutation。

受保护本地 probe 只使用内存字典和实际两轮 lifecycle facts。没有实例化 Core BindingAuthority、发 token、打开 Living Runtime、调用 Core 方法或网络。对比规则可复现为：

```python
def compare(reference, current):
    if not isinstance(reference, dict) or set(reference) != set(current):
        return "REJECT"
    if any(value is None or value == "" for value in reference.values()):
        return "REJECT"
    return "CURRENT" if reference == current else "STALE"

old_capability = "REJECT" if compare(old_reference, new_snapshot) != "CURRENT" else "ACCEPT"
```

reference 精确包含 Home、install、profile、Owner、platform、Server、Channel、registry generation、synthetic binding generation、实际 PID/start tuple、synthetic adapter incarnation。真实旧/新 start identity 不同；固定 session identity 不会修补 process 或 generation mismatch。第二轮运行中已做真实 facts comparison；停止后基于已捕获且 PID/start 匹配的独立 running snapshot 完成 profile helper 与完整本地 probe 复核。

| case | evidence / 结果 |
| --- | --- |
| 新 snapshot 的完整 inert reference（正对照） | CURRENT；仅 snapshot 比较，不是停止后继续授权 |
| 旧 process authority 对新 snapshot | STALE → REJECT |
| 旧 lifecycle capability reference | REJECT |
| synthetic PID reuse：保留新 PID + 旧 start | STALE → REJECT |
| Home/install/profile/Owner/platform/Server/Channel 单字段不一致 | 每项 STALE → REJECT |
| registry generation / synthetic binding generation 不一致 | STALE → REJECT；未改变真实 generation |
| synthetic adapter incarnation replacement | STALE → REJECT；不冒充同进程实际 reload |
| 任一必需字段缺失 | 每项 REJECT |
| 相同历史 session + 新 process | 旧 reference 仍 STALE，session 不赋新 authority |
| session-only reference | REJECT |

这是“旧权限可以由专用 binding projection 设计为 fail closed”的局部证明；不是真实 permit consumer、同步 reload revocation barrier 或执行管线的实现证明。future adapter 必须在 action 前重新取当前 lifecycle facts，以不完整、关闭、替换或不匹配为拒绝条件，不能让历史 snapshot 自行成为 authority。

## Adapter / plugin / recovery / execution 分类

旧进程退出意味着旧内存 Discord adapter instance 无法存活于新进程；新进程独立 connected，restart replacement 可分类。`build_source` 的 transport adapter weakref、`run_adapters.py::_install_reconnected_adapter` 与 teardown 路径是 future incarnation fence 的候选。没有导出或访问真实 adapter object ID，同进程 reconnect/replacement 的同步撤销仍须 future trusted binding barrier，不能靠 observer hook 补齐。

`PluginManager.discover_and_load(force=True)` 会先 unload，再重发现，并清理 ownership registrations；这是静态分类，未调用。plugin/config/profile reload 均未执行；本阶段 restart 结论不依赖额外 reload，故不需要追加 mutation authorization，也不宣称真实 reload PASS。

`gateway/run_startup.py::_claim_pending_obligations` / `_redeliver_claimed_obligations` 与普通 delivery ledger 仍可能 resend；重启前排除了未授权 pending work，新增日志未观察到本轮 claim/replay/redelivery。**Hermes generic delivery ledger != Living recovery**。未来 Living 专用路径必须 bypass / disable / isolate 普通 boot/reconnect/flood/base retry/reference fallback；本阶段只记录约束，没有实现或连接二者。

`DeliveryTransport.send` 持有 adapter reference，native 路径委托 `DiscordAdapter.send` → `channel.send()`；该 reference 的有效期应受 owning process + adapter incarnation + binding generation 限制。候选挂接位置继续 DISCOVERABLE。native one-time permit consumer = NOT IMPLEMENTED / NOT EXECUTED，未升级 KNOWN_SAFE；ACK validator 继续 HOST_GAP。完整 SessionSource hook、native authority/plugin epoch、native permit consumer、ACK 等 gap 不阻止当前有限 lifecycle/projection 结论。

## 本地证据与边界

原始 snapshots、process comparisons、增量日志、只读 DB counts、probe 输入/输出、观察器缺证与纠正记录、脚本和 SHA-256 manifest 保存在 expected owner 控制的 mode `0700` 本地 evidence directory，文件 mode `0600`；不提交。公开报告仅记录证据类型、比较结果与脱敏 PASS/FAIL，不含 credential、真实 Owner/Bot/Server/Channel ID、私有 Home path、PID、session ID、raw Discord response 或 Authorization header。保留 Host 日志/state/SQLite artifacts，未直接改写或清理。

没有事实要求修改冻结 Core/Attempt/permit/recovery/delivery/Session World Revision Fence，也没有要求 patch Hermes；`ARCHITECTURE_CHANGE_REQUIRED = NO`、`HOST_PATCH_REQUIRED = NO`。PASS 只表示真实隔离 restart 已验证，persistent identity 与 transient process identity 可区分，inert candidate 拒绝旧 lifecycle reference，session persistence 不自动继承 execution authority。Living execution、dry-run、delivery、recovery 安全和真实发送资格仍未取得。

## Mandatory Final Declaration

```text
SP-005A4-HLV2 = PASS
ENVIRONMENT_GATE = PASS
FIRST_GATEWAY_START = PASS
FIRST_PLANNED_STOP = PASS
SECOND_GATEWAY_START = PASS
FINAL_PLANNED_STOP = PASS
PERSISTENT_HOST_IDENTITY = PASS
PROCESS_LIFECYCLE_IDENTITY = PASS
TEST_AGENT_RUNTIME_LOAD = PASS
DISCORD_CONNECTION = PASS
COMMAND_SYNC_RUNTIME = OFF_CONFIRMED
NEW_COMMAND_SYNC_ATTEMPT = NO
HOST_IDENTITY_ENVELOPE = DISCOVERABLE
SESSION_SOURCE = HOST_GAP
SESSION_PERSISTENCE = CLASSIFIED
SESSION_AUTHORITY_SEPARATION = PASS
AUTHORITY_EPOCH_CANDIDATE = DISCOVERABLE
OLD_AUTHORITY_AFTER_RESTART = REJECT
OLD_CAPABILITY_AFTER_RESTART = REJECT
ADAPTER_LIFECYCLE = CLASSIFIED
PLUGIN_RELOAD_EXECUTED = NO
CONFIG_RELOAD_EXECUTED = NO
PROFILE_RELOAD_EXECUTED = NO
GENERIC_DELIVERY_RECOVERY = MAY_RESEND
LIVING_RECOVERY_CONNECTED = NO
EXECUTION_CONSUMER = DISCOVERABLE
PERMIT_CONSUMED = NO
SEND_EVIDENCE = NO_SEND_OBSERVED
REAL_INBOUND = NO
REAL_SEND = NO
LIVING_OPERATION = NO
ACK_VALIDATOR = HOST_GAP
DEFAULT_GATEWAY_MUTATED = NO
CONFIG_FINGERPRINT_MATCH = YES
FINAL_TEST_GATEWAY_STATE = STOPPED
EVIDENCE_LEVEL = REAL_HOST_LIFECYCLE_AUTHORITY_PASS
ARCHITECTURE_CHANGE_REQUIRED = NO
HOST_PATCH_REQUIRED = NO
H_LV3_STARTED = NO
H_LV4_STARTED = NO
```

STOP：完成独立 Draft PR 与 exact Head 的四矩阵 pull_request CI 后，等待 ChatGPT / 小雪独立 Draft Review；不得转 Ready、Auto Merge 或 Merge。
