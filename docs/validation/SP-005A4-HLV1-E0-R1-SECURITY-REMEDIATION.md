# SP-005A4-HLV1-E0-R1：Hermes Test Home Secret 与 Cron 静态审计

## 范围与结论

Roadmap Stage：Real Host Integration → SP-005A4-HLV1 → Environment Gate Remediation。固定 Base：`f52042188fa960b0d66b99644334454d08995420`。本轮仅处理 Dedicated Test Home 的 `.env` 权限并静态审计 cron。未启动、停止或重启任何 Gateway；未访问 Discord、Telegram、微信 API；未发送消息；未启动 HLV1 retry。

**SP-005A4-HLV1-E0-R1 = BLOCKED。** `.env` 权限修复已完成，cron 原始五文件的静态审计表明当前快照没有可调度 job 或待投递队列；但审计使用 SQLite `mode=ro` 查询执行账本时，在 Test Home 的 cron 目录意外生成两个 SQLite 辅助文件（`-shm` 与空的 `-wal`）。这违反本任务的 cron 零修改约束。保留现场，未删除、重命名或修复辅助文件；后续清理和复核需单独授权。`ARCHITECTURE_CHANGE_REQUIRED = NO`。HLV1、HLV1-E0 继续 BLOCKED；Test Gateway 不得启动。

## 隔离与 Secret 权限

在修改前重新核对：Test Home 与 Default Home 的解析路径不同，install ID 不同；Test `.env` 为 Test Home 内的普通文件、不是 symlink，真实路径不落在 Default Home；owner 为当前 Test 用户（UID 本地核对）。未输出任何 Home 路径、install ID、Owner ID 或凭据值。

| 项目 | 结果 |
| --- | --- |
| Test `.env` 修改前 mode | `0664` |
| Test `.env` 修改后 mode | `0600` |
| owner | VERIFIED LOCALLY |
| symlink | NO |
| Discord credential | PRESENT_REDACTED；内容未读取或输出 |
| credential rotation / validity / bot online | NO / NOT_TESTED / NOT_TESTED |
| Default Home / Default Gateway | PROTECTED / UNTOUCHED |

只对 Test `.env` 执行 `chmod 600`，前后以 `lstat` 和 `realpath` 核对文件身份、归属和 mode。没有修改文件内容。

## Cron 原始五文件 inventory

审计开始时 Test Home cron 目录有五个普通文件，均属于当前 Test 用户且不是 symlink。路径及文件名以编号替代；没有输出文件正文、消息内容、个人标识或 credential。

| 编号 | 类型 / mode | 启用项、schedule、action | 启动发现 / 注册 | 立即执行 / catch-up | 外部 transport 可达 | 分类 |
| --- | --- | --- | --- | --- | --- | --- |
| CRON-01 | 空锁文件 / `0664` | 无 job 定义 | NO / NO | NO / NO | NO | SAFE_LOCAL |
| CRON-02 | 空锁文件 / `0664` | 无 job 定义 | NO / NO | NO / NO | NO | SAFE_LOCAL |
| CRON-03 | SQLite 执行账本 / `0644` | `executions` 表 0 行；无待恢复 execution | ledger recovery / NO | NO / NO | NO | SAFE_LOCAL |
| CRON-04 | 心跳标记 / `0600` | 无 job 定义 | heartbeat / NO | NO / NO | NO | SAFE_LOCAL |
| CRON-05 | 成功心跳标记 / `0600` | 无 job 定义 | status marker / NO | NO / NO | NO | SAFE_LOCAL |

Test Home 的 cron job registry `jobs.json` 不存在；`deliveries.db`、`bot_chat_pending`、二级 profile 目录不存在；cron output 目录没有文件。配置中没有显式 cron provider，按当前 Hermes 默认值使用内置 ticker。上述状态只对本次静态快照成立，不能代替 Gateway 实际运行证据。

## Gateway startup / catch-up 路径

当前 Hermes 源码 checkout：`01382698fc32ec7740b6a204d9b7a6abeac74d33`。只读源码检查：

1. `gateway/run.py::_start_gateway_start_cron_and_housekeeping` 创建并启动 cron ticker 和 housekeeping 线程（约 5132–5201 行）。这是注册执行路径，不只是文件发现。
2. `cron/scheduler_provider.py::InProcessCronScheduler.start` 先恢复中断账本并写心跳，随后立即执行首次 `cron_tick`，之后才等待下一间隔（约 405–500 行）。因此 Gateway 启动 **可能立即执行** 已到期 job，不能笼统视为非发送。
3. `cron/jobs.py::load_jobs` 在 `jobs.json` 不存在时返回空列表（约 1294–1320 行）；当前 Test Home 正是此状态。`cron/scheduler_tick.py::_tick_admitted` 会扫描 due jobs，仅在有 due job 时提交执行（约 20–115 行）。
4. 内置 ticker 有 late / catch-up 行为；默认 `cron.catch_up_missed = true`（`hermes_cli/config_defaults.py`），所以未来一旦注册 job，启动时可能补跑，不能凭本轮结果永久豁免。外部 provider 的 misfire sweep 对内置 ticker 为 no-op（`cron/scheduler_provider.py::fire_overdue_jobs`），且当前配置没有外部 cron provider。
5. 首轮 tick 还会 drain deferred Bot Chat；Gateway housekeeping 首轮会 drain restart-safe delivery queue（`cron/scheduler_tick.py`、`gateway/run.py::_start_gateway_housekeeping`）。当前 Test Home 对应队列不存在，因此本快照无待发送 cron 结果。

原始五文件都不是 job definition，账本为空、job registry 与投递队列缺席，所以**静态 cron 专项判断：当前快照没有可由 Gateway 启动立即触发的 cron 外部发送**。这不证明整个 Gateway 启动安全，也不授权启动。E0 的 Test Agent、显式 Discord Test Channel/Target、Bot identity 等独立 Gate 仍未完成。

## 审计偏差与后续 Gate

原计划要求 cron 文件保持零修改。审计期间 SQLite 只读连接仍创建了 `executions.db-shm` 和零字节 `executions.db-wal`；原始五文件没有被显式编辑，但 cron 目录由五个普通文件变为七个。两个辅助文件现由 Test 用户持有。未尝试删除它们，因为本轮明确禁止对 cron 文件删除、重命名、移动或编辑。

因此：`CRON_STARTUP_GATE = PASS_STATIC_SNAPSHOT` 仅指原始五文件与当前无 job/queue 的静态结论；`R1 = BLOCKED`，`TEST_CRON_REMEDIATION_REQUIRED = YES`（先授权处理审计辅助文件并重新核验零修改约束）。`TEST_GATEWAY_START = BLOCKED`。即使将来 R1 通过，HLV1-E0 仍需完成其余环境 Gate，HLV1 Phase 0 仍须重新执行。

## 执行与保密声明

执行了 Git Base / clean worktree 检查、Test 与 Default Home 身份和 `.env` metadata 核验、仅针对 Test `.env` 的 `chmod 600`、Test cron metadata / SQLite 账本只读查询、Hermes 源码及 Test 配置静态检查。SQLite 查询产生辅助文件的偏差如上披露。没有读取 `.env` 内容；没有输出或提交 token、Owner ID、Channel ID、消息内容及 secret-containing cron 数据。Default Home 和 Gateway 均未操作。`NETWORK_SEND = NO`，`REAL_SEND = NO`。
