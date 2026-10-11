# M1-A — Continuity Storage / Admission 设计决定

状态：`DESIGN_PROPOSAL / NOT_PROVEN / NO_IMPLEMENTATION_AUTHORIZATION`。设计 Base：`c26d6c5c4a721bedf7dde6c6575ee23277574dd6`。授权合同：`M1-A-DESIGN-V1`，任务书 SHA-256 `85C6F82A40D389509A83B278BFAB535C72D55D47730C0451553EEEB4930E8704`，用户在看到确切版本与 Base 后回复“好”。本文只选择候选与验证路径，不声称任何 M1-A 原语、场景或真实 Host 已 PASS。

依据：[SP-006S0](../architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md)、[M1-P0 协议](../architecture/M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md)、[实施门禁](M1-P0-IMPLEMENTATION-GATE.md)、[故障矩阵](M1-P0-CRASH-RECOVERY-MATRIX.md)。冻结不变量：`Soul != Host/Model/World`，`Recovery != Authorization`，`COPY != CONTINUATION`，`UNKNOWN = FAIL_CLOSED`；唯一性只限一个受信 management authority domain。无共同协调者的真实跨机器或 Host 迁移为 `UNKNOWN`。

## 1. 选择与边界

**首选设计候选**：在业务备份域外由唯一受信 authority 服务独占写入的 SQLite continuity store。一个数据库内含 immutable Record 与唯一 SoulRoot；Record 用先行提交的事务保存并读回，随后另一个事务以 `BEGIN IMMEDIATE` 读取、比较并更新**同一 SoulRoot 行**。同一行内的 `root_revision`、source head、target `ABSENT` 与 Soul retirement fence 一起受检；仅符合受信 decision 才写入新完整 root 值。`COMMIT` 并在新连接读回精确 root/Record 后才可报告结果；ACK 丢失以同一 `transition_id` 查证，不重基。此为待验证实现蓝图，SQLite 事务不能单独提供外部备份不回滚、跨机器共识或旧进程准入。

| 候选 | 得失 | 决定 |
| --- | --- | --- |
| 独立 continuity SQLite DB + 独占 authority 服务 | 本地事务可把多条件比较和 root 更新置于同一原子单位；Record 与 root 有可查询引用；仍依赖平台同步、权限、备份隔离和 admission | 首选，全部关键保证 `PENDING / NOT_PROVEN` |
| 独立不可变文件 + manifest/锁 | 文件替换、目录同步、锁次序及跨文件引用在 Windows/Linux 的 crash 语义更难证明；锁不能使旧 binary 服从 fence | 暂不选，除非原语实验推翻首选 |
| 远端协调或硬件不可回滚介质 | 可扩大故障/信任边界，但引入独立服务与网络协议；不在本阶段授权 | 不选；真实跨机器仍 `UNKNOWN` |

**物理边界**：`D-business` 是 World/Memory/Story/Living 数据与 DataGeneration，可按既有方案备份恢复；`D-registry` 是活动 Instance→DataGeneration 指针，激活必须核对 continuity store；`D-continuity-record` 与 `D-continuity-anchor` 逻辑分离但首选放在同一受保护 SQLite 文件，绝不随业务备份、schema rollback、代码 rollback 或旧 `registry.json` 替换而回退。Memory/Bridge control 继续各自的非回滚域，不合并为 Soul 账本。数据库、WAL/rollback-journal、目录、备份和恢复工具必须整体在受信 authority 控制下；仅把文件放在另一目录不足以阻止有同权限写入者回滚。旧备份只能恢复业务候选，不能恢复 root、retirement fence 或已引用 Record。

本候选**明确选择受信管理域排除整体回滚的部署假设**，不另造一个未经设计的“外部水位”：只有 authority 服务主体可写 continuity store，其完整文件集、备份策略、快照/恢复权限和管理变更记录由业务备份域之外的管理方控制；业务 restore、schema/code rollback、普通运行身份和旧 binary 均无修改/覆盖权。启动与每次恢复须核对该管理域的部署证明、文件来源和权限；来源不明、曾把 continuity 文件纳入可回退快照、证明中断或文件缺损时一律 `UNKNOWN / DENIED / STOP`，不凭数据库内容自证未回滚，也不从旧备份自动修复。若同一管理员/磁盘快照可整体回滚管理域，此信任假设不成立，软件无法在该威胁模型下证明 nonrollback，结果为 `NO_SAFE_PROTOCOL_WITH_CURRENT_PRIMITIVES / STOP`。实施验证须提供 Windows/Linux 真实部署权限与备份清单、恢复演练和管理审计原件；目前均 `PENDING / NOT_PROVEN`。

**平台假设与故障模型**：先限定本地受信磁盘、单一 authority 进程、SQLite 受支持的 VFS/文件系统，不使用共享网络文件系统承载 WAL。候选配置优先评估 `WAL + synchronous=FULL`，也须比较 rollback journal `EXTRA`、目录项持久性与 Windows/Linux VFS 差异。进程 crash、OS crash、突然断电、失 ACK、并发、旧备份回滚分别验证；不得把 `COMMIT` 返回、`fsync` 调用或模拟 kill 当成断电证明。文件系统/硬件可能不诚实兑现 flush，电源故障保证只能限于实测平台和信任假设。SQLite 官方的 [atomic commit](https://www.sqlite.org/atomiccommit.html)、[synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous) 与 [WAL](https://www.sqlite.org/wal.html) 文档是候选依据，不是本项目实证。

## 2. 最小实体及不变量

| 实体 | 最小字段与约束 |
| --- | --- |
| SoulRoot | `(authority_domain, soul_id)` 唯一；`protocol_version, root_revision, retirement_fence, active_branch, branch_heads`。`branch_heads` 每项为 `(branch_id, sequence, soul_generation, record_hash, instance_id, activation_ref)`；同一持久行 CAS，revision 单调。retirement fence 保留 retirement `transition_id`/Record hash 且不得清除。 |
| Record | 内容寻址 `record_hash`；canonical bytes 绑定 protocol/domain/SoulId/InstanceId/branch、operation、`transition_id`、受信 decision 摘要、expected root revision/source/target、parent kind/hash/sequence、Soul generation、目标 DataGeneration 精确引用/摘要、控制水位与 timeline/relationship 摘要。存储后不可覆写；引用存在时不得 GC。 |
| Instance binding | 独立 `(instance_id, soul_id, branch_id, registry_entry_id)`；同一 branch 的当前 Record 与目标 DataGeneration 相互核对。FORK 必须新 target Instance/registry entry，source binding 保持逐字节不变。 |
| DataGeneration | 候选与 active 区分；包含可复核的内容摘要、Schema 版本、Scope/控制水位；编号不是 Soul generation。 |
| Transition decision | `(transition_id, domain, soul, operation, expected_root, expected_source_head, target_absent, target_instance/data, payload_hash, issuer)` 唯一且持久可查。同 ID 异 payload 是冲突，不能生成第二 generation。 |

`CREATE` 的专用 `GENESIS/NONE` parent 与 `SoulRoot=ABSENT` 建立 B0/**G0**；`ENROLL` 是另一个 `ENROLL_BASELINE/NONE` parent，历史 verdict 永远不能由 enrollment 倒推为已证明。无受信 enrollment decision 的旧 `soul_id`/旧库仅只读 `UNKNOWN`；未知 protocol version 也 `UNKNOWN / QUARANTINED`。迁移只在非活动业务副本准备，不能修改现有真源或将 schema 升级等同 Soul continuation。具体 Schema 版本号和兼容窗口待原语、旧入口证据后独立授权确定；本设计不修改 `DATA_SCHEMA=8`。

Record 必须先于引用它的 root CAS **durable**；CAS 前校验 Record hash、parent、decision 与候选数据，CAS 后读回并按引用集合保护 Record。**M1 首轮完全禁用 continuity Record GC**，包含未引用的 prepared/orphan Record；不得通过业务备份清理、手工维护或 VACUUM 变相删除。保留集合至少为所有 root branch head、retirement Record、它们的完整 parent 闭包，以及未决 decision 的 prepared Record。将来若单独设计 GC，删除与 CAS 的引用校验/更新必须在同一 SQLite 写事务序列化，候选已删除则 CAS 拒绝，不得悬空引用；该扩展另行审核授权。root 所指 Record 缺失或损坏时不能由 Registry、备份或相似内容重建 lineage。SQLite 事务使引用检查较易表达，但 Record 先提交与 root 后提交的顺序及断电存活仍须证明。

## 3. Admission 与旧进程围栏

当前源码的 `durable.locked` 是本地互斥；`durable.write`/`registry` 在 `runtime/life_engine/durable.py` 处理 `registry.json`，`restore`、`upgrade`、`rollback_code`、`rollback_schema`、`rollback_living`、`create_install` 与 `run` 有不同切换路径。`deploy_cli.py` 暴露管理命令；`world_sqlite_repository.py`、`memory_sqlite_repository.py`、`story_sqlite_repository.py`、`lore_sqlite_repository.py`、`living_runtime.py` 分别触及业务读写；`living_host_binding.py` 的 simulated/real permit consume、`RealDeliveryBindingFactory.one_shot` 触及发送门。`durable.run` 还可能产生观测、备份标记与媒体发布。此清单是代码入口初查，实施前须穷尽其他 CLI、插件/Host 包装和直接文件/SQLite 写者；未覆盖入口默认拒绝，不能声称封闭。

目标 admission：受信服务独占 continuation DB 写权限并提供版本化、按当前 SoulRoot/branch/data binding 检查的访问接口。**设计选择同一受信 authority 的共享/排他 epoch gate**：每个新版本业务写事务由受信 broker 取得共享 gate 后重读 root/branch/data/retirement 和原业务权限，持有 gate 直至业务 `COMMIT`/`ROLLBACK` 确定结束；gate 丢失或提交状态不明时停写并隔离，不能继续提交。continuity transition 取得排他 gate，等待或拒绝所有在途共享持有者，拿到后才锁内重检、prepare/CAS/registry activate，直到切换结果确认才释放；相同 gate 的持久 epoch 在 root revision 中体现，重启时先收敛旧进程与未决事务，不继承内存锁结论。现有 `durable.locked('management')` 只能作本地锁顺序参考；同一受信服务必须使业务库写入口不可绕过 broker，且实际跨进程 gate 与失效语义需 M1-A 证明。读/启动检查或旧 permit 不构成持续授权。**Host permit 与所有 delivery 本阶段持续关闭**，直至后续独立设计并证明检查到不可撤回外部发送之间的围栏；一次 root 读取绝不授权发送。

| 入口（现有位置） | 副作用 | 目标守卫 | 主要绕过路径 / 待验证场景 |
| --- | --- | --- | --- |
| `durable.py` 的 create/upgrade/restore/rollback/run 与 `deploy_cli.py` | Registry、DataGeneration、安装/备份状态 | 排他 gate、root/version/retirement 重检，候选先准备 | 旧 CLI 直接写 `registry.json`；C09/C18/C19 |
| `world_sqlite_repository.py`、`memory_sqlite_repository.py` | World/Memory 事务写入 | broker 共享 gate 持至事务终结，保留原业务/控制门 | 旧 Python/SQLite 直连；C16/C17/C18 |
| `story_sqlite_repository.py`、`lore_sqlite_repository.py`、`living_runtime.py` | Story/Lore/Living 事务写入 | 同一共享 gate + 原会话/权限检查 | 旧 worker 直接事务、在途旧句柄；C16/C17/C19 |
| `living_host_binding.py` permit consume 与 real delivery factory | permit 消费、外部发送 | 当前设计一律 `DENIED`，不创建真实发送资格 | 旧 Host 进程/缓存 permit；C19，真实 Host 另立门禁 |
| `durable.run` 的媒体/观测和未知插件/Host 包装 | 文件发布或其他副作用 | 逐项纳入 broker，否则暂停/拒绝 | 直接文件系统写与未发现入口；入口审计及 C09/C19 |

此表是审计工作清单，不表明现有代码已受守卫；最终须以文件/DB/进程/Host 的全入口枚举与旧版本绕过试验封闭。

**部署 barrier**：先保持所有业务/Host 入口暂停，停止旧服务和 CLI/worker，收敛所有持有旧 SQLite/文件句柄或旧 permit 的进程，审计进程/句柄及可写 ACL，撤销旧执行身份的写权限；新受信服务以不同受限主体独占受保护域，完成版本准入与 fresh-process 重检后才逐入口解除暂停。已运行旧进程不能靠新代码里的检查被围栏；同 OS 身份仍可直接写业务库或调用 Host 的旧 binary 时，ACL 也不能区分新旧版本。必须证明旧句柄已无可写能力，或把所有副作用置于旧身份不可绕过的 broker/权限域；证不成就保持 `UNKNOWN / DENIED / STOP`，不做 active enrollment。旧代码 rollback 不得重新给旧 binary 写权。此设计依赖未来改造与部署证据，当前仓库**没有**可信全入口 barrier。

## 4. 操作、恢复及线性化

统一顺序：受信 decision → 暂停相关副作用并获 authority 排他 gate/management lock → **锁内**重读 root、branch、Registry、控制水位及版本 → 准备独立 DataGeneration → durable Record → 单次 SoulRoot CAS → 核验 root/Record/data → 仅对精确 target Instance 幂等激活 Registry → 重新判定运行资格。任何 CAS 条件失败不得自动更新 expected 值；失 ACK 按原 `transition_id` 和完整 payload 查询。`D-registry` 可能仍旧时，完整已提交链可给 `COMMITTED` 和 `CONTINUATION`/`FORK`，但 `QUARANTINED(ACTIVATION_PENDING)`、`DENIED`；证据不全为 `UNKNOWN / QUARANTINED(EVIDENCE_CONFLICT) / DENIED`。

SQLite 错误必须分流：**条件不匹配**是已确定的 `CAS_FAIL`；`BEGIN IMMEDIATE` 的 `BUSY` 是未取得写事务，等待有界重取锁并重新核验，不能宣布提交；`COMMIT BUSY` 可能保留活动事务，须在该连接上有界完成/回滚并确认连接关闭与受信 writer 排空，随后才以**新连接**读 root/Record/decision 判定；`IOERR`、`INTERRUPT`、进程死亡、断电或无法证明事务已收敛均为 `INDETERMINATE / QUARANTINED / DENIED`。不得在旧事务可能稍后提交时依据旧 root 重试、激活或开放共享 gate。超时仍未确定则停在隔离并交人工治理；不能用自动修复篡改 root。

| 操作 | 单次 CAS 的预期与效果 | 激活/竞争 |
| --- | --- | --- |
| CREATE | `SoulRoot=ABSENT` → Genesis B0/G0；唯一 winner | 败者 `CAS_FAIL`；ACK 丢失原 ID 查 root，不换 SoulId |
| ENROLL | `SoulRoot=ABSENT` → baseline B0/G0，保留旧历史 `UNKNOWN` | 无管理决议或已有 root 不准入 |
| 普通 successor | root revision、source branch head、未退休同时匹配 → 指向下一代 Record | 目标候选先于 CAS；旧 writer 不得改基准重试 |
| FORK | 同一 root CAS 检查 root revision、source head、target `ABSENT`、未退休 → **只增加** target Bx/G0 | source head、active branch、source Registry/Data 与执行权不变；target 独立激活 |
| SOUL_RETIREMENT | root revision、未退休与受信 decision 匹配 → 设置全 Soul 不可清除 retirement fence | 所有 branch、旧备份/permit/Host state 均拒绝；`BRANCH_RETIREMENT` 范围外 |

每次 fresh-process recovery 分四轴输出：`Persistence Fact = ABSENT/PREPARED/COMMITTED/INDETERMINATE`（另记 RETIRED lifecycle），`Identity Verdict = CONTINUATION/FORK/MISMATCH/UNKNOWN`，`Operational State = READY/QUARANTINED(reason)/RETIRED`，`Execution Authority = DENIED/由现有独立合同另授`。CAS 已提交不自动给 verdict 或权限；恢复仅完成已证明同一 transition 的尾步骤，不能签新 decision。FORK/RETIRE 竞争以同一 root revision 序列化，失败者停止；退役优先的旧数据不能复活。

## 5. 场景归属与待取证据

矩阵全部编号仍是 `PROTOCOL_SCENARIO`，下表只给未来验证归属；各行当前均 `PENDING / NOT_PROVEN`，不计 PASS。每个实验须保留 fixture、平台/FS/SQLite/VFS 配置、注入点、候选/Record/root/Registry 原始 bytes/hash、旧/新进程 ID、decision/T1、fresh-process 重复 recovery 的四轴结果及冲突/拒绝日志。M1-A 先证明存储与 admission 原语；M1-C 验证 writer 的 prepare/CAS/activate 与重复恢复；M1-D 验证 transition/判定语义；有任何必需原语不成立，停止后续动作。

| 场景 | M1-A 原语/admission 证据 | M1-C writer 证据 | M1-D transition 证据与阻断 |
| --- | --- | --- | --- |
| C01–C03 锁前/锁后/准备前 crash | 管理 barrier、锁释放/重检 | 同 ID 重新验证，无预提交副作用 | 四轴保持旧头；阻断新授权 |
| C04–C05 Record 写中/已 durable、锚旧 | 数据/Record 同步、原子可读、孤儿保护 | prepare 后不激活，原 ID 重试 | 候选 `UNKNOWN`；阻断候选运行 |
| C06–C08 CAS outcome unknown、失 ACK、激活未完 | 单行 CAS/断电/读回、Record 稳定寻址 | 精确 ID 查证与幂等激活 | 完整 A1 与缺证区别；阻断权限提升 |
| C09–C12 Data 偷跑、Record 缺损/parent 错 | registry 准入、引用/哈希/parent 校验 | 禁止异常顺序 | 隔离、`UNKNOWN`；阻断恢复猜测 |
| C13–C15 高序候选、旧 Record、同 T1 重放 | 序列/ID 唯一与 GC 保护 | stale/replay 拒绝 | 精确 verdict；阻断二次 generation |
| C16–C17 双 writer、stale writer | 原子多条件 CAS、旧进程 fence | 并发注入 | 至多一赢家；阻断自动重基 |
| C18–C19 旧备份与退休后恢复 | 备份域隔离、nonrollback fence、全入口拒绝 | restore 不回退 root | 所有 branch 与旧 permit `DENIED` |
| C20 完整提交后回应前死亡 | 持久读回及 ACK 独立性 | 同 T1 尾步骤 | 不再签发新 decision |
| G01–G02 Genesis 准备前/锚前 | `ABSENT` 与 Record 顺序、孤儿处理 | CREATE prepare | G0 未提交不得称 Genesis |
| G03–G05 Genesis CAS 不确定/激活/失 ACK | ABSENT→root 持久读回 | 同 ID 激活 | `COMMITTED` 与 READY/权限分离 |
| G06 双 CREATE | `expected=ABSENT` single-winner | 败者不换 ID/Soul | 不得生成双 Genesis |
| FK01–FK02 Fork 准备前/锚前 | source/target 独立引用 | target prepare | source 保持有效，target 未提交 |
| FK03–FK04 source 前进/CAS 不确定 | 同 root 多条件 CAS/读回 | 失败不重基 | target `UNKNOWN` 或精确 FORK |
| FK05–FK07 已提交、重试、同 target 竞争 | 独立 target binding、ID 与唯一键 | target-only 激活/重复恢复 | source 不变；至多一 target winner |
| FK08 Fork 与退休竞争 | 同 root revision 与不可清 fence | 双方竞争注入 | 退休后全 branch 不可运行 |

**证据台账**：设计依据是上述冻结合同与源码入口初查；M1-A 存储原语（durable CAS、Record 引用、nonrollback fence、旧进程 admission、target binding）全部 `PENDING / NOT_PROVEN`，阻断任何 active Soul 写入或旧数据 enrollment。M1-C writer 对应上述全部操作/故障点 `PENDING / NOT_PROVEN`，阻断宣称 transition 完成。M1-D verdict/retirement/fork 四轴断言 `PENDING / NOT_PROVEN`，阻断执行许可。普通 CI、协议文档审核、SQLite 官方说明均不替代目标平台原始实证。

## 6. 独立实施切片与停止条件

1. **M1-A primitive/admission 探针**：另行授权仅合成隔离环境，测试本地 SQLite CAS、Record 同步、OS/断电故障、备份回滚隔离、旧 binary/句柄和多入口围栏；交原始证据。任一平台/FS 无证明路径即 `NO_SAFE_PROTOCOL_WITH_CURRENT_PRIMITIVES / STOP`。
2. **M1-A 存储/Schema/migration**：原语通过后再独立授权；实现唯一 authority store、准入服务、最小实体与只读 legacy 分类。不得把旧历史提升为已证明；不可控入口保持关闭。
3. **M1-B read model**：独立授权四轴读取/校验与 `UNKNOWN` fail-closed，不写 Anchor。
4. **M1-C writer**：独立授权 prepare→CAS→activate、同 ID 幂等和 C/G/FK 故障注入；不得以 M1-A 设计 PASS 替代验证。
5. **M1-D transitions**：独立授权 CREATE/ENROLL/FORK/RETIRE 的 verdict、竞争和全 branch fence；M1-E/Host/Provider/REAL_SEND 继续另立门禁。

若必须改变 World/Memory/Story/Living 真源、四值 verdict、Soul/执行权分离，报告 `ARCHITECTURE_CHANGE_REQUIRED`；不得缩小故障模型或在代码中暗改。设计审核通过仅表示候选和证据计划可供下一次人工门禁审议。
