# SP-006S0 — Soul Continuity Implementation Plan V1（Draft）

## 治理状态与阶段顺序

Execution Base = `5f04caf5050efb4742a8f6cb1f8546544d935b64`，仅表示本规划的审计基线，**不是**未来合并后的永久 canonical main。`SP-006S0 = AUTHORIZED / ARCHITECTURE_ONLY`；本文件是实施计划，不是任何实施授权。`M1 / M1.x / M2 = NOT AUTHORIZED`。Soul Continuity = `ACTIVE_MAINLINE`；Host Integration / Real Delivery = `DEFERRED`；Full Private RP = `FROZEN_EXTERNAL_BLOCKER`。与[架构合同](../architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md)和[验证矩阵](SP-006S0-CONTINUITY-VALIDATION-MATRIX.md)一起供独立 Draft Review。

正式顺序冻结为 `M0 SP-006S0 → M1 Soul Identity Core V1 → M1.x Continuity Proof / Simulation Gate → M2 Memory Evolution V1 + Read-only Prompt Projection → M3 Relationship / Autobiographical Memory → M4 Soul / Relationship Continuity Evolution + Living Integration → M5 Proactive Life / Routine + Media → M6 Voice + Host Expansion`。`M1.x` 保留为本版显式门禁名称；如需给实现任务编号，须在独立治理任务书冻结，绝不跳过此门。`SP-006S0` Draft PR、CI 或未来合并本身都不授权 M1。

## 共同边界与禁止的捷径

`Soul != Model`、`Soul != Host`、`Identity Continuity != Execution Authority`、`Recovery != Authorization`、`COPY != CONTINUATION`、`UNKNOWN = FAIL_CLOSED`。数据库恢复、模型自述、Prompt 名称、Host session 皆不是 Continuity Proof。World/Memory/Story/Living/Host Binding 维持各自真源；Continuity 仅存最小 lineage 证据。Original Soul 与 RP Character 分离，Soul World/RP World 默认隔离，Controlled Bridge 只能 explicit/bounded/authorized projection。`CLAIMED != SENT != ACKNOWLEDGED`，UNKNOWN 不自动重发。

现有冻结值保持：`DATA_SCHEMA = 8`、Living Runtime Signature = `SP-005A-living-runtime-v1`、Prompt Template Signature = `SP-004K-prompt-v1`、`PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES`。下述 schema 与 Prompt 扩展是**未来候选工作**，本 PR 不修改任何值、迁移、模板或 Runtime。若设计复核表明需要破坏 World 隔离、Controlled Bridge、authority、delivery 或 recovery 语义，立即 `ARCHITECTURE_CHANGE_REQUIRED = YES / STOP` 并单独裁定，而不是在实施 PR 中暗改。

## M1 — Soul Identity Core V1（NOT AUTHORIZED）

| 项 | 冻结计划 |
| --- | --- |
| Scope | 在现有 SoulId 上建立创建/不可变 identity、SoulInstance、SoulContinuityGeneration、creation/continuation lineage、timeline/relationship/authority binding；提供只读身份查询、受控创建/退役和导入校验。Character/Agent/World/Session/Model/Host ID 保持异类。不得在此阶段实现 Memory Evolution、Host 实测或真实发送。 |
| Dependencies | SP-006S0 独立架构审核及单独 M1 实施授权；复用 WorldScope、durable registry/restore fences、Memory/Bridge nonrollback controls；先确定本文件下方的持久化/anchor 决策。 |
| Schema impact | `SCHEMA_CHANGE_REQUIRED = YES`：需要最小 identity/instance/lineage 元数据与外部非回滚 anchor。Schema 8 不在本 PR 改动；后续独立 Schema/Migration 评审确定版本及 signature。 |
| Migration impact | 旧库不得仅由既有 `soul_id` 自动获当前 continuation。迁移应分类 legacy identity 为未证明状态，保留原 World/Memory/Story/Living 数据与隔离；生成新记录需要显式受控 enrollment。兼容只读访问，不发旧 permit。 |
| Test strategy | 隔离 Core 单元/持久化测试：identity 创建唯一性、不可变性、retirement、Scope/cardinality、instance 复制区分、generation 与 data/World/Living/Host 代次分离；迁移前后旧数据只读与失败原子性。无真实 Host/Provider。 |
| Entry gate | 本架构 Draft 独立核验、合并后 exact main CI，另发 M1 实施任务书；schema/anchor 方案经治理确认。 |
| Exit gate | 身份/实例/代次可机械读取与比较；创建/退役/恢复不会自动授予执行权；测试覆盖身份映射和 legacy 未证明态。此时仍**不得**宣称 Continuity Proof PASS。 |
| Stop conditions | 需要改写 World identity、把旧 permit 当身份、旧库自动确权、非文档治理未批准、Schema/Migration 范围超出独立授权。 |
| Risk / rollback | 新字段与旧库映射不唯一；双写/部分迁移可能造成幽灵实例。未来迁移应先备份、校验、可回退数据路径，但回退数据不得复活任何 authority；旧版本仅安全只读或暂停。 |

## M1.x — Continuity Proof / Simulation Gate（NOT AUTHORIZED）

| 项 | 冻结计划 |
| --- | --- |
| Scope | 实现四 verdict `CONTINUATION/FORK/MISMATCH/UNKNOWN`、最小 `SoulContinuityRecord` 与非回滚 `ContinuityAnchor` 的读取/推进/完整性检查、受控 copy/fork/restore/迁移转移、离线确定性 Continuity Simulation Harness。Core 无全局协调时 `UNKNOWN`。该阶段不接真实 Host 或执行发送。 |
| Dependencies | M1 独立验收、另发 M1.x 实施授权；以不含真实 Person 确权的 opaque relationship namespace 测试错误 lineage，跨机器全局协调缺失时返回 `UNKNOWN`。完整 PersonRef 留给 M3，不阻塞离线身份门禁。 |
| Schema impact | 若 M1 已提供足够 record/anchor 字段，仅补 index/约束；不足则必须另审 Schema。不得为方便建立第二套 World/Memory/Story 真源。 |
| Migration impact | 旧 backup/snapshot 的 lineage 位点按未知处理，不能因 restore 成功升级为 continuation；升级时保留非回滚 anchor 与旧分支撤销证据。 |
| Test strategy | 按[矩阵](SP-006S0-CONTINUITY-VALIDATION-MATRIX.md) S01–S16、S19–S20 逐项跑正负例、崩溃注入、复制、并发、损坏、旧 snapshot、不同 Model、模拟 Host 迁移；结构化 fixture 与可重复证据。绝不把 attempt/simulation 标为真实 Host PASS。 |
| Entry gate | M1 出口达成；record writer、anchor 原子协议、fork/authority 边界与失败语义确认；单独任务授权。 |
| Exit gate | fresh-process restart、backup restore、fork/copy、concurrent instance、model switch、simulated Host migration、stale incarnation、rollback resurrection 全部机械判定；缺证据 `UNKNOWN / FAIL_CLOSED`，任意 verdict 不自动赋权；达到 M2 进入门禁。 |
| Stop conditions | 只能凭 Prompt/Model/DB 恢复判断、离线伪称全局唯一、需要真实 Host 才能证明模拟 Core 合同、双实例可持同一有效权、任一负例被自动接受。 |
| Risk / rollback | anchor 与 record 崩溃窗口、复制的协调缺失、备份时点落后。未来变更应保留审计记录并使异常路径暂停执行；回滚实现不能回滚非回滚位点或复活旧许可。 |

## M2 — Memory Evolution V1 + Read-only Prompt Projection（NOT AUTHORIZED）

| 项 | 冻结计划 |
| --- | --- |
| Scope | 在现有 Memory 真源上逐步加入 Working/Episodic/Semantic 与 Relationship/Autobiographical 的类型及 ownership 边界、Consolidation/Deduplication/Conflict/Supersession/Importance/Decay/Controlled Forgetting/Retrieval。先实现经授权的基础 Memory 写入/纠正/遗忘，再将有可信来源的 Soul/World/Memory/Living 状态只读投影给模型；Relationship Context 仅在确权后进入投影，完整跨 World Relationship Memory 与 Autobiographical Memory 留给 M3。完整新 Prompt Runtime、SP-005A2-P1 与真实 Host 均非本阶段自动授权。 |
| Dependencies | M1.x Gate 独立验收；Memory truth、Story accepted event、Bridge Scope、Living authorization 均保持原 ownership。M2 基础不依赖完整 PersonRef；跨 World Relationship 读写/投影必须等 M3 的 PersonRef identity 与映射规则获单独冻结。 |
| Schema impact | 未来可能新增记忆类型、派生 lineage、失效索引及版本；必须逐项审查最小 schema/签名变更，不在此规划中实施。Prompt projection contract 尽量复用现有 PromptSnapshot/section/budget/revalidation，若模板升级须独立批准。 |
| Migration impact | 旧聊天摘要不能自动升级为权威事实；需带 provenance 分类、重新授权或留在非权威层。删除控制与派生/缓存/备份恢复的失效位点不可回退。 |
| Test strategy | S17/S18 与产品里程碑组合测试：事实纠正不再作为当前事实、受控遗忘后常规检索和 projection 不复活、旧 backup 恢复后仍受非回滚控制；跨 World/RP 隔离、budget trimming、revision/fingerprint/cache invalidation；模型生成摘要不得直接成为权威 Memory。离线模拟，不调用模型。 |
| Entry gate | M1.x 正负矩阵通过独立核验；另发 M2 授权、必要的 schema/Prompt 模板评审。 |
| Exit gate | 同一 Soul 重启后身份与记忆均经机械证据验证；纠正、遗忘和只读投影契约可测；`Prompt != Truth Source`，Living 不形成第二人格真源。 |
| Stop conditions | 绕过受控写入、遗忘不能传播至派生/缓存/投影、旧摘要复活、Runtime/Schema/Prompt 越过未授权边界、把 simulation 当 REAL_HOST_VALIDATION。 |
| Risk / rollback | 派生记忆与旧备份造成再污染；Prompt 缓存可能过期。未来回滚应停用失效投影、保留控制记录，不回退删除/失效位点；绝不以恢复旧库恢复发送许可。 |

## Schema 与迁移决策记录（仅设计）

`SCHEMA_CHANGE_REQUIRED = YES`，因为现有 Schema 8 的 `Soul.soul_id`、World/Memory/Story/Living/Host 各自 revision/epoch 不能表达独立的持久 SoulInstance、受控 ContinuityGeneration、创建/延续/fork 关系及非回滚比较锚点。最小新增实体是 `SoulContinuityRecord` 与与可复制数据库分离的 `ContinuityAnchor`；最小字段为 SoulId、InstanceId、lineage/branch ID、continuity generation、parent record hash/ID、状态、Scope/timeline binding 摘要、证据版本、writer authority reference、提交位点/完整性指纹以及 anchor 中的 SoulId、当前 branch/generation、单调序号/撤销位点。完整状态仍归原真源，anchor 不存 Memory/Story 正文。

迁移策略：先升级只读解析与兼容检查，再在单独授权下引入新 schema/存储、建立双侧一致性与 crash-recovery 测试，最后受控 enrollment/激活；旧库导入初始为 `UNKNOWN`，绝不自动签发 authority。回滚风险是旧二进制忽视新 anchor 或读取旧备份后重复激活，因此版本不兼容时必须暂停写入/发送、保留非回滚控制，并要求人工治理裁定。不得在 SP-006S0 修改 `DATA_SCHEMA = 8` 或运行 migration。

## 未决决定与交接

1. `OPEN_QUESTION_01`：跨机器全局唯一 continuation 的协调者与身份由谁提供？当前源码只证明单安装局部门禁。建议 Core 离线 `UNKNOWN`，未来 Host/coordination authority 独立审查；阻塞真实跨 Host 权限，不阻塞离线 M1.x 模拟合同。
2. `OPEN_QUESTION_02`：跨 World 的 `PersonRef` 如何与既有 Story CharacterInstance/WorldScope 映射并保护隐私？建议独立 Soul↔Person 稳定键与 explicit scope mapping；阻塞 M3 跨 World Relationship 实现，不阻塞 M1.x 离线身份 Gate 或 M2 基础 Memory。
3. `OPEN_QUESTION_03`：record 与非回滚 anchor 的原子提交、崩溃恢复与迁移介质是什么？建议先设计 fail-closed prepare/commit protocol 与故障注入；阻塞 M1.x 正式落地，需在 M1 Schema 设计前裁定。

三个问题的设计选项、证据和治理决策位置详见[架构文档的 Open Questions 小节](../architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md)。任何阶段需新授权；`SP-006S0 = DONE`（将来若达成）也不代表 `M1 = STARTED`。本轮终点仅为 Draft PR 独立审核。
