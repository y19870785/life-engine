# SP-004B-001 — Memory 语义、来源与接受权

## 状态

SP-004B0 架构冻结候选 / PENDING_INDEPENDENT_REVIEW。基线 `4372b557dc8e3cc498098b6fe26e13df51ce802e`。只有文档，没有新增类型、枚举、表或服务；作者不自行标记独立审核通过。

## 背景

[A 的真实性与正史 ADR](SP-004A-002-REALITY-AND-CANON.md) 已分开 RealityStatus 与 CanonStatus，但现有值构造允许显式 ACCEPTED，不执行接受权限验证。[D](../SP-004D-WORLD-INSTANCE-RUNTIME.md) 的 Values/relationships 只用于最小状态验证；[G](../SP-004G-CHARACTER-IMPORT-IR.md) 的 LoreIR 是保留来源。必须避免把“持久化了一句话”变成“故事已发生”，也不能制造第二套 Provenance。

## 决策

### 一、知识记录与事实权威

MemoryRecord 是长期可检索知识记录，包含明确来源、Scope、受众、真实性和接受状态。它可以描述观察、用户报告、推断、体验、语义知识或摘要；它不是事件日志、StoryState、Lore、Prompt、缓存、检索索引或聊天历史。

未来 StoryEvent 是经接受流程使 World canonical story state 发生变化的事件。accepted StoryEvents → 确定性 reducer → StoryState/RelationshipState。StoryEvent 可以产生 Memory；Memory 不能自动证明 StoryEvent 已发生。即使 Memory ACCEPTED，也只表示该知识记录获准成为相应域的已接受记录；不会自动建立或修正 Story canon。

“昨天去过城堡”的记忆不能直接设置 visited_castle。主观“我信任 B”可以被保留，不能越过 C 修改 canonical RelationshipState；反之关系 reducer 的结果也不意味着角色已经知道全部关系事件。

### 二、接受权与真实性

B1 采用最小权威：Owner 经可信 Principal 明确接受精确记录/内容版本，保存操作来源和接受依据。模型可提出 candidate，不能提交可信的 accepted 标志、Owner 身份或政策引用。用户随口陈述与“接受这条记忆”是不同动作，USER_REPORT 本身不是接受命令。

未来 C 可实现 Delegated Narrative Policy：Owner 预先指定 World、事件类型、风险等级、有效期和版本，由 Runtime 校验条件后接受普通虚构叙事；模型仍无接受权。跨 World、现实事实、Bridge、重要关系变化、重大分支、删除/覆盖 canonical state、现实工具动作要求独立且更严格的明确确认，不能落入普通叙事默认授权。B0 不实现政策，B1 不实现自动叙事接受。

RealityStatus 与 CanonStatus 正交：FICTIONAL/ACCEPTED 合法且仍虚构；USER_CLAIMED/ACCEPTED 不意味着观测为真。Owner 接受也不能把 USER_REPORT 改成 OBSERVED_REAL_WORLD_FACT，若确有新观测，应以新来源建立新记录并关联原陈述。模型新输出默认 CANDIDATE，来源不明旧数据或导入默认 UNREVIEWED。REJECTED 不进入默认检索；CANDIDATE/UNREVIEWED 仅在显式候选审阅用途下可读并带标签，不偷偷混入普通已接受知识结果。

### 三、来源映射与唯一 Provenance

| 来源 | 复用 SourceType | 默认 RealityStatus / CanonStatus | 接入要求 |
| --- | --- | --- | --- |
| 可信观测 | OBSERVATION | 有受信观测证据才 OBSERVED_REAL_WORLD_FACT，否则 UNKNOWN；CANDIDATE | 标签本身不作证据，验证采集来源；没有观测接入不能伪造 |
| 用户陈述 | USER_REPORT | USER_CLAIMED / CANDIDATE | 可信输入主体及消息身份，不自动接受 |
| 模型输出 | MODEL | 角色叙事 FICTIONAL，现实推断 AGENT_INFERRED；CANDIDATE | 不能自填 OBSERVED 或 ACCEPTED |
| 模拟状态 | SIMULATION | SIMULATED_LIFE_STATE / CANDIDATE | 不能因为放在 Soul World 就升级为现实事实 |
| 外部导入 | IMPORT | UNKNOWN / UNREVIEWED | 保留指纹/来源版本；卡片内容不颁发权限 |
| 历史未审来源 | LEGACY | LEGACY_UNREVIEWED / UNREVIEWED | 不推断历史授权；旧数据映射另审 |
| Owner 明确命令 | OWNER_COMMAND | 陈述正文仍 USER_CLAIMED，虚构指令 FICTIONAL，未知则 UNKNOWN | 接受操作可产生 ACCEPTED 后继，但保留原来源类型；Owner 身份不伪装观测 |
| 跨域派生 | BRIDGE | 保留原真实性或明确虚构变换；独立接受依据 | 未来 F 验证双侧权限、grant、lineage；B1 拒绝该写路径 |
| 未来已接受 StoryEvent | 未来 SourceType.STORY_EVENT 提案 | 继承事件真实性；派生 Memory 默认 CANDIDATE | 现枚举没有此值；未来 C 验证 source_event_id 和接受依据后才开放，B0 不改枚举 |

当前 Provenance 的 source_id、actor、aware created_at 与 source_world/timeline/session/event 继续使用。Memory 顶层的 reality/canon/source_event 是这些值的语义视图，不允许存在两个可分歧的来源真源。Memory lineage 表示派生关系，是附属引用，不另建一套来源认证系统。

对候选的接受不修改旧 Provenance：创建后继记录，新的 Provenance 保留原 source_type/source_id/actor/来源时间，canon_status 表达此次新的接受状态；另记 Owner 接受操作及时间。记录 created_at 是后继提交时间，不冒充来源发生时间。修改真实性或事实正文则必须提供相应新来源并保留 supersedes 链，不可无理由改分类。模型摘要的 source_type 仍为 MODEL；引用观测来源不使摘要自身变成观测。

### 四、分类、摘要与选择

memory_kind 是内容用途分类。episodic 表示经历回忆，semantic 表示知识，summary 表示有源摘要，observation 表示观察记录，preference 表示偏好陈述，relationship_experience 表示互动认知，shared_experience 表示共享体验内容。它们均不能授予读写权、真实性或 canon。B1 可形成有限枚举，但 B0 不加代码；shared_experience 名称不是 Bridge grant。

自然聊天不全部入长期 Memory。可信 selector 根据明确政策提出候选并保留 source model response/message identity；LLM selector 不能最终接受。B1 不实现 LLM 自动提取。用户指定一条陈述保存也不意味着对全部历史进行了授权。

summary ≠ source deletion ≠ canon promotion ≠ provenance erasure。摘要需保留精确来源集合、版本及分类，来源受众取有效可见身份交集；不能从“一人可看 A、另一人可看 B”推出所有人可看摘要。不同 reality/canon 的来源分组保存；模型归纳作为新候选，引用原状态但不继承 ACCEPTED。禁止将已知虚构洗成 UNKNOWN 后再升级现实。摘要不能替代整个 Story state，删源或撤销来源会使依赖摘要退出检索。

### 五、生命周期

正文、来源、Scope 与接受语义不静默覆写。supersede、accept、reject 或语义修正创建新 ID，关联精确 predecessor/version，后继 content_version 加一；旧记录有唯一 superseded_by，禁止循环和跨 Scope 替代。双方链接与 MemoryCollectionRevision 在同一事务更新，失败两者都不变。

可见性管理可原地更新单独控制状态，但必须追加操作来源、执行集合 CAS 并失效缓存。LIVE、HIDDEN、SUPERSEDED、TOMBSTONED 与 CanonStatus 分离。hide 可由 Owner 显式撤销；delete 不是 hide，不以普通 unhide 撤销 tombstone。删除正文可保留最小非正文引用，但不承诺立即清除旧备份；详见 [ADR-004](SP-004B-004-SCHEMA-4-MIGRATION.md)。

retention 首版默认保留，不自动删候选/旧正文。未来显式保留策略与手动删除同样受控。源删除或事件失效立即禁止依赖记录被检索，随后可以生成新版本或清理，不能仅等待异步 reindex。源事件只修改其派生记忆，不通过删 Memory 反向删除 StoryEvent。

## 备选方案

| 方案 | 判断 |
| --- | --- |
| 所有 Memory 都是已发生事件 | 拒绝；混淆陈述与 Story 接受，无法保存主观或错误记忆 |
| 分别建 SoulMemory/PersonaMemory 类型与服务 | 拒绝；会产生不同授权/恢复规则，安全应依赖 Scope |
| 每句聊天自动保存 | 拒绝；既无选择依据也扩大长期私有数据范围 |
| 原地改正文/canon 以减少行数 | 拒绝；丢失修正和接受依据 |
| 先等完整 Story Runtime 再定义 Memory | 不采用；Owner/用户报告路径可独立实现，Story 来源保持关闭 |

## 影响

修正链会增加历史记录，需要有界查询、明确保留和删除合同。记忆的 ACCEPTED 与事件的 ACCEPTED 是不同接受对象，界面和将来的 Prompt 必须保留来源及标签，不能只展示一句脱离分类的“事实”。

## 明确拒绝的做法

禁止模型自封接受权、从导入卡建立既成事实、自动 EXIT → Soul memory、同卡共享 persona memory、以最近几条摘要驱动 canonical relationship 或 Story。

## 验证要求

未来 B1 验证 MODEL 无权 ACCEPTED、USER_CLAIMED 接受后不变 OBSERVED、替代链回滚、来源与记录时间分别往返、拒绝/隐藏退出默认检索、摘要受众交集和来源删除传播。未来 C 验证 Memory 不触发 Story reducer。当前 [test_domain.py](../../../tests/test_domain.py) 只证明类型正交及来源限制，不证明未来接受服务已实现。

## 后续工作

B1 增加 Memory 类型及 Owner 接受操作；C 才能开放 Story 来源验证和叙事委托政策，F 才能开放 Bridge。相关：[主架构](../SP-004B-WORLD-MEMORY.md)、[访问隔离](SP-004B-002-SCOPE-AUDIENCE-ISOLATION.md)。

## B1 实现状态

IMPLEMENTED / PENDING_INDEPENDENT_REVIEW。固定 Base 为 `4d628ca1b7b68609cd6fcf95e835c25ffa638c6b`。本节追加实施证据，不重写上述 B0 历史决策。

领域对象位于 [memory.py](../../../runtime/life_engine/memory.py)，接受、拒绝与替代由 [MemoryRuntime](../../../runtime/life_engine/memory_runtime.py) 实现。后继保留来源、增加正文版本并记录管理操作。观测适配器和自动提取未实现，无来源证明的 OBSERVATION 拒绝。验收见 [领域测试](../../../tests/test_memory_domain.py) 与 [运行测试](../../../tests/test_memory_runtime.py)。
