# Soul Continuity 后续开发计划

## 地位、基线与授权

Roadmap Stage: Soul Continuity Mainline / 已审阶段规划基线。
Why Now: GOV-SOUL-ROADMAP1 已确立主线，需要将长期目标细化成可验收的身份、连续性证明、记忆、关系与生活体验闭环。

Planning Governance Base 为 `11b5e51ea0033351b6d21cc56a75caa665a8cb4f`（PR #47 的 Squash commit）；它只标识本规划开工前的固定基线，不声明未来合并后的 canonical main。Soul Continuity Plan V2 已通过独立规划审核，状态为 `APPROVED_PLANNING_BASELINE / NOT_EXECUTION_AUTHORIZATION`。**HISTORICAL SNAPSHOT — 规划编制时的 SP-006S0 生命周期：**其审计基线为 `5f04caf5050efb4742a8f6cb1f8546544d935b64`；[架构合同](../architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md)、[验证矩阵](SP-006S0-CONTINUITY-VALIDATION-MATRIX.md)与[实施计划](SP-006S0-IMPLEMENTATION-PLAN.md)的内容曾获 `APPROVED_ARCHITECTURE_BASELINE / NOT_IMPLEMENTATION_AUTHORIZATION`；当时仓库任务仍需 Ready、Squash Merge、exact main push CI 与合并后核验，M1/M1.x/M2 均未获授权。这是当时真实状态，不作为当前授权声明。

**CURRENT stage override：**`SP-006S0 = DONE`（其 Execution Base 仍是上述历史审计 SHA）；`M1 = ACTIVE_STAGE`；仅 [M1-P0 Continuity Persistence Protocol Freeze](../architecture/M1-P0-CONTINUITY-PERSISTENCE-PROTOCOL.md) 为 `AUTHORIZED / PROTOCOL_FREEZE_ONLY`。该 Gate 的[Crash / Recovery Matrix](M1-P0-CRASH-RECOVERY-MATRIX.md)及[Implementation Gate](M1-P0-IMPLEMENTATION-GATE.md)均只设计，不实施。M1 Schema、Migration、Record/Anchor writer、SoulInstance enrollment、M1-A 及后续实施、M1.x、M2 全部 `NOT AUTHORIZED`。

[GOV-SOUL-ROADMAP1](../architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md)的三轨治理继续有效：Soul Continuity = `ACTIVE_MAINLINE`；Host Integration / Real Delivery = `DEFERRED`；Full Private RP = `FROZEN_EXTERNAL_BLOCKER`。本文补强原规划的 Continuity Proof / Simulation Gate，不覆盖既有 World、Memory、Story、Living、Host authority 或 delivery 安全合同。

## 长期目标与当前起点

Life Engine 是 Host-neutral、Model-neutral 的长期 Personal Agent Runtime。Soul 跨会话、跨日、进程重启、模型变化及未来 Host 迁移，应保留可审计的身份、时间线、经历、记忆、关系、自我叙事、偏好、Persona / Values、Living State 与连续性证据。`Soul != Model`，`Soul != Host`，也不等于 Session、Character Card、Prompt 或 World。模型是 Inference / Cognitive Engine；Host 是 Execution / Delivery Environment。换模型只在连续性合同成立时才可解释为同一个 Soul 更换认知引擎，不能靠模型自称建立身份。

复用现有 World、World Memory、Lore、Story、Prompt、Controlled Bridge、Character Import、Living、Host Binding 和 A2-R1 provider transport。它们各有真源；小雪只是一个使用实例，Runtime 不绑定特定角色、模型、渠道或宿主。已有本地实现不等于真实部署完成；新 Living 链路的真实 plugin load、delivery boundary、SENT、ACK 仍未取得，2026-09-30 的历史单次发送不能升级为当前 Living 验收。

Host-neutral 方向保持为 `Life Engine → Host Adapter Contract → Hermes / OpenClaw / Future Agent Host / Self-hosted Host`。Host 差异归 Adapter / Binding；Life Engine 不演变为单一 Host 插件。Core 的连续性验证不依赖真实 Host 或 provider network。

## 建议阶段与完成门

M0～M6 是规划语义标签，不是新 SP 编号或执行授权。`M1.x` 仅表示 M1 与 M2 之间不可跳过的 Gate；正式编号由 SP-006S0 Architecture Freeze 冻结，本规划基线不预定 M1.5、SP-006S1 或 SP-006S2。SP-006S0 的已完成架构文档不延伸授权 M1 Runtime、M1.x 或 M2 实施；当前仅 M1-P0 文档 Gate 获单独授权。

| 里程碑 | 工作范围与依赖 | 必须交付的能力或证据 |
| --- | --- | --- |
| M0：SP-006S0 Soul Continuity Architecture Freeze | 审计既有真源与缺口；冻结六种 Continuity、身份/实例/代次、恢复/分叉、M1.x 证据与最小 Prompt Projection Contract | 架构合同、生命周期转换、复用/缺口矩阵、Continuity verdict 与证据能力边界、Simulation Harness 计划、验证矩阵和实施切片；`SP-006S0 = DONE`，不自动授权 Runtime |
| M1：Soul Identity Core V1 | 依赖 M0；建立 Soul ID、incarnation / generation、creation / continuation lineage、timeline / relationship / authority binding；复用现有持久化但不混同代次 | Soul Identity 独立于 Agent、Character、Host、Session、Model；重启、恢复、复制和迁移有可核对的身份与来源状态，旧执行权限不随恢复继承 |
| M1.x：Continuity Proof / Simulation Gate | 依赖 M1，且必须先于大规模 Memory Evolution；建立机械 verdict、证据与离线模拟验收 | 对合法 continuation 与 fork、mismatch、unknown 作机械区分；缺证默认 fail-closed；规定并发声称和离线不可判定的处理；通过最低场景矩阵后才进入 M2 |
| M2：Memory Evolution V1 + Read-only Prompt Projection | 依赖 M1.x 与 M0 的最小投影合同；先完成有来源的最小记忆闭环，再按证据扩展记忆演化 | 记录→持久化→检索→只读投影→纠正/遗忘；Identity、Memory、World、Relationship Context 安全投影；跨会话、跨日、重启、隔离、缓存失效均有机械证据 |
| M3：Relationship Memory + Autobiographical Memory | 依赖 M2；共同经历、关系演进与有来源的自我叙事 | 固定身份、共同历史、模型总结与 Story 事实分立；关系变化可追溯，虚构经历不冒充事实，RP 不覆盖 Original Soul |
| M4：Soul / Relationship Continuity Evolution + Living Integration | 依赖稳定的身份、记忆与关系状态；复用既有 Living Core，真实体验另受 Host Gate 约束 | Living 消费同一个 Soul 的 Identity、Memory、Relationship、Living State；主动行为不由独立 scheduler 假装成人格 |
| M5：Proactive Life / Routine + Media Runtime | 依赖 M4；情境产生意图，Living 决定执行资格；媒体成为 Soul Life Event | daily greeting、follow-up、routine、important date 等有上下文依据；图片受 location、time、weather、activity、relationship、recent event、persona 影响；生成、artifact、发送、receipt 分开 |
| M6：Voice Runtime + Host Expansion | 依赖稳定的文本与媒体连续性及独立 Host 治理 | Voice 是 Soul Expression Layer；换 TTS / Voice Provider 不改变 Soul Identity；各 Host / Provider 单独验收，不由 Core 模拟结果推导真实交付 PASS |

### M0 必须冻结的连续性与投影边界

SP-006S0 至少分别回答六个问题：Identity Continuity（我是谁）；Temporal Continuity（昨天、今天、重启后的我为何在同一时间线）；Experience Continuity（发生过的事如何成为我的历史）；Memory Continuity（如何记住、纠正、覆盖、衰减与遗忘）；Relationship Continuity（关系如何跨时间发展）；Execution Continuity（换进程、模型或 Host 后谁有权代表这个 Soul）。六者不能由单一 Prompt、数据库恢复成功或 Host session 代替。

M0 同时冻结 Minimal Prompt Projection Contract：authority、provenance、projection boundary、budget、read-only semantics，并评估版本、section ordering、裁剪、fingerprint / integrity 与 revision invalidation。M0 不实现完整新 Prompt Runtime。M2 才从可信的 Identity + Memory + World + Relationship Context 派生只读投影；完整 `SP-005A2-P1 = NOT AUTHORIZED`，不得用 legacy prependContext 或普通 tool output 冒充正式投影。

### M1.x Continuity Proof / Simulation Gate

Life Engine 必须机械判断新运行实例是否为原 Soul 的合法 continuation。Prompt 自称、Character name、Model response、Host session 或单纯主观判断都不是证明。SP-006S0 应评估并冻结 verdict contract，推荐至少有 `CONTINUATION`、`FORK`、`MISMATCH`、`UNKNOWN`；`UNKNOWN` 默认 fail-closed，绝不自动解释为 `CONTINUATION`。它还须决定 Continuity Ledger、Continuity Proof、Continuation Record、Generation Chain、Lineage Evidence 是否需要及各自最小职责，回答新实例凭什么继续某个 Soul，以及双实例同时声称同一 Soul 时如何处理。命名和持久化方案留待架构冻结，不在本规划中预定 Schema。

Continuity Simulation Harness 应尽可能 Host-neutral、Model-neutral、offline-testable，并在可能处确定性验证：同一 Soul 经 normal / fresh-process restart、model switch、process migration、simulated Host migration 后的合法延续；以及 backup / snapshot restore、fork / copy、concurrent instance、stale incarnation、rollback resurrection、wrong Soul import、wrong timeline binding、wrong relationship lineage 的拒绝、分叉或 UNKNOWN 结果。模拟不调用真实 Hermes、OpenClaw、Discord、Provider 或 REAL_SEND；模拟迁移只能提供 Core 证据，不能冒充真实 Host 验收。无法离线证明的全局唯一性须明确能力边界，而不是猜测为成功。

### M2 与 M3 的记忆边界

Memory 不是保存更多聊天记录，而是 Soul 对经历长期组织、巩固、修正、遗忘和重新理解的机制。Memory Evolution 长期覆盖 Working、Episodic、Semantic、Relationship、Autobiographical / Self Memory，以及 Consolidation、Deduplication、Conflict、Supersession、Importance、Decay、Controlled Forgetting、Retrieval。M2 先交付最小可验证闭环，不一次完成所有排序和衰减策略；具体存储、删除及检索语义另行冻结。

Relationship Memory 不等于普通 Semantic Memory。它应保留 shared experiences、relationship history、trust evolution、important corrections、互动中学到的偏好、relationship milestones 和关系特定上下文，使 Soul 知道“我们共同经历过什么”。Autobiographical / Self Memory 应逐步形成 life events、important experiences、self interpretation、关系里程碑、随时间变化的理解与 personal narrative；它不是 conversation summary，模型生成的叙事也不能未经核验成为 Story 事实。

## 首个 Soul Continuity 产品里程碑

首个里程碑同时验证 Identity Continuity 与 Memory Continuity：重启后仍是同一个 Soul 且仍记得；事实纠正后不再把旧说法当当前事实；受控遗忘后不再正常召回；fork、stale incarnation、wrong restore 不能冒充合法 continuation；model switch 后 Soul Identity 不变；simulated Host migration 后仍能证明 continuation。数据库成功恢复不等于 Soul Continuity PASS，模型说“我记得”也不是机械证据。

场景还应覆盖跨会话/跨日、事实冲突、原始记录及派生摘要/缓存失效、World / Subject 可见性、RP 隔离、备份恢复和删除控制状态。删除控制与审计不能继续暴露已忘正文；不承诺清除控制域外的第三方历史或模型已有知识。缺少必要删除控制状态的旧备份应如何拒绝或隔离，由 M0 冻结。

## Host 回归与 Full Private RP

M2 完成时可做只读 Host 缺口盘点；只有出现 official final-output commit boundary、reliable delivery authority、stable principal / session identity、replay fencing、late-result fencing 等实质新证据，才可提出独立 Host Governance Review。Hermes / OpenClaw 的小幅变化不自动恢复 Host 主线。获新授权后才可从既有 A2-R1 成果继续 A2 retry、HLV4-B 与 Adapter Stabilization；真实发送及跨日自动调度分别授权。Host 仍受阻时，记录缺口并继续可离线完成的 Core 工作，不能伪造 M4 的真实体验 PASS。

Full Private RP 保持 `FROZEN_EXTERNAL_BLOCKER`；H1/H2 blocker、RP Core 与历史审计证据保留。只有实质官方 Host 能力证据可触发新 source audit 与独立评审。Living delivery authority 不等于 Full Private RP final-output commit authority。

## 开发与审核节奏

每个实施切片写清固定 Base、实际体验、依赖、范围、禁止范围、验证证据、停止条件及可回滚边界，按可验收结果推进，不预设完成日期。流程保持 Draft PR → 独立审核 → 明确授权 Ready → 轻量终审 → 明确授权 Squash Merge → exact main push CI → 独立核验 → DONE。作者自检、PR CI、Merge 均不自动升级下一阶段授权；失败或取消的 CI 重试需当次明确授权。

[SP-006S0 架构冻结任务书候选](SP-006S0-ARCHITECTURE-FREEZE-TASK.md)记录本规划获批时的历史候选状态；后续独立授权已指定架构任务 Execution Base `5f04caf5050efb4742a8f6cb1f8546544d935b64`，不沿用本规划编制 Base，也不授权 M1 实施。
