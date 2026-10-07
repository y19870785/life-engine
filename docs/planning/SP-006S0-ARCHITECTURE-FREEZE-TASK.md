# SP-006S0 — Soul Continuity 架构冻结任务书（候选）

## 任务状态与目的

Roadmap Stage: Soul Continuity Mainline / Architecture Freeze。
Why Now: GOV-SOUL-ROADMAP1 已确立主线，现有状态系统需要明确身份连续性、机械证明与记忆闭环的合同，避免先堆叠实现再补架构。

状态：`TASK_DRAFT / NEXT / NOT AUTHORIZED`。本轮只编制并提交规划文档，不启动 SP-006S0。Planning Governance Base 为 `11b5e51ea0033351b6d21cc56a75caa665a8cb4f`，只指本规划开工前的固定基线；正式发布任务时须重新核验当时的 canonical main、CI 与明确授权，不能把此 SHA 写成永久 post-merge main。Base 漂移时 STOP，不能自行换 Base 或 rebase。

SP-006S0 将来获授权后的范围仅为源码/合同只读审计、架构文档和验证计划；不实现 Runtime、不升级 Schema、不修改真实 Prompt、不操作 Host。完成架构冻结也不等于 Soul Continuity 产品能力已实现。

## 开工阅读与现状证据

阅读 README、[长期路线](LIFE-ENGINE-DEVELOPMENT-ROADMAP.md)、[后续开发计划](SOUL-CONTINUITY-DEVELOPMENT-PLAN.md)、[三轨治理](../architecture/GOV-SOUL-ROADMAP1-SOUL-CONTINUITY-MAINLINE.md)、[World](../architecture/SP-004A-WORLD-DOMAIN-MODEL.md)、[Memory](../architecture/SP-004B-WORLD-MEMORY.md)、[Story](../architecture/SP-004C-STORY-RUNTIME.md)、[持久化](../architecture/SP-004E-WORLD-SQLITE-PERSISTENCE.md)、[Bridge](../architecture/SP-004F-CONTROLLED-WORLD-BRIDGE.md)、[Prompt](../architecture/SP-004K-PROMPT-RUNTIME.md)、[Living](../architecture/SP-005A-LIVING-RUNTIME.md)和[Host Binding](../architecture/SP-005A2-LIVING-HOST-BINDING.md)合同，并只读核对对应源码和测试。

按“已实现且有证据／仅合同已定义／缺口／本阶段不做”分类，附文件、符号、测试或历史证据位置。不能凭 README、阶段名或旧 PASS 推断更高能力。保持 `DATA_SCHEMA = 8`、`Schema Signature = SP-005A-living-runtime-v1`、`Prompt Template = SP-004K-prompt-v1`、`PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES`；未来变更只提出设计与理由。

## 必须冻结的六种 Continuity

| 维度 | 必须回答的问题 |
| --- | --- |
| Identity Continuity | 我是谁；Soul ID、incarnation 和 creation / continuation lineage 如何建立与区分？ |
| Temporal Continuity | 为什么昨天、今天、正常重启或恢复后的状态属于同一条生命时间线？ |
| Experience Continuity | 发生过的事件如何成为该 Soul 的历史，如何与 Story 事实和模型叙事区分？ |
| Memory Continuity | 经历如何记住、纠正、覆盖、衰减、受控遗忘及检索？ |
| Relationship Continuity | 共同经历、信任和关系变化如何跨时间持续，如何追溯来源？ |
| Execution Continuity | 换进程、模型或 Host 后，谁有权继续代表该 Soul，旧执行权何时失效？ |

Soul Identity 必须独立于 Agent、Character、Host、Session、Model Identity；它也不等于 Prompt 或 World。模型是推理/认知引擎，Host 是执行/交付环境。换模型、TTS 或 Host 不应单独创建新 Soul，也不能单凭名称或角色卡证明延续。

## 必须解决的架构问题

| 主题 | 必须明确的合同 |
| --- | --- |
| 身份与绑定 | SoulIdentity、SoulInstance、SoulContinuityGeneration 的职责；Soul ID、incarnation / generation、creation / continuation lineage、timeline / relationship / authority binding；与 Agent、Character、World、Session、Model、Host 的基数和关系 |
| 生命周期 | 创建、正常/进程重启、升级、备份与快照恢复、复制、分叉、迁移、退役的状态转换、合法调用方、来源依据、拒绝条件和可观察结果 |
| 代次与执行权 | 新连续性代次如何映射既有 data generation、World revision、Host epoch；不得默认等同；恢复或迁移不得复制旧 permit、capability 或执行资格 |
| 连续性 verdict | 机械判断 `CONTINUATION`、`FORK`、`MISMATCH`、`UNKNOWN` 的输入、证据、稳定性与失败模式；`UNKNOWN` 默认 fail-closed，不自动升级为 continuation |
| 连续性证据 | 评估 Continuity Ledger、Proof、Continuation Record、Generation Chain、Lineage Evidence 的必要性、最小字段与替代方案；说明新实例凭什么继续某个 Soul，双实例声称同一 Soul 时如何处理，避免再造覆盖 World/Memory/Story 的统一真源 |
| 可信边界 | 本地数据复制、旧快照回退、并发副本、缺失/损坏记录、离线无法证明全局唯一性时，明确 UNKNOWN、拒绝或隔离边界 |
| 记忆闭环 | 事件、事实、待跟进事项的来源、Subject/World 可见性、冲突、supersession、删除和派生内容失效；区分原始内容、模型总结、关系解释与 Story 事实 |
| 最小只读投影 | authority、provenance、projection boundary、budget、read-only semantics，以及版本、section ordering、裁剪、fingerprint / integrity、缓存与 revision invalidation；Prompt 声明不能授予 authority |
| 恢复与遗忘 | 删除控制状态、旧备份、缓存、摘要、自传和跨 World 投影的相互作用；不完整恢复的拒绝/隔离；审计不保留被删除正文 |
| 关系与自传 | 固定身份、共同经历、关系状态、自我叙事和表达变化的真源；模型总结不得直接成为事实或改写 Soul |
| Host / Model neutrality | Core 无真实 Host、无模型网络调用也能验证；模拟迁移与真实 Host 验收分开，Host 差异只归 Adapter / Binding |

Original Soul 不得被 RP 覆盖；Soul World / RP World 默认隔离，Controlled Bridge 只提供显式授权的有界投影。Lore、Memory、Story、Prompt、Bridge、Living、Host Binding 真源和权限继续分立。`CLAIMED != SENT != ACKNOWLEDGED`；Recovery != Authorization；UNKNOWN 不自动重发。

## M1.x Continuity Proof / Simulation Gate 设计

本阶段必须把 M1 Soul Identity Core V1 与 M2 Memory Evolution V1 之间的 Continuity Proof / Simulation Gate 写成独立进入/退出门，不得只留在研究问题清单。`M1.x` 是语义占位；最终编号由本架构冻结决定，不预设 M1.5 或某个 SP 号。没有机械 continuation 证据，不得以数据库恢复、Prompt 自称、Character name、Model response、Host session 或主观判断进入大规模 Memory Evolution。

Continuity Simulation Harness 的设计应尽可能 Host-neutral、Model-neutral、offline-testable，并在可能处 deterministic。最低矩阵分别覆盖 normal restart、fresh-process restart、backup restore、snapshot restore、model switch、process migration、simulated Host migration、fork / copy、concurrent instance、stale incarnation、rollback resurrection、wrong Soul import、wrong timeline binding、wrong relationship lineage。逐项规定预期 verdict、证据缺口与 fail-closed 结果。模拟不得依赖真实 Hermes、OpenClaw、Discord、Provider 或 REAL_SEND；Core 模拟 PASS 不能写成真实 Host PASS。

## 必须交付的文档与决策

正式执行时预期提交 `docs/architecture/SP-006S0-SOUL-CONTINUITY-ARCHITECTURE.md`、`docs/planning/SP-006S0-CONTINUITY-VALIDATION-MATRIX.md` 和 `docs/planning/SP-006S0-IMPLEMENTATION-PLAN.md`；它们是计划产物，本任务书提交时尚未创建或标注 DONE。

架构合同包含现状复用/缺口矩阵、对象与权限关系、生命周期转换、verdict 与证据能力/局限、持久化和兼容迁移影响、Prompt / Memory 依赖决策、必要 ADR 与未决问题。是否新增 Schema、Ledger 或接口须提出具体理由和最小方案，本任务书不预定实现。

验证矩阵逐项列前置状态、输入、预期状态变化或拒绝结果、机械证据、证据等级和对应实施阶段。本阶段只设计矩阵，不运行新 Runtime 或 Host 验证。

实施拆分必须明确 M1 Identity Core、M1.x Continuity Proof / Simulation、M2 Memory Evolution 与 Read-only Prompt Projection 的顺序、进入/退出 Gate、迁移风险和停止条件。M0 只冻结最小 Prompt Projection Contract，M2 才形成可信状态的只读投影；完整 `SP-005A2-P1` 不因本规划获得授权。M3～M6 只保留必要依赖，不提前冻结实现细节。

## 首个产品里程碑与后续边界

首个产品里程碑同时验证 Identity Continuity 与 Memory Continuity：重启后仍是同一个 Soul 且仍记得；纠正后不再把旧说法当当前事实；受控遗忘后不再正常召回；fork / stale incarnation / wrong restore 不能冒充合法 continuation；model switch 不改变 Soul Identity；simulated Host migration 后仍能证明 continuation。确定性状态、检索、投影与 verdict 证据同模型表达体验分开，架构场景描述不算实现 PASS。

Relationship Memory 不等于普通 Semantic Memory；共同经历、关系变化和自传式解释要保留来源。既有 Living Core 后续应消费 Soul Identity、Memory、Relationship、Living State，而非另建人格真源。Media 将来可成为 Soul Life Event，Voice 是 Soul Expression Layer；这些都不在本阶段实施。

Host Integration / Real Delivery 仍 `DEFERRED`。只有官方 final-output commit、reliable delivery authority、稳定 principal/session、replay/late-result fencing 等实质能力变化，才进入独立 Host Governance Review；本阶段不自动恢复 A2 retry 或 HLV4-B。Full Private RP 仍 `FROZEN_EXTERNAL_BLOCKER`，H1/H2 不因本规划重启。

## 禁止范围、停止条件与独立审核

不修改 Python、测试语义、Schema、数据库、Prompt 模板、workflow、Host Adapter、provider transport；不启动 Gateway、读取凭据、安装插件、建立 cron、制造 inbound、执行 REAL_SEND 或调用真实模型、ComfyUI、语音 Provider。本任务书不授权 SP-006S0 正式开工。

若最小方案必须改变既有 World 隔离、Bridge、authority、delivery/recovery 合同，须提交影响与替代方案并 `STOP / ARCHITECTURE_CHANGE_REQUIRED`。Base 漂移、设计必须触碰真实 Host 或生产数据、真源冲突无法消除时同样停止。

将来正式执行 SP-006S0 时，交付实际 Base/Head、复用/缺口矩阵、设计决策及未决问题、文档链接检查、范围检查和 exact PR Head CI。达到可审状态后先建 Draft PR；作者自检不等于独立审核。Ready、Squash Merge、canonical main 和 exact main push CI 分别按独立授权推进；本阶段 DONE 不自动启动 M1。
