# M1-P0 — Continuity Persistence Protocol Contract

> 状态：`PROTOCOL_FREEZE_PROPOSAL / NOT_IMPLEMENTATION_AUTHORIZATION`。Execution Base = `c4bda15d77cfee4374d31d30caf94d92d83ee3ca`（本次审计基线，不是未来永久 canonical main）。`SP-006S0 = DONE`，`M1 = ACTIVE_STAGE`，仅 `M1-P0 = AUTHORIZED / PROTOCOL_FREEZE_ONLY`；Schema、Migration、Writer、M1-A 及后续实施均未获授权。本文是对[SP-006S0 上游架构合同](SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md)中 `OPEN_QUESTION_03` 的持久化细化，不改其身份、四值 verdict 或真源边界。配套[崩溃矩阵](../planning/M1-P0-CRASH-RECOVERY-MATRIX.md)与[实施门禁](../planning/M1-P0-IMPLEMENTATION-GATE.md)。

## 1. 范围、不变量与审计方法

仅设计单一受信 management authority domain 内的 Soul continuity transition。`Soul != Model / Host / Session / Prompt / Character Card / World`；`SoulContinuityGeneration != DataGeneration / WorldRevision / WriterEpoch / LivingGeneration / HostEpoch`。`Identity Continuity != Execution Authority`、`Recovery != Authorization`、`COPY != CONTINUATION`、`Database Restore != Soul Continuity`、`UNKNOWN = FAIL_CLOSED`。Verdict 仍只有 `CONTINUATION / FORK / MISMATCH / UNKNOWN`。本文不设计 Memory/Story/Living/Host 的通用事务，不选择 SQLite、fsync、TPM 或远端协调实现，也不调用真实 Host/Provider。

只读审计基于 exact Base 的 `runtime/life_engine/durable.py`、`memory_control.py`、`bridge_control.py`、`world_schema.py`、`world_runtime.py`、`living_runtime.py`、`living_recovery.py`、`living_repository.py`、`living_host_binding.py`、相应 repository 与 `tests/test_durable.py`、`test_memory_restore.py`、`test_schema8_migration.py`、`test_living_host_binding.py`。源码和现有测试仅证明当前功能；下述 Soul 协议全部是**待实现合同**，不标记验证 PASS。

### Persistence Primitive Inventory / Reuse–Gap Matrix

| Primitive | 源码中可证事实 | M1-P0 分类与理由 |
| --- | --- | --- |
| Management Lock | `durable.locked` 使用同一不替换 lock file 的 OS 排他锁；restore/upgrade/rollback、部分 Core 写路径和 Host permit consume 使用 `management`，另有 instance lock。它只协调同一受信安装，不是持久 commit 证据。 | `REUSE` 锁顺序与本地互斥；`EXTEND` 所有 continuity transition 与 recovery 必须共用锁及重检；`DO_NOT_REUSE` 为跨机器共识。 |
| Durable Registry | `registry.json` 指向 release/schema/instance DataGeneration；`write` 经 `atomic_write` 替换并同步目录。restore/upgrade 在候选校验后最后写 registry；`test_durable` 覆盖失败写时旧指针保持。 | `REUSE` 数据激活指针与模式；`EXTEND` 引入可核对的 transition/anchor 引用；`DO_NOT_REUSE` 为 Soul current-head authority。原子文件替换不是跨 record/anchor/DB 的原子事务。 |
| Data Generation | `copy_state` 用 SQLite backup API 复制已提交 WAL、校验 DB，`sync_tree` 尝试同步候选；旧 generation 保留。 | `REUSE` 不活动候选准备；`DO_NOT_REUSE` DataGeneration 编号为 SoulContinuityGeneration。其持久化完成/电源故障语义仍须在目标平台故障注入证明。 |
| Backup / Restore | `snapshot` 含 manifest/hash/控制水位；`restore` 验证后复制候选、重放 Memory/Bridge control、暂停联系、fence Living，然后写 registry。 | `PATTERN_ONLY` 先准备后激活；`EXTEND` 恢复须经独立 continuity decision/anchor；`DO_NOT_REUSE` 备份成功或 registry 切换作合法 continuation。 |
| World WriterEpoch | World transaction 检查 revision、WriterEpoch 与 SessionBinding。 | `REUSE` World 原有围栏；`DO_NOT_REUSE` WriterEpoch 为 Soul lineage 序号。 |
| Memory Deletion Control | `memory-control.db` 递增 sequence/hash chain + 业务备份外 `identity.json`；DB 先提交、锚后写，间隙不一致时拒绝服务；restore 重放删除。`test_memory_restore` 覆盖缺失与 gap。 | `PATTERN_ONLY` nonrollback domain 和 fail-closed；`DO_NOT_REUSE` 账本/sequence 为 Soul 当前头。其不一致窗口不能当已提交 continuity。 |
| Bridge Revoke Control | `bridge-control.db` + `bridge-identity.json` 同类序号、链与撤销重放，缺失/不一致拒绝；原 Scope/授权独立。 | `PATTERN_ONLY` 撤销优先和 fail-closed；`DO_NOT_REUSE` Bridge grant/revoke 为 Soul authority。 |
| Living Recovery | `living_recovery` 提供只读、绑定 generation/operation 的 recovery 投影；`living_runtime` 有 operation ID、事务内幂等收据、generation/session 检查。 | `PATTERN_ONLY` operation identity / 查询先于重复执行；`DO_NOT_REUSE` Living operation、permit 或 receipt 为 Soul commit/发送授权。 |
| Host Binding | `living_host_binding` 消费 permit 时再持 management lock、检查当前 generation；Host epoch/capability 独立。 | `REUSE` 当前发送围栏，未来须另接 continuity read guard；`DO_NOT_REUSE` Host epoch 或 permit 为 Soul identity。未获真实 Host 验证。 |
| Schema Migration | `migrate_generation` 只在非活动副本运行；`upgrade` 准备全部候选后一次切 registry；`rollback_schema`/`rollback_living` 有受控回退与控制重放。 | `PATTERN_ONLY` 非活动迁移与校验；`EXTEND` continuity 版本门禁；`DO_NOT_REUSE` 旧 binary 可安全忽视新 anchor 的假设。 |
| Continuity Anchor CAS / legacy admission guard | 当前源码未发现 SoulId/branch/record-hash 的非回滚单调 CAS、旧 binary 的 continuity-protocol 拒绝门。 | `NEW_PRIMITIVE_REQUIRED = YES`。在实现并故障注入前，不能声称已有可运行安全协议。 |

## 2. Actors、authority 与持久化域

| Actor | 可读/准备/提交/激活/恢复/退役 | 禁止事项 |
| --- | --- | --- |
| Management Authority | 签发有界 `transition_id` 与 Soul/branch/预期头/操作/目标的 decision；持管理锁审核 create/enroll/restore/fork/handoff/retire；批准恢复或人工隔离解除。 | 不能把 decision 当 Host 执行许可；无共同协调者不能签跨机器唯一性。 |
| Continuity Writer | 在锁内依 decision 准备候选、请求 Anchor CAS、核验后激活数据；可重放同一 transition 的幂等尾步骤。 | 不得从 Prompt、模型、墙钟、最后启动者生成 decision；CAS 失败不得自动改 expected head 重试。 |
| Continuity Record Store | 按内容/hash 寻址保存 immutable record，支持精确读取、完整性验证及引用保护；可有孤儿候选。 | 不得通过 record 的 `active` 字段独立裁决 current head；不得覆盖已引用 record。 |
| Continuity Anchor Store | 在业务备份回滚域外保存 SoulId/domain 的单调 `sequence + committed record hash + active branch/head + retirement fence + protocol version`；对 `expected previous anchor` 做持久 CAS。 | 不得被业务 restore/registry 写/旧 binary 重置；不得授予执行权限。 |
| Durable Registry / Data Generation Store | 准备、校验不活动候选；仅在匹配已提交 anchor 后激活精确 data reference。 | registry/DB 成功不等于 continuity commit；不独立发 Soul verdict。 |
| Recovery Reader | fresh process 下读 Anchor、Record、registry、候选、版本并确定分类；仅在严格前提下完成幂等尾步骤。 | 不能静默创建 decision、新 generation、新 Instance、新 authority；UNKNOWN 不可升级。 |

持久化域分为：`D-business`（可备份/恢复的 World、Memory、Story、Living DB 与 DataGeneration）、`D-registry`（现有活动数据指针）、`D-continuity-record`（immutable、可由 anchor 稳定寻址、已引用者不得被 GC）及 `D-continuity-anchor`（不随业务备份回退、单调 CAS）。`D-continuity-record` 可以在未来选择同盘或独立存储，但**必须**即使 registry 仍指旧 data 也能由新 anchor 找到对应 durable record；否则 C08 不安全。Memory/Bridge control 各保留原 nonrollback 域，不与 continuity anchor 混为一账本。上述隔离是*所需能力*，不是当前仓库已经实现的性质。业务文件、record 和 anchor 全部可被同权限恶意管理员复制/篡改时，单机 Core 无法证明外部全局唯一；真实跨机器/Host 操作继续 `UNKNOWN`。

## 3. Record–Anchor 权威关系、状态机与顺序比较

Record 是 immutable lineage evidence，最小绑定上游字段：protocol version、SoulId、authority domain、SoulInstanceId、branch、SoulContinuityGeneration、parent hash/sequence、`transition_id`、operation/decision reference、target DataGeneration 与其完整性 digest、timeline/opaque relationship namespace 摘要、record hash。`transition_id` 由受信 Management Authority 在准备前签发，作用域为 `authority-domain + SoulId + branch`，同一 ID 重试必须绑定**相同** decision、expected head、目标/操作和 record hash；不同 payload 重用 ID 是冲突并隔离。备份、模型或 Host 文本不得签发。`SoulContinuityGeneration` 随受信 transition 前进，不能从 DataGeneration/World/Living/Host 数字推导。

Anchor 是**唯一 current-head adjudicator**。Anchor CAS 的单个持久状态包含所引用的 committed transition record hash、序号、当前 active continuation branch/head、retirement fence 与版本；显式 `FORK` 可以登记新 branch record，但原 active branch 不因复制而转让执行权。Record 的 `candidate/active/fork/retired` 是操作意图/派生描述，`record exists != record committed`，`record says active != current active head`。已提交链由可验证的 anchor head 及其 parent chain 判定；anchor 不存业务正文。不能用时间戳在 record 与 anchor 间选较新者。

状态：`ABSENT`（无候选）、`PREPARED`（候选 record/数据完整持久，anchor 旧）、`COMMITTED`（anchor CAS 已持久完成且链/候选完整；业务激活可能待完成）、`SUPERSEDED`（被后继有效 anchor 链覆盖）、`RETIRED`（anchor 不可回滚退役 fence）、`QUARANTINED`（操作处理状态，不是 verdict）。`PREPARED` 仅是候选的持久事实；`COMMITTED/SUPERSEDED/RETIRED` 必须由 Anchor 与链派生，不能只存在可回滚 DB。`UNKNOWN` 是证据 verdict，不是处理状态；典型为 `UNKNOWN + QUARANTINED`。

| 候选 ordering | 崩溃与不一致 | 结论 |
| --- | --- | --- |
| A：Record prepare → Anchor commit → Registry/Data activate | 前锚 crash 留孤儿候选、旧头有效；后锚 crash 可凭完整候选与 anchor 重放精确激活；需 Anchor durable CAS、稳定 record 引用与旧 binary guard。 | **选择为 `MINIMAL_SAFE_PROTOCOL`，条件是新增原语和实测满足**。Anchor CAS 持久化是唯一 continuity linearization point。 |
| B：Data activate → Record → Anchor | Data 已活跃而 anchor 仍旧；旧/新 binary 可读取新业务状态并越过旧 lineage，崩溃时 registry 与锚分裂。 | `DO_NOT_REUSE`；C09 必须注入并隔离，不能视为正常中间态。 |
| C：Anchor → Record → Data activate | Anchor 可能悬空指向缺失/损坏 record，无法机械验证新链；退役/迁移仍可留下歧义。 | 拒绝；C10/C11 必须 fail-closed。 |

### 选定抽象协议与 linearization point

1. **Admission / lock**：无锁只可读候选输入、计算计划，不可宣告 active 或发权限。`CREATE / ENROLL / RESTORE / FORK / HANDOFF / RETIRE / CONTINUITY GENERATION ADVANCE` 及 recovery activation 均持同一 management lock，必要时依既有顺序再持 instance lock。拿锁后重读当前 Anchor、Record、registry/schema、控制水位、旧/新版本兼容与 decision；预期头或权限变化即停止。锁丢失、超时或进程 crash 后旧进程不得继续写；下一进程重新获取锁并从 durable evidence 读起。OS 锁释放只证明本地互斥，不证明旧进程已被持久 fence；Anchor expected-head CAS 是最终 stale-writer fence。两个 writer 对同一旧头最多一个成功，失败者不得自动改基准重试。
2. **Prepare**：先准备并同步目标 DataGeneration/迁移结果、必要的 Memory/Bridge 控制重放及 pause/fence，校验 digest/Schema/Scope；再持久写 immutable Record，绑定同一 `transition_id`、expected head 和精确 data reference。未获新 anchor 前 registry 不得指向新 data；record store 的写入必须是不可见半成品或可检测损坏。任何失败保持旧头、拒绝新执行权。准备期间的候选可以后续谨慎清理，但不能清理已被 anchor 引用的 record/data。
3. **Commit**：在锁内以 `expected previous anchor + transition_id + candidate record hash` 请求**单次持久化、线性化、单调** Anchor CAS。`CONTINUITY_LINEARIZATION_POINT = Anchor CAS durable commit`。CAS 操作须对读者呈现完整旧值或完整新值；调用方 ACK 丢失时不能凭返回超时推断失败，须 fresh-read anchor。Anchor 不能随 business backup rollback。若底层无法给出这些语义，`NO_SAFE_PROTOCOL_WITH_CURRENT_PRIMITIVES / NEW_PRIMITIVE_REQUIRED`，不得进入写路径。
4. **Activate**：读回新 Anchor、验证完整链/目标数据、registry 旧值仍是 decision 绑定值，然后幂等激活精确 DataGeneration；激活后再核对 Anchor/registry/Schema，进程可以返回 lineage committed 的收据。已提交但未激活时**不得**向业务/Host 报可运行 `CONTINUATION`；只允许只读 recovery，正常 verdict `UNKNOWN` 且 operational state `QUARANTINED`，直到仅凭已持久候选和原 decision 安全完成激活。若内容、schema、控制、registry 不匹配，必须保持隔离并要求人工治理；不得创建新 transition 代替。

因此在 linearization point 前 crash，恢复只可用旧 committed head（且新候选不得活跃）；点后 crash，Anchor 可识别已提交 transition，但若验证/激活不完整则 `UNKNOWN / QUARANTINE`，绝不猜测运行资格。`Continuity Commit → Identity Continuity Established` **不等于** `Execution Authority Granted`。Host Binding、Living permit、delivery gate、Session 和 provider 资格仍独立重新授权；`CLAIMED != SENT != ACKNOWLEDGED`，`REAL_SEND = NO`。

## 4. Recovery、lost ACK、quarantine 与不可回滚围栏

Recovery 必须在 fresh process 中先进入不可发送/不可写的 admission 状态，获取 management lock，读取并验证协议版本、Anchor 完整性与非回滚域身份、链/hash/父序、decision/transition ID、Record 与 target DataGeneration/控制水位，再看 registry。固定 fixture（相同 bytes、anchor、registry、version）得到同一 classification、verdict、quarantine 结果：`recover(recover(s)) == recover(s)`。重复运行不得仅因次数将 `UNKNOWN` 升为 `CONTINUATION`；变化只能来自新受信 evidence、原 decision 所允许的确定性尾步骤，或新受信 management decision。

| Evidence | 恢复裁决 |
| --- | --- |
| 新 Record durable、Anchor 旧、registry 旧 | 新候选未提交；旧头可用（需旧头完整），新候选 `UNKNOWN`，不得激活。相同 transition 可以在重新校验与明确原 decision 仍有效后重试原 CAS；不得制造第二 generation。孤儿清理仅在未被任何 anchor 引用且已证明无执行泄漏时允许。 |
| Anchor 新、Record/数据完整、registry 旧 | transition 已提交；仅按原 decision、原精确目标幂等完成 activation；完成前 `UNKNOWN / QUARANTINED` 且无执行权。无完整候选则持续隔离，不能回滚 Anchor。 |
| Anchor 新、Record 缺失/损坏或父 hash 错 | `UNKNOWN / QUARANTINED`；禁止从可回滚 backup 猜造 record，人工治理。 |
| Registry/Data 新、Anchor 旧 | 协议禁止；`UNKNOWN / QUARANTINED`，拒绝旧/新执行权。不可自动选择 registry 或简单回滚（可能存在外部副作用）。 |
| Anchor/Record/registry 完整一致，且非 retired | 单受信域内可导出 `CONTINUATION`；仍不授予任何 Host/Living/delivery 权限。 |

`commit succeeded / ACK lost`：以原 `transition_id` 查询 Anchor 中已提交 hash；若匹配，返回**同一**结果并完成允许的尾步骤；若 Anchor 仍为 expected old，候选未提交，可在原 decision 未失效且重检后重试**同一个** CAS；Anchor 不可读、出现别的 head、record/目标不匹配时 `UNKNOWN / QUARANTINED`。绝不按墙钟、调用次数或进程重启次数递增 SoulContinuityGeneration。

可幂等重放的仅是同一 `transition_id` 下的只读验证、完整候选准备（内容寻址/严格相等）、Anchor 旧且 decision 有效时的同一 expected-head CAS，以及 Anchor 已新时的精确 registry activation/收据读取。**不可**重放为“新操作”的是 CREATE/enrollment、generation advance、fork/handoff、RETIRE、Host permit consumption、delivery/REAL_SEND 或未知外部副作用；这些必须先查询受信 evidence，必要时由新的 management decision 单独处理。CAS crash 后旧值的读取必须在上一个 writer crash-stop 与存储操作最终落定后进行；若底层可能在读取 `A0` 后再异步落下旧 CAS，该实现不满足 linearizable durable CAS 要求，判 `UNKNOWN / QUARANTINED` 而非安全重试。

Quarantine 进入条件：missing/corrupt/unknown-version anchor，悬空 anchor、断链/哈希错、record/anchor/registry 不匹配、未知或部分 migration、退役冲突、并发/锁丢失歧义、无法判明 CAS durable outcome、业务控制水位冲突。隔离只允许有界只读检查和脱敏诊断；continuity write、执行/Host authority、REAL_SEND 均拒绝。修复须有新受信 evidence 或独立 governance decision，不能自动覆盖锚。`UNKNOWN` 是 verdict，`QUARANTINED` 是运行处理状态；二者分离。

`RETIRE` 使用同一 Prepare→Anchor CAS；线性化点是 Anchor 中不可回滚 retirement fence 的持久提交。fence 是 SoulId/domain 的终态，不可被旧 backup/registry/Host state/permit/Living Attempt 清除；同一 SoulId 不再生成 active successor。旧 binary 若不能理解 fence 必须在部署 admission 层被阻断，不能读取旧 DB 后激活。`G12 → restore G9` 仅得待审数据候选，Anchor 仍 G12；未来获授权的受控 restore 若可行，须由当前头签发新 successor（例如 G13），绝非将 anchor 回退 G9。裸 COPY 即便 DB+Record 一致也无新 authority-domain admission；无共同协调者判 `UNKNOWN`，受信显式 fork record 才得 `FORK`，但不继承原 branch 执行权。

## 5. Migration、legacy binary 与能力边界

Migration 可在 continuity commit 前对**不活动候选**准备/校验，绝不可提前使新 schema/registry active。新 binary 读旧 schema：无已批准 enrollment/升级合同则 paused/read-only/`UNKNOWN`；旧 binary 读新 Anchor/不支持协议：必须由**独立于旧 binary 代码路径的 admission/launcher/release gate**在任何业务写、Host permit 或发送前拒绝。当前 launcher/registry 仅有 data-schema/release 检查，未见已实现的 continuity-protocol gate；单靠新 binary 自检无法防止旧 binary 被直接启动。该兼容围栏是 `NEW_PRIMITIVE_REQUIRED` 的一部分，后续必须给出可验证的部署威胁模型；若无法阻断旧 binary，则不能激活新协议。Migration 成功但 Anchor 旧只留下不活动候选；Anchor 新而 migration/activation 失败为 quarantine，不得用旧 binary 降级绕开。Schema rollback 不得回滚 Anchor 或 retirement fence。

当前 `DATA_SCHEMA = 8`、`SP-005A-living-runtime-v1`、`SP-004K-prompt-v1`、`PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES` 均未改变；`SCHEMA_CHANGE_REQUIRED = YES / SCHEMA_CHANGE_AUTHORIZED = NO`。新原语最小语义是：单受信域单调 durable Anchor CAS、稳定可寻址 immutable Record、以 Anchor 版本约束的所有 active/writable 入口、非回滚退役 fence。它们不授予 Soul 以外真源的写权、不授予 Host/REAL_SEND 权限。`OPEN_QUESTION_01 = ACCEPTED_CAPABILITY_BOUNDARY`：无共同受信跨机器协调者仍 `UNKNOWN / FAIL_CLOSED`，本 Gate 不引入远端服务。`OPEN_QUESTION_02 = DEFERRED_TO_M3_PERSON_IDENTITY_GATE`：这里只能用 opaque/synthetic relationship namespace，不设计真实 PersonRef。

## 6. Q1–Q16、未决与停止条件

| 问题 | 冻结答案 |
| --- | --- |
| Q1–Q2 linearization 与安全性 | Anchor 的 durable expected-head CAS；候选 data/record 先完整持久，单调非回滚锚只指完整 record，前锚旧态、后锚新态或隔离。能力尚待实现/故障注入证明。 |
| Q3 Record 新/Anchor 旧 | 未提交，旧头；候选不可激活，只可原 ID 重试或安全清理。 |
| Q4 Anchor 新/Record 缺 | `UNKNOWN / QUARANTINED`，不能从备份推断。 |
| Q5 Anchor 新/Data inactive | 验证候选与原 decision 后幂等激活；完成前隔离。 |
| Q6 Data active/Anchor 旧 | 非法不一致，隔离并人工治理。 |
| Q7–Q8 lost ACK/重复 retry | `transition_id` 绑定唯一候选；fresh-read Anchor 判同一 commit/未提交/歧义，不增第二代。 |
| Q9 stale writer | management lock + 锚 expected-head CAS + read guard；失败者停，不能自动换头。 |
| Q10–Q11 rollback/retirement | Anchor 在业务回滚域外；旧数据不改 current head，终态 fence 不可倒退。 |
| Q12 legacy binary | 独立 admission/release protocol gate 阻断未知版本；现有实现不足，必须后续实现并证实。 |
| Q13–Q14 UNKNOWN/quarantine | 缺证、损坏、跨域不唯一、提交歧义等返回 UNKNOWN；持久域/激活不一致同时隔离。两者不是同一 enum。 |
| Q15 自动尾步骤 | 仅 Anchor 已提交且 record、原 decision、目标数据、控制水位、旧 registry 预期全部可验证时，重复执行同一 activation。 |
| Q16 人工治理 | dangling/corrupt anchor、断链、registry 新锚旧、版本不支持、退役冲突、缺候选或跨域全局歧义；不得自动修复。 |

**Open questions（非本 Gate 的事实猜测）**：所选存储技术能否提供跨电源故障 durable CAS 与 nonrollback 保护；record/anchor 具体同盘布局、GC 证明与旧 binary 独立 admission；如何在目标平台确定锁丢失和目录同步语义。这些是 M1-A/M1-C 的**阻塞实施验收条件**，不是改变协议的许可。若任何技术选型无法满足上述语义，则 `NO_SAFE_PROTOCOL_WITH_CURRENT_PRIMITIVES / NEW_PRIMITIVE_REQUIRED = YES`，停止写路径；若必须破坏 World isolation、Controlled Bridge、Host safety、Recovery/authority 或上游身份原则，则 `ARCHITECTURE_CHANGE_REQUIRED = YES / STOP`，交独立裁定。本次只冻结合同、矩阵与后续门禁，`ARCHITECTURE_CHANGE_REQUIRED = NO`。
