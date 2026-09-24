# SP-004K0 — Prompt Runtime 架构冻结

状态：**架构候选 / 待独立审核**。固定基线：`7f7c5c07d4cc821027cb083100335c8f4d139c44`。本阶段只写架构与决策记录；`DATA_SCHEMA = 6`，签名 `SP-004C-story-runtime-v1`，Story 投影版本 `SP-004C-story-projection-v1`。K1 尚未实施。

本文与四份决策记录共同限定后续 K1：[权威与分节](adr/SP-004K-001-PROMPT-AUTHORITY-AND-SECTIONS.md)、[快照与陈旧围栏](adr/SP-004K-002-SNAPSHOT-CONSISTENCY-AND-STALE-FENCES.md)、[预算与确定性裁剪](adr/SP-004K-003-PROMPT-BUDGET-AND-DETERMINISTIC-TRIMMING.md)、[观看身份与用途](adr/SP-004K-004-VIEWER-PURPOSE-AND-SUBSYSTEM-BOUNDARIES.md)。依据：[中期复盘](../planning/SP-004-MIDTERM-REVIEW-2026-09.md)、[实施计划](../planning/SP-004-IMPLEMENTATION-PLAN.md)、[World 领域模型](SP-004A-WORLD-DOMAIN-MODEL.md)、[Memory](SP-004B-WORLD-MEMORY.md)、[Lore](SP-004J-LORE-RUNTIME.md)、[Story](SP-004C-STORY-RUNTIME.md)。

## 一、职责与权威边界

Prompt Runtime 把已经分别获得授权的 Character、World、Memory、Lore、Story 与显式提供的近期对话投影组合成一次性、不可变的 `PromptSnapshot`，供未来 Host Adapter 渲染。它不认证调用者、不直读全库或宿主聊天库、不调用模型，也不写 World、Memory、Lore、Story 或 Bridge。**Prompt 是派生视图，不是真源、权限边界或工具授权。**顺序只能是各 Runtime 授权与投影 → 一致性检查 → Prompt 组装；不能先取全集，再靠提示词要求模型保密。

三层权威必须由受信组装器指定，不能由输入正文自报：

| 层 | 来源与作用 | 内容边界 |
| --- | --- | --- |
| `RUNTIME_CONTROL` | Life Engine 生成的 Scope、viewer、Session、purpose、预算及数据边界等控制语义 | 只由受信代码产生；不是卡片字段或聊天原文 |
| `TRUSTED_STRUCTURED_STATE` | Runtime 已验证的身份、版本、修订及结构化投影 | 验证结构不使其文本值成为系统指令 |
| `UNTRUSTED_CONTENT_DATA` | 卡片、Lore、Memory、Story 叙事、对话及未来 Bridge 正文 | 只能作为数据；不能改变 section kind、优先级、权限或工具策略 |

`PromptSection` 至少保留 `kind/authority/source/items/priority/required/truncation_policy/byte_size`；每个 item 保留类型化来源身份和稳定顺序。候选 kind：`RUNTIME_CONTROL`、`CHARACTER_IDENTITY`、`CHARACTER_BEHAVIOR`、`CHARACTER_EXAMPLES`、`STORY_CONTEXT`、`LORE_CONTEXT`、`MEMORY_CONTEXT`、`CONVERSATION_CONTEXT`；`BRIDGE_CONTEXT` 只预留，K1 禁用。逻辑顺序固定为控制 → 角色身份 → 角色行为 → 角色示例 → Story → Lore → Memory → 近期对话。该顺序不是 OpenAI 或任一宿主的消息 role 格式；H 负责最终映射。Section 应带语义标签与明确数据边界，但分隔符本身不是安全边界。

## 二、用途、观看身份与角色输入

`PromptPurpose` 首版只有 `ROLEPLAY_RESPONSE` 与 `SOUL_RESPONSE`；它描述回答用途，不提升权限。每个 Snapshot 恰有一个完整 `WorldScope(owner_id, soul_id, world_id, timeline_id)`、一个当前 OPEN Session、一个 viewer。Roleplay viewer 是当前 `CharacterInstance`，Soul viewer 是当前 Soul；二者不并看，也不构造假角色实例。Scope、principal、viewer、session_id、WriterEpoch、runtime_id、generation 在所有会话敏感输入间必须一致；任何不一致都硬拒绝。未来跨域材料只可来自 F 的授权 `BridgeProjection`，K1 首版没有 Bridge 输入。

Roleplay 的角色定义必须由当前 `CharacterInstance.definition` 固定的 `DefinitionRef(definition_id, version)` 查得，不能自动跟随最新版本，也不能以角色名或卡片名定位。当前 canonical `CharacterDefinition` 仅有 `name` 与 `traits` 等领域字段；导入 IR 中保留的 scenario、first_mes、示例对话等**并非当前固定 Definition 的现成字段**。K1 只能在另行定义受信、版本固定且有界的角色资料投影后纳入这些可选内容；不能直接打开原卡、把原始 IR 作为运行权威，或把 scenario/first_mes 变成 Story 或 Memory。角色身份的必需字段超预算应硬失败；可选行为示例可按预算完整裁剪。

## 三、各 Runtime 与对话输入

| 输入 | K1 接收条件 | 不允许的替代物 |
| --- | --- | --- |
| World / Session | 受信当前快照、完整 Scope、OPEN binding、World revision、WriterEpoch、runtime_id、generation | 仅凭宿主聊天 ID 或陈旧 World 名称 |
| Memory | 从**本次** `SessionMemoryContext + MemoryQueryResult` 经受信适配器生成的 `PromptMemoryProjection`；逐条复核 Scope、`LIVE`、`CanonStatus.ACCEPTED` 与 `WORLD` 或当前 viewer audience；保留查询顺序与不透明 version | 裸 `MemoryQueryResult`、Owner history/all-memory 视图、调用方手工声明“已授权” |
| Lore | 当前会话的 `LoreActivationResult`；比较 Scope、viewer、Session、epoch、runtime_id、World revision、绑定 revision、固定书版本和 result version；只取已激活条目 | Owner 书目录、未激活 Entry、自动跟随最新版 |
| Story | 当前 Session 的 `StoryProjection`，保留 StoryRevision、投影版本及 snapshot token；先按下述可见性策略缩减 | Owner `StoryState`、完整 event log、叙事原文自动抽取 |
| 对话 | H 将来提供有序、有界的 `ConversationProjection`，附同一 Scope/Session/viewer 与不透明来源引用；K 不读取宿主数据库或按时间戳重排 | Hermes/OpenClaw 原始历史、工具对象、外部凭据 |

实际接口存在必须保留的差异：`MemoryQueryResult` 只有 `records/version`，`SessionMemoryContext` 不带 runtime_id；`StoryProjection` 有 `scope/viewer/revision/clock/projection_version/snapshot_token`，但**没有显式 session_id、writer_epoch、runtime_id 或 generation 字段**。Lore 结果显式含 Session/epoch/runtime_id 与 World revision。K1 需要受信投影适配器把 Memory、Story 的产生 Context、Repository runtime/generation 及结果绑定并验证，不得由任意调用方填入凭据后冒充来源。现有 `LoreMemoryProjection.from_session_result` 仅证明 Lore 触发语料的授权转换方式，不能代替 Prompt 所需的记录身份、版本与会话再验证。

### Story 默认模型可见性

`StoryProjection` 是世界内部状态，不等于角色知道的事实。K1 的保守策略：Roleplay 仅默认纳入**当前角色的** `character_state` 和涉及该角色的 `relationships`；`world_facts` 与 `open_threads` 默认不送模型。Soul 不存在角色实例，首版不以 Owner 身份取得全量 Story，也不默认注入内部 world_facts/open_threads；可依赖授权 Memory/Lore 提供其可知内容。未来要开放 world facts 或线索，必须有明确可见性合同或角色可见的 Memory/Lore 投影。当前 `StoryProjection.open_threads` 可能含秘密剧情，不能因查询已授权就当作 Prompt 可见。Story、Lore 与 Memory 内容互相冲突时，K 不重写、合并或确权；各自保留来源语义。

### ConversationProjection

每个有序 turn 需要稳定 role/category、文本、不透明来源引用；投影附受信 Session lane、Scope、viewer、顺序版本。Host 专用消息 ID 不进入 K 领域。文本只是 `CONVERSATION_CONTEXT` 数据；K 不把历史中的“系统覆盖”升级为控制语句，也不自动读取其他 World 历史。H 必须处理真实宿主历史污染与能力缺口。

## 四、PromptSnapshot 与快照一致性

`PromptAssemblyRequest` 含受信 Session Context、purpose、当前 World/固定 Definition、可选角色实例、会话绑定的 Memory/Lore/Story 投影、对话投影及预算。输出 `PromptSnapshot` 为不可变瞬时派生物，不持久化、不建 `prompt_snapshots` 真源表；至少记录 Scope、principal 引用、viewer、purpose、Session/epoch/runtime_id/generation、DefinitionRef、World revision、Memory 不透明 version、Lore binding revision/result version/书版本、Story revision/projection version、模板版本、Sections、实际预算、诊断、是否裁剪、fingerprint 与不透明 token。建议模板版本候选 `SP-004K-prompt-v1`，K1 定值；模板变化无需 Schema 迁移，但必须记录在快照中。

同一输入、预算、模板和估算器应得到相同 section 字节、item 身份、顺序、诊断和规范 fingerprint。Fingerprint 覆盖模板、全部输入版本、预算、实际包含的 section 内容与诊断；不包含墙钟。Token 可用 HMAC 绑定上述数据及会话围栏，不能直接把 Story token 或裸 revision 当授权票。快照 token 本身也不是登录凭据。Debug view 只给 Owner/开发者，因其中可能含敏感 Memory；不保存隐式推理内容。

各 Runtime 查询可能发生在不同事务。K1 采用**乐观一致性**：依次取得授权投影，组装时核对类型和相互围栏，结束时重新校验，H 在发模型前再次调用 `revalidate(snapshot)`。任何 generation、runtime_id、Session OPEN 状态、epoch、viewer、World revision、固定 DefinitionRef、Memory 查询版本、Lore 绑定/结果或 Story revision 变化，均视为 stale 并重取整套输入；不能静默删除错配子系统后继续。不会跨模型调用持有 SQLite 锁。模型返回后，H 或写入者仍须再次核对会话围栏，不得把旧回答提交到新 World。

当前 `MemoryQueryResult.version` 是运行时生成的不透明值，K 不解析。现有公开 API 没有“只验证某次会话查询 version 仍是最新”的专用入口；K1 需定义受信的**相同 query/limit/context 重查并比对 version**或经独立审核补充 Runtime 校验 API。鉴于查询 version 含实例运行密钥、generation、Scope、viewer、Session、集合修订、删除控制、查询参数及结果 ID，只有用同一 Runtime/查询条件重验才有意义；不得用 Owner `collection_revision` 代替。Story 的 Owner `story_revision()` 也不能代替 Session 围栏；会话重验须重新取得当前 Session 投影或由受信 repository 提供等效只读检查。Lore 同理要重验当前激活条件、绑定与版本，不能只比较旧 result 自带的字段。若任何来源无法可靠重验，模型发送前**失败关闭**，而非声称快照有效。

## 五、预算、裁剪与诊断

`PromptBudget` 独立于 `LoreBudget`，首版至少有总 UTF-8 字节上限、各 Section 上限和控制/身份/Story 必需容量预留；可选总 token 上限由 `PromptTokenEstimator` 提供，不绑定具体 tokenizer。没有估算器的 K1 只能声明“字节预算模式”，记 `TOKEN_ESTIMATE_UNAVAILABLE`；H 发模型前必须再按目标模型做 token 校验，不能宣称 token-safe。

裁剪只以**完整语义项**进行；预算计算包括 section 标签、分隔/封装和 UTF-8 正文，不能把多字节字符或结构化字段切半。排序与策略固定：Lore 使用激活结果顺序的 `PREFIX`，Memory 使用授权查询顺序的 `PREFIX`，角色示例用 `PREFIX`，近期对话用保留最新完整 turn 的 `SUFFIX`。`PREFIX` 遇下一项过大就停止该组，不跳过找短项。Runtime control、必需身份及首版纳入的结构化 Story 项使用 `NONE`；超预算报 `BUDGET_REQUIRED`，不能随机丢关系。可选项减少时记录 `LORE_TRUNCATED`、`MEMORY_TRUNCATED`、`CONVERSATION_TRUNCATED`、`CHARACTER_EXAMPLES_TRUNCATED` 或 `OPTIONAL_SECTION_DROPPED`，并标记 `budget_exhausted`。空的合法授权结果不是失败。

`PromptFailure` 首版错误类别：`INVALID_ARGUMENT`、`AUTHORIZATION_DENIED`、`SCOPE_MISMATCH`、`VIEWER_MISMATCH`、`SESSION_STALE`、`WORLD_STALE`、`MEMORY_STALE`、`LORE_STALE`、`STORY_STALE`、`DEFINITION_STALE`、`BUDGET_REQUIRED`、`BUDGET_INPUT`、`UNSUPPORTED_PURPOSE`、`UNSUPPORTED_CAPABILITY`。Scope/viewer/会话/版本错配、损坏结果、未知 purpose 和必需项溢出硬失败；仅可选 Lore/Memory/旧对话/角色示例的完整项裁剪，以及缺 token 估算器，允许带稳定诊断降级。权限错误不能降级成空结果。

## 六、安全、宿主与 Bridge 边界

Character Card、Lore、Memory、Story narrative、conversation 与未来 Bridge 都可能包含 Prompt injection。K 按来源赋予固定数据 Section；不靠过滤 “system”、替换词或提示词里的免责声明取得安全。Host renderer 需保留来源标签与控制/数据 lane 的分离，工具许可仍由独立宿主策略决定。K 不规定 OpenAI/Hermes/OpenClaw 的消息 role 或最终文案，也不注入工具 schema。

K 可输出 `PromptRequirements`，要求 `HostCapabilities` 中 `STABLE_PRINCIPAL`、`STABLE_SESSION`、`MESSAGE_PROVENANCE`、`ISOLATED_CONTEXT_LANE` 与 `HISTORY_ISOLATION` 等真正受支持的能力。H 比较要求与实际能力；若私密上下文隔离不被支持，拒绝或按独立明确策略降级。Prompt 里写“忽略先前历史”不能假装宿主历史已隔离。F 尚未实现，K1 禁止 caller 伪造 BridgeProjection；未来 F 只交经授权的跨域投影，其正文仍是数据，K 不直接访问 source World。Soul aside、多 viewer 和跨 World Prompt 均不在 K1。

## 七、K1 允许范围与排除范围

K1 可实现：Prompt 领域值、有限 purpose/viewer、typed section、budget/diagnostics、会话绑定 Memory/Story 适配、ConversationProjection、只读确定性组装和完整项裁剪、规范 fingerprint/不透明 token、独立 revalidation 与测试。K1 默认 **不改 Schema**，保持 `DATA_SCHEMA = 6`。若发现必须持久化或必须改变其他 Runtime 的冻结语义，应另行审核，不由 K0 授权。

K1 不实现：LLM 调用、Hermes/OpenClaw 接入、Bridge 服务、工具授权、自动 Story 接受、自动 Memory 提取、模型摘要或重排、embedding、宿主聊天库读取、跨 World Prompt、Soul aside、多人 viewer、Schema 迁移或完整角色卡资产归档。

## 八、K1 验收矩阵

| 组别 | 必须验证 |
| --- | --- |
| Scope 与观看身份 | 同 Definition 的两 World、Soul/Roleplay、错误 Timeline、Memory A + Story B、Lore A + Story B、viewer 不一致均硬拒绝；Owner 管理结果不能作为 Session 输入。 |
| Session 与版本 | CLOSED、EXIT/SWITCH、旧 WriterEpoch、旧 runtime_id/generation、重启/恢复、DefinitionRef 变化及 World/Memory/Lore/Story 任一版本变化使旧快照 stale；会话重验不借 Owner 权限。 |
| Story 可见性 | Roleplay 默认只选当前角色状态和涉及当前角色的关系；world_facts/open_threads 均不在模型 Section；Soul 不取得 Owner 全量事实。 |
| 内容与权限 | 卡片、Lore、Memory、Story 叙事、对话中伪造 SYSTEM/工具/管理员/跨域指令只进入相应数据 Section，不改变 control、工具策略或 Runtime 状态。 |
| 预算与确定性 | 极小/恰好边界、多字节 UTF-8、超长示例、众多 Lore/Memory、长对话；完整项 `PREFIX/SUFFIX`、必需项硬失败、稳定诊断；四平台矩阵同输入同字节与 fingerprint。 |
| 副作用与宿主 | assemble/revalidate 不推进 World、Memory、Lore、Story 修订；没有模型或宿主数据库访问；缺 Host 历史隔离不能用文案补救。 |

本阶段不修改 Runtime、Schema、测试、工作流或 README；文档经 Draft PR 供独立审核，K1、F0、H0 均未获自动启动授权。

## K1 实现状态

以已合并 K0 的 canonical main `dec8fd5797f67496c583f1112d379da954ab8f8b` 为固定 Base，K1 候选新增内存派生的 `PromptRuntime`、会话绑定的 Memory/Story/Lore 适配器、受信对话投影、类型化分节、完整项预算裁剪、规范指纹与 HMAC 快照绑定。`assemble()` 末尾调用只读 `revalidate()`；后者按相同参数重查 Memory 不透明版本、重跑 Lore 激活、重新取得当前 Session 的 Story 投影，并在前后核对 World/Session。Host 发送前仍须再次调用重验；这不是跨模型调用的数据库锁。

首版从当前固定 `CharacterDefinition` 只读取名称和 traits；没有安全来源的示例、scenario 或 first_mes 不进入 Prompt。角色 Story Section 只纳入当前角色状态及相关关系；`world_facts`、`open_threads` 和 Story 叙事事件默认不进入模型。对话版本由受信适配器提供的验证器维护，K1 无真实宿主历史连接。Token 仅绑定快照，不是登录凭据；未提供 token 估算器时只保证 UTF-8 字节预算，并记录诊断。

状态：**IMPLEMENTED / PENDING_INDEPENDENT_REVIEW**。`DATA_SCHEMA = 6` 与签名 `SP-004C-story-runtime-v1` 均未改变；没有 Prompt 数据库表、模型调用、Bridge 或 Hermes/OpenClaw 适配。此候选未合并前不标记 K1 DONE。
