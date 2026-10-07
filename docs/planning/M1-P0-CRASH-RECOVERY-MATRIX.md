# M1-P0 — Crash / Recovery Matrix（设计，不是测试结果）

> 全部 C01–C20 均为 `PROTOCOL_SCENARIO`，**没有**任何场景标为 PASS；尚未实现 failure injection 或 continuity writer。依据[协议合同](../architecture/M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md)，后续实施准入见[实施门禁](M1-P0-IMPLEMENTATION-GATE.md)。范围只限单受信 authority domain；无共同协调者的跨机器行为为 `UNKNOWN / FAIL_CLOSED`。固定 fixture 重复 fresh-process recovery 必须得到相同分类、verdict 和隔离决定。

## 读表约定与必须收集的证据

每行的 `P` 是同一受信域中完整、已提交且未退役的旧状态：Anchor `A0` 指 Record `R0`、registry 指旧 `D0`；若旧态本身不完整，任何“OLD”路径改为 `UNKNOWN / QUARANTINED`。`R1` 为绑定唯一 `transition_id=T1`、expected `A0`、目标 `D1` 的 immutable 候选；`A1` 为经 durable CAS 提交的锚；`D1p` 为完整但不活动的数据候选，`D1a` 为 registry 已激活的新 data。`Q` = `UNKNOWN / QUARANTINED`、无 continuity 写/执行/Host/REAL_SEND；`OLD` = 旧 committed lineage 可读（旧执行权**不**由 recovery 复活）；`NEW` = 验证并完成精确激活后的新 lineage。即使 `CONTINUATION`，执行权限仍需 Host Binding/Living/delivery 独立授权。`—` 表示尚不存在；`?` 表示 torn/读不出，不允许猜测。

列中“分类/动作”必须以 fresh-process 重新读取的持久证据决定，不能用内存中的成功返回值。`旧头` verdict 只针对原 `R0`，`候选` verdict 针对 `R1`；未提交候选为 `UNKNOWN` 而不是已证明的 continuation。所有行证据等级均为 `PROTOCOL_SCENARIO`。未来注入器需能在指定边界确定性杀进程、另启进程、读取原始 persisted bytes/Anchor/registry/protocol version，并验证状态与副作用；当前无此实现。

| ID / 前态、操作、故障点 | Record 持久态 | Anchor 持久态 | Registry / Data 持久态 | Recovery 分类与动作 | Continuity verdict / Operational state | 执行权限 | 原 ID 重试？/ 清理？/ 隔离？ | 必需机械证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 `P`；CREATE/advance；获取 management lock 前崩溃 | `R0` | `A0` | `D0` | `OLD`；无新 transition | 旧头 `CONTINUATION` / 正常只读；候选不存在 | 不继承/不新增 | 重试须原 decision 仍有效；无候选可清；否 | `A0-R0-D0` 一致、锁不被旧进程持有 |
| C02 `P`；获锁后、重检前崩溃 | `R0` | `A0` | `D0` | `OLD`；下次重新获锁并重检，旧内存验证作废 | 旧头 `CONTINUATION`；候选不存在 | 不继承/不新增 | 原 decision 可重检；无；否 | `A0-R0-D0`、锁释放与新进程锁获取 |
| C03 `P`；重检后、候选准备前崩溃 | `R0` | `A0` | `D0` | `OLD`；不得凭先前重检直接提交 | 旧头 `CONTINUATION`；候选不存在 | 不继承/不新增 | 原 ID 重检；无；否 | expected `A0`、decision/T1、当前 `A0` |
| C04 `P`；候选 Record 持久化中崩溃 | `R0 + R1?`（无效/半写可检） | `A0` | `D0 + D1p` 或部分候选 | `OLD`；无完整 `R1` 不可 CAS；损坏候选仅隔离该候选 | 旧头 `CONTINUATION`；候选 `UNKNOWN` / candidate isolated | 不新增 | 只能原 ID 重新准备并校验；无引用候选可审慎清；旧态完整则不全局隔离 | `A0`、完整旧链、候选 hash/长度、T1、D1 digest |
| C05 `P`；`R1` durable、Anchor 尚旧时崩溃 | `R0 + R1` 完整 | `A0` | `D0 + D1p` | `OLD`；`R1` 是孤儿候选，未提交 | 旧头 `CONTINUATION`；候选 `UNKNOWN` | 不新增 | 原 decision 有效且重检后可用同 T1 CAS；未引用可清；否 | `R1` hash/parent/T1/decision、D1 完整、`A0` |
| C06 `P`；Anchor CAS 已开始但 durable outcome 未返回即崩溃 | `R0 + R1` | `A0` **或** `A1` **或** `?` | `D0 + D1p` | fresh-read：若 `A0` → C05；若完整 `A1` → C08；若 `?` → `Q`。不能凭 ACK 缺失推断。 | 按读回分类；不可读 `UNKNOWN / QUARANTINED` | 全部新权限拒绝 | 同 T1 仅在证实 `A0` 后可重试；不可读时不可清；`?` 必隔离 | 原始 Anchor 完整性/版本、expected `A0`、T1、R1 hash、CAS 证据 |
| C07 `P`；`A1` durable、调用方未收到成功即崩溃 | `R0 + R1` | `A1` | `D0 + D1p` | `NEW_COMMITTED / ACTIVATION_PENDING`；按原 T1 完成精确激活 | 激活前 `UNKNOWN / QUARANTINED`；后 `CONTINUATION` | 不自动授予 | 同 T1 查询/重放尾步骤；不能清 R1/D1；激活前是 | `A1→R1`、parent、T1、D1 digest、D0 expected registry |
| C08 `P`；Anchor 前进、registry/data 激活未完成崩溃 | `R0 + R1` | `A1` | `D0 + D1p`（或 activation 写入结果不明） | 先核对 registry；仍 D0 且 D1 完整则幂等激活；D1a 且匹配则确认；其他 `Q` | 完成前 `UNKNOWN / QUARANTINED`，确认后 `CONTINUATION` | 不自动授予 | 同 T1 幂等尾步骤；不可清；未确认前是 | `A1/R1/T1`、registry 原始 bytes、D1 digest/Schema/控制水位 |
| C09 `P`；故障注入使 registry/data 已新、Anchor 仍旧（协议禁止） | `R0 + R1?` | `A0` | `D1a` | `Q`；不能自动选新 registry 或回滚旧态，人工治理 | `UNKNOWN / QUARANTINED` | 全拒绝 | 禁止自动重试/清理；是 | `A0`、registry `D1a`、R1/decision 与可能副作用审计 |
| C10 `P`；故障注入 Anchor 指向缺失 Record | `R0`，`R1` 缺 | `A1→R1` | `D0` 或 `D1p` | `Q`；禁止从旧备份猜造已提交 Record | `UNKNOWN / QUARANTINED` | 全拒绝 | 否/否/是；人工治理 | Anchor hash/序号、Record store 缺失、所有受信副本来源 |
| C11 `P`；Anchor 指向损坏 Record | `R1` hash/结构损坏 | `A1→R1` | 任意 | `Q`；不得仅凭锚 hash 宣称 lineage 有效 | `UNKNOWN / QUARANTINED` | 全拒绝 | 否/否/是 | Anchor、Record bytes/hash/格式、保全日志 |
| C12 `P`；Record parent hash 与 `R0` 不符 | `R1.parent != hash(R0)` | `A1` 或尝试 `A1` | 任意 | 提交前应拒 CAS；若已出现则 `Q` | `UNKNOWN`（若明确异 Soul 可 `MISMATCH`）/ `QUARANTINED` | 全拒绝 | 否/否/是 | 完整 parent chain、hash、SoulId/domain、T1 |
| C13 `P`；Record sequence **大于** Anchor sequence 且未被锚引用 | `R1.seq > A0.seq` | `A0` | `D0 + D1p` | 仅完整、绑定同一 expected head 的下一步候选可按 C05；跨号/缺号 `Q` | 正常候选 `UNKNOWN`、旧头 `CONTINUATION`；跨号 `UNKNOWN / QUARANTINED` | 不新增 | 仅连续单步原 T1 可重试；安全孤儿可清；跨号隔离 | seq 连续性、T1、parent hash、锚引用集合 |
| C14 `P`；Record sequence **小于** Anchor sequence（旧记录冒充当前） | 只有 `R0` 或陈旧 `R1` | `A1`/更高 | `D0`/旧数据 | 若 Anchor 可找到完整新链，旧 record 判 stale；若缺新链则 `Q` | 旧声称 `MISMATCH`；缺链 `UNKNOWN / QUARANTINED` | 旧权限全拒绝 | 旧 T1 不可推进；旧记录不清；缺链隔离 | Anchor 当前 seq/hash、完整后继链、旧 record/Instance |
| C15 `P`；同一 `T1` 重复提交请求（含 lost ACK） | 同一 `R1` 或同 ID 不同 payload | `A0` 或 `A1` | `D0+D1p` 或匹配的 `D1a` | `A1` 且同 hash 返回同一结果；`A0` 重检后重试同 CAS；同 ID 不同 payload `Q` | 完整激活后 `CONTINUATION`；冲突 `UNKNOWN / QUARANTINED` | 不自动授予 | 同 ID 可；不同 payload 否；已引用不可清；冲突隔离 | T1 唯一性、decision/hash、Anchor、registry/target |
| C16 `P`；Writer A/B 基于 `A0` 竞争 | `R1a + R1b` 候选 | 至多一个 `A1a`/`A1b` | 仅 winner 目标可激活 | CAS winner 可按 C08；loser 必须读新头并停止，不能自动改基准 | winner 激活后 `CONTINUATION`；loser `UNKNOWN` 候选 | loser 无；winner 也需另授权 | loser 不能自动 retry；孤儿安全后可清；若双成功 `Q` | 两个 T/expected head、Anchor 原子 CAS 顺序、registry |
| C17 `P→A1`；旧 Writer 恢复后试图按 `A0` 写 | 旧候选 `R1old` + 新链 | `A1` | `D1a` 或 pending | expected-head CAS 失败；停止并 fresh-read，绝不覆盖新头 | 旧候选 `MISMATCH` 或 `UNKNOWN`；新链按完整性裁决 | 旧 writer 全拒绝 | 旧 decision 不可自动重基；不可清当前链；异常时隔离 | Anchor seq/hash、旧 expected `A0`、锁与 T 证据 |
| C18 `G12`；旧 snapshot DB `G9` 覆盖候选，外部 Anchor 仍 `G12` | 当前链 `R12`；备份含旧证据 | `A12` | `D9` 仅候选；若已 active 为异常 | `D9` 不可冒充 continuation；受控 restore 必须从当前头签新后继；误激活 `Q` | 旧数据声称 `MISMATCH`；误激活 `UNKNOWN / QUARANTINED` | 旧 permit/Host/Living 全拒绝 | 不可用旧 T 重试；备份只读保留；误激活隔离 | `A12/R12`、backup manifest/控制水位、registry/数据代 |
| C19 退役 fence 已由 Anchor 提交，随后恢复旧备份 | 退役 Record `Rret` 与旧链 | `Aret` 终态 | 旧 `D0` 候选或异常激活 | 永不恢复同 SoulId active；旧 registry/DB/Host 状态不得覆盖 fence | 旧声称 `MISMATCH`（缺证则 `UNKNOWN`）；运行拒绝/异常隔离 | 全拒绝 | 不可重启 active；旧候选不可当新头；异常是 | 不回滚 retirement fence、Rret/decision、旧备份 ID |
| C20 `P`；durable commit + Data activation 完成，回应 caller 前死亡 | `R0 + R1` | `A1` | `D1a` 匹配 | fresh-read 完整校验，按同 T1 返回已有收据/分类，不再递增 generation | `CONTINUATION` / 可进入独立权限评估；不等于 active Host | 无自动授予 | 同 T1 查询可；已引用不可清；否 | `A1-R1-D1a`、T1、parent、控制水位、协议版本 |

## 特殊操作与一致性判定

- `RETIRE`：C05–C08 的 `A1` 替换为不可回滚 `Aret`；Anchor 提交前旧头仍是唯一已提交 lineage，提交后**绝不**因为 registry 仍旧而准许旧实例运行。任何不完整退役证据为 `UNKNOWN / QUARANTINED`，不能自动撤销 fence。
- `FORK`：只对受信、显式签发的新 branch record 及 Anchor commitment 返回 `FORK`，原 active branch 不转让执行权。裸 COPY 只有相同 bytes、没有共同独立 authority 的情况下为 `UNKNOWN`；无跨机器 coordinator 不宣称 global uniqueness。
- `RESTORE / MIGRATION`：D1 准备必须包含旧备份校验、Memory 删除/Bridge 撤销控制重放、Living pause/fence 与目标 Schema 校验；这些是数据候选条件，不是执行许可。旧 binary 不理解协议时须在独立 admission 层拒绝，不能绕过矩阵。
- `same persisted bytes + same Anchor + same registry + same protocol version` 重复 recovery 的分类/判决/隔离必须相同。允许的尾步骤只依据原 decision 和已提交完整 evidence，完成后形成**新持久状态**；不得因 recovery 次数改变结论。墙钟、随机值、模型、Prompt、Host 文本一律不参与裁决。

## 后续 failure injection 合同（未实现）

每个 C01–C20 应有具名 hook 与可确定触发的断点；测试 runner 须在**新进程**恢复，保留 crash 前 record/anchor/registry/data 原始证据和协议版本，验证 verdict、operational state、authority deny、是否允许同 `transition_id` 重放以及清理/隔离。C06 至少分别注入旧值、新值、不可读值；C08 注入 registry 旧值、精确新值、第三值；C09–C14 是异常/损坏注入，不能因为“正常顺序不会出现”而省略。每个 fixture 用无真实 Host/Provider 的合成 Soul、opaque relationship namespace 与隔离 Core；不得访问 REAL_SEND。实现与运行注入器需后续独立授权。
