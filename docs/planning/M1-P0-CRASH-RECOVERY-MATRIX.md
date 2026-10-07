# M1-P0 — Crash / Recovery Matrix（设计，不是测试结果）

> 全部 C01–C20、G01–G06、FK01–FK08 均为 `PROTOCOL_SCENARIO`，**没有**任何场景标为 PASS；尚未实现 failure injection 或 continuity writer。依据[协议合同](../architecture/M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md)，后续实施准入见[实施门禁](M1-P0-IMPLEMENTATION-GATE.md)。范围只限单受信 authority domain；无共同协调者的跨机器行为为 `UNKNOWN / FAIL_CLOSED`。固定 fixture 重复 fresh-process recovery 必须得到相同 persistence fact、identity verdict、operational state。

## 读表约定与必须收集的证据

每行的 `P` 是同一受信域中完整、已提交且未退役的旧状态：SoulRoot 的 branch `B0` Anchor `A0` 指 Record `R0`、registry 指旧 `D0`；若旧态本身不完整，任何“OLD”路径改为 `INDETERMINATE / UNKNOWN / QUARANTINED`。`R1` 为绑定唯一 `transition_id=T1`、expected `A0`、目标 `D1` 的 immutable 候选；`A1` 为经 durable SoulRoot CAS 提交的 B0 锚；`D1p` 为完整但不活动的数据候选，`D1a` 为 registry 已激活的新 data。`OLD` = 旧 committed lineage 可读（旧执行权**不**由 recovery 复活）；`NEW` = 完整新 lineage。执行权限始终需 Host Binding/Living/delivery **另行授权**，表中的 Authority 默认 `DENIED`。`—` 表示尚不存在；`?` 表示 torn/读不出，不允许猜测。

必须分开记录 `Persistence Fact`、`Identity Verdict`、`Operational State` 与 `Execution Authority`。`旧头` verdict 只针对原 `R0`，`候选` verdict 针对 `R1`；未提交候选为 `UNKNOWN` 而不是已证明的 continuation。已提交且 Record、目标候选、decision、控制水位完整的 R1 即便 registry 旧，identity 仍可 `CONTINUATION`，但 operational 为 `QUARANTINED(reason=ACTIVATION_PENDING)`、authority `DENIED`。所有行证据等级均为 `PROTOCOL_SCENARIO`。未来注入器需能在指定边界确定性杀进程、另启进程、读取原始 persisted bytes/SoulRoot/BranchAnchor/registry/protocol version，并验证状态与副作用；当前无此实现。

| ID / 前态、操作、故障点 | Record | Anchor | Registry/Data | Persistence Fact | Identity Verdict | Operational State / recovery | Execution Authority | 原 ID 重试 / 清理 | 必需证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 `P`；successor/advance 获取锁前 crash（CREATE 见 G01） | R0 | A0 | D0 | 旧头 COMMITTED；新操作 ABSENT | 旧头 CONTINUATION；新候选不存在 | 旧态可只读；下次重新获锁重检 | DENIED（不继承） | 原 decision 可重检 / 无 | A0-R0-D0、锁释放 |
| C02 `P`；获锁后重检前 crash | R0 | A0 | D0 | 旧 COMMITTED；新 ABSENT | 旧 CONTINUATION | 旧态只读；旧内存验证作废 | DENIED | 原 ID 可重检 / 无 | A0-R0-D0、锁证据 |
| C03 `P`；重检后准备前 crash | R0 | A0 | D0 | 旧 COMMITTED；新 ABSENT | 旧 CONTINUATION | 旧态只读；不得凭先前重检提交 | DENIED | 原 ID 重新验证 / 无 | A0、decision/T1 |
| C04 `P`；R1 持久化中 crash | R0+R1? | A0 | D0+D1p 或部分 | 旧 COMMITTED；候选未提交 | 旧 CONTINUATION；候选 UNKNOWN | 仅损坏候选隔离；旧态完整才可只读 | DENIED | 原 ID 重备 / 未引用候选可审慎清 | A0/R0、R1 hash/长度、T1、D1 digest |
| C05 `P`；R1 durable、锚旧 crash | R0+R1 | A0 | D0+D1p | 旧 COMMITTED；候选 PREPARED | 旧 CONTINUATION；候选 UNKNOWN | 旧态只读；R1 不可激活 | DENIED | 原 decision/同 T1 重检后 CAS / 未引用可清 | R1 parent/hash、T1/decision、D1、A0 |
| C06 `P`；CAS 开始、outcome 未知 crash | R0+R1 | A0 或 A1 或 ? | D0+D1p | fresh-read A0→PREPARED；A1→COMMITTED；?→INDETERMINATE | A0 候选 UNKNOWN；A1 完整证据 CONTINUATION；? UNKNOWN | A1 时 QUARANTINED(ACTIVATION_PENDING)；? QUARANTINED(EVIDENCE_CONFLICT)；A0 旧态只读 | DENIED | 仅证实 A0 后同 T1 可重试 / ? 不清 | root CAS 旧/新完整值、T1、R1/D1、版本 |
| C07 `P`；A1 durable、ACK 丢失 crash | R0+R1 完整 | A1 | D0+D1p 完整 | COMMITTED | CONTINUATION | QUARANTINED(ACTIVATION_PENDING)；按原 T1 精确激活后可 READY | DENIED | 同 T1 查询/尾步骤 / R1/D1 不清 | A1→R1、parent、decision/T1、D1/水位、D0 expected |
| C08 `P`；A1 前进、激活未完成 crash | R0+R1 完整 | A1 | D0+D1p 或 D1a 或第三值 | 完整 A1 为 COMMITTED；锚损坏为 INDETERMINATE | D0/D1a 且目标完整为 CONTINUATION；第三值/缺证 UNKNOWN | D0→QUARANTINED(ACTIVATION_PENDING)，可幂等激活；D1a 匹配→READY；其他→QUARANTINED(EVIDENCE_CONFLICT) | DENIED | 同 T1 尾步骤仅 D0 / 不清 | A1/R1/T1、registry bytes、D1 digest/Schema/水位 |
| C09 `P`；异常 Data active、Anchor 旧 | R0+R1? | A0 | D1a | 旧 COMMITTED；新未提交 | 新声称 UNKNOWN | QUARANTINED(EVIDENCE_CONFLICT)，人工治理；不得选 registry 或回滚猜测 | DENIED | 否 / 否 | A0、D1a、R1/decision、副作用审计 |
| C10 `P`；Anchor 指缺失 R1 | R1 缺 | A1→R1 | D0 或 D1p | Anchor COMMITTED；Record evidence 缺 | UNKNOWN | QUARANTINED(EVIDENCE_CONFLICT)；不可用旧备份猜造 | DENIED | 否 / 否 | A1/hash/序号、Record store 缺失与来源 |
| C11 `P`；Anchor 指损坏 R1 | R1 hash/结构损坏 | A1→R1 | 任意 | Anchor COMMITTED；evidence 损坏 | UNKNOWN | QUARANTINED(EVIDENCE_CONFLICT) | DENIED | 否 / 否 | A1、R1 bytes/hash/格式、保全日志 |
| C12 `P`；R1 parent hash 错 | R1.parent≠R0 | A1 或尝试 A1 | 任意 | 提交前应拒；若 A1 已在则 COMMITTED 但链坏 | UNKNOWN（可证异 Soul 才 MISMATCH） | QUARANTINED(EVIDENCE_CONFLICT) | DENIED | 否 / 否 | parent chain、hash、SoulId/domain、T1 |
| C13 `P`；R1 seq>A0 seq，未被引用 | R1.seq>A0.seq | A0 | D0+D1p | 旧 COMMITTED；候选 PREPARED 或损坏 | 旧 CONTINUATION；正常候选 UNKNOWN | 连续下一步可按 C05；跨号隔离 | DENIED | 仅连续原 T1 / 未引用可审慎清 | seq 连续性、T1、parent、引用集合 |
| C14 `P`；旧 Record seq<当前 Anchor | R0 或 stale R1 | A1/更高 | D0/旧数据 | 当前 Anchor COMMITTED；缺新链则 evidence 不完整 | 旧声称 MISMATCH；缺链 UNKNOWN | 旧实例拒绝；缺链 QUARANTINED(EVIDENCE_CONFLICT) | DENIED | 旧 T1 不可重基 / 当前链不清 | Anchor seq/hash、后继链、旧 Instance |
| C15 `P`；同 T1 重复提交/lost ACK | 同 R1 或同 ID 异 payload | A0 或 A1 | D0+D1p 或 D1a | A0→PREPARED；A1 同 hash→COMMITTED；冲突→INDETERMINATE | A1 完整证据 CONTINUATION（激活前后相同）；A0 候选 UNKNOWN；冲突 UNKNOWN | A1+D0→QUARANTINED(ACTIVATION_PENDING)；A1+D1a→READY；冲突隔离 | DENIED | 同 ID 同 payload 可 / 已引用不清 | T1 唯一性、decision/hash、root、registry |
| C16 `P`；Writer A/B 同 A0 竞争 | R1a+R1b | 至多一个 A1 | 仅 winner 目标可激活 | winner COMMITTED；loser PREPARED | winner 完整则 CONTINUATION；loser UNKNOWN | winner 激活前隔离；loser 停止；双赢为证据冲突隔离 | DENIED | loser 不自动重基 / 孤儿可审慎清 | 两个 T/expected root、CAS 顺序 |
| C17 `P→A1`；stale Writer 按 A0 继续 | stale R1+新链 | A1 | D1a 或 pending | 新链 COMMITTED；旧候选未提交 | 旧声称 MISMATCH/UNKNOWN；新链依证据 | stale writer 停止；新链待激活则隔离 | DENIED | 旧 decision 不重基 / 当前链不清 | root revision/head、旧 expected A0、T |
| C18 当前 G12，旧 snapshot G9 恢复 | R12+备份旧证据 | A12 | D9 候选；误激活异常 | G12 COMMITTED；G9 未提交为当前 | 旧 G9 声称 MISMATCH | 候选只读；误激活 QUARANTINED(EVIDENCE_CONFLICT) | DENIED | 旧 T 不可重试 / 备份保留 | A12/R12、manifest/水位、registry |
| C19 Soul retirement fence 已提交，旧备份恢复 | Rret+旧链 | SoulRoot Aret 终态，所有 branch 保留只读头 | 旧 D0 候选或异常 active | SOUL_RETIRED lifecycle fact；不可回滚 | 旧实例声称 current→MISMATCH；缺证 UNKNOWN | RETIRED；异常激活另 QUARANTINED(EVIDENCE_CONFLICT) | DENIED | 不可重启 active / 旧候选不作新头 | Soul-level fence、Rret/decision、旧备份 ID |
| C20 `P`；A1+D1a 持久完成，回应前死亡 | R0+R1 | A1 | D1a 匹配 | COMMITTED | CONTINUATION | READY 仅供独立权限评估，不等于 Host active | DENIED（除非另行授权） | 同 T1 查询 / 已引用不清 | A1-R1-D1a、T1、parent、水位、版本 |

## Genesis CREATE 专项（G01–G06）

`CREATE` 初态是 `SoulRoot=ABSENT`，不是 C01–C20 的 `P/A0/R0`。受信 decision 固定 SoulId、main branch B0、`G1`、InstanceId、target DataGeneration Dg 与 `Tg`；Genesis Record 的 `parent kind=GENESIS / hash=NONE`。单个 durable SoulRoot CAS `expected=ABSENT → A_genesis(B0/G1/Rg)` 是 Genesis linearization point。以下 `CONTINUATION` 只证明从新 Genesis 起的合法 identity baseline，绝不证明 Host/执行许可。G 行中 `DENIED` 覆盖所有 Host/Living/delivery/REAL_SEND；均为 `PROTOCOL_SCENARIO`。

| ID / 故障点 | Record | Anchor / SoulRoot | Registry/Data | Persistence Fact | Identity Verdict | Operational State / recovery | 重试规则 | Authority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01 decision 已签发、候选准备前 crash | 无 Rg | ABSENT | 无 Dg active | ABSENT | UNKNOWN（无 baseline） | QUARANTINED(NO_BASELINE)；不得加载为 current Soul | 仅同 Tg、原 decision 仍有效并重检 root ABSENT 后重做 prepare | DENIED |
| G02 Rg durable、Anchor 仍 ABSENT crash | Rg 完整，parent=GENESIS/NONE | ABSENT | Dg candidate，不活动 | PREPARED，未提交 | UNKNOWN | QUARANTINED(PREPARED_ONLY)；不得激活 | 同 Tg 重新验证 decision/Dg/root 后 CAS；未引用候选可审慎清理 | DENIED |
| G03 Genesis CAS outcome unknown crash | Rg 完整 | ABSENT 或 A_genesis 或不可读 | Dg candidate | ABSENT→PREPARED；A_genesis→COMMITTED；不可读→INDETERMINATE | ABSENT/不可读→UNKNOWN；A_genesis 且证据全→CONTINUATION | A_genesis→QUARANTINED(ACTIVATION_PENDING)；不可读→QUARANTINED(EVIDENCE_CONFLICT) | 仅证明 ABSENT 且先前 CAS 已终结后同 Tg 重试；否则查询或停 | DENIED |
| G04 A_genesis 已提交、registry/data 未激活 crash | Rg 完整 | A_genesis | Dg candidate、registry 无新 active | COMMITTED | 完整证据下 CONTINUATION | QUARANTINED(ACTIVATION_PENDING)；按原 Tg 幂等激活，缺证改 UNKNOWN/EVIDENCE_CONFLICT | 同 Tg 仅尾步骤，绝不再 CAS 出 G2 | DENIED |
| G05 A_genesis 与 Dg activation 完成、ACK 丢失 | Rg 完整 | A_genesis | Dg active 且匹配 | COMMITTED | CONTINUATION | READY 只用于独立权限评估 | 同 Tg 读取已有结果，不增新 Soul/Instance/G | DENIED |
| G06 两个 CREATE 均以 SoulRoot ABSENT 竞争同 domain+SoulId | Rga/Rgb 候选 | 最多一个 A_genesis | 仅胜者 Dg 可激活 | 胜者 COMMITTED；败者 PREPARED/CAS_FAIL | 胜者证据全→CONTINUATION；败者 UNKNOWN | 败者停止/候选隔离；如双赢则 EVIDENCE_CONFLICT | 败者不得换 SoulId、选号或自动重基；需新受信 decision | DENIED |

`ENROLL` 可复用 expected-root-ABSENT 的持久 CAS 与 G01–G06 crash 形状，但 Record 必须是 `operation=ENROLL / parent=ENROLL_BASELINE/NONE`，绑定 legacy 数据来源与新的管理 decision。它只建立 **PROTOCOL ENROLLMENT BASELINE**，不把旧 `soul_id`/DB 或 enrollment 前历史升级为 **HISTORICAL CONTINUITY PROOF**；此前历史 verdict 保持 `UNKNOWN`。已有 root（含退休 fence）不能被 ENROLL 覆盖。

## FORK 专项（FK01–FK08）

初态：SoulRoot 未退休，source `B0/Gn/As→Rs` 完整，target branch `B1=ABSENT`；受信 fork decision 绑定 expected root revision、source head/hash/generation、target branchId/InstanceId、`Tf` 与目标 Df。Fork Record 的 parent 指向 source committed Rs，target branch 首代 `G1`（不是普通 Genesis parent）。唯一提交点是**同一 SoulRoot CAS**，同时验证 source head 仍预期、target BranchAnchor 仍 ABSENT、retirement fence 缺席，只新增 target branch head；B0/head、active branch 指定及 source Registry/Data 指针保持不变。目标激活只可写全新 target Instance/branch 指针；若现有 registry 无法表达，停止并标 `NEW_PRIMITIVE_REQUIRED`，不能覆盖 source。以下均为 `PROTOCOL_SCENARIO`，Authority 均 `DENIED`。

| ID / 故障点 | Record | Source / Target Anchor 与 SoulRoot | Registry/Data | Persistence Fact | Identity Verdict | Operational State / recovery | 重试规则 | Authority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FK01 source valid、target ABSENT、target record 前 crash | 无 Rf | source As；target ABSENT；未退休 | 无 Df active | target ABSENT | target UNKNOWN；source CONTINUATION | target QUARANTINED(NO_BASELINE) | 原 Tf/decision 有效且 source/root 重检后可准备 | DENIED |
| FK02 Rf durable、target Anchor ABSENT crash | Rf→Rs 完整 | source As；target ABSENT | Df candidate | target PREPARED | target UNKNOWN | target QUARANTINED(PREPARED_ONLY) | 同 Tf 重检 source/root/retirement 后 CAS；未引用候选可审慎清 | DENIED |
| FK03 source head 在 target CAS 前推进 | Rf 绑定旧 Rs | source As'≠As；target ABSENT | Df candidate | target PREPARED；CAS_FAIL | target UNKNOWN；新 source 依完整证据 | target QUARANTINED(EVIDENCE_CONFLICT)，停止 | 不得把 Tf 自动重基到 As'；须新管理 decision | DENIED |
| FK04 target CAS outcome unknown crash | Rf 完整 | source As/target ABSENT，或 source As/target Af，或 root 不可读 | Df candidate | ABSENT→PREPARED；Af→COMMITTED；不可读→INDETERMINATE | Af 且 evidence 全→FORK；其他 target UNKNOWN | Af→QUARANTINED(ACTIVATION_PENDING)；不可读→EVIDENCE_CONFLICT | 仅证实旧 root 且原 CAS 终结后同 Tf 重试 | DENIED |
| FK05 target Af 已提交、source branch 未变 | Rf→Rs 完整 | source As 原样；target Af；Soul 未退休 | Df candidate 或精确 active | target COMMITTED | FORK | candidate→QUARANTINED(ACTIVATION_PENDING)；精确 active→READY（仍非原 branch 当前执行者） | 同 Tf 只可完成尾步骤/查询，不得推进 B0 | DENIED |
| FK06 同一 Tf 重复请求 | 同一 Rf；异 payload 为冲突 | target ABSENT 或 Af | Df candidate/active | Af 同 hash→COMMITTED；ABSENT→PREPARED；冲突 INDETERMINATE | Af 完整→FORK；ABSENT/冲突→UNKNOWN | Af 未激活则 ACTIVATION_PENDING；冲突 EVIDENCE_CONFLICT | 同 payload/Tf 查询或原条件重试；异 payload 不可重试 | DENIED |
| FK07 同 target branchId 并发创建 | Rfa/Rfb | 同一 root CAS 至多一个 target Af | 仅胜者 Df 可激活 | 胜者 COMMITTED；败者 PREPARED/CAS_FAIL | 胜者完整→FORK；败者 UNKNOWN | 败者停止；双赢为 EVIDENCE_CONFLICT | 败者不得自动换 branchId 或 source | DENIED |
| FK08 Soul retirement 与 fork 创建竞争 | Rret 与 Rf | retire 先赢→Soul fence；fork 先赢→target Af、旧 retire expected revision 失效 | 旧候选保留，均不可自动激活 | 同一 CAS 至多一个 commit；败者未提交 | retire 胜→旧 fork UNKNOWN/旧实例 MISMATCH；fork 胜且证据全→FORK | retire 胜→RETIRED；fork 胜→target ACTIVATION_PENDING，retire 需新 decision | fork 败不得重试；retire 败不得自动重基，须纳入新 branch 重审 | DENIED |

## 特殊操作与一致性判定

- `RETIRE Soul`：C05–C08 的提交形状适用，但 CAS 更新的是 SoulRoot 的**全 branch** retirement fence，而非单一 branch head；Anchor 提交前旧头仍是已提交 lineage，提交后绝不因 registry 仍旧而准许任何 branch 运行。`BRANCH_RETIREMENT = OUT_OF_SCOPE`；不完整退役证据使 identity `UNKNOWN`、operational `QUARANTINED`，不能自动撤销 fence。
- `FORK`：按 FK01–FK08，只对受信、显式签发的新 target branch Record 和 SoulRoot 内 target BranchAnchor commitment 返回 `FORK`；同一 CAS 保证 source head 未变、target ABSENT、Soul 未退休。原 branch head 与 active branch 指定不变，不转让执行权。裸 COPY 只有相同 bytes、没有共同独立 authority 的情况下为 `UNKNOWN`；无跨机器 coordinator 不宣称 global uniqueness。
- `RESTORE / MIGRATION`：D1 准备必须包含旧备份校验、Memory 删除/Bridge 撤销控制重放、Living pause/fence 与目标 Schema 校验；这些是数据候选条件，不是执行许可。旧 binary 不理解协议时须在独立 admission 层拒绝，不能绕过矩阵。
- `same persisted bytes + same SoulRoot/BranchAnchor + same registry + same protocol version` 重复 recovery 的 persistence fact、identity verdict、operational state 必须相同。允许的尾步骤只依据原 decision 和已提交完整 evidence，完成后形成**新持久状态**；对完整已提交 lineage，activation 只改变 operational state，不把 identity `UNKNOWN` 升级为 `CONTINUATION`。墙钟、随机值、模型、Prompt、Host 文本一律不参与裁决。

## 后续 failure injection 合同（未实现）

每个 C01–C20、G01–G06、FK01–FK08 应有具名 hook 与可确定触发的断点；测试 runner 须在**新进程**恢复，保留 crash 前 record/SoulRoot/BranchAnchor/registry/data 原始证据和协议版本，分别验证 persistence fact、identity verdict、operational state、authority deny、是否允许同 `transition_id` 重放以及清理/隔离。C06/G03/FK04 至少分别注入旧值、新值、不可读值；C08 注入 registry 旧值、精确新值、第三值；C09–C14 是异常/损坏注入，不能因为“正常顺序不会出现”而省略。G06/FK07 要证明 single-winner，FK03/FK08 要证明 source-head 与 Soul retirement 同一 CAS 条件。每个 fixture 用无真实 Host/Provider 的合成 Soul、opaque relationship namespace 与隔离 Core；不得访问 REAL_SEND。实现与运行注入器需后续独立授权。
