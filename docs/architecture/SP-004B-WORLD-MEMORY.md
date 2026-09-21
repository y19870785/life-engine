# SP-004B — World Memory 架构与 B0 冻结候选

## 一、状态、基线与文档职责

阶段：SP-004B0。固定 Base：`4372b557dc8e3cc498098b6fe26e13df51ce802e`。状态：**架构冻结候选 / PENDING_INDEPENDENT_REVIEW**。本文对方案作出明确选择，等待 ChatGPT / 小雪独立审核；不是实施完成或合并授权。B1 尚未开始。

当前 SP-004/A/G/D/E/R、GOV-CI0 已合并。当前 `DATA_SCHEMA = 3`、`SIGNATURE = SP-004E-world-runtime-v1` 不变。未来持久 Memory 必须进入 Schema 4；本文没有 DDL、运行代码或迁移实现。

旧阶段文档中的 PENDING、Schema 2、PR #3 OPEN 等是当时记录。当前 [PR #3](https://github.com/y19870785/life-engine/pull/3) 为 CLOSED / NOT MERGED，历史 Head 为 `ab227f2179eeaa7ded662d612508a98ad5cdf04a`，只能只读参考。本轮不重写历史记录，不复活其 card/session 根、自动 EXIT 元记忆或旧 Schema 3。

四份 ADR 分别是下列合同的权威细化，主文档负责整合与边界，发生实施疑问应回到 ADR 而不是自行放宽：

- [001 — 语义、来源与接受权](adr/SP-004B-001-MEMORY-SEMANTICS.md)。
- [002 — 作用域、受众与访问隔离](adr/SP-004B-002-SCOPE-AUDIENCE-ISOLATION.md)。
- [003 — 修订、围栏、查询与缓存](adr/SP-004B-003-REVISION-QUERY-CACHE.md)。
- [004 — Schema 4、副本迁移与安全恢复](adr/SP-004B-004-SCHEMA-4-MIGRATION.md)。

## 二、当前代码审计与可复用合同

| 当前文件 | 已有合同 | B0 的边界判断 |
| --- | --- | --- |
| [domain.py](../../runtime/life_engine/domain.py) | DomainId、Principal、WorldScope、Provenance、RealityStatus/CanonStatus | Principal 是可信调用方断言，不是凭据；枚举存在不等于接受权限已实现；尚无 MEMORY ID |
| [domain_policy.py](../../runtime/life_engine/domain_policy.py) | Bridge 默认拒绝、显式能力 SUPPORTED 检查 | 纯资格判断不传输数据；audience 字符串集合不是未来 Memory ACL 的完整模型 |
| [domain_lifecycle.py](../../runtime/life_engine/domain_lifecycle.py) | World revision、WriterEpoch、SessionBinding 纯校验 | 必须对照存储内最新状态；现有 validate_write 接收实例/WorldState，不直接充当 Memory 写接口 |
| [world_repository.py](../../runtime/life_engine/world_repository.py) | 单 Timeline、每 World 最多一个 OPEN、身份与历史不变式 | Memory 不塞入 WorldSnapshot 或 Values，不要求每条 Memory 保存整个聚合 |
| [world_runtime.py](../../runtime/life_engine/world_runtime.py) | ENTER/EXIT/SUSPEND/RESUME/Switch、最小实例状态更新 | 没有 Memory、Story 接受或关系 reducer；新的 Memory 事务适配由 B1 独立实现 |
| [world_sqlite_repository.py](../../runtime/life_engine/world_sqlite_repository.py) | BEGIN IMMEDIATE、数据库 CAS、runtime_id、重启围栏与显式连接释放 | B1 要共用同一数据库原子边界和启动代次；不能每个 Memory 连接重新启动 World Repository |
| [world_schema.py](../../runtime/life_engine/world_schema.py) | Schema 3 精确结构、签名、外键和完整性校验 | 增加额外 Memory 表也会不匹配；不能继续叫 Schema 3 |
| [world_codec.py](../../runtime/life_engine/world_codec.py) | 确定性 JSON、DomainId、aware datetime 往返 | 复用编码原则，不以 repr/pickle 保存；Provenance 字段集目前严格校验 |
| [durable.py](../../runtime/life_engine/durable.py) | 安装锁、备份、代次复制、整安装 registry 激活、整组回退 | 现有恢复不是未来隐私删除/撤销账本；B1 需要显式扩展验证路径，B0 不改它 |
| [import_ir.py](../../runtime/life_engine/import_ir.py)、[import_cards.py](../../runtime/life_engine/import_cards.py) | 不可信导入、保留 LoreIR、IMPORT/UNKNOWN/UNREVIEWED 定义投影 | 卡片陈述与 first message 不自动成为记忆、权限或既成 Story |
| [store.py](../../runtime/life_engine/store.py) | 原生活 memories、observations 等表 | 旧 memories 无四元 Scope，不是新 MemoryRecord；升级原样保留，不自动混入新查询 |

设计依据：[总体架构](SP-004-PERSISTENT-WORLD-RUNTIME.md)、[A](SP-004A-WORLD-DOMAIN-MODEL.md)、[G](SP-004G-CHARACTER-IMPORT-IR.md)、[D](SP-004D-WORLD-INSTANCE-RUNTIME.md)、[E](SP-004E-WORLD-SQLITE-PERSISTENCE.md)、[差距分析](SP-004-GAP-ANALYSIS.md)、[实施计划](../planning/SP-004-IMPLEMENTATION-PLAN.md)、[PR #3 替代记录](../planning/SP-004R-PR3-SUPERSESSION.md)。本轮没有发现必须先实现 Story 才能定义 Memory 的依赖：B1 可先接收 Owner、可信观测或用户报告，Story 派生入口在 C 出现前保持不可用。

## 三、Memory 的定义与逻辑记录

Memory 是带 provenance、WorldScope、真实性、接受状态和 audience 的长期可检索知识记录。它可表达经历、观察、用户陈述、推断、知识或摘要，不等于这些来源对象本身，不保证其命题为真。

**Memory ≠ StoryEvent ≠ StoryState；Memory ≠ Lore、Prompt、Cache、Chat History。** accepted StoryEvent 是未来 Story/Relationship 投影的真源。Memory 是其自身知识记录的真源，不能用一条 ACCEPTED Memory 自动修改 StoryState。每条自然聊天也不是一条长期 Memory；可信 selector 可提出候选，模型 selector 不能接受自己。

统一 Soul/Roleplay 的 MemoryRecord 模型，不创建相互竞争的 SoulMemory/CharacterMemory 仓库。统一模型不共享访问。所有记录必须携带完整四元 Scope；“World 级”知识在首版仍归唯一 Timeline，不允许 timeline_id 为空或通配，也不自动对未来分支可见。

| 逻辑字段 | 冻结语义与不变式 |
| --- | --- |
| memory_id | B1 增加 IdKind.MEMORY 的类型化 UUID4；全局不可复用，不由内容、卡名或宿主 ID 派生 |
| owner_id / soul_id / world_id / timeline_id | 一个不可变 WorldScope，必须与已存储 World/Timeline 一致；角色引用也必须属于它 |
| subject_refs | 关于谁/什么；类型化实体引用或明确非实体主题；不授予读取权，不解析模型伪造路径 |
| audience | 非空、规范化的类型化受众集合；默认不能 WORLD；详见 ADR-002 |
| memory_kind | 内容用途候选：episodic、semantic、summary、observation、preference、relationship_experience、shared_experience；B1 固定有限取值，不作权限/真假/接受状态 |
| content / content_version | 有界 UTF-8 语义正文；不可静默覆盖；content_version 首次为 1，替代链后继加一并使用新 memory_id，不是 collection revision |
| reality_status / canon_status | 两个正交维度；从该记录的 Provenance 取得，不设可独立矛盾的第二权威字段；若物理展开必须同事务强制一致 |
| provenance | 复用现有 Provenance；来源 actor/时间/事件引用不可暗改；接受、拒绝和管理动作有各自操作来源记录 |
| source_event_id | 使用现有 Provenance.source_event_id；未来仅可由可信 C 验证后引用；没有 Story 服务时不能自填已接受事件证明 |
| source_memory_id / lineage | 同域派生的精确源记录与版本；多源用 lineage 边；跨域必须另含源 Scope、grant/版本和变换记录，B1 不开放跨域入口 |
| created_at | 记录提交时间，aware UTC；来源发生时间保留在来源中，不倒写提交顺序 |
| superseded_by | 单一同域后继；正文/分类/来源修正及 canon 变化创建新记录；原记录保留可追踪历史但退出默认检索 |
| lifecycle / tombstone | 可检索性独立于 canon；LIVE、HIDDEN、SUPERSEDED、TOMBSTONED 是逻辑状态，不在 B0 增加枚举；删除不表示清除所有备份 |
| acceptance_ref / operation provenance | 接受主体、政策版本或 Owner 命令及所接受内容的精确引用；模型输入不能自行构造有效证明 |
| idempotency identity | 可信操作来源、来源消息/事件身份和操作槽位；与载荷指纹共同防重复，不用正文相等推导同一经历 |
| MemoryCollectionRevision | 每个完整 WorldScope 一份独立单调计数；不属于某条正文；数据库 CAS 的比较对象 |

B1 需要 Memory ID 与独立修订值类型，不需要为每个 collection 再造 UUID；collection 由 Scope 定位，IndexGeneration 用集合内单调版本标记。额外操作记录和索引的具体物理键留给实现验证。

## 四、谁拥有、谁写、谁看

Owner 控制自己的记录；Principal 必须来自受信入口。Roleplay 会话写入只允许当前绑定角色的私有候选，默认 audience 为该实例；扩大到其他角色、WORLD 或接受为 canon 必须经 Owner 权限。Soul 会话默认 SOUL 候选。维护入口单独校验 Owner 管理权，不伪装成角色会话，也不自动恢复或推进剧情。

所有读取先验证 WorldScope 和用途，再确定单一有效观看身份：当前 CharacterInstance、当前 Soul 或显式 Owner 管理视图。相同 Owner 的管理权限不能被 Prompt 自动用来读取全部私人记录。单角色、多角色共享、WORLD、USER、SOUL 和显式 Principal 的具体交集规则见 ADR-002；subject 永远不是权限。

模型新输出默认为 CANDIDATE；来源不明导入为 UNREVIEWED。B1 的 ACCEPTED 仅允许可验证 Owner 命令；未来 Delegated Narrative Policy 的范围、类型、风险和版本必须先经 Owner 授权，模型永远只是提议者。跨域、现实事实、重大分支/关系、删除或覆盖 canonical state、现实行动/工具不可借普通叙事授权自动接受。

`FICTIONAL + ACCEPTED` 是已接受虚构知识；`USER_CLAIMED + ACCEPTED` 仍是用户陈述，不是系统观测。重要关系投影来自 accepted StoryEvents → relationship reducer → RelationshipState；角色的主观关系记忆允许与投影不同。现有 relationships Values 不是该引擎。

## 五、逻辑流程与原子点

### Memory 写入

```text
可信调用方 → 认证 Principal → 解析完整 WorldScope
→ 明确会话写入或 Owner 维护操作
→ 同一事务读取当前 World/Timeline/绑定/runtime_id
→ 会话操作校验 ACTIVE、Principal、实例、OPEN、WriterEpoch
→ 校验来源、provenance、audience 和接受权
→ 幂等身份与载荷核对
→ MemoryCollectionRevision 数据库 CAS
→ 同事务保存记录/替代/幂等回执并推进 Memory revision
→ 提交后失效派生视图；按新版本重建或走授权的真源查询
```

CAS、记录、幂等回执必须同提交；索引可异步但不得在陈旧版本上返回结果。World revision 不因普通 Memory 写入推进。网络、模型调用在事务外；返回后重新验证围栏，绝不把晚到响应路由到当前另一个世界。细节见 ADR-003。

### Memory 查询、直接 ID 与导出

```text
可信 Principal + 明确用途/观看身份
→ 授权 WorldScope 与 audience
→ 取得当前安全版本、Memory revision 与可用索引版本
→ 限域且限受众候选集
→ 检索/排序/分页
→ 输出前复核权限和失效状态
→ 有界 MemoryQueryResult → 未来 Prompt Runtime
```

禁止全库检索后过滤，包括隐藏候选数量、词频、分数和摘要。直接 ID 也需要同一授权流水线；对外“无记录”与“无权限”统一为不含存在性信息的不可用结果。Owner 导出是单一明确 Scope 的显式管理行为，不隐含跨 World。备份是另一个受信管理入口，不能暴露给角色工具。

### Lore → Story → Memory 示例

1. Lore 写“北方有古城”：它是来源设定，G 保留不执行。
2. 对话说“我们明天去古城”：只是对话，不写 visited_city。
3. 模型提出“角色抵达古城”的 Story candidate，FICTIONAL/CANDIDATE。
4. 未来 C 在 Owner 或合格叙事政策授权后接受事件 E，记录权威事件身份并推进 Story 投影。
5. 可信派生器可选择生成“我到访过古城”的 Memory candidate，引用 E，限定见证角色 audience；Owner 另行接受后成为 FICTIONAL/ACCEPTED Memory。
6. 删掉这条 Memory 不会撤销事件 E；修正事件需 C 的修正流程，关联 Memory 随来源失效规则退出检索再重建。

反例：“昨天我们去过城堡”进入 Memory，不自动令 `visited_castle = true`。Memory 接受只是接受该知识记录，并不充当 StoryEvent 接受。

### Roleplay → Soul

```text
Roleplay Memory -X→ Soul Memory（默认禁止）
Roleplay Memory → 未来 F：双侧授权、grant、preview、显式确认
→ 新的目标域记录 + lineage + transformation + RealityStatus
```

EXIT、SUSPEND、summary 不触发跨域。共同体验可表达“共同玩过月球探险剧情”，不能表达“现实去过月球”；使用 FICTIONAL_SHARED_EXPERIENCE，不能直接改源记录的 world_id。反向 Soul → Roleplay 同样默认拒绝，aside 也不能绕过 F。

## 六、生命周期与安全恢复

| 操作 | 选定合同 |
| --- | --- |
| create | 校验来源与范围后持久候选；Owner 显式接受可直接建立 ACCEPTED 记录及接受凭据；不是每句聊天自动保存 |
| supersede / accept / reject | 新 ID 记录精确替代来源，旧正文/provenance 保留，原子设置后继；REJECTED 不进入默认检索；不悄悄改旧 canon |
| hide / audience 收紧 | 有操作来源的可见性控制，同事务推进集合修订；默认检索与缓存立即失效；Owner 可显式恢复普通 HIDDEN |
| audience 扩大 | Owner 显式批准的新记录，不能由模型增加观看者；不允许越过 Scope |
| delete | 不可由普通会话调用；写最小 tombstone 并阻止自动恢复，不把 DELETE 当 hide；正文清除与派生清理另有可验证步骤 |
| retention | B1 默认不自动过期；Owner 明确策略才能清理，策略操作仍需审计/修订与删除门禁 |
| source deletion / Bridge revocation | 依赖来源不可用时派生记录立即不可检索；反向 lineage 查找、缓存/索引及摘要均覆盖；元引用不授权读源正文 |
| reindex | 从授权真源构造；不能新增知识、改 canon 或复活 tombstone；只发布匹配来源版本的完整索引代次 |
| restart | 已提交记录/修订/幂等保持；新运行代次使旧会话写入失效；不用重启次数充当内容修订 |
| restore | 旧数据复制到新 generation，重放不随数据回滚的删除/撤销控制记录，验证后才激活；缺失控制记录则隔离并拒绝服务 |

安全删除与备份时间回溯必须分开。未来 B1 的最低承诺是“不经恢复门禁重新检索被删除的 Memory”，不是擦除所有磁盘/外部副本。为此删除控制记录需位于 durable 管理域、独立于被回溯 generation；这不是第二套内容库。完整合同及宕机次序见 ADR-004。无法读取该控制域时不降级成无删除限制，已发送到模型或用户的内容无法承诺撤回。

摘要保留来源集合、版本和所有分类；不是删除源、擦除 provenance 或提升 canon 的捷径。混合真实性/接受状态需分组，不用 UNKNOWN 洗掉明确的 FICTIONAL；模型摘要自身保持 MODEL 来源，最多以 AGENT_INFERRED 或 FICTIONAL 表达，不能伪装 OBSERVATION。摘要受众不得大于源可见身份集合的交集。

## 七、数据所有权矩阵

“未来”表示合同，不表示已实现。物理共库不等于相互授权。

| 对象 | Owner | 真源 | 持久化 | 修改权威 | 隔离边界 | 真源 / 派生 |
| --- | --- | --- | --- | --- | --- | --- |
| World | 资源 Owner | 当前元数据与 revision | E 已有 | 授权 World 命令/CAS | owner/soul/world | 真源 |
| Timeline | World Owner | 已登记 Timeline；未来事件顺序 | E 已有最小字段 | 当前聚合合同；未来 C | 完整 WorldScope | 身份真源；未来时钟/投影单独版本 |
| CharacterDefinition | 定义 Owner | 固定版本定义及导入来源 | E 已有定义；完整资产另属 L | Owner 登记新版本 | owner/definition/version | 真源，不等于所有实例知识 |
| CharacterInstance | World Owner | 固定 DefinitionRef 与实例局部状态 | E 已有 Values | 当前会话 World CAS；未来专门 reducer | Scope/instance | 身份真源；未来关系状态为派生 |
| SessionBinding | World Owner，绑定 Principal | 存储绑定/epoch/runtime_id | E 已有历史 | 生命周期/恢复协调方 | Scope/principal/session | 写权限绑定真源 |
| StoryEvent（未来 C） | World Owner | 通过接受的事件与依据 | 未来持久 | Owner/委托政策校验后的 C | Scope/event | Story 变化真源 |
| StoryState（未来 C） | World Owner | accepted StoryEvents | 未来快照 | 确定性 reducer | Scope | 派生 |
| RelationshipState（未来 C） | World Owner | accepted StoryEvents | 未来投影 | relationship reducer | Scope/实体对 | 派生，不以 Memory 代替 |
| WorldMemory（未来 B1） | World Owner | 记录版本、来源、控制状态 | 同 life.db 的 Schema 4 | 受权会话/Owner 维护 + Memory CAS | Scope/audience | 知识记录真源，不是 Story 真源 |
| Lore（未来 J） | 设定资产 Owner | 固定书/条目版本 | G 仅有 IR；未来 L/J | 受信导入/Owner 选用 | 资产权限及 World 版本绑定 | 设定来源；激活结果派生 |
| BridgeEvent（未来 F） | Owner 双侧授权 | grant、变换、lineage 和结果 | 未来审计 | F 校验器与目标 writer | 源/目标 Scope 双侧 | 跨域动作真源；目标内容为有来源的新记录 |
| Prompt projection（未来 K） | 请求主体所在域 | 已授权结果 | 默认临时 | K 有界组装，无接受权 | Scope/观看身份/用途 | 派生 |
| Retrieval Index（未来） | 所属集合 Owner | canonical Memory | 可重建，可不备份 | 授权索引维护 | Scope/audience/版本 | 派生 |
| Cache（未来） | 请求授权域 | 当前授权查询结果 | 默认进程内 | 查询服务，逐次检查版本 | Scope/principal/观看身份/用途/安全版本 | 派生 |
| 删除/撤销控制记录（未来） | 安装 Owner | 不回溯的控制序列 | durable 管理域 | Owner 删除；未来 F 撤销 | 安装身份/Scope/目标引用 | 安全控制真源，不存 Memory 正文 |

## 八、小型威胁模型

边界内可信：已认证入口、授权服务、数据库事务和 durable 管理器。模型、卡片、请求 ID、索引候选均不可信。拥有操作系统原始数据库读取权的攻击者、外部模型已保留内容及物理介质取证不在逻辑 ACL 能防止的范围；不能因此允许应用接口绕过检查。

| 攻击 / 误用 | 阻断与剩余限制 |
| --- | --- |
| 猜测跨 World memory_id | 完整 Scope 与受众先校验，限域取值；无权/不存在统一对外结果，无全局存在性探针 |
| World B 相同 query 命中 A 缓存 | 完整 namespace、当前授权及安全版本复核；缓存不是授权票据 |
| 同一 CharacterDefinition 混读 | 定义不参加访问授权；实例必须精确匹配 World/Timeline |
| 旧 Session 晚到模型输出 | 同事务检查 OPEN/Principal/epoch/runtime_id；EXIT/Switch/恢复后拒绝，不能转投 Soul |
| restore 复活已删除记录 | 不回溯控制记录先重放，缺失则拒绝激活；外部旧副本不能保证物理消失 |
| Bridge 撤销后摘要仍出现 | 来源依赖检查与反向 lineage 失效，安全版本立即阻断陈旧索引；B1 无 Bridge 写入口 |
| Prompt builder 直接读表 | 只允许消费授权 MemoryQueryResult；不把裸仓储暴露为模型工具，H 必须限制实际接线 |
| embedding/index 泄漏 | 建候选、统计及排序前分区，继承 audience；不把多 World 数据送无隔离外部索引 |
| debug/export 泄漏 | 同等读授权、明确管理用途；匿名诊断无正文/原 prompt/查询文本/可反查来源 |
| 模型伪造 reality/canon | 服务器推导来源分类、验证接受凭据；MODEL 不可自封观测或接受权 |
| 权限在查询中撤销 | 返回前重验安全版本；不一致则丢弃/重试有界次数；不发送已失效分页或流式后续块 |
| 私有写入数量经修订号泄漏 | 原始集合修订仅内部使用；角色只拿不透明游标，计数/排序只依赖授权候选 |

先授权后检索防止明显的排名、候选及缓存串域；共享 SQLite/CPU 无法保证严格恒时或完全消除资源争用计时侧信道。不得把逻辑隔离写成完整侧信道认证。

## 九、B1 可实施边界与后续验收

B1 在新任务书授权后可实现 Memory 领域值、仓储合同、同库 SQLite 持久化、Schema 4 与 3 → 4 副本迁移、Owner/会话的限域写读、独立 revision/幂等、重启、备份恢复和隔离测试。最低查询可使用确定性限域列表/文本匹配，不依赖向量服务；缓存与索引可以暂不启用，但一旦启用必须遵守本合同。

B1 的必要最小依赖是可信 Principal/观看上下文、共享事务围栏和恢复删除门禁，不是 Story/Bridge 服务。IdKind.MEMORY 与修订类型是未来新增提案；SourceType.STORY_EVENT 留给 C 配套审核，当前枚举不改。无验证器的事件/Bridge 来源写入在 B1 拒绝。旧生活 memories 原样保留且不纳入 World Memory 查询，未来显式映射另审。

B1 不包含 embeddings、vector DB、LLM 自动提取、Story/Lore/Bridge/Prompt Runtime、Hermes/OpenClaw 或关系引擎。不把本节当作 B1 执行任务书，也不提前授权第一行实现。

后续必须新增的合同验收包括：同定义双 World、角色 A/B/用户视角、UUID 猜测、来源伪造、同修订双连接竞争、EXIT 与写入竞争、幂等重试、替代失败原子性、缓存/分页撤销、索引落后、摘要来源撤销、恢复与删除控制记录故障、多实例迁移失败、旧 Schema 拒绝和 Windows 连接清理。现有 [领域测试](../../tests/test_domain.py)、[运行测试](../../tests/test_world_runtime.py)、[SQLite 测试](../../tests/test_world_sqlite_repository.py)、[迁移测试](../../tests/test_schema3_migration.py) 只锁定 A/D/E 基础，不能冒充上述未来 Memory 验收。

## 十、本阶段交付限制

仅主文档及四份 ADR；Runtime/tests/CI 不修改。DATA_SCHEMA before/after 均为 3，Schema impact = NONE AT RUNTIME，Migration = NOT IMPLEMENTED。未来 Schema 4 是架构选择，独立审核通过后才成为接受的架构决策；不是已运行的 Schema。

未冻结的物理细节仅为 B1 的列类型/索引组合/具体序列编码、最终内容大小上限与错误码拼写；不得借这些实施选择重议已明确的所有权、访问、接受权、修订和恢复安全合同。未来 C 的叙事委托政策及 F 的 Bridge 服务另行设计，不阻塞 B1 的 Owner 路径。
