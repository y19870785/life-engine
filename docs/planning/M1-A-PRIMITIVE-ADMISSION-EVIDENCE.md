# M1-A — Primitive / Admission Probe 证据与缺口

状态：`E0_SYNTHETIC_PARTIAL / M1-A_PRIMITIVE_GATE_PENDING / EXECUTION_AUTHORITY_DENIED`。授权来源：用户在看到本地确定任务书 `M1-A-PRIMITIVE-ADMISSION-PROBE-TASK-DRAFT.md`、SHA-256 `8BFC43EBA6E87373791BC957D651B4B640ADDC5EFF55E9DFE6E0CAF9D68DA027` 与固定 Base `ca16d19e33bc274b0d3ac984c9761abb5a60e946` 后回复“可以”。任务书保留在本地授权记录，不作为本探针 PR 的文件范围。本文只记录该合同的隔离合成探针，不是产品 writer、完整 M1-A 原语 PASS 或任何 Host 许可。

## 环境与可复核原件

本地 E0 运行原件：[最终运行清单](evidence/M1-A-PROBE/run-20261011T140153Z.manifest.json) 与[原始文件归档](evidence/M1-A-PROBE/run-20261011T140153Z.zip)，归档 SHA-256 `f621b6a2e21620c9464fa9988cdc6636e133060109527651c8a109f65c1dbd7c`。平台为 Windows `10.0.26200`、Python `3.12.10`、SQLite `3.49.1`，默认 Python sqlite3 VFS；具名机器、底层文件系统/磁盘型号与真实 VFS 名称未取得，因此不作设备级保证。探针用新建的系统临时目录，合成 `domain=synthetic, soul=S`，不导入产品 Runtime，不接触 Host Home 或真实 `soul_id`。每个连接分别设 `WAL + synchronous=FULL` 或 `DELETE + synchronous=EXTRA`；不使用网络文件系统。run manifest 给出版本、程序、平台、退出码及每个保全文件的 SHA-256；归档中各测试子目录的 manifest 给出操作观察、原始 SQLite DB、进程结果文件和损坏 fixture。进程故障的 DB/WAL/journal 文件集在**首次恢复读回之前**复制到 `crash-raw-before-reopen`，全部原件在测试清理临时目录之前保全；打包时逐文件比对归档解出的 bytes 与清单 SHA-256。先前调整中的原件也保留为同目录中的归档和清单，但不作为以下最终断言依据。

本地 `unittest` 20 项通过（1 项 Windows symlink 创建权限不足而跳过）；`P01/P02` 在每种 journal 配置分别进行了 10 次独立双进程 CREATE 和 10 次 FORK 竞争，另有各 3 次 FORK 对 source ADVANCE、RETIRE 的同 revision 竞争。worker 先准备 Record、记录共同预期 root，再同时放行 CAS；每次均单赢家、败者 `CAS_FAIL`。`P03` 四个进程退出 hook 在两种配置下各重复三次。单个 worker 总时限约 10 秒；这仍只是 E0 进程故障，`before_commit` 是 **COMMIT 前退出**，不是原子提交期间断电。`BEGIN IMMEDIATE BUSY` 在两种配置用真实连接锁竞争触发；`COMMIT BUSY` 在 `DELETE` 配置以在途 reader 触发并确认事务仍未决。WAL 的 `COMMIT BUSY` 未证明。`SQLITE_INTERRUPT` 用真实 progress handler 触发；`IOERR`/测试 VFS 注入未执行，标 `NOT_DEMONSTRATED`，不混同真实 SQLite 返回与 mock。

最终 run manifest 逐文件记录运行前后相同的探针源码 SHA-256、退出码 0、`timed_out=false`、`worker_tree_stopped=true` 与无存活登记 worker，并明确 `working_tree_clean=false`。其中 `worktree_head_before_commit=e439bc043d712b76c5443d4bec598bd36a5a1156` 是本轮采证前的待修复提交，不能误读为本轮源码已进入该提交。归档为 510 个校验通过的条目；独立 `worker-ledger.jsonl` 记录 240 次子进程启动意图及对应登记，并以 run ID、PID、创建时间和可执行文件核对存活进程。取证器拒绝 ledger 缺失或启动登记未完成，先用只读进程身份查询确认已登记 worker 均不存活，再允许复制超时残留；在 Windows 不再使用 `os.kill(pid, 0)`。取证器在建立目录前逐级拒绝证据根及祖先中的 symlink/junction，再规范化路径并限制目的地为本仓库约定目录；打包器共用此检查并拒绝内部逃逸。Windows 临时目录的 8.3 短名称与长名称可归一为同一路径，不能再仅凭两种拼写不同判定逃逸。正常测试的数据库、故障前后快照及进程结果均在独占临时 fixture 清理前复制。

新增负例在 worker 仍存活时调用同一收敛检查：返回未收敛、不产生 `timeout-raw` 副本，并在检查前后确认 worker 仍运行。另对 ledger 缺失、只写启动意图但未完成登记分别断言拒绝复制。它只验证本探针取证器的拒绝路径，不代表真实旧进程已被围栏。

另以 2 秒上限有意触发取证器超时：[失败清单](evidence/M1-A-PROBE/run-20261011T094013Z.manifest.json)与[失败运行归档](evidence/M1-A-PROBE/run-20261011T094013Z.zip)，归档 SHA-256 `4115edd14e8778190f3daff9d7b4aca0559952daa0624d7ec949d4f720afa9db`。这是本轮收敛顺序修复**之前**的历史负例；清单记录 `timed_out=true`、`worker_tree_stopped=false`、`exit_code=1`，因此该运行**不作为静止原件或正面原语证据**，不能证明当前收敛实现。它没有复制未确认收敛的临时 fixture，也没有按成功清理。测试后另查系统进程列表未见探针 worker，但不倒填当时的收敛证明。

仓库全量回归在 Windows 本地 Python 3.12 运行 `610 tests / OK (skipped=2)`，用时 652.289 秒；其中本轮新增 symlink 负例因当前 Windows 账号缺创建权限而跳过，另一项为仓库既有跳过。最终采证的 20 项定向测试同样 `OK (skipped=1)`。默认 Python 3.10 的试跑报出既有仓库使用 `hashlib.file_digest` 等 3.11+ API 的版本不兼容，且试跑期间 worker 接口还在修订，故该次失败不计最终验证；本机登记的 3.11 临时解释器不可启动。正式 3.11 与 Linux 结果留待精确 Head 的 CI，不能从本地 3.12 推断。

旧 Head `e439bc043d712b76c5443d4bec598bd36a5a1156` 的 PR CI #38132715723 两次 attempt 均是 Ubuntu 3.11/3.12 成功、Windows 3.11/3.12 失败。Windows 失败发生在探针 `setUp`：临时路径的 `RUNNER~1` 短名称与 `resolve()` 得到的 `runneradmin` 长名称被按字符串不相等拒绝，20 项探针测试未进入主体。本轮仅将路径检查改为先逐级拒绝 symlink/junction、再规范化后检查专属临时根与目标；本机没有可用的 8.3 短名称样本，修复效果仍待新 Head 的四矩阵 CI 验证，旧 attempt 不能计为本轮通过。

## P01–P07 原语裁定

| 探针 | 本轮实际观察 | 仍缺的证据 / 阻断 |
| --- | --- | --- |
| P01 Genesis/ENROLL | `expected=ABSENT` 双进程单赢家；ENROLL 独立 `ENROLL_BASELINE/NONE` parent；旧历史仅 `UNKNOWN`。 | 未验证产品 decision 签发、真实历史或物理断电；不得 active enrollment。 |
| P02 Fork 多条件 CAS | 同一 root 行比较 revision、source Record、target ABSENT、retirement；损坏 root 或缺 source Record 时拒绝 CAS；逐项负例 root 不变；十轮双进程 target 单赢家；与 source ADVANCE、RETIRE 各三轮同 revision 竞速均单赢家。 | 真实 Registry target binding、产品 writer 与断电未验证；不得产品 FORK。 |
| P03 Record 顺序/GC | Record 写中退出回滚；已准备未锚定 Record 留存；COMMIT 前退出 root 未出现；锚后未激活仍可读。探针没有 GC。 | 未证明 Record/root 断电持久性、真实数据候选/parent 闭包与运维清理围栏。 |
| P04 未决事务/重放 | 真实 `BEGIN BUSY`、适用配置真实 `COMMIT BUSY`、真实 `INTERRUPT`；DELETE 中业务 `COMMIT BUSY` 期间共享 gate 未释放，排他 transition 不能越过，收敛后重读 root 再 CAS；`ack_lost` hook 在 COMMIT 后、回应前退出，独立新进程按同 ID 核对 Record/payload/root，三轮均只见一个锚；异 payload 拒绝。 | `IOERR`/WAL `COMMIT BUSY`、COMMIT 临界区不可知结果及产品尾步骤未证明。 |
| P05 旧入口围栏 | 跨进程 SQLite SHARED/EXCLUSIVE 合成 gate 中，业务持锁后重读 root 并提交业务事务；transition 被阻塞，放行或杀死 owner 后才获排他锁、重读 root 并作退休 CAS。另证实同一 OS 身份可绕开 gate 直接修改合成 root DB，属**准入缺口**。 | 真旧 binary/句柄/CLI、媒体、Host permit/delivery、产品入口接 gate、故障后真实 fencing 均未验证；所有入口默认拒绝。 |
| P06 备份域/nonrollback | 业务 fixture 恢复不改变 continuity DB；同一身份用旧 DB 文件覆盖可令 root 版本回退，说明合成目录不构成 nonrollback 域。 | 真实 Windows/Linux authority 身份、ACL、备份清单、恢复演练及审计原件缺失；E3 `NOT_PROVEN`。 |
| P07 Fork target/四轴 | target 独立 Instance/Data 引用，锚已提交但 Registry 未激活为 `COMMITTED / FORK / QUARANTINED(ACTIVATION_PENDING) / DENIED`；retired 后 persistence 仍为 `COMMITTED`；Registry 第三值、parent 缺失、Record 损坏、未知版本隔离。ADVANCE 后删除 Genesis parent 时，完整 parent 闭包检查使 read verdict 隔离、后续 FORK CAS 拒绝；损坏前后 DB 分别保全。 | 合成 read model 不等于 M1-D 产品 verdict，未完成全矩阵 failure injection。 |

## 入口准入盘点

本轮只实际测量合成 `gate_worker.py` 的共享/排他锁与同身份直写绕过。对真实入口逐一默认 `DENIED / UNTESTED`：产品 World/Character/Memory/Story/Lore/Living 写路径，部署与管理 CLI，旧 binary 与持久句柄，直接 SQLite/文件写入，Host permit、delivery 与 ACK，以及备份/恢复入口。探针未改接这些入口，也没有证据说明它们已经共享同一 gate。合成 gate 能阻止**自愿持锁的业务进程**与 transition 重叠；同身份绕过仍说明当前没有完整的强制围栏。此处的 `P05` 观察不能提升为产品 admission。

## 故障等级与平台

| 维度 | Windows 本地 | Linux / 其他 | 最强结论 |
| --- | --- | --- | --- |
| E0 逻辑与进程 | 上述 SQLite 合成观察及原始文件；部分原语/反例已触达 | 当前无带原始 DB 的独立 Linux 证据；后续 CI 测试结果单列 | `E0_SYNTHETIC_PARTIAL` |
| E1 OS/VM crash | 未执行 | 未执行 | `PENDING`；普通进程退出不能代替 |
| E2 物理断电/flush | 未执行 | 未执行 | `NOT_PROVEN`；需独立目标硬件、电源切断方法、保护方案、重复 raw file/日志与恢复读回授权 |
| E3 管理域不回滚 | 同身份覆盖旧 DB 成功，是负例 | 真实部署未执行 | `NOT_PROVEN`；需管理主体、ACL、完整 DB/WAL/journal/目录及备份域证明 |

## C/G/FK 逐 ID 责任台账

下表的“部分”只指该行关联的 **M1-A 合成原语**已有 E0 观察，**不是**该协议场景已执行。原 [故障矩阵](M1-P0-CRASH-RECOVERY-MATRIX.md) 的 34 行全部仍为 `PROTOCOL_SCENARIO`；M1-C 的 writer failure injection、M1-D 的完整 transition/verdict 均 `NOT_EXECUTED`。所有行缺 E1/E2/E3 与真实 admission，统一阻断 active Soul 写入、自动恢复和执行许可。

| ID | M1-A 责任 → 探针 | 本轮 E0 | 未执行部分 / 阻断动作 |
| --- | --- | --- | --- |
| C01 | 锁前准入 → P05 | 缺口 | 真旧进程/锁释放未执行；DENIED |
| C02 | 锁后重检 → P05 | 部分 | 合成 gate 跨进程锁/owner 死亡及持锁 root 重检已执行；产品重检未执行；DENIED |
| C03 | 重检后准备 → P05 | 部分 | 合成业务事务持共享锁、COMMIT 未决阻挡排他切换已执行；产品事务 TOCTOU 未执行；DENIED |
| C04 | Record 写中 → P03 | 部分 | 仅进程退出，断电与产品候选未执行；DENIED |
| C05 | Record 已存、锚旧 → P03 | 部分 | 产品重试/断电未执行；DENIED |
| C06 | CAS outcome unknown → P02/P04 | 部分 | COMMIT 临界区、损坏旧/新三分支未执行；DENIED |
| C07 | 锚新、ACK 丢失 → P04/P07 | 部分 | 产品幂等激活未执行；DENIED |
| C08 | 锚新、激活未完 → P03/P07 | 部分 | 合成 Registry pending/ready/第三值已分类；真实切换未执行；DENIED |
| C09 | Data 偷跑 → P05/P07 | 缺口 | 真实 Registry 绕过未执行；DENIED |
| C10 | 锚指缺 Record → P03/P07 | 部分 | 合成 root 所指 Record 缺失时仍判锚已提交、证据冲突隔离；产品隔离未执行；DENIED |
| C11 | 锚指损坏 Record → P03/P07 | 部分 | 合成 hash 损坏；产品隔离未执行；DENIED |
| C12 | parent 错误 → P03/P07 | 部分 | 合成 parent 缺失/ADVANCE 断链时隔离且拒绝后继 CAS；异 parent 决策未执行；DENIED |
| C13 | 未引用高序候选 → P03 | 缺口 | 高序拒绝/parent 闭包未执行；DENIED |
| C14 | 旧 Record 对当前锚 → P02/P05 | 部分 | 旧进程 stale writer 未执行；DENIED |
| C15 | 同 ID 重放/冲突 → P04 | 部分 | 合成同 ID 冲突；产品尾步骤未执行；DENIED |
| C16 | 双 writer → P01/P02 | 部分 | 合成双进程单赢家；产品 writer 未执行；DENIED |
| C17 | stale writer → P02/P05 | 部分 | revision/source 单独拒绝；真旧句柄未执行；DENIED |
| C18 | 旧业务备份 → P06 | 部分 | 合成业务 restore；部署隔离未执行；DENIED |
| C19 | 退休后旧备份 → P02/P06 | 部分 | 合成退休 fence；真旧备份/全入口未执行；DENIED |
| C20 | 已完成、回应前死亡 → P04/P07 | 部分 | 合成 COMMIT 后失回应、新进程按 ID 重查已执行；产品尾步骤未执行；DENIED |
| G01 | Genesis 准备前 → P01/P03 | 缺口 | 精确故障点未执行；DENIED |
| G02 | Genesis Record 后、锚前 → P01/P03 | 部分 | 合成 prepared 存留；断电未执行；DENIED |
| G03 | Genesis CAS 不确定 → P01/P04 | 部分 | COMMIT 临界区未执行；DENIED |
| G04 | Genesis 锚后激活前 → P03/P07 | 部分 | 合成 anchor pending；产品激活未执行；DENIED |
| G05 | Genesis 激活后失 ACK → P04/P07 | 缺口 | 精确尾步骤未执行；DENIED |
| G06 | 双 CREATE → P01 | 部分 | 双进程单赢家；断电/真实 decision 未执行；DENIED |
| FK01 | Fork Record 前 → P02/P03 | 缺口 | 精确故障点未执行；DENIED |
| FK02 | Fork Record 后、锚前 → P02/P03 | 缺口 | 精确 Fork prepared 注入未执行；DENIED |
| FK03 | source 前进 → P02 | 部分 | 合成双进程 FORK/ADVANCE 同 revision 竞速已执行；产品 writer 未执行；DENIED |
| FK04 | Fork CAS 不确定 → P02/P04 | 部分 | COMMIT 临界区未执行；DENIED |
| FK05 | target 锚后 source 不变 → P02/P07 | 部分 | 合成 source bytes 保持；真实 Registry 未执行；DENIED |
| FK06 | 同 Tf 重试 → P02/P04 | 缺口 | Fork ID 重放未执行；DENIED |
| FK07 | 同 target 并发 → P02 | 部分 | 双进程单赢家；断电未执行；DENIED |
| FK08 | Fork/退休竞争 → P02 | 部分 | 合成双进程 FORK/RETIRE 同 revision 竞速已执行；产品 writer 未执行；DENIED |

## 出口与下一门禁

目前只能提交 `E0_SYNTHETIC_PARTIAL` 与反例证据，不能裁定 `M1-A_PRIMITIVE_PASS`。`P05` 直接写绕过、`P06` 同身份旧文件覆盖说明：如果目标部署不给 authority 服务独占且不可整体回滚的管理域，本候选在该威胁模型下须 `NO_SAFE_PROTOCOL_WITH_CURRENT_PRIMITIVES / STOP`；本轮没有足够真实部署证据判断该条件能否满足，现状态为 `M1-A_PRIMITIVE_GATE_PENDING`。独立审核即使认可原始证据，也只能给 `PROBE_EVIDENCE_REVIEW_COMPLETE`；不能开启 Schema/migration、SoulRoot writer、Host 或下一阶段。
