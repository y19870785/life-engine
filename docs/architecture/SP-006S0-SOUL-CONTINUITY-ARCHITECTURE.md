# SP-006S0 — Soul Continuity Architecture Freeze V1

## 状态与范围

`Architecture Content = APPROVED_ARCHITECTURE_BASELINE / NOT_IMPLEMENTATION_AUTHORIZATION`；Execution Base = `5f04caf5050efb4742a8f6cb1f8546544d935b64`（规划 PR #48 的合并提交，**不是**本 PR 将来的 post-merge main）。独立 Draft Review 已通过架构内容；但 SP-006S0 仓库任务只有经 Ready → Squash Merge → exact main push CI → 合并后独立核验，才能判定 DONE，DONE 也不授权 M1。本文件不宣称功能已实现或测试 PASS。`M1 / M1.x / M2 = NOT AUTHORIZED`；Host Integration / Real Delivery = `DEFERRED`，Full Private RP = `FROZEN_EXTERNAL_BLOCKER`。Soul Continuity = `ACTIVE_MAINLINE`，规划方向为 `APPROVED_PLANNING_BASELINE / NOT_EXECUTION_AUTHORIZATION`。

设计前提：`Soul != Model`、`Soul != Host`、`Soul != Session`、`Soul != Prompt`、`Soul != Character Card`、`Soul != World`。模型是推理引擎，Host 是执行/交付环境。Soul 组织 Identity、Timeline、Experience、Memory、Relationship、Self Narrative、Preferences、Persona / Values、Living State 和最小 Continuity Evidence；它不吞并这些子系统的真源。`Identity Continuity != Execution Authority`、`Recovery != Authorization`、`COPY != CONTINUATION`、`Database Restore != Soul Continuity`、`UNKNOWN = FAIL_CLOSED`。

相关规划：[后续开发计划](../planning/SOUL-CONTINUITY-DEVELOPMENT-PLAN.md)、[验证矩阵](../planning/SP-006S0-CONTINUITY-VALIDATION-MATRIX.md)、[实施计划](../planning/SP-006S0-IMPLEMENTATION-PLAN.md)。以下源码、测试、迁移只读审计，不在本阶段修改或运行 Host。

## Current Runtime Reuse / Gap Matrix

| 领域及代码/测试证据 | 当前可证明的边界 | 结论与后续最小工作 |
| --- | --- | --- |
| World：[domain.py](../../runtime/life_engine/domain.py)、[world_runtime.py](../../runtime/life_engine/world_runtime.py)、[world_schema.py](../../runtime/life_engine/world_schema.py)、[test_world_runtime.py](../../tests/test_world_runtime.py) | `Soul(soul_id,owner_id,soul_world_id)`、一 World 归一 Soul、完整 `WorldScope`、独立 World revision / WriterEpoch、SessionBinding；同一 World 至多一个 OPEN Session。现有 `soul_id` 不是创建/延续/退役证明。 | `REUSE` Soul/World/Scope ID 与围栏；`NEW_CONTRACT_REQUIRED` SoulInstance、continuity lineage、Soul 级 timeline/retirement；`DO_NOT_REUSE` WriterEpoch 作 Soul 代次。 |
| Durable：[durable.py](../../runtime/life_engine/durable.py)、[test_durable.py](../../tests/test_durable.py) | registry 的 instance/data generation、备份、新 generation 原子切换；restore 重放 Memory/Bridge 控制并暂停联系。复制出的数据库与旧 generation 可保留，不能证明唯一合法继续者。 | `REUSE` copy/verify/management lock 与 restore pause；`EXTEND` 安装外的非回滚 lineage anchor 和激活门；`DO_NOT_REUSE` data generation 当 continuity generation。 |
| Memory：[memory.py](../../runtime/life_engine/memory.py)、[memory_runtime.py](../../runtime/life_engine/memory_runtime.py)、[memory_control.py](../../runtime/life_engine/memory_control.py)、[test_memory_restore.py](../../tests/test_memory_restore.py) | 精确 Scope、audience、来源/canon、独立 collection revision、supersession、隐藏/删除及备份外删除控制；`SourceType.BRIDGE` 和跨 Scope lineage 当前被拒绝。 | `REUSE` 原始 Memory 真源和删除控制思想；`EXTEND` 受控派生、关系/自传及失效；`DO_NOT_REUSE` 模型总结为事实、Memory revision 为 Soul 代次。 |
| Lore：[lore_runtime.py](../../runtime/life_engine/lore_runtime.py)、[test_lore_runtime.py](../../tests/test_lore_runtime.py) | 固定书版本、Scope 绑定和激活结果；背景素材不自动成为经历。 | `REUSE` 来源版本/投影；`DO_NOT_REUSE` Lore 为 Experience/Story 真源。 |
| Story：[story.py](../../runtime/life_engine/story.py)、[story_runtime.py](../../runtime/life_engine/story_runtime.py)、[test_story_runtime.py](../../tests/test_story_runtime.py) | 显式 accepted event、独立 StoryRevision/Clock、可重放投影；首版关系是同 Scope CharacterInstance 对，非跨 World 的 Soul↔Person 关系。 | `REUSE` 已接受事件历史；`NEW_CONTRACT_REQUIRED` 跨时间 Relationship identity；`DO_NOT_REUSE` StoryClock 当 Soul 年龄或会话时间。 |
| Bridge：[bridge_runtime.py](../../runtime/life_engine/bridge_runtime.py)、[bridge_control.py](../../runtime/life_engine/bridge_control.py)、[test_bridge_runtime.py](../../tests/test_bridge_runtime.py) | 明确 grant、双 Scope、来源版本/lineage、撤销控制、只读有界投影；不自动写入目标 Memory/Story。 | `REUSE` 默认隔离与显式投影；`DO_NOT_REUSE` Bridge grant 为 Soul 身份或无界数据同步。 |
| Character Import：[import_ir.py](../../runtime/life_engine/import_ir.py)、[import_cards.py](../../runtime/life_engine/import_cards.py)、[test_import_cards.py](../../tests/test_import_cards.py) | 导入固定版本 CharacterDefinition；卡片/名称是表达素材。 | `REUSE` presentation 来源；`DO_NOT_REUSE` 卡片 fingerprint、角色名作 Soul ID。 |
| Prompt：[prompt.py](../../runtime/life_engine/prompt.py)、[prompt_runtime.py](../../runtime/life_engine/prompt_runtime.py)、[test_prompt_runtime.py](../../tests/test_prompt_runtime.py) | 不可变只读 PromptSnapshot，typed authority/section、budget、fingerprint 和来源重验；模板 `SP-004K-prompt-v1`。 | `REUSE` 最小投影机制；`EXTEND` 后续 Soul/Relationship section 需独立权限/版本合同；`DO_NOT_REUSE` Prompt 文本作真源/授权。 |
| Living：[living_runtime.py](../../runtime/life_engine/living_runtime.py)、[living_recovery.py](../../runtime/life_engine/living_recovery.py)、[test_living_runtime.py](../../tests/test_living_runtime.py)、[test_living_recovery.py](../../tests/test_living_recovery.py) | Soul World Scope、durable generation、policy/day/revision、已保留 Intent 与 Attempt；授权先于 receipt，`CLAIMED != SENT != ACKNOWLEDGED`，UNKNOWN 不自动重发。 | `REUSE` Living 状态/发送门禁；`EXTEND` 将可信 Soul/Memory/Relationship 状态作为输入；`DO_NOT_REUSE` Living generation 为 Soul 身份。 |
| Host Binding：[living_host_binding.py](../../runtime/life_engine/living_host_binding.py)、[living_host_capability.py](../../runtime/life_engine/living_host_capability.py)、[test_living_host_binding.py](../../tests/test_living_host_binding.py) | 安装/Host/session 绑定、authority/plugin epoch、短时 capability/permit、reload 撤销；当前真实 Host plugin/delivery/ACK 未验收。 | `REUSE` 局部执行权门禁；`NEW_CONTRACT_REQUIRED` 未来真实迁移/跨节点协调；`DO_NOT_REUSE` Host epoch、permit 为 continuity proof。 |
| Schema/迁移：[world_schema.py](../../runtime/life_engine/world_schema.py)、[test_schema8_migration.py](../../tests/test_schema8_migration.py) | 当前 `DATA_SCHEMA = 8`、`SP-005A-living-runtime-v1`；升级只在新 data generation 副本。 | `EXTEND` 未来新增最小 lineage 实体及副本迁移；本 PR **不改** Schema/迁移。 |
| 跨机器协调与跨 World Person identity：当前代码/测试无共同受信协调者或稳定 PersonRef 真源 | 单安装的 World/Host fence 不能外推为全局唯一，Story 同 Scope CharacterInstance 不能外推为现实 Person。 | `UNRESOLVED`：真实跨 Host 唯一性与 PersonRef 确权分别进入 `OPEN_QUESTION_01/02`；不能以名称、时间戳或本地文件假定答案。 |

审计结论：现有 `soul_id` 能标记归属，但缺少不可回滚的合法 continuation 链、copy/fork 判别及退役状态。现有 Host Binding 解决单安装当前调用权限，不证明跨机器唯一性。该缺口可通过**新增有界合同**处理，不需要改写 World/Bridge/Host Safety 真源；`ARCHITECTURE_CHANGE_REQUIRED = NO`。跨机器全局唯一性为 `OPEN_QUESTION_01 = ACCEPTED_CAPABILITY_BOUNDARY`：无共同受信协调者时 `UNKNOWN / FAIL_CLOSED`，不阻塞 M1 或离线 M1.x 模拟，但阻塞真实跨机器 continuation/Host 迁移与多节点双活。若实施审计发现必须改变冻结语义，立即 `STOP / ARCHITECTURE_CHANGE_REQUIRED`，不得以本文件作为默许。

## Soul Identity、Instance 与代次

| 概念 | Owner / purpose | 生命周期、持久性、比较及权限含义 |
| --- | --- | --- |
| `SoulIdentity` | Soul 领域；沿用现有 `DomainId(IdKind.SOUL)` 与 Owner 绑定，不引入第二个 Soul ID | 创建时唯一、不可变；不因模型、Host、Session、World 切换而改变。导入只能建立显式新 Soul 或带证据的受控恢复；退役为不可回滚终态，不重用 ID。**ID 相等仅是必要条件，不是合法 continuation 充分证据。** |
| `SoulInstance` | Continuity 层；一个已登记的持久副本/安装附着，不等于进程 runtime_id 或 durable instance_id | 一 Soul 可有多个 Instance（候选、fork、退役），同一进程重启保留该持久 Instance ID，但产生新进程 runtime_id；恢复/复制/迁移目标须登记新 Instance ID。未经登记的裸副本保持 `UNKNOWN`，不得自报为当前实例。 |
| `SoulContinuityGeneration` | Continuity 层；有向合法 lineage 上的单调序号 + parent record hash | 仅受信激活/显式 fork/handoff 推进；normal/fresh restart、model switch 不推进。新 data generation 不自动推进它；相同数字在不同 branch 不可比较，须同时比 `SoulIdentity + lineage head + authority domain`。不授予发送权。 |
| `DataGeneration` | durable registry；物理业务状态副本 | restore/upgrade 可改变，重启通常不变；用于数据路径与旧上下文围栏，不证明 Soul lineage。 |
| `WorldRevision / WriterEpoch` | World；聚合 CAS 与单 World writer/session 围栏 | World 级持久值；不跨 World 比较，不代表 Soul 代次。 |
| `LivingGeneration` | LivingRoot；与 durable generation 绑定的业务执行围栏 | restore 后旧 Context/Intent 失效；它不是 SoulIdentity 或 continuity generation。 |
| `HostEpoch` | Host Binding authority/plugin；当前服务/插件凭据围栏 | reload/restart 撤销旧 handle；局部、短时、不持久代表 Soul lineage。 |
| `ExecutionAuthority` | 当前受信 Core/Host 管理者；具体操作资格 | 必须独立验证当前 Scope/session、data generation、Host epoch、capability/permit 与 policy；永不因 Soul verdict 为 `CONTINUATION` 自动授予。 |
| `Session / Model / Host Identity` | 各自边界的会话、推理引擎、交付环境元数据 | 可变；可入审计/经历来源，但不参与 Soul ID 等值判断，也不能签发 lineage。 |

`SoulInstance` 不是 WorldRuntime 已有 `Soul`、durable `instance_id` 或一进程 `runtime_id` 的别名。一个 `SoulIdentity` 允许 `1:N` 历史 Instance，但在**一个受信 authority domain** 中至多一个当前 continuation head；显式 fork 后另成 branch，不自动继承原 Soul 当前执行权。跨 authority domain 无协调时无法证明全局唯一性，判 `UNKNOWN` 并隔离。

### Binding / Cardinality

| 关系 | 冻结约束 |
| --- | --- |
| Soul → Agent | 首版一个 Soul 绑定一个受信部署 Agent principal/Owner 管理域；Agent ID 不等于 Soul ID。多 Agent 代理同一 Soul 需后续独立 authority 合同。 |
| Soul → Character presentation | `1:N` 可版本化表达；CharacterDefinition/Instance 不能改变 SoulIdentity。RP Character 仍在其 World/Scope。 |
| Soul → World / World → Soul | Soul 可有默认 Soul World 加多个 RP World；当前 World 行恰归一个 Soul。跨 Soul 共用 World 不在 V1 范围。 |
| Soul → SoulTimeline / WorldTimeline | 首版一 Soul 一条 canonical SoulTimeline lineage，可显式 fork 出 branch；各 World 可有自己的 WorldTimeline ID，不能直接当 SoulTimeline。绑定须携 Soul ID、branch、WorldScope 与来源。 |
| Soul → Session | 历史 `1:N`；当前同一 World 最多一个 OPEN Session（现有 WorldRuntime 约束）。跨 World 可能有不同 Session，但不能因此推导并发执行权；新 Soul 级执行者仍受 authority fence。 |
| Soul → Model / Host | 生命周期中 `1:N` 使用记录，同一可信操作绑定一个当前配置；切换不改变 SoulIdentity。真实 Host 迁移另需独立 Host 授权。 |
| Soul ↔ Relationship | 稳定关系 key 为 `SoulId + SubjectIdentity + relationship_namespace`；World/Session/Model/Host 是可选来源与 facet，不是关系根 ID。当前无可信跨 World `Person` 注册真源，SubjectIdentity 的确权留 `OPEN_QUESTION_02`；未确权者不得合并关系。 |

## Six Continuities 与真源

| 维度 | 机械依据及边界 |
| --- | --- |
| Identity | `SoulId`、Owner、creation record、合法 parent chain；不看名字、模型输出或卡片。 |
| Temporal | 有序 continuation record 与 SoulTimeline branch；墙钟、StoryClock、WorldTimeline tick 各有用途，不互为替代。 |
| Experience | 受信来源与显式接受的事件才进入历史；Story 是 scoped accepted-event 真源，Memory 记录可含经历候选；Prompt 表达不使事件发生。 |
| Memory | MemoryRuntime 管原始记录、audience、supersession 与删除控制；长期 consolidation/decay 另需受控写入，不复制到 Continuity 层。 |
| Relationship | `SoulId + SubjectIdentity` 的关系 lineage，保留共同经历、纠正、信任、里程碑与来源；当前 Story 同 Scope 角色关系不是跨 World Soul↔Person 真源。 |
| Execution | lineage 合法与否只回答“是不是同一 Soul”；当前执行还须独立 authority、generation、Session/Host fence。不能由 `CONTINUATION` 推出发送资格。 |

## Continuity Evidence、verdict 与信任边界

**决定 AD-01：需要最小 `SoulContinuityRecord` + 不随业务备份回退的 `ContinuityAnchor`；不建 Memory/Story/Living 的超级账本。** Record 只存 `format/version, SoulId, Owner/authority-domain ID, InstanceId, branch ID, continuity generation, parent record hash, operation, SoulTimeline binding, optional relationship namespace/version digest, source/target data-generation reference, issuer/decision ID, monotonic sequence, evidence digest, state (candidate/active/fork/retired), record hash`。不存聊天、Memory 正文、Story payload、关系正文、Prompt 或模型输出。`ContinuityProof` 是对当前 chain/anchor/来源校验的只读派生报告，不是新真源或 bearer token。

受信 Owner/安装管理 authority 才能写 creation、restore、fork、handoff、retire record；普通 Runtime、模型、Host 文本只可提交候选输入，不能签发。Reader 可在 Core 内验证精确 Soul/Instance/branch/anchor/版本后得到 verdict；Host 只收窄后的只读判断，不读取敏感内容。Append-only，禁止就地改 parent、序号或判决；新的纠错/退役为后继记录。Anchor 持当前 head/sequence/hash/retirement fence，存于业务备份恢复域之外。`OPEN_QUESTION_03 = ACCEPTED_WITH_PRE_M1_WRITE_GATE`：M1 获独立授权后，必须先完成 [M1-P0 Continuity Persistence Protocol Freeze](../planning/SP-006S0-IMPLEMENTATION-PLAN.md)，经独立 gate 审核，才可实现任何 continuity record/anchor 写路径、激活或 active-state migration。M1-P0 须冻结受信 management lock、record/anchor prepare→commit 顺序、DB/registry/anchor 崩溃不一致的隔离与幂等恢复；在此之前不预定生产存储技术。部分提交不等于 continuation，DB 成功不等于 anchor 成功，anchor 成功不等于执行权；崩溃歧义返回 `UNKNOWN / QUARANTINE`，绝不猜测成功。

现有 Memory deletion control 与 Bridge revoke control 可作为**模式**但不是同一 authority：它们的安装身份/序列/哈希不能替 Soul 决定 lineage。未经认证的本地文件、备份内复制的 anchor 或仅有 HMAC 不证明对抗同 OS 用户恶意复制；V1 的可信边界是受信安装管理域与离线模拟权威。跨机器全局唯一性、真实 Host 权限另需协调/外部 authority；缺失时 `UNKNOWN`。损坏、缺字段、未知版本、断链、序号回退、锚缺失/不匹配均 fail-closed 并保留脱敏诊断。业务备份不得覆盖当前 anchor；退役不可被旧备份复活。

**决定 AD-02：verdict 为四值。** `CONTINUATION`：同一 Soul/branch、有效 parent chain、当前 anchor 指向候选，且所需操作证据齐全；只证明身份延续。`FORK`：有效共同祖先 + 有证据的独立 branch/Instance；不占原 branch 的当前 head。`MISMATCH`：可证的 Soul/Owner、SoulTimeline、relationship namespace、parent lineage 不同，或当前 anchor 明确证明所声称的 generation 已过期。`UNKNOWN`：缺证、损坏、未协调复制/并发或无法确认当前 head；默认 `FAIL_CLOSED`，不得映射为 `CONTINUATION`。Fork 不是 Mismatch；对已知同源但未授权创建的并行副本可标 `FORK`（来源事实）同时拒绝原 branch 执行权；无法证明来源则 `UNKNOWN`。

**决定 AD-03：COPY 与并发。** 文件 copy 不签发新 Instance/record；若两个进程持相同文件/Instance ID，只有一个受信 anchor/CAS 当前 head 有资格成为本 authority domain 的 continuation，另一方 `UNKNOWN`/隔离。已显式签发 fork record 的副本得 `FORK`；不得“最后启动者获胜”。若两台机器各复制了可写的本地 anchor，离线 Core 不能知道另一方存在，**不能声称全局唯一**；没有共同受信协调时两方均不得取得跨域 continuation/Host 执行资格。模拟 harness 必须注入复制/并发并验证这一限制。

**决定 AD-04：rollback。** `Generation 12 → restore Generation 9` 只产生待审数据候选；anchor 仍指向 12。旧快照中的旧 Session、capability、permit、Host epoch、Living Intent/Attempt 不恢复执行资格。受信恢复可在完成 Memory/Bridge 控制重放、差异审计和暂停/协调后签发新 Instance/后继 record；否则 `UNKNOWN`。退役 anchor 阻止任何旧备份复活原 Soul；显式新 Soul 导入必须新 ID，不能覆盖旧 lineage。

## Lifecycle State Machine

状态：`UNREGISTERED → CANDIDATE → ACTIVE`；`ACTIVE → SUSPENDED_FOR_RECONCILIATION / FORKED / RETIRED`；损坏、失锚或竞争为 `QUARANTINED`。只有受信管理 authority 可激活/退役；`QUARANTINED` 无自动出边，须人工审核新证据。下表的“执行权”均指**现有资格不得继承**，重新签发仍须独立 Host/Core Gate。

| 操作 | SoulId / Instance / ContinuityGeneration | 必需证据与失败处理 | 旧执行权 |
| --- | --- | --- | --- |
| CREATE | 新 / 新 / 0 | Owner creation、唯一 SoulId、初始 anchor；重复/冲突拒绝 | 无 |
| NORMAL_RESTART / FRESH_PROCESS_RESTART | 不变 / 同持久 Instance，新 runtime_id / 不变 | 当前 anchor + 完整链 + data generation、World 恢复与新会话 fence；缺失 `UNKNOWN` | 全部失效，重新授权 |
| UPGRADE | 不变 / 同 Instance / 不变 | 受信新 release 与副本迁移、Schema 验证、anchor 核对；失败候选隔离 | 旧 token/permit 失效 |
| BACKUP | 不变 / 不变 / 不变 | 含 source generation 与 record head 的清单；备份只是证据快照，不签发 continuation | 不复制 |
| RESTORE / SNAPSHOT_RESTORE | 不变 / 新 Instance / 待批准后推进一代 | 当前外部 anchor、备份清单、删除/撤销控制、差异审计与协调；旧/缺锚 `UNKNOWN` | 不继承，默认 paused |
| COPY | 不变 / 未登记副本无合法 Instance / 不变 | 仅相同数据不足；同源可证且分支被明确登记才 `FORK`，否则 `UNKNOWN` | 无 |
| FORK | 同源 SoulId + 新 branch / 新 Instance / branch 新代；若将来需作为独立 Soul 运行，必须另行显式创建新 SoulId | 受信 fork 决议、parent hash、独立 anchor；不可占原 head | 原权限不复制 |
| MODEL_SWITCH | 不变 / 不变 / 不变 | 当前链 + 受信配置变更；模型元数据只供审计 | 依当前执行门重验 |
| PROCESS_MIGRATION | 不变 / 目标新 Instance / 受信 handoff 后推进 | 源端撤销、目标确认、共同 anchor/CAS；无协调 `UNKNOWN` | 源权限撤销，目标另签 |
| HOST_MIGRATION | 不变 / 目标新 Instance / 受信 handoff 后推进 | Core 模拟可用合成 coordinator；真实 Host 尚无验收/授权，不能仅凭模拟放行 | 目标 Host 权限另审 |
| RETIRE | ID 不复用 / 全部 Instance 退役 / 锚记终态 | Owner 决议 + 不可回滚退役 fence；旧备份 `UNKNOWN`/拒绝 | 全部撤销 |

## Memory、Relationship、自传与遗忘

| 类型 | 未来 owner / 写入、读取与纠正 | 禁止的捷径 |
| --- | --- | --- |
| Working | 会话/短时受信投影；只读到 Prompt，随会话/版本失效 | 不当作跨重启事实库。 |
| Episodic | MemoryRuntime 中有来源的事件记忆；Owner/授权会话提议，显式接受/纠正；与 Story accepted event 引用分开 | 对话全文自动确权。 |
| Semantic | MemoryRuntime 中可纠正事实、冲突/supersession、重要度、受控衰减；Owner/受控确认者可改 | 模型总结直接成当前事实。 |
| Relationship | 新的 Soul↔Subject key 和来源链；共同经历、关系变化、信任、重要纠正、互动偏好、里程碑；受控写入与按受众读取 | 普通 Semantic 标签或当前 Story 的 RP Character 关系冒充跨 World 真源。 |
| Autobiographical / Self | 有来源的 life event 与自我解释的派生视图；原始事实仍归 Story/Memory，解释可修订、失效 | conversation summary 或虚构叙事直接改写 SoulIdentity/Story。 |

Consolidation、Deduplication、Conflict Resolution、Supersession、Importance、Decay 与 Controlled Forgetting 均须保留来源/版本和受控写者；模型输出是候选 DATA，`Model Summary != Authoritative Memory Fact`。Relationship subject 的稳定确权缺口见 `OPEN_QUESTION_02`。RP/Original Soul 默认隔离；同一 SoulId 不构成跨 World 读取许可，Controlled Bridge 仍要求显式 grant、有界投影、来源语义不提升。`Original Soul != RP Character`。

受控遗忘先由 Memory owner 接受删除/隐藏/替代，再使派生摘要、索引、PromptSnapshot、关系/自传投影和桥接来源引用按来源版本失效；旧备份恢复前必须重放不回滚的删除控制，缺控制隔离。审计只存 ID、操作和最小 hash/状态，不无界保留已删除正文。外部模型/用户已经见过的内容无法撤回，不作该承诺。Story 首版 accepted event 的物理删除另需独立合同；不能因 Memory 遗忘而悄悄改写 Story 真源。

## Minimal Prompt Projection 与 Living

M0 仅冻结：`projection authority = 受信 Core/适配器`；输入各自有 Scope/viewer/来源/版本；section ownership 明确，顺序为 Runtime control → Soul identity（必需结构化、非模型自称）→ Character presentation → Story → Lore → Memory → Relationship/Living（未来获授权后）→ Bridge → Conversation；预算按完整 item `PREFIX/SUFFIX` 与必需项硬失败，记录诊断；read-only、确定性 fingerprint/integrity 与 token；任何 Soul lineage/Instance、World/Memory/Story/Bridge/Living/Session、generation 或删除控制版本变化使旧快照 stale。未来新 section 的精确优先级和 byte budget 须在 M2 实施任务独立冻结，不在本 PR 修改模板。`Prompt != Truth Source`，`Prompt declaration != Authority`；legacy prependContext、普通 tool output 不能冒充正式 Soul Projection。现有 `SP-004K-prompt-v1` 保持不变，`PROMPT_TEMPLATE_UPGRADE_REQUIRED = YES`。

Living Runtime 继续拥有日程、活动、意图、预算与 Attempt。未来只消费经验证的 SoulIdentity、Memory、Relationship、Living State 的有界投影；不另立人格真源。主动联系仍经原 quota、session/generation/Host authority 与 delivery gate；continuity verdict 不授予 REAL_SEND。`CLAIMED != SENT != ACKNOWLEDGED`、`UNKNOWN != permission`、`UNKNOWN != automatic resend`。

## Failure Semantics、Trust Boundary 与架构决定

优先级：**当前授权/锚与损坏检查 → lineage verdict → 各子系统当前 Scope/版本 → 操作资格**。缺失、冲突或旧证据返回明确 `UNKNOWN`/`MISMATCH`/`FORK` 与拒绝结果，不自动创建新 ID、回退到旧 generation、调用模型裁判或静默修复。离线 harness 只证明单受信 authority 域内的确定性结果；真实 Host、provider、跨机器全局唯一性、真实发送另需独立证据。

架构决定：`AD-01` 最小 record+anchor，`AD-02` 四值 verdict，`AD-03` copy/concurrent fail-closed，`AD-04` restore 不继承权限，`AD-05` 现有 World/Memory/Story/Living/Host 真源与 Scope 原样保留，`AD-06` M1 → **M1.x Continuity Proof / Simulation Gate** → M2，不得跳过。重要决定已在本文写明理由和替代边界；若独立审核要求单独 ADR，可在同一文档阶段补，但 ADR 批准不等于实现授权。

`SCHEMA_CHANGE_REQUIRED = YES / SCHEMA_CHANGE_AUTHORIZED = NO`：M1/M1.x 需要最小 SoulInstance/lineage record 与业务备份外 anchor；不是 Schema 8 已存在实体。最小字段、迁移/兼容/回滚风险见[实施计划](../planning/SP-006S0-IMPLEMENTATION-PLAN.md)。本 PR 不改 `DATA_SCHEMA = 8`、`SP-005A-living-runtime-v1`、`SP-004K-prompt-v1`，不执行迁移。

### Open Questions 的审核裁定与后续 Gate

| ID / blocking | 缺失证据、影响与推荐决策阶段 |
| --- | --- |
| `OPEN_QUESTION_01 = ACCEPTED_CAPABILITY_BOUNDARY`；**不阻塞 M1 或离线 M1.x，阻塞真实跨机器/Host continuation 与多节点双活** | 现有代码无共同可信协调者，两个完整拷贝可各自持本地 anchor。无共同协调者 → `UNKNOWN / FAIL_CLOSED`；未来真实能力须独立 Host / Coordination Governance Review，不能以本地模拟冒充。 |
| `OPEN_QUESTION_02 = DEFERRED_TO_M3_PERSON_IDENTITY_GATE`；**不阻塞 M1、M1.x 或 M2 basic Memory，阻塞 M3 跨 World Relationship** | 当前 Story 关系只含同 Scope CharacterInstance，Memory Subject 不授予身份确权。M3 前须冻结 PersonRef、identity provenance、explicit Scope mapping、merge/split/correction 与 privacy boundary；名字匹配禁止，Host principal 不自动等于 PersonRef。 |
| `OPEN_QUESTION_03 = ACCEPTED_WITH_PRE_M1_WRITE_GATE`；**不阻塞 SP-006S0，阻塞 M1 任意 continuity 持久化写路径** | 现有 Memory/Bridge 控制账本仅提供 fail-closed 模式，不提供 Soul lineage 的现成事务。M1 授权后先完成 M1-P0 与独立审核，再实现 record/anchor、SoulInstance enrollment、generation/restore/fork/handoff/retirement activation 或创建 active state 的 Schema migration；不在 SP-006S0 选择生产存储技术。 |

上述裁定冻结能力边界与实施顺序，具体生产协调者、PersonRef 与持久化技术留待各自 Gate；不以 `UNKNOWN` 伪装能力 PASS，也不因这些局限重写既有 World/Bridge/Host Safety 合同。
