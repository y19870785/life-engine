# M1-P0 — Implementation Admission Gate

> **流程治理切换（条件生效）：** [阶段自主开发方案 R2](CODEX-STAGE-AUTONOMY-PLAN.md)允许用户在后续有效阶段合同中逐项列明 M1-A–E 的内部权限和自主续片条件。承载本段的治理 PR 自身仍沿用旧流程；其合并后独立收口前，本段不生效。R2 规划 PASS、协议 PR 合并或 `M1 = ACTIVE_STAGE` 均不授权当前任何切片。下文的 M1-A 存储/Schema 与 admission 门槛、M1-C 独立写路径许可、M1-D 每种 transition 审核、M1.x/M2 阶段隔离保持。未被有效合同逐项纳入的切片仍按下文“每片均需独立授权”执行。

> 本文只冻结**后续独立授权所需条件**，不是实施任务书。`SP-006S0 = DONE`；`M1 = ACTIVE_STAGE` 仅表示阶段已进入；本次 `M1-P0 = AUTHORIZED / PROTOCOL_FREEZE_ONLY`。M1-A/B/C/D/E、Schema、Migration、SoulIdentity Runtime、Record/Anchor write、M1.x、M2、Host/Provider/REAL_SEND 均 `NOT AUTHORIZED`。协议见[架构合同](../architecture/M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md)，C01–C20、G01–G06、FK01–FK08 见[崩溃矩阵](M1-P0-CRASH-RECOVERY-MATRIX.md)。

## 1. 本 Gate 冻结的选择与阻断条件

抽象 `MINIMAL_SAFE_PROTOCOL = Data candidate durable → immutable Record durable → nonrollback Anchor expected-head CAS durable → exact Registry/Data activation`。`CONTINUITY_LINEARIZATION_POINT = Anchor CAS durable commit`；CREATE/ENROLL 的 Genesis CAS 必须 `expected SoulRoot=ABSENT`，普通 successor 比较 branch head，FORK 的同一 SoulRoot CAS 比较 source head、target branch `ABSENT` 与 Soul retirement fence。每次 recovery 分列 `Persistence Commit Fact`、`Identity Verdict`、`Operational State`、`Execution Authority`：已提交、Record/候选/decision/控制完整而 registry 未激活时分别为 `COMMITTED`、普通后继 `CONTINUATION`（fork 为 `FORK`）、`QUARANTINED(ACTIVATION_PENDING)`、`DENIED`，不是 identity `UNKNOWN`；缺证才 `UNKNOWN`。`Record exists != committed`，`DB/registry success != Anchor success`，`Anchor success != Execution Authority`，`Recovery != Authorization`。原 `transition_id` 绑定 decision/expected root/branch head/record hash/目标 DataGeneration；lost ACK 的重复调用只能查询或完成同一 transition。同一持久 fixture 的分类确定；受控 activation 改变 registry bytes 与 operational state，重复恢复对新状态幂等，不凭运行次数升级 identity verdict。

**`NEW_PRIMITIVE_REQUIRED = YES`**，不是可选优化：当前代码没有 Soul Continuity 非回滚 durable Anchor CAS、稳定可寻址且受锚引用保护的 immutable Record，也没有可证明旧 binary 无法绕过新协议的独立 admission guard。R1 还要求最小 SoulRoot/branch-scoped head 原子模型：root `ABSENT` 的 Genesis single-winner CAS、同一 CAS 验证 source head + target `ABSENT` 的 Fork、覆盖所有 branch 的 Soul-level retirement fence。Memory/Bridge 控制账本仅是 fail-closed 模式，durable registry 的原子替换仅是 DataGeneration 指针。选定协议是**条件性安全合同**，不是声称现有实现已经满足。后续实现若不能在目标平台证明这些最小语义，应 `NO_SAFE_PROTOCOL_WITH_CURRENT_PRIMITIVES / STOP`；不得先写 Schema/Writer 再补证据。

## 2. M1 内部实施切片（每片均需独立授权）

| 切片 | 目标和依赖 | 准入、退出证据、停止条件 |
| --- | --- | --- |
| `M1-A` Schema / Storage Contract | 在 M1-P0 经独立审核后，只评审最小实体/字段、protocol version、SoulRoot/branch-scoped Anchor CAS 抽象、Record 可寻址和 rollback domain；验证 Genesis `expected=ABSENT`、Fork source+target 双条件与 Soul-level retirement fence 可在单受信域内作为单个 durable CAS 语义。决定具体存储但不合并不同真源。 | 独立授权后才可改 Schema/Migration。退出需证明旧 binary admission、跨崩溃 durability/CAS、record 引用与 GC、备份不回滚锚及所有 branch 受退休 fence 约束；做不到即 STOP，禁止 active state。 |
| `M1-B` SoulIdentity / SoulInstance / Record Read Model | 依赖 M1-A 字段与迁移合同；只读解析旧/新版本、SoulId/Instance/branch/parent 与隔离诊断。 | 旧数据默认 `UNKNOWN`，不得自动 enrollment；读路径不得签发权限。未知版本/缺锚 fail-closed。 |
| `M1-C` Continuity Writer / Anchor Commit Protocol | 依赖 M1-A/B 和独立写路径授权；实现 management lock、decision/T1、prepare、SoulRoot expected-head CAS、幂等 activation/recovery。 | C01–C20、G01–G06、FK01–FK08 failure injection、新进程重复 recovery、Genesis single-winner、Fork 双条件、并发/stale writer、lost ACK 与三层判定均有确定性证据；任何未提交候选判 continuation 即 STOP。 |
| `M1-D` CREATE / ENROLL / RESTORE / FORK / HANDOFF / RETIRE | 依赖 M1-C 机械证明；每种 transition 保留独立审核与最小作用域。 | 退役、回滚、复制、旧备份、跨域无协调、旧 binary 全 fail-closed；不能自动继承 Host/Living/delivery 许可。真实跨机器/Host handoff 仍受 `OPEN_QUESTION_01` 外部治理阻断。 |
| `M1-E` M1 Verification | 汇集身份/实例/代次、Record/Anchor 与恢复合同；保持 World/Memory/Story/Living/Host 原真源。 | exact CI + 独立审核；M1 出口不等于 M1.x Proof PASS，不授权 M2 或真实 Host。 |

固定顺序：`M1-P0 独立审核 → M1-A 独立授权与存储/Schema 评审 → M1-B → M1-C → M1-D → M1-E`。若实际拆分需调整，须新治理任务，不得在本 PR 把它解释为实施许可。不得先创建“空表”、Anchor prototype、writer 或 active enrollment。`SCHEMA_CHANGE_REQUIRED = YES / SCHEMA_CHANGED = NO`；当前 `DATA_SCHEMA = 8`，Living `SP-005A-living-runtime-v1`、Prompt `SP-004K-prompt-v1`、`PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES` 均保持。

## 3. M1-A 之前的决策与证据门槛

1. **Authority/admission**：所有可能写业务数据、发 Host permit、触发 delivery 的新/旧 binary 入口必须经过受信协议版本门。已运行旧进程也要在管理 barrier 与可验证 fence 下失效；若可绕过，新协议不得激活。OS management lock 只在本地安装内有效，不能冒充全球协调。
2. **Persistence**：给出 target-platform 的 durable CAS 证据，证明断电/进程 crash 下 SoulRoot 读者只见旧或新完整值，root `ABSENT` 只能一个 CREATE/ENROLL 获胜，FORK 的 source-head、target-ABSENT 与 retirement 条件同点原子比较，退役 fence 对所有 branch 单调不回滚；Anchor 不随业务备份/Schema rollback 恢复。Record 被 Anchor 引用前已 durable、之后可稳定寻址且不会被清理。普通 successor 不得使用 GENESIS parent；Genesis B0/G0 与 ENROLL baseline 的专用 parent 必须可区分。
3. **Data/registry**：D1 在锚前准备/校验，registry 只在锚后激活；激活前任何旧/新业务入口均不能取得执行权。Anchor 已新/registry 旧可凭完整候选与原 decision 幂等完成；registry 已新/Anchor 旧必须隔离，不可猜测回滚。FORK target 激活不得改 source branch 的 registry/data 指针；如现有 registry 无独立 target binding，必须先在 M1-A 冻结新增最小合同，不得伪装可复用。
4. **Recovery/retirement**：`transition_id` 同一 decision 重试不产生第二 generation；C01–C20、G01–G06、FK01–FK08 均有故障注入、fresh-process、原始证据检查与 persistence/verdict/operational/authority 分列断言。ENROLL baseline 不证明旧历史；Soul RETIRE fence 已提交后所有 branch、旧 backup、旧 permit、旧 Host/Living state 永不复活。`BRANCH_RETIREMENT = OUT_OF_SCOPE`。
5. **Safety boundary**：World revision、Memory/Story/Living truth、Controlled Bridge grant、Host Binding authority 原样归各 owner。ContinuityProof 是派生只读报告，不是 bearer token。`UNKNOWN = FAIL_CLOSED`；`CONTINUATION` 也不自动赋予 execution authority。无共同协调者的真实跨机器/Host 迁移保持 `UNKNOWN`。

以上任一证据缺失时，M1-A/C 等相关切片不得进入 active write。技术选择（SQLite transaction、filesystem sync、硬件密钥或其他）必须先证明语义，再获实施授权；本文件不预选。当前 `OPEN_QUESTION_01 = ACCEPTED_CAPABILITY_BOUNDARY`；`OPEN_QUESTION_02 = DEFERRED_TO_M3_PERSON_IDENTITY_GATE`，测试只用 synthetic/opaque relationship namespace。

## 4. M1-P0 文档退出检查与停止

文档审核至少逐项检查：只读 primitive audit 与 Reuse/Gap Matrix；Actors/authority/persistence domains；SoulRoot/BranchAnchor 唯一 current-head 裁决；CREATE Genesis、ENROLL baseline、FORK source/target 双条件；状态机、Prepare/Commit 与 linearization；锁重检与 Anchor CAS/fencing；lost ACK 与同 ID 幂等；persistence fact、identity verdict、operational state、authority 分离；Soul retirement/rollback；DataGeneration/Schema migration/legacy binary；C01–C20、G01–G06、FK01–FK08；M1-A–E 依赖及禁止自动授权。文档通过只意味着协议基线可供下一份实施任务书引用，**不**证明目标平台原语已存在、场景已 PASS 或 M1-P0 仓库任务 DONE。若独立审核要求更改协议，先在同一治理流程修订，不能在实现中暗改。

如源码/未来验证证明必须破坏 SP-006S0 的 `Soul != Model/Host`、`Identity Continuity != Execution Authority`、`Recovery != Authorization`、`COPY != CONTINUATION`、`UNKNOWN = FAIL_CLOSED`、Original Soul/RP 隔离、World/Memory/Story/Living 真源、Controlled Bridge 或 Host Safety，则 `ARCHITECTURE_CHANGE_REQUIRED = YES / STOP` 并交独立裁定；本次审计未发现此要求，当前设计 `ARCHITECTURE_CHANGE_REQUIRED = NO`。若只是缺 Anchor CAS、Record 稳定寻址或 legacy admission，记录 `NEW_PRIMITIVE_REQUIRED = YES`，不实现，等待独立审核与后续授权。

本 PR 的唯一目标是 Draft Review。`M1-P0 Draft PR != Ready != Merge != DONE`，且未来 `M1-P0 DONE != M1-A AUTHORIZED`。Runtime/tests/Schema/migration/workflow、Host operation、Provider Network、REAL_SEND 均保持未改/未执行。
