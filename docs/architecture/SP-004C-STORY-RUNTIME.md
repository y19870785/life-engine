# SP-004C0 — Story Runtime 架构冻结

状态：**PROPOSED / PENDING_INDEPENDENT_REVIEW**。固定基线：`0028faedc36e00c52b9328e15a43fa81c31f9475`。本阶段只交付设计；`DATA_SCHEMA = 5`，签名 `SP-004J-lore-runtime-v1`，Runtime、数据库、测试和宿主入口均不改变。

本文与四份决策记录共同约束未来 SP-004C1：[事件真源](adr/SP-004C-001-STORY-EVENT-TRUTH.md)、[投影与重放](adr/SP-004C-002-STORY-PROJECTION-REPLAY.md)、[逻辑时钟](adr/SP-004C-003-STORY-CLOCK-LIFECYCLE.md)、[事实、关系与线索](adr/SP-004C-004-STORY-RELATIONSHIPS-THREADS.md)。现有依据包括[总体架构](SP-004-PERSISTENT-WORLD-RUNTIME.md)、[World 领域模型](SP-004A-WORLD-DOMAIN-MODEL.md)、[World Memory](SP-004B-WORLD-MEMORY.md)、[Lore Runtime](SP-004J-LORE-RUNTIME.md)与[实施计划](../planning/SP-004-IMPLEMENTATION-PLAN.md)。历史文档的阶段状态按成文时点理解。

## 一、问题与现有合同

Story Runtime 需要判定一个精确 `WorldScope(owner_id, soul_id, world_id, timeline_id)` 内**哪些事已被正式接受为发生过**，再将这些事投影为可恢复的当前故事状态。提到、记住、设定记载、模型叙述与 Prompt 呈现都不构成事件接受。它不是聊天归档、NPC 自主模拟或通用事件溯源框架。

现有 `WorldRuntime` 负责 World/Timeline/CharacterInstance/SessionBinding 的身份和生命周期，`World.revision` 与 `WriterEpoch` 保护该聚合；`CharacterInstance.state`、`relationships` 和 `WorldState.values` 是最小 `Values` 面，不带已接受事件依据。现有 `WorldTimeline.logical_tick` 也没有 Story 接受语义。`MemoryRuntime` 拥有独立 `MemoryCollectionRevision`、可见范围和删除恢复控制；`LoreRuntime` 拥有固定书版本、Scope 绑定及 `LoreBindingRevision`。C1 不把这些现有值、Memory 或 Lore 解释为历史 Story 事实。

## 二、真源、候选和接受权

唯一 canonical Story 历史是按 Scope 排序的**不可变 Accepted StoryEvent 日志**。`StoryState`、关系、线程和供未来 K 消费的 `StoryProjection` 都是该日志的确定性派生；快照可持久化，但不是第二真源。新 World 的 StoryRevision 与 StoryClock 均为 0，投影为空。只有显式接受的 bootstrap 事件才能建立初始事实；不从 CharacterDefinition、scenario、first_mes、Lore、Memory 或既有 `Values` 自动回填。

`StoryEventCandidate` 是短暂、受限的提案，可由受信 Owner、当前会话、用户报告、模型或外部信息启发；C1 默认不持久化候选。来源不授予接受权。第一版仅允许受信入口执行两类显式操作：`OwnerStoryContext` 的 Owner 管理接受/修正，或 `SessionStoryContext` 对当前 OPEN Session 的明确 accept 命令。后者必须是上游主动调用 Story API；模型自然语言、普通宿主消息、Lore 激活、Memory 命中本身均不能调用 accept。`Principal` 是受信上游提供的身份断言，不是登录凭据，两个 Context 均不得直接交给模型构造。

接受记录的 `accepted` 表示已进入 Story 日志；`CanonStatus` 仍描述来源/内容分类，两者不是同一个开关。C1 接受时验证 `Provenance`、`RealityStatus`、`CanonStatus` 和现有来源约束；不能通过写 Story 把 `USER_CLAIMED`、`AGENT_INFERRED` 或 `FICTIONAL` 提升为可信观测。内容即使包含命令式语句仍只是数据，不授予工具、Bridge grant、Memory audience 或 Host 权限。

## 三、事件身份与首版类型

事件使用现有 `DomainId(IdKind.EVENT)`，不另造 UUID 体系。建议持久字段：`event_id`、完整 Scope、`story_revision`、Scope 内连续 `event_sequence`、独立 `logical_tick`、`event_kind`、`payload_version`、受限类型化 payload、`Provenance`、内容来源引用、接受操作者、可选角色行为主体、`created_at`、`accepted_at`、可选 `supersedes_event_id`。`accepted_at` 是带时区 UTC 审计时间，不参与 reducer 或排序。行为主体 `Principal` 与故事中的 `CharacterInstanceId` 不可混同。来源引用只保留带类型身份/lineage，不自动读取其他子系统的正文，不设跨 Memory/Lore 表的硬外键。

| 首版 `StoryEventKind` 候选 | 确定性作用 |
| --- | --- |
| `WORLD_FACT_SET` / `WORLD_FACT_REMOVED` | 设置或移除有界命名空间键值 |
| `CHARACTER_STATE_SET` / `CHARACTER_STATE_REMOVED` | 修改本 Scope 的指定 CharacterInstance 投影 |
| `RELATIONSHIP_SET` / `RELATIONSHIP_REMOVED` | 修改本 Scope 的明确有向实例对关系键 |
| `THREAD_OPENED` / `THREAD_UPDATED` / `THREAD_RESOLVED` / `THREAD_CANCELLED` | 按 StoryThreadId 推进线索投影 |
| `NARRATIVE_EVENT` | 仅进入已接受历史，不从正文推断结构化变化 |

每类 payload 有明确版本、字段、引用和 UTF-8 字节上限；不能把任意 `dict[str, Any]` 留给 reducer 猜。建议新增 `IdKind.STORY_THREAD` 用于线索，C0 不改 `domain.py`。`NARRATIVE_EVENT` 可记录“雨夜进入钟楼”，但不自动设置地点、关系或任务完成。第一版不建 StoryArc 引擎、评分、情绪向量、用户代理实体或自动摘要。

## 四、修订、时钟、修正与幂等

`StoryRevision` 每完整 WorldScope 从 0 开始，每接受**一个**事件递增 1；首版一次调用接受一个事件。它与 `World.revision`、`MemoryCollectionRevision`、`LoreBindingRevision` 完全独立。`event_sequence` 是同 Scope 的连续数据库接受顺序，`logical_tick` 是独立 `StoryClock` 的故事刻度：首版每接受一个事件推进一格，故正常日志中三个数字都从 1 开始逐事件连续；列语义仍独立，后续不能用一个字段冒充另一个。调用方不能提交旧 tick、倒插历史或自行选择时钟。

故事时钟**不写回**现有 `WorldTimeline.logical_tick`，该字段暂留为最小/历史 Timeline 面；C1 不改 World 生命周期或 `World.revision`。ACTIVE 但没有 accepted event、SUSPEND、离线、重启以及墙钟流逝都不推进 Story。恢复旧备份只恢复当时已接受的事件、修订、刻度和投影，不凭离线时长补事件。Soul World 仍按自身生命周期处理会话，但它的 StoryClock 同样只由显式事件推进。

已接受事件的 Scope、payload、来源、类型和时间永久不可变；首版不物理删除。修正选用**新普通事件 + `supersedes_event_id`**：只允许指向同 Scope、已存在且序号更早的事件；新事件以显式结构化 payload 改变**当前**投影，旧事件的历史作用不从过去重放结果中抹掉。修正是前向补偿，不是把旧事件从日志过滤后改写历史；对错误事实使用新的 SET/REMOVED，对线索使用合法的后继状态事件。对 `NARRATIVE_EVENT` 的修正仍只是新的叙事/撤回说明，不会自动改结构化字段。更复杂的追溯重算或依法删除须另立任务。

接受操作采用 `(producer, source, slot)` 幂等身份及规范提案指纹。指纹覆盖 Scope、类型/版本、payload、provenance、source refs、预期 StoryRevision 和修正目标，不包含首次接受时生成的随机 EventId。同键同指纹的重试优先返回原 `event_id/revision/tick` 回执，即使携带旧预期修订；同键不同指纹拒绝。非重试请求才做数据库级 StoryRevision CAS。两个独立连接持相同预期修订并发接受，至多一个成功，另一个 `REVISION_CONFLICT`；忙锁不能伪装成冲突。

## 五、确定性投影与结构化边界

`reduce(previous_state, accepted_event) → next_state` 是纯、确定、无副作用函数；不得访问数据库、Memory、Lore、宿主、网络、时钟、随机数或工具。Event 必须携带 reducer 所需全部值。相同有序事件与同一 `StoryProjectionVersion` 在 Windows/Linux 得到逐字节相同的规范投影。建议首版版本 `SP-004C-story-projection-v1`；未来改 reducer 语义必须显式升级版本、迁移并重建验证，不可用新代码静默重新解释旧事件。

`StoryState` 建议包含 Scope、`StoryRevision`、`StoryClock.logical_tick`、`last_event_sequence`、投影版本，以及四组按规范顺序序列化的派生值：

| 投影 | 第一版边界 |
| --- | --- |
| `world_facts` | 受限命名空间的字符串键与有界字符串值；SET/REMOVE 明确作用 |
| `character_states` | 以本 Scope `CharacterInstanceId` 为键；与 DefinitionId/角色名无关 |
| `relationships` | 有向 `(source CharacterInstanceId, target CharacterInstanceId, key)`；首版只支持同 Scope 的实例对，不引入 UserProxy |
| `threads` | `OPEN/RESOLVED/CANCELLED`、有界标题/摘要及打开、最近更新、结案事件引用；`THREAD_UPDATED` 仅对 OPEN 线索合法 |

同一定义在 A/B World 的实例、关系、事件和线程完全独立。Thread 是叙事线索，不是提醒、UserTask 或调度任务；不调用 scheduler。现有 `CharacterInstance.state/relationships`、`WorldState.values` 保持兼容，但 C1 **不从中读取 Story 真源，也不双写同步**。未来若需废弃或映射旧值，必须另立经 Owner 审阅的迁移，不用 Schema 迁移伪造无事件依据的事实。

建议持久化单行、有大小上限的规范 JSON `StoryState` 投影与不可变事件日志。每次接受在同一 SQLite 事务中完成：授权与会话围栏 → 同键幂等检查 → StoryRevision CAS → payload/引用校验 → reducer 预演及投影预算 → 插入事件 → 更新投影/修订/时钟 → 审计与回执 → commit。任一步失败全部回滚，不得出现孤立 event 或孤立投影。`NARRATIVE_EVENT` 不增结构化 state，但仍推进修订、顺序与刻度。事件 payload 候选上限 64 KiB，叙事正文建议 8–16 KiB，投影建议不超过 512 KiB 或 1 MiB；C1 任务书须固定具体值和测试。超预算拒绝整次接受，不截断投影或先写事件。

重放按 Scope 内 `event_sequence` 严格升序，从空投影运行同版本 reducer，必须与持久投影语义及规范编码一致。完整重放是可执行验收和修复依据；生产启动可用有限一致性检查，无须每次启动全量重放。缺失/重复序号、错误末事件、修订/刻度不一致、未知投影版本或校验时重放不符，均 `STORAGE_CORRUPT`，不能静默修补。具体何时做全量校验由 C1 在规模预算内设计。

## 六、操作权、生命周期与查询

Session 接受在同一稳定事务边界核对 Principal、完整 Scope、World `ACTIVE`、当前 `SessionBinding OPEN`、`WriterEpoch`、`runtime_id`、对应 viewer/CharacterInstance、安装 generation 和预期 StoryRevision。Roleplay viewer 必须是当前角色实例；Soul viewer 必须是 Soul。EXIT、SUSPEND、SWITCH、重启或 restore 后旧调用不得提交到当前/其他 World。Owner 管理接受不伪造 Session：CREATED/SUSPENDED 可显式 bootstrap/修正；ARCHIVED 默认只读，须经合法 UNARCHIVE 后再写；TOMBSTONED 只读审计、不接受事件。当前 `WorldRuntime` 尚无完整 ARCHIVE/UNARCHIVE 应用入口，C1 不能假设该入口已存在。

Owner 审计可限自己拥有的 Scope 列表/读取完整接受日志与事件；Session 不提供按猜测 EventId 直接查事件或全量日志，只能经当前 Scope/围栏取得有界 `StoryProjection`。投影仍代表世界状态，**不是角色知识 ACL**：即使 Session 内部可取得投影，未来 K 仍须按用途选择可向模型显示的字段，不能直接把隐藏世界事实全部拼入 Prompt。C1 不自动将投影接入 Host。查询先授权后读取，不用全库扫描后过滤；结果附 Scope、修订、时钟、投影版本及不透明 snapshot token，原始修订不充当授权票据。

## 七、其他子系统的责任边界

| 来源或消费者 | C0 冻结合同 |
| --- | --- |
| World Memory | Memory 是“谁可记住/知道什么”；即使 `CanonStatus.ACCEPTED` 也不是 Story 接受。C1 不查询 Memory 仓储、不自动从 Memory 生成 Story，也不从 Story 自动写 Memory。未来派生需独立授权与可见性。 |
| Lore / World Book | 固定设定与激活结果是上下文，不是发生事件；Lore 不能改变 Story。若设定需成为初始事实，受信 Owner 提交明确 bootstrap 事件。C1 不直接依赖 `LoreActivationResult`。 |
| SP-004F Bridge | Soul ↔ Roleplay 默认不共享。未来 F 可带 source World/Event 类型化 lineage 提出目标候选，仍须目标 Scope 重新接受；C1 不跨 World 复制事件、不签发 grant。 |
| SP-004K Prompt | K 将来消费有界、用途明确的 StoryProjection，不能直读完整日志或反向写 Story；Prompt 文本不产生 Story 权限。 |
| SP-004H Host | H 将来实现受信调用、历史隔离和路由；C1 不读 Hermes/OpenClaw 聊天库、不绑定聊天 ID、不实现 `/rp`。 |

StoryEvent 的来源引用可以指向 MemoryId、`(LoreBookId, Version, LoreEntryId)`、旧 EventId 或外部消息身份，但只是不可自动解引用的 lineage；Bridge 来源必须保留 source WorldScope。Story content 永远不是权限。Soul 与 Roleplay 即便同 Owner、同 Definition、同 LoreBook，也不自动共享事件。

## 八、未来持久化与迁移提案

C0 不修改 Schema。C1 **候选** `DATA_SCHEMA = 6`、签名 `SP-004C-story-runtime-v1`；若独立审核改变编号或结构，应以 C1 正式任务书为准。候选表：`story_collection_state`（一 Scope 一行，修订/刻度/末序号/投影版本/规范 JSON）、`story_events`（不可变且按 Scope/sequence 唯一）、`story_event_subjects`、按需 `story_event_sources`、`story_operations` 和 `story_idempotency`。Thread、关系、world facts 只存在于事件与派生投影中；如为查询物化独立表，也必须可重建，不能有单独管理写入口。数据库应约束 PK/FK/Scope、唯一序号、不可变事件及 CAS；仍在同一实例 `life.db` 内，不建独立 Story 内容库。

Schema 5→6 只在**新 generation 副本**创建空 Story 日志与每个既有 Scope 的 revision/tick=0 空投影；不从旧 `CharacterInstance` Values、Memory、Lore、场景、聊天或卡片回填。全实例迁移/验证成功后原子切换 registry；失败保留旧 release/generation。Schema 2–5 精确结构与签名继续可识别，旧生活/World/Memory/Lore 数据不变；Memory 删除控制适用于 `schema >= 4`，不能因 Schema 6 中断。备份/恢复精确恢复当时 Story 日志、投影、修订和时钟，并验证一致性；恢复旧 Story 备份允许回退备份后事件，首版无 Story 物理删除或独立不复活控制账本。代码回退与数据回退仍需按整组 Schema 合同执行，不得让旧 release 直接打开新 Schema。

## 九、C1 验收矩阵

| 组别 | 必须验证 |
| --- | --- |
| 接受与幂等 | Owner 与当前 Session 明确接受；模型/Lore/Memory/普通聊天不能自动接受；同键同载荷返回原回执、异载荷拒绝；双连接 CAS 冲突；event 与 projection 原子提交。 |
| Scope | 同 Definition/同卡在两 World、Soul/Roleplay、同 Owner 跨 World、不同 Owner、错误 Timeline、猜 EventId，均不串读写。 |
| 生命周期 | ACTIVE、CLOSED、旧 WriterEpoch、SUSPENDED、ARCHIVED、TOMBSTONED、EXIT/SWITCH 竞争、重启与 restore 的旧 Session 围栏。 |
| Reducer | fact、实例状态、关系 set/remove；thread open/update/resolve/cancel；纯 Narrative；非法主体、目标、状态转换和超预算整次拒绝。 |
| 重放与修正 | 相同日志跨平台相同投影；快照等于重放；缺事件/错序号/错版本拒绝；同 Scope 前向修正保留旧事件，跨 Scope/未知目标拒绝。 |
| 时钟 | 空态 0、逐事件 +1；ACTIVE 无事件、墙钟、SUSPEND、重启均不推进；restore 精确恢复。 |
| 子系统边界 | Story/Memory/Lore 无自动互写；事件不授予工具；Prompt 文本不改 Story；无跨 World Bridge。 |
| 未来迁移 | Schema 5→6 空投影、旧表逐项保留、多实例失败不激活、Memory 删除控制及 Lore 固定绑定不回归。 |

## 十、C1 可实施边界与未决项

C1 可实现：Story 领域值、独立修订/时钟、类型化事件及来源、Owner/Session 显式接受、幂等、CAS、不可变日志、纯 reducer、投影、前向修正、事实/实例/关系/线索、Owner 审计、Session 有界投影、Schema 迁移、重启/备份/恢复及验收测试。

C1 不实现：LLM 抽取/自动接受、Story↔Memory 自动派生、Lore 自动转换、Prompt Runtime、Bridge、Hermes/OpenClaw、NPC 自主模拟、离线/墙钟剧情推进、AI 关系打分、情绪/规划引擎、向量库、聊天全文存档、物理删除或全系统事件溯源。

留给 C1 任务书复核的**物理参数**：payload/叙事/投影最终字节上限，投影校验频率、索引与 snapshot token 格式。它们不得改变本文的真源、接受权、隔离、确定性、时钟和原子提交合同。C0 不启动 C1，不改 README，也不把架构提案宣称为已可用功能。
