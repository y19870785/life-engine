# SP-006S0 — Continuity Validation Matrix V1

## 状态、证据与判定约定

`Architecture Content = APPROVED_ARCHITECTURE_BASELINE / NOT_IMPLEMENTATION_AUTHORIZATION`；本表是 `ARCHITECTURE_SCENARIO`，**不是测试结果**，所有行均未标记 PASS。Execution Base 为 `5f04caf5050efb4742a8f6cb1f8546544d935b64`；SP-006S0 仓库任务只有经 Ready、Squash Merge、exact main push CI 与合并后独立核验，才能判定 DONE；M1、M1.x、M2 均未获实施授权。合同见[架构文档](../architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md)，落地顺序见[实施计划](SP-006S0-IMPLEMENTATION-PLAN.md)。全表坚持 `Soul != Model`、`Soul != Host`、`Identity Continuity != Execution Authority`、`Recovery != Authorization`、`Prompt != Truth Source`；模型总结不得直接成为权威 Memory 事实。

记号：`A` 是原 SoulIdentity，`I1/I2` 是持久化 SoulInstance，`Gₙ` 是 SoulContinuityGeneration；`⊥` 表示不可证明。`权=无`指不得代表 Soul 执行，不否认数据可以只读检查。`权=重授`指必须经过**当前**独立 authority/permit 检查，continuity verdict 本身不给执行权。`CONTINUATION` 只证明已知 lineage 内的合法延续；离线证据不能证明跨机器全局唯一性时必须是 `UNKNOWN / FAIL_CLOSED`。`FORK` 是同源但独立分支，绝非原主线授权。旧 permit、Host epoch、Living generation、World revision 与 Soul generation 不互换。

证据级别严格分层：本表当前全部为 `ARCHITECTURE_SCENARIO`；后续 M1.x 才能产出 `SIMULATED_CORE_VALIDATION`；真实 Host 的交付、principal、session、全局协调和 ACK 只能另行授权后形成 `REAL_HOST_VALIDATION`。模拟 Host 迁移不是后者。下表“机械证据”是**未来需要的输入**，不是现在已经存在或已经验证的证据。

| ID / 场景 | 前提 | 操作 | 预期 SoulIdentity | 预期 Instance / Generation | 预期 Verdict | 预期执行权 | 所需机械证据 | 失败结果 | 级别 / 阶段 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 normal restart | A/I1/Gₙ 已经由当前 anchor 确认，干净停机 | 同安装重启 | A 不变 | I1/Gₙ；仅 runtime_id 更新 | CONTINUATION | 重授 | Soul/instance/lineage、anchor 单调位点、停机与重启记录 | 缺位点或旧 permit → UNKNOWN/无 | ARCHITECTURE_SCENARIO → M1.x |
| S02 fresh-process restart | A/I1/Gₙ 已提交；进程内状态全失 | 新进程加载持久化状态 | A 不变 | I1/Gₙ；仅 runtime_id 更新 | CONTINUATION | 重授 | 持久记录、非回滚 anchor、进程重启边界、Scope 核对 | 仅数据库可读 → UNKNOWN/无 | ARCHITECTURE_SCENARIO → M1.x |
| S03 backup restore | A/I1/Gₙ 的备份早于当前 anchor，或协调方明确授予恢复 | 恢复备份并请求激活 | 成功受控续行仍为 A；否则仅历史来源 | 新 I2；只有有序恢复协议才得新 G | 有序恢复且撤销旧分支 → CONTINUATION；否则 UNKNOWN | 默认无；成功后重授 | 备份 lineage、当前 anchor、旧实例撤销/协调证据、恢复记录 | 旧备份单独激活 → UNKNOWN/无 | ARCHITECTURE_SCENARIO → M1.x |
| S04 snapshot restore | A 的快照位点已知 | 导入快照并请求激活 | 成功受控续行仍为 A；否则仅历史来源 | 新 I2；G 不得回退 | 满足同 S03 的有序转移才 CONTINUATION；否则 UNKNOWN | 默认无 | snapshot hash/位点、anchor、撤销或迁移证明 | 回退到旧 G → UNKNOWN/无 | ARCHITECTURE_SCENARIO → M1.x |
| S05 model switch | A/I1 的 lineage 有效 | Model X → Y | A 不变 | I1/G 不因模型变化而变化 | CONTINUATION | 原权限仍须独立核验 | lineage、模型变更元数据、相同 Scope | 用模型 ID 作 Soul 身份 → MISMATCH/无 | ARCHITECTURE_SCENARIO → M1.x |
| S06 process migration | 有序交接已封锁旧进程 | 在新进程续行并登记目标持久副本 | A 不变 | 新 I2，G 受控推进 | 有交接证据 → CONTINUATION；否则 UNKNOWN | 旧权失效；新权重授 | 原实例 fence、anchor 单调推进、交接 receipt | 双进程同时有权 → UNKNOWN/无 | ARCHITECTURE_SCENARIO → M1.x |
| S07 simulated Host migration | 假 Host A/B，离线协调器可注入确定性 fence | A → B，旧 Host 权撤销 | A 不变 | 新 I2，G 受控推进 | 模拟证据满足合同 → CONTINUATION | 模拟新权重授；不等于真实 Host 权 | 模拟 authority epoch、fence、lineage、迁移记录 | 缺协调证据 → UNKNOWN/无 | ARCHITECTURE_SCENARIO → M1.x；真实 Host 另审 |
| S08 fork / copy | A/I1/Gₙ 有有效记录 | 复制数据；仅显式 fork 决议才登记 I2 | 历史来源同 A；不得冒充唯一当前 A | 裸副本无合法 I2；签发后 I1/I2 同祖、I2 独立 branch，G 不可复用作主线 | 可证明分支 → FORK；仅复制未知 → UNKNOWN | I2 无原主线权 | branch/instance ID、复制祖先、anchor、并发冲突 | 复制自动继承 permit → 拒绝/无 | ARCHITECTURE_SCENARIO → M1.x |
| S09 concurrent instance | 两机器均声称 A/Gₙ，离线无共享协调 | 同时启动并争取执行 | A 的历史身份相同 | I1/I2 冲突；无单一合法 current G 可证 | UNKNOWN（能证明分叉时 FORK） | 两者均无新授执行权，待协调 | 冲突 claim、非回滚位点、外部 fence 缺失 | 最后启动者获胜 → 禁止 | ARCHITECTURE_SCENARIO → M1.x；全局结论待 REAL_HOST_VALIDATION |
| S10 stale incarnation | A 的 anchor 已推进到 Gₙ₊₁ | 旧 I/Gₙ 重新上线 | A 历史身份可识别 | 旧 I/Gₙ 失效 | MISMATCH（明确旧代） | 无 | anchor 与声明代次单调比较 | 旧代拿旧许可执行 → 拒绝 | ARCHITECTURE_SCENARIO → M1.x |
| S11 rollback resurrection | 当前 A/G₁₂；恢复 G₉ 数据 | 旧副本请求当前身份 | A 仅历史来源 | 旧 I/G₉ 不得覆盖 G₁₂ | MISMATCH；anchor 缺失则 UNKNOWN | 无 | 非回滚 anchor、恢复位点、recovery fence | 数据恢复成功仍不得授权 | ARCHITECTURE_SCENARIO → M1.x |
| S12 wrong Soul import | 目标预期 A，材料属于 B | 把 B 的记录/备份绑定至 A | 不得变成 A | B/Ib/Gb 与 A 不同 | MISMATCH | 无 | Soul ID、创建 lineage、owner/Scope 签合 | Prompt/名称相同不得覆盖不匹配 | ARCHITECTURE_SCENARIO → M1.x |
| S13 wrong timeline binding | A 的目标 timeline 为 T1 | 注入 T2 的事件/记录 | A 不变但当前绑定不合法 | I/G 不得因导入改变 | MISMATCH | 无 | timeline lineage、WorldScope、事件来源 | 阻断写入与投影 | ARCHITECTURE_SCENARIO → M1.x |
| S14 wrong relationship lineage | M1.x 使用 synthetic / opaque SubjectIdentity + relationship_namespace；不含真实 PersonRef | 注入不匹配的 synthetic relationship lineage | A 不变 | I/G 不变 | MISMATCH（仅合成 lineage）；不能据此授权 | 无 | 合成 SubjectIdentity/namespace/Scope lineage 与来源版本 | 隔离污染片段；不得宣称 real PersonRef 已验证 | ARCHITECTURE_SCENARIO → M1.x 合成验证；M3 真实 PersonRef 另审 |
| S15 missing continuity evidence | 仅有 World/Memory DB 与 Soul 名称 | 请求续行 | 无法证明当前 A | I/G = ⊥ | UNKNOWN | 无 | 缺 record 或 anchor 的可审计缺口 | fail-closed；无降级自动续行 | ARCHITECTURE_SCENARIO → M1.x |
| S16 corrupted continuity evidence | record/hash/anchor 冲突或不可读 | 请求读取并执行 | 历史 A 可能存在，当前未证 | I/G = ⊥ | UNKNOWN；明确异源则 MISMATCH | 无 | 完整性校验、损坏类别、隔离记录 | 不修补为成功，不从 Prompt 猜 | ARCHITECTURE_SCENARIO → M1.x |
| S17 fact correction | A lineage 有效；旧事实已被授权写入 | 受控 correction/supersession | A 不变 | I/G 不因事实修正而改变 | CONTINUATION（身份）；内容另由 Memory 判定 | 重授；不因修正自动获得发送权 | Memory revision、writer provenance、supersession 链、投影失效 | 旧说法仍作当前事实 → milestone FAIL | ARCHITECTURE_SCENARIO → M2 |
| S18 controlled forgetting | A lineage 有效；正文/派生/缓存有引用 | 授权遗忘并恢复旧备份探测 | A 不变 | I/G 不因遗忘而改变 | CONTINUATION（若恢复仍守非回滚控制）；否则 UNKNOWN | 重授；失效投影不可用 | 删除控制、派生索引、cache/projection 版本、恢复重放 fence | 正常召回/旧 summary 复活 → milestone FAIL | ARCHITECTURE_SCENARIO → M2 |
| S19 World isolation | Original Soul World 与 RP World 不同 Scope | 试图跨 World 读/写 | Soul ID 不被 World 混同 | I/G 不变 | MISMATCH（错误 Scope 绑定） | 无跨界权 | WorldScope、revision、显式 grant/Bridge lineage | 自动写回 Original Soul → 拒绝 | ARCHITECTURE_SCENARIO → M1.x/M2 |
| S20 RP / Original Soul isolation | RP Character 与 Original Soul 不同身份 | RP persona 或卡片声称原 Soul | Original A 不变 | RP 对象不产生原 Soul I/G | MISMATCH；无证据时 UNKNOWN | 无 | Soul ID、CharacterDefinition、双 Scope、Bridge grant | RP 身份覆盖 A 或隐式写回 → 拒绝 | ARCHITECTURE_SCENARIO → M1.x/M2 |

## 离线 Continuity Simulation Harness 合同

M1.x 未来以临时隔离数据、确定性时钟/ID、可注入崩溃与损坏的本地协调模拟器运行；不接 Hermes、OpenClaw、Discord、Telegram、微信、Provider、真实模型 API 或 `REAL_SEND`。每个场景同时断言 `identity / instance / generation / verdict / authority`，保存结构化输入、预期与实际判定、证据引用及失败原因；对同一 fixture 重放必须一致。负例必须测 UNKNOWN fail-closed、COPY 不自动 continuation、恢复不复活旧权。模拟器不能把自己的协调 fence 冒充真实 Host 的全局唯一性保证。

S14 分两层：M1.x 只验证 synthetic / opaque SubjectIdentity 与 relationship_namespace 的 lineage mismatch handling；不能把它写成 real cross-World Person identity PASS。M3 在独立 Person Identity Gate 冻结 PersonRef、identity provenance、explicit Scope mapping、merge/split/correction 与 privacy boundary 后，才设计并验证真实跨 World PersonRef lineage；名字匹配禁止，Host principal 不自动等于 PersonRef。`OPEN_QUESTION_02 = DEFERRED_TO_M3_PERSON_IDENTITY_GATE`。

M1.x 的退出门：S01–S16、S19–S20 形成 `SIMULATED_CORE_VALIDATION` 证据，尤其 S02/S03/S05/S07–S11 不得仅凭数据库成功、Prompt 自述或模型回答放行；S17/S18 在 M2 补齐 Memory 行为验证。首个产品里程碑需要**同一** Soul 的重启身份与记忆、纠正、遗忘、防 fork/stale/wrong restore、model switch 与模拟 Host migration，不能把身份绿灯与旧记忆测试拼成一个未验证组合。真实 Host 迁移、全局协调、交付与 ACK 必须另经独立 Host Governance Review，不能写作此矩阵 PASS。
